"""
Corre toda la cadena, desde los datos filtrados del repositorio hasta la red completa, y guarda lo que imprime cada
paso en un solo log (ver docs/contexto_entrega_3/01_como_correr.md, seccion 7).

   1. Etapa 0: expediciones del dia laboral                        (3-)
   2. Etapa 1: rutas a electroterminales                           (4-)
   3. Etapa 2: jornadas sin bateria, caso base                     (6- --modo ruta)
   4. Etapa 2: jornadas sin bateria, caso base con interlining     (6- --modo cluster)
   5. Caso base de la red completa                                 (10- --escenario E0)
   6. Caso base con interlining de la red completa                 (10- --escenario E1)
   7. Vespucio Norte                                               (correr_terminal.py --terminal 1)
   8. El Conquistador                                              (correr_terminal.py --terminal 2)
   9. Los Espinos + Santa Rosa                                     (correr_terminal.py --terminal 3)
  10. La Reina                                                     (correr_terminal.py --terminal 4)
  11. Red completa: suma de los cuatro terminales                  (17-)

Parte de data-filtrado/, que esta en el repositorio. Los GTFS crudos que leen 1- y 2- no viajan en el repositorio,
asi que esos dos scripts no se corren aqui. Se detiene en el primer paso que falla. El log queda en
results/correr_todo.log; cada terminal deja ademas su propio correr_terminal.log.

Uso (desde la raiz del repositorio):
    python scripts/correr_todo.py                    # todo
    python scripts/correr_todo.py --desde 7          # retoma desde el paso 7
    python scripts/correr_todo.py --hasta 6          # solo Etapas 0-2 y el caso base de la red
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
RAIZ = SCRIPTS.parent
LOG = RAIZ / "results" / "correr_todo.log"
C1B = "data-processed/rutas_cluster_c1b.csv"

PASOS = [
    ("Etapa 0: expediciones", ["3-preprocesamiento_expediciones.py"]),
    ("Etapa 1: rutas a electroterminales", ["4-clustering_c1.py"]),
    ("Etapa 2: jornadas del caso base", ["6-vsp_asignacion_buses.py", "--modo", "ruta", "--asignacion", C1B,
                                         "--unir-electroterminales", "--etiqueta", "E0"]),
    ("Etapa 2: jornadas con interlining", ["6-vsp_asignacion_buses.py", "--modo", "cluster", "--asignacion", C1B,
                                           "--unir-electroterminales", "--etiqueta", "E1"]),
    ("Caso base de la red completa", ["10-caso_base_carga_reactiva.py", "--escenario", "E0"]),
    ("Caso base con interlining de la red completa", ["10-caso_base_carga_reactiva.py", "--escenario", "E1"]),
    ("Vespucio Norte", ["correr_terminal.py", "--terminal", "1"]),
    ("El Conquistador", ["correr_terminal.py", "--terminal", "2"]),
    ("Los Espinos + Santa Rosa", ["correr_terminal.py", "--terminal", "3"]),
    ("La Reina", ["correr_terminal.py", "--terminal", "4"]),
    ("Red completa", ["17-red_completa.py"]),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--desde", type=int, default=1, help=f"Paso desde el que se parte (1 a {len(PASOS)}).")
    parser.add_argument("--hasta", type=int, default=len(PASOS), help="Ultimo paso que se corre.")
    args = parser.parse_args()
    assert 1 <= args.desde <= args.hasta <= len(PASOS), f"--desde y --hasta deben ir de 1 a {len(PASOS)}"

    LOG.parent.mkdir(parents=True, exist_ok=True)
    tiempos = []
    t0 = time.perf_counter()
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"\n===== Cadena completa, pasos {args.desde} a {args.hasta} =====\n")
        for num, (titulo, cmd) in enumerate(PASOS, start=1):
            if not args.desde <= num <= args.hasta:
                continue
            print(f"\n>>>>> Paso {num} de {len(PASOS)}: {titulo}", flush=True)
            f.write(f"\n>>>>> Paso {num}: {titulo}: python scripts/{' '.join(cmd)}\n")
            f.flush()
            ti = time.perf_counter()
            proc = subprocess.Popen([sys.executable, str(SCRIPTS / cmd[0])] + cmd[1:], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                    cwd=RAIZ)
            for linea in proc.stdout:
                print(linea, end="", flush=True)
                f.write(linea)
            proc.wait()
            dur = time.perf_counter() - ti
            f.write(f"<<<<< Paso {num} terminado en {dur:,.0f} s (codigo {proc.returncode})\n")
            if proc.returncode != 0:
                print(f"\n***** El paso {num} ({titulo}) fallo. Mandar el log completo: {LOG}")
                if cmd[0] == "correr_terminal.py":
                    print(f"***** Para retomar dentro del terminal: python scripts/correr_terminal.py "
                          f"--terminal {cmd[2]} --desde <paso que fallo>; luego "
                          f"python scripts/correr_todo.py --desde {num + 1}")
                else:
                    print(f"***** Para retomar: python scripts/correr_todo.py --desde {num}")
                sys.exit(1)
            tiempos.append((num, titulo, dur))
            print(f"<<<<< Paso {num} listo en {dur / 60:,.1f} min", flush=True)

        total = (time.perf_counter() - t0) / 60
        resumen = "\n".join(f"  {n:>2}. {t:<46} {d / 60:6.1f} min" for n, t, d in tiempos)
        resumen = f"\n===== Tiempo por paso =====\n{resumen}\n  Total: {total:,.1f} min\n"
        print(resumen)
        f.write(resumen)
    print(f"===== Todo listo. Log: {LOG} =====")


if __name__ == "__main__":
    main()
