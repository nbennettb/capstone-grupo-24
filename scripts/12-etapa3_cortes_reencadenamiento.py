"""
Etapa 3 de la metodologia - ICS2122 Capstone Buses Electricos (ver docs/context/01_como_funciona.md).

Cortes y re-encadenamiento con recarga: reorganiza las jornadas del VSP (Etapa 2) para que todo bus las
cumpla con su bateria, con la menor flota. Trabaja sobre un electroterminal completo (--terminal).

3a. CORTE (programacion dinamica por jornada). Cada jornada se divide en TRAMOS que un bus hace partiendo del
    patio con la bateria llena y volviendo a el. Un tramo es factible si, al terminar cada expedicion, lo
    consumido desde el patio mas la energia para volver al patio no supera la bateria util (315 kWh): la misma
    regla de seguridad del caso base. La DP minimiza (parametros.REGLA_CORTE): primero el numero de tramos y,
    a igualdad, los km extra del corte (vuelta al patio + nueva salida - conexion que se ahorra).

3b. RE-ENCADENAMIENTO (flujo de costo minimo, la misma red espacio-tiempo de la Etapa 2). Nodos = tramos; una
    linea de tiempo = el patio. El bus que termina el tramo k llega al patio en a_k y queda listo en
    rho_k = a_k + E_k / P + h (recarga completa de lo consumido a charge_power_kw, mas la holgura h). Despues puede
    tomar cualquier tramo que salga del patio en s_l >= rho_k. Costo: vehicle_fixed_cost por bus (los km de cada
    tramo no dependen del encadenamiento). Es una matriz de red: la LP entrega la solucion entera.
    Las cadenas se arman con la regla "sale primero el bus que lleva mas tiempo en el patio" (entre los listos,
    el de llegada mas temprana): le da la mayor ventana de carga y es determinista.

Salida para la Etapa 4: VENTANAS de carga. Intermedia: entre dos tramos seguidos de una cadena (llegada a_k,
hora limite = siguiente salida del bus, energia E_k). Nocturna: tras el ultimo tramo (hora limite = primera
salida del bus del dia siguiente). La Etapa 3 NO ve los puestos: eso lo resuelve la Etapa 4.

Diagnostico de flota (cada paso = maximo de intervalos [salida, listo) superpuestos):
  (i) VSP; (ii) reuso del patio sin bateria (jornadas enteras, listo = llegada); (iii) solo cortes (cada tramo
  un bus); (iv) cortes + re-encadenamiento (la Etapa 3 completa).

Input:  data-processed/{expediciones,jornadas_<escenario>}.csv, data-filtrado/depots.csv
Output: results/instancia_<siglas>/etapa3/h<h>/   (La Reina: instancia_LR)
        tablas/{tramos,cadenas,ventanas,diagnostico_flota,resumen}.csv
        graficos/{gantt_cadenas,llegadas_patio_por_hora}.png (+ .csv con los datos de cada grafico)
        reporte.md

Uso:
    python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --escenario E1 --holgura 0
    python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --escenario E1 --holgura 30
    python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --rutas C09 C10      # prueba chica
"""

import argparse
import heapq
import importlib.util
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import graficos as gr, instancia, medicion, nombres, parametros   # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP                # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "caso_base", Path(__file__).resolve().parent / "10-caso_base_carga_reactiva.py")
caso_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(caso_base)

DIA_MIN = 1440
EPS = 1e-6


# --------------------------------------------------------------------------- #
# 3a. Corte de cada jornada (programacion dinamica)
# --------------------------------------------------------------------------- #

class Contexto:
    """Datos fisicos que comparten el corte y las validaciones."""

    def __init__(self, sim, costos):
        self.sim = sim
        self.c = parametros.CONSUMO_KWH_KM
        self.v = parametros.VELOCIDAD_KMH
        self.layover = parametros.LAYOVER_MIN
        self.util = costos.bateria_util_ciclica_kwh(1.0)                  # 315 kWh: ciclo al 100%
        self.P = costos.charge_power_kw

    def km_salida(self, bus, i):
        """Pullout al origen de la expedicion i de la jornada: el del VSP si es la primera; si no, desde el patio
        mas cercano del terminal."""
        if i == 0:
            return bus.pullout_km
        patios = self.sim.term_patios[bus.term]
        return float(self.sim.dist_o[bus.rows[i], patios].min())

    def km_vuelta(self, bus, k):
        """Vuelta al patio desde el destino de la expedicion k: el pullin del VSP si es la ultima."""
        if k == len(bus.rows) - 1:
            return bus.pullin_km
        return float(self.sim.dterm_d[bus.rows[k]][bus.term])


def cortar_jornada(ctx, bus):
    """DP sobre los puntos de corte. Devuelve la lista de tramos [(i, j), ...] (indices inclusive) que minimiza
    (numero de tramos, km extra)."""
    assert parametros.REGLA_CORTE == "min_tramos_km", f"Regla de corte no implementada: {parametros.REGLA_CORTE}."
    rows, n, c, kwh = bus.rows, len(bus.rows), ctx.c, ctx.sim.kwh
    # factible[i] = ultimo j tal que el tramo [i..j] es factible (la factibilidad se pierde al alargar el tramo,
    # porque cada punto de control solo depende de lo consumido desde la salida)
    ultimo = np.full(n, -1)
    for i in range(n):
        e = ctx.km_salida(bus, i) * c
        for k in range(i, n):
            if k > i:
                e += bus.conn[k - 1] * c
            e += kwh[rows[k]]
            if e + ctx.km_vuelta(bus, k) * c > ctx.util + EPS:
                break
            ultimo[i] = k
        assert ultimo[i] >= i, (
            f"Jornada {bus.jid}: la expedicion {rows[i]} no se puede hacer ni saliendo llena del patio y volviendo.")
    INF = (10 ** 9, float("inf"))
    mejor = [INF] * (n + 1)          # mejor[m]: cubrir las expediciones 0..m-1
    previo = [-1] * (n + 1)
    mejor[0] = (0, 0.0)
    for m in range(1, n + 1):
        j = m - 1
        for i in range(j + 1):
            if ultimo[i] < j or mejor[i] == INF:
                continue
            extra = 0.0
            if i > 0:                # corte entre i-1 e i
                extra = ctx.km_vuelta(bus, i - 1) + ctx.km_salida(bus, i) - bus.conn[i - 1]
            cand = (mejor[i][0] + 1, mejor[i][1] + extra)
            if cand < mejor[m]:
                mejor[m], previo[m] = cand, i
    tramos, m = [], n
    while m > 0:
        i = previo[m]
        tramos.append((i, m - 1))
        m = i
    return tramos[::-1]


def datos_tramo(ctx, bus, i, j, h):
    """Kilometros, energia y tiempos del tramo [i..j] de la jornada."""
    sim, rows = ctx.sim, bus.rows
    km_out, km_in = ctx.km_salida(bus, i), ctx.km_vuelta(bus, j)
    km_conn = float(sum(bus.conn[i:j]))
    kwh_exp = float(sum(sim.kwh[r] for r in rows[i:j + 1]))
    energia = kwh_exp + (km_out + km_conn + km_in) * ctx.c
    s = sim.dep[rows[i]] - ctx.layover - km_out / ctx.v * 60
    a = sim.arr[rows[j]] + km_in / ctx.v * 60
    espera = sum(sim.dep[rows[k]] - sim.arr[rows[k - 1]] - ctx.layover - bus.conn[k - 1] / ctx.v * 60
                 for k in range(i + 1, j + 1))
    servicio = sum(sim.arr[r] - sim.dep[r] for r in rows[i:j + 1])
    return dict(km_pullout=km_out, km_conexion=km_conn, km_pullin=km_in, kwh=energia, kwh_expediciones=kwh_exp,
                salida_patio_min=s, llegada_patio_min=a, listo_min=a + energia / ctx.P * 60 + h,
                espera_entre_viajes_min=espera, minutos_con_pasajeros=servicio)


def validar_tramo(ctx, bus, i, j):
    """Revision independiente paso a paso: parte lleno, nunca baja del minimo y siempre puede volver al patio."""
    sim, rows, c = ctx.sim, bus.rows, ctx.c
    s = sim.L - ctx.km_salida(bus, i) * c
    for k in range(i, j + 1):
        if k > i:
            s -= bus.conn[k - 1] * c
        s -= sim.kwh[rows[k]]
        assert s - ctx.km_vuelta(bus, k) * c >= sim.smin - 1e-6, (
            f"Tramo infactible en la jornada {bus.jid} (expediciones {i}-{j}): tras la expedicion {k} no puede "
            f"volver al patio sin bajar del minimo.")
    assert s - ctx.km_vuelta(bus, j) * c >= sim.smin - 1e-6


# --------------------------------------------------------------------------- #
# 3b. Re-encadenamiento (flujo de costo minimo en la linea de tiempo del patio)
# --------------------------------------------------------------------------- #

def flota_por_intervalos(salidas, listos):
    """Maximo de intervalos [salida, listo) superpuestos (chequeo independiente de la flota)."""
    ev = sorted([(t, 0) for t in listos] + [(t, 1) for t in salidas])     # en empate, primero se libera
    act = pico = 0
    for _, tipo in ev:
        act += 1 if tipo == 1 else -1
        pico = max(pico, act)
    return pico


def resolver_flujo(tramos, costo_bus):
    """Flujo de costo minimo: fuente -> tramo (costo bus), tramo -> evento 'listo' en la linea de tiempo del patio,
    espera en la linea de tiempo, evento 'salida' -> tramo, tramo -> sumidero. Devuelve (buses, segundos)."""
    t0 = time.perf_counter()
    n = len(tramos)
    E = pd.DataFrame({"t": np.concatenate([tramos["listo_min"].values, tramos["salida_patio_min"].values]),
                      "tipo": np.r_[np.zeros(n, int), np.ones(n, int)],            # 0 = listo, 1 = salida
                      "tramo": np.r_[np.arange(n), np.arange(n)]})
    E = E.sort_values(["t", "tipo"]).reset_index(drop=True)                        # en empate, listo antes que salida
    E["nodo"] = np.arange(len(E)) + n
    L, D = E[E["tipo"] == 0], E[E["tipo"] == 1]
    esp_de, esp_a = E["nodo"].values[:-1], E["nodo"].values[1:]
    colas = np.concatenate([L["tramo"].values, D["nodo"].values, esp_de, np.full(n, -1), np.arange(n)])
    cabezas = np.concatenate([L["nodo"].values, D["tramo"].values, esp_a, np.arange(n), np.full(n, -2)])
    costo = np.concatenate([np.zeros(len(L) + len(D) + len(esp_de)), np.full(n, costo_bus), np.zeros(n)])
    N, M = n + len(E), len(colas)
    ok_c, ok_h = colas >= 0, cabezas >= 0
    Aout = sps.csr_matrix((np.ones(ok_c.sum()), (colas[ok_c], np.where(ok_c)[0])), shape=(N, M))
    Ain = sps.csr_matrix((np.ones(ok_h.sum()), (cabezas[ok_h], np.where(ok_h)[0])), shape=(N, M))
    m = gp.Model()
    m.Params.OutputFlag = 0
    x = m.addMVar(M, lb=0, obj=costo)
    m.addConstr(Ain[:n] @ x == 1)
    m.addConstr(Aout[:n] @ x == 1)
    m.addConstr(Ain[n:] @ x == Aout[n:] @ x)
    m.optimize()
    assert m.Status == gp.GRB.OPTIMAL, f"El flujo de re-encadenamiento no resolvio al optimo (status {m.Status})."
    xv = x.X
    assert np.all(np.abs(xv - np.round(xv)) < 1e-6), "El flujo entrego una solucion fraccional (se esperaba entera)."
    buses = int(round(xv[-2 * n:-n].sum()))
    assert abs(m.ObjVal - buses * costo_bus) < 1e-6
    return buses, time.perf_counter() - t0


def armar_cadenas(tramos):
    """Recorre el dia: en cada salida del patio toma, entre los buses ya listos, el que llego primero al patio
    ("sale primero el que lleva mas tiempo en el patio"); si no hay ninguno listo, entra un bus nuevo."""
    ev = sorted([(r.listo_min, 0, k) for k, r in enumerate(tramos.itertuples())]
                + [(r.salida_patio_min, 1, k) for k, r in enumerate(tramos.itertuples())])
    llegada = tramos["llegada_patio_min"].values
    listos, cadena_de, cadenas = [], {}, []
    for _, tipo, k in ev:
        if tipo == 0:
            if k in cadena_de:                 # el tramo ya fue hecho por un bus: ese bus queda disponible
                heapq.heappush(listos, (llegada[k], k, cadena_de[k]))
            continue
        if listos:
            _, _, b = heapq.heappop(listos)
        else:
            b = len(cadenas)
            cadenas.append([])
        cadenas[b].append(k)
        cadena_de[k] = b
    return cadenas


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #

def hora(t):
    t = t % DIA_MIN
    return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def graficar_gantt(tramos, cadenas, path_png, h):
    """Cadenas de ejemplo: las de mas tramos (servicio, recarga minima y espera en el patio)."""
    elegidas = sorted(range(len(cadenas)), key=lambda b: (-len(cadenas[b]), b))[:12]
    filas = []
    for y, b in enumerate(elegidas):
        for orden, k in enumerate(cadenas[b]):
            r = tramos.iloc[k]
            filas.append(dict(bus=b + 1, fila=y, tramo_id=r["tramo_id"], actividad="tramo",
                              inicio_min=r["salida_patio_min"], fin_min=r["llegada_patio_min"]))
            filas.append(dict(bus=b + 1, fila=y, tramo_id=r["tramo_id"], actividad="recarga minima + holgura",
                              inicio_min=r["llegada_patio_min"], fin_min=r["listo_min"]))
            if orden + 1 < len(cadenas[b]):
                sig = tramos.iloc[cadenas[b][orden + 1]]
                filas.append(dict(bus=b + 1, fila=y, tramo_id=r["tramo_id"], actividad="en el patio",
                                  inicio_min=r["listo_min"], fin_min=sig["salida_patio_min"]))
    df = pd.DataFrame(filas)
    colores = {"tramo": gr.CATEGORICOS[0], "recarga minima + holgura": gr.CATEGORICOS[1], "en el patio": gr.GRILLA}
    fig, ax = plt.subplots(figsize=(11, 0.45 * len(elegidas) + 1.6))
    for act, g in df.groupby("actividad", sort=False):
        ax.barh(g["fila"], (g["fin_min"] - g["inicio_min"]) / 60, left=g["inicio_min"] / 60, height=0.6,
                color=colores[act], label=act)
    ax.set_yticks(range(len(elegidas)))
    ax.set_yticklabels([f"bus {b + 1} ({len(cadenas[b])} tramos)" for b in elegidas], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Hora del dia (h; mas de 24 = madrugada del dia siguiente)")
    ax.set_title(f"Cadenas de la Etapa 3 con mas tramos (holgura {h} min): el bus vuelve al patio, recarga y "
                 "sale con otro tramo", fontsize=10, loc="left")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
    gr.estilo(ax)
    ax.grid(False)
    gr.guardar(fig, path_png, df.round(2))


def graficar_llegadas(tramos, ventanas, path_png):
    """Llegadas al patio por hora del dia, separadas en las que siguen trabajando (ventana intermedia) y las que
    terminan su dia (nocturna), y salidas del patio."""
    hora_lleg = (ventanas["llegada_min"] % DIA_MIN // 60).astype(int)
    tab = pd.DataFrame({"hora": range(24)})
    for tipo in ("intermedia", "nocturna"):
        tab[f"llegadas_{tipo}"] = hora_lleg[ventanas["tipo"] == tipo].value_counts().reindex(range(24), fill_value=0).values
    tab["salidas_patio"] = (tramos["salida_patio_min"] % DIA_MIN // 60).astype(int).value_counts() \
        .reindex(range(24), fill_value=0).values
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.bar(tab["hora"], tab["llegadas_intermedia"], color=gr.CATEGORICOS[1], edgecolor=gr.FONDO, linewidth=1,
           label="llegan y vuelven a salir (intermedia)")
    ax.bar(tab["hora"], tab["llegadas_nocturna"], bottom=tab["llegadas_intermedia"], color=gr.CATEGORICOS[0],
           edgecolor=gr.FONDO, linewidth=1, label="llegan y terminan el dia (nocturna)")
    ax.step(tab["hora"], tab["salidas_patio"], where="mid", color=gr.TEXTO, linewidth=1.2, label="salidas del patio")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hora del dia")
    ax.set_ylabel("buses por hora")
    ax.set_title("Llegadas al patio por hora (insumo de la Etapa 4)", fontsize=10, loc="left")
    ax.legend(fontsize=8, frameon=False)
    gr.estilo(ax)
    gr.guardar(fig, path_png, tab)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terminal", default=parametros.TERMINAL_INSTANCIA, help="depot_id del electroterminal.")
    parser.add_argument("--escenario", default="E1", help="Jornadas del VSP de entrada (E1: con interlining).")
    parser.add_argument("--holgura", type=float, default=parametros.HOLGURAS_RECARGA_MIN[0],
                        help="Holgura h (min) sumada al tiempo de recarga antes de tomar otro tramo.")
    parser.add_argument("--rutas", nargs="*", default=None,
                        help="Solo para pruebas chicas: deja las jornadas que tocan esas rutas.")
    args = parser.parse_args()
    t_inicio = time.perf_counter()
    h = args.holgura
    h_txt = f"{h:g}"

    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    ex_ids = ex["expedicion_id"].tolist()
    ex_idx = {e: i for i, e in enumerate(ex_ids)}
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    costos = parametros.cargar_costos()
    patios = instancia.patios_terminal(depots, args.terminal)
    nombre = instancia.nombre_terminal(depots, patios)
    carpeta = instancia.carpeta_instancia(depots, args.terminal) / ("etapa3_prueba" if args.rutas else "etapa3")
    salida = carpeta / f"h{h_txt}"
    tablas, graficos = salida / "tablas", salida / "graficos"
    for d in (tablas, graficos):
        d.mkdir(parents=True, exist_ok=True)

    print(f"=== ETAPA 3: cortes y re-encadenamiento (terminal {nombre}, jornadas {args.escenario}, holgura {h_txt} min) ===\n")
    j = pd.read_csv(DATA_PROCESSED / f"jornadas_{args.escenario}.csv", sep=CSV_SEP,
                    dtype={"depot_salida": str, "depot_llegada": str})
    j = instancia.filtrar_jornadas(j, patios)
    if args.rutas:
        j = instancia.filtrar_rutas(j, ex, args.rutas)
        print(f"  PRUEBA CHICA: solo las jornadas que tocan las rutas {args.rutas}.")
    depots_t = depots[depots["depot_id"].astype(str).isin(patios)].reset_index(drop=True)
    unir = [d for d in parametros.ELECTROTERMINALES_UNIDOS if d in patios]
    sim = caso_base.Simulador(ex, depots_t, costos, 1.0, unir, caso_base.cargar_tarifa(), set())
    buses = caso_base.construir_buses(sim, j, ex_idx)
    print(f"  Jornadas del VSP en el terminal: {len(j):,} | expediciones: {int(j['n_expediciones'].sum()):,}")
    idle_vsp_h = caso_base.validar_reconstruccion(sim, j, buses, None)
    ctx = Contexto(sim, costos)

    # --- 3a: corte ---
    t0 = time.perf_counter()
    filas = []
    km_extra_total = 0.0
    for b in buses:
        cortes = cortar_jornada(ctx, b)
        for p, (i, jj) in enumerate(cortes, start=1):
            validar_tramo(ctx, b, i, jj)
            d = datos_tramo(ctx, b, i, jj, h)
            filas.append(dict(tramo_id=f"{b.jid}.{p}", jornada_vsp=b.jid, parte=p, n_partes=len(cortes),
                              n_expediciones=jj - i + 1,
                              expedicion_ids=";".join(ex_ids[r] for r in b.rows[i:jj + 1]), **d))
        for (_, j1), (i2, _) in zip(cortes[:-1], cortes[1:]):
            km_extra_total += ctx.km_vuelta(b, j1) + ctx.km_salida(b, i2) - b.conn[j1]
    tramos = pd.DataFrame(filas)
    t_corte = time.perf_counter() - t0
    n_cortadas = int((tramos.groupby("jornada_vsp").size() > 1).sum())
    print(f"\n--- 3a. Corte: {len(tramos):,} tramos desde {len(j):,} jornadas ({n_cortadas:,} jornadas cortadas; "
          f"{km_extra_total:,.1f} km extra) en {t_corte:.2f} s")

    cubiertas = [e for s in tramos["expedicion_ids"] for e in s.split(";")]
    todas = [e for s in j["expedicion_ids"] for e in s.split(";")]
    assert len(cubiertas) == len(set(cubiertas)) == len(todas) and set(cubiertas) == set(todas), \
        "Cobertura rota: alguna expedicion del terminal quedo sin tramo o en dos tramos."
    assert (tramos["kwh"] <= ctx.util + 1e-6).all(), "Hay un tramo que consume mas que la bateria util."
    # energia de las jornadas del VSP recalculada con los mismos km (validar_reconstruccion ya exigio que calce con el CSV)
    kwh_vsp = float(sum(sum(sim.kwh[r] for r in b.rows) + (b.pullout_km + sum(b.conn) + b.pullin_km) * ctx.c
                        for b in buses))
    dif = tramos["kwh"].sum() - (kwh_vsp + km_extra_total * ctx.c)
    assert abs(dif) < 1e-6 * len(j), f"Balance de energia roto: tramos - (VSP + km extra) = {dif:.6f} kWh."
    print(f"  [OK] Cobertura exacta de las {len(todas):,} expediciones | todo tramo factible paso a paso "
          f"(SOC >= {costos.min_soc:.0%} y puede volver) | energia de los tramos = VSP + km extra x {ctx.c} kWh/km.")

    # --- 3b: re-encadenamiento ---
    buses_flujo, t_flujo = resolver_flujo(tramos, costos.vehicle_fixed_cost)
    cadenas = armar_cadenas(tramos)
    flota_int = flota_por_intervalos(tramos["salida_patio_min"].values, tramos["listo_min"].values)
    salida_t, listo_t = tramos["salida_patio_min"].values, tramos["listo_min"].values
    for c in cadenas:
        for k, l in zip(c[:-1], c[1:]):
            assert salida_t[l] >= listo_t[k] - 1e-9, f"Cadena infactible en tiempo: el tramo {l} sale antes de que el {k} este listo."
    assert sorted(k for c in cadenas for k in c) == list(range(len(tramos))), "Las cadenas no cubren cada tramo una vez."
    assert buses_flujo == len(cadenas) == flota_int, (
        f"Flota inconsistente: flujo {buses_flujo}, cadenas {len(cadenas)}, maximo de intervalos {flota_int}.")
    print(f"\n--- 3b. Re-encadenamiento: {buses_flujo:,} buses en {t_flujo:.2f} s")
    print(f"  [OK] Solucion entera | cadenas factibles en tiempo | flota del flujo = cadenas = maximo de intervalos "
          f"superpuestos ({flota_int:,}).")

    # --- Ventanas de carga ---
    bus_de = {k: b for b, c in enumerate(cadenas) for k in c}
    tramos.insert(0, "bus", [bus_de[k] + 1 for k in range(len(tramos))])
    tramos.insert(1, "orden_en_bus", [cadenas[bus_de[k]].index(k) + 1 for k in range(len(tramos))])
    fil_c, fil_v = [], []
    for b, c in enumerate(cadenas, start=1):
        primera = tramos.iloc[c[0]]
        fil_c.append(dict(bus=b, n_tramos=len(c), tramo_ids=";".join(tramos["tramo_id"].iloc[c]),
                          primera_salida_min=primera["salida_patio_min"],
                          ultima_llegada_min=tramos["llegada_patio_min"].iloc[c[-1]],
                          kwh_total=tramos["kwh"].iloc[c].sum()))
        for o, k in enumerate(c):
            r = tramos.iloc[k]
            nocturna = o == len(c) - 1
            # Nocturna: hora limite = primera salida del bus al dia siguiente. Como el flujo (igual que el VSP) es de un
            # dia y no ciclico, una cadena puede durar mas de 24 h (limite <= llegada): esa salida la cubre un bus de
            # reserva en la Etapa 4, la misma regla del caso base.
            d = primera["salida_patio_min"] + DIA_MIN if nocturna else tramos["salida_patio_min"].iloc[c[o + 1]]
            fil_v.append(dict(ventana_id=len(fil_v) + 1, bus=b, tipo="nocturna" if nocturna else "intermedia",
                              tramo_id=r["tramo_id"], llegada_min=r["llegada_patio_min"], limite_min=d,
                              kwh=r["kwh"], minutos_carga_plena=r["kwh"] / ctx.P * 60,
                              holgura_min=d - r["llegada_patio_min"] - r["kwh"] / ctx.P * 60))
    ventanas = pd.DataFrame(fil_v)
    cadenas_df = pd.DataFrame(fil_c)
    vi = ventanas[ventanas["tipo"] == "intermedia"]
    assert (vi["holgura_min"] >= h - 1e-6).all(), "Una ventana intermedia no alcanza la recarga completa mas la holgura."
    assert abs(ventanas["kwh"].sum() - tramos["kwh"].sum()) < 1e-6, "La energia de las ventanas no calza con la de los tramos."
    vn = ventanas[ventanas["tipo"] == "nocturna"]
    n_mas_24h = int((vn["limite_min"] <= vn["llegada_min"]).sum())
    n_noct_sin_tiempo = int((vn["holgura_min"] < 0).sum())
    print(f"  [OK] {len(ventanas):,} ventanas ({len(vi):,} intermedias, {len(vn):,} nocturnas): "
          f"cada una repone su tramo; energia de las ventanas = energia de los tramos.")
    print(f"  Nocturnas que no alcanzan la recarga completa ni con puesto libre: {n_noct_sin_tiempo:,} (de ellas "
          f"{n_mas_24h:,} son cadenas de mas de 24 h). Iran a reserva en la Etapa 4, como en el caso base.")

    # --- Diagnostico de flota ---
    s_vsp = np.array([sim.dep[b.rows[0]] - ctx.layover - b.pullout_km / ctx.v * 60 for b in buses])
    a_vsp = np.array([sim.arr[b.rows[-1]] + b.pullin_km / ctx.v * 60 for b in buses])
    diag = pd.DataFrame([
        dict(paso="(i) VSP", buses=len(j), que_mide="Punto de partida: una jornada = un bus"),
        dict(paso="(ii) Reuso del patio sin bateria", buses=flota_por_intervalos(s_vsp, a_vsp),
             que_mide="Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga"),
        dict(paso="(iii) Solo cortes", buses=len(tramos), que_mide="Cada tramo un bus"),
        dict(paso="(iv) Cortes + re-encadenamiento", buses=len(cadenas),
             que_mide=f"La Etapa 3 completa (recarga completa + holgura {h_txt} min)"),
    ])
    print("\n--- Diagnostico de flota ---")
    for r in diag.itertuples():
        print(f"  {r.paso:36s} {r.buses:6,}")

    # --- Salidas ---
    t_total = time.perf_counter() - t_inicio
    mem = medicion.pico_memoria_mb()
    tramos_out = tramos.copy()
    for col in ("salida_patio_min", "llegada_patio_min", "listo_min"):
        tramos_out[col.replace("_min", "_hora")] = tramos_out[col].map(hora)
    tramos_out.round(4).to_csv(tablas / "tramos.csv", index=False, sep=CSV_SEP)
    cadenas_df.round(4).to_csv(tablas / "cadenas.csv", index=False, sep=CSV_SEP)
    ventanas.round(4).to_csv(tablas / "ventanas.csv", index=False, sep=CSV_SEP)
    diag.to_csv(tablas / "diagnostico_flota.csv", index=False, sep=CSV_SEP)
    km_vac = float((tramos["km_pullout"] + tramos["km_conexion"] + tramos["km_pullin"]).sum())
    resumen = dict(terminal=nombre, escenario_vsp=args.escenario, holgura_min=h, prueba=int(bool(args.rutas)),
                   jornadas_vsp=len(j), buses_vsp=len(j), buses_reuso_sin_bateria=int(diag["buses"].iloc[1]),
                   tramos=len(tramos), jornadas_cortadas=n_cortadas, buses_etapa3=len(cadenas),
                   ventanas_intermedias=len(vi), ventanas_nocturnas=len(vn),
                   nocturnas_sin_tiempo_carga=n_noct_sin_tiempo, cadenas_mas_24h=n_mas_24h,
                   km_extra_cortes=round(km_extra_total, 2), km_vacios=round(km_vac, 2),
                   km_comerciales=round(float(ex.loc[[ex_idx[e] for e in todas], "distance_km"].sum()), 2),
                   kwh_vsp=round(kwh_vsp, 2), kwh_tramos=round(float(tramos["kwh"].sum()), 2),
                   espera_entre_viajes_h=round(float(tramos["espera_entre_viajes_min"].sum()) / 60, 2),
                   espera_vsp_h=round(idle_vsp_h, 2),
                   horas_con_pasajeros=round(float(tramos["minutos_con_pasajeros"].sum()) / 60, 2),
                   segundos_corte=round(t_corte, 2), segundos_flujo=round(t_flujo, 2), segundos_total=round(t_total, 1),
                   memoria_mb=round(mem))
    pd.DataFrame([resumen]).to_csv(tablas / "resumen.csv", index=False, sep=CSV_SEP)
    graficar_gantt(tramos, cadenas, graficos / "gantt_cadenas.png", h_txt)
    graficar_llegadas(tramos, ventanas, graficos / "llegadas_patio_por_hora.png")

    lineas = [
        f"# Etapa 3 - Cortes y re-encadenamiento, {nombre} (jornadas {args.escenario}, holgura {h_txt} min)",
        "",
        "## Diagnostico de flota",
        "",
        diag.to_markdown(index=False),
        "",
        "## Cifras",
        "",
        f"- Tramos: {len(tramos):,} ({n_cortadas:,} de {len(j):,} jornadas se cortan); km extra por los cortes: "
        f"{km_extra_total:,.1f} km.",
        f"- Energia: {tramos['kwh'].sum() / 1000:,.2f} MWh en los tramos (VSP: {kwh_vsp / 1000:,.2f} MWh).",
        f"- Ventanas de carga: {len(vi):,} intermedias y {len(ventanas) - len(vi):,} nocturnas. Holgura mediana de las "
        f"intermedias: {vi['holgura_min'].median() if len(vi) else float('nan'):,.0f} min; de las nocturnas: "
        f"{vn['holgura_min'].median():,.0f} min.",
        f"- Ventanas nocturnas que no alcanzan la recarga completa ni con puesto libre: {n_noct_sin_tiempo:,}; de ellas "
        f"{n_mas_24h:,} son cadenas de mas de 24 h (el flujo, como el VSP, es de un dia y no ciclico). La Etapa 4 las "
        "cubre con un bus de reserva, la misma regla del caso base.",
        "",
        "## Validaciones (todas pasaron)",
        "- Reconstruccion de las jornadas = VSP (kWh por jornada).",
        "- Cobertura exacta de cada expedicion del terminal.",
        "- Cada tramo factible al revisarlo paso a paso (SOC >= minimo y puede volver al patio).",
        "- Solucion del flujo entera; cadenas factibles en tiempo.",
        "- Flota del flujo = numero de cadenas = maximo de intervalos [salida, listo) superpuestos.",
        "- Balance de energia: tramos = VSP + km extra; ventanas = tramos.",
        "",
        "## Tiempo y memoria",
        f"- Corte: {t_corte:.2f} s | flujo: {t_flujo:.2f} s | total: {t_total:.1f} s | pico de memoria: {mem:,.0f} MB.",
        "",
        "## Archivos",
        "- `tablas/tramos.csv`: un tramo por fila (bus, jornada del VSP, expediciones, km, kWh, salida, llegada y listo).",
        "- `tablas/cadenas.csv`: los tramos de cada bus en orden.",
        "- `tablas/ventanas.csv`: ventanas de carga (llegada, hora limite, kWh, holgura) = entrada de la Etapa 4.",
        "- `tablas/diagnostico_flota.csv`, `tablas/resumen.csv`.",
        "- `graficos/gantt_cadenas.png` (+ .csv): cadenas con mas tramos.",
        "- `graficos/llegadas_patio_por_hora.png` (+ .csv): llegadas al patio por hora.",
    ]
    (salida / "reporte.md").write_text(nombres.renombrar_texto("\n".join(lineas)), encoding="utf-8")
    print(f"\n  -> {salida}")
    print(f"\n  Tiempo: {t_total:,.1f} s | pico de memoria: {mem:,.0f} MB")
    print("\n=== FIN ETAPA 3 ===")


if __name__ == "__main__":
    main()
