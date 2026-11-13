"""Instancia de un electroterminal: sus patios, su nombre, su carpeta de resultados y el filtro de sus jornadas.
Tras la Etapa 1 cada electroterminal es un subproblema independiente."""

import pandas as pd

from . import parametros
from .rutas import RESULTS_DIR


def patios_terminal(depots: pd.DataFrame, terminal: str) -> list:
    """depot_id (texto) de los patios que forman el electroterminal: los dos del terminal unido
    (parametros.ELECTROTERMINALES_UNIDOS) si `terminal` es uno de ellos, o solo `terminal`."""
    terminal = str(terminal)
    ids = depots["depot_id"].astype(str).tolist()
    assert terminal in ids, f"El terminal {terminal} no existe en depots.csv (disponibles: {ids})."
    if terminal in parametros.ELECTROTERMINALES_UNIDOS:
        return [d for d in ids if d in parametros.ELECTROTERMINALES_UNIDOS]
    return [terminal]


def nombre_terminal(depots: pd.DataFrame, patios: list) -> str:
    """Mismo nombre que usa el simulador del caso base (patios unidos con ' + ')."""
    d = depots[depots["depot_id"].astype(str).isin(patios)]
    return " + ".join(d["nombre"].tolist())


def siglas(nombre: str) -> str:
    """'La Reina' -> 'LR'; 'Los Espinos + Santa Rosa' -> 'LESR'."""
    return "".join(p[0].upper() for p in nombre.replace("+", " ").split())


def carpeta_instancia(depots: pd.DataFrame, terminal: str):
    """resultados/instancia_<siglas>/ del electroterminal (La Reina: resultados/instancia_LR/)."""
    carpeta = RESULTS_DIR / f"instancia_{siglas(nombre_terminal(depots, patios_terminal(depots, terminal)))}"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def filtrar_jornadas(j: pd.DataFrame, patios: list) -> pd.DataFrame:
    """Jornadas del VSP que salen de un patio del terminal. Exige que todas vuelvan al mismo terminal."""
    sel = j[j["depot_salida"].astype(str).isin(patios)].reset_index(drop=True)
    assert sel["depot_llegada"].astype(str).isin(patios).all(), (
        "Hay jornadas que salen del terminal y vuelven a otro: el terminal no es un subproblema independiente.")
    assert len(sel) > 0, f"No hay jornadas que salgan de los patios {patios}."
    return sel
