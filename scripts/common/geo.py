"""Utilidades geograficas: proyeccion plana aproximada centrada en Santiago
(suficiente para distancias cortas dentro de la RM) y distancia haversine,
usadas para estimar el deadhead entre paraderos y electroterminales.

Nota de alcance (ver docs/context/02_pendientes_profesor.md, pregunta 5):
esto es una aproximacion euclidiana x FACTOR_DESVIO, no una ruta real por la
red vial. Calibrar/sensibilizar con OpenStreetMap (osmnx) queda para una
etapa posterior.
"""

import numpy as np

# Latitud de referencia para la proyeccion plana (centro aprox. de Santiago).
LAT0 = -33.45
LON0 = -70.65

# Factores de conversion grados -> km a la latitud de referencia.
KM_POR_GRADO_LAT = 110.57
KM_POR_GRADO_LON = 111.32 * np.cos(np.radians(LAT0))


def xy(lat, lon):
    """Proyecta (lat, lon) en grados a coordenadas planas aproximadas en km,
    centradas en LAT0/LON0. Acepta escalares o arrays/Series de numpy/pandas.
    Devuelve un array (..., 2) con columnas [x_km, y_km].
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    x = (lon - LON0) * KM_POR_GRADO_LON
    y = (lat - LAT0) * KM_POR_GRADO_LAT
    return np.stack([x, y], axis=-1)


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia haversine en km entre pares de puntos (lat1,lon1) y
    (lat2,lon2). Acepta escalares o arrays de igual forma (broadcast-safe).
    """
    lat1, lon1, lat2, lon2 = (np.radians(np.asarray(v, dtype=float))
                               for v in (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def matriz_distancias_planas(puntos_a, puntos_b):
    """Matriz de distancias euclidianas (km, ya proyectadas) entre dos
    conjuntos de puntos planos (arrays Nx2 y Mx2, salida de xy()).
    Devuelve una matriz NxM.
    """
    a = np.asarray(puntos_a)
    b = np.asarray(puntos_b)
    return np.hypot(a[:, None, 0] - b[None, :, 0], a[:, None, 1] - b[None, :, 1])
