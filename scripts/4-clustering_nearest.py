"""
Etapa 1 (C1) del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia_y_avance.md seccion 1 y
docs/Propuesta_metodologia_reunion.md seccion 5).

Estrategia de clustering heuristica: cada RUTA (no cada expedicion
individual, ver diagnostico D4 en Propuesta_metodologia_reunion.md sobre
por que la unidad de clustering debe ser la ruta) se asigna al
electroterminal mas cercano a su centroide.

Es la version mas simple de la Etapa 1: no considera capacidad de carga
(eso lo hace la estrategia C2, scripts/5-clustering_milp.py). Sirve de
referencia rapida y de punto de partida para C2.

Input:  data-processed/expediciones.csv, data-filtrado/depots.csv
Output: data-processed/rutas_cluster_c1.csv (route_id, depot_id,
        depot_nombre, distancia_km)
        results/04_clustering_c1/reporte.md + grafico de barras (rutas por
        electroterminal)

Uso:
    python scripts/4-clustering_nearest.py
        Corre sobre las 417 rutas.

    python scripts/4-clustering_nearest.py --rutas 101 301 516 ...
        Checkpoint chico: corre solo sobre las rutas indicadas.

    python scripts/4-clustering_nearest.py --muestra 20 --semilla 42
        Checkpoint chico alternativo: toma una muestra aleatoria
        reproducible de N rutas (cubre distintas zonas de la red sin
        tener que elegirlas a mano).
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parametros                                                # noqa: E402
from common.clustering import distancia_rutas_a_depots                       # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("04_clustering_c1")
RUTAS_ESPERADAS = 417


def cargar_datos(subset_rutas=None, muestra=None, semilla=42):
    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)

    if subset_rutas:
        subset_rutas = {str(r) for r in subset_rutas}
        ex = ex[ex["route_id"].astype(str).isin(subset_rutas)]
    elif muestra:
        rutas_disponibles = ex["route_id"].astype(str).unique()
        elegidas = np.random.default_rng(semilla).choice(rutas_disponibles, size=min(muestra, len(rutas_disponibles)),
                                                           replace=False)
        ex = ex[ex["route_id"].astype(str).isin(elegidas)]
    return ex.reset_index(drop=True), depots


def graficar_rutas_por_depot(asignacion, path_png):
    conteo = asignacion["depot_nombre"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(conteo.index, conteo.values, color="#2c6e8f")
    ax.set_ylabel("Numero de rutas asignadas")
    ax.set_title("Rutas asignadas por electroterminal (C1: heuristica del mas cercano)")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def escribir_reporte(asignacion, corrida_parcial):
    conteo = asignacion["depot_nombre"].value_counts().sort_index()
    lineas = [
        "# Reporte Etapa 1 - Clustering C1 (heuristica del electroterminal mas cercano)",
        "",
        f"Corrida: {'PARCIAL (checkpoint chico, ' + str(len(asignacion)) + ' rutas)' if corrida_parcial else 'RED COMPLETA (417 rutas)'}",
        "",
        "## Rutas asignadas por electroterminal",
        "",
        conteo.to_markdown(),
        "",
        "## Distancia ruta-electroterminal asignado (km, con factor de desvio ya aplicado)",
        "",
        asignacion["distancia_km"].describe().round(2).to_markdown(),
        "",
        f"Factor de desvio usado: {parametros.FACTOR_DESVIO}.",
        "",
        "## Grafico",
        "- `rutas_por_depot.png`: rutas asignadas por electroterminal.",
        "",
        "*(Generado automaticamente por scripts/4-clustering_nearest.py)*",
    ]
    (RESULTS / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rutas", nargs="*", default=None,
                         help="Checkpoint chico: lista de route_id a incluir.")
    parser.add_argument("--muestra", type=int, default=None,
                         help="Checkpoint chico alternativo: N rutas elegidas al azar (reproducible).")
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args()

    corrida_parcial = bool(args.rutas or args.muestra)
    ex, depots = cargar_datos(args.rutas, args.muestra, args.semilla)
    print(f"--- Rutas a asignar: {ex['route_id'].nunique()} | Electroterminales: {len(depots)} ---")

    dist = distancia_rutas_a_depots(ex, depots, parametros.FACTOR_DESVIO)
    idx = dist.values.argmin(axis=1)
    filas = np.arange(len(dist))

    asignacion = pd.DataFrame({
        "route_id": dist.index,
        "depot_id": depots["depot_id"].astype(str).values[idx],
        "depot_nombre": depots["nombre"].values[idx],
        "distancia_km": dist.values[filas, idx],
    }).reset_index(drop=True)

    print("\n--- Distribucion de rutas por electroterminal ---")
    print(asignacion["depot_nombre"].value_counts().sort_index().to_string())

    print("\n--- Guardando resultados ---")
    out_path = DATA_PROCESSED / "rutas_cluster_c1.csv"
    asignacion.to_csv(out_path, index=False, sep=CSV_SEP)
    print(f"  -> {out_path} ({len(asignacion)} rutas)")

    graficar_rutas_por_depot(asignacion, RESULTS / "rutas_por_depot.png")
    escribir_reporte(asignacion, corrida_parcial)
    print(f"  -> {RESULTS / 'reporte.md'}")

    # --- Chequeos de sanidad ---
    assert asignacion["route_id"].is_unique, "Alguna ruta quedo asignada mas de una vez."
    assert asignacion["depot_id"].notna().all(), "Alguna ruta quedo sin electroterminal asignado."
    assert asignacion["depot_nombre"].nunique() >= min(2, len(depots)), \
        "Todas las rutas quedaron en el mismo electroterminal: revisar la matriz de distancias."
    print("\n  [OK] Chequeos de sanidad pasaron (asignacion unica, sin NaN, mas de un electroterminal usado).")

    if not corrida_parcial and len(asignacion) != RUTAS_ESPERADAS:
        print(f"  [aviso] {len(asignacion)} rutas asignadas, se esperaban {RUTAS_ESPERADAS}.")

    print("\n=== FIN ETAPA 1 (C1) ===")


if __name__ == "__main__":
    main()
