"""
Paso 1 de los datos: filtra los archivos del curso a lo que sirve para los buses.

Filas: excluye Metro (L1-L6), Metrotren (MTN, MTR) y el bus al aeropuerto (BA).
Columnas: elimina las que quedan vacias o constantes tras el filtro.
No filtra por tipo de dia (lo hace 2-filtro_tipo_dia.py). No usa agency, calendar_dates, feed_info, levels ni pathways.

Input:  datos/gtfs/{routes,trips,stop_times,frequencies,stops,shapes}.txt, datos/shape_distances.csv y los CSV del
        curso (charger_capacity, charging_activities, depots, electricity_prices, parameters,
        parametros_descripcion, vehicles)
Output: resultados/datos_filtrados/{routes,trips,stop_times,stops,frequencies,shapes,shape_distances}_bus.csv
        y los CSV del curso reescritos con ';'

Uso:
    python 1-filtro_datos_buses.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.rutas import CSV_SEP, DATA_FILTRADO, DATOS, GTFS  # noqa: E402

DATA_DIR, GTFS_DIR, OUT_DIR = DATOS, GTFS, DATA_FILTRADO

# --- route_id a excluir: Metro + Metrotren + Bus Acercamiento Aeropuerto ---
METRO_ROUTE_IDS = {"L1", "L2", "L3", "L4", "L4A", "L5", "L6"}
METROTREN_ROUTE_IDS = {"MTN", "MTR"}
AEROPUERTO_ROUTE_IDS = {"BA"}
EXCLUDED_ROUTE_IDS = METRO_ROUTE_IDS | METROTREN_ROUTE_IDS | AEROPUERTO_ROUTE_IDS


def cargar_gtfs(nombre):
    return pd.read_csv(GTFS_DIR / nombre, dtype=str, low_memory=False)


def limpiar_columnas(df, nombre_archivo, proteger=None):
    """
    Elimina columnas que, dentro del subconjunto ya filtrado a buses,
    quedan 100% vacias o con un unico valor constante (sin vacios).
    Nunca elimina columnas en `proteger`. Imprime cada eliminacion.
    """
    proteger = set(proteger or [])
    df = df.copy()
    for col in list(df.columns):
        if col in proteger or col not in df.columns:
            continue
        serie = df[col]
        vacios = serie.isna() | (serie.astype(str).str.strip() == "")
        if vacios.all():
            df = df.drop(columns=[col])
            print(f"  [{nombre_archivo}] '{col}' eliminada (100% vacia)")
            continue
        if vacios.sum() == 0:
            valores = serie.astype(str).str.strip().unique()
            if len(valores) == 1:
                df = df.drop(columns=[col])
                print(f"  [{nombre_archivo}] '{col}' eliminada (constante = '{valores[0]}')")
    return df


def reportar_columna_protegida(df, nombre_archivo, col):
    """Imprime diagnostico de una columna protegida, sin eliminarla."""
    if col not in df.columns:
        return
    serie = df[col]
    vacios = (serie.isna() | (serie.astype(str).str.strip() == "")).sum()
    n = len(serie)
    valores_unicos = serie.dropna().astype(str).str.strip().nunique()
    print(f"  [{nombre_archivo}] '{col}' PROTEGIDA -> {n - vacios}/{n} no vacios, "
          f"{valores_unicos} valores unicos distintos (revisar manualmente si conviene mantenerla)")


def guardar(df, nombre):
    path = OUT_DIR / nombre
    df.to_csv(path, index=False, sep=CSV_SEP)
    print(f"  -> Guardado {nombre}: {len(df)} filas, {len(df.columns)} columnas")


def main():
    print("=== PASO 1: FILTRO COMPLETO A DATOS DE BUSES ===\n")

    # --- 1. routes.txt -> routes_bus.csv ---
    print("--- routes.txt ---")
    routes = cargar_gtfs("routes.txt")
    n_routes_total = len(routes)
    routes_bus = routes[~routes["route_id"].isin(EXCLUDED_ROUTE_IDS)].copy()
    routes_bus = limpiar_columnas(routes_bus, "routes_bus", proteger=["route_id"])
    print(f"  Filas: {n_routes_total} -> {len(routes_bus)} (excluidas {n_routes_total - len(routes_bus)})")
    guardar(routes_bus, "routes_bus.csv")
    bus_route_ids = set(routes_bus["route_id"])

    # --- 2. trips.txt -> trips_bus.csv ---
    print("\n--- trips.txt ---")
    trips = cargar_gtfs("trips.txt")
    n_trips_total = len(trips)
    trips_bus = trips[trips["route_id"].isin(bus_route_ids)].copy()
    proteger_trips = ["trip_id", "route_id", "service_id", "shape_id", "block_id"]
    trips_bus = limpiar_columnas(trips_bus, "trips_bus", proteger=proteger_trips)
    reportar_columna_protegida(trips_bus, "trips_bus", "block_id")
    print(f"  Filas: {n_trips_total} -> {len(trips_bus)} (excluidas {n_trips_total - len(trips_bus)})")
    guardar(trips_bus, "trips_bus.csv")
    bus_trip_ids = set(trips_bus["trip_id"])
    bus_shape_ids = set(trips_bus["shape_id"].dropna())

    # --- 3. stop_times.txt -> stop_times_bus.csv ---
    print("\n--- stop_times.txt ---")
    stop_times = cargar_gtfs("stop_times.txt")
    n_st_total = len(stop_times)
    stop_times_bus = stop_times[stop_times["trip_id"].isin(bus_trip_ids)].copy()
    proteger_st = ["trip_id", "stop_id", "stop_sequence", "arrival_time",
                   "departure_time", "shape_dist_traveled"]
    stop_times_bus = limpiar_columnas(stop_times_bus, "stop_times_bus", proteger=proteger_st)
    reportar_columna_protegida(stop_times_bus, "stop_times_bus", "shape_dist_traveled")
    print(f"  Filas: {n_st_total} -> {len(stop_times_bus)} (excluidas {n_st_total - len(stop_times_bus)})")
    guardar(stop_times_bus, "stop_times_bus.csv")
    bus_stop_ids = set(stop_times_bus["stop_id"])

    # --- 4. frequencies.txt -> frequencies_bus.csv ---
    print("\n--- frequencies.txt ---")
    frequencies = cargar_gtfs("frequencies.txt")
    n_freq_total = len(frequencies)
    frequencies_bus = frequencies[frequencies["trip_id"].isin(bus_trip_ids)].copy()
    frequencies_bus = limpiar_columnas(frequencies_bus, "frequencies_bus",
                                        proteger=["trip_id", "start_time", "end_time", "headway_secs"])
    print(f"  Filas: {n_freq_total} -> {len(frequencies_bus)} (excluidas {n_freq_total - len(frequencies_bus)})")
    guardar(frequencies_bus, "frequencies_bus.csv")

    # --- 5. stops.txt -> stops_bus.csv ---
    print("\n--- stops.txt ---")
    stops = cargar_gtfs("stops.txt")
    n_stops_total = len(stops)
    stops_bus = stops[stops["stop_id"].isin(bus_stop_ids)].copy()
    stops_bus = limpiar_columnas(stops_bus, "stops_bus",
                                  proteger=["stop_id", "stop_name", "stop_lat", "stop_lon"])
    print(f"  Filas: {n_stops_total} -> {len(stops_bus)} (excluidas {n_stops_total - len(stops_bus)})")
    guardar(stops_bus, "stops_bus.csv")

    # --- 6. shapes.txt -> shapes_bus.csv (conversion txt -> csv + filtro) ---
    print("\n--- shapes.txt ---")
    shapes = cargar_gtfs("shapes.txt")
    n_shapes_total = len(shapes)
    shapes_bus = shapes[shapes["shape_id"].isin(bus_shape_ids)].copy()
    shapes_bus = limpiar_columnas(
        shapes_bus, "shapes_bus",
        proteger=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"]
    )
    print(f"  Filas: {n_shapes_total} -> {len(shapes_bus)} (excluidas {n_shapes_total - len(shapes_bus)})")
    guardar(shapes_bus, "shapes_bus.csv")

    # --- 7. shape_distances.csv -> shape_distances_bus.csv (filtro de filas) ---
    print("\n--- shape_distances.csv ---")
    shape_dist = pd.read_csv(DATA_DIR / "shape_distances.csv", dtype=str, low_memory=False)
    n_sd_total = len(shape_dist)
    shape_dist_bus = shape_dist[shape_dist["shape_id"].isin(bus_shape_ids)].copy()
    print(f"  Filas: {n_sd_total} -> {len(shape_dist_bus)} (excluidas {n_sd_total - len(shape_dist_bus)})")
    guardar(shape_dist_bus, "shape_distances_bus.csv")

    # --- 8. Releer y reescribir los CSV ya limpios (sin filtro necesario) ---
    # No se usa una copia directa de archivo porque el original usa "," y
    # aqui queremos reescribirlo con CSV_SEP para que sea consistente con
    # el resto de los datos filtrados.
    print("\n--- Releyendo y reescribiendo CSVs ya limpios (sin filtro de filas) ---")
    archivos_limpios = [
        "charger_capacity.csv", "charging_activities.csv", "depots.csv",
        "electricity_prices.csv", "parameters.csv",
        "parametros_descripcion.csv", "vehicles.csv",
    ]
    for nombre in archivos_limpios:
        origen = DATA_DIR / nombre
        if origen.exists():
            df_tmp = pd.read_csv(origen, dtype=str, low_memory=False)
            guardar(df_tmp, nombre)
        else:
            print(f"  [!] No encontrado: {nombre}")

    print("\n=== FIN PASO 1 ===")


if __name__ == "__main__":
    main()