"""Brecha del modelo detallado de la Etapa 4.

El detallado tiene las restricciones del agregado mas los eventos de carga, asi que su costo es al menos la cota LP del
agregado mas un evento por cada ventana que carga. Toda ventana carga en una solucion que valga la pena (dejarla sin
cargar cuesta la penalizacion del deficit), de modo que esa cota es valida si la penalizacion supera el objetivo. Se
reporta la menor entre la brecha de Gurobi y la de esta cota.
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
