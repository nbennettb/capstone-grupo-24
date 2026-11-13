"""
Corre en orden todos los scripts que producen los resultados del informe y se detiene en el primer error.

Antes de correr, copiar los datos del curso en datos/ (ver la Seccion 4.1.2 del informe).

Uso (desde esta carpeta):
    python correr_todo.py                  # todo (~2 h; el modelo detallado de la Etapa 4 tarda 1 h)
    python correr_todo.py --sin-pesados    # omite el barrido de niveles, los bloques de 5 min, el detallado y los graficos 13
    python correr_todo.py --desde 12       # retoma desde el paso 12 (los pasos se numeran al listarlos con --listar)
    python correr_todo.py --listar         # muestra los pasos con sus argumentos sin correr nada

Cada paso imprime sus resultados en consola y guarda tablas y figuras en resultados/.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
S = RAIZ
ASIG = ["--asignacion", "rutas_cluster_c1b.csv"]
UNIR = ["--unir-electroterminales"]
LR = ["--terminal", "4"]                    # La Reina

# (descripcion, script, argumentos, pesado)
PASOS = [
    ("Datos: filtro a buses", "1-filtro_datos_buses.py", [], False),
    ("Datos: filtro al dia laboral", "2-filtro_tipo_dia.py", [], False),
    ("Etapa 0: expediciones", "3-etapa0_expediciones.py", [], False),
    ("Etapa 1: asignacion de rutas", "4-etapa1_asignacion_rutas.py", [], False),
    ("Calibracion del deadhead", "5-calibracion_deadhead.py", [], False),
    ("Etapa 2: caso base (E0)", "6-etapa2_jornadas.py", ["--modo", "ruta"] + ASIG + UNIR + ["--etiqueta", "E0"], False),
    ("Etapa 2: con interlining (E1)", "6-etapa2_jornadas.py", ["--modo", "cluster"] + ASIG + UNIR + ["--etiqueta", "E1"], False),
    ("Etapa 2: cota inferior (LB)", "6-etapa2_jornadas.py", ["--modo", "libre", "--etiqueta", "LB"], False),
    ("Etapa 2: E0 con terminales separados", "6-etapa2_jornadas.py", ["--modo", "ruta"] + ASIG + ["--etiqueta", "E0_sep"], False),
    ("Etapa 2: E1 con terminales separados", "6-etapa2_jornadas.py", ["--modo", "cluster"] + ASIG + ["--etiqueta", "E1_sep"], False),
] + [
    (f"Etapa 2: sensibilidad {etq}", "6-etapa2_jornadas.py",
     ["--modo", "cluster"] + ASIG + UNIR + ["--sin-jornadas", "--etiqueta", etq] + extra, False)
    for etq, extra in [("E1_f1.2", ["--factor-desvio", "1.2"]), ("E1_f1.35", ["--factor-desvio", "1.35"]),
                       ("E1_f1.5", ["--factor-desvio", "1.5"]), ("E1_l0", ["--layover", "0"]),
                       ("E1_l10", ["--layover", "10"]), ("E1_r1", ["--radio", "1"]), ("E1_r2", ["--radio", "2"]),
                       ("E1_r4", ["--radio", "4"]), ("E1_r5", ["--radio", "5"])]
] + [
    ("Etapa 2: comparacion de escenarios", "7-etapa2_comparar_escenarios.py", [], False),
    ("Caso base, red completa (E0)", "8-caso_base_carga_reactiva.py", ["--escenario", "E0"], False),
    ("Caso base, red completa (E1)", "8-caso_base_carga_reactiva.py", ["--escenario", "E1"], False),
    ("Caso base: barrido del nivel de bateria", "9-caso_base_nivel_bateria.py", [], True),
    ("Caso base en La Reina (E0)", "8-caso_base_carga_reactiva.py", ["--escenario", "E0"] + LR, False),
    ("Caso base en La Reina (E1)", "8-caso_base_carga_reactiva.py", ["--escenario", "E1"] + LR, False),
    ("Etapa 3 en La Reina, holgura 0", "10-etapa3_cortes_reencadenamiento.py", LR + ["--escenario", "E1", "--holgura", "0"], False),
    ("Etapa 3 en La Reina, holgura 30", "10-etapa3_cortes_reencadenamiento.py", LR + ["--escenario", "E1", "--holgura", "30"], False),
    ("Etapa 3 en La Reina, holgura 60", "10-etapa3_cortes_reencadenamiento.py", LR + ["--escenario", "E1", "--holgura", "60"], False),
    ("Etapa 4, holgura 0, bloques de 15 min", "11-etapa4_programacion_carga.py", LR + ["--holgura", "0", "--delta", "15"], False),
    ("Etapa 4, holgura 0, bloques de 30 min", "11-etapa4_programacion_carga.py", LR + ["--holgura", "0", "--delta", "30"], False),
    ("Etapa 4, holgura 0, bloques de 5 min", "11-etapa4_programacion_carga.py", LR + ["--holgura", "0", "--delta", "5"], True),
    ("Etapa 4, holgura 30, bloques de 15 min", "11-etapa4_programacion_carga.py", LR + ["--holgura", "30", "--delta", "15"], False),
    ("Etapa 4, holgura 60, bloques de 15 min", "11-etapa4_programacion_carga.py", LR + ["--holgura", "60", "--delta", "15"], False),
    ("Etapa 4: modelo detallado (1 h)", "11-etapa4_programacion_carga.py", LR + ["--holgura", "0", "--delta", "15", "--detallado"], True),
    ("KPIs, validaciones y figuras F0-F6", "12-kpis_instancia.py", LR, False),
    ("Graficos de los datos (G1, G2, G5, G6)", "13-graficos_datos.py", [], True),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-pesados", action="store_true", help="Omite los pasos largos o que dependen de ellos.")
    ap.add_argument("--desde", type=int, default=1, help="Numero del primer paso a correr.")
    ap.add_argument("--listar", action="store_true", help="Lista los pasos y termina.")
    args = ap.parse_args()

    for k, (desc, script, argumentos, pesado) in enumerate(PASOS, start=1):
        if args.listar:
            print(f"{k:2d}. {desc}{'  [pesado]' if pesado else ''}: {script} {' '.join(argumentos)}")
    if args.listar:
        return

    inicio = time.perf_counter()
    for k, (desc, script, argumentos, pesado) in enumerate(PASOS, start=1):
        if k < args.desde or (pesado and args.sin_pesados):
            print(f"\n>>> Paso {k}/{len(PASOS)} omitido: {desc}")
            continue
        print(f"\n{'=' * 100}\n>>> Paso {k}/{len(PASOS)}: {desc}\n{'=' * 100}", flush=True)
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, str(S / script)] + argumentos, cwd=RAIZ)
        if r.returncode != 0:
            sys.exit(f"\nEl paso {k} ({desc}) fallo con codigo {r.returncode}. Corregir y retomar con --desde {k}.")
        print(f"\n>>> Paso {k} terminado en {time.perf_counter() - t0:,.0f} s", flush=True)
    print(f"\nTodo terminado en {(time.perf_counter() - inicio) / 60:,.1f} min. Resultados en {RAIZ / 'resultados'}")


if __name__ == "__main__":
    main()
