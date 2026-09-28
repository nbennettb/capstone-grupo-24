"""Utilidades compartidas de la Etapa 1 (clustering de rutas a
electroterminales) y del modo 'ruta' de la Etapa 2 (que necesita el mismo
electroterminal base por ruta). Ver docs/Propuesta_metodologia_reunion.md
seccion 5 y docs/context/01_metodologia_y_avance.md.
"""

import numpy as np
import pandas as pd

from . import geo


def centroides_por_ruta(ex: pd.DataFrame) -> pd.DataFrame:
    """Centroide (lat, lon) de cada ruta: promedio de todos sus paraderos
    terminales (origen y destino, ambos sentidos). Se usa como punto
    representativo de la ruta para estimar su electroterminal mas cercano
    -- una aproximacion simple, no la ubicacion real de ningun paradero."""
    pts = pd.concat([
        ex[["route_id", "o_lat", "o_lon"]].rename(columns={"o_lat": "lat", "o_lon": "lon"}),
        ex[["route_id", "d_lat", "d_lon"]].rename(columns={"d_lat": "lat", "d_lon": "lon"}),
    ])
    return pts.groupby("route_id")[["lat", "lon"]].mean()


def distancia_rutas_a_depots(ex: pd.DataFrame, depots: pd.DataFrame, factor_desvio: float) -> pd.DataFrame:
    """Matriz (rutas x electroterminales) de distancia estimada en km
    (euclidiana * factor_desvio) entre el centroide de cada ruta y cada
    electroterminal. Filas indexadas por route_id, columnas por depot_id."""
    centroides = centroides_por_ruta(ex)
    P = geo.xy(centroides["lat"].values, centroides["lon"].values)
    DP = geo.xy(depots["lat"].values, depots["lon"].values)
    d = geo.matriz_distancias_planas(P, DP) * factor_desvio
    return pd.DataFrame(d, index=centroides.index, columns=depots["depot_id"].astype(str).values)


def depot_mas_cercano_por_ruta(ex: pd.DataFrame, depots: pd.DataFrame, factor_desvio: float) -> pd.Series:
    """Para cada ruta, el INDICE POSICIONAL (0..k-1, no el depot_id) del
    electroterminal mas cercano a su centroide. Es la estrategia C1
    (heuristica) de la Etapa 1, y tambien el electroterminal base que usa
    el modo 'ruta' de la Etapa 2 (scripts/6-vsp_asignacion_buses.py)."""
    dist = distancia_rutas_a_depots(ex, depots, factor_desvio)
    return pd.Series(dist.values.argmin(axis=1), index=dist.index)
