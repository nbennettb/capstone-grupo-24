"""
Etapa 1 (C1) del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md seccion 4 y
docs/Propuesta_metodologia_reunion.md seccion 5).

Dos variantes de la heuristica "electroterminal mas cercano", pensadas para
aislar UN solo cambio entre ellas (no comparar dos cosas que difieren en
mas de un aspecto a la vez):

  C1a - centroide: cada RUTA se asigna al electroterminal mas cercano al
        centroide de sus paraderos terminales (promedio simple de lat/lon).
        Es la version que se uso en la ronda anterior.

  C1b - terminales reales: cada RUTA se asigna al electroterminal que
        minimiza la distancia ESPERADA a sus paraderos terminales REALES
        (no un punto promedio artificial), ponderando cada paradero por
        cuantas expediciones lo usan como origen o destino.

C1a -> C1b cambia SOLO la forma de medir la distancia. La comparacion entre
ambas (bajo el mismo criterio de evaluacion) se hace en
scripts/8-clustering_comparacion.py, junto con C2.

Ninguna de las dos considera capacidad de carga (eso lo hace C2,
scripts/5-clustering_c2.py).

Input:  data-processed/rutas_resumen.csv, terminales_por_ruta.csv,
        terminales.csv, data-filtrado/depots.csv
Output: data-processed/rutas_cluster_c1a.csv, rutas_cluster_c1b.csv
        results/etapa1_clustering/tablas/distancias_ruta_terminal.csv
        results/etapa1_clustering/graficos/distancias.png

Uso:
    python scripts/4-clustering_c1.py
        Corre sobre las 417 rutas.

    python scripts/4-clustering_c1.py --rutas 101 301 516 ...
        Checkpoint chico: corre solo sobre las rutas indicadas.
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
from common import geo, parametros                                            # noqa: E402
from common.clustering import distancia_ponderada_a_terminales_reales         # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa1_clustering")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)

RUTAS_ESPERADAS = 417


def cargar_datos(subset_rutas=None):
    rutas_resumen = pd.read_csv(DATA_PROCESSED / "rutas_resumen.csv", sep=CSV_SEP)
    terminales_por_ruta = pd.read_csv(DATA_PROCESSED / "terminales_por_ruta.csv", sep=CSV_SEP)
    terminales = pd.read_csv(DATA_PROCESSED / "terminales.csv", sep=CSV_SEP)
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)

    rutas_resumen["route_id"] = rutas_resumen["route_id"].astype(str)
    terminales_por_ruta["route_id"] = terminales_por_ruta["route_id"].astype(str)

    if subset_rutas:
        subset_rutas = {str(r) for r in subset_rutas}
        rutas_resumen = rutas_resumen[rutas_resumen["route_id"].isin(subset_rutas)].reset_index(drop=True)
        terminales_por_ruta = terminales_por_ruta[terminales_por_ruta["route_id"].isin(subset_rutas)]

    return rutas_resumen, terminales_por_ruta, terminales, depots


def distancia_c1a(rutas_resumen, depots, factor_desvio):
    """Distancia (rutas x electroterminales) al CENTROIDE de cada ruta,
    ya calculado en la Etapa 0 (rutas_resumen.csv: centroide_lat/lon)."""
    P = geo.xy(rutas_resumen["centroide_lat"].values, rutas_resumen["centroide_lon"].values)
    DP = geo.xy(depots["lat"].values, depots["lon"].values)
    d = geo.matriz_distancias_planas(P, DP) * factor_desvio
    depot_ids = depots["depot_id"].astype(str).values
    return pd.DataFrame(d, index=rutas_resumen["route_id"].values, columns=depot_ids)


def asignar_mas_cercano(dist, depots):
    idx = dist.values.argmin(axis=1)
    filas = np.arange(len(dist))
    return pd.DataFrame({
        "route_id": dist.index,
        "depot_id": depots["depot_id"].astype(str).values[idx],
        "depot_nombre": depots["nombre"].values[idx],
        "distancia_km": dist.values[filas, idx],
    }).reset_index(drop=True)


def graficar_distancias(asig_c1a, asig_c1b, path_png):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(asig_c1a["distancia_km"], bins=30, alpha=0.6, label="C1a (centroide)", color="#2c6e8f")
    ax.hist(asig_c1b["distancia_km"], bins=30, alpha=0.6, label="C1b (terminales reales)", color="#8f4a2c")
    ax.set_xlabel("Distancia al electroterminal asignado (km, con factor de desvio)")
    ax.set_ylabel("Numero de rutas")
    ax.set_title("Distancia ruta -> electroterminal asignado: C1a vs C1b")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rutas", nargs="*", default=None,
                         help="Checkpoint chico: lista de route_id a incluir.")
    args = parser.parse_args()
    corrida_parcial = bool(args.rutas)

    print("=== ETAPA 1 (C1): heuristica del electroterminal mas cercano ===\n")
    rutas_resumen, terminales_por_ruta, terminales, depots = cargar_datos(args.rutas)
    print(f"--- Rutas a asignar: {len(rutas_resumen)} | Electroterminales: {len(depots)} ---")

    print("\n--- C1a: distancia al centroide ---")
    dist_c1a = distancia_c1a(rutas_resumen, depots, parametros.FACTOR_DESVIO)
    asig_c1a = asignar_mas_cercano(dist_c1a, depots)
    print(asig_c1a["depot_nombre"].value_counts().sort_index().to_string())

    print("\n--- C1b: distancia ponderada a paraderos terminales reales ---")
    dist_c1b = distancia_ponderada_a_terminales_reales(terminales_por_ruta, terminales, depots,
                                                         parametros.FACTOR_DESVIO)
    dist_c1b = dist_c1b.loc[rutas_resumen["route_id"].values]
    asig_c1b = asignar_mas_cercano(dist_c1b, depots)
    print(asig_c1b["depot_nombre"].value_counts().sort_index().to_string())

    cambian = (asig_c1a.set_index("route_id")["depot_id"] != asig_c1b.set_index("route_id")["depot_id"]).sum()
    print(f"\n--- Rutas que cambian de electroterminal entre C1a y C1b: {cambian} de {len(rutas_resumen)} ---")

    print("\n--- Guardando resultados ---")
    out_c1a = DATA_PROCESSED / "rutas_cluster_c1a.csv"
    out_c1b = DATA_PROCESSED / "rutas_cluster_c1b.csv"
    asig_c1a.to_csv(out_c1a, index=False, sep=CSV_SEP)
    asig_c1b.to_csv(out_c1b, index=False, sep=CSV_SEP)
    print(f"  -> {out_c1a} ({len(asig_c1a)} rutas)")
    print(f"  -> {out_c1b} ({len(asig_c1b)} rutas)")

    tabla_dist = pd.concat([
        asig_c1a[["distancia_km"]].describe().round(2).rename(columns={"distancia_km": "C1a_centroide"}),
        asig_c1b[["distancia_km"]].describe().round(2).rename(columns={"distancia_km": "C1b_terminales"}),
    ], axis=1)
    tabla_dist.to_csv(TABLAS / "distancias_ruta_terminal.csv", sep=CSV_SEP)
    print(f"  -> {TABLAS / 'distancias_ruta_terminal.csv'}")

    graficar_distancias(asig_c1a, asig_c1b, GRAFICOS / "distancias.png")
    print(f"  -> {GRAFICOS / 'distancias.png'}")

    # --- Chequeos de sanidad ---
    for etiqueta, asignacion in [("C1a", asig_c1a), ("C1b", asig_c1b)]:
        assert asignacion["route_id"].is_unique, f"{etiqueta}: alguna ruta quedo asignada mas de una vez."
        assert asignacion["depot_id"].notna().all(), f"{etiqueta}: alguna ruta quedo sin electroterminal."
        assert asignacion["depot_nombre"].nunique() >= min(2, len(depots)), \
            f"{etiqueta}: todas las rutas quedaron en el mismo electroterminal."
    print("\n  [OK] Chequeos de sanidad pasaron (asignacion unica, sin NaN, mas de un electroterminal usado).")

    if not corrida_parcial and len(asig_c1a) != RUTAS_ESPERADAS:
        print(f"  [aviso] {len(asig_c1a)} rutas asignadas, se esperaban {RUTAS_ESPERADAS}.")

    print("\n=== FIN ETAPA 1 (C1) ===")


if __name__ == "__main__":
    main()
