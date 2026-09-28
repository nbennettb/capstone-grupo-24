"""
Etapa 2 del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia_y_avance.md seccion 1).

Asignacion de expediciones a buses (Electric Vehicle Scheduling Problem SIN
la restriccion de bateria) como un flujo de costo minimo en una red
espacio-tiempo (Kliewer, Mellouli & Suhl, 2006): cada expedicion es un
nodo, cada electroterminal tiene una "linea de tiempo" de eventos de
llegada/salida, y una unidad de flujo = un bus. La matriz de restricciones
es de red (totalmente unimodular), por lo que la relajacion LP entrega
directamente una solucion entera: no hace falta declarar variables
binarias/enteras.

A diferencia del prototipo exploratorio del 28/09 (an3.py, fuera del
repo), este script SI modela los arcos de *pullout* (electroterminal ->
primera expedicion de la jornada) y *pullin* (ultima expedicion ->
electroterminal), con costo real de deadhead hacia el electroterminal mas
cercano permitido segun el modo. Sin esto no se puede saber a que
electroterminal "pertenece" cada bus, dato que necesitan las Etapas 3-4.

Tres modos (--modo):
  ruta:    caso base. Cada ruta usa solo sus propios buses (interlining
           solo dentro de la misma ruta). Electroterminal de cada ruta =
           el mas cercano al centroide de sus paraderos terminales.
  libre:   cota inferior C0. Interlining libre entre cualquier ruta (sujeto
           al radio maximo), y cada bus elige el electroterminal mas
           barato en cada pullout/pullin. Es el mejor caso posible.
  cluster: interlining solo entre rutas asignadas al mismo electroterminal
           segun un archivo de asignacion de la Etapa 1 (--asignacion).

Uso:
    # Checkpoint chico (ver docs/context/01_metodologia_y_avance.md):
    python scripts/6-vsp_asignacion_buses.py --modo ruta --subset 101 102 301
    python scripts/6-vsp_asignacion_buses.py --modo libre --subset 101 102 301

    # Red completa:
    python scripts/6-vsp_asignacion_buses.py --modo ruta
    python scripts/6-vsp_asignacion_buses.py --modo libre

    # Por cluster (requiere haber corrido antes 4-clustering_nearest.py /
    # 5-clustering_milp.py):
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1.csv --etiqueta cluster_c1
"""

import argparse
import sys
import time
from collections import deque
from pathlib import Path

import gurobipy as gp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.sparse as sps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import geo, parametros                                          # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("06_vsp")
RESUMEN_PATH = RESULTS / "resumen_escenarios.csv"


# --------------------------------------------------------------------------- #
# Carga de datos
# --------------------------------------------------------------------------- #

def cargar_expediciones(subset_rutas=None):
    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    if subset_rutas:
        subset_rutas = {str(r) for r in subset_rutas}
        ex = ex[ex["route_id"].astype(str).isin(subset_rutas)].reset_index(drop=True)
        if ex.empty:
            raise ValueError(f"--subset {subset_rutas} no matchea ninguna route_id en expediciones.csv")
    else:
        ex = ex.reset_index(drop=True)
    return ex


def cargar_depots():
    return pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)


# --------------------------------------------------------------------------- #
# Electroterminal asignado a cada expedicion (para pullout/pullin) y grupo de
# interlining (que determina con que otras expediciones se puede encadenar)
# --------------------------------------------------------------------------- #

def depot_mas_cercano_por_ruta(ex, depots, factor_desvio):
    """Para cada ruta, el electroterminal mas cercano al centroide de sus
    paraderos terminales (usado en el modo 'ruta': el bus de una ruta
    siempre sale/vuelve al mismo electroterminal base)."""
    pts = pd.concat([
        ex[["route_id", "o_lat", "o_lon"]].rename(columns={"o_lat": "lat", "o_lon": "lon"}),
        ex[["route_id", "d_lat", "d_lon"]].rename(columns={"d_lat": "lat", "d_lon": "lon"}),
    ])
    centroides = pts.groupby("route_id")[["lat", "lon"]].mean()
    P = geo.xy(centroides["lat"].values, centroides["lon"].values)
    DP = geo.xy(depots["lat"].values, depots["lon"].values)
    d = geo.matriz_distancias_planas(P, DP) * factor_desvio
    idx = d.argmin(axis=1)
    return pd.Series(idx, index=centroides.index)  # route_id -> indice de depot (0..4)


def calcular_asignacion_depots(ex, depots, modo, asignacion_df, factor_desvio):
    """Devuelve, para cada expedicion, el/los indices de electroterminal
    permitidos para pullout/pullin:
      - 'libre': None (senal de que se permite CUALQUIER electroterminal,
        se usa el mas barato para cada expedicion individualmente).
      - 'ruta' / 'cluster': un indice fijo por expedicion (columna del
        DataFrame), determinado por su ruta.
    """
    if modo == "libre":
        return None
    if modo == "ruta":
        idx_por_ruta = depot_mas_cercano_por_ruta(ex, depots, factor_desvio)
    elif modo == "cluster":
        depot_id_a_idx = {d: i for i, d in enumerate(depots["depot_id"].astype(str).values)}
        idx_por_ruta = (asignacion_df.set_index(asignacion_df["route_id"].astype(str))["depot_id"]
                         .astype(str).map(depot_id_a_idx))
        faltantes = set(ex["route_id"].astype(str)) - set(idx_por_ruta.index)
        if faltantes:
            raise ValueError(f"{len(faltantes)} rutas de expediciones.csv no tienen asignacion de "
                              f"electroterminal en el archivo --asignacion (ej: {sorted(faltantes)[:5]}). "
                              f"Revisar que la Etapa 1 se haya corrido sobre las mismas rutas.")
    else:
        raise ValueError(f"modo desconocido: {modo}")
    return ex["route_id"].astype(str).map(idx_por_ruta).values.astype(int)


def costos_pullout_pullin(ex, depots, idx_fijo, factor_desvio):
    """Distancia (km, ya con factor de desvio aplicado) y electroterminal
    elegido para el pullout (deposito -> origen de la expedicion) y el
    pullin (destino de la expedicion -> deposito) de cada expedicion.

    idx_fijo=None -> se permite cualquier electroterminal, se usa el mas
    barato (esto es lo que hace que el modo 'libre' sea una cota inferior).
    idx_fijo=array -> un electroterminal fijo por expedicion (modos 'ruta'
    y 'cluster').
    """
    O = geo.xy(ex["o_lat"].values, ex["o_lon"].values)
    D = geo.xy(ex["d_lat"].values, ex["d_lon"].values)
    DP = geo.xy(depots["lat"].values, depots["lon"].values)
    dist_o = geo.matriz_distancias_planas(O, DP) * factor_desvio  # n x k_depots
    dist_d = geo.matriz_distancias_planas(D, DP) * factor_desvio

    n = len(ex)
    if idx_fijo is None:
        idx_out = dist_o.argmin(axis=1)
        idx_in = dist_d.argmin(axis=1)
    else:
        idx_out = idx_fijo
        idx_in = idx_fijo
    filas = np.arange(n)
    return dist_o[filas, idx_out], idx_out, dist_d[filas, idx_in], idx_in


# --------------------------------------------------------------------------- #
# Construccion y resolucion del flujo de costo minimo
# --------------------------------------------------------------------------- #

def construir_grupos(ex, modo, idx_depot_fijo):
    """Etiqueta de grupo por expedicion: dos expediciones solo pueden
    encadenarse (interlining) si comparten grupo (ademas de cumplir el
    radio maximo). 'ruta' -> route_id; 'libre' -> un unico grupo; 'cluster'
    -> electroterminal asignado."""
    if modo == "ruta":
        return ex["route_id"].astype(str).values
    if modo == "libre":
        return np.full(len(ex), "TODAS", dtype=object)
    if modo == "cluster":
        return idx_depot_fijo.astype(str)
    raise ValueError(modo)


def resolver_flujo(ex, grupo, pullout_km, pullin_km, costos, radio_km):
    """Arma y resuelve el flujo de costo minimo en la red espacio-tiempo.
    Devuelve (x_arcos_usados_df, buses, deadhead_km_interlining, espera_h,
    tiempo_construccion_s, tiempo_total_s)."""
    t0 = time.time()
    n = len(ex)
    dep, arr = ex["dep_min"].values, ex["arr_min"].values

    stops_all = pd.unique(pd.concat([ex["o_stop"], ex["d_stop"]]))
    sid = {s: k for k, s in enumerate(stops_all)}
    ex = ex.assign(ot=ex["o_stop"].map(sid), dt=ex["d_stop"].map(sid))
    P = np.zeros((len(stops_all), 2))
    P[ex["ot"].values] = geo.xy(ex["o_lat"].values, ex["o_lon"].values)
    P[ex["dt"].values] = geo.xy(ex["d_lat"].values, ex["d_lon"].values)
    TD = geo.matriz_distancias_planas(P, P) * parametros.FACTOR_DESVIO

    key_dep = list(zip(ex["ot"].values, grupo))
    eventos = [(k, dep[j], "D", j, 0.0) for j, k in enumerate(key_dep)]

    origenes_por_grupo = (pd.DataFrame({"b": ex["ot"].values, "g": grupo})
                           .drop_duplicates().groupby("g")["b"].apply(np.array).to_dict())
    for g, bs in origenes_por_grupo.items():
        idx_g = np.where(grupo == g)[0]
        for a in np.unique(ex["dt"].values[idx_g]):
            ii = idx_g[ex["dt"].values[idx_g] == a]
            for b in bs[TD[a, bs] <= radio_km]:
                t = arr[ii] + parametros.LAYOVER_MIN + TD[a, b] / parametros.VELOCIDAD_KMH * 60
                eventos += [((b, g), t[q], "A", ii[q], TD[a, b]) for q in range(len(ii))]

    E = pd.DataFrame(eventos, columns=["key", "t", "kind", "trip", "km"])
    E["korden"] = (E["kind"] == "D").astype(int)  # llegadas antes que salidas en empates
    E = E.sort_values(["key", "t", "korden"]).reset_index(drop=True)
    E["node"] = np.arange(len(E)) + n

    mismo_sig = (E["key"].shift(-1) == E["key"]).values
    espera_desde = E["node"].values[:-1][mismo_sig[:-1]]
    espera_hacia = E["node"].values[1:][mismo_sig[:-1]]
    espera_min = (E["t"].values[1:] - E["t"].values[:-1])[mismo_sig[:-1]]

    A = E[E["kind"] == "A"]
    Dd = E[E["kind"] == "D"]

    # Arcos: llegada->timeline (deadhead interlining), timeline->salida,
    # espera en timeline, PULLOUT (fuente->expedicion, costo bus+pullout),
    # PULLIN (expedicion->sumidero, costo pullin).
    tails = np.concatenate([A["trip"].values, Dd["node"].values, espera_desde,
                             np.full(n, -1), np.arange(n)])
    heads = np.concatenate([A["node"].values, Dd["trip"].values, espera_hacia,
                             np.arange(n), np.full(n, -2)])
    cost = np.concatenate([
        costos.cost_per_km * A["km"].values,
        np.zeros(len(Dd)),
        costos.waiting_cost_per_min * espera_min,
        costos.vehicle_fixed_cost + costos.cost_per_km * pullout_km,
        costos.cost_per_km * pullin_km,
    ])

    N, M = n + len(E), len(tails)
    ok_t, ok_h = tails >= 0, heads >= 0
    Aout = sps.csr_matrix((np.ones(ok_t.sum()), (tails[ok_t], np.where(ok_t)[0])), shape=(N, M))
    Ain = sps.csr_matrix((np.ones(ok_h.sum()), (heads[ok_h], np.where(ok_h)[0])), shape=(N, M))

    t_build = time.time() - t0
    m = gp.Model()
    m.Params.OutputFlag = 0
    x = m.addMVar(M, lb=0, obj=cost)
    m.addConstr(Ain[:n] @ x == 1)              # cada expedicion: exactamente 1 predecesor
    m.addConstr(Aout[:n] @ x == 1)             # cada expedicion: exactamente 1 sucesor
    m.addConstr(Ain[n:] @ x == Aout[n:] @ x)   # conservacion de flujo en la linea de tiempo
    m.optimize()
    if m.Status != gp.GRB.OPTIMAL:
        raise RuntimeError(f"Gurobi no encontro solucion optima (status={m.Status})")

    xv = x.X
    n_frac = int(((xv > 1e-6) & (np.abs(xv - np.round(xv)) > 1e-6)).sum())
    if n_frac:
        print(f"  [aviso] {n_frac} arcos con valor fraccional (se esperaba una solucion entera "
              f"por ser una red). Revisar antes de confiar en los resultados.")

    n_espera = len(espera_desde)
    inicio_pullout = len(A) + len(Dd) + n_espera
    resultado = dict(
        A=A, Dd=Dd, E=E, xv=xv, n=n, n_espera=n_espera, inicio_pullout=inicio_pullout,
        buses=int(round(xv[inicio_pullout: inicio_pullout + n].sum())),
        deadhead_interlining_km=float((xv[:len(A)] * A["km"].values).sum()),
        espera_h=float((xv[len(A) + len(Dd): len(A) + len(Dd) + n_espera] * espera_min).sum() / 60),
        t_build=t_build, t_total=time.time() - t0,
    )
    return resultado


def reconstruir_jornadas(res, ex, pullout_km, pullout_idx, pullin_km, pullin_idx, depots):
    """A partir de la solucion del flujo, reconstruye la secuencia de
    expediciones de cada jornada (bus), emparejando llegadas y salidas de
    cada linea de tiempo en orden FIFO (arcos con costo minimo => sin
    cruces, FIFO es correcto)."""
    A, Dd, E, xv, n = res["A"], res["Dd"], res["E"], res["xv"], res["n"]
    xa = xv[:len(A)]
    xd = xv[len(A):len(A) + len(Dd)]
    flujo_llegada = dict(zip(A["node"].values, xa > 0.5))
    flujo_salida = dict(zip(Dd["node"].values, xd > 0.5))

    succ = -np.ones(n, dtype=int)
    deadhead_km_sig = np.zeros(n)
    for _, g in E.groupby("key", sort=False):
        cola = deque()
        for r in g.itertuples():
            if r.kind == "A" and flujo_llegada[r.node]:
                cola.append((r.trip, r.km))
            elif r.kind == "D" and flujo_salida[r.node]:
                i, km = cola.popleft()
                succ[i] = r.trip
                deadhead_km_sig[i] = km

    x_pullout = xv[res["inicio_pullout"]: res["inicio_pullout"] + n]
    starts = np.where(x_pullout > 0.5)[0]

    depot_ids = depots["depot_id"].astype(str).values
    kwh = ex["kwh"].values
    # OJO: usar expedicion_id (unico por fila), NO trip_id (un mismo patron
    # GTFS se repite muchas veces por frecuencia, no identifica una salida).
    expedicion_ids = ex["expedicion_id"].values
    filas = []
    for bus_id, st in enumerate(starts, start=1):
        # OJO: pullout_km/pullin_km estan precomputados para las n
        # expediciones (todas las opciones posibles), pero solo cuentan
        # para el TOTAL de la flota cuando la expedicion es efectivamente
        # inicio (pullout) o fin (pullin) de una jornada -- por eso se
        # acumulan aqui, jornada por jornada, y no sumando el array
        # completo en main().
        secuencia, k = [], st
        km_pullout = pullout_km[st]
        km_interlining = 0.0
        kwh_total = kwh[st] + km_pullout * parametros.CONSUMO_KWH_KM
        while k >= 0:
            secuencia.append(expedicion_ids[k])
            nxt = succ[k]
            if nxt >= 0:
                km_interlining += deadhead_km_sig[k]
                kwh_total += kwh[nxt] + deadhead_km_sig[k] * parametros.CONSUMO_KWH_KM
            ultimo = k
            k = nxt
        km_pullin = pullin_km[ultimo]
        kwh_total += km_pullin * parametros.CONSUMO_KWH_KM
        filas.append(dict(
            bus_id=bus_id,
            n_expediciones=len(secuencia),
            expedicion_ids=";".join(secuencia),
            depot_salida=depot_ids[pullout_idx[st]],
            depot_llegada=depot_ids[pullin_idx[ultimo]],
            dep_min=ex["dep_min"].values[st],
            arr_min=ex["arr_min"].values[ultimo],
            duracion_min=ex["arr_min"].values[ultimo] - ex["dep_min"].values[st],
            km_pullout=km_pullout,
            km_interlining=km_interlining,
            km_pullin=km_pullin,
            km_total=km_pullout + km_interlining + km_pullin,
            kwh_total=kwh_total,
        ))
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Reportes
# --------------------------------------------------------------------------- #

def graficar_jornadas(jornadas, path_png, etiqueta):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    axs[0].hist(jornadas["kwh_total"], bins=30, color="#2c6e8f")
    axs[0].axvline(315, color="crimson", linestyle="--", label="Bateria util (315 kWh)")
    axs[0].set_xlabel("Energia por jornada (kWh)")
    axs[0].set_ylabel("Numero de jornadas")
    axs[0].legend()
    axs[1].hist(jornadas["duracion_min"] / 60, bins=30, color="#8f4a2c")
    axs[1].set_xlabel("Duracion de la jornada (h)")
    axs[1].set_ylabel("Numero de jornadas")
    fig.suptitle(f"Escenario: {etiqueta}")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def actualizar_resumen(fila: dict):
    fila_df = pd.DataFrame([fila])
    if RESUMEN_PATH.exists():
        prev = pd.read_csv(RESUMEN_PATH, sep=CSV_SEP)
        out = pd.concat([prev, fila_df], ignore_index=True)
    else:
        out = fila_df
    out.to_csv(RESUMEN_PATH, index=False, sep=CSV_SEP)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modo", required=True, choices=["ruta", "libre", "cluster"])
    parser.add_argument("--subset", nargs="*", default=None,
                         help="Checkpoint chico: lista de route_id a incluir (ej. --subset 101 102 301). "
                              "Si se omite, corre sobre toda la red.")
    parser.add_argument("--asignacion", type=str, default=None,
                         help="Requerido si --modo cluster: CSV de la Etapa 1 con columnas "
                              "route_id, depot_id (ej. data-processed/rutas_cluster_c1.csv).")
    parser.add_argument("--radio", type=float, default=parametros.RADIO_INTERLINING_KM,
                         help=f"Radio maximo de interlining en km (default {parametros.RADIO_INTERLINING_KM}).")
    parser.add_argument("--etiqueta", type=str, default=None,
                         help="Nombre del escenario para los archivos de salida. Default: el --modo, o "
                              "'cluster_<nombre del archivo --asignacion>' si --modo cluster.")
    args = parser.parse_args()

    etiqueta = args.etiqueta
    if etiqueta is None:
        etiqueta = args.modo if args.modo != "cluster" else f"cluster_{Path(args.asignacion).stem.replace('rutas_cluster_', '')}"
    if args.subset:
        etiqueta += "_subset"

    print(f"=== ETAPA 2: VSP (modo={args.modo}, radio={args.radio} km, etiqueta={etiqueta}) ===\n")

    ex = cargar_expediciones(args.subset)
    depots = cargar_depots()
    costos = parametros.cargar_costos()
    print(f"  Expediciones a asignar: {len(ex)} | rutas: {ex['route_id'].nunique()}")

    asignacion_df = None
    if args.modo == "cluster":
        if not args.asignacion:
            raise SystemExit("--modo cluster requiere --asignacion <csv de la Etapa 1>. "
                              "Correr antes scripts/4-clustering_nearest.py o 5-clustering_milp.py.")
        asignacion_df = pd.read_csv(args.asignacion, sep=CSV_SEP)

    idx_depot_fijo = calcular_asignacion_depots(ex, depots, args.modo, asignacion_df, parametros.FACTOR_DESVIO)
    grupo = construir_grupos(ex, args.modo, idx_depot_fijo)
    pullout_km, pullout_idx, pullin_km, pullin_idx = costos_pullout_pullin(
        ex, depots, idx_depot_fijo, parametros.FACTOR_DESVIO)

    print("\n--- Resolviendo flujo de costo minimo ---")
    res = resolver_flujo(ex, grupo, pullout_km, pullin_km, costos, args.radio)
    print(f"  buses={res['buses']} | deadhead interlining={res['deadhead_interlining_km']:,.0f} km | "
          f"espera={res['espera_h']:,.0f} h | t_build={res['t_build']:.0f}s | t_total={res['t_total']:.0f}s")

    print("\n--- Reconstruyendo jornadas ---")
    jornadas = reconstruir_jornadas(res, ex, pullout_km, pullout_idx, pullin_km, pullin_idx, depots)

    # --- Chequeo de cobertura: cada expedicion en exactamente 1 jornada ---
    # Se usa expedicion_id (unico por fila) y no trip_id (se repite por
    # frecuencia): con trip_id este chequeo no detectaria duplicados ni
    # faltantes, porque muchas expediciones distintas comparten trip_id.
    todas_las_expediciones = set(ex["expedicion_id"])
    cubiertos = [e for seq in jornadas["expedicion_ids"].str.split(";") for e in seq]
    assert len(cubiertos) == len(ex), (
        f"Cobertura incorrecta: {len(cubiertos)} expediciones en jornadas, se esperaban {len(ex)}.")
    assert len(set(cubiertos)) == len(ex), \
        "Hay expedicion_id repetidos entre jornadas (alguna expedicion cubierta mas de una vez)."
    assert set(cubiertos) == todas_las_expediciones, \
        "Hay expediciones que no aparecen en ninguna jornada."
    assert (jornadas["arr_min"] >= jornadas["dep_min"]).all(), "Jornada con llegada antes que salida."
    print(f"  [OK] Cobertura verificada: las {len(ex)} expediciones quedan cubiertas exactamente una vez "
          f"en {len(jornadas)} jornadas.")

    print("\n--- Guardando resultados ---")
    jornadas_path = DATA_PROCESSED / f"jornadas_{etiqueta}.csv"
    jornadas.to_csv(jornadas_path, index=False, sep=CSV_SEP)
    print(f"  -> {jornadas_path} ({len(jornadas)} jornadas)")

    png_path = RESULTS / f"graficos_{etiqueta}.png"
    graficar_jornadas(jornadas, png_path, etiqueta)
    print(f"  -> {png_path}")

    # OJO: los totales de pullout/pullin/interlining se leen de `jornadas`
    # (solo las expediciones que efectivamente son inicio/fin/enlace de una
    # jornada), NUNCA sumando pullout_km/pullin_km sobre las n expediciones
    # completas -- esos arrays traen el costo de la opcion mas barata para
    # CADA expedicion, la mayoria de las cuales no inicia ni termina ninguna
    # jornada (van "en medio" de su jornada, sin pullout/pullin propio).
    pct_mayor_315 = float((jornadas["kwh_total"] > costos.bateria_util_kwh).mean() * 100)
    km_pullout_tot = float(jornadas["km_pullout"].sum())
    km_pullin_tot = float(jornadas["km_pullin"].sum())
    km_interlining_tot = float(jornadas["km_interlining"].sum())
    assert abs(km_interlining_tot - res["deadhead_interlining_km"]) < 1.0, (
        f"Inconsistencia: interlining sumado desde jornadas ({km_interlining_tot:.1f} km) no calza con "
        f"el reportado por el solver ({res['deadhead_interlining_km']:.1f} km).")
    deadhead_total_km = km_pullout_tot + km_interlining_tot + km_pullin_tot
    cost_bus = res["buses"] * costos.vehicle_fixed_cost
    cost_deadhead = deadhead_total_km * costos.cost_per_km
    cost_comercial = float(ex["distance_km"].sum()) * costos.cost_per_km
    cost_espera = res["espera_h"] * 60 * costos.waiting_cost_per_min
    fila = dict(
        etiqueta=etiqueta, modo=args.modo, subset=",".join(args.subset) if args.subset else "",
        radio_km=args.radio, n_expediciones=len(ex), buses=res["buses"],
        deadhead_interlining_km=round(km_interlining_tot, 1),
        pullout_km=round(km_pullout_tot, 1), pullin_km=round(km_pullin_tot, 1),
        deadhead_total_km=round(deadhead_total_km, 1), espera_h=round(res["espera_h"], 1),
        pct_jornadas_mayor_315kwh=round(pct_mayor_315, 1),
        cost_bus_usd=round(cost_bus, 0), cost_deadhead_usd=round(cost_deadhead, 0),
        cost_comercial_usd=round(cost_comercial, 0), cost_espera_usd=round(cost_espera, 0),
        cost_total_usd=round(cost_bus + cost_deadhead + cost_comercial + cost_espera, 0),
        tiempo_computo_s=round(res["t_total"], 1),
    )
    actualizar_resumen(fila)
    print(f"  -> {RESUMEN_PATH} (fila agregada: {etiqueta})")

    print(f"\n  Resumen: {res['buses']} buses | costo total ~ {fila['cost_total_usd']:,.0f} USD | "
          f"{pct_mayor_315:.1f}% de jornadas superan la bateria util ({costos.bateria_util_kwh:.0f} kWh)")
    print("\n=== FIN ETAPA 2 ===")


if __name__ == "__main__":
    main()
