"""
Corre toda la propuesta en un electroterminal, en orden, y guarda lo que imprime cada paso en un log
(ver docs/contexto_entrega_3/03_como_correr.md).

  1. Caso base y caso base con interlining en el terminal        (10-)
  2. Etapa 3: cortes y re-encadenamiento                          (12-)
  3. Etapa 4: modelo relajado (reservas de partida y cota)        (13-)
  4. Etapa 4: plan de carga exacto al minuto                      (13- --exacto)
  5. Validacion independiente del plan de carga                   (15-)
  6. KPIs, figuras y resumen para el analisis                     (14-)

Se detiene en el primer paso que falla. Los resultados quedan en results/instancia_<siglas>/ y el log en
results/instancia_<siglas>/correr_terminal.log.

Uso (desde la raiz del repositorio):
    python scripts/correr_terminal.py --terminal 4          # La Reina
    python scripts/correr_terminal.py --terminal 1          # Vespucio Norte
    python scripts/correr_terminal.py --terminal 2          # El Conquistador
    python scripts/correr_terminal.py --terminal 3          # Los Espinos + Santa Rosa
    python scripts/correr_terminal.py --terminal 4 --desde 4   # retoma desde el paso 4
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import instancia                                   # noqa: E402
from common.rutas import DATA_FILTRADO, CSV_SEP                 # noqa: E402

SCRIPTS = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terminal", required=True, help="depot_id: 1, 2, 3 (o 5) o 4.")
    parser.add_argument("--desde", type=int, default=1, help="Paso desde el que se parte (1 a 6).")
    args = parser.parse_args()
    t = str(args.terminal)
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    nombre = instancia.nombre_terminal(depots, instancia.patios_terminal(depots, t))
    carpeta = instancia.carpeta_instancia(depots, t)
    pasos = [
        ("Caso base", ["10-caso_base_carga_reactiva.py", "--escenario", "E0", "--terminal", t]),
        ("Caso base con interlining", ["10-caso_base_carga_reactiva.py", "--escenario", "E1", "--terminal", t]),
        ("Etapa 3", ["12-etapa3_cortes_reencadenamiento.py", "--terminal", t, "--escenario", "E1", "--holgura", "0"]),
        ("Etapa 4, modelo relajado", ["13-etapa4_programacion_carga.py", "--terminal", t, "--holgura", "0",
                                      "--delta", "15"]),
        ("Etapa 4, plan de carga exacto", ["13-etapa4_programacion_carga.py", "--terminal", t, "--holgura", "0",
                                           "--delta", "15", "--exacto"]),
        ("Validacion del plan de carga", ["15-validar_plan_carga.py", "--terminal", t]),
        ("KPIs y figuras", ["14-kpis_instancia.py", "--terminal", t]),
    ]
    # el paso 1 del usuario son los dos casos base
    numeros = [1, 1, 2, 3, 4, 5, 6]
    log = carpeta / "correr_terminal.log"
    t0 = time.perf_counter()
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n===== {nombre} (terminal {t}), desde el paso {args.desde} =====\n")
        for num, (titulo, cmd) in zip(numeros, pasos):
            if num < args.desde:
                continue
            print(f"\n>>> Paso {num}: {titulo} ({nombre})", flush=True)
            f.write(f"\n>>> Paso {num}: {titulo}: python scripts/{' '.join(cmd)}\n")
            f.flush()
            ti = time.perf_counter()
            proc = subprocess.Popen([sys.executable, str(SCRIPTS / cmd[0])] + cmd[1:], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                    cwd=SCRIPTS.parent)
            for linea in proc.stdout:
                print(linea, end="", flush=True)
                f.write(linea)
            proc.wait()
            dur = time.perf_counter() - ti
            f.write(f"<<< Paso {num} terminado en {dur:,.0f} s (codigo {proc.returncode})\n")
            if proc.returncode != 0:
                print(f"\n*** El paso {num} ({titulo}) fallo. Mandar el log completo: {log}")
                print(f"*** Para retomar: python scripts/correr_terminal.py --terminal {t} --desde {num}")
                sys.exit(1)
            print(f"<<< Paso {num} listo en {dur:,.0f} s", flush=True)
    print(f"\n=== {nombre}: todo listo en {(time.perf_counter() - t0) / 60:,.1f} min. Resultados en {carpeta} ===")
    print(f"=== Log: {log} ===")


if __name__ == "__main__":
    main()
