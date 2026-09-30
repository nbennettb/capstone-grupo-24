"""
Etapa 0 del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia_y_avance.md seccion 1 para el lugar de
esta etapa dentro de la metodologia de 4 etapas aprobada el 28/09/2026).

Expande frequencies_dia_L.csv a expediciones reales (una fila por salida
individual de bus) y calcula, para cada una, duracion, distancia y energia
necesaria. Continua el pipeline de scripts/1-filtro_datos_buses.py y
scripts/2-filtro_tipo_dia.py.

Ademas de expediciones.csv y terminales.csv (que ya existian), esta version
agrega tres tablas por RUTA que sirven de insumo directo a la Etapa 1
(scripts/4-clustering_c1.py y 5-clustering_c2.py) sin depender de la Etapa 2:
  - rutas_resumen.csv: buses estimados, km/dia y kWh/dia por ruta.
  - rutas_ida_vuelta.csv: que tan cerca termina la ida de donde empieza la
    vuelta (el argumento de por que se clusteriza por ruta y no por
    expedicion individual, ver Propuesta_metodologia_reunion.md seccion 5).
  - terminales_por_ruta.csv: que paraderos usa cada ruta como origen/destino.

Input:  data-filtrado/{trips_dia_L, stop_times_dia_L, frequencies_dia_L,
                       shape_distances_bus, stops_bus}.csv
Output: data-processed/expediciones.csv       (una fila por expedicion)
        data-processed/terminales.csv         (paraderos unicos usados como
                                                origen/destino, con coordenadas)
        data-processed/rutas_resumen.csv      (una fila por ruta)
        data-processed/rutas_ida_vuelta.csv   (rutas con ida y vuelta)
        data-processed/terminales_por_ruta.csv (pares ruta x paradero)
        results/etapa0_preprocesamiento/      (reporte, tablas y graficos)

Uso:
    python scripts/3-preprocesamiento_expediciones.py
        Corre sobre la red completa (417 rutas, ~64.502 expediciones
        esperadas).

    python scripts/3-preprocesamiento_expediciones.py --rutas 101 102
        Checkpoint chico: corre solo sobre las rutas indicadas, para
        revisar a mano que expediciones/horarios/energia tengan sentido
        antes de correr la red completa. No se comparan las cifras contra
        las de la red completa.
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
from common import geo, parametros                               # noqa: E402
from common.clustering import centroides_por_ruta                # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402
from common.tiempo import time_to_min, expandir_frecuencias      # noqa: E402

RESULTS = carpeta_resultados("etapa0_preprocesamiento")
GRAFICOS = RESULTS / "graficos"
GRAFICOS.mkdir(exist_ok=True)

# Cifras de referencia de la red completa (Informe 1 / prototipo del
# 28/09), usadas como chequeo de sanidad, no como valor forzado.
EXPEDICIONES_ESPERADAS = 64502
RUTAS_ESPERADAS = 417
CONCURRENCIA_ESPERADA = 6539
HORA_PEAK_ESPERADA = 8.0
UMBRAL_IDA_VUELTA_M = 500.0


# --------------------------------------------------------------------------- #
# Carga y calculo de viajes/expediciones (igual que antes, mas registro de
# descartes para que quede trazable en results/, no solo en el log)
# --------------------------------------------------------------------------- #

def cargar_datos():
    print("--- Cargando data-filtrado/ ---")
    trips = pd.read_csv(DATA_FILTRADO / "trips_dia_L.csv", sep=CSV_SEP, dtype=str)
    stop_times = pd.read_csv(DATA_FILTRADO / "stop_times_dia_L.csv", sep=CSV_SEP, dtype=str)
    # stop_sequence debe ser numerico: si se deja como texto, "10" ordena antes
    # que "2" y corrompe el calculo de paradero de origen/destino (first/last
    # tras sort_values) en cualquier viaje con mas de 9 paraderos.
    stop_times["stop_sequence"] = stop_times["stop_sequence"].astype(int)
    frequencies = pd.read_csv(DATA_FILTRADO / "frequencies_dia_L.csv", sep=CSV_SEP, dtype=str)
    shape_dist = pd.read_csv(DATA_FILTRADO / "shape_distances_bus.csv", sep=CSV_SEP)
    stops = pd.read_csv(DATA_FILTRADO / "stops_bus.csv", sep=CSV_SEP)
    print(f"  trips_dia_L: {len(trips)} | stop_times_dia_L: {len(stop_times)} | "
          f"frequencies_dia_L: {len(frequencies)} | stops_bus: {len(stops)}")
    return trips, stop_times, frequencies, shape_dist, stops


def calcular_viajes(trips, stop_times, shape_dist, descartes):
    """Un viaje (trip_id) = un patron GTFS. Calcula su duracion, paradero
    de origen/destino y distancia recorrida (via shape_id).

    direccion se deriva del propio trip_id (convencion "<ruta>-<I|R>-...",
    ya usada en la ronda anterior) y se valida contra direction_id (campo
    numerico real de trips_dia_L.csv, 0/1): si alguna vez no coinciden, se
    reporta el conteo en descartes.csv en vez de fallar en silencio, porque
    "direccion" se usa en toda la Etapa 1 para decidir que es ida y que es
    vuelta de una misma ruta.
    """
    st = stop_times.copy()
    st["t_min"] = time_to_min(st["arrival_time"])
    st = st.sort_values(["trip_id", "stop_sequence"])
    g = st.groupby("trip_id")
    resumen = pd.DataFrame({
        "dur_min": g["t_min"].max() - g["t_min"].min(),
        "o_stop": g["stop_id"].first(),
        "d_stop": g["stop_id"].last(),
    })
    out = trips.merge(resumen, left_on="trip_id", right_index=True, how="inner")
    out = out.merge(shape_dist, on="shape_id", how="left")
    out["direccion"] = out["trip_id"].str.split("-").str[1]

    direccion_desde_id = out["direction_id"].map({"0": "I", "1": "R"})
    discrepancias = int((out["direccion"] != direccion_desde_id).sum())
    descartes.append(("viajes", "direccion (texto trip_id) distinta de direction_id", discrepancias))
    if discrepancias:
        print(f"  [aviso] {discrepancias} viajes con direccion (texto del trip_id) distinta de "
              f"direction_id (campo GTFS numerico) -- revisar antes de confiar en 'direccion'.")

    sin_dist = int(out["distance_km"].isna().sum())
    descartes.append(("viajes", "sin distance_km (shape_id sin match en shape_distances_bus.csv)", sin_dist))
    if sin_dist:
        print(f"  [aviso] {sin_dist} viajes sin distance_km (shape_id sin match en "
              f"shape_distances_bus.csv) -> se descartan.")
        out = out.dropna(subset=["distance_km"])
    return out


def expandir_a_expediciones(viajes, frequencies, stops, descartes):
    """Expande cada viaje por su frecuencia real y agrega energia y
    coordenadas de origen/destino."""
    trips_frequencies = set(frequencies["trip_id"]) - set(viajes["trip_id"])
    descartes.append(("expediciones", "trip_id de frequencies sin viaje calculado (dropeado antes)",
                       len(trips_frequencies)))

    exp = expandir_frecuencias(frequencies).merge(viajes, on="trip_id", how="inner")
    exp["arr_min"] = exp["dep_min"] + exp["dur_min"]
    exp["kwh"] = exp["distance_km"] * parametros.CONSUMO_KWH_KM

    coords_o = stops.rename(columns={"stop_id": "o_stop", "stop_lat": "o_lat", "stop_lon": "o_lon"})
    coords_d = stops.rename(columns={"stop_id": "d_stop", "stop_lat": "d_lat", "stop_lon": "d_lon"})
    exp = exp.merge(coords_o[["o_stop", "o_lat", "o_lon"]], on="o_stop", how="left")
    exp = exp.merge(coords_d[["d_stop", "d_lat", "d_lon"]], on="d_stop", how="left")

    # expedicion_id es la clave UNICA de cada fila (trip_id no lo es: un mismo
    # patron se repite muchas veces por frecuencia). Usar expedicion_id en
    # cualquier join/merge posterior (Etapas 1-4), no trip_id.
    cols = ["expedicion_id", "trip_id", "route_id", "direccion", "dep_min", "arr_min", "dur_min",
            "distance_km", "kwh", "o_stop", "d_stop", "o_lat", "o_lon", "d_lat", "d_lon"]
    return exp[cols].reset_index(drop=True)


def construir_terminales(expediciones):
    """Paraderos unicos usados como origen o destino de alguna expedicion,
    con sus coordenadas (insumo de las Etapas 1-2: clustering y deadhead)."""
    o = expediciones[["o_stop", "o_lat", "o_lon"]].rename(
        columns={"o_stop": "stop_id", "o_lat": "lat", "o_lon": "lon"})
    d = expediciones[["d_stop", "d_lat", "d_lon"]].rename(
        columns={"d_stop": "stop_id", "d_lat": "lat", "d_lon": "lon"})
    return pd.concat([o, d]).drop_duplicates("stop_id").reset_index(drop=True)


def concurrencia_por_minuto(expediciones, minutos_dia=30 * 60):
    """Curva de expediciones en curso minuto a minuto (0 a 30h, para cubrir
    trips que cruzan medianoche). Devuelve el array de concurrencia."""
    t = np.arange(0, minutos_dia)
    eventos = np.zeros(len(t) + 1)
    dep = expediciones["dep_min"].astype(int).clip(0, len(t) - 1).values
    arr = expediciones["arr_min"].astype(int).clip(0, len(t)).values
    np.add.at(eventos, dep, 1)
    np.add.at(eventos, arr, -1)
    return np.cumsum(eventos)[:len(t)]


# --------------------------------------------------------------------------- #
# Tablas nuevas por ruta (insumo directo de la Etapa 1, sin pasar por la
# Etapa 2: ver docs/context/01_metodologia_y_avance.md, decision de esta
# ronda de recalcular buses/energia por ruta desde la Etapa 0)
# --------------------------------------------------------------------------- #

def construir_rutas_resumen(expediciones):
    """Una fila por ruta con lo que necesita la Etapa 1 para clusterizar:
    cuantos buses moviliza (estimado), cuanta energia y km demanda por dia,
    y su centroide geografico.

    n_buses_estimados = maximo de expediciones simultaneas DE ESA RUTA. Es
    una COTA INFERIOR del numero real de buses (ignora layover y que el bus
    tiene que volver fisicamente a completar el ciclo): sumada sobre las 417
    rutas da 7.454, contra los 8.654 del VSP sin interlining de la ronda
    anterior (docs/context/01_metodologia_y_avance.md seccion 3). Se usa
    solo para PONDERAR el peso relativo de cada ruta en el costo de C2, no
    como cifra de flota final.
    """
    n_buses = expediciones.groupby("route_id", group_keys=False).apply(
        lambda g: concurrencia_por_minuto(g).max(), include_groups=False)
    n_buses.name = "n_buses_estimados"

    terminales_ruta = pd.concat([
        expediciones[["route_id", "o_stop"]].rename(columns={"o_stop": "stop_id"}),
        expediciones[["route_id", "d_stop"]].rename(columns={"d_stop": "stop_id"}),
    ]).drop_duplicates()
    n_terminales = terminales_ruta.groupby("route_id").size().rename("n_terminales_usados")

    centroides = centroides_por_ruta(expediciones)

    resumen = expediciones.groupby("route_id").agg(
        n_expediciones=("expedicion_id", "size"),
        km_dia=("distance_km", "sum"),
        kwh_dia=("kwh", "sum"),
        dur_min_media=("dur_min", "mean"),
        primera_salida_min=("dep_min", "min"),
        ultima_salida_min=("dep_min", "max"),
    )
    resumen = resumen.join(n_buses).join(n_terminales).join(centroides)
    resumen = resumen.rename(columns={"lat": "centroide_lat", "lon": "centroide_lon"})
    return resumen.reset_index().round(3)


def _terminal_representativo(g, stop_col, lat_col, lon_col):
    """Paradero mas frecuente de un grupo (ruta, direccion) para el rol
    dado (origen o destino), con sus coordenadas y cuantos paraderos
    distintos se usaron para ese rol (mide la ambiguedad: no todas las
    rutas tienen un unico paradero de inicio/fin por sentido)."""
    conteo = g[stop_col].value_counts()
    top = conteo.index[0]
    fila = g.loc[g[stop_col] == top].iloc[0]
    return pd.Series({
        "stop_id": top,
        "lat": fila[lat_col],
        "lon": fila[lon_col],
        "n_paraderos_distintos": g[stop_col].nunique(),
    })


def construir_rutas_ida_vuelta(expediciones):
    """Para cada ruta con ambas direcciones (ida=I, vuelta=R) presentes:
    distancia entre el paradero final de la ida (mas frecuente) y el
    paradero inicial de la vuelta (mas frecuente). Es la evidencia que
    justifica clusterizar por RUTA y no por expedicion individual (ver
    Propuesta_metodologia_reunion.md seccion 5, diagnostico D4): si ambos
    extremos quedan cerca, la ida y la vuelta se encadenan naturalmente y
    conviene tratarlas como una sola unidad frente al electroterminal.
    """
    ex_ir = expediciones[expediciones["direccion"].isin(["I", "R"])]

    fin_ida = (ex_ir[ex_ir["direccion"] == "I"].groupby("route_id")
               .apply(_terminal_representativo, "d_stop", "d_lat", "d_lon", include_groups=False)
               .rename(columns={"stop_id": "d_stop_ida", "lat": "d_lat_ida", "lon": "d_lon_ida",
                                 "n_paraderos_distintos": "n_d_stops_ida"}))
    inicio_vuelta = (ex_ir[ex_ir["direccion"] == "R"].groupby("route_id")
                      .apply(_terminal_representativo, "o_stop", "o_lat", "o_lon", include_groups=False)
                      .rename(columns={"stop_id": "o_stop_vuelta", "lat": "o_lat_vuelta", "lon": "o_lon_vuelta",
                                        "n_paraderos_distintos": "n_o_stops_vuelta"}))

    ida_vuelta = fin_ida.join(inicio_vuelta, how="inner")
    ida_vuelta["distancia_fin_ida_inicio_vuelta_m"] = geo.haversine_km(
        ida_vuelta["d_lat_ida"], ida_vuelta["d_lon_ida"],
        ida_vuelta["o_lat_vuelta"], ida_vuelta["o_lon_vuelta"]) * 1000
    ida_vuelta["bajo_500m"] = ida_vuelta["distancia_fin_ida_inicio_vuelta_m"] < UMBRAL_IDA_VUELTA_M
    return ida_vuelta.reset_index().round(3)


def construir_terminales_por_ruta(expediciones):
    """Pares (ruta, paradero) con cuantas expediciones de esa ruta lo usan
    como origen y cuantas como destino. Insumo de los mapas de la Etapa 1 y
    de la variante de C1 que mide contra el paradero terminal real (no el
    centroide de la ruta)."""
    origen = expediciones.groupby(["route_id", "o_stop"]).size().rename("n_como_origen")
    destino = expediciones.groupby(["route_id", "d_stop"]).size().rename("n_como_destino")
    origen.index.names = destino.index.names = ["route_id", "stop_id"]
    tabla = pd.concat([origen, destino], axis=1).fillna(0).reset_index()
    tabla[["n_como_origen", "n_como_destino"]] = tabla[["n_como_origen", "n_como_destino"]].astype(int)
    return tabla


# --------------------------------------------------------------------------- #
# Graficos
# --------------------------------------------------------------------------- #

def graficar_buses_por_hora(concurrencia, path_png):
    horas = np.arange(0, 26)
    max_por_hora = [concurrencia[h * 60:(h + 1) * 60].max() if h * 60 < len(concurrencia) else 0
                     for h in horas]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(horas, max_por_hora, color="#2c6e8f")
    ax.set_xlabel("Hora del dia")
    ax.set_ylabel("Expediciones en curso (max.)")
    ax.set_title("Expediciones simultaneas por hora - dia laboral")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_energia(expediciones, path_png):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(expediciones["kwh"], bins=40, color="#8f4a2c")
    ax.set_xlabel("Energia por expedicion (kWh)")
    ax.set_ylabel("Numero de expediciones")
    ax.set_title("Distribucion de energia por expedicion")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_duracion_y_distancia(expediciones, path_png):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.hist(expediciones["dur_min"], bins=40, color="#2c6e8f")
    ax1.set_xlabel("Duracion (min)")
    ax1.set_ylabel("Numero de expediciones")
    ax2.hist(expediciones["distance_km"], bins=40, color="#4a8f2c")
    ax2.set_xlabel("Distancia (km)")
    fig.suptitle("Duracion y distancia por expedicion")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_ida_vuelta(ida_vuelta, path_png):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(ida_vuelta["distancia_fin_ida_inicio_vuelta_m"], bins=40, color="#8f2c6e")
    ax.axvline(UMBRAL_IDA_VUELTA_M, color="black", linestyle="--",
               label=f"{UMBRAL_IDA_VUELTA_M:.0f} m")
    ax.set_xlabel("Distancia fin de ida -> inicio de vuelta (m)")
    ax.set_ylabel("Numero de rutas")
    ax.set_title("Que tan cerca cierra el ciclo ida-vuelta de cada ruta")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Reporte
# --------------------------------------------------------------------------- #

def escribir_reporte(expediciones, terminales, rutas_resumen, ida_vuelta, viajes,
                      concurrencia, descartes, corrida_parcial, rutas_filtro):
    max_conc = int(concurrencia.max())
    t_peak = concurrencia.argmax() / 60
    n_rutas = expediciones["route_id"].nunique()
    n_exp = len(expediciones)
    n_ida_vuelta = len(ida_vuelta)
    n_bajo_500 = int(ida_vuelta["bajo_500m"].sum())
    pct_bajo_500 = 100 * n_bajo_500 / n_ida_vuelta if n_ida_vuelta else float("nan")
    n_ambiguas = int(((ida_vuelta["n_d_stops_ida"] > 1) | (ida_vuelta["n_o_stops_vuelta"] > 1)).sum())

    lineas = [
        "# Reporte de preprocesamiento (Etapa 0)",
        "",
        f"Corrida: {'PARCIAL (checkpoint chico, rutas = ' + str(rutas_filtro) + ')' if corrida_parcial else 'RED COMPLETA'}",
        "",
        "## Conteos",
        f"- Rutas: {n_rutas}",
        f"- Viajes (patrones GTFS): {len(viajes)}",
        f"- Expediciones (viajes expandidos por frecuencia): {n_exp}",
        f"- Paraderos terminales unicos (origen/destino de alguna expedicion): {len(terminales)}",
        f"- Energia total del dia: {expediciones['kwh'].sum() / 1000:.1f} MWh",
        "",
        "## Estadisticas descriptivas (ver tambien distribucion_expediciones.csv)",
        "",
        expediciones[["dur_min", "distance_km", "kwh"]].describe().round(2).to_markdown(),
        "",
        "## Concurrencia",
        f"- Maximo de expediciones simultaneas: {max_conc} a las {t_peak:.2f} h",
        f"- (referencia red completa, prototipo 28/09: {CONCURRENCIA_ESPERADA} a las {HORA_PEAK_ESPERADA} h)",
        f"- Suma de la concurrencia maxima POR RUTA (rutas_resumen.csv): "
        f"{int(rutas_resumen['n_buses_estimados'].sum())} -- es una cota inferior de la flota real "
        f"(ignora layover y el viaje de vuelta al deposito); se usa solo para ponderar rutas en la Etapa 1.",
        "",
        "## Por que se clusteriza por ruta y no por expedicion (ver rutas_ida_vuelta.csv)",
        f"- Rutas con ida y vuelta identificables: {n_ida_vuelta} de {n_rutas}.",
        f"- De esas, {n_bajo_500} ({pct_bajo_500:.1f}%) terminan la ida a menos de "
        f"{UMBRAL_IDA_VUELTA_M:.0f} m de donde empieza la vuelta.",
        f"- {n_ambiguas} rutas tienen mas de un paradero distinto usado como fin-de-ida o "
        f"inicio-de-vuelta (el 'paradero representativo' es el mas frecuente, no el unico).",
        "",
        "## Descartes y chequeos (detalle completo en descartes.csv)",
        "",
        pd.DataFrame(descartes, columns=["etapa", "motivo", "cantidad"]).to_markdown(index=False),
        "",
        "## Supuestos aplicados",
        f"- Consumo energetico: {parametros.CONSUMO_KWH_KM} kWh/km (constante, sin congestion ni topografia).",
        "- Dia tipo: L (laboral, lunes-viernes) — unico dia modelado en esta ronda.",
        "- Duracion y distancia de una expedicion son las de su patron GTFS: iguales para todas las "
        "salidas del mismo patron a lo largo del dia (no hay variacion por hora peak).",
        "",
        "## Tablas generadas",
        "- `conteos.csv`, `descartes.csv`, `distribucion_expediciones.csv`, `concurrencia_por_minuto.csv`.",
        "- `../../data-processed/rutas_resumen.csv`, `rutas_ida_vuelta.csv`, `terminales_por_ruta.csv`.",
        "",
        "## Graficos",
        "- `graficos/buses_por_hora.png`: expediciones simultaneas por hora.",
        "- `graficos/energia_por_expedicion.png`: distribucion de energia por expedicion.",
        "- `graficos/duracion_y_distancia.png`: duracion y distancia por expedicion.",
        "- `graficos/ida_vuelta_distancia.png`: distancia fin de ida -> inicio de vuelta, por ruta.",
        "",
    ]
    (RESULTS / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rutas", nargs="*", default=None,
                         help="Checkpoint chico: filtrar a estas route_id antes de expandir "
                              "(ej. --rutas 101 102). Si se omite, corre la red completa.")
    args = parser.parse_args()

    descartes = []  # lista de (etapa, motivo, cantidad), se vuelca a descartes.csv al final

    trips, stop_times, frequencies, shape_dist, stops = cargar_datos()

    if args.rutas:
        print(f"\n[CHECKPOINT CHICO] Filtrando a rutas: {args.rutas}")
        trips = trips[trips["route_id"].isin(args.rutas)].copy()
        stop_times = stop_times[stop_times["trip_id"].isin(trips["trip_id"])].copy()
        frequencies = frequencies[frequencies["trip_id"].isin(trips["trip_id"])].copy()

    print("\n--- Calculando duracion/distancia por viaje ---")
    viajes = calcular_viajes(trips, stop_times, shape_dist, descartes)
    print(f"  Viajes con distancia valida: {len(viajes)}")

    print("\n--- Expandiendo por frecuencia a expediciones ---")
    expediciones = expandir_a_expediciones(viajes, frequencies, stops, descartes)
    print(f"  Expediciones: {len(expediciones)}")

    sin_coords = int(expediciones[["o_lat", "o_lon", "d_lat", "d_lon"]].isna().any(axis=1).sum())
    descartes.append(("expediciones", "sin coordenadas de origen/destino", sin_coords))
    if sin_coords:
        print(f"  [aviso] {sin_coords} expediciones sin coordenadas de origen/destino -> se descartan.")
        expediciones = expediciones.dropna(subset=["o_lat", "o_lon", "d_lat", "d_lon"]).reset_index(drop=True)

    print("\n--- Construyendo tabla de terminales ---")
    terminales = construir_terminales(expediciones)
    print(f"  Paraderos terminales unicos: {len(terminales)}")

    print("\n--- Calculando concurrencia ---")
    concurrencia = concurrencia_por_minuto(expediciones)
    max_conc = int(concurrencia.max())
    t_peak = concurrencia.argmax() / 60
    print(f"  Maximo de expediciones simultaneas: {max_conc} a las {t_peak:.2f} h")

    print("\n--- Construyendo tablas por ruta (insumo de la Etapa 1) ---")
    rutas_resumen = construir_rutas_resumen(expediciones)
    ida_vuelta = construir_rutas_ida_vuelta(expediciones)
    terminales_por_ruta = construir_terminales_por_ruta(expediciones)
    print(f"  rutas_resumen: {len(rutas_resumen)} rutas | "
          f"rutas_ida_vuelta: {len(ida_vuelta)} rutas con ambas direcciones | "
          f"terminales_por_ruta: {len(terminales_por_ruta)} pares ruta-paradero")

    print("\n--- Guardando outputs de data-processed/ ---")
    expediciones.to_csv(DATA_PROCESSED / "expediciones.csv", index=False, sep=CSV_SEP)
    terminales.to_csv(DATA_PROCESSED / "terminales.csv", index=False, sep=CSV_SEP)
    rutas_resumen.to_csv(DATA_PROCESSED / "rutas_resumen.csv", index=False, sep=CSV_SEP)
    ida_vuelta.to_csv(DATA_PROCESSED / "rutas_ida_vuelta.csv", index=False, sep=CSV_SEP)
    terminales_por_ruta.to_csv(DATA_PROCESSED / "terminales_por_ruta.csv", index=False, sep=CSV_SEP)
    for nombre, df in [("expediciones.csv", expediciones), ("terminales.csv", terminales),
                       ("rutas_resumen.csv", rutas_resumen), ("rutas_ida_vuelta.csv", ida_vuelta),
                       ("terminales_por_ruta.csv", terminales_por_ruta)]:
        print(f"  -> {DATA_PROCESSED / nombre} ({len(df)} filas)")

    print("\n--- Guardando tablas de results/ ---")
    pd.DataFrame({
        "metrica": ["rutas", "viajes_patrones_gtfs", "expediciones", "paraderos_terminales_unicos",
                    "concurrencia_maxima", "hora_peak", "energia_total_mwh_dia",
                    "rutas_con_ida_y_vuelta", "rutas_ida_vuelta_bajo_500m"],
        "valor": [expediciones["route_id"].nunique(), len(viajes), len(expediciones), len(terminales),
                  max_conc, round(t_peak, 2), round(expediciones["kwh"].sum() / 1000, 1),
                  len(ida_vuelta), int(ida_vuelta["bajo_500m"].sum())],
    }).to_csv(RESULTS / "conteos.csv", index=False, sep=CSV_SEP)
    pd.DataFrame(descartes, columns=["etapa", "motivo", "cantidad"]).to_csv(
        RESULTS / "descartes.csv", index=False, sep=CSV_SEP)
    expediciones[["dur_min", "distance_km", "kwh"]].describe().round(3).to_csv(
        RESULTS / "distribucion_expediciones.csv", sep=CSV_SEP)
    pd.DataFrame({"t_min": np.arange(len(concurrencia)), "concurrencia": concurrencia.astype(int)}).to_csv(
        RESULTS / "concurrencia_por_minuto.csv", index=False, sep=CSV_SEP)
    print(f"  -> {RESULTS / 'conteos.csv'}, descartes.csv, distribucion_expediciones.csv, "
          f"concurrencia_por_minuto.csv")

    graficar_buses_por_hora(concurrencia, GRAFICOS / "buses_por_hora.png")
    graficar_energia(expediciones, GRAFICOS / "energia_por_expedicion.png")
    graficar_duracion_y_distancia(expediciones, GRAFICOS / "duracion_y_distancia.png")
    if len(ida_vuelta):
        graficar_ida_vuelta(ida_vuelta, GRAFICOS / "ida_vuelta_distancia.png")
    print(f"  -> {GRAFICOS}/ (4 graficos)")

    escribir_reporte(expediciones, terminales, rutas_resumen, ida_vuelta, viajes, concurrencia,
                      descartes, corrida_parcial=bool(args.rutas), rutas_filtro=args.rutas)
    print(f"  -> {RESULTS / 'reporte.md'}")

    # --- Chequeos de sanidad (obligatorios siempre) ---
    assert expediciones[["distance_km", "kwh"]].isna().sum().sum() == 0, \
        "Hay expediciones con distancia o energia NaN: revisar el merge con shape_distances_bus."
    assert (expediciones["dur_min"] > 0).all(), \
        "Hay expediciones con duracion <= 0: revisar stop_times (posible trip con 1 sola parada)."
    assert (expediciones["arr_min"] >= expediciones["dep_min"]).all(), \
        "Hay expediciones que llegan antes de salir."
    assert expediciones["expedicion_id"].nunique() == len(expediciones), \
        "expedicion_id no es unico: revisar expandir_frecuencias() en scripts/common/tiempo.py."
    assert rutas_resumen["n_expediciones"].sum() == len(expediciones), \
        "La suma de expediciones por ruta no calza con el total: revisar construir_rutas_resumen()."
    # Tolerancia de 1 kWh (no 1e-3): rutas_resumen redondea kwh_dia a 3 decimales
    # para que sea legible, y eso acumula un error de redondeo del orden de
    # 0.01 kWh sobre las 417 rutas -- irrelevante frente a los ~1.88 millones
    # de kWh/dia totales, no una señal de que el calculo este mal.
    assert abs(rutas_resumen["kwh_dia"].sum() - expediciones["kwh"].sum()) < 1.0, \
        "La suma de kWh/dia por ruta no calza con el total de expediciones.csv."
    assert set(ida_vuelta["route_id"]).issubset(set(expediciones["route_id"])), \
        "rutas_ida_vuelta.csv tiene una ruta que no esta en expediciones.csv."
    print("\n  [OK] Chequeos de sanidad basicos pasaron (sin NaN, duraciones y horarios consistentes, "
          "tablas por ruta cuadran con expediciones.csv).")

    # --- Chequeos de sanidad SOLO para la corrida de red completa ---
    if not args.rutas:
        n_exp, n_rutas = len(expediciones), expediciones["route_id"].nunique()
        if n_exp != EXPEDICIONES_ESPERADAS:
            print(f"  [aviso] {n_exp} expediciones, se esperaban {EXPEDICIONES_ESPERADAS} "
                  f"(diferencia = {n_exp - EXPEDICIONES_ESPERADAS}). Revisar si es esperable "
                  f"(p. ej. descartes por coordenadas/distancia faltante) antes de seguir.")
        else:
            print(f"  [OK] {n_exp} expediciones == cifra de referencia del Informe 1 / prototipo.")
        if n_rutas != RUTAS_ESPERADAS:
            print(f"  [aviso] {n_rutas} rutas, se esperaban {RUTAS_ESPERADAS}.")
        if abs(max_conc - CONCURRENCIA_ESPERADA) > 50:
            print(f"  [aviso] Concurrencia maxima {max_conc} se aleja de la referencia "
                  f"{CONCURRENCIA_ESPERADA} en mas de 50 buses. Revisar antes de usar en la Etapa 2.")
        else:
            print(f"  [OK] Concurrencia maxima {max_conc} consistente con la referencia "
                  f"({CONCURRENCIA_ESPERADA}).")
    else:
        print("\n  Corrida parcial (checkpoint chico): no se comparan cifras contra la red completa.")

    print("\n=== FIN ETAPA 0 ===")


if __name__ == "__main__":
    main()
