"""
Etapa 0 del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia_y_avance.md seccion 1 para el lugar de
esta etapa dentro de la metodologia de 4 etapas aprobada el 28/09/2026).

Expande frequencies_dia_L.csv a expediciones reales (una fila por salida
individual de bus) y calcula, para cada una, duracion, distancia y energia
necesaria. Continua el pipeline de scripts/1-filtro_datos_buses.py y
scripts/2-filtro_tipo_dia.py.

Input:  data-filtrado/{trips_dia_L, stop_times_dia_L, frequencies_dia_L,
                       shape_distances_bus, stops_bus}.csv
Output: data-processed/expediciones.csv   (una fila por expedicion)
        data-processed/terminales.csv     (paraderos unicos usados como
                                            origen/destino, con coordenadas)
        results/03_preprocesamiento/reporte.md  (conteos, estadisticas,
                                                  supuestos y 2 graficos)

Uso:
    python scripts/3-preprocesamiento_expediciones.py
        Corre sobre la red completa (417 rutas, ~64.502 expediciones
        esperadas).

    python scripts/3-preprocesamiento_expediciones.py --rutas 101 102
        Checkpoint chico: corre solo sobre las rutas indicadas, para
        revisar a mano que expediciones/horarios/energia tengan sentido
        antes de correr la red completa. No escribe el reporte de
        validacion de la red completa (se marca en el reporte que es una
        corrida parcial).
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
from common import parametros                                    # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402
from common.tiempo import time_to_min, expandir_frecuencias      # noqa: E402

RESULTS = carpeta_resultados("03_preprocesamiento")

# Cifras de referencia de la red completa (Informe 1 / prototipo del
# 28/09), usadas como chequeo de sanidad, no como valor forzado.
EXPEDICIONES_ESPERADAS = 64502
RUTAS_ESPERADAS = 417
CONCURRENCIA_ESPERADA = 6539
HORA_PEAK_ESPERADA = 8.0


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


def calcular_viajes(trips, stop_times, shape_dist):
    """Un viaje (trip_id) = un patron GTFS. Calcula su duracion, paradero
    de origen/destino y distancia recorrida (via shape_id)."""
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
    sin_dist = out["distance_km"].isna().sum()
    if sin_dist:
        print(f"  [aviso] {sin_dist} viajes sin distance_km (shape_id sin match en "
              f"shape_distances_bus.csv) -> se descartan.")
        out = out.dropna(subset=["distance_km"])
    return out


def expandir_a_expediciones(viajes, frequencies, stops):
    """Expande cada viaje por su frecuencia real y agrega energia y
    coordenadas de origen/destino."""
    exp = expandir_frecuencias(frequencies).merge(viajes, on="trip_id", how="inner")
    exp["arr_min"] = exp["dep_min"] + exp["dur_min"]
    exp["kwh"] = exp["distance_km"] * parametros.CONSUMO_KWH_KM

    coords_o = stops.rename(columns={"stop_id": "o_stop", "stop_lat": "o_lat", "stop_lon": "o_lon"})
    coords_d = stops.rename(columns={"stop_id": "d_stop", "stop_lat": "d_lat", "stop_lon": "d_lon"})
    exp = exp.merge(coords_o[["o_stop", "o_lat", "o_lon"]], on="o_stop", how="left")
    exp = exp.merge(coords_d[["d_stop", "d_lat", "d_lon"]], on="d_stop", how="left")

    cols = ["trip_id", "route_id", "direccion", "dep_min", "arr_min", "dur_min",
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


def escribir_reporte(expediciones, terminales, viajes, concurrencia, corrida_parcial, rutas_filtro):
    max_conc = int(concurrencia.max())
    t_peak = concurrencia.argmax() / 60
    n_rutas = expediciones["route_id"].nunique()
    n_exp = len(expediciones)

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
        f"- Expediciones sin distancia (descartadas antes de este punto): ver log de consola",
        "",
        "## Estadisticas descriptivas",
        "",
        expediciones[["dur_min", "distance_km", "kwh"]].describe().round(2).to_markdown(),
        "",
        "## Concurrencia",
        f"- Maximo de expediciones simultaneas: {max_conc} a las {t_peak:.2f} h",
        f"- (referencia red completa, prototipo 28/09: {CONCURRENCIA_ESPERADA} a las {HORA_PEAK_ESPERADA} h)",
        "",
        "## Supuestos aplicados",
        f"- Consumo energetico: {parametros.CONSUMO_KWH_KM} kWh/km (constante, sin congestion ni topografia).",
        "- Dia tipo: L (laboral, lunes-viernes) — unico dia modelado en esta ronda.",
        "",
        "## Graficos",
        "- `buses_por_hora.png`: expediciones simultaneas por hora.",
        "- `energia_por_expedicion.png`: distribucion de energia por expedicion.",
        "",
        "*(Generado automaticamente por scripts/3-preprocesamiento_expediciones.py)*",
    ]
    (RESULTS / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rutas", nargs="*", default=None,
                         help="Checkpoint chico: filtrar a estas route_id antes de expandir "
                              "(ej. --rutas 101 102). Si se omite, corre la red completa.")
    args = parser.parse_args()

    trips, stop_times, frequencies, shape_dist, stops = cargar_datos()

    if args.rutas:
        print(f"\n[CHECKPOINT CHICO] Filtrando a rutas: {args.rutas}")
        trips = trips[trips["route_id"].isin(args.rutas)].copy()
        stop_times = stop_times[stop_times["trip_id"].isin(trips["trip_id"])].copy()
        frequencies = frequencies[frequencies["trip_id"].isin(trips["trip_id"])].copy()

    print("\n--- Calculando duracion/distancia por viaje ---")
    viajes = calcular_viajes(trips, stop_times, shape_dist)
    print(f"  Viajes con distancia valida: {len(viajes)}")

    print("\n--- Expandiendo por frecuencia a expediciones ---")
    expediciones = expandir_a_expediciones(viajes, frequencies, stops)
    print(f"  Expediciones: {len(expediciones)}")

    sin_coords = expediciones[["o_lat", "o_lon", "d_lat", "d_lon"]].isna().any(axis=1).sum()
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

    print("\n--- Guardando outputs ---")
    expediciones.to_csv(DATA_PROCESSED / "expediciones.csv", index=False, sep=CSV_SEP)
    terminales.to_csv(DATA_PROCESSED / "terminales.csv", index=False, sep=CSV_SEP)
    print(f"  -> {DATA_PROCESSED / 'expediciones.csv'} ({len(expediciones)} filas)")
    print(f"  -> {DATA_PROCESSED / 'terminales.csv'} ({len(terminales)} filas)")

    graficar_buses_por_hora(concurrencia, RESULTS / "buses_por_hora.png")
    graficar_energia(expediciones, RESULTS / "energia_por_expedicion.png")
    escribir_reporte(expediciones, terminales, viajes, concurrencia,
                      corrida_parcial=bool(args.rutas), rutas_filtro=args.rutas)
    print(f"  -> {RESULTS / 'reporte.md'}")

    # --- Chequeos de sanidad (obligatorios siempre) ---
    assert expediciones[["distance_km", "kwh"]].isna().sum().sum() == 0, \
        "Hay expediciones con distancia o energia NaN: revisar el merge con shape_distances_bus."
    assert (expediciones["dur_min"] > 0).all(), \
        "Hay expediciones con duracion <= 0: revisar stop_times (posible trip con 1 sola parada)."
    assert (expediciones["arr_min"] >= expediciones["dep_min"]).all(), \
        "Hay expediciones que llegan antes de salir."
    print("\n  [OK] Chequeos de sanidad basicos pasaron (sin NaN, duraciones y horarios consistentes).")

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
