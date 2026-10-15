"""
Etapa 4 de la metodologia - ICS2122 Capstone Buses Electricos (ver docs/context/01_como_funciona.md).

Programacion de la carga en el electroterminal: dadas las ventanas de carga de la Etapa 3 (llegada a_w, hora
limite d_w, energia E_w), decide cuando carga cada bus para minimizar energia y buses de reserva sin superar los
puestos. Compara dos politicas sobre LAS MISMAS ventanas:

E2-FIFO (linea de comparacion). Cada ventana, por orden de llegada, carga a plena potencia y al minuto en el primer
    tramo continuo con puesto libre dentro de [a_w, a_w + 24 h) (si no hay, en los minutos libres que encuentre),
    con la logica de puestos del caso base (funciones buscar_slot, reservar y costo_energia de 10-). Si la carga
    termina despues de d_w, un bus de reserva ya cargado cubre la salida (vehicle_fixed_cost).

E2 (modelo agregado). 24 h de una vez en bloques de Delta minutos, modulo 24 h:
    min  sum_{w,t} p_t e_wt + C_bus sum_w r_w + M sum_w delta_w
    s.a. sum_t e_wt + delta_w = E_w                         (toda la energia del tramo se repone)
         0 <= e^dentro_wt <= P Delta alpha_wt                (alpha: fraccion del bloque dentro de [a_w, d_w))
         0 <= e^ext_wt    <= P Delta beta_wt                 (beta: fraccion dentro de la extension [d_w, a_w + 24 h))
         sum_t e^ext_wt <= E_w r_w                           (cargar despues de d_w exige reserva)
         sum_w e_wt <= P Delta kappa                         (puestos, escritos en energia)
         r_w binaria, delta_w >= 0
    Los bloques de borde se tratan con su fraccion exacta (sin redondear). Un bloque que contiene d_w tiene una
    parte dentro y otra en la extension: por eso cada bloque lleva dos variables (asi la FIFO es una solucion
    factible del modelo y E2 <= E2-FIFO). Se resuelve primero el LP (cota) y luego el MILP con la FIFO en la grilla
    como solucion inicial. Los eventos de carga (fixed_charge_cost) se cuentan despues: tramos contiguos de
    bloques con carga.

E2 detallado (--detallado). El agregado mas, por (ventana, bloque), una binaria de enchufe, el inicio de cada evento
    de carga con fixed_charge_cost en el objetivo y carga continua a plena potencia dentro del evento. Capacidad,
    reservas y deficit son los del agregado: la diferencia es solo la estructura de los eventos, que el agregado no ve.

Capacidad por minuto: la FIFO se valida al minuto. El agregado es exacto por bloque salvo en los bloques de borde;
se valida por bloque y se informa una realizacion por minuto (LP por bloque) con los minutos sobre los puestos.

Input:  results/instancia_<siglas>/etapa3/h<h>/tablas/ventanas.csv, data-filtrado/{depots,electricity_prices}.csv
Output: results/instancia_<siglas>/etapa4/h<h>_d<Delta>/
        tablas/{programa_FIFO,programa_E2,programa_E2_detallado (con --detallado),ocupacion_minutos,ocupacion_bloques,energia_por_tarifa,reservas,
                modelo,resumen}.csv
        graficos/{ocupacion_24h,energia_por_tarifa}.png (+ .csv con los datos de cada grafico)
        reporte.md

Uso:
    python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 15
    python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 5
    python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 15 --detallado
    python scripts/13-etapa4_programacion_carga.py --prueba --puestos-prueba 5      # prueba chica (ventanas de etapa3_prueba)
"""

import argparse
import importlib.util
import math
import sys
import time
from pathlib import Path

import gurobipy as gp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.sparse as sps
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import graficos as gr, instancia, medicion, parametros            # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP                # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "caso_base", Path(__file__).resolve().parent / "10-caso_base_carga_reactiva.py")
caso_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(caso_base)

DIA_MIN = 1440
EPS = 1e-6
TOL_E = 1e-4          # kWh bajo los cuales una variable de energia se considera cero


# --------------------------------------------------------------------------- #
# Segmentos: (ventana, bloque, parte dentro / extension) con su fraccion exacta
# --------------------------------------------------------------------------- #

def construir_segmentos(v, delta, kwh_min):
    """Una fila por (ventana, bloque desenrollado u, parte). lo/hi en minutos desenrollados; t = bloque del reloj.
    Dentro = [a, d) si d > a; extension = [max(a, d), a + 24 h)."""
    filas = []
    for w, (a, d) in enumerate(zip(v["llegada_min"].values, v["limite_min"].values)):
        partes = [(0, a, max(a, d)), (1, max(a, d), a + DIA_MIN)]
        u0, u1 = math.floor(a / delta), math.ceil((a + DIA_MIN) / delta)
        for u in range(u0, u1):
            b0, b1 = u * delta, (u + 1) * delta
            for parte, lo, hi in partes:
                lo2, hi2 = max(lo, b0), min(hi, b1)
                if hi2 - lo2 > 1e-9:
                    filas.append((w, u, parte, lo2, hi2))
    s = pd.DataFrame(filas, columns=["w", "u", "parte", "lo", "hi"])
    s["t"] = s["u"] % (DIA_MIN // delta)
    s["k"] = s["u"] - np.floor(v["llegada_min"].values[s["w"].values] / delta).astype(int)   # bloques desde la llegada
    s["ub"] = kwh_min * (s["hi"] - s["lo"])          # P * Delta * fraccion, en kWh
    return s


# --------------------------------------------------------------------------- #
# E2-FIFO: por orden de llegada, al minuto, con la logica de puestos del caso base
# --------------------------------------------------------------------------- #

def correr_fifo(sim, v):
    """Devuelve (filas por ventana, lista de (w, minutos, kWh por minuto))."""
    term = 0
    kwh_min = sim.kwh_min
    orden = np.lexsort((v["ventana_id"].values, v["llegada_min"].values))
    filas, cargas = [None] * len(v), []
    for w in orden:
        a, d, need = float(v["llegada_min"].iat[w]), float(v["limite_min"].iat[w]), float(v["kwh"].iat[w])
        t0 = int(math.ceil(a - 1e-9))
        m_fin = int(math.floor(a + DIA_MIN + 1e-9))       # ultimo minuto utilizable: m + 1 <= a + 24 h
        dwant = max(1, int(math.ceil(need / kwh_min - 1e-9)))
        slot = sim.buscar_slot(term, t0, m_fin - dwant, dwant, dwant) if m_fin - dwant >= t0 else None
        fragmentada = slot is None
        if not fragmentada:
            minutos = np.arange(slot[0], slot[0] + dwant)
        else:
            libres = [m for m in range(t0, m_fin) if sim.occ[term][m % DIA_MIN] < sim.kappa[term]]
            minutos = np.asarray(libres[:dwant], dtype=int)
        cargado = min(need, kwh_min * len(minutos))
        deficit = need - cargado
        if len(minutos):
            sim.reservar(term, minutos)
            costo = sim.costo_energia(minutos, cargado)
            e_min = np.full(len(minutos), kwh_min)
            e_min[-1] = cargado - kwh_min * (len(minutos) - 1)
            ini = float(minutos[0])
            fin = float(minutos[-1]) + 1 - (kwh_min - e_min[-1]) / kwh_min
            eventos = int(1 + (np.diff(minutos) > 1).sum())
        else:
            costo, e_min, ini, fin, eventos = 0.0, np.zeros(0), np.nan, np.nan, 0
        tarde = bool(len(minutos) and fin > d + 1e-9) or deficit > EPS
        filas[w] = dict(kwh_cargado=cargado, deficit_kwh=deficit, reserva=int(tarde), inicio_carga_min=ini,
                        fin_carga_min=fin, eventos=eventos, fragmentada=fragmentada, costo_energia_usd=costo)
        cargas.append((w, minutos, e_min))
    return pd.DataFrame(filas), cargas


def fifo_en_grilla(cargas, v, seg, delta):
    """Lleva la FIFO a las variables de segmento (para la solucion inicial y para comparar en la grilla). Cada minuto se
    reparte entre la parte dentro y la extension segun d_w."""
    idx = {(w, u, p): i for i, (w, u, p) in enumerate(zip(seg["w"].values, seg["u"].values, seg["parte"].values))}
    e = np.zeros(len(seg))
    lim = v["limite_min"].values
    for w, minutos, e_min in cargas:
        d = lim[w]
        for m, em in zip(minutos, e_min):
            u = m // delta
            frac_dentro = min(max(d - m, 0.0), 1.0)
            if frac_dentro >= 1 - 1e-9:
                e[idx[(w, u, 0)]] += em
            elif frac_dentro <= 1e-9:
                e[idx[(w, u, 1)]] += em
            else:
                e[idx[(w, u, 0)]] += em * frac_dentro
                e[idx[(w, u, 1)]] += em * (1 - frac_dentro)
    return e


# --------------------------------------------------------------------------- #
# E2: modelo agregado
# --------------------------------------------------------------------------- #

def desempate(seg):
    """Costo de desempate por kWh de cada segmento (parametros.DESEMPATE_USD_KWH_BLOQUE x bloques desde la llegada)."""
    return parametros.DESEMPATE_USD_KWH_BLOQUE * seg["k"].values


def resolver_agregado(seg, v, precio_bloque, cap_bloque, costos, e_ini, r_ini, d_ini, delta):
    """LP (cota, r continua) y luego MILP. Devuelve (e, r, delta, dict con estado, brecha y tiempos)."""
    nS, nW, nb = len(seg), len(v), DIA_MIN // delta
    E = v["kwh"].values
    A_en = sps.csr_matrix((np.ones(nS), (seg["w"].values, np.arange(nS))), shape=(nW, nS))
    ext = seg["parte"].values == 1
    A_ext = sps.csr_matrix((np.ones(ext.sum()), (seg["w"].values[ext], np.where(ext)[0])), shape=(nW, nS))
    A_cap = sps.csr_matrix((np.ones(nS), (seg["t"].values, np.arange(nS))), shape=(nb, nS))
    t0 = time.perf_counter()
    m = gp.Model()
    m.Params.OutputFlag = 0
    e = m.addMVar(nS, lb=0, ub=seg["ub"].values, obj=precio_bloque[seg["t"].values] + desempate(seg))
    r = m.addMVar(nW, lb=0, ub=1, obj=costos.vehicle_fixed_cost)
    dlt = m.addMVar(nW, lb=0, obj=parametros.PENALIZACION_DEFICIT_USD_KWH)
    m.addConstr(A_en @ e + dlt == E)
    m.addConstr(A_ext @ e - sps.diags(E) @ r <= 0)
    m.addConstr(A_cap @ e <= np.full(nb, cap_bloque))
    m.update()
    t_armado = time.perf_counter() - t0
    info = dict(variables=m.NumVars, binarias=nW, restricciones=m.NumConstrs, segundos_armado=round(t_armado, 2))

    m.optimize()
    assert m.Status == gp.GRB.OPTIMAL, f"El LP de la Etapa 4 no resolvio al optimo (status {m.Status})."
    info.update(cota_lp=m.ObjVal, segundos_lp=round(m.Runtime, 2), r_fraccionales_lp=int(((r.X > 1e-6) & (r.X < 1 - 1e-6)).sum()))

    r.VType = gp.GRB.BINARY
    e.Start, r.Start, dlt.Start = e_ini, r_ini, d_ini
    m.Params.MIPGap = parametros.GAP_MIP
    m.Params.TimeLimit = parametros.TIEMPO_LIMITE_S["agregado"]
    m.optimize()
    assert m.SolCount > 0, f"El MILP de la Etapa 4 no encontro solucion (status {m.Status})."
    estado = {gp.GRB.OPTIMAL: "optimo (brecha pedida)", gp.GRB.TIME_LIMIT: "limite de tiempo"}.get(m.Status, f"status {m.Status}")
    info.update(estado=estado, objetivo=m.ObjVal, desempate_usd=float(desempate(seg) @ e.X), cota_milp=m.ObjBound,
                brecha=m.MIPGap,
                segundos_milp=round(m.Runtime, 2), nodos=int(m.NodeCount))
    rx = np.round(r.X)
    assert np.all(np.abs(r.X - rx) < 1e-5), "Las reservas del MILP no son enteras."
    return np.where(e.X > TOL_E, e.X, 0.0), rx.astype(int), dlt.X, info


# --------------------------------------------------------------------------- #
# E2 detallado: el agregado + eventos de carga (P2)
# --------------------------------------------------------------------------- #

def pares_bloque(seg):
    """Un par (ventana, bloque desenrollado) por cada bloque en que la ventana puede cargar, con su energia maxima y
    los indices del bloque anterior y siguiente de la misma ventana (-1 si no hay)."""
    p = seg.groupby(["w", "u"], sort=True).agg(cap=("ub", "sum")).reset_index()
    p["id"] = np.arange(len(p))
    mismo_ant = np.r_[False, (p["w"].values[1:] == p["w"].values[:-1]) & (p["u"].values[1:] == p["u"].values[:-1] + 1)]
    mismo_sig = np.r_[mismo_ant[1:], False]
    p["ant"] = np.where(mismo_ant, p["id"] - 1, -1)
    p["sig"] = np.where(mismo_sig, p["id"] + 1, -1)
    par_de_seg = p.set_index(["w", "u"])["id"].reindex(pd.MultiIndex.from_arrays([seg["w"], seg["u"]])).values
    return p, par_de_seg


def y_desde_e(p, par_de_seg, e):
    """Enchufe y eventos implicados por una carga: y = bloque con carga; z = y sin carga en el bloque anterior."""
    y = (np.bincount(par_de_seg, weights=e, minlength=len(p)) > TOL_E).astype(float)
    ant = p["ant"].values
    z = np.where(ant >= 0, np.clip(y - y[np.maximum(ant, 0)], 0, 1), y)
    return y, z


def resolver_detallado(seg, v, precio_bloque, cap_bloque, costos, inicios, delta):
    """Modelo detallado: el agregado mas, por (ventana, bloque), y = enchufado (binaria) y z = inicio de evento
    (fixed_charge_cost en el objetivo). Solo se carga enchufado (e <= tope * y) y la carga es continua: en un bloque
    interior de un evento (enchufado antes, ahora y despues) el bus carga a plena potencia todo el bloque. La capacidad,
    las reservas y el deficit son los del agregado. inicios: lista de soluciones iniciales (e, r, deficit)."""
    nS, nW, nb = len(seg), len(v), DIA_MIN // delta
    E = v["kwh"].values
    p, par_de_seg = pares_bloque(seg)
    nP = len(p)
    ant, sig, cap = p["ant"].values, p["sig"].values, p["cap"].values
    t0 = time.perf_counter()
    A_en = sps.csr_matrix((np.ones(nS), (seg["w"].values, np.arange(nS))), shape=(nW, nS))
    ext = seg["parte"].values == 1
    A_ext = sps.csr_matrix((np.ones(ext.sum()), (seg["w"].values[ext], np.where(ext)[0])), shape=(nW, nS))
    A_cap = sps.csr_matrix((np.ones(nS), (seg["t"].values, np.arange(nS))), shape=(nb, nS))
    S_par = sps.csr_matrix((np.ones(nS), (par_de_seg, np.arange(nS))), shape=(nP, nS))       # suma de e por par
    Y_seg = sps.csr_matrix((seg["ub"].values, (np.arange(nS), par_de_seg)), shape=(nS, nP))  # tope * y por segmento
    con_ant = np.where(ant >= 0)[0]
    D_ant = sps.csr_matrix((np.ones(len(con_ant)), (con_ant, ant[con_ant])), shape=(nP, nP))  # y del bloque anterior
    interior = np.where((ant >= 0) & (sig >= 0))[0]
    I_sel = sps.csr_matrix((np.ones(len(interior)), (np.arange(len(interior)), interior)), shape=(len(interior), nP))
    I_vec = sps.csr_matrix((np.ones(3 * len(interior)), (np.repeat(np.arange(len(interior)), 3),
                                                        np.column_stack([ant[interior], interior, sig[interior]]).ravel())),
                           shape=(len(interior), nP))

    m = gp.Model()
    m.Params.OutputFlag = 0
    e = m.addMVar(nS, lb=0, ub=seg["ub"].values, obj=precio_bloque[seg["t"].values] + desempate(seg))
    r = m.addMVar(nW, vtype=gp.GRB.BINARY, obj=costos.vehicle_fixed_cost)
    dlt = m.addMVar(nW, lb=0, obj=parametros.PENALIZACION_DEFICIT_USD_KWH)
    y = m.addMVar(nP, vtype=gp.GRB.BINARY)
    z = m.addMVar(nP, lb=0, ub=1, obj=costos.fixed_charge_cost)
    m.addConstr(A_en @ e + dlt == E)
    m.addConstr(A_ext @ e - sps.diags(E) @ r <= 0)
    m.addConstr(A_cap @ e <= np.full(nb, cap_bloque))
    m.addConstr(e - Y_seg @ y <= 0)                                     # solo se carga enchufado
    m.addConstr(z - y + D_ant @ y >= 0)                                 # z = 1 si se enchufa y antes no lo estaba
    cap_i = cap[interior]
    m.addConstr((I_sel @ S_par) @ e - (sps.diags(cap_i) @ I_vec) @ y >= -2 * cap_i)   # carga continua en el interior
    m.update()
    info = dict(variables=m.NumVars, binarias=nW + nP, restricciones=m.NumConstrs,
                segundos_armado=round(time.perf_counter() - t0, 2))

    m.NumStart = len(inicios)
    for k, (e0, r0, d0) in enumerate(inicios):
        m.Params.StartNumber = k
        y0, z0 = y_desde_e(p, par_de_seg, e0)
        e.Start, r.Start, dlt.Start, y.Start, z.Start = e0, r0, d0, y0, z0
    m.Params.MIPGap = parametros.GAP_MIP
    m.Params.TimeLimit = parametros.TIEMPO_LIMITE_S["detallado"]
    m.optimize()
    assert m.SolCount > 0, f"El modelo detallado no encontro solucion (status {m.Status})."
    estado = {gp.GRB.OPTIMAL: "optimo (brecha pedida)", gp.GRB.TIME_LIMIT: "limite de tiempo"}.get(m.Status, f"status {m.Status}")
    rx = np.round(r.X)
    assert np.all(np.abs(r.X - rx) < 1e-5), "Las reservas del modelo detallado no son enteras."
    info.update(estado=estado, objetivo=m.ObjVal, desempate_usd=float(desempate(seg) @ e.X),
                eventos_usd=float(costos.fixed_charge_cost * z.X.sum()), cota_milp=m.ObjBound, brecha=m.MIPGap,
                segundos_milp=round(m.Runtime, 2), nodos=int(m.NodeCount))
    return np.where(e.X > TOL_E, e.X, 0.0), rx.astype(int), dlt.X, info


def programa_desde_segmentos(seg, e, v, kwh_min):
    """Por ventana: kWh, inicio y fin de la carga (borde de los segmentos con carga) y eventos (tramos contiguos)."""
    s = seg.assign(e=e)
    s = s[s["e"] > TOL_E].sort_values(["w", "lo"])
    filas = {}
    for w, g in s.groupby("w", sort=False):
        lo, hi = g["lo"].values, g["hi"].values
        cortes = (lo[1:] - hi[:-1]) > 1e-9                # hay un hueco sin carga entre dos segmentos
        filas[w] = dict(kwh_cargado=g["e"].sum(), inicio_carga_min=lo[0], fin_carga_min=hi[-1],
                        eventos=int(1 + cortes.sum()))
    out = pd.DataFrame([filas.get(w, dict(kwh_cargado=0.0, inicio_carga_min=np.nan, fin_carga_min=np.nan, eventos=0))
                        for w in range(len(v))])
    return out


def realizacion_por_minuto(seg, e, delta, kappa, kwh_min):
    """Para cada bloque, el mejor reparto por minuto de la carga del agregado (LP de transporte): cada bus a lo mas un
    puesto por minuto, dentro de su parte del bloque. Devuelve la ocupacion por minuto del dia (puede superar kappa en
    bloques de borde: eso es lo que se informa)."""
    occ = np.zeros(DIA_MIN)
    s = seg.assign(e=e)
    s = s[s["e"] > TOL_E]
    for t, g in s.groupby("t"):
        base = t * delta
        lo = g["lo"].values - g["u"].values * delta + base       # al reloj
        hi = g["hi"].values - g["u"].values * delta + base
        D = g["e"].values / kwh_min                               # minutos-puesto que necesita cada segmento
        nj = len(g)
        mins = np.arange(base, base + delta)
        ov = np.clip(np.minimum(hi[:, None], mins[None, :] + 1) - np.maximum(lo[:, None], mins[None, :]), 0, 1)
        assert np.all(D <= ov.sum(axis=1) + 1e-6), f"Bloque {t}: un segmento carga mas que su fraccion del bloque."
        nvar = nj * delta
        # variables y_jm (fila j, minuto m) y holgura s_m sobre kappa
        A_eq = sps.hstack([sps.kron(sps.eye(nj), np.ones((1, delta))), sps.csr_matrix((nj, delta))])
        A_ub = sps.hstack([sps.kron(np.ones((1, nj)), sps.eye(delta)), -sps.eye(delta)])
        c = np.r_[np.zeros(nvar), np.ones(delta)]
        bounds = np.c_[np.zeros(nvar + delta), np.r_[ov.ravel(), np.full(delta, np.inf)]]
        res = linprog(c, A_ub=A_ub, b_ub=np.full(delta, float(kappa)), A_eq=A_eq, b_eq=np.minimum(D, ov.sum(axis=1)),
                      bounds=bounds, method="highs")
        assert res.status == 0, f"La realizacion por minuto del bloque {t} no resolvio ({res.message})."
        occ[base:base + delta] = res.x[:nvar].reshape(nj, delta).sum(axis=0)
    return occ


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #

def energia_por_periodo(precios, e_por_minuto):
    """kWh y costo por periodo tarifario (electricity_prices.csv)."""
    filas = []
    for r in precios.itertuples():
        sl = slice(int(r.start_hour) * 60, int(r.end_hour) * 60)
        kwh = float(e_por_minuto[sl].sum())
        filas.append(dict(periodo=r.period_id, horas=f"{int(r.start_hour):02d}-{int(r.end_hour):02d}",
                          precio_usd_kwh=r.price_usd_kwh, kwh=kwh, costo_usd=kwh * r.price_usd_kwh))
    return pd.DataFrame(filas)


def energia_minuto_fifo(cargas):
    em = np.zeros(DIA_MIN)
    for _, minutos, e_min in cargas:
        np.add.at(em, np.asarray(minutos, dtype=int) % DIA_MIN, e_min)
    return em


def energia_minuto_segmentos(seg, e):
    """Reparte la energia de cada segmento uniformemente en sus minutos (solo para agregar por periodo tarifario:
    los periodos cambian en horas exactas, asi que el resultado por periodo es exacto)."""
    em = np.zeros(DIA_MIN)
    s = seg.assign(e=e)
    for r in s[s["e"] > TOL_E].itertuples():
        m0, m1 = int(math.floor(r.lo)), int(math.ceil(r.hi))
        ms = np.arange(m0, m1)
        ov = np.clip(np.minimum(r.hi, ms + 1) - np.maximum(r.lo, ms), 0, None)
        np.add.at(em, ms % DIA_MIN, r.e * ov / ov.sum())
    return em


def graficar_ocupacion(occ_fifo, occ_e2, occ_det, kappa, tarifa, path_png, titulo):
    horas = np.arange(DIA_MIN) / 60
    fig, ax = plt.subplots(figsize=(11, 3.8))
    caro = tarifa >= tarifa.max() - 1e-9
    techo = max(kappa, occ_fifo.max(), occ_e2.max(), 0 if occ_det is None else occ_det.max()) * 1.15
    ax.fill_between(horas, 0, techo, where=caro, color=gr.PUNTA, alpha=0.08, step="post", linewidth=0,
                    label="tarifa punta")
    ax.plot(horas, occ_fifo, color=gr.ESCENARIO["E2-FIFO"], linewidth=1.2, drawstyle="steps-post",
            label="E2-FIFO (orden de llegada)")
    ax.plot(horas, occ_e2, color=gr.ESCENARIO["E2"], linewidth=1.6, drawstyle="steps-post", label="E2 (programada)")
    if occ_det is not None:
        ax.plot(horas, occ_det, color=gr.CATEGORICOS[6], linewidth=1.2, drawstyle="steps-post", label="E2 detallado")
    ax.axhline(kappa, color=gr.PUESTOS, linestyle="--", linewidth=1, label=f"{kappa} puestos")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_ylim(0, techo)
    ax.set_xlabel("Hora del dia")
    ax.set_ylabel("buses cargando")
    ax.set_title(titulo, fontsize=10, loc="left")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False)
    gr.estilo(ax)
    datos = pd.DataFrame({"minuto": np.arange(DIA_MIN), "precio_usd_kwh": tarifa, "fifo": occ_fifo,
                          "e2": np.round(occ_e2, 4), "puestos": kappa})
    if occ_det is not None:
        datos.insert(4, "e2_detallado", np.round(occ_det, 4))
    gr.guardar(fig, path_png, datos)


def graficar_tarifa(tabla, path_png, titulo):
    x = np.arange(len(tabla))
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.bar(x - 0.2, tabla["kwh_fifo"] / 1000, 0.38, color=gr.ESCENARIO["E2-FIFO"], label="E2-FIFO")
    ax.bar(x + 0.2, tabla["kwh_e2"] / 1000, 0.38, color=gr.ESCENARIO["E2"], label="E2")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{p}\n{h} h\n{pr:.2f} USD/kWh" for p, h, pr in
                        zip(tabla["periodo"], tabla["horas"], tabla["precio_usd_kwh"])], fontsize=8)
    ax.set_ylabel("MWh cargados")
    ax.set_title(titulo, fontsize=10, loc="left")
    ax.legend(fontsize=8, frameon=False)
    gr.estilo(ax)
    gr.guardar(fig, path_png, tabla.round(3))


def resumen_politica(nombre, prog, v, occ_min, kappa, costos, P, segundos):
    """Cifras de una politica con las mismas definiciones para FIFO y E2."""
    noct = v["tipo"].values == "nocturna"
    res = prog["reserva"].values.astype(bool)
    dia = ~noct
    # espera en el patio de dia: d - a - E/P (la parte de la ventana que el bus no esta cargando a plena potencia)
    espera_dia = np.clip(v["limite_min"].values - v["llegada_min"].values - v["kwh"].values / P * 60, 0, None)[dia].sum()
    # espera nocturna "original" (como la cola del caso base): de la llegada al inicio de la primera carga
    espera_noche = np.nan_to_num(prog["inicio_carga_min"].values - v["llegada_min"].values)[noct].clip(0).sum()
    return dict(
        politica=nombre, ventanas=len(v), kwh_necesarios=round(v["kwh"].sum(), 2),
        kwh_cargados=round(prog["kwh_cargado"].sum(), 2), kwh_deficit=round(prog["deficit_kwh"].sum(), 4),
        costo_energia_usd=round(prog["costo_energia_usd"].sum(), 2),
        reservas_intermedias=int(res[dia].sum()), reservas_nocturnas=int(res[noct].sum()), reservas=int(res.sum()),
        eventos=int(prog["eventos"].sum()), costo_eventos_usd=round(prog["eventos"].sum() * costos.fixed_charge_cost, 2),
        espera_patio_dia_min=round(espera_dia, 1), espera_patio_noche_hasta_carga_min=round(espera_noche, 1),
        uso_maximo_pct=round(occ_min.max() / kappa * 100, 1),
        minutos_saturados=int((occ_min >= kappa - 1e-6).sum()),
        minutos_sobre_puestos=int((occ_min > kappa + 1e-6).sum()), segundos=round(segundos, 2))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terminal", default=parametros.TERMINAL_INSTANCIA, help="depot_id del electroterminal.")
    parser.add_argument("--holgura", type=float, default=parametros.HOLGURAS_RECARGA_MIN[0],
                        help="Holgura de la Etapa 3 cuyas ventanas se programan (lee etapa3/h<h>/).")
    parser.add_argument("--delta", type=int, default=parametros.DELTA_MIN, help="Largo del bloque en minutos.")
    parser.add_argument("--prueba", action="store_true", help="Lee las ventanas de etapa3_prueba/ y escribe en etapa4_prueba/.")
    parser.add_argument("--puestos-prueba", type=int, default=None,
                        help="SOLO PRUEBAS: reemplaza los puestos del terminal para forzar congestion.")
    parser.add_argument("--detallado", action="store_true",
                        help="Corre ademas el modelo detallado (eventos de carga en el objetivo, carga continua) y lo "
                             "compara con el agregado.")
    args = parser.parse_args()
    t_inicio = time.perf_counter()
    delta, h_txt = args.delta, f"{args.holgura:g}"
    assert 60 % delta == 0, f"Delta = {delta} min no divide la hora: las tarifas cambian en horas exactas."
    prueba = args.prueba or args.puestos_prueba is not None

    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    costos = parametros.cargar_costos()
    patios = instancia.patios_terminal(depots, args.terminal)
    nombre = instancia.nombre_terminal(depots, patios)
    carpeta = instancia.carpeta_instancia(depots, args.terminal)
    entrada = carpeta / ("etapa3_prueba" if args.prueba else "etapa3") / f"h{h_txt}" / "tablas" / "ventanas.csv"
    assert entrada.exists(), f"No existen las ventanas de la Etapa 3 ({entrada}): correr antes 12- con --holgura {h_txt}."
    salida = carpeta / ("etapa4_prueba" if prueba else "etapa4") / f"h{h_txt}_d{delta}"
    tablas, graficos = salida / "tablas", salida / "graficos"
    for d in (tablas, graficos):
        d.mkdir(parents=True, exist_ok=True)

    v = pd.read_csv(entrada, sep=CSV_SEP)
    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    depots_t = depots[depots["depot_id"].astype(str).isin(patios)].reset_index(drop=True)
    unir = [d for d in parametros.ELECTROTERMINALES_UNIDOS if d in patios]
    tarifa = caso_base.cargar_tarifa()
    sim = caso_base.Simulador(ex, depots_t, costos, 1.0, unir, tarifa, set())
    if args.puestos_prueba is not None:
        sim.kappa[0] = args.puestos_prueba
        print(f"  *** PRUEBA: puestos reemplazados por {args.puestos_prueba} (NO es la instancia real) ***")
    kappa = sim.kappa[0]
    P = costos.charge_power_kw
    kwh_min = sim.kwh_min
    nb = DIA_MIN // delta
    precio_bloque = tarifa[np.arange(nb) * delta]
    for t in range(nb):
        assert np.all(tarifa[t * delta:(t + 1) * delta] == precio_bloque[t]), "La tarifa cambia dentro de un bloque."
    cap_bloque = kwh_min * delta * kappa

    print(f"=== ETAPA 4: programacion de la carga (terminal {nombre}, {kappa} puestos, holgura {h_txt} min, "
          f"Delta {delta} min) ===\n")
    carga = v["kwh"].sum() / (kappa * P * 24)
    print(f"  Ventanas: {len(v):,} ({(v['tipo'] == 'intermedia').sum():,} intermedias, {(v['tipo'] == 'nocturna').sum():,} "
          f"nocturnas) | energia a reponer {v['kwh'].sum() / 1000:,.1f} MWh")
    print(f"  Chequeo previo: energia / capacidad de 24 h = {carga:.1%} "
          f"({kappa} puestos x {P:.0f} kW x 24 h = {kappa * P * 24 / 1000:,.1f} MWh)")

    # --- E2-FIFO ---
    t0 = time.perf_counter()
    prog_f, cargas = correr_fifo(sim, v)
    t_fifo = time.perf_counter() - t0
    occ_f = sim.occ[0].astype(float)
    assert occ_f.max() <= kappa, "FIFO: ocupacion por minuto sobre los puestos."
    assert abs(prog_f["kwh_cargado"].sum() + prog_f["deficit_kwh"].sum() - v["kwh"].sum()) < 1e-6 * len(v), \
        "FIFO: energia cargada + deficit != energia consumida."
    print(f"\n--- E2-FIFO ({t_fifo:.1f} s): reservas {int(prog_f['reserva'].sum()):,} | energia "
          f"{prog_f['costo_energia_usd'].sum():,.0f} USD | deficit {prog_f['deficit_kwh'].sum():,.1f} kWh")
    print("  [OK] FIFO: ocupacion <= puestos en cada minuto | energia cargada + deficit = consumida.")

    # --- Grilla ---
    seg = construir_segmentos(v, delta, kwh_min)
    e_f = fifo_en_grilla(cargas, v, seg, delta)
    assert np.all(e_f <= seg["ub"].values + 1e-6), "FIFO en la grilla: un segmento supera P x Delta x fraccion."
    ocup_bloque_f = np.bincount(seg["t"].values, weights=e_f, minlength=nb)
    assert ocup_bloque_f.max() <= cap_bloque + 1e-6, "FIFO en la grilla: un bloque supera la capacidad."
    costo_grilla_f = float((precio_bloque[seg["t"].values] * e_f).sum())
    assert abs(costo_grilla_f - prog_f["costo_energia_usd"].sum()) < 1e-6 * max(1.0, costo_grilla_f), \
        "El costo de la FIFO en la grilla no calza con el costo al minuto."
    r_f = prog_f["reserva"].values.astype(float)
    d_f = prog_f["deficit_kwh"].values
    obj_f = costo_grilla_f + costos.vehicle_fixed_cost * r_f.sum() + parametros.PENALIZACION_DEFICIT_USD_KWH * d_f.sum()
    obj_f_modelo = obj_f + float(desempate(seg) @ e_f)          # el mismo objetivo que ve el MILP (con desempate)
    print(f"  [OK] FIFO en la grilla de {delta} min: factible para el modelo agregado y mismo costo de energia "
          f"(energia + reservas: {obj_f:,.2f} USD).")

    # --- E2 agregado ---
    print(f"\n--- E2 agregado: {len(seg):,} variables de energia, {len(v):,} binarias, {nb} bloques ---")
    e2, r2, d2, info = resolver_agregado(seg, v, precio_bloque, cap_bloque, costos, e_f, r_f, d_f, delta)
    obj_2 = info["objetivo"] - info["desempate_usd"]                    # energia + reservas (+ deficit), sin desempate
    print(f"  LP (cota): {info['cota_lp']:,.2f} USD en {info['segundos_lp']:.1f} s | MILP: {obj_2:,.2f} USD "
          f"(+ desempate {info['desempate_usd']:.2f}), {info['estado']}, brecha {info['brecha']:.3%}, "
          f"{info['segundos_milp']:.1f} s")
    kwh2 = e2.sum()
    assert abs(kwh2 + d2.sum() - v["kwh"].sum()) < 1e-3 * len(v), "E2: energia cargada + deficit != energia consumida."
    ocup_bloque_2 = np.bincount(seg["t"].values, weights=e2, minlength=nb)
    assert ocup_bloque_2.max() <= cap_bloque * (1 + 1e-6) + 1e-6, "E2: un bloque supera la capacidad en energia."
    assert info["objetivo"] <= obj_f_modelo + 1e-6 * abs(obj_f_modelo) + 1e-3, (
        f"E2 ({info['objetivo']:,.2f}) es peor que E2-FIFO en la grilla ({obj_f_modelo:,.2f}): la FIFO era solucion inicial.")
    print(f"  [OK] E2: energia cargada + deficit = consumida | ocupacion <= puestos en cada bloque | "
          f"E2 <= E2-FIFO en la grilla (energia + reservas: {obj_2:,.2f} vs {obj_f:,.2f} USD).")
    if d2.sum() > 1e-3:
        print(f"  [AVISO] E2 deja {d2.sum():,.1f} kWh de deficit: la energia no cabe en los puestos en 24 h.")

    t0 = time.perf_counter()
    occ_2 = realizacion_por_minuto(seg, e2, delta, kappa, kwh_min)
    t_real = time.perf_counter() - t0
    print(f"  Realizacion por minuto de E2 ({t_real:.1f} s): maximo {occ_2.max():.2f} buses; minutos sobre "
          f"{kappa} puestos: {int((occ_2 > kappa + 1e-6).sum())} (solo pueden aparecer en bloques de borde).")

    # --- E2 detallado (opcional) ---
    if args.detallado:
        print("\n--- E2 detallado: eventos de carga en el objetivo, carga continua dentro del evento ---")
        e_d, r_d, d_d, info_d = resolver_detallado(seg, v, precio_bloque, cap_bloque, costos,
                                                   [(e_f, r_f, d_f), (e2, r2.astype(float), d2)], delta)
        obj_d = info_d["objetivo"] - info_d["desempate_usd"]                  # energia + reservas + eventos
        obj_d_er = obj_d - info_d["eventos_usd"]                              # energia + reservas
        eventos_f = float(costos.fixed_charge_cost * prog_f["eventos"].sum())
        print(f"  Detallado: {info_d['binarias']:,} binarias | {obj_d:,.2f} USD (energia + reservas {obj_d_er:,.2f} + "
              f"eventos {info_d['eventos_usd']:,.2f}), {info_d['estado']}, brecha {info_d['brecha']:.3%}, "
              f"{info_d['segundos_milp']:.1f} s")
        assert abs(e_d.sum() + d_d.sum() - v["kwh"].sum()) < 1e-3 * len(v), \
            "Detallado: energia cargada + deficit != energia consumida."
        ocup_bloque_d = np.bincount(seg["t"].values, weights=e_d, minlength=nb)
        assert ocup_bloque_d.max() <= cap_bloque * (1 + 1e-6) + 1e-6, "Detallado: un bloque supera la capacidad en energia."
        assert info_d["objetivo"] <= obj_f_modelo + eventos_f + 1e-6 * abs(obj_f_modelo) + 1e-3, (
            "Detallado peor que E2-FIFO con sus eventos: la FIFO era solucion inicial.")
        assert info["cota_lp"] <= info_d["objetivo"] - info_d["eventos_usd"] + 1e-6 * abs(obj_f_modelo) + 1e-3, (
            "La cota LP del agregado supera al detallado sin eventos: el agregado deberia ser una relajacion.")
        print(f"  [OK] Detallado: energia cargada + deficit = consumida | ocupacion <= puestos en cada bloque | "
              f"detallado <= E2-FIFO con eventos ({obj_d:,.2f} <= {obj_f + eventos_f:,.2f}) | cota LP del agregado "
              f"<= detallado sin eventos ({info['cota_lp']:,.2f} <= {obj_d_er:,.2f}).")
        if d_d.sum() > 1e-3:
            print(f"  [AVISO] El detallado deja {d_d.sum():,.1f} kWh de deficit.")
        t0 = time.perf_counter()
        occ_d = realizacion_por_minuto(seg, e_d, delta, kappa, kwh_min)
        print(f"  Realizacion por minuto del detallado ({time.perf_counter() - t0:.1f} s): maximo {occ_d.max():.2f} "
              f"buses; minutos sobre {kappa} puestos: {int((occ_d > kappa + 1e-6).sum())}.")

    # --- Programas por ventana ---
    p2 = programa_desde_segmentos(seg, e2, v, kwh_min)
    em2 = energia_minuto_segmentos(seg, e2)
    costo_w2 = np.bincount(seg["w"].values, weights=precio_bloque[seg["t"].values] * e2, minlength=len(v))
    p2 = p2.assign(deficit_kwh=d2, reserva=r2, costo_energia_usd=costo_w2)
    base = v[["ventana_id", "bus", "tipo", "tramo_id", "llegada_min", "limite_min", "kwh"]]
    prog_f_out = pd.concat([base, prog_f], axis=1)
    prog_2_out = pd.concat([base, p2], axis=1)
    for p in (prog_f_out, prog_2_out):
        p["termina_a_tiempo"] = p["fin_carga_min"] <= p["limite_min"] + 1e-6
    assert (prog_2_out.loc[~prog_2_out["termina_a_tiempo"] & (prog_2_out["kwh_cargado"] > TOL_E), "reserva"] == 1).all(), \
        "E2: una ventana carga despues de su hora limite sin reserva."
    if args.detallado:
        p_d = programa_desde_segmentos(seg, e_d, v, kwh_min)
        costo_wd = np.bincount(seg["w"].values, weights=precio_bloque[seg["t"].values] * e_d, minlength=len(v))
        prog_d_out = pd.concat([base, p_d.assign(deficit_kwh=d_d, reserva=r_d, costo_energia_usd=costo_wd)], axis=1)
        prog_d_out["termina_a_tiempo"] = prog_d_out["fin_carga_min"] <= prog_d_out["limite_min"] + 1e-6
        tarde = ~prog_d_out["termina_a_tiempo"] & (prog_d_out["kwh_cargado"] > TOL_E)
        assert (prog_d_out.loc[tarde, "reserva"] == 1).all(), \
            "Detallado: una ventana carga despues de su hora limite sin reserva."

    t_total = time.perf_counter() - t_inicio
    mem = medicion.pico_memoria_mb()
    res_f = resumen_politica("E2-FIFO", prog_f_out, v, occ_f, kappa, costos, P, t_fifo)
    res_2 = resumen_politica("E2", prog_2_out, v, occ_2, kappa, costos, P, info["segundos_milp"] + info["segundos_lp"])
    filas_res = [res_f, res_2]
    if args.detallado:
        filas_res.append(resumen_politica("E2-detallado", prog_d_out, v, occ_d, kappa, costos, P,
                                          info_d["segundos_milp"]))
    resumen = pd.DataFrame(filas_res)
    resumen.insert(0, "terminal", nombre)
    resumen.insert(1, "holgura_min", args.holgura)
    resumen.insert(2, "delta_min", delta)
    resumen.insert(3, "puestos", kappa)
    resumen.insert(4, "prueba", int(prueba))
    resumen["energia_sobre_capacidad_pct"] = round(carga * 100, 2)
    resumen["costo_medio_energia_usd_kwh"] = (resumen["costo_energia_usd"] / resumen["kwh_cargados"]).round(4)

    em_f = energia_minuto_fifo(cargas)
    precios = pd.read_csv(DATA_FILTRADO / "electricity_prices.csv", sep=CSV_SEP)
    tf, t2 = energia_por_periodo(precios, em_f), energia_por_periodo(precios, em2)
    tarifa_tab = tf[["periodo", "horas", "precio_usd_kwh"]].assign(
        kwh_fifo=tf["kwh"], costo_fifo_usd=tf["costo_usd"], kwh_e2=t2["kwh"], costo_e2_usd=t2["costo_usd"])
    columnas_kwh = ["kwh_fifo", "kwh_e2"]
    if args.detallado:
        td = energia_por_periodo(precios, energia_minuto_segmentos(seg, e_d))
        tarifa_tab = tarifa_tab.assign(kwh_e2_detallado=td["kwh"], costo_e2_detallado_usd=td["costo_usd"])
        columnas_kwh.append("kwh_e2_detallado")
    valle = tarifa_tab["precio_usd_kwh"] <= tarifa_tab["precio_usd_kwh"].min() * 1.2
    resumen["pct_energia_valle"] = [round(tarifa_tab.loc[valle, c].sum() / tarifa_tab[c].sum() * 100, 2)
                                    for c in columnas_kwh]
    resumen["segundos_total_script"] = round(t_total, 1)
    resumen["memoria_mb"] = round(mem)

    modelo = pd.DataFrame([
        dict(modelo="E2-FIFO", estado="heuristica (sin optimizacion)", objetivo_usd=round(obj_f, 2), cota_usd=np.nan,
             brecha=np.nan, segundos=round(t_fifo, 2), variables=np.nan, binarias=np.nan, restricciones=np.nan),
        dict(modelo="E2 agregado - LP (cota)", estado="optimo", objetivo_usd=round(info["cota_lp"], 2),
             cota_usd=round(info["cota_lp"], 2), brecha=0.0, segundos=info["segundos_lp"], variables=info["variables"],
             binarias=0, restricciones=info["restricciones"]),
        dict(modelo="E2 agregado - MILP", estado=info["estado"], objetivo_usd=round(obj_2, 2),
             cota_usd=round(info["cota_milp"], 2), brecha=round(info["brecha"], 6), segundos=info["segundos_milp"],
             desempate_usd=round(info["desempate_usd"], 4),
             variables=info["variables"], binarias=info["binarias"], restricciones=info["restricciones"]),
    ])
    if args.detallado:
        modelo = pd.concat([modelo, pd.DataFrame([dict(
            modelo="E2 detallado - MILP", estado=info_d["estado"], objetivo_usd=round(obj_d, 2),
            cota_usd=round(info_d["cota_milp"], 2), brecha=round(info_d["brecha"], 6), segundos=info_d["segundos_milp"],
            desempate_usd=round(info_d["desempate_usd"], 4), eventos_usd=round(info_d["eventos_usd"], 2),
            variables=info_d["variables"], binarias=info_d["binarias"], restricciones=info_d["restricciones"])])],
            ignore_index=True)
    modelo.insert(0, "delta_min", delta)
    modelo.insert(0, "holgura_min", args.holgura)

    horas_bloque = np.arange(nb) * delta
    ocup_bloques = pd.DataFrame({"bloque": np.arange(nb), "inicio_min": horas_bloque,
                                 "hora": [f"{m // 60:02d}:{m % 60:02d}" for m in horas_bloque],
                                 "precio_usd_kwh": precio_bloque,
                                 "buses_equivalentes_fifo": ocup_bloque_f / (kwh_min * delta),
                                 "buses_equivalentes_e2": ocup_bloque_2 / (kwh_min * delta), "puestos": kappa})
    ocup_min = pd.DataFrame({"minuto": np.arange(DIA_MIN), "fifo": occ_f, "e2": np.round(occ_2, 4), "puestos": kappa})
    if args.detallado:
        ocup_bloques.insert(6, "buses_equivalentes_e2_detallado", ocup_bloque_d / (kwh_min * delta))
        ocup_min.insert(3, "e2_detallado", np.round(occ_d, 4))
        prog_d_out.round(4).to_csv(tablas / "programa_E2_detallado.csv", index=False, sep=CSV_SEP)
    reservas = resumen[["politica", "reservas_intermedias", "reservas_nocturnas", "reservas"]]

    prog_f_out.round(4).to_csv(tablas / "programa_FIFO.csv", index=False, sep=CSV_SEP)
    prog_2_out.round(4).to_csv(tablas / "programa_E2.csv", index=False, sep=CSV_SEP)
    ocup_min.to_csv(tablas / "ocupacion_minutos.csv", index=False, sep=CSV_SEP)
    ocup_bloques.round(4).to_csv(tablas / "ocupacion_bloques.csv", index=False, sep=CSV_SEP)
    tarifa_tab.round(3).to_csv(tablas / "energia_por_tarifa.csv", index=False, sep=CSV_SEP)
    reservas.to_csv(tablas / "reservas.csv", index=False, sep=CSV_SEP)
    modelo.to_csv(tablas / "modelo.csv", index=False, sep=CSV_SEP)
    resumen.to_csv(tablas / "resumen.csv", index=False, sep=CSV_SEP)
    graficar_ocupacion(occ_f, occ_2, occ_d if args.detallado else None, kappa, tarifa, graficos / "ocupacion_24h.png",
                       f"Buses cargando en {nombre}: por orden de llegada vs programada (holgura {h_txt} min, Delta {delta} min)")
    graficar_tarifa(tarifa_tab, graficos / "energia_por_tarifa.png",
                    f"Energia cargada por periodo tarifario en {nombre} (holgura {h_txt} min, Delta {delta} min)")

    tabla_md = resumen.set_index("politica")[["reservas_intermedias", "reservas_nocturnas", "costo_energia_usd",
                                              "costo_medio_energia_usd_kwh", "pct_energia_valle", "eventos",
                                              "kwh_deficit", "uso_maximo_pct", "minutos_saturados",
                                              "minutos_sobre_puestos"]].T
    lineas = [
        f"# Etapa 4 - Programacion de la carga, {nombre} (holgura {h_txt} min, Delta {delta} min, {kappa} puestos)",
        "" if not prueba else "\n**PRUEBA: no es la instancia real.**\n",
        f"- Ventanas: {len(v):,}; energia a reponer {v['kwh'].sum() / 1000:,.1f} MWh = {carga:.1%} de la capacidad de 24 h.",
        "",
        "## E2-FIFO vs E2",
        "",
        tabla_md.to_markdown(),
        "",
        "## Modelos (estado, brecha y tiempos)",
        "",
        modelo.to_markdown(index=False),
        "",
        "## Energia por periodo tarifario",
        "",
        tarifa_tab.round(1).to_markdown(index=False),
        "",
        "## Validaciones (todas pasaron)",
        "- FIFO: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = "
        "su costo al minuto.",
        "- E2: energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora "
        "limite lleva reserva; E2 <= E2-FIFO en la grilla.",
        f"- Realizacion por minuto de E2: {int((occ_2 > kappa + 1e-6).sum())} minutos sobre los puestos (maximo "
        f"{occ_2.max():.2f}); es el error del agregado en los bloques de borde.",
        "",
    ]
    if args.detallado:
        lineas += [
            "## Modelo detallado vs agregado",
            "",
            f"- Detallado: {info_d['estado']}, brecha {info_d['brecha']:.3%}, {info_d['segundos_milp']:.1f} s, "
            f"{info_d['binarias']:,} binarias. Objetivo {obj_d:,.2f} USD = energia + reservas {obj_d_er:,.2f} + "
            f"eventos {info_d['eventos_usd']:,.2f}.",
            f"- Agregado: energia + reservas {obj_2:,.2f} USD; con sus eventos contados despues: "
            f"{obj_2 + costos.fixed_charge_cost * p2['eventos'].sum():,.2f} USD.",
            f"- Realizacion por minuto del detallado: {int((occ_d > kappa + 1e-6).sum())} minutos sobre los puestos "
            f"(maximo {occ_d.max():.2f}).",
            "",
        ]
    lineas += [
        "## Tiempo y memoria",
        f"- FIFO {t_fifo:.1f} s | armado {info['segundos_armado']:.1f} s | LP {info['segundos_lp']:.1f} s | MILP "
        f"{info['segundos_milp']:.1f} s ({info['nodos']:,} nodos) | realizacion por minuto {t_real:.1f} s | total "
        f"{t_total:.1f} s | pico de memoria {mem:,.0f} MB.",
        "",
        "## Archivos",
        "- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, "
        "reserva, deficit y costo.",
        "- `tablas/ocupacion_minutos.csv` (FIFO exacta; E2 = realizacion por minuto), `tablas/ocupacion_bloques.csv`.",
        "- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.",
        "- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).",
    ]
    (salida / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")

    print("\n=== Resultado ===")
    print(resumen.set_index("politica").T.to_string())
    print(f"\n  -> {salida}")
    print(f"\n  Tiempo: {t_total:,.1f} s | pico de memoria: {mem:,.0f} MB")
    print("\n=== FIN ETAPA 4 ===")


if __name__ == "__main__":
    main()
