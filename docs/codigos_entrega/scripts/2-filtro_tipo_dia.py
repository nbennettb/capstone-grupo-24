"""
Paso 2 de los datos: filtra los datos de buses (salida del paso 1) al dia laboral (service_id L, lunes a viernes).

Solo se filtran las tablas que dependen del servicio (trips, stop_times, frequencies). Rutas, paraderos, trazados y
distancias de trazado no dependen del dia.

Input:  resultados/datos_filtrados/{trips,stop_times,frequencies}_bus.csv, datos/gtfs/calendar.txt
Output: resultados/datos_filtrados/{trips,stop_times,frequencies}_dia_L.csv

Uso:
    python 2-filtro_tipo_dia.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.rutas import CSV_SEP, DATA_FILTRADO, GTFS  # noqa: E402

GTFS_DIR, FILTRADO_DIR = GTFS, DATA_FILTRADO

DIA_TIPO = "L"  # laboral, lunes a viernes


def guardar(df, nombre):
    path = FILTRADO_DIR / nombre
    df.to_csv(path, index=False, sep=CSV_SEP)
    print(f"  -> Guardado {nombre}: {len(df)} filas, {len(df.columns)} columnas")


def main():
    print(f"=== PASO 2: FILTRO POR TIPO DE DIA = '{DIA_TIPO}' ===\n")

    calendar = pd.read_csv(GTFS_DIR / "calendar.txt", dtype=str, low_memory=False)
    print("Tipos de dia disponibles en calendar.txt:")
    print(calendar["service_id"].value_counts())

    if DIA_TIPO not in set(calendar["service_id"]):
        print(f"\n[!] service_id == '{DIA_TIPO}' no existe en calendar.txt. Revisar valores de arriba.")
        return

    # --- trips ---
    trips_bus = pd.read_csv(FILTRADO_DIR / "trips_bus.csv", dtype=str, low_memory=False, sep=CSV_SEP)
    n_trips_total = len(trips_bus)
    trips_L = trips_bus[trips_bus["service_id"] == DIA_TIPO].copy()
    print(f"\n--- trips_bus.csv ---")
    print(f"  Filas: {n_trips_total} -> {len(trips_L)} (excluidas {n_trips_total - len(trips_L)})")
    guardar(trips_L, "trips_dia_L.csv")
    trip_ids_L = set(trips_L["trip_id"])

    # --- stop_times ---
    stop_times_bus = pd.read_csv(FILTRADO_DIR / "stop_times_bus.csv", dtype=str, low_memory=False, sep=CSV_SEP)
    n_st_total = len(stop_times_bus)
    stop_times_L = stop_times_bus[stop_times_bus["trip_id"].isin(trip_ids_L)].copy()
    print(f"\n--- stop_times_bus.csv ---")
    print(f"  Filas: {n_st_total} -> {len(stop_times_L)} (excluidas {n_st_total - len(stop_times_L)})")
    guardar(stop_times_L, "stop_times_dia_L.csv")

    # --- frequencies ---
    frequencies_bus = pd.read_csv(FILTRADO_DIR / "frequencies_bus.csv", dtype=str, low_memory=False, sep=CSV_SEP)
    n_freq_total = len(frequencies_bus)
    frequencies_L = frequencies_bus[frequencies_bus["trip_id"].isin(trip_ids_L)].copy()
    print(f"\n--- frequencies_bus.csv ---")
    print(f"  Filas: {n_freq_total} -> {len(frequencies_L)} (excluidas {n_freq_total - len(frequencies_L)})")
    guardar(frequencies_L, "frequencies_dia_L.csv")

    print("\n=== FIN PASO 2 ===")
    print("\nNota: routes_bus.csv, stops_bus.csv, shapes_bus.csv y "
          "shape_distances_bus.csv no se tocan en este paso (no dependen del dia).")


if __name__ == "__main__":
    main()