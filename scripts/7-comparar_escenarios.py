"""
Cierre de la Fase 6 (ver docs/context/01_metodologia.md): compara
los 4 escenarios de la Etapa 2 (ruta, libre, cluster_c1, cluster_c2) y
calcula el "precio del clustering" prometido en
docs/Propuesta_metodologia_reunion.md seccion 5: cuantos buses/cuanto costo
adicional paga cada estrategia de clustering frente a la cota inferior sin
restriccion de electroterminal (modo 'libre').

No corre ningun modelo nuevo: solo lee results/06_vsp/resumen_escenarios.csv
(que van llenando las corridas de scripts/6-vsp_asignacion_buses.py) y
genera la comparacion final para llevar a la reunion / al informe.

Requiere que los 4 escenarios ya esten en resumen_escenarios.csv:
    python scripts/6-vsp_asignacion_buses.py --modo ruta
    python scripts/6-vsp_asignacion_buses.py --modo libre
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1.csv --etiqueta cluster_c1
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c2.csv --etiqueta cluster_c2
    python scripts/7-comparar_escenarios.py

Output: results/06_vsp/comparacion_escenarios.png
        results/06_vsp/precio_del_clustering.csv
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.rutas import CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("06_vsp")
RESUMEN_PATH = RESULTS / "resumen_escenarios.csv"

# Cota inferior teorica: maximo de expediciones simultaneas (ningun plan
# puede usar menos buses que esto), ver results/03_preprocesamiento/reporte.md.
COTA_INFERIOR_TEORICA = 6539

ESCENARIOS = ["ruta", "libre", "cluster_c1", "cluster_c2"]
ETIQUETAS_BONITAS = {
    "ruta": "Caso base\n(sin interlining)",
    "libre": "Cota inferior C0\n(interlining libre)",
    "cluster_c1": "Cluster C1\n(heuristica)",
    "cluster_c2": "Cluster C2\n(MILP capacidad)",
}
COLORES = ["#8f4a2c", "#2c6e8f", "#4a8f6e", "#6e4a8f"]


def main():
    if not RESUMEN_PATH.exists():
        raise SystemExit(f"No existe {RESUMEN_PATH}. Correr antes los 4 escenarios de "
                          f"scripts/6-vsp_asignacion_buses.py (ver docstring de este script).")
    r = pd.read_csv(RESUMEN_PATH, sep=CSV_SEP).set_index("etiqueta")
    faltantes = [e for e in ESCENARIOS if e not in r.index]
    if faltantes:
        raise SystemExit(f"Faltan escenarios en {RESUMEN_PATH}: {faltantes}. "
                          f"Correr scripts/6-vsp_asignacion_buses.py para cada uno (ver docstring).")
    r = r.loc[ESCENARIOS]

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    axs[0].bar([ETIQUETAS_BONITAS[e] for e in r.index], r["buses"], color=COLORES)
    axs[0].axhline(COTA_INFERIOR_TEORICA, color="crimson", linestyle="--",
                    label=f"Cota inferior teorica ({COTA_INFERIOR_TEORICA})")
    for i, v in enumerate(r["buses"]):
        axs[0].text(i, v + 60, f"{v:,.0f}", ha="center", fontsize=10)
    axs[0].set_ylabel("Numero de buses")
    axs[0].set_title("Buses necesarios por escenario")
    axs[0].legend()

    precio_buses = r["buses"] - r.loc["libre", "buses"]
    axs[1].bar([ETIQUETAS_BONITAS[e] for e in r.index], precio_buses, color=COLORES)
    for i, v in enumerate(precio_buses):
        axs[1].text(i, v + (15 if v >= 0 else -30), f"{v:+,.0f}", ha="center", fontsize=10)
    axs[1].axhline(0, color="black", linewidth=0.8)
    axs[1].set_ylabel("Buses adicionales vs. cota inferior C0 (libre)")
    axs[1].set_title('"Precio" de cada estrategia frente al optimo\nsin restriccion de electroterminal')

    fig.suptitle("Comparacion final de escenarios - Etapa 2 (VSP sin bateria)", fontsize=13)
    fig.tight_layout()
    png_path = RESULTS / "comparacion_escenarios.png"
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"  -> {png_path}")

    tabla = r.copy()
    tabla["precio_buses_vs_libre"] = precio_buses
    tabla["precio_costo_vs_libre_usd"] = r["cost_total_usd"] - r.loc["libre", "cost_total_usd"]
    tabla["precio_costo_vs_libre_pct"] = (
        tabla["precio_costo_vs_libre_usd"] / r.loc["libre", "cost_total_usd"] * 100).round(1)
    csv_path = RESULTS / "precio_del_clustering.csv"
    tabla.to_csv(csv_path, sep=CSV_SEP)
    print(f"  -> {csv_path}")

    print("\n=== Precio del clustering (frente a la cota inferior C0 'libre') ===")
    print(tabla[["buses", "precio_buses_vs_libre", "cost_total_usd",
                  "precio_costo_vs_libre_usd", "precio_costo_vs_libre_pct"]].to_string())

    # --- Chequeo de sanidad: el orden esperado es ruta >= cluster >= libre >= cota inferior ---
    assert r.loc["ruta", "buses"] >= r.loc["cluster_c1", "buses"] >= r.loc["libre", "buses"] >= COTA_INFERIOR_TEORICA, (
        "Orden inesperado entre escenarios: se esperaba ruta >= cluster_c1 >= libre >= cota inferior teorica. "
        "Revisar si algun escenario se corrio con parametros distintos (radio, subset, etc.).")
    print("\n  [OK] Orden de escenarios consistente (ruta >= cluster >= libre >= cota inferior teorica).")


if __name__ == "__main__":
    main()
