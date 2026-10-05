"""
Etapa 4 del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md, seccion 4, Etapa 4, y docs/context/02_supuestos_y_decisiones.md, B12).

MILP de PROGRAMACION DE CARGA en una INSTANCIA REDUCIDA (no es el resultado de toda la red). Para un electroterminal
(el terminal unido Los Espinos + Santa Rosa, el mas exigido) decide CUANDO y CUANTO carga cada bus dentro de su ventana
en el patio (llegada hasta su primera salida del dia siguiente), minimizando energia (tarifa por bloque) + 5 USD por
evento de carga + 250 USD por bus de reserva, sin exceder los puestos. Se compara contra la politica reactiva
(Etapa 3) sobre exactamente los mismos buses y puestos.

Que es y que NO es "bloque": el MILP resuelve las 24 horas de una sola vez (no hay descomposicion temporal ni nada
se congela). Los bloques de BLOQUE_MILP_MIN minutos (96 por dia) son solo la unidad con que se mide el tiempo.

Formulacion (un terminal; bloques t modulo 96; ver 02, B12):
    min  sum_{b,t} p_t e_bt + c_fix sum z_bt + c_res sum r_b      (+ las cargas intermedias, fijas)
    s.a. sum_t e_bt = E_b                  (el bus vuelve exactamente al nivel: condicion ciclica)
         e_bt <= q y_bt                    (q = potencia x bloque = 45 kWh)
         y_bt <= r_b                       para t fuera de la ventana [llegada, salida) del bus
         sum_b y_bt <= kappa - f_t         (puestos, modulo 24 h; f_t = cargas intermedias de la reactiva)
         z_bt >= y_bt - y_b,t-1            (inicio de evento de carga)
         e_bt >= q (y_bt + y_b,t+1 - 1)    (evento continuo a plena potencia: solo su ultimo bloque puede ir parcial)
    r_b = 1 es un BUS DE RESERVA: el bus puede terminar de cargar despues de su salida (hasta 24 h desde su llegada) y
    su salida la cubre un bus de reserva ya cargado (misma regla que el simulador). La energia se carga igual y ocupa
    puestos: la holgura no regala energia.
La espera en cola NO esta en el objetivo; se reporta aparte como demora hasta iniciar la carga.

Instancia (docs/justificaciones/07, criterios): muestra de jornadas del VSP del terminal con semilla fija y anidada,
puestos proporcionales (kappa = N x puestos del terminal / buses del terminal en la red completa), chequeo de no
trivialidad (puestos saturados en >= UMBRAL_NO_TRIVIAL de los bloques en la reactiva).

Comparacion justa: el simulador real (Etapa 3, minuto a minuto) y la MISMA regla reactiva en bloques se corren sobre
la instancia. La reactiva en bloques es factible para el MILP y se le entrega como solucion inicial; el costo del MILP
debe ser <= al de ella (si no, hay un error).

Input:  data-processed/{expediciones,jornadas_<esc>}.csv, data-filtrado/{depots,electricity_prices}.csv,
        results/etapa3_carga_reactiva/tablas/{jornadas,eventos,ventanas}_<esc>_soc100.csv (solo para la
        proporcion de puestos y la tabla de representatividad), scripts/10-carga_reactiva.py (simulador)
Output: results/etapa4_milp_carga/tablas/{instancias,comparacion_reactiva_milp,tiempos_resolucion,representatividad,
            energia_por_tarifa,ocupacion_N<n>,programa_reactiva_N<n>,programa_milp_N<n>}.csv
        results/etapa4_milp_carga/graficos/{ocupacion_reactiva_vs_milp_N<n>,energia_por_tarifa,
            costo_reactiva_vs_milp,brecha_vs_N}.png
        results/etapa4_milp_carga/reporte.md

Uso:
    python scripts/11-milp_carga.py --n 10 --detalle --sin-salidas   # checkpoint chico, se revisa a mano
    python scripts/11-milp_carga.py                                  # escalera N = 30 / 50 / 100 / 200 / 400
    python scripts/11-milp_carga.py --n 200 --semilla 7              # otra semilla (variabilidad)
    python scripts/11-milp_carga.py --regenerar                      # graficos y reporte desde los CSV, sin resolver
"""

import argparse
import importlib.util
import math
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parametros                                                  # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, RESULTS_DIR, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa4_milp_carga")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)
RES3 = RESULTS_DIR / "etapa3_carga_reactiva" / "tablas"

DIA_MIN = 1440
B = parametros.BLOQUE_MILP_MIN
NB = DIA_MIN // B                                    # bloques por dia
EPS = 1e-6
COLOR_REACTIVA, COLOR_MILP = "#d95f02", "#2c6e8f"


# --------------------------------------------------------------------------- #
# Contexto: datos, simulador de la Etapa 3 y proporciones de la red completa
# --------------------------------------------------------------------------- #

def cargar_simulador():
    """Importa scripts/10-carga_reactiva.py (nombre con guion) sin modificarlo."""
    spec = importlib.util.spec_from_file_location("carga_reactiva", Path(__file__).resolve().parent / "10-carga_reactiva.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Contexto:
    pass


def cargar_contexto(mod, escenario):
    c = Contexto()
    c.escenario = escenario
    c.ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    c.ex_idx = {e: i for i, e in enumerate(c.ex["expedicion_id"].tolist())}
    c.depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    c.costos = parametros.cargar_costos()
    c.tarifa = mod.cargar_tarifa()
    c.unir_ids = [str(d) for d in parametros.ELECTROTERMINALES_UNIDOS]
    c.q = c.costos.charge_power_kw * B / 60.0                      # kWh por puesto y bloque (45)
    c.tb = np.array([c.tarifa[(k * B) % DIA_MIN] for k in range(NB)])
    c.es_valle = c.tb <= c.tarifa.min() * 1.2 + 1e-12
    # periodo tarifario de cada bloque
    p = pd.read_csv(DATA_FILTRADO / "electricity_prices.csv", sep=CSV_SEP)
    c.periodo_bloque = []
    for k in range(NB):
        h = (k * B) // 60
        fila = p[(p["start_hour"] <= h) & (h < p["end_hour"])].iloc[0]
        c.periodo_bloque.append(fila["period_id"])
    c.periodos = p["period_id"].tolist()
    c.precio_periodo = dict(zip(p["period_id"], p["price_usd_kwh"]))
    valle_min = c.tarifa <= c.tarifa.min() * 1.2 + 1e-12
    cum = np.concatenate([[0.0], np.cumsum(valle_min)])
    c.F_valle = lambda x: (np.asarray(x, float) // DIA_MIN) * cum[-1] + np.interp(np.asarray(x, float) % DIA_MIN, np.arange(DIA_MIN + 1), cum)

    # red completa: proporcion puestos/bus del terminal unido (se calcula, no se escribe a mano)
    caps = c.depots.set_index(c.depots["depot_id"].astype(str)).loc[c.unir_ids, "capacity"].astype(int)
    c.kappa_red = int(caps.sum())
    sfx = f"{escenario}_soc100"
    c.jr = pd.read_csv(RES3 / f"jornadas_{sfx}.csv", sep=CSV_SEP, dtype={"bus_origen": str, "jornada_id": str})
    c.ev_red = pd.read_csv(RES3 / f"eventos_{sfx}.csv", sep=CSV_SEP, dtype={"jornada_id": str})
    c.vent_red = pd.read_csv(RES3 / f"ventanas_{sfx}.csv", sep=CSV_SEP, dtype={"jornada_id": str})
    unidos = [n for n in set(c.jr["terminal"]) if " + " in n]
    assert len(unidos) == 1, "La corrida de la Etapa 3 no tiene exactamente un terminal unido: revisar el escenario."
    c.terminal = unidos[0]
    c.jr_t = c.jr[c.jr["terminal"] == c.terminal]
    c.n_final_red = len(c.jr_t)
    c.n_vsp_red = c.jr_t["bus_origen"].nunique()
    c.razon = c.kappa_red / c.n_final_red                          # puestos por bus tras la carga
    c.buses_por_vsp = c.n_final_red / c.n_vsp_red

    j = pd.read_csv(DATA_PROCESSED / f"jornadas_{escenario}.csv", sep=CSV_SEP, dtype={"depot_salida": str, "depot_llegada": str})
    j = j[j["depot_salida"].isin(c.unir_ids)].copy()
    j["_id"] = j["bus_id"].astype(int)
    c.jt = j.sort_values("_id").reset_index(drop=True)
    assert len(c.jt) == c.n_vsp_red, (f"El terminal unido tiene {len(c.jt)} jornadas en el VSP pero {c.n_vsp_red} en la "
                                      f"Etapa 3: no calzan.")
    return c


# --------------------------------------------------------------------------- #
# Instancia: muestreo, puestos proporcionales y simulacion reactiva real
# --------------------------------------------------------------------------- #

def construir_instancia(mod, c, n_obj, orden):
    n_vsp = max(1, round(n_obj / c.buses_por_vsp))
    sub = c.jt.iloc[orden[:n_vsp]].drop(columns="_id").reset_index(drop=True)
    kappa = max(1, round(n_obj * c.razon))
    sim = mod.Simulador(c.ex, c.depots, c.costos, 1.0, c.unir_ids, c.tarifa, set())
    assert sim.term_nombre[0] == c.terminal, "El terminal unido no es el terminal 0 del simulador."
    sim.kappa[0] = kappa
    sim.kwh_dia = np.zeros(DIA_MIN)
    costo_orig = sim.costo_energia

    def costo_y_acumular(minutos, kwh_total):
        m = np.asarray(minutos)
        e = np.full(len(m), sim.kwh_min)
        e[-1] = kwh_total - sim.kwh_min * (len(m) - 1)
        np.add.at(sim.kwh_dia, m % DIA_MIN, e)
        return costo_orig(minutos, kwh_total)
    sim.costo_energia = costo_y_acumular

    buses = mod.construir_buses(sim, sub, c.ex_idx)
    mod.validar_reconstruccion(sim, sub, buses, None)
    sim.correr(buses)
    return sim, sub, kappa


def extraer(sim, finales, c):
    """Datos de las cargas finales (lo que optimiza el MILP) y cargas intermedias (fijas)."""
    evf = {str(e["jornada_id"]): e for e in sim.eventos if e["tipo"] == "final"}
    fin = []
    for b in sorted(finales, key=lambda b: (int(b.origen), b.parte)):
        assert b.deficit < EPS, (f"La instancia no cabe en sus puestos: la jornada {b.jid} queda con deficit de energia en "
                                 f"la reactiva. Instancia invalida (carga sobre 100% de la capacidad).")
        w = [w for w in b.ventanas if w["tipo"] == "final"]
        assert len(w) == 1, f"La jornada {b.jid} no tiene exactamente una ventana final."
        e = evf[str(b.jid)]
        a = math.ceil(w[0]["t_ini"] / B - 1e-9)
        we = math.floor(w[0]["t_fin"] / B + 1e-9)               # primer bloque que ya NO cabe en la ventana
        assert we - a <= NB, f"La ventana de la jornada {b.jid} supera 24 h."
        fin.append(dict(jid=str(b.jid), origen=str(b.origen), llegada=float(w[0]["t_ini"]), salida=float(w[0]["t_fin"]),
                        a=a, we=we, kwh=float(e["kwh"]), inicio=float(e["t_inicio"]), t_fin=float(e["t_fin"]),
                        cola=float(e["espera_cola_min"]), ciclo_ok=bool(e["ciclo_cumplido"]),
                        n=math.ceil(e["kwh"] / c.q - 1e-9)))
    inter = [e for e in sim.eventos if e["tipo"] == "intermedia"]
    occ_i = np.zeros(DIA_MIN, dtype=int)
    for e in inter:
        m0 = int(e["t_inicio"])
        for m in range(m0, m0 + int(math.ceil(e["kwh"] / sim.kwh_min - 1e-9))):
            occ_i[m % DIA_MIN] += 1
    f = occ_i.reshape(NB, B).max(axis=1)
    return fin, inter, f


# --------------------------------------------------------------------------- #
# Solucion por bloques: representacion, evaluacion y verificacion independiente
# --------------------------------------------------------------------------- #
# Una solucion es (y, e): y[i] = conjunto de bloques ABSOLUTOS con el bus i enchufado; e[i] = {bloque: kWh}.

def reactiva_bloques(fin, kappa, f, c):
    """Misma regla reactiva del simulador, en bloques: por orden de llegada, el primer tramo continuo de puestos libres
    que alcance para toda la carga, sin mirar la tarifa."""
    uso = np.zeros(NB, dtype=int)
    y, e = {}, {}
    for i in sorted(range(len(fin)), key=lambda i: (fin[i]["llegada"], fin[i]["jid"])):
        b = fin[i]
        a, n = b["a"], b["n"]
        libre = (kappa - f - uso) > 0
        ini = None
        for s in range(a, a + NB - n + 1):
            if all(libre[(s + k) % NB] for k in range(n)):
                ini = s
                break
        if ini is not None:
            bloques = list(range(ini, ini + n))
        else:                                         # sin tramo continuo: usa los bloques libres que encuentre
            bloques = [t for t in range(a, a + NB) if libre[t % NB]][:n]
            assert len(bloques) == n, f"La reactiva en bloques no encuentra puestos para la jornada {b['jid']}."
        for t in bloques:
            uso[t % NB] += 1
        y[i] = set(bloques)
        e[i] = {t: c.q for t in bloques}
        e[i][bloques[-1]] = b["kwh"] - c.q * (n - 1)
    return y, e


def evaluar(fin, y, e, kappa, f, c, etiqueta):
    """Costo de las cargas finales de una solucion por bloques, recalculado desde cero, con todos los chequeos."""
    uso = np.zeros(NB, dtype=int)
    energia = kwh = kwh_valle = demora = 0.0
    eventos = reservas = 0
    por_periodo = {p: 0.0 for p in c.periodos}
    for i, b in enumerate(fin):
        ts = sorted(y[i])
        assert ts, f"[{etiqueta}] el bus {b['jid']} no tiene ningun bloque de carga."
        assert min(ts) >= b["a"] and max(ts) < b["a"] + NB, f"[{etiqueta}] el bus {b['jid']} carga fuera de las 24 h desde su llegada."
        assert abs(sum(e[i].values()) - b["kwh"]) < 1e-4, f"[{etiqueta}] el bus {b['jid']} no repone exactamente su energia."
        for t, kw in e[i].items():
            assert t in y[i], f"[{etiqueta}] el bus {b['jid']} carga en un bloque en que no esta enchufado."
            assert -EPS <= kw <= c.q + 1e-6, f"[{etiqueta}] el bus {b['jid']} excede la potencia del cargador en un bloque."
            energia += kw * c.tb[t % NB]
            kwh += kw
            if c.es_valle[t % NB]:
                kwh_valle += kw
            por_periodo[c.periodo_bloque[t % NB]] += kw
        for t in ts:
            uso[t % NB] += 1
        eventos += 1 + sum(1 for k in range(1, len(ts)) if ts[k] != ts[k - 1] + 1)
        reservas += int(max(ts) >= b["we"])
        primero = min(t for t, kw in e[i].items() if kw > EPS)
        demora += primero * B - b["llegada"]
    assert (uso + f <= kappa).all(), f"[{etiqueta}] se exceden los puestos en algun bloque."
    ocup = uso + f
    return dict(energia_usd=energia, kwh=kwh, kwh_valle=kwh_valle, eventos=eventos, reservas=reservas,
                demora_h=demora / 60, saturacion_pct=float((ocup >= kappa).mean() * 100), ocup=ocup,
                por_periodo=por_periodo)


# --------------------------------------------------------------------------- #
# MILP
# --------------------------------------------------------------------------- #

def resolver_milp(fin, kappa, f, c, inicio, limite, gap, log):
    import gurobipy as gp
    from gurobipy import GRB
    c_ev, c_res = c.costos.fixed_charge_cost, c.costos.vehicle_fixed_cost
    m = gp.Model("carga_instancia_reducida")
    m.Params.OutputFlag = 1 if log else 0
    m.Params.TimeLimit = limite
    m.Params.MIPGap = gap
    m.Params.MIPFocus = 2                                      # foco en probar optimalidad
    m.Params.IntegralityFocus = 1                              # integralidad estricta (evita y casi cero con energia positiva)
    r = m.addVars(len(fin), vtype=GRB.BINARY, name="r")
    y, e, z = {}, {}, {}
    cap = [[] for _ in range(NB)]
    for i, b in enumerate(fin):
        a = b["a"]
        for t in range(a, a + NB):
            y[i, t] = m.addVar(vtype=GRB.BINARY)
            e[i, t] = m.addVar(lb=0.0, ub=c.q)
            z[i, t] = m.addVar(lb=0.0, ub=1.0)
        for t in range(a, a + NB):
            m.addConstr(e[i, t] <= c.q * y[i, t])
            if t >= b["we"]:                                   # fuera de la ventana: solo con bus de reserva
                m.addConstr(y[i, t] <= r[i])
            m.addConstr(z[i, t] >= y[i, t] - (y[i, t - 1] if t > a else 0))
            if t < a + NB - 1:                                 # evento continuo a plena potencia: solo su ultimo bloque puede ir parcial
                m.addConstr(e[i, t] >= c.q * (y[i, t] + y[i, t + 1] - 1))
            cap[t % NB].append(y[i, t])
        m.addConstr(gp.quicksum(e[i, t] for t in range(a, a + NB)) == b["kwh"])
        # desigualdades validas (no cambian el modelo, solo ajustan su relajacion): la energia cargada fuera de la
        # ventana no puede superar la energia total del bus por r_b, y el bus necesita al menos n_b bloques enchufado
        if b["we"] < a + NB:
            m.addConstr(gp.quicksum(e[i, t] for t in range(b["we"], a + NB)) <= b["kwh"] * r[i])
        m.addConstr(gp.quicksum(y[i, t] for t in range(a, a + NB)) >= b["n"])
        m.addConstr(gp.quicksum(z[i, t] for t in range(a, a + NB)) >= 1)       # todo bus tiene al menos un evento de carga
    for k in range(NB):
        m.addConstr(gp.quicksum(cap[k]) <= kappa - int(f[k]))
    m.setObjective(gp.quicksum(c.tb[t % NB] * e[i, t] for (i, t) in e) + c_ev * gp.quicksum(z.values())
                   + c_res * gp.quicksum(r.values()), GRB.MINIMIZE)
    for i, b in enumerate(fin):                                # solucion inicial: la reactiva en bloques
        yi, ei = inicio[0][i], inicio[1][i]
        r[i].Start = float(max(yi) >= b["we"])
        for t in range(b["a"], b["a"] + NB):
            y[i, t].Start = float(t in yi)
            e[i, t].Start = ei.get(t, 0.0)
            z[i, t].Start = float(t in yi and (t - 1) not in yi)
    t0 = time.time()
    m.optimize()
    seg = time.time() - t0
    assert m.SolCount > 0, "Gurobi no encontro ninguna solucion en el tiempo limite (el modelo deberia aceptar la reactiva)."
    # Solo cuentan los bloques con y > 0,5. La tolerancia de integralidad (1e-5) deja pasar energias de ~1e-4 kWh en bloques con
    # y casi cero: se descartan y el residuo (de ese orden) se devuelve al bloque del mismo bus con mas holgura de potencia.
    ys, es = {}, {}
    for i, b in enumerate(fin):
        bloques = {t: e[i, t].X for t in range(b["a"], b["a"] + NB) if y[i, t].X > 0.5 and e[i, t].X > 1e-6}
        bloques = {t: min(v, c.q) for t, v in bloques.items()}
        resto = b["kwh"] - sum(bloques.values())
        assert abs(resto) < 0.05, f"El residuo de energia del bus {b['jid']} tras el redondeo ({resto:.4f} kWh) es demasiado grande."
        t_ajuste = max(bloques, key=lambda t: c.q - bloques[t])
        bloques[t_ajuste] += resto
        ys[i], es[i] = set(bloques), bloques
    info = dict(estado=int(m.Status), obj=float(m.ObjVal), cota=float(m.ObjBound), gap=float(m.MIPGap), seg=seg,
                n_binarias=len(y) + len(r), n_variables=m.NumVars, n_restricciones=m.NumConstrs)
    return ys, es, info


def cota_reservas(fin, kappa, f, c, limite=120):
    """Minimo de buses de reserva que necesita CUALQUIER programa de carga con estas ventanas y puestos: relajacion donde los
    puestos se miden en energia (sum_b e_bt <= q (kappa - f_t)) y solo r_b es binaria. Es una cota inferior valida de las
    reservas del MILP (misma logica que la cota LP de la Etapa 3, pero contando buses)."""
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model("cota_reservas")
    m.Params.OutputFlag = 0
    m.Params.TimeLimit = limite
    r = m.addVars(len(fin), vtype=GRB.BINARY)
    e = {}
    cap = [[] for _ in range(NB)]
    for i, b in enumerate(fin):
        for t in range(b["a"], b["a"] + NB):
            e[i, t] = m.addVar(lb=0.0, ub=c.q)
            cap[t % NB].append(e[i, t])
        m.addConstr(gp.quicksum(e[i, t] for t in range(b["a"], b["a"] + NB)) == b["kwh"])
        if b["we"] < b["a"] + NB:
            m.addConstr(gp.quicksum(e[i, t] for t in range(b["we"], b["a"] + NB)) <= b["kwh"] * r[i])
    for k in range(NB):
        m.addConstr(gp.quicksum(cap[k]) <= c.q * (kappa - int(f[k])))
    m.setObjective(r.sum(), GRB.MINIMIZE)
    m.optimize()
    return int(math.ceil(m.ObjBound - 1e-6))


def verificar_minuto(fin, y, e, kappa, f, c):
    """Ejecuta el programa del MILP minuto a minuto: cada bus carga a 180 kW desde el inicio de sus bloques (el ultimo bloque
    de cada tramo solo los minutos que necesita). Comprueba los puestos por minuto y recalcula las reservas reales (el bus
    termina despues de su salida). Devuelve (reservas_al_minuto, ocupacion_por_minuto)."""
    kmin = c.costos.charge_power_kw / 60.0
    occ = np.zeros(DIA_MIN, dtype=int)
    reservas = 0
    for i, b in enumerate(fin):
        fin_carga = 0.0
        for t, kw in e[i].items():
            assert t * B >= b["llegada"] - 1e-6, f"El bus {b['jid']} empieza a cargar antes de llegar."
            dur = int(math.ceil(kw / kmin - 1e-9))
            for mnt in range(t * B, t * B + dur):
                occ[mnt % DIA_MIN] += 1
            fin_carga = max(fin_carga, t * B + kw / kmin)
        reservas += int(fin_carga > b["salida"] + 1e-9)
    assert (occ + np.repeat(f, B) <= kappa).all(), "El programa del MILP excede los puestos al ejecutarlo minuto a minuto."
    return reservas, occ


# --------------------------------------------------------------------------- #
# Metricas de la reactiva real (minuto a minuto) y de las cargas intermedias fijas
# --------------------------------------------------------------------------- #

def metricas_intermedias(inter, c):
    kwh = sum(e["kwh"] for e in inter)
    kwh_valle = 0.0
    for e in inter:
        d = e["t_fin"] - e["t_inicio"]
        kwh_valle += e["kwh"] * (float(c.F_valle(e["t_fin"]) - c.F_valle(e["t_inicio"])) / d if d > 0 else 0.0)
    return dict(energia_usd=sum(e["costo_energia_usd"] for e in inter), kwh=kwh, kwh_valle=kwh_valle, eventos=len(inter))


def metricas_reactiva_minuto(sim, fin, c, kappa):
    finales = [e for e in sim.eventos if e["tipo"] == "final"]
    kwh_valle = sum(e["kwh"] * (float(c.F_valle(e["t_fin"]) - c.F_valle(e["t_inicio"])) / (e["t_fin"] - e["t_inicio"])
                                if e["t_fin"] > e["t_inicio"] else 0.0) for e in finales)
    por_periodo = {p: 0.0 for p in c.periodos}
    for e in finales:                                            # reparte la energia del evento por minuto
        m0, m1 = e["t_inicio"], e["t_fin"]
        if m1 <= m0:
            continue
        for m in range(int(math.floor(m0)), int(math.ceil(m1))):
            ov = max(0.0, min(m1, m + 1) - max(m0, m))
            por_periodo[c.periodo_bloque[(m % DIA_MIN) // B]] += e["kwh"] * ov / (m1 - m0)
    occ = sim.occ[0]
    return dict(energia_usd=sum(e["costo_energia_usd"] for e in finales), kwh=sum(e["kwh"] for e in finales),
                kwh_valle=kwh_valle, eventos=len(finales), reservas=int(sum(not b["ciclo_ok"] for b in fin)),
                demora_h=sum(e["espera_cola_min"] for e in finales) / 60,
                saturacion_pct=float((occ >= kappa).mean() * 100), por_periodo=por_periodo,
                ocup=occ.reshape(NB, B).mean(axis=1))


def fila_comparacion(n_obj, variante, m, inter_m, c):
    kwh = m["kwh"] + inter_m["kwh"]
    energia = m["energia_usd"] + inter_m["energia_usd"]
    eventos = m["eventos"] + inter_m["eventos"]
    total = energia + eventos * c.costos.fixed_charge_cost + m["reservas"] * c.costos.vehicle_fixed_cost
    return dict(N_objetivo=n_obj, variante=variante, kwh_cargados=round(kwh, 1), costo_energia_usd=round(energia, 2),
                usd_por_kwh=round(energia / kwh, 4), pct_energia_valle=round((m["kwh_valle"] + inter_m["kwh_valle"]) / kwh * 100, 2),
                eventos_carga=eventos, costo_eventos_usd=eventos * c.costos.fixed_charge_cost, buses_reserva=m["reservas"],
                costo_reservas_usd=m["reservas"] * c.costos.vehicle_fixed_cost, costo_carga_total_usd=round(total, 2),
                demora_inicio_carga_h=round(m["demora_h"], 1), saturacion_pct=round(m["saturacion_pct"], 1))


# --------------------------------------------------------------------------- #
# Representatividad: la instancia contra el terminal completo
# --------------------------------------------------------------------------- #

def estadisticas_fin(fin, kappa, inter_m, n_res, c):
    llegada_h = np.array([(b["llegada"] % DIA_MIN) // 60 for b in fin])
    salida_h = np.array([(b["salida"] % DIA_MIN) // 60 for b in fin])
    kwh = np.array([b["kwh"] for b in fin])
    return {
        "buses (cargas finales)": len(fin),
        "puestos": kappa,
        "puestos por bus": round(kappa / len(fin), 4),
        "% llegadas entre 19:00 y 02:00": round(float(((llegada_h >= 19) | (llegada_h < 2)).mean() * 100), 1),
        "% salidas entre 04:00 y 08:00": round(float(((salida_h >= 4) & (salida_h < 8)).mean() * 100), 1),
        "ventana mediana en el patio (h)": round(float(np.median([(b["salida"] - b["llegada"]) / 60 for b in fin])), 2),
        "energia media a reponer (kWh)": round(float(kwh.mean()), 1),
        "carga / capacidad de 24 h (%)": round((kwh.sum() + inter_m["kwh"]) / (kappa * 24 * c.costos.charge_power_kw) * 100, 1),
        "% buses con ciclo no cumplido (reactiva)": round(n_res / len(fin) * 100, 1),
    }


def estadisticas_red(c):
    t = c.terminal
    vf = c.vent_red[(c.vent_red["terminal"] == t) & (c.vent_red["tipo"] == "final")]
    ev = c.ev_red[c.ev_red["terminal"] == t]
    evf = ev[ev["tipo"] == "final"]
    llegada_h = (vf["t_ini_mod24"] // 60).values
    salida_h = (vf["t_fin_mod24"] // 60).values
    kwh_tot = ev["kwh"].sum()
    return {
        "buses (cargas finales)": len(c.jr_t),
        "puestos": c.kappa_red,
        "puestos por bus": round(c.razon, 4),
        "% llegadas entre 19:00 y 02:00": round(float(((llegada_h >= 19) | (llegada_h < 2)).mean() * 100), 1),
        "% salidas entre 04:00 y 08:00": round(float(((salida_h >= 4) & (salida_h < 8)).mean() * 100), 1),
        "ventana mediana en el patio (h)": round(float(((vf["t_fin"] - vf["t_ini"]) / 60).median()), 2),
        "energia media a reponer (kWh)": round(float(evf["kwh"].mean()), 1),
        "carga / capacidad de 24 h (%)": round(kwh_tot / (c.kappa_red * 24 * c.costos.charge_power_kw) * 100, 1),
        "% buses con ciclo no cumplido (reactiva)": round(float((~c.jr_t["ciclo_cumplido"]).mean() * 100), 1),
    }


def usd_kwh_valle_red(c):
    ev = c.ev_red[(c.ev_red["terminal"] == c.terminal) & c.ev_red["t_fin"].notna()]
    d = (ev["t_fin"] - ev["t_inicio"]).values
    ok = d > 0
    kv = (ev["kwh"].values[ok] * (c.F_valle(ev["t_fin"].values[ok]) - c.F_valle(ev["t_inicio"].values[ok])) / d[ok]).sum()
    return ev["costo_energia_usd"].sum() / ev["kwh"].sum(), kv / ev["kwh"].sum() * 100


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #

def hora(t):
    t = t % DIA_MIN
    return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def actualizar_tabla(path, nueva, claves):
    """Escribe `nueva` reemplazando las filas con la misma clave (asi correr un solo N no borra los demas)."""
    if path.exists():
        prev = pd.read_csv(path, sep=CSV_SEP)
        k_prev = prev[claves].astype(str).agg("|".join, axis=1)
        k_new = nueva[claves].astype(str).agg("|".join, axis=1)
        nueva = pd.concat([prev[~k_prev.isin(k_new)], nueva], ignore_index=True)
    nueva = nueva.sort_values(claves, kind="stable").reset_index(drop=True)
    nueva.to_csv(path, index=False, sep=CSV_SEP)
    return nueva


def tabla_programa(fin, y, e, c):
    filas = []
    for i, b in enumerate(fin):
        for t in sorted(y[i]):
            filas.append(dict(jornada_id=b["jid"], bloque_abs=t, inicio_bloque=hora(t * B), bloque_mod24=t % NB,
                              kwh=round(e[i].get(t, 0.0), 3), tarifa_usd_kwh=c.tb[t % NB],
                              fuera_de_ventana=int(t >= b["we"])))
    return pd.DataFrame(filas)


def estilo(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.7)


def ahorro_vs_simulador(comp, n):
    """% que el MILP (en bloques de 15 min, conservador) baja el costo de la carga frente al simulador real al minuto."""
    d = comp[comp["N_objetivo"] == n].set_index("variante")["costo_carga_total_usd"]
    return (1 - d["milp_al_minuto"] / d["reactiva_minuto"]) * 100


def graficar_ocupacion(n_obj, kappa, ocup_r, ocup_m, c, path_png, mensaje):
    fig, ax = plt.subplots(figsize=(11, 4.4))
    horas = np.arange(NB) * B / 60
    pico = c.tb >= c.tb.max() - 1e-9
    ymax = kappa * 1.2
    ax.fill_between(horas, 0, ymax, where=pico, color="#999999", alpha=0.15, step="post", linewidth=0,
                    label=f"Tarifa punta ({c.tb.max():.2f} USD/kWh)")
    ax.plot(horas, ocup_r, color=COLOR_REACTIVA, linewidth=1.8, drawstyle="steps-post", label="Politica reactiva (simulador al minuto)")
    ax.plot(horas, ocup_m, color=COLOR_MILP, linewidth=1.8, drawstyle="steps-post", label="MILP")
    ax.axhline(kappa, color="#b22222", linestyle="--", linewidth=1, label=f"Puestos ({kappa})")
    ax.set_ylim(0, ymax)
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xlabel("Hora del dia (la carga que cruza medianoche vuelve al inicio)")
    ax.set_ylabel("Buses cargando")
    ax.set_title(mensaje, fontsize=11, loc="left")
    estilo(ax)
    ax.legend(loc="upper right", fontsize=8, ncol=2, frameon=False)
    fig.text(0.01, 0.01, f"Instancia reducida: N = {n_obj} buses y {kappa} puestos del terminal {c.terminal} (no es el resultado de toda la red).",
             fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_tarifa(df, c, n_obj, path_png):
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ancho = 0.38
    x = np.arange(len(c.periodos))
    for k, (var, col, lab) in enumerate((("reactiva_minuto", COLOR_REACTIVA, "Politica reactiva"), ("milp", COLOR_MILP, "MILP"))):
        d = df[df["variante"] == var].set_index("periodo").reindex(c.periodos)
        ax.bar(x + (k - 0.5) * ancho, d["pct_kwh"].values, ancho, color=col, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{p}\n{c.precio_periodo[p]:.2f} USD/kWh" for p in c.periodos], fontsize=8)
    ax.set_ylabel("% de la energia cargada")
    ax.set_title(f"Energia cargada por periodo tarifario (instancia reducida, N = {n_obj})", fontsize=11, loc="left")
    estilo(ax)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_costos(comp, path_png):
    ns = sorted(comp["N_objetivo"].unique())
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ancho = 0.36
    x = np.arange(len(ns))
    comp_cols = (("costo_energia_usd", "Energia", "#4a8f6e"), ("costo_eventos_usd", "Eventos de carga", "#e6ab02"),
                 ("costo_reservas_usd", "Buses de reserva", "#b22222"))
    for k, (var, nombre) in enumerate((("reactiva_minuto", "Reactiva"), ("milp_al_minuto", "MILP"))):
        base = np.zeros(len(ns))
        for col, lab, color in comp_cols:
            v = np.array([(lambda d: d[col].iloc[0] / d["buses"].iloc[0])(comp[(comp.N_objetivo == n) & (comp.variante == var)]) for n in ns])
            ax.bar(x + (k - 0.5) * ancho, v, ancho, bottom=base, color=color, alpha=0.55 if k == 0 else 1.0,
                   label=lab if k == 0 else None, edgecolor="white")
            base += v
        for xi, b in zip(x + (k - 0.5) * ancho, base):
            ax.text(xi, b, f"{nombre}\n{b:.1f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([f"N = {n}" for n in ns])
    ax.set_ylabel("USD por bus (costo de la carga)")
    ax.set_title("Costo de la carga por bus: reactiva real (tenue) vs MILP (instancia reducida)", fontsize=11, loc="left")
    estilo(ax)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_brecha(tiempos, path_png):
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.bar([f"N = {n}" for n in tiempos["N_objetivo"]], tiempos["brecha_pct"], color=COLOR_MILP)
    ax.axhline(parametros.GAP_MILP * 100, color="#b22222", linestyle="--", linewidth=1, label=f"Brecha pedida ({parametros.GAP_MILP:.0%})")
    for i, r in enumerate(tiempos.itertuples()):
        ax.text(i, r.brecha_pct, f"{r.brecha_pct:.1f}%\n({r.segundos:.0f} s)\n{'OPTIMO' if r.resuelta_optimo else 'factible'}", ha="center", va="bottom", fontsize=7)
    ax.set_ylabel("Brecha de optimalidad alcanzada (%)")
    ax.set_title("Brecha que alcanza el MILP en el limite de tiempo, segun el tamano", fontsize=11, loc="left")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.15)
    estilo(ax)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Una instancia completa
# --------------------------------------------------------------------------- #

def correr_instancia(mod, c, n_obj, orden, args):
    print(f"\n=== Instancia reducida N = {n_obj} ===")
    sim, sub, kappa = construir_instancia(mod, c, n_obj, orden)
    finales = sim.buses_terminados
    fin, inter, f = extraer(sim, finales, c)
    n_fin = len(fin)
    print(f"  Jornadas del VSP muestreadas: {len(sub)} -> {n_fin} buses tras la carga | puestos: {kappa} "
          f"(razon {kappa / n_fin:.4f}; red completa {c.razon:.4f}) | cargas intermedias fijas: {len(inter)}")
    inter_m = metricas_intermedias(inter, c)

    # particiones: la instancia debe partir las jornadas como la corrida de la red completa
    partidas_red = set(c.jr_t[c.jr_t["parte"] > 0]["bus_origen"])
    partidas_inst = {str(b.origen) for b in finales if b.parte > 0}
    ids = set(sub["bus_id"].astype(str))
    iguales = len(ids) - len((partidas_red & ids) ^ partidas_inst)
    print(f"  Jornadas partidas igual que en la red completa: {iguales}/{len(ids)}")

    # reactiva real (minuto) y reactiva en bloques
    m_min = metricas_reactiva_minuto(sim, fin, c, kappa)
    yr, er = reactiva_bloques(fin, kappa, f, c)
    m_rb = evaluar(fin, yr, er, kappa, f, c, "reactiva en bloques")
    cota_c, cota_n = mod.cota_carga_lp(sim, finales)
    cota_pct = cota_c / cota_n * 100
    no_trivial = m_rb["saturacion_pct"] >= parametros.UMBRAL_NO_TRIVIAL * 100
    print(f"  Reactiva: saturacion de puestos {m_rb['saturacion_pct']:.1f}% de los bloques ({m_min['saturacion_pct']:.1f}% de los minutos) | "
          f"ciclos no cumplidos {m_min['reservas']} (minuto) / {m_rb['reservas']} (bloques) | cota LP {cota_pct:.1f}%")
    print("  " + ("[OK] instancia no trivial" if no_trivial else
                  f"[INSTANCIA DESCARTADA] puestos saturados en menos de {parametros.UMBRAL_NO_TRIVIAL:.0%} de los bloques"))

    # MILP
    ym, em, info = resolver_milp(fin, kappa, f, c, (yr, er), args.tiempo, parametros.GAP_MILP, args.log)
    m_mi = evaluar(fin, ym, em, kappa, f, c, "MILP")

    def costo(m):
        return m["energia_usd"] + m["eventos"] * c.costos.fixed_charge_cost + m["reservas"] * c.costos.vehicle_fixed_cost
    c_rb, c_mi = costo(m_rb), costo(m_mi)
    tol = 1e-3 * max(1.0, abs(c_mi)) + 0.5
    assert info["cota"] - tol <= c_mi <= info["obj"] + tol, (
        f"El costo recalculado de la solucion del MILP ({c_mi:.2f}) no es coherente con el objetivo ({info['obj']:.2f}) "
        f"y la cota inferior ({info['cota']:.2f}) de Gurobi.")
    assert c_mi <= c_rb + 1e-3, (f"ERROR: el MILP ({c_mi:.2f} USD) cuesta mas que la reactiva en bloques ({c_rb:.2f} USD), que es "
                                 f"una solucion factible suya. Hay un error de modelacion.")
    print(f"  MILP: {info['seg']:.1f} s, estado {info['estado']} ({'optimo' if info['estado'] == 2 else 'limite de tiempo'}), "
          f"brecha {info['gap'] * 100:.3f}% | costo de las cargas finales: reactiva {c_rb:,.0f} -> MILP {c_mi:,.0f} USD "
          f"({(c_mi / c_rb - 1) * 100:+.2f}%) | reservas {m_rb['reservas']} -> {m_mi['reservas']}")
    print("  [OK] solucion del MILP verificada: energia exacta por bus, <= potencia por bloque, puestos, costo recalculado coherente con Gurobi, <= reactiva.")

    res_cota = cota_reservas(fin, kappa, f, c)
    res_min, occ_min = verificar_minuto(fin, ym, em, kappa, f, c)
    assert res_min <= m_mi["reservas"], "Al ejecutarlo al minuto el MILP tiene mas reservas que en bloques: error."
    assert res_cota <= res_min, f"La cota de reservas ({res_cota}) supera las reservas del programa ({res_min}): error."
    m_mm = dict(m_mi, reservas=res_min)
    resuelta = info["estado"] == 2
    print(f"  Cota de reservas: ningun programa tiene menos de {res_cota} | MILP en bloques {m_mi['reservas']}, ejecutado al minuto {res_min} "
          f"| {'RESUELTA AL OPTIMO (brecha <= 1%)' if resuelta else 'factible verificada (brecha > 1%)'}")
    filas = []
    for var, m in (("reactiva_minuto", m_min), ("reactiva_bloques", m_rb), ("milp", m_mi), ("milp_al_minuto", m_mm)):
        fila = fila_comparacion(n_obj, var, m, inter_m, c)
        fila["buses"] = n_fin
        filas.append(fila)
    kwh_inst = sum(b["kwh"] for b in fin) + inter_m["kwh"]
    inst = dict(N_objetivo=n_obj, jornadas_vsp=len(sub), buses=n_fin, puestos=kappa, puestos_por_bus=round(kappa / n_fin, 4),
                semilla=args.semilla, jornadas_partidas=int(sum(b.parte > 0 for b in finales)),
                jornadas_partidas_igual_que_red=f"{iguales}/{len(ids)}", cargas_intermedias_fijas=len(inter),
                energia_mwh=round(kwh_inst / 1000, 2),
                carga_pct_capacidad=round(kwh_inst / (kappa * 24 * c.costos.charge_power_kw) * 100, 1),
                saturacion_reactiva_pct=round(m_rb["saturacion_pct"], 1), saturacion_milp_pct=round(m_mi["saturacion_pct"], 1),
                cota_lp_pct=round(cota_pct, 1), no_trivial=int(no_trivial), n_binarias=info["n_binarias"],
                n_variables=info["n_variables"], n_restricciones=info["n_restricciones"],
                reservas_cota=res_cota, reservas_milp_bloques=m_mi["reservas"], reservas_milp_al_minuto=res_min)
    tiempo = dict(N_objetivo=n_obj, buses=n_fin, segundos=round(info["seg"], 1), estado="optimo" if info["estado"] == 2 else "limite de tiempo",
                  brecha_pct=round(info["gap"] * 100, 3), cota_inferior_usd=round(info["cota"], 2), objetivo_usd=round(info["obj"], 2),
                  brecha_usd=round(info["obj"] - info["cota"], 2), resuelta_optimo=int(resuelta))
    estad = estadisticas_fin(fin, kappa, inter_m, m_min["reservas"], c)
    por_p = []
    for var, m in (("reactiva_minuto", m_min), ("milp", m_mi)):
        tot = sum(m["por_periodo"].values())
        for p in c.periodos:
            por_p.append(dict(N_objetivo=n_obj, variante=var, periodo=p, precio_usd_kwh=c.precio_periodo[p],
                              kwh=round(m["por_periodo"][p], 1), pct_kwh=round(m["por_periodo"][p] / tot * 100, 2)))
    ocup = pd.DataFrame(dict(bloque=np.arange(NB), hora=[hora(k * B) for k in range(NB)], puestos=kappa, tarifa_usd_kwh=c.tb,
                             intermedias_fijas=f, reactiva_minuto_promedio=np.round(m_min["ocup"], 3),
                             reactiva_bloques=m_rb["ocup"], milp=m_mi["ocup"]))
    if args.detalle:
        print("\n  --- Detalle por bus (ventana en el patio, energia, bloques cargados) ---")
        for i, b in enumerate(fin):
            def rango(y, e):
                ts = sorted(t for t in y[i] if e[i].get(t, 0.0) > EPS)
                ocioso = len(y[i]) - len(ts)
                txt = ",".join(hora(t * B) for t in ts) if len(ts) <= 12 else f"{hora(ts[0] * B)}..{hora((ts[-1] + 1) * B)} ({len(ts)} bloques)"
                return txt + (f" [+{ocioso} bloques enchufado sin cargar]" if ocioso else "")
            print(f"   bus {b['jid']:>6s} | llega {hora(b['llegada'])} sale {hora(b['salida'])} (ventana {(b['salida'] - b['llegada']) / 60:5.2f} h) | "
                  f"{b['kwh']:6.1f} kWh = {b['n']} bloques | reactiva: {rango(yr, er)} {'(RESERVA)' if max(yr[i]) >= b['we'] else ''} | "
                  f"MILP: {rango(ym, em)} {'(RESERVA)' if max(ym[i]) >= b['we'] else ''}")
        print("   (Revisar a mano: la energia de cada bus, que los bloques esten dentro de la ventana salvo reserva, y que la ocupacion no pase de los puestos.)")
    return dict(n=n_obj, kappa=kappa, inst=inst, filas=filas, tiempo=tiempo, estad=estad, por_p=por_p, ocup=ocup,
                prog_r=tabla_programa(fin, yr, er, c), prog_m=tabla_programa(fin, ym, em, c), m_min=m_min, m_rb=m_rb, m_mi=m_mi,
                c_rb=c_rb, c_mi=c_mi, info=info, inter_m=inter_m)


# --------------------------------------------------------------------------- #
# Reporte
# --------------------------------------------------------------------------- #

def escribir_reporte(ns, comp, inst, tiempos, rep, c, semilla):
    comp, inst, tiempos = comp[comp["N_objetivo"].isin(ns)], inst[inst["N_objetivo"].isin(ns)], tiempos[tiempos["N_objetivo"].isin(ns)]
    L = []
    L.append("# Reporte Etapa 4 - MILP de programacion de carga (INSTANCIA REDUCIDA)")
    L.append("")
    L.append(f"> **Instancia reducida:** muestra de jornadas del terminal {c.terminal} (escenario {c.escenario}, nivel 100%) con "
             f"semilla {semilla}. **No es el resultado de toda la red**: el MILP sobre la red completa (E3) solo se estima.")
    L.append("")
    L.append("## Que se resolvio")
    L.append("")
    L.append("Para cada bus, dentro de su ventana en el patio (llegada hasta su primera salida del dia siguiente), el MILP decide "
             f"en cuales de los {NB} bloques de {B} min del dia carga y cuanta energia, minimizando energia (tarifa del bloque) + "
             f"{c.costos.fixed_charge_cost:.0f} USD por evento de carga + {c.costos.vehicle_fixed_cost:.0f} USD por bus de reserva, "
             "sin pasar los puestos. Resuelve las 24 horas de una vez: los bloques son solo la unidad de medida del tiempo, no una "
             "descomposicion temporal. Un **bus de reserva** (r = 1) puede terminar de cargar despues de su salida (hasta 24 h desde "
             "su llegada) y su salida la cubre otro bus ya cargado: es la misma regla del simulador. La energia se carga igual y ocupa "
             "puestos. Las cargas intermedias (0,5% de los buses) quedan fijas como las dejo la reactiva. La espera en cola no esta en el "
             "objetivo: se reporta como demora hasta iniciar la carga.")
    L.append("")
    L.append("## Instancias")
    L.append("")
    L.append(inst.to_markdown(index=False))
    L.append("")
    L.append(f"`no_trivial` = puestos saturados en al menos {parametros.UMBRAL_NO_TRIVIAL:.0%} de los bloques en la reactiva. "
             "`jornadas_partidas_igual_que_red` = jornadas muestreadas que el simulador parte (o no) igual que en la corrida de la red completa.")
    L.append("")
    L.append("## Comparacion reactiva vs MILP (mismos buses, mismos puestos)")
    L.append("")
    L.append("`reactiva_minuto` es el simulador de la Etapa 3 (la politica real, al minuto); `reactiva_bloques` es la misma regla "
             "en la grilla de 15 min del MILP: es la solucion inicial que se le entrega y la prueba de correctitud (el MILP debe costar "
             "menos o igual). **La referencia para el valor de la carga inteligente es `reactiva_minuto`**: la grilla de 15 min es "
             "conservadora y encarece la reactiva en bloques (mas reservas), de modo que compararse con ella infla la ganancia. "
             "Costo de la carga = energia + eventos + reservas (flota, km y espera del VSP son iguales en ambas).")
    L.append("")
    cols = ["N_objetivo", "variante", "buses", "kwh_cargados", "costo_energia_usd", "usd_por_kwh", "pct_energia_valle", "eventos_carga",
            "buses_reserva", "costo_reservas_usd", "costo_carga_total_usd", "demora_inicio_carga_h", "saturacion_pct"]
    L.append(comp[cols].to_markdown(index=False))
    L.append("")
    L.append("### Valor de la carga inteligente (MILP frente a las dos reactivas)")
    L.append("")
    L.append("El MILP trabaja en bloques de 15 min (restringen sus opciones) y su programa se **ejecuta al minuto** (`milp_al_minuto`): se "
             "verifica que respeta los puestos minuto a minuto y se recalculan sus reservas reales. Esa es la ganancia frente al simulador real; es una "
             "**cota inferior** del valor de optimizar, porque el optimo al minuto seria igual o mejor y la brecha deja margen.")
    L.append("")
    val = []
    for n in ns:
        d = comp[comp.N_objetivo == n].set_index("variante")
        val.append(dict(N_objetivo=n, costo_reactiva_minuto_usd=d.loc["reactiva_minuto", "costo_carga_total_usd"],
                        costo_reactiva_bloques_usd=d.loc["reactiva_bloques", "costo_carga_total_usd"], costo_milp_bloques_usd=d.loc["milp", "costo_carga_total_usd"], costo_milp_al_minuto_usd=d.loc["milp_al_minuto", "costo_carga_total_usd"],
                        ganancia_vs_simulador_pct=round(ahorro_vs_simulador(comp, n), 1),
                        ganancia_vs_reactiva_bloques_pct=round((1 - d.loc["milp", "costo_carga_total_usd"] / d.loc["reactiva_bloques", "costo_carga_total_usd"]) * 100, 1),
                        reservas_simulador=int(d.loc["reactiva_minuto", "buses_reserva"]), reservas_reactiva_bloques=int(d.loc["reactiva_bloques", "buses_reserva"]),
                        reservas_milp_bloques=int(d.loc["milp", "buses_reserva"]), reservas_milp_al_minuto=int(d.loc["milp_al_minuto", "buses_reserva"])))
    L.append(pd.DataFrame(val).to_markdown(index=False))
    L.append("")
    L.append("### Variacion del MILP respecto de la reactiva en bloques")
    L.append("")
    dif = []
    for n in ns:
        a = comp[(comp.N_objetivo == n) & (comp.variante == "reactiva_bloques")].iloc[0]
        b = comp[(comp.N_objetivo == n) & (comp.variante == "milp")].iloc[0]
        dif.append(dict(N_objetivo=n, d_costo_total_usd=round(b.costo_carga_total_usd - a.costo_carga_total_usd, 1),
                        d_costo_total_pct=round((b.costo_carga_total_usd / a.costo_carga_total_usd - 1) * 100, 2),
                        d_energia_usd=round(b.costo_energia_usd - a.costo_energia_usd, 1),
                        d_usd_por_kwh=round(b.usd_por_kwh - a.usd_por_kwh, 4), d_pct_valle=round(b.pct_energia_valle - a.pct_energia_valle, 2),
                        d_eventos=int(b.eventos_carga - a.eventos_carga), d_reservas=int(b.buses_reserva - a.buses_reserva),
                        d_costo_reservas_usd=round(b.costo_reservas_usd - a.costo_reservas_usd, 1)))
    L.append(pd.DataFrame(dif).to_markdown(index=False))
    L.append("")
    L.append("## Tiempo de resolucion")
    L.append("")
    L.append(tiempos.to_markdown(index=False))
    L.append("")
    sin_gap = tiempos[tiempos["resuelta_optimo"] == 0]["N_objetivo"].tolist()
    con_gap = tiempos[tiempos["resuelta_optimo"] == 1]["N_objetivo"].tolist()
    L.append("")
    L.append(f"- Instancias que **no** alcanzaron la brecha pedida ({parametros.GAP_MILP:.0%}) en {parametros.TIEMPO_LIMITE_MILP_S} s: "
             f"{sin_gap if sin_gap else 'ninguna'}. **Resueltas al optimo (brecha <= 1%): {con_gap if con_gap else 'ninguna'}.** La brecha es la distancia entre la mejor solucion y la cota de Gurobi: la solucion "
             "es factible y verificada, pero su optimalidad solo esta certificada hasta esa brecha (la ganancia real es al menos la medida).")
    L.append("- **Regla declarada antes de correr:** solo se llama 'resuelta al optimo' a una instancia con brecha <= 1% certificada por Gurobi; "
             "las demas son soluciones factibles verificadas, con su brecha en % y en USD y la cota de reservas (`reservas_cota`: ningun programa de carga "
             "puede tener menos reservas, calculada con una relajacion en segundos).")
    L.append("")
    L.append("## Representatividad de la instancia")
    L.append("")
    L.append(rep.to_markdown(index=False))
    L.append("")
    L.append("## Chequeos que se hicieron en cada corrida (el script falla si alguno no se cumple)")
    L.append("")
    L.append("- Las jornadas reconstruidas sin cargas calzan con el VSP (kWh por jornada).")
    L.append("- Cobertura y balance de energia del simulador sobre la instancia (los de `10-carga_reactiva.py`).")
    L.append("- El programa del MILP se ejecuta minuto a minuto: respeta los puestos y sus reservas reales son menores o iguales a las de bloques; la cota de reservas es menor o igual a las del MILP.")
    L.append("- La reactiva en bloques es factible para el MILP y se evalua con la misma funcion que la solucion del MILP.")
    L.append("- Solucion del MILP: energia exacta por bus, no mas de 45 kWh por bloque, bloques dentro de las 24 h desde la llegada, "
             "fuera de la ventana solo con reserva, puestos respetados en cada bloque, costo recalculado coherente con el objetivo y la cota de Gurobi.")
    L.append("- **Costo del MILP <= costo de la reactiva en bloques.**")
    L.append("")
    L.append("## Limitaciones")
    L.append("")
    L.append("- Instancia reducida: muestra aleatoria con semilla fija de un solo terminal; extrapolar a toda la red es una estimacion.")
    L.append(f"- Bloques de {B} min: un bus solo puede usar bloques que su ventana cubre completos (error conservador de hasta {B} min en los bordes).")
    L.append("- Las cargas intermedias quedan fijas (0,5% de los buses); no se re-optimizan.")
    L.append("- Las ventanas vienen de las jornadas del VSP, que ignora la bateria: el MILP optimiza cuando cargar, no cambia la flota ni las jornadas.")
    L.append("- Carga lineal a 180 kW; un solo dia laboral.")
    L.append("")
    L.append("## Archivos")
    L.append("")
    for t, d in (("instancias.csv", "una fila por tamano: muestra, puestos, carga, saturacion, cota LP, tamano del modelo"),
                 ("comparacion_reactiva_milp.csv", "tabla de comparacion (reactiva al minuto, reactiva en bloques, MILP)"),
                 ("tiempos_resolucion.csv", "tiempo, estado y brecha del MILP por N"),
                 ("representatividad.csv", "la instancia contra el terminal completo de la red"),
                 ("energia_por_tarifa.csv", "energia cargada por periodo tarifario, reactiva vs MILP"),
                 ("ocupacion_N<n>.csv", "buses cargando por bloque de 15 min (reactiva y MILP), puestos y tarifa"),
                 ("programa_reactiva_N<n>.csv` y `programa_milp_N<n>.csv", "bloques de carga de cada bus")):
        L.append(f"- `tablas/{t}`: {d}.")
    for g, d in (("ocupacion_reactiva_vs_milp_N<n>.png", "buses cargando durante el dia, reactiva vs MILP, contra los puestos"),
                 ("energia_por_tarifa.png", "% de la energia por periodo tarifario (mayor N)"),
                 ("costo_reactiva_vs_milp.png", "costo de la carga por bus, apilado, simulador real vs MILP, por N"),
                 ("brecha_vs_N.png", "brecha de optimalidad alcanzada en el limite de tiempo, por tamano de instancia")):
        L.append(f"- `graficos/{g}`: {d}.")
    (RESULTS / "reporte.md").write_text("\n".join(L), encoding="utf-8")


def graficos_y_reporte(c, ns, semilla, inst_all, comp_all, tiempos_all, por_p_all, rep):
    """Todos los graficos y el reporte salen de los CSV de tablas/ (asi se pueden regenerar sin volver a resolver)."""
    for n in ns:
        o = pd.read_csv(TABLAS / f"ocupacion_N{n}.csv", sep=CSV_SEP)
        kappa = int(o["puestos"].iloc[0])
        graficar_ocupacion(n, kappa, o["reactiva_minuto_promedio"].values, o["milp"].values, c,
                           GRAFICOS / f"ocupacion_reactiva_vs_milp_N{n}.png",
                           f"Puestos ocupados por hora: reactiva vs MILP (N = {n}; el MILP baja el costo de la carga al menos "
                           f"{ahorro_vs_simulador(comp_all, n):.1f}%)")
    grande = max(ns)
    graficar_tarifa(por_p_all[por_p_all["N_objetivo"] == grande], c, grande, GRAFICOS / "energia_por_tarifa.png")
    graficar_costos(comp_all, GRAFICOS / "costo_reactiva_vs_milp.png")
    graficar_brecha(tiempos_all, GRAFICOS / "brecha_vs_N.png")
    escribir_reporte(sorted(comp_all["N_objetivo"].unique()), comp_all, inst_all, tiempos_all, rep, c, semilla)
    print(f"\n  -> {TABLAS} | {GRAFICOS} | {RESULTS / 'reporte.md'}")
    print("\n=== FIN ETAPA 4 (MILP de carga, instancia reducida) ===")


def regenerar(c, args):
    """Regenera graficos y reporte desde los CSV ya escritos (no resuelve nada)."""
    inst_all = pd.read_csv(TABLAS / "instancias.csv", sep=CSV_SEP)
    comp_all = pd.read_csv(TABLAS / "comparacion_reactiva_milp.csv", sep=CSV_SEP)
    tiempos_all = pd.read_csv(TABLAS / "tiempos_resolucion.csv", sep=CSV_SEP)
    por_p_all = pd.read_csv(TABLAS / "energia_por_tarifa.csv", sep=CSV_SEP)
    rep = pd.read_csv(TABLAS / "representatividad.csv", sep=CSV_SEP)
    graficos_y_reporte(c, sorted(comp_all["N_objetivo"].unique()), args.semilla, inst_all, comp_all, tiempos_all, por_p_all, rep)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, nargs="*", default=None, help=f"Tamanos de la instancia (default {parametros.N_MILP}).")
    parser.add_argument("--semilla", type=int, default=parametros.SEMILLA_MILP)
    parser.add_argument("--tiempo", type=float, default=parametros.TIEMPO_LIMITE_MILP_S, help="Limite de resolucion por instancia (s).")
    parser.add_argument("--escenario", default=parametros.ESCENARIO_MILP)
    parser.add_argument("--detalle", action="store_true", help="Imprime la programacion bus por bus (para el checkpoint chico).")
    parser.add_argument("--sin-salidas", action="store_true", help="No escribe tablas, graficos ni reporte (checkpoint).")
    parser.add_argument("--log", action="store_true", help="Muestra el log de Gurobi.")
    parser.add_argument("--regenerar", action="store_true", help="Regenera graficos y reporte desde los CSV ya escritos, sin resolver.")
    args = parser.parse_args()
    ns = args.n if args.n else list(parametros.N_MILP)

    print(f"=== ETAPA 4: MILP de programacion de carga, INSTANCIA REDUCIDA (escenario {args.escenario}, semilla {args.semilla}) ===")
    mod = cargar_simulador()
    c = cargar_contexto(mod, args.escenario)
    print(f"  Terminal: {c.terminal} | red completa: {c.n_vsp_red} jornadas del VSP -> {c.n_final_red} buses tras la carga, "
          f"{c.kappa_red} puestos ({c.razon:.4f} puestos por bus; {c.buses_por_vsp:.4f} buses por jornada del VSP)")
    orden = np.random.default_rng(args.semilla).permutation(len(c.jt))      # muestreo anidado: N chico dentro de N grande

    if args.regenerar:
        regenerar(c, args)
        return
    res = [correr_instancia(mod, c, n, orden, args) for n in ns]
    if args.sin_salidas:
        print("\n(--sin-salidas: no se escribio nada)")
        return

    inst = pd.DataFrame([r["inst"] for r in res])
    comp = pd.DataFrame([f for r in res for f in r["filas"]])
    tiempos = pd.DataFrame([r["tiempo"] for r in res])
    por_p = pd.DataFrame([x for r in res for x in r["por_p"]])
    inst_all = actualizar_tabla(TABLAS / "instancias.csv", inst, ["N_objetivo", "semilla"])
    comp_all = actualizar_tabla(TABLAS / "comparacion_reactiva_milp.csv", comp, ["N_objetivo", "variante"])
    tiempos_all = actualizar_tabla(TABLAS / "tiempos_resolucion.csv", tiempos, ["N_objetivo"])
    por_p_all = actualizar_tabla(TABLAS / "energia_por_tarifa.csv", por_p, ["N_objetivo", "variante", "periodo"])

    # representatividad (instancias de esta corrida contra el terminal completo)
    red = estadisticas_red(c)
    usd_red, valle_red = usd_kwh_valle_red(c)
    rep = {"metrica": list(red) + ["USD/kWh (reactiva)", "% energia en valle (reactiva)"],
           "red_completa": list(red.values()) + [round(usd_red, 4), round(valle_red, 1)]}
    for r in res:
        rm = comp[(comp.N_objetivo == r["n"]) & (comp.variante == "reactiva_minuto")].iloc[0]
        rep[f"N={r['n']}"] = list(r["estad"].values()) + [rm.usd_por_kwh, rm.pct_energia_valle]
    rep = pd.DataFrame(rep)
    rep.to_csv(TABLAS / "representatividad.csv", index=False, sep=CSV_SEP)

    for r in res:
        n = r["n"]
        r["ocup"].to_csv(TABLAS / f"ocupacion_N{n}.csv", index=False, sep=CSV_SEP)
        r["prog_r"].to_csv(TABLAS / f"programa_reactiva_N{n}.csv", index=False, sep=CSV_SEP)
        r["prog_m"].to_csv(TABLAS / f"programa_milp_N{n}.csv", index=False, sep=CSV_SEP)
    graficos_y_reporte(c, [r["n"] for r in res], args.semilla, inst_all, comp_all, tiempos_all, por_p_all, rep)


if __name__ == "__main__":
    main()
