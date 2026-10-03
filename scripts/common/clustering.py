"""Utilidades compartidas de la Etapa 1 (clustering de rutas a
electroterminales) y del modo 'ruta' de la Etapa 2 (que necesita el mismo
electroterminal base por ruta). Ver docs/Propuesta_metodologia_reunion.md
seccion 5 y docs/context/01_metodologia.md.
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


def distancia_ponderada_a_terminales_reales(terminales_por_ruta: pd.DataFrame, terminales: pd.DataFrame,
                                             depots: pd.DataFrame, factor_desvio: float) -> pd.DataFrame:
    """Matriz (rutas x electroterminales) de distancia ESPERADA en km entre
    los paraderos terminales REALES de cada ruta (no su centroide) y cada
    electroterminal, ponderando cada paradero por cuantas expediciones lo
    usan como origen o destino (columnas n_como_origen/n_como_destino de
    data-processed/terminales_por_ruta.csv).

    Es la estrategia C1b de la Etapa 1 (y la metrica de distancia que usa
    tambien C2): mide contra donde el bus efectivamente empieza/termina un
    viaje, en vez de contra un punto promedio que puede no coincidir con
    ningun paradero real de la ruta.
    """
    t = terminales_por_ruta.merge(terminales, on="stop_id", how="left")
    t["peso"] = t["n_como_origen"] + t["n_como_destino"]

    P = geo.xy(t["lat"].values, t["lon"].values)
    DP = geo.xy(depots["lat"].values, depots["lon"].values)
    d = geo.matriz_distancias_planas(P, DP) * factor_desvio    # (paraderos x depots)

    depot_ids = depots["depot_id"].astype(str).values
    ponderada = pd.DataFrame(d * t["peso"].values[:, None], columns=depot_ids)
    ponderada["route_id"] = t["route_id"].values
    ponderada["peso"] = t["peso"].values

    agg = ponderada.groupby("route_id").sum()
    return agg[depot_ids].div(agg["peso"], axis=0)
