"""
Etapa 1 (cierre) del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md seccion 4).

Junta las tres asignaciones ya generadas por scripts/4-clustering_c1.py
(C1a, C1b) y scripts/5-clustering_c2.py (C2, bajo ciclo diario):
  - Las compara bajo un CRITERIO COMUN (distancia esperada a los paraderos
    terminales reales de cada ruta, la misma metrica de C1b/C2), para que
    la comparacion sea justa aunque C1a haya decidido con otra metrica
    (el centroide).
  - Arma una tabla ancha por ruta (una fila, todas las estrategias) para
    revisar a mano en Excel.
  - Genera los mapas: uno por estrategia, uno por electroterminal, el mapa
    de paraderos terminales, y el mapa de diferencias entre C1b (el mas
    cercano) y C2 (el mismo criterio, mas la capacidad): las rutas que la
    capacidad obliga a mover.
  - Escribe el reporte final de la Etapa 1 (resultado que se lleva a la
    reunion con el grupo y el profesor).

Input:  data-processed/rutas_cluster_{c1a,c1b,c2}.csv,
        rutas_resumen.csv, terminales_por_ruta.csv, terminales.csv,
        data-filtrado/{depots,trips_dia_L,shapes_bus}.csv,
        data-alumnos/chile.gpkg (fondo geografico, capa de comunas)
        results/etapa1_clustering/tablas/{capacidad_por_terminal,capacidad_sin_vs_con_recuperacion,
            barrido_theta}.csv (generados por 5)
Output: data-processed/rutas_clustering_completo.csv
        results/etapa1_clustering/tablas/{resumen_por_terminal,
            comparacion_estrategias,rutas_que_cambian}.csv
        results/etapa1_clustering/graficos/rutas_por_terminal.png
        results/etapa1_clustering/mapas/*.png
        results/etapa1_clustering/reporte.md

Uso:
    python scripts/8-clustering_comparacion.py
        Requiere haber corrido antes 4-clustering_c1.py y 5-clustering_c2.py
        sobre la red completa (417 rutas).
"""

import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import geo, parametros                                            # noqa: E402
from common.clustering import distancia_ponderada_a_terminales_reales         # noqa: E402
from common.rutas import DATA_ALUMNOS, DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa1_clustering")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
MAPAS = RESULTS / "mapas"
for _d in (TABLAS, GRAFICOS, MAPAS):
    _d.mkdir(exist_ok=True)

RUTAS_ESPERADAS = 417
NOMBRE_UNIDO = "Los Espinos + Santa Rosa"
ESTRATEGIAS = ["c1a", "c1b", "c2"]
NOMBRES_ESTRATEGIA = {
    "c1a": "C1a (centroide)",
    "c1b": "C1b (terminales reales)",
    "c2": "C2 (MILP con capacidad, ciclo diario)",
}
COLORES_DEPOT = {  # paleta fija para que el color de un electroterminal sea el mismo en todos los mapas
    "Vespucio Norte": "#1b9e77",
    "El Conquistador": "#d95f02",
    "Los Espinos": "#7570b3",
    "La Reina": "#e7298a",
    "Santa Rosa": "#66a61e",
}
BBOX_MAPA = (-70.95, -33.72, -70.47, -33.28)  # RM urbana, con margen sobre los paraderos terminales


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #

def cargar_asignaciones():
    asignaciones = {}
    for etq in ESTRATEGIAS:
        path = DATA_PROCESSED / f"rutas_cluster_{etq}.csv"
        if not path.exists():
            raise SystemExit(f"No se encontro {path}. Correr antes: scripts/4-clustering_c1.py "
                              f"y scripts/5-clustering_c2.py sobre la red completa.")
        df = pd.read_csv(path, sep=CSV_SEP)
        df["route_id"] = df["route_id"].astype(str)
        df["depot_id"] = df["depot_id"].astype(str)
        asignaciones[etq] = df.set_index("route_id")[["depot_id", "depot_nombre"]]
    return asignaciones


def cargar_geometria_rutas():
    """Un LineString por shape_id (trazado GTFS), unido a route_id. Una
    ruta puede tener varios shapes (ida, vuelta, variantes) -- se dibujan
    todos, coloreados igual, para mostrar el trazado real completo."""
    shapes = pd.read_csv(DATA_FILTRADO / "shapes_bus.csv", sep=CSV_SEP)
    shapes = shapes.sort_values(["shape_id", "shape_pt_sequence"])
    trips = pd.read_csv(DATA_FILTRADO / "trips_dia_L.csv", sep=CSV_SEP, dtype=str,
                         usecols=["route_id", "shape_id"]).drop_duplicates()

    def a_linea(g):
        return LineString(zip(g["shape_pt_lon"], g["shape_pt_lat"])) if len(g) >= 2 else None

    geoms = shapes.groupby("shape_id").apply(a_linea, include_groups=False)
    gdf = gpd.GeoDataFrame({"shape_id": geoms.index.values, "geometry": geoms.values}, crs="EPSG:4326")
    gdf = gdf.dropna(subset=["geometry"]).merge(trips, on="shape_id", how="left")
    gdf["route_id"] = gdf["route_id"].astype(str)
    return gdf.dropna(subset=["route_id"])


def cargar_fondo_comunas():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return gpd.read_file(DATA_ALUMNOS / "chile.gpkg", layer="gis_osm_adminareas_a_free", bbox=BBOX_MAPA)


# --------------------------------------------------------------------------- #
# Comparacion bajo criterio comun
# --------------------------------------------------------------------------- #

def construir_comparacion(asignaciones, rutas_resumen, dist_comun, depots):
    """Evalua las 3 estrategias con la MISMA metrica de distancia (a
    paraderos terminales reales), sin importar con que metrica decidio
    cada una. Compararlas con sus propias metricas seria injusto: C1a
    reportaria una distancia mas chica solo porque mide distinto, no
    porque asigne mejor."""
    filas = []
    n_buses = rutas_resumen.set_index("route_id")["n_buses_estimados"]
    costo_km = parametros.cargar_costos().cost_per_km

    for etq, asign in asignaciones.items():
        # distancia de cada ruta a SU electroterminal asignado, leida de la matriz comun
        dist_asignada = np.array([dist_comun.loc[r, asign.loc[r, "depot_id"]] for r in dist_comun.index])
        costo = 2 * dist_asignada * costo_km * n_buses.loc[dist_comun.index].values
        filas.append({
            "estrategia": NOMBRES_ESTRATEGIA[etq],
            "distancia_media_km": round(dist_asignada.mean(), 3),
            "distancia_p90_km": round(np.percentile(dist_asignada, 90), 3),
            "distancia_max_km": round(dist_asignada.max(), 3),
            "costo_pullout_pullin_usd_dia": round(costo.sum(), 0),
            "rutas_distintas_de_c1b": int((asign["depot_id"] != asignaciones["c1b"]["depot_id"]).sum()),
        })
    return pd.DataFrame(filas)


def construir_resumen_por_terminal(asignaciones, rutas_resumen):
    rr = rutas_resumen.set_index("route_id")
    filas = []
    for etq, asign in asignaciones.items():
        j = asign.join(rr[["n_buses_estimados", "km_dia", "kwh_dia"]])
        g = j.groupby("depot_nombre").agg(n_rutas=("depot_id", "size"), n_buses=("n_buses_estimados", "sum"),
                                           km_dia=("km_dia", "sum"), kwh_dia=("kwh_dia", "sum"))
        g.insert(0, "estrategia", NOMBRES_ESTRATEGIA[etq])
        filas.append(g.reset_index())
    return pd.concat(filas, ignore_index=True).round(1)


def construir_rutas_que_cambian(asignaciones):
    pares = [("c1a", "c1b"), ("c1b", "c2")]
    filas = []
    for a, b in pares:
        da, db = asignaciones[a], asignaciones[b]
        comunes = da.index.intersection(db.index)
        distintas = comunes[da.loc[comunes, "depot_id"].values != db.loc[comunes, "depot_id"].values]
        for r in distintas:
            filas.append({"route_id": r, "comparacion": f"{a} -> {b}",
                          "depot_desde": da.loc[r, "depot_nombre"], "depot_hacia": db.loc[r, "depot_nombre"]})
    return pd.DataFrame(filas)


def construir_tabla_ancha(asignaciones, rutas_resumen, dist_comun, depots, h_comercial, h_asignada_c2):
    ancha = rutas_resumen.set_index("route_id").copy()
    ancha = ancha.join(pd.DataFrame({"h_r_comercial_horas_cargador": h_comercial,
                                      "h_r_asignada_c2_horas_cargador": h_asignada_c2}, index=rutas_resumen["route_id"]))

    for nombre_col, depot_id in zip(depots["nombre"], depots["depot_id"].astype(str)):
        ancha[f"dist_km_a_{nombre_col.replace(' ', '_')}"] = dist_comun[depot_id].reindex(ancha.index)

    for etq, asign in asignaciones.items():
        ancha[f"depot_{etq}"] = asign["depot_nombre"].reindex(ancha.index)

    ancha["cambia_c1a_c1b"] = ancha["depot_c1a"] != ancha["depot_c1b"]
    ancha["cambia_c1b_c2"] = ancha["depot_c1b"] != ancha["depot_c2"]
    return ancha.reset_index().round(3)


# --------------------------------------------------------------------------- #
# Graficos y mapas
# --------------------------------------------------------------------------- #

def graficar_rutas_por_terminal(asignaciones, path_png):
    conteos = {etq: asign["depot_nombre"].value_counts() for etq, asign in asignaciones.items()}
    tabla = pd.DataFrame(conteos).fillna(0)
    tabla.columns = [NOMBRES_ESTRATEGIA[c] for c in tabla.columns]
    tabla = tabla.sort_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(tabla))
    ancho = 0.8 / len(tabla.columns)
    for i, col in enumerate(tabla.columns):
        ax.bar(x + i * ancho, tabla[col], width=ancho, label=col)
    ax.set_xticks(x + ancho * (len(tabla.columns) - 1) / 2)
    ax.set_xticklabels(tabla.index, rotation=20, ha="right")
    ax.set_ylabel("Numero de rutas asignadas")
    ax.set_title("Rutas por electroterminal, las 3 estrategias")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_mapa_estrategia(geom_rutas, asignacion, comunas, depots, titulo, path_png):
    fig, ax = plt.subplots(figsize=(9, 9))
    comunas.plot(ax=ax, facecolor="#f2f2f2", edgecolor="#cfcfcf", linewidth=0.5, zorder=0)

    g = geom_rutas.merge(asignacion.reset_index(), on="route_id", how="inner")
    for nombre, grupo in g.groupby("depot_nombre"):
        gpd.GeoDataFrame(grupo).plot(ax=ax, color=COLORES_DEPOT.get(nombre, "#333333"), linewidth=0.6,
                                       alpha=0.75, label=nombre, zorder=1)

    ax.scatter(depots["lon"], depots["lat"], s=depots["capacity"] * 1.5, c="black", marker="^",
               zorder=3, label="Electroterminal (tamaño = capacidad)")
    ax.set_xlim(BBOX_MAPA[0], BBOX_MAPA[2])
    ax.set_ylim(BBOX_MAPA[1], BBOX_MAPA[3])
    ax.set_title(titulo)
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_mapa_por_terminal(geom_rutas, asignacion, comunas, depots, path_dir):
    for _, dep in depots.iterrows():
        nombre = dep["nombre"]
        rutas_dep = asignacion[asignacion["depot_nombre"] == nombre].index
        g = geom_rutas[geom_rutas["route_id"].isin(rutas_dep)]

        fig, ax = plt.subplots(figsize=(8, 8))
        comunas.plot(ax=ax, facecolor="#f2f2f2", edgecolor="#cfcfcf", linewidth=0.5, zorder=0)
        gpd.GeoDataFrame(g).plot(ax=ax, color=COLORES_DEPOT.get(nombre, "#333333"), linewidth=0.7,
                                   alpha=0.8, zorder=1)
        ax.scatter([dep["lon"]], [dep["lat"]], s=dep["capacity"] * 2, c="black", marker="^", zorder=3)
        ax.set_xlim(BBOX_MAPA[0], BBOX_MAPA[2])
        ax.set_ylim(BBOX_MAPA[1], BBOX_MAPA[3])
        ax.set_title(f"{nombre}: {len(rutas_dep)} rutas asignadas (C2, ciclo diario)")
        ax.set_xticks([]); ax.set_yticks([])
        fig.tight_layout()
        nombre_archivo = nombre.lower().replace(" ", "_")
        fig.savefig(path_dir / f"mapa_terminal_{nombre_archivo}.png", dpi=150)
        plt.close(fig)


def graficar_mapa_paraderos(terminales, depots, comunas, path_png):
    DP = geo.xy(depots["lat"].values, depots["lon"].values)
    P = geo.xy(terminales["lat"].values, terminales["lon"].values)
    d = geo.matriz_distancias_planas(P, DP)
    idx = d.argmin(axis=1)
    terminales = terminales.copy()
    terminales["depot_nombre"] = depots["nombre"].values[idx]

    fig, ax = plt.subplots(figsize=(9, 9))
    comunas.plot(ax=ax, facecolor="#f2f2f2", edgecolor="#cfcfcf", linewidth=0.5, zorder=0)
    for nombre, grupo in terminales.groupby("depot_nombre"):
        ax.scatter(grupo["lon"], grupo["lat"], s=6, color=COLORES_DEPOT.get(nombre, "#333333"),
                   alpha=0.7, label=nombre)
    ax.scatter(depots["lon"], depots["lat"], s=depots["capacity"] * 1.5, c="black", marker="^", zorder=3)
    ax.set_xlim(BBOX_MAPA[0], BBOX_MAPA[2])
    ax.set_ylim(BBOX_MAPA[1], BBOX_MAPA[3])
    ax.set_title("641 paraderos terminales, coloreados por electroterminal mas cercano")
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_mapa_diferencias(geom_rutas, asig_ref, asig_c2, comunas, depots, path_png):
    comunes = asig_ref.index.intersection(asig_c2.index)
    distintas = comunes[asig_ref.loc[comunes, "depot_id"].values != asig_c2.loc[comunes, "depot_id"].values]

    fig, ax = plt.subplots(figsize=(9, 9))
    comunas.plot(ax=ax, facecolor="#f2f2f2", edgecolor="#cfcfcf", linewidth=0.5, zorder=0)

    g_todas = geom_rutas[~geom_rutas["route_id"].isin(distintas)]
    gpd.GeoDataFrame(g_todas).plot(ax=ax, color="#d9d9d9", linewidth=0.4, zorder=1)
    g_cambia = geom_rutas[geom_rutas["route_id"].isin(distintas)]
    gpd.GeoDataFrame(g_cambia).plot(ax=ax, color="#e41a1c", linewidth=1.1, zorder=2,
                                      label=f"Cambia de electroterminal ({len(distintas)} rutas)")

    ax.scatter(depots["lon"], depots["lat"], s=depots["capacity"] * 1.5, c="black", marker="^", zorder=3)
    ax.set_xlim(BBOX_MAPA[0], BBOX_MAPA[2])
    ax.set_ylim(BBOX_MAPA[1], BBOX_MAPA[3])
    ax.set_title("Rutas que la capacidad obliga a mover: C1b (mas cercano) -> C2 (con capacidad, theta = 1)")
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)
    return distintas


# --------------------------------------------------------------------------- #
# Reporte
# --------------------------------------------------------------------------- #

def escribir_reporte(comparacion, resumen_terminal, capacidad, validacion, evidencia, barrido_theta,
                      n_diferencias_mapa):
    uso_max = capacidad[capacidad["electroterminal"] != NOMBRE_UNIDO].sort_values("uso_pct").iloc[-1]
    tot = evidencia[evidencia["electroterminal"] == "TOTAL"]
    resumen_recup = (tot.pivot(index="nivel_soc_pct", columns="supuesto",
                               values=["h_cargador_dia", "uso_pct"]).sort_index(ascending=False))
    resumen_recup.columns = [f"{m} - {s}" for m, s in resumen_recup.columns]
    resumen_recup = resumen_recup.reset_index()
    nivel0 = int(tot["nivel_soc_pct"].max())
    t0 = tot[tot["nivel_soc_pct"] == nivel0].set_index("supuesto")
    lineas = [
        "# Reporte Etapa 1 - Clustering de rutas a electroterminales (ciclo diario)",
        "",
        "**C1b** (el electroterminal mas cercano a los paraderos terminales reales de cada ruta) es la asignacion "
        "base de la entrega y se llama simplemente 'C1' en el relato. **C1a** (distancia al centroide) es un control "
        "de sensibilidad: no la usa ninguna etapa posterior. **C2** (MILP con capacidad bajo la condicion ciclica) "
        "es la **propuesta** que se formula y se prueba, pero no entra al caso base.",
        "",
        "## Comparacion bajo criterio comun (distancia a paraderos terminales reales)",
        "",
        comparacion.to_markdown(index=False),
        "",
        "## Capacidad bajo ciclo diario (theta = 1, H = 24 h)",
        "",
        capacidad.round(1).to_markdown(index=False),
        "",
        "La carga de cada ruta incluye su pullout y pullin (depende del electroterminal): ver "
        "`tablas/validacion_carga_c2.csv`. Con esa carga, la asignacion C1b (mas cercano, sin capacidad) "
        f"excede la capacidad donde `uso_c1b_con_carga_corregida_pct` pasa de 100%; C2 mueve "
        f"{n_diferencias_mapa} rutas para respetarla (uso maximo de C2: {uso_max['uso_pct']:.1f}% en "
        f"{uso_max['electroterminal']}).",
        "- C2 ve un promedio diario en horas-cargador; la carga real se concentra en ciertas horas, y esa "
        "saturacion horaria la mide el simulador de carga reactiva (colas de espera), no C2.",
        "",
        "## Validacion del estimador de carga contra la energia real de las jornadas (asignacion C1b)",
        "",
        validacion.to_markdown(index=False) if len(validacion) else "(sin jornadas del VSP para validar)",
        "",
        "## Barrido de theta (rutas movidas respecto de C2 con theta = 1)",
        "",
        barrido_theta.to_markdown(index=False),
        "",
        "Capacidad `separada` = una restriccion por electroterminal; `combinada` = Los Espinos y Santa "
        "Rosa comparten una bolsa de 270 puestos. Las rutas movidas se miden contra la asignacion con "
        "theta = 1. Es evidencia secundaria: el efecto real de unir esos dos terminales esta en el "
        "interlining (Etapa 2, E1 frente a E1_sep) y en la carga (Etapa 3).",
        "",
        "## Evidencia: sin recuperacion vs con recuperacion, al mismo nivel (proxy por ruta, sin deadhead)",
        "",
        "Sin recuperacion: los buses parten con el nivel indicado y no lo recuperan al terminar (solo "
        "se paga el excedente sobre la bateria util). Con recuperacion: condicion ciclica, se paga todo "
        "lo consumido. Totales de los 5 electroterminales (detalle por electroterminal en "
        "`tablas/capacidad_sin_vs_con_recuperacion.csv`):",
        "",
        resumen_recup.round(2).to_markdown(index=False),
        "",
        f"- Al nivel {nivel0}% (el maximo de los datos), sin recuperacion solo se recargarian "
        f"{t0.loc['Sin recuperacion', 'mwh_a_recargar']:,.0f} MWh de "
        f"{t0.loc['Con recuperacion (ciclo)', 'mwh_a_recargar']:,.0f} MWh consumidos, y los puestos "
        f"usarian {t0.loc['Sin recuperacion', 'uso_pct']:.1f}% de su capacidad (con recuperacion: "
        f"{t0.loc['Con recuperacion (ciclo)', 'uso_pct']:.1f}%).",
        "- Con recuperacion, la energia a recargar y la asignacion de C2 no dependen del nivel: el nivel "
        "solo cambia cuantas jornadas recargan a mitad del dia, y eso se mide en el barrido de niveles "
        "con el simulador de carga reactiva (el nivel base lo elige el costo total, ver "
        "docs/context/02_supuestos_y_decisiones.md, B6).",
        "- Estas cifras son un PROXY POR RUTA (kWh comerciales, sin pullout/pullin). La medicion por "
        "jornada se produce en la Etapa 2, con las jornadas regeneradas.",
        "",
        "## Rutas por electroterminal, por estrategia",
        "",
        resumen_terminal.pivot(index="depot_nombre", columns="estrategia", values="n_rutas").to_markdown(),
        "",
        f"## Rutas que la capacidad obliga a mover, de C1b a C2 (mapa de diferencias): {n_diferencias_mapa}",
        "",
        "## Indice de esta carpeta",
        "",
        "Tablas (`tablas/`):",
        "- `comparacion_estrategias.csv`: distancia y costo de pullout/pullin de C1a, C1b y C2 bajo el mismo criterio.",
        "- `resumen_por_terminal.csv`: rutas, buses estimados, km y kWh por electroterminal y estrategia.",
        "- `rutas_que_cambian.csv`: cada ruta que cambia de electroterminal entre estrategias.",
        "- `distancias_ruta_terminal.csv`: distancia de cada ruta a cada electroterminal (centroide y paraderos reales).",
        "- `capacidad_por_terminal.csv`: horas-cargador asignadas vs capacidad, bajo ciclo diario, y el uso que tendria la asignacion C1b con la misma carga (incluye la fila combinada Los Espinos + Santa Rosa).",
        "- `validacion_carga_c2.csv`: energia por electroterminal estimada por C2 vs la real de las jornadas del VSP.",
        "- `capacidad_sin_vs_con_recuperacion.csv`: sin recuperacion vs con recuperacion al mismo nivel de bateria (proxy por ruta).",
        "- `barrido_theta.csv`: rutas movidas y uso maximo al apretar la capacidad, separada y combinada.",
        "",
        "Graficos (`graficos/`):",
        "- `rutas_por_terminal.png`: rutas por electroterminal en las 3 estrategias.",
        "- `distancias.png`: distancias ruta-electroterminal (C1a vs C1b).",
        "- `capacidad_ciclo.png`: carga asignada vs capacidad bajo ciclo diario.",
        "- `capacidad_sin_vs_con_recuperacion.png`: uso de capacidad sin vs con recuperacion, por electroterminal y segun el nivel.",
        "- `barrido_theta.png`: rutas movidas y uso maximo segun theta.",
        "",
        "Mapas (`mapas/`): `mapa_c1a.png`, `mapa_c1b.png`, `mapa_c2.png` (rutas coloreadas por electroterminal), "
        "`mapa_terminal_<nombre>.png` (x5, rutas de cada electroterminal bajo C2), "
        "`mapa_paraderos_terminales.png` (641 paraderos por electroterminal mas cercano) y "
        "`mapa_diferencias.png` (rutas que cambian de C1b a C2: las que la capacidad obliga a mover).",
        "",
        "Tabla ancha por ruta: `data-processed/rutas_clustering_completo.csv`.",
        "",
        "*(Ver docs/context/01_metodologia.md para la interpretacion completa y las "
        "decisiones que este resultado habilita o deja pendientes.)*",
    ]
    (RESULTS / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")


def main():
    print("=== ETAPA 1 (cierre): comparacion, tabla ancha y mapas ===\n")

    asignaciones = cargar_asignaciones()
    for etq, a in asignaciones.items():
        if len(a) != RUTAS_ESPERADAS:
            print(f"  [aviso] {etq}: {len(a)} rutas (se esperaban {RUTAS_ESPERADAS}). "
                  f"¿Se corrieron 4 y 5 sobre la red completa?")

    rutas_resumen = pd.read_csv(DATA_PROCESSED / "rutas_resumen.csv", sep=CSV_SEP)
    rutas_resumen["route_id"] = rutas_resumen["route_id"].astype(str)
    terminales_por_ruta = pd.read_csv(DATA_PROCESSED / "terminales_por_ruta.csv", sep=CSV_SEP)
    terminales_por_ruta["route_id"] = terminales_por_ruta["route_id"].astype(str)
    terminales = pd.read_csv(DATA_PROCESSED / "terminales.csv", sep=CSV_SEP)
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    depots["depot_id"] = depots["depot_id"].astype(str)
    costos = parametros.cargar_costos()

    print("--- Calculando distancia comun (paraderos terminales reales) ---")
    dist_comun = distancia_ponderada_a_terminales_reales(terminales_por_ruta, terminales, depots,
                                                            parametros.FACTOR_DESVIO)
    dist_comun = dist_comun.loc[rutas_resumen["route_id"].values]

    h_comercial = rutas_resumen.set_index("route_id")["kwh_dia"] / costos.charge_power_kw
    h_asignada_c2 = (pd.read_csv(DATA_PROCESSED / "rutas_cluster_c2.csv", sep=CSV_SEP, dtype={"route_id": str})
                     .set_index("route_id")["h_r_horas_cargador"].reindex(h_comercial.index))

    print("--- Comparacion bajo criterio comun ---")
    comparacion = construir_comparacion(asignaciones, rutas_resumen, dist_comun, depots)
    print(comparacion.to_string(index=False))
    comparacion.to_csv(TABLAS / "comparacion_estrategias.csv", index=False, sep=CSV_SEP)

    print("\n--- Resumen por terminal, las 3 estrategias ---")
    resumen_terminal = construir_resumen_por_terminal(asignaciones, rutas_resumen)
    resumen_terminal.to_csv(TABLAS / "resumen_por_terminal.csv", index=False, sep=CSV_SEP)

    print("--- Rutas que cambian entre pares de estrategias ---")
    rutas_que_cambian = construir_rutas_que_cambian(asignaciones)
    rutas_que_cambian.to_csv(TABLAS / "rutas_que_cambian.csv", index=False, sep=CSV_SEP)
    print(f"  {len(rutas_que_cambian)} cambios registrados en total (sumando los 2 pares comparados)")

    print("\n--- Tabla ancha por ruta ---")
    ancha = construir_tabla_ancha(asignaciones, rutas_resumen, dist_comun, depots, h_comercial, h_asignada_c2)
    ancha.to_csv(DATA_PROCESSED / "rutas_clustering_completo.csv", index=False, sep=CSV_SEP)
    print(f"  -> {DATA_PROCESSED / 'rutas_clustering_completo.csv'} ({len(ancha)} filas)")

    print("\n--- Graficos ---")
    graficar_rutas_por_terminal(asignaciones, GRAFICOS / "rutas_por_terminal.png")
    print(f"  -> {GRAFICOS / 'rutas_por_terminal.png'}")

    print("\n--- Cargando geometria (trazados GTFS + fondo de comunas) ---")
    geom_rutas = cargar_geometria_rutas()
    comunas = cargar_fondo_comunas()
    print(f"  {geom_rutas['route_id'].nunique()} rutas con trazado, {len(comunas)} comunas de fondo")

    print("\n--- Mapas ---")
    for etq in ESTRATEGIAS:
        graficar_mapa_estrategia(geom_rutas, asignaciones[etq], comunas, depots,
                                  f"Clustering de rutas a electroterminales -- {NOMBRES_ESTRATEGIA[etq]}",
                                  MAPAS / f"mapa_{etq}.png")
        print(f"  -> {MAPAS / f'mapa_{etq}.png'}")

    graficar_mapa_por_terminal(geom_rutas, asignaciones["c2"], comunas, depots, MAPAS)
    print(f"  -> {MAPAS}/mapa_terminal_<nombre>.png (x{len(depots)})")

    graficar_mapa_paraderos(terminales, depots, comunas, MAPAS / "mapa_paraderos_terminales.png")
    print(f"  -> {MAPAS / 'mapa_paraderos_terminales.png'}")

    n_diferencias_mapa = len(graficar_mapa_diferencias(geom_rutas, asignaciones["c1b"], asignaciones["c2"],
                                                          comunas, depots, MAPAS / "mapa_diferencias.png"))
    print(f"  -> {MAPAS / 'mapa_diferencias.png'} ({n_diferencias_mapa} rutas resaltadas)")

    print("\n--- Reporte final ---")
    capacidad = pd.read_csv(TABLAS / "capacidad_por_terminal.csv", sep=CSV_SEP)
    evidencia = pd.read_csv(TABLAS / "capacidad_sin_vs_con_recuperacion.csv", sep=CSV_SEP)
    barrido_theta = pd.read_csv(TABLAS / "barrido_theta.csv", sep=CSV_SEP)
    val_path = TABLAS / "validacion_carga_c2.csv"
    validacion = pd.read_csv(val_path, sep=CSV_SEP) if val_path.exists() else pd.DataFrame()
    escribir_reporte(comparacion, resumen_terminal, capacidad, validacion, evidencia, barrido_theta,
                      n_diferencias_mapa)
    print(f"  -> {RESULTS / 'reporte.md'}")

    # --- Chequeos de sanidad ---
    for etq, asign in asignaciones.items():
        assert asign.index.is_unique, f"{etq}: alguna ruta aparece mas de una vez."
    assert (capacidad.loc[capacidad["electroterminal"] != NOMBRE_UNIDO, "uso_pct"] <= 100.0 + 1e-6).all(), \
        "C2 deja algun electroterminal sobre su capacidad (ver tablas/capacidad_por_terminal.csv)."
    assert n_diferencias_mapa == int(comparacion.loc[comparacion.estrategia == NOMBRES_ESTRATEGIA["c2"],
                                                     "rutas_distintas_de_c1b"].iloc[0]), \
        "El mapa de diferencias C1b -> C2 no calza con la tabla de comparacion."
    assert set(ancha["route_id"]) == set(rutas_resumen["route_id"]), \
        "La tabla ancha no tiene las mismas rutas que rutas_resumen.csv."
    print("\n  [OK] Chequeos de sanidad pasaron (asignaciones unicas, capacidad de C2 respetada, tabla ancha completa).")

    print("\n=== FIN ETAPA 1 ===")


if __name__ == "__main__":
    main()
