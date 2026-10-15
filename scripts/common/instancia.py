"""Instancia de un electroterminal: que patios lo forman, como se llama, donde
escribe sus resultados y como se filtran sus jornadas.

Tras la Etapa 1 cada electroterminal es un subproblema independiente: sus
jornadas salen y vuelven a el, cargan solo ahi y sus puestos no se comparten.
Por eso la instancia reducida es un electroterminal completo
(parametros.TERMINAL_INSTANCIA) y la entrega final repite lo mismo terminal
por terminal.
"""

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
    """results/instancia_<siglas>/ del electroterminal (La Reina: results/instancia_LR/)."""
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


def filtrar_rutas(j: pd.DataFrame, ex: pd.DataFrame, rutas: list) -> pd.DataFrame:
    """Solo para pruebas chicas: jornadas que tocan alguna de las rutas dadas (jornadas completas)."""
    rutas = {str(r) for r in rutas}
    exp_ruta = dict(zip(ex["expedicion_id"], ex["route_id"].astype(str)))
    toca = j["expedicion_ids"].map(lambda s: any(exp_ruta[e] in rutas for e in s.split(";")))
    sel = j[toca].reset_index(drop=True)
    assert len(sel) > 0, f"Ninguna jornada toca las rutas {sorted(rutas)}."
    return sel
