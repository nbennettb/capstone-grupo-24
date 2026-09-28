"""Utilidades de tiempo: parseo de horas GTFS (que pueden pasar de 24:00:00
en trips que cruzan medianoche) y expansion de frequencies.txt a expediciones
reales (salidas individuales), vectorizado con pandas/numpy.

Reimplementa, de forma reutilizable, lo que se probo en el prototipo
exploratorio del 28/09 (an1.py) para el analisis de dimensionamiento.
"""

import numpy as np
import pandas as pd


def time_to_min(serie_hhmmss: pd.Series) -> pd.Series:
    """Convierte una columna de horas 'HH:MM:SS' (con HH pudiendo ser >=24,
    como usa GTFS para viajes que cruzan medianoche) a minutos desde las
    00:00 del dia de servicio. Vectorizado: NO usar pd.to_datetime, que
    falla con horas >=24.
    """
    partes = serie_hhmmss.str.split(":", expand=True).astype(int)
    return partes[0] * 60 + partes[1] + partes[2] / 60


def expandir_frecuencias(frequencies: pd.DataFrame) -> pd.DataFrame:
    """Expande frequencies.txt (un patron con headway) a una fila por
    salida real. Devuelve columnas: trip_id, dep_min (minuto de salida de
    esa expedicion especifica).

    Ejemplo: un patron con start=05:30, end=07:30, headway=900s (15 min)
    genera 8 filas (una cada 15 min entre 05:30 y 07:30, exclusive del
    extremo derecho segun el estandar GTFS).
    """
    fq = frequencies.copy()
    fq["s"] = time_to_min(fq["start_time"])
    fq["e"] = time_to_min(fq["end_time"])
    fq["h"] = fq["headway_secs"].astype(float) / 60
    fq["n"] = np.ceil((fq["e"] - fq["s"]) / fq["h"] - 1e-9).astype(int)

    expandido = fq.loc[fq.index.repeat(fq["n"])].copy()
    expandido["k"] = expandido.groupby(level=0).cumcount()
    expandido["dep_min"] = expandido["s"] + expandido["k"] * expandido["h"]
    return expandido[["trip_id", "dep_min"]].reset_index(drop=True)
