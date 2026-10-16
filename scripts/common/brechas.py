"""Brecha del modelo detallado de la Etapa 4 (ver docs/context/02_decisiones.md, G12).

El detallado tiene todas las restricciones del agregado mas los eventos de carga, asi que su costo es al menos
la cota LP del agregado mas el costo de un evento por cada ventana que carga. Toda ventana carga en una solucion
que valga la pena comparar: dejarla sin cargar cuesta la penalizacion del deficit por su energia, y si esa
penalizacion supera la mejor solucion encontrada, la cota es valida. Se reporta la mejor brecha disponible: la de
Gurobi o la de esta cota, la que sea menor.
"""

from . import parametros


def mejor_brecha(objetivo, cota_gurobi, cota_lp_agregado, kwh_ventanas, costo_evento):
    """objetivo y cotas en las mismas unidades del modelo (con desempate). kwh_ventanas: energia de cada ventana.
    Devuelve (brecha, cota usada, fuente, cota valida o None si no aplica)."""
    con_energia = [k for k in kwh_ventanas if k > 0]
    cota_valida = None
    if con_energia and parametros.PENALIZACION_DEFICIT_USD_KWH * min(con_energia) > objetivo:
        cota_valida = cota_lp_agregado + costo_evento * len(con_energia)
        assert cota_valida <= objetivo + 1e-6 * abs(objetivo) + 1e-3, (
            f"La cota valida ({cota_valida:,.2f}) supera la solucion del detallado ({objetivo:,.2f}): revisar el modelo.")
    if cota_valida is not None and cota_valida > cota_gurobi:
        cota, fuente = cota_valida, "cota valida (LP del agregado + un evento por ventana)"
    else:
        cota, fuente = cota_gurobi, "Gurobi"
    return (objetivo - cota) / abs(objetivo), cota, fuente, cota_valida
