"""
Etapa 2 del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md seccion 4).

Asignacion de expediciones a buses (Electric Vehicle Scheduling Problem SIN
la restriccion de bateria) como un flujo de costo minimo en una red
espacio-tiempo (Kliewer, Mellouli & Suhl, 2006): cada expedicion es un
nodo, cada electroterminal tiene una "linea de tiempo" de eventos de
llegada/salida, y una unidad de flujo = un bus. La matriz de restricciones
es de red (totalmente unimodular), por lo que la relajacion LP entrega
directamente una solucion entera: no hace falta declarar variables
binarias/enteras.

El modelo incluye los arcos de *pullout* (electroterminal -> primera
expedicion de la jornada) y *pullin* (ultima expedicion -> electroterminal),
con costo real de deadhead hacia el electroterminal permitido segun el modo.
Asi cada jornada "pertenece" a un electroterminal, dato que necesitan las
Etapas 3-4.

Tres modos (--modo):
  ruta:    CASO BASE (escenario E0). Cada ruta usa solo sus propios buses
           (interlining solo dentro de la misma ruta). El electroterminal de
           cada ruta sale del archivo --asignacion de la Etapa 1.
  cluster: interlining solo entre rutas asignadas al mismo electroterminal
           segun --asignacion (escenario E1).
  En ambos modos, --unir-electroterminales trata los electroterminales indicados
  como UN solo terminal (Los Espinos y Santa Rosa, en todos los escenarios
  operacionales; sin unirlos Los Espinos no tiene puestos para reponer su energia,
  Etapa 3). En cluster forman ademas UN solo grupo de interlining: una jornada puede
  salir de un patio y volver al otro; no viola el retorno porque es un solo
  electroterminal. Sin la opcion se obtienen los escenarios de evidencia E0_sep y E1_sep.
  libre:   COTA INFERIOR (LB). Interlining libre entre cualquier ruta (sujeto
           al radio maximo) y cada bus elige el electroterminal mas barato en
           cada pullout/pullin. VIOLA el retorno al propio electroterminal:
           no es un escenario operacional.

Retorno [Profesor]: en 'ruta' y 'cluster' toda jornada empieza y termina en
el mismo electroterminal (o en el mismo terminal unido); el script falla si
no se cumple. En 'libre' solo se cuenta cuantas jornadas lo violan.

Costos: se reporta el costo de OPERACION = flota + km sin pasajeros + espera
(lo que cambia entre escenarios). El costo de los km con pasajeros es igual
en todos los escenarios y se reporta aparte, sin sumarlo. La energia se agrega
en la Etapa 3 (simulador de carga).

Input:  data-processed/expediciones.csv, data-filtrado/depots.csv,
        data-processed/rutas_cluster_*.csv (modos ruta y cluster)
Output: data-processed/jornadas_<etiqueta>.csv
        results/etapa2_vsp/tablas/resumen_escenarios.csv  (una fila por etiqueta)
        results/etapa2_vsp/tablas/resumen_sensibilidad.csv (corridas con --sin-jornadas)
        results/etapa2_vsp/graficos/jornadas_<etiqueta>.png

Uso:
    # Checkpoint chico (revisar a mano una jornada):
    python scripts/6-vsp_asignacion_buses.py --modo ruta --asignacion data-processed/rutas_cluster_c1b.csv --subset 101 102 301 --etiqueta E0
    python scripts/6-vsp_asignacion_buses.py --modo libre --subset 101 102 301 --etiqueta LB

    # Escalera de escenarios, red completa (terminales unidos):
    python scripts/6-vsp_asignacion_buses.py --modo ruta    --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --etiqueta E0
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --etiqueta E1
    python scripts/6-vsp_asignacion_buses.py --modo libre --etiqueta LB

    # Evidencia de por que se unen (separados):
    python scripts/6-vsp_asignacion_buses.py --modo ruta    --asignacion data-processed/rutas_cluster_c1b.csv --etiqueta E0_sep
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --etiqueta E1_sep

    # Variantes con C2 (la asignacion con restriccion de capacidad, propuesta; fuera de la escalera):
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c2.csv --unir-electroterminales --etiqueta E1_C2
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c2.csv --etiqueta E1_C2_sep

    # Sensibilidad (no escribe jornadas):
    python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --factor-desvio 1.5 --sin-jornadas --etiqueta E1_f1.5
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

RESULTS = carpeta_resultados("etapa2_vsp")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)
RESUMEN_PATH = TABLAS / "resumen_escenarios.csv"
RESUMEN_SENSIBILIDAD_PATH = TABLAS / "resumen_sensibilidad.csv"


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

def calcular_asignacion_depots(ex, depots, modo, asignacion_df):
    """Devuelve, para cada expedicion, el indice posicional del electroterminal de su ruta
    (segun la asignacion de la Etapa 1) en los modos 'ruta' y 'cluster'; None en 'libre'
    (senal de que se permite CUALQUIER electroterminal, el mas barato para cada expedicion)."""
    if modo == "libre":
        return None
    if modo not in ("ruta", "cluster"):
        raise ValueError(f"modo desconocido: {modo}")
    depot_id_a_idx = {d: i for i, d in enumerate(depots["depot_id"].astype(str).values)}
    idx_por_ruta = (asignacion_df.set_index(asignacion_df["route_id"].astype(str))["depot_id"]
                     .astype(str).map(depot_id_a_idx))
    faltantes = set(ex["route_id"].astype(str)) - set(idx_por_ruta.index)
    if faltantes:
        raise ValueError(f"{len(faltantes)} rutas de expediciones.csv no tienen asignacion de "
                          f"electroterminal en el archivo --asignacion (ej: {sorted(faltantes)[:5]}). "
                          f"Revisar que la Etapa 1 se haya corrido sobre las mismas rutas.")
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

def construir_grupos(ex, modo, idx_depot_fijo, idx_unidos=None):
    """Etiqueta de grupo por expedicion: dos expediciones solo pueden
    encadenarse (interlining) si comparten grupo (ademas de cumplir el
    radio maximo). 'ruta' -> route_id; 'libre' -> un unico grupo; 'cluster'
    -> electroterminal asignado, con los electroterminales de idx_unidos
    (indices posicionales) fusionados en un solo grupo."""
    if modo == "ruta":
        return ex["route_id"].astype(str).values
    if modo == "libre":
        return np.full(len(ex), "TODAS", dtype=object)
    if modo == "cluster":
        grupo = idx_depot_fijo.astype(str).astype(object)
        if idx_unidos:
            grupo[np.isin(idx_depot_fijo, list(idx_unidos))] = "UNIDOS"
        return grupo
    raise ValueError(modo)


def resolver_flujo(ex, grupo, pullout_km, pullin_km, costos, radio_km, factor_desvio, layover_min):
    """Arma y resuelve el flujo de costo minimo en la red espacio-tiempo.
    El deadhead entre expediciones es distancia euclidiana * factor_desvio, a
    parametros.VELOCIDAD_KMH, mas layover_min de maniobra; el radio de interlining
    se compara contra esa distancia ya multiplicada por el factor."""
    t0 = time.time()
    n = len(ex)
    dep, arr = ex["dep_min"].values, ex["arr_min"].values

    stops_all = pd.unique(pd.concat([ex["o_stop"], ex["d_stop"]]))
    sid = {s: k for k, s in enumerate(stops_all)}
    ex = ex.assign(ot=ex["o_stop"].map(sid), dt=ex["d_stop"].map(sid))
    P = np.zeros((len(stops_all), 2))
    P[ex["ot"].values] = geo.xy(ex["o_lat"].values, ex["o_lon"].values)
    P[ex["dt"].values] = geo.xy(ex["d_lat"].values, ex["d_lon"].values)
    TD = geo.matriz_distancias_planas(P, P) * factor_desvio

    key_dep = list(zip(ex["ot"].values, grupo))
    eventos = [(k, dep[j], "D", j, 0.0) for j, k in enumerate(key_dep)]

    origenes_por_grupo = (pd.DataFrame({"b": ex["ot"].values, "g": grupo})
                           .drop_duplicates().groupby("g")["b"].apply(np.array).to_dict())
    for g, bs in origenes_por_grupo.items():
        idx_g = np.where(grupo == g)[0]
        for a in np.unique(ex["dt"].values[idx_g]):
            ii = idx_g[ex["dt"].values[idx_g] == a]
            for b in bs[TD[a, bs] <= radio_km]:
                t = arr[ii] + layover_min + TD[a, b] / parametros.VELOCIDAD_KMH * 60
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
    cruces, FIFO es correcto). Ademas de la secuencia, deja los km de cada
    conexion entre expediciones consecutivas (km_deadhead_seq) para que el
    simulador de carga reconstruya exactamente los mismos traslados."""
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
        secuencia, conexiones, k = [], [], st
        km_pullout = pullout_km[st]
        km_interlining = 0.0
        kwh_total = kwh[st] + km_pullout * parametros.CONSUMO_KWH_KM
        while k >= 0:
            secuencia.append(expedicion_ids[k])
            nxt = succ[k]
            if nxt >= 0:
                km_interlining += deadhead_km_sig[k]
                conexiones.append(deadhead_km_sig[k])
                kwh_total += kwh[nxt] + deadhead_km_sig[k] * parametros.CONSUMO_KWH_KM
            ultimo = k
            k = nxt
        km_pullin = pullin_km[ultimo]
        kwh_total += km_pullin * parametros.CONSUMO_KWH_KM
        filas.append(dict(
            bus_id=bus_id,
            n_expediciones=len(secuencia),
            expedicion_ids=";".join(secuencia),
            km_deadhead_seq=";".join(f"{c:.4f}" for c in conexiones),
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

def graficar_jornadas(jornadas, path_png, etiqueta, costos):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    axs[0].hist(jornadas["kwh_total"], bins=40, color="#2c6e8f")
    for soc in parametros.SOC_CICLICO_BARRIDO:
        axs[0].axvline(costos.bateria_util_ciclica_kwh(soc), color="crimson", linestyle="--", linewidth=1)
        axs[0].text(costos.bateria_util_ciclica_kwh(soc), axs[0].get_ylim()[1] * 0.97, f" {soc:.0%}",
                    color="crimson", fontsize=8, va="top")
    axs[0].set_xlabel("Energia por jornada (kWh); lineas: bateria util por nivel de partida")
    axs[0].set_ylabel("Numero de jornadas")
    axs[1].hist(jornadas["duracion_min"] / 60, bins=30, color="#8f4a2c")
    axs[1].set_xlabel("Duracion de la jornada (h)")
    axs[1].set_ylabel("Numero de jornadas")
    for ax in axs:
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
    fig.suptitle(f"Escenario: {etiqueta}")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def actualizar_resumen(fila: dict, path):
    """Escribe la fila del escenario; si ya existe una con la misma etiqueta, la REEMPLAZA."""
    fila_df = pd.DataFrame([fila])
    if path.exists():
        prev = pd.read_csv(path, sep=CSV_SEP)
        prev = prev[prev["etiqueta"] != fila["etiqueta"]]
        out = pd.concat([prev, fila_df], ignore_index=True)
    else:
        out = fila_df
    out.to_csv(path, index=False, sep=CSV_SEP)


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
                         help="Requerido en los modos ruta y cluster: CSV de la Etapa 1 con columnas "
                              "route_id, depot_id (ej. data-processed/rutas_cluster_c1b.csv).")
    parser.add_argument("--unir-electroterminales", nargs="*", default=None, metavar="DEPOT_ID",
                         help="Modos cluster y ruta: depot_id de los electroterminales que forman UN solo terminal (en cluster, ademas, un grupo "
                              "de interlining. Sin valores, usa parametros.ELECTROTERMINALES_UNIDOS "
                              f"{parametros.ELECTROTERMINALES_UNIDOS}.")
    parser.add_argument("--radio", type=float, default=parametros.RADIO_INTERLINING_KM,
                         help=f"Radio maximo de interlining en km (default {parametros.RADIO_INTERLINING_KM}).")
    parser.add_argument("--factor-desvio", type=float, default=parametros.FACTOR_DESVIO,
                         help=f"Factor de desvio del deadhead (default {parametros.FACTOR_DESVIO}). Ojo: el radio "
                              f"se compara contra la distancia ya multiplicada por el factor.")
    parser.add_argument("--layover", type=float, default=parametros.LAYOVER_MIN,
                         help=f"Layover minimo en minutos (default {parametros.LAYOVER_MIN}).")
    parser.add_argument("--etiqueta", type=str, default=None,
                         help="Nombre del escenario para los archivos de salida (E0, E1, LB, E0_sep, E1_sep, E1_C2, E1_C2_sep...). "
                              "Default: el --modo.")
    parser.add_argument("--sin-jornadas", action="store_true",
                         help="Corrida de sensibilidad: no escribe jornadas ni grafico; la fila va a "
                              "resumen_sensibilidad.csv en vez de resumen_escenarios.csv.")
    args = parser.parse_args()

    if args.modo in ("ruta", "cluster") and not args.asignacion:
        raise SystemExit(f"--modo {args.modo} requiere --asignacion <csv de la Etapa 1> "
                          f"(ej. data-processed/rutas_cluster_c1b.csv).")
    if args.unir_electroterminales is not None and args.modo not in ("cluster", "ruta"):
        raise SystemExit("--unir-electroterminales solo tiene sentido en --modo cluster o --modo ruta.")

    etiqueta = args.etiqueta or args.modo
    if args.subset:
        etiqueta += "_subset"

    print(f"=== ETAPA 2: VSP (modo={args.modo}, etiqueta={etiqueta}, radio={args.radio} km, "
          f"factor={args.factor_desvio}, layover={args.layover} min) ===\n")

    ex = cargar_expediciones(args.subset)
    depots = cargar_depots()
    costos = parametros.cargar_costos()
    depot_ids = depots["depot_id"].astype(str).tolist()
    print(f"  Expediciones a asignar: {len(ex)} | rutas: {ex['route_id'].nunique()}")

    ids_unidos = set()
    if args.unir_electroterminales is not None:
        ids_unidos = {str(d) for d in (args.unir_electroterminales or parametros.ELECTROTERMINALES_UNIDOS)}
        desconocidos = ids_unidos - set(depot_ids)
        if desconocidos:
            raise SystemExit(f"--unir-electroterminales: depot_id inexistentes {sorted(desconocidos)}; "
                              f"disponibles: {depot_ids}.")
        print(f"  Terminal unido: depot_id {sorted(ids_unidos)} forman un solo grupo de interlining.")
    idx_unidos = {depot_ids.index(d) for d in ids_unidos}

    asignacion_df = pd.read_csv(args.asignacion, sep=CSV_SEP) if args.asignacion else None
    if asignacion_df is not None:
        print(f"  Asignacion de electroterminales: {args.asignacion}")

    idx_depot_fijo = calcular_asignacion_depots(ex, depots, args.modo, asignacion_df)
    grupo = construir_grupos(ex, args.modo, idx_depot_fijo, idx_unidos)
    pullout_km, pullout_idx, pullin_km, pullin_idx = costos_pullout_pullin(
        ex, depots, idx_depot_fijo, args.factor_desvio)

    print("\n--- Resolviendo flujo de costo minimo ---")
    res = resolver_flujo(ex, grupo, pullout_km, pullin_km, costos, args.radio, args.factor_desvio, args.layover)
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

    # --- Chequeo de retorno [Profesor]: cada bus termina en su electroterminal ---
    distinto = jornadas["depot_salida"] != jornadas["depot_llegada"]
    en_unidos = jornadas["depot_salida"].isin(ids_unidos) & jornadas["depot_llegada"].isin(ids_unidos)
    cruzan_patio = int((distinto & en_unidos).sum())            # sale de un patio y vuelve al otro del terminal unido
    sin_retorno = int((distinto & ~en_unidos).sum())            # viola el retorno
    if args.modo in ("ruta", "cluster"):
        assert sin_retorno == 0, (
            f"{sin_retorno} jornadas no terminan en el electroterminal donde empezaron (y no pertenecen al "
            f"mismo terminal unido): se viola el retorno [Profesor]. Revisar la asignacion.")
        print(f"  [OK] Retorno verificado: toda jornada vuelve a su electroterminal"
              + (f" ({cruzan_patio} cruzan de un patio al otro del terminal unido)." if ids_unidos else "."))
    else:
        print(f"  [LB] {sin_retorno} de {len(jornadas)} jornadas ({sin_retorno / len(jornadas):.1%}) terminan en un "
              f"electroterminal distinto al de salida: por eso LB es cota inferior y no un escenario operacional.")

    print("\n--- Guardando resultados ---")
    if not args.sin_jornadas:
        jornadas_path = DATA_PROCESSED / f"jornadas_{etiqueta}.csv"
        jornadas.to_csv(jornadas_path, index=False, sep=CSV_SEP)
        print(f"  -> {jornadas_path} ({len(jornadas)} jornadas)")
        png_path = GRAFICOS / f"jornadas_{etiqueta}.png"
        graficar_jornadas(jornadas, png_path, etiqueta, costos)
        print(f"  -> {png_path}")

    # OJO: los totales de pullout/pullin/interlining se leen de `jornadas`
    # (solo las expediciones que efectivamente son inicio/fin/enlace de una
    # jornada), NUNCA sumando pullout_km/pullin_km sobre las n expediciones
    # completas -- esos arrays traen el costo de la opcion mas barata para
    # CADA expedicion, la mayoria de las cuales no inicia ni termina ninguna
    # jornada (van "en medio" de su jornada, sin pullout/pullin propio).
    km_pullout_tot = float(jornadas["km_pullout"].sum())
    km_pullin_tot = float(jornadas["km_pullin"].sum())
    km_interlining_tot = float(jornadas["km_interlining"].sum())
    assert abs(km_interlining_tot - res["deadhead_interlining_km"]) < 1.0, (
        f"Inconsistencia: interlining sumado desde jornadas ({km_interlining_tot:.1f} km) no calza con "
        f"el reportado por el solver ({res['deadhead_interlining_km']:.1f} km).")
    deadhead_total_km = km_pullout_tot + km_interlining_tot + km_pullin_tot
    km_comercial = float(ex["distance_km"].sum())
    cost_bus = res["buses"] * costos.vehicle_fixed_cost
    cost_deadhead = deadhead_total_km * costos.cost_per_km
    cost_espera = res["espera_h"] * 60 * costos.waiting_cost_per_min
    fila = dict(
        etiqueta=etiqueta, modo=args.modo, subset=",".join(args.subset) if args.subset else "",
        asignacion=Path(args.asignacion).name if args.asignacion else "",
        unir=",".join(sorted(ids_unidos)), factor_desvio=args.factor_desvio, layover_min=args.layover,
        radio_km=args.radio, n_expediciones=len(ex), buses=res["buses"],
        km_comercial=round(km_comercial, 1), km_pullout=round(km_pullout_tot, 1),
        km_interlining=round(km_interlining_tot, 1), km_pullin=round(km_pullin_tot, 1),
        km_vacios_total=round(deadhead_total_km, 1),
        pct_km_vacios=round(deadhead_total_km / (deadhead_total_km + km_comercial) * 100, 2),
        espera_h=round(res["espera_h"], 1),
        jornadas_cruzan_patio=cruzan_patio, jornadas_sin_retorno=sin_retorno,
        cost_bus_usd=round(cost_bus, 0), cost_km_vacios_usd=round(cost_deadhead, 0),
        cost_espera_usd=round(cost_espera, 0),
        cost_operacion_usd=round(cost_bus + cost_deadhead + cost_espera, 0),
        cost_km_comerciales_usd=round(km_comercial * costos.cost_per_km, 0),
        tiempo_computo_s=round(res["t_total"], 1),
    )
    # % de jornadas cuya energia supera la bateria util de cada nivel de partida (descriptivo)
    for soc in parametros.SOC_CICLICO_BARRIDO:
        fila[f"pct_jornadas_sobre_bateria_{round(soc * 100)}"] = round(
            float((jornadas["kwh_total"] > costos.bateria_util_ciclica_kwh(soc)).mean() * 100), 1)
    destino = RESUMEN_SENSIBILIDAD_PATH if args.sin_jornadas else RESUMEN_PATH
    actualizar_resumen(fila, destino)
    print(f"  -> {destino} (fila: {etiqueta})")

    sobre = ", ".join(f"{round(s * 100)}%: {fila[f'pct_jornadas_sobre_bateria_{round(s * 100)}']:.1f}%"
                      for s in parametros.SOC_CICLICO_BARRIDO)
    print(f"\n  Resumen: {res['buses']} buses | costo de operacion ~ {fila['cost_operacion_usd']:,.0f} USD | "
          f"{fila['pct_km_vacios']:.1f}% de km vacios")
    print(f"  Jornadas cuya energia supera la bateria util segun el nivel de partida -> {sobre}")
    print("\n=== FIN ETAPA 2 ===")


if __name__ == "__main__":
    main()
