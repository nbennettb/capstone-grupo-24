"""
KPIs de la instancia - ICS2122 Capstone Buses Electricos (ver docs/context/01_como_funciona.md).

No corre ningun modelo: lee lo que dejaron el caso base (10-), la Etapa 3 (12-) y la Etapa 4 (13-) en
results/instancia_<siglas>/ y arma UNA tabla de KPIs con las mismas definiciones para todos los escenarios:

  E0       Caso base: VSP por linea + carga reactiva (ciclo al 100% con buses de reserva)
  E1       Segundo caso base: VSP con interlining + carga reactiva
  E2-FIFO  Propuesta con carga por orden de llegada: Etapa 3 + carga FIFO
  E2       Propuesta completa: Etapa 3 + Etapa 4
  (y las variantes de la holgura h de la Etapa 3 y del bloque Delta de la Etapa 4)

Definiciones (iguales para todos):
  Costo total = flota + reservas (intermedias y nocturnas) + km vacios + espera + energia + eventos de carga.
    Original: la espera como la cobra el caso base (entre viajes + en el patio de dia + cola hasta empezar a cargar
    al final del dia). Comparable: sin la espera nocturna en el patio (estacionar de noche no es un costo de operacion;
    E2 espera a proposito la tarifa barata).
  N de buses = buses operativos (tras la carga en el caso base; de la Etapa 3 en E2) + buses de reserva.
  Buses extra por bateria = N de buses - buses del VSP del mismo escenario.
  % km vacios = km sin pasajeros / km totales.  Costo medio de la energia = USD / kWh cargado; % en valle (P1 y P6).
  Uso de los puestos: uso maximo y horas con todos los puestos ocupados (por minuto).
  Utilizacion del bus = horas con pasajeros / (N de buses x 24 h).

Ademas re-verifica las validaciones leyendo los CSV (no confia en lo que imprimio cada script) y escribe
results/instancia_<siglas>/resumen_para_analisis.md, el unico archivo que se entrega para el analisis.

Output: results/instancia_<siglas>/kpis/tablas/*.csv, kpis/graficos/*.png (+ .csv de cada grafico),
        results/instancia_<siglas>/resumen_para_analisis.md

Uso:
    python scripts/14-kpis_instancia.py --terminal 4
    python scripts/14-kpis_instancia.py --terminal 4 --prueba      # lee las carpetas *_prueba
"""

import argparse
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import figuras_informe as fi, graficos as gr, instancia, nombres, parametros  # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, RESULTS_DIR   # noqa: E402

DIA_MIN = 1440
ESCENARIOS = ["E0", "E1", "E2-FIFO", "E2"]
COLUMNA_OCUPACION = {"E2-FIFO": "fifo", "E2": "e2", "E2-detallado": "e2_detallado"}
MODELO = {"E2-FIFO": "-", "E2": "agregado", "E2-detallado": "detallado"}


def leer(path, **kw):
    return pd.read_csv(path, sep=CSV_SEP, **kw) if path.exists() else None


def fmt(x, d=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x:,.{d}f}"


# --------------------------------------------------------------------------- #
# Lectura de las corridas
# --------------------------------------------------------------------------- #

class Corridas:
    """Todo lo que existe en la carpeta de la instancia."""

    def __init__(self, carpeta, sufijo):
        self.cb = carpeta / f"caso_base{sufijo}" / "tablas"
        self.e3 = {}
        for d in sorted((carpeta / f"etapa3{sufijo}").glob("h*")):
            if (d / "tablas" / "resumen.csv").exists():
                self.e3[float(d.name[1:])] = d / "tablas"
        self.e4 = {}
        for d in sorted((carpeta / f"etapa4{sufijo}").glob("h*_d*")):
            m = re.fullmatch(r"h([\d.]+)_d(\d+)", d.name)
            if m and (d / "tablas" / "resumen.csv").exists():
                self.e4[(float(m.group(1)), int(m.group(2)))] = d / "tablas"


def carpeta_detallado(t4):
    """Carpeta del modelo detallado de una corrida de la Etapa 4 (o None si no se ha corrido). Las filas de detallado que
    pudieran quedar en las tablas principales de una version anterior se ignoran."""
    d = t4.parent / "detallado"
    return d if (d / "resumen.csv").exists() and (d / "modelo.csv").exists() else None


def ocupacion_caso_base(cb, esc):
    o = leer(cb / f"ocupacion_{esc}_soc100.csv")
    return None if o is None else o["buses_cargando"].values.astype(float)


# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #

def fila_caso_base(cb, esc, costos, ex_info):
    rc = leer(cb / "resumen_carga.csv")
    if rc is None or not ((rc["escenario"] == esc) & (rc["soc_pct"] == 100)).any():
        return None
    r = rc[(rc["escenario"] == esc) & (rc["soc_pct"] == 100)].iloc[-1]
    ev = leer(cb / f"eventos_{esc}_soc100.csv")
    jor = leer(cb / f"jornadas_{esc}_soc100.csv")
    occ = ocupacion_caso_base(cb, esc)
    cola_noche_min = float(ev.loc[ev["tipo"] == "final", "espera_cola_min"].fillna(0).sum())
    exps = {e for s in jor["expedicion_ids"] for e in s.split(";")}
    km_com, h_pas = ex_info(exps)
    w = costos.waiting_cost_per_min
    c_esp = float(r["costo_espera_usd"])
    kappa = int(leer(cb / f"ocupacion_{esc}_soc100.csv")["puestos"].iloc[0])
    return dict(
        escenario=esc, variante="base", holgura_min=np.nan, delta_min=np.nan,
        buses_vsp=int(r["buses_vsp"]), buses_operativos=int(r["buses_final"]), reservas_intermedias=0,
        reservas_nocturnas=int(r["buses_reserva"]),
        costo_flota=float(r["costo_flota_usd"]), costo_reservas_intermedias=0.0,
        costo_reservas_nocturnas=float(r["costo_reservas_usd"]), costo_km_vacios=float(r["costo_km_vacios_usd"]),
        costo_espera_original=c_esp, costo_espera_comparable=c_esp - cola_noche_min * w,
        costo_energia=float(r["costo_energia_usd"]), costo_eventos=float(r["costo_eventos_usd"]),
        eventos=int(r["eventos_total"]), km_vacios=float(r["km_vacios_total"]), km_comerciales=km_com,
        horas_con_pasajeros=h_pas, kwh_cargados=float(r["kwh_cargados"]), kwh_deficit=float(r["kwh_deficit"]),
        usd_kwh=float(r["costo_medio_energia_usd_kwh"]), pct_valle=float(r["pct_energia_valle"]),
        puestos=kappa, uso_max_pct=occ.max() / kappa * 100, max_buses_minuto=float(occ.max()),
        horas_saturadas=(occ >= kappa).sum() / 60,
        minutos_sobre_puestos=int((occ > kappa).sum()),
        segundos=float(r["tiempo_computo_s"]) if "tiempo_computo_s" in r and not pd.isna(r["tiempo_computo_s"]) else np.nan)


def fila_propuesta(t3, t4, politica, h, delta, costos):
    r3 = leer(t3 / "resumen.csv").iloc[0]
    r4 = leer(t4 / "resumen.csv").set_index("politica").loc[politica]
    occ = leer(t4 / "ocupacion_minutos.csv")[COLUMNA_OCUPACION[politica]].values
    kappa = int(r4["puestos"])
    w, cb = costos.waiting_cost_per_min, costos.vehicle_fixed_cost
    esp_viajes = float(r3["espera_entre_viajes_h"]) * 60
    esp_dia, esp_noche = float(r4["espera_patio_dia_min"]), float(r4["espera_patio_noche_hasta_carga_min"])
    seg3 = float(r3["segundos_total"])
    return dict(
        escenario=politica, variante="base", holgura_min=h, delta_min=delta,
        buses_vsp=int(r3["buses_vsp"]), buses_operativos=int(r3["buses_etapa3"]),
        reservas_intermedias=int(r4["reservas_intermedias"]), reservas_nocturnas=int(r4["reservas_nocturnas"]),
        costo_flota=int(r3["buses_etapa3"]) * cb, costo_reservas_intermedias=int(r4["reservas_intermedias"]) * cb,
        costo_reservas_nocturnas=int(r4["reservas_nocturnas"]) * cb,
        costo_km_vacios=float(r3["km_vacios"]) * costos.cost_per_km,
        costo_espera_original=(esp_viajes + esp_dia + esp_noche) * w, costo_espera_comparable=(esp_viajes + esp_dia) * w,
        costo_energia=float(r4["costo_energia_usd"]), costo_eventos=float(r4["costo_eventos_usd"]),
        eventos=int(r4["eventos"]), km_vacios=float(r3["km_vacios"]), km_comerciales=float(r3["km_comerciales"]),
        horas_con_pasajeros=float(r3["horas_con_pasajeros"]), kwh_cargados=float(r4["kwh_cargados"]),
        kwh_deficit=float(r4["kwh_deficit"]), usd_kwh=float(r4["costo_medio_energia_usd_kwh"]),
        pct_valle=float(r4["pct_energia_valle"]), puestos=kappa, uso_max_pct=occ.max() / kappa * 100,
        max_buses_minuto=float(occ.max()),
        horas_saturadas=(occ >= kappa - 1e-6).sum() / 60, minutos_sobre_puestos=int((occ > kappa + 1e-6).sum()),
        segundos=seg3 + float(r4["segundos"]))


def completar(f):
    f["costo_reservas"] = f["costo_reservas_intermedias"] + f["costo_reservas_nocturnas"]
    comunes = (f["costo_flota"] + f["costo_reservas"] + f["costo_km_vacios"] + f["costo_energia"] + f["costo_eventos"])
    f["costo_total_original"] = comunes + f["costo_espera_original"]
    f["costo_total_comparable"] = comunes + f["costo_espera_comparable"]
    f["reservas"] = f["reservas_intermedias"] + f["reservas_nocturnas"]
    f["buses_totales"] = f["buses_operativos"] + f["reservas"]
    f["buses_extra_bateria"] = f["buses_totales"] - f["buses_vsp"]
    f["pct_km_vacios"] = f["km_vacios"] / (f["km_vacios"] + f["km_comerciales"]) * 100
    f["utilizacion_bus_pct"] = f["horas_con_pasajeros"] / (f["buses_totales"] * 24) * 100
    return f


# --------------------------------------------------------------------------- #
# Validaciones (re-verificadas desde los CSV)
# --------------------------------------------------------------------------- #

def max_intervalos(salidas, listos):
    ev = sorted([(t, 0) for t in listos] + [(t, 1) for t in salidas])
    act = pico = 0
    for _, tipo in ev:
        act += 1 if tipo else -1
        pico = max(pico, act)
    return pico


def validaciones(corr, nombre, patios, prueba, costos):
    filas = []

    def anotar(que, ok, detalle):
        filas.append(dict(validacion=que, resultado="OK" if ok else "FALLA", detalle=detalle))

    red = RESULTS_DIR / "caso_base" / "tablas"
    for esc in ("E0", "E1"):
        j = leer(corr.cb / f"jornadas_{esc}_soc100.csv", dtype={"jornada_id": str})
        if j is None:
            filas.append(dict(validacion=f"{nombres.ESCENARIO[esc]}: igual a la red completa filtrada", resultado="NO CORRIDO",
                              detalle="falta correr 10-"))
            continue
        rj = leer(red / f"jornadas_{esc}_soc100.csv", dtype={"jornada_id": str})
        if prueba or rj is None:
            filas.append(dict(validacion=f"{nombres.ESCENARIO[esc]}: igual a la red completa filtrada", resultado="NO APLICA",
                              detalle="prueba chica" if prueba else "no existe la corrida de la red completa"))
        else:
            rj = rj[rj["terminal"] == nombre]
            ok = (len(rj) == len(j) and int((~rj["ciclo_cumplido"]).sum()) == int((~j["ciclo_cumplido"]).sum())
                  and set(rj["jornada_id"]) == set(j["jornada_id"]))
            anotar(f"{nombres.ESCENARIO[esc]}: igual a la red completa filtrada", ok,
                   f"{len(j):,} jornadas finales y {int((~j['ciclo_cumplido']).sum()):,} reservas "
                   f"(red completa filtrada: {len(rj):,} y {int((~rj['ciclo_cumplido']).sum()):,})")
        anotar(f"{nombres.ESCENARIO[esc]}: deficit de energia 0", float(j["kwh_deficit"].sum()) < 1e-3,
               f"{j['kwh_deficit'].sum():.3f} kWh")

    jv = pd.read_csv(DATA_PROCESSED / "jornadas_E1.csv", sep=CSV_SEP, dtype={"depot_salida": str, "depot_llegada": str})
    jv = instancia.filtrar_jornadas(jv, patios)
    util = costos.bateria_util_ciclica_kwh(1.0)
    for h, t3 in corr.e3.items():
        tr = leer(t3 / "tramos.csv", dtype={"jornada_vsp": str})
        r3 = leer(t3 / "resumen.csv").iloc[0]
        base = jv[jv["bus_id"].astype(str).isin(set(tr["jornada_vsp"]))] if prueba else jv
        esperadas = [e for s in base["expedicion_ids"] for e in s.split(";")]
        cubiertas = [e for s in tr["expedicion_ids"] for e in s.split(";")]
        anotar(f"Etapa 3 (h={h:g}): cobertura exacta", sorted(esperadas) == sorted(cubiertas),
               f"{len(cubiertas):,} expediciones en {len(tr):,} tramos")
        anotar(f"Etapa 3 (h={h:g}): todo tramo cabe en la bateria util", bool((tr["kwh"] <= util + 1e-6).all()),
               f"maximo {tr['kwh'].max():.1f} kWh de {util:.0f}")
        fi = max_intervalos(tr["salida_patio_min"].values, tr["listo_min"].values)
        anotar(f"Etapa 3 (h={h:g}): flota = maximo de intervalos superpuestos", fi == int(r3["buses_etapa3"]),
               f"flujo {int(r3['buses_etapa3']):,}, intervalos {fi:,}")
    for (h, d), t4 in corr.e4.items():
        r4 = leer(t4 / "resumen.csv").set_index("politica")
        ob = leer(t4 / "ocupacion_bloques.csv")
        om = leer(t4 / "ocupacion_minutos.csv")
        mo = leer(t4 / "modelo.csv").set_index("modelo")
        k = int(ob["puestos"].iloc[0])
        anotar(f"Etapa 4 (h={h:g}, Delta={d}): deficit 0", float(r4["kwh_deficit"].sum()) < 1e-3,
               f"orden de llegada {r4.loc['E2-FIFO', 'kwh_deficit']:.3f} kWh, modelo agregado {r4.loc['E2', 'kwh_deficit']:.3f} kWh")
        anotar(f"Etapa 4 (h={h:g}, Delta={d}): ocupacion <= {k} por bloque (modelo agregado) y por minuto (orden de llegada)",
               bool((ob["buses_equivalentes_e2"] <= k + 1e-6).all() and (om["fifo"] <= k).all()),
               f"maximo del modelo agregado por bloque {ob['buses_equivalentes_e2'].max():.2f}; orden de llegada por minuto "
               f"{om['fifo'].max():.0f}; ejecucion minuto a minuto del modelo agregado: {int((om['e2'] > k + 1e-6).sum())} min "
               f"sobre {k} (informativo)")
        o2, of = mo.loc["E2 agregado - MILP", "objetivo_usd"], mo.loc["E2-FIFO", "objetivo_usd"]
        anotar(f"Etapa 4 (h={h:g}, Delta={d}): modelo agregado <= orden de llegada (energia + reservas)", o2 <= of + 0.01,
               f"{fmt(o2, 2)} <= {fmt(of, 2)} USD")
        det_dir = carpeta_detallado(t4)
        if det_dir is not None:
            md = leer(det_dir / "modelo.csv").set_index("modelo").loc["E2 detallado - MILP"]
            rd = leer(det_dir / "resumen.csv").iloc[0]
            obd, omd = leer(det_dir / "ocupacion_bloques.csv"), leer(det_dir / "ocupacion_minutos.csv")
            od = float(md["objetivo_usd"])
            of_ev = of + r4.loc["E2-FIFO", "costo_eventos_usd"]
            anotar(f"Etapa 4 (h={h:g}, Delta={d}): modelo detallado, deficit 0", float(rd["kwh_deficit"]) < 1e-3,
                   f"{rd['kwh_deficit']:.3f} kWh")
            supera = od <= of_ev + 0.01
            filas.append(dict(validacion=f"Etapa 4 (h={h:g}, Delta={d}): modelo detallado <= orden de llegada (energia + reservas + eventos)",
                              resultado="OK" if supera else "AVISO",
                              detalle=f"{fmt(od, 2)} <= {fmt(of_ev, 2)} USD" if supera else
                              f"{fmt(od, 2)} > {fmt(of_ev, 2)} USD: el detallado no supero a la FIFO en el tiempo dado"))
            anotar(f"Etapa 4 (h={h:g}, Delta={d}): modelo detallado, ocupacion <= {k} por bloque",
                   bool((obd["buses_equivalentes_e2_detallado"] <= k + 1e-6).all()),
                   f"maximo por bloque {obd['buses_equivalentes_e2_detallado'].max():.2f}; ejecucion minuto a minuto: "
                   f"{int((omd['e2_detallado'] > k + 1e-6).sum())} min sobre {k} (informativo)")
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terminal", default=parametros.TERMINAL_INSTANCIA, help="depot_id del electroterminal.")
    parser.add_argument("--prueba", action="store_true", help="Lee las carpetas *_prueba (pruebas chicas).")
    args = parser.parse_args()
    sufijo = "_prueba" if args.prueba else ""

    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    costos = parametros.cargar_costos()
    patios = instancia.patios_terminal(depots, args.terminal)
    nombre = instancia.nombre_terminal(depots, patios)
    carpeta = instancia.carpeta_instancia(depots, args.terminal)
    tablas = carpeta / f"kpis{sufijo}" / "tablas"
    for d in (tablas,):
        d.mkdir(parents=True, exist_ok=True)
    corr = Corridas(carpeta, sufijo)
    h0, d0 = float(parametros.HOLGURAS_RECARGA_MIN[0]), parametros.DELTA_MIN
    print(f"=== KPIs de la instancia {nombre}{' (PRUEBA)' if args.prueba else ''} ===\n")
    print(f"  Etapa 3 corrida con holgura: {sorted(corr.e3)} | Etapa 4 con (holgura, Delta): {sorted(corr.e4)}")

    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    ex_km = dict(zip(ex["expedicion_id"], ex["distance_km"]))
    ex_dur = dict(zip(ex["expedicion_id"], ex["arr_min"] - ex["dep_min"]))

    def ex_info(ids):
        return float(sum(ex_km[e] for e in ids)), float(sum(ex_dur[e] for e in ids)) / 60

    # --- tabla de KPIs ---
    filas = []
    for esc in ("E0", "E1"):
        f = fila_caso_base(corr.cb, esc, costos, ex_info)
        if f is None:
            print(f"  [aviso] Falta el caso base {esc} (correr 10- con --terminal).")
        else:
            filas.append(f)
    for (h, d), t4 in sorted(corr.e4.items()):
        if h not in corr.e3:
            continue
        det_dir = carpeta_detallado(t4)
        for pol in ("E2-FIFO", "E2") + (("E2-detallado",) if det_dir is not None else ()):
            if pol == "E2-FIFO" and d != d0:
                continue                      # la FIFO es al minuto: no depende de Delta
            f = fila_propuesta(corr.e3[h], det_dir if pol == "E2-detallado" else t4, pol, h, d, costos)
            if pol == "E2-detallado":
                f["escenario"], f["variante"] = "E2", f"modelo detallado, h={h:g}, Delta={d}"
            else:
                f["variante"] = "base" if (h == h0 and d == d0) else (f"h={h:g}" if d == d0 else f"Delta={d}")
            f["modelo"] = MODELO[pol]
            filas.append(f)
    assert filas, "No hay ninguna corrida que resumir en " + str(carpeta)
    k = completar(pd.DataFrame(filas))
    k["modelo"] = k["modelo"].fillna("-")
    # La Propuesta completa de la tabla principal y de las figuras es el modelo detallado con el largo del bloque base;
    # el agregado queda como variante (validacion y sensibilidades).
    det_base = (k["escenario"] == "E2") & (k["modelo"] == "detallado") & (k["holgura_min"] == h0) & (k["delta_min"] == d0)
    if det_base.any():
        k.loc[(k["escenario"] == "E2") & (k["modelo"] == "agregado") & (k["variante"] == "base"), "variante"] = \
            "modelo agregado"
        k.loc[det_base, "variante"] = "base"
    det_dir_base = carpeta_detallado(corr.e4[(h0, d0)]) if (h0, d0) in corr.e4 and det_base.any() else None
    nombres.presentar(k.round(4)).to_csv(tablas / "kpis_escenarios.csv", index=False, sep=CSV_SEP)
    kb = k[k["variante"] == "base"].set_index("escenario").reindex([e for e in ESCENARIOS if e in set(k["escenario"])]) \
        .reset_index()

    # --- validaciones ---
    val = validaciones(corr, nombre, patios, args.prueba, costos)
    val = nombres.presentar(val)
    val.to_csv(tablas / "validaciones.csv", index=False, sep=CSV_SEP)

    # --- tablas de detalle ---
    tarifa = None
    precios = pd.read_csv(DATA_FILTRADO / "electricity_prices.csv", sep=CSV_SEP)
    tarifa = np.zeros(DIA_MIN)
    for r in precios.itertuples():
        tarifa[int(r.start_hour) * 60:int(r.end_hour) * 60] = r.price_usd_kwh
    tab_tarifa = pd.DataFrame({"tramo horario": [nombres.tramo_horario(a, b) for a, b in
                                                 zip(precios["start_hour"], precios["end_hour"])],
                               "precio_usd_kwh": precios["price_usd_kwh"].values})
    for esc in ("E0", "E1"):
        em = leer(corr.cb / f"energia_minuto_{esc}_soc100.csv")
        if em is not None:
            e = em["kwh"].values
            tab_tarifa[f"kWh {nombres.ESCENARIO[esc]}"] = [e[int(a) * 60:int(b) * 60].sum()
                                                          for a, b in zip(precios["start_hour"], precios["end_hour"])]
    base4 = corr.e4.get((h0, d0))
    if base4 is not None:
        et = leer(base4 / "energia_por_tarifa.csv")
        tab_tarifa[f"kWh {nombres.ESCENARIO['E2-FIFO']}"] = et["kwh_fifo"].values
        tab_tarifa[f"kWh {nombres.ESCENARIO['E2']}"] = (leer(det_dir_base / "energia_por_tarifa.csv")["kwh"].values
                                                        if det_dir_base is not None else et["kwh_e2"].values)
    for c in [c for c in tab_tarifa if c.startswith("kWh ")]:
        tab_tarifa[c.replace("kWh ", "USD ")] = tab_tarifa[c] * tab_tarifa["precio_usd_kwh"]
    tab_tarifa.round(2).to_csv(tablas / "energia_por_tarifa.csv", index=False, sep=CSV_SEP)

    series = {}
    for esc in ("E0", "E1"):
        o = ocupacion_caso_base(corr.cb, esc)
        if o is not None:
            series[esc] = o
    if base4 is not None:
        om = leer(base4 / "ocupacion_minutos.csv")
        series["E2-FIFO"] = om["fifo"].values
        series["E2"] = (leer(det_dir_base / "ocupacion_minutos.csv")["e2_detallado"].values
                        if det_dir_base is not None else om["e2"].values)
    kappa = int(kb["puestos"].iloc[0])
    ocup_h = pd.DataFrame({"hora": range(24)})
    for esc, s in series.items():
        ocup_h[f"{nombres.CORTO[esc]} (promedio)"] = s.reshape(24, 60).mean(axis=1).round(1)
        ocup_h[f"{nombres.CORTO[esc]} (maximo)"] = s.reshape(24, 60).max(axis=1).round(1)
    ocup_h.to_csv(tablas / "ocupacion_por_hora.csv", index=False, sep=CSV_SEP)

    diag = None
    if h0 in corr.e3:
        diag = leer(corr.e3[h0] / "diagnostico_flota.csv")
        diag_h = pd.DataFrame([dict(holgura_min=h, **dict(zip(leer(t / "diagnostico_flota.csv")["paso"],
                                                               leer(t / "diagnostico_flota.csv")["buses"])))
                               for h, t in sorted(corr.e3.items())])
        diag_h = nombres.presentar(diag_h)
        diag_h.columns = [nombres.renombrar_texto(c) for c in diag_h.columns]
        diag_h.to_csv(tablas / "diagnostico_flota_por_holgura.csv", index=False, sep=CSV_SEP)

    sens_h = []
    for h, t3 in sorted(corr.e3.items()):
        if (h, d0) not in corr.e4:
            continue
        r3 = leer(t3 / "resumen.csv").iloc[0]
        e2 = k[(k["escenario"] == "E2") & (k["modelo"] == "agregado") & (k["holgura_min"] == h)
               & (k["delta_min"] == d0)].iloc[0]
        ff = k[(k["escenario"] == "E2-FIFO") & (k["holgura_min"] == h)].iloc[0]
        sens_h.append(dict(holgura_min=h, buses_etapa3=int(r3["buses_etapa3"]), reservas_FIFO=int(ff["reservas"]),
                           reservas_E2=int(e2["reservas"]), buses_totales_FIFO=int(ff["buses_totales"]),
                           buses_totales_E2=int(e2["buses_totales"]),
                           costo_total_comparable_E2=round(e2["costo_total_comparable"], 0),
                           costo_energia_E2=round(e2["costo_energia"], 0),
                           nocturnas_sin_tiempo_carga=int(r3["nocturnas_sin_tiempo_carga"])))
    sens_h = pd.DataFrame(sens_h)
    sens_d = []
    for (h, d), t4 in sorted(corr.e4.items()):
        if h != h0:
            continue
        mo = leer(t4 / "modelo.csv").set_index("modelo")
        e2 = k[(k["escenario"] == "E2") & (k["modelo"] == "agregado") & (k["holgura_min"] == h)
               & (k["delta_min"] == d)].iloc[0]
        sens_d.append(dict(delta_min=d, objetivo_usd=mo.loc["E2 agregado - MILP", "objetivo_usd"],
                           cota_lp_usd=mo.loc["E2 agregado - LP (cota)", "objetivo_usd"], reservas=int(e2["reservas"]),
                           costo_energia=round(e2["costo_energia"], 2), eventos=int(e2["eventos"]),
                           minutos_sobre_puestos=int(e2["minutos_sobre_puestos"]),
                           variables=int(mo.loc["E2 agregado - MILP", "variables"]),
                           segundos_lp=float(mo.loc["E2 agregado - LP (cota)", "segundos"]),
                           segundos_milp=float(mo.loc["E2 agregado - MILP", "segundos"]),
                           brecha=float(mo.loc["E2 agregado - MILP", "brecha"]),
                           estado=mo.loc["E2 agregado - MILP", "estado"]))
    sens_d = pd.DataFrame(sens_d)
    nombres.presentar(sens_h).to_csv(tablas / "sensibilidad_holgura.csv", index=False, sep=CSV_SEP)
    nombres.presentar(sens_d).to_csv(tablas / "sensibilidad_delta.csv", index=False, sep=CSV_SEP)

    modelos = []
    for esc in ("E0", "E1"):
        f = k[k["escenario"] == esc]
        if len(f):
            modelos.append(dict(corrida=f"{nombres.ESCENARIO[esc]} (simulador reactivo)", estado="-", brecha="-",
                                fuente_brecha="-", segundos=f["segundos"].iloc[0]))
    for h, t3 in sorted(corr.e3.items()):
        r3 = leer(t3 / "resumen.csv").iloc[0]
        modelos.append(dict(corrida=f"Etapa 3 (h={h:g}) (DP + flujo)", estado="optimo (flujo entero)", brecha=0,
                            fuente_brecha="flujo entero", segundos=float(r3["segundos_total"])))
    for (h, d), t4 in sorted(corr.e4.items()):
        mo = leer(t4 / "modelo.csv").set_index("modelo")
        mo = mo[~mo.index.str.startswith("E2 detallado")]
        det_dir = carpeta_detallado(t4)
        if det_dir is not None:
            mo = pd.concat([mo, leer(det_dir / "modelo.csv").set_index("modelo")])
        for nombre_mo, r in mo.iterrows():
            fuente = r["fuente_brecha"] if "fuente_brecha" in r and isinstance(r["fuente_brecha"], str) else (
                "Gurobi" if r["brecha"] == r["brecha"] else "-")
            modelos.append(dict(corrida=f"Etapa 4 (h={h:g}, Delta={d}): {nombre_mo}", estado=r["estado"],
                                brecha=r["brecha"], fuente_brecha=fuente, segundos=r["segundos"]))
    modelos = nombres.presentar(pd.DataFrame(modelos))
    modelos.to_csv(tablas / "tiempos_y_brechas.csv", index=False, sep=CSV_SEP)
    det = detallado_vs_agregado(corr)
    if det is not None:
        nombres.presentar(det).to_csv(tablas / "detallado_vs_agregado.csv", index=False, sep=CSV_SEP)

    figuras = []
    extras = []
    if not args.prueba:
        figuras = figuras_del_informe(carpeta / "informe", corr, kb, series, kappa, tarifa, sens_h, sens_d, h0,
                                      det_dir_base)
        extras = seccion_figuras(figuras) + seccion_herramientas()

    # --- resumen para el analisis ---
    md = resumen_md(nombre, kappa, args.prueba, costos, corr, k, kb, val, diag, tab_tarifa, ocup_h, sens_h, sens_d,
                    modelos, det, figuras, carpeta, sufijo, extras)
    path_md = carpeta / f"resumen_para_analisis{sufijo}.md"
    path_md.write_text(nombres.renombrar_texto(md), encoding="utf-8")

    print("\n--- Validaciones ---")
    for r in val.itertuples():
        print(f"  [{r.resultado}] {r.validacion}: {r.detalle}")
    print("\n--- KPIs (escenarios base) ---")
    cols = ["costo_total_original", "costo_total_comparable", "buses_vsp", "buses_operativos", "reservas",
            "buses_totales", "buses_extra_bateria", "pct_km_vacios", "usd_kwh", "pct_valle", "uso_max_pct",
            "horas_saturadas"]
    print(kb.set_index("escenario")[cols].T.round(2).to_string())
    print(f"\n  -> {tablas}\n  -> {carpeta / 'informe'}\n  -> {path_md}")
    fallas = (val["resultado"] == "FALLA").sum()
    print(f"\n  {'TODAS LAS VALIDACIONES OK' if fallas == 0 else f'{fallas} VALIDACIONES FALLAN: revisar antes de analizar'}")
    print("\n=== FIN KPIs ===")


def tabla_md(df, **kw):
    return df.to_markdown(index=False, **kw)


def detallado_vs_agregado(corr):
    """Una fila por modelo (agregado y detallado) en cada corrida de la Etapa 4 que tenga el detallado."""
    filas = []
    for (h, d), t4 in sorted(corr.e4.items()):
        det_dir = carpeta_detallado(t4)
        if det_dir is None:
            continue
        fuentes = {"agregado": (leer(t4 / "modelo.csv").set_index("modelo").loc["E2 agregado - MILP"],
                                leer(t4 / "resumen.csv").set_index("politica").loc["E2"],
                                leer(t4 / "ocupacion_minutos.csv"), "e2"),
                   "detallado": (leer(det_dir / "modelo.csv").set_index("modelo").loc["E2 detallado - MILP"],
                                 leer(det_dir / "resumen.csv").set_index("politica").loc["E2-detallado"],
                                 leer(det_dir / "ocupacion_minutos.csv"), "e2_detallado")}
        for nombre, (m, r, om, col) in fuentes.items():
            k = int(om["puestos"].iloc[0])
            eventos_usd = float(r["costo_eventos_usd"])
            # el objetivo del detallado incluye los eventos; el del agregado no
            energia_reservas = float(m["objetivo_usd"]) - (float(m["eventos_usd"]) if nombre == "detallado" else 0.0)
            brecha, fuente = float(m["brecha"]), (m["fuente_brecha"] if nombre == "detallado" else "Gurobi")
            filas.append(dict(holgura_min=h, delta_min=d, modelo=nombre, estado=m["estado"], brecha=round(brecha, 6),
                              fuente_brecha=fuente, segundos=m["segundos"], binarias=int(m["binarias"]),
                              variables=int(m["variables"]),
                              energia_mas_reservas_usd=round(energia_reservas, 2), eventos=int(r["eventos"]),
                              costo_eventos_usd=round(eventos_usd, 2),
                              total_carga_usd=round(energia_reservas + eventos_usd, 2),
                              reservas_intermedias=int(r["reservas_intermedias"]),
                              reservas_nocturnas=int(r["reservas_nocturnas"]),
                              costo_energia_usd=round(float(r["costo_energia_usd"]), 2),
                              minutos_sobre_puestos=int((om[col] > k + 1e-6).sum()),
                              maximo_por_minuto=round(float(om[col].max()), 2)))
    return pd.DataFrame(filas) if filas else None


def tabla_detallado(det):
    """La comparacion en una sola tabla (USD/dia)."""
    t = pd.DataFrame({
        "largo del bloque (min)": det["delta_min"].astype(int), "modelo": det["modelo"],
        "reservas": det["reservas_intermedias"] + det["reservas_nocturnas"], "eventos": det["eventos"],
        "energia + reservas (USD)": det["energia_mas_reservas_usd"].map(lambda x: fmt(x)),
        "total carga = + eventos (USD)": det["total_carga_usd"].map(lambda x: fmt(x)),
        "minutos sobre los puestos": det["minutos_sobre_puestos"], "segundos": det["segundos"].map(lambda x: fmt(x)),
        "brecha": det["brecha"].map(lambda x: f"{x:.2%}"), "fuente de la brecha": det["fuente_brecha"]})
    return tabla_md(t)


def conclusion_detallado(det):
    """Una frase con la comparacion del Delta base (o el primero disponible)."""
    d0 = parametros.DELTA_MIN if (det["delta_min"] == parametros.DELTA_MIN).any() else det["delta_min"].iloc[0]
    a = det[(det["delta_min"] == d0) & (det["modelo"] == "agregado")].iloc[0]
    b = det[(det["delta_min"] == d0) & (det["modelo"] == "detallado")].iloc[0]
    res = lambda f: int(f["reservas_intermedias"] + f["reservas_nocturnas"])
    return (f"**Conclusion:** con bloques de {int(d0)} min, la programacion del modelo detallado cuesta {fmt(b['total_carga_usd'])} "
            f"USD/dia contra {fmt(a['total_carga_usd'])} del modelo agregado con sus eventos contados despues "
            f"({(b['total_carga_usd'] / a['total_carga_usd'] - 1) * 100:+.1f}%), con {res(b)} reservas contra {res(a)} y "
            f"{fmt(b['eventos'])} eventos contra {fmt(a['eventos'])}; el modelo agregado se resuelve en {fmt(a['segundos'])} s "
            f"y el modelo detallado en {fmt(b['segundos'])} s, con brecha {b['brecha']:.2%}.")


def figuras_del_informe(destino, corr, kb, series, kappa, tarifa, sens_h, sens_d, h0, det_dir):
    """Figuras finales del informe (F0-F6) en destino/: PDF, PNG y CSV. Devuelve (archivo, caption, cifra)."""
    fi.estilo()
    figuras = []
    rc = leer(RESULTS_DIR / "caso_base" / "tablas" / "resumen_carga.csv")
    if rc is not None:
        figuras.append(fi.f0_caso_base_red(rc[(rc["soc_pct"] == 100) & rc["escenario"].isin(["E0", "E1"])], destino))
    figuras.append(fi.f1_metodologia(destino))
    if det_dir is not None and h0 in corr.e3:
        cb_j = leer(corr.cb / "jornadas_E1_soc100.csv", dtype={"jornada_id": str, "bus_origen": str})
        cb_ev = leer(corr.cb / "eventos_E1_soc100.csv", dtype={"jornada_id": str})
        tramos = leer(corr.e3[h0] / "tramos.csv", dtype={"jornada_vsp": str, "tramo_id": str})
        prog = leer(det_dir / "programa_E2_detallado.csv", dtype={"tramo_id": str})
        figuras.append(fi.f2_gantt(cb_j, cb_ev, tramos, prog, destino))
    figuras.append(fi.f3_escalera(kb, destino))
    figuras.append(fi.f4_costo(kb, destino))
    figuras.append(fi.f5_ocupacion(series, kappa, tarifa, destino))
    if len(sens_h) > 1 and len(sens_d) > 1:
        figuras.append(fi.f6_sensibilidades(sens_h, sens_d, destino))
    return figuras


def seccion_figuras(figuras):
    lineas = ["## Figuras del informe", "",
              "En `informe/`, cada una en PDF (vectorial, para LaTeX), PNG y CSV con sus datos. Ancho pensado para "
              "0.8 del ancho de texto de LaTeX, letra de 9 pt, sin titulo en la imagen (va en el caption).", "",
              "| Figura | Caption propuesto | Cifra principal que respalda |", "|---|---|---|"]
    lineas += [f"| `{f}.pdf` | {c} | {n} |" for f, c, n in figuras]
    return lineas + [""]


def seccion_herramientas():
    """Versiones de las herramientas y equipo, leidas del entorno en que se corre este script."""
    import platform
    import gurobipy
    import scipy
    import psutil
    cpu = platform.processor()
    try:
        import winreg
        clave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        cpu = winreg.QueryValueEx(clave, "ProcessorNameString")[0].strip()
    except (ImportError, OSError):
        pass
    g = ".".join(str(x) for x in gurobipy.gurobi.version())
    return ["## Herramientas y equipo", "",
            f"- Python {platform.python_version()}; Gurobi {g} (gurobipy, licencia academica); scipy {scipy.__version__} "
            f"(HiGHS); pandas {pd.__version__}; numpy {np.__version__}; matplotlib {matplotlib.__version__}.",
            f"- Equipo: {cpu}, {psutil.cpu_count(logical=False)} nucleos y {psutil.cpu_count()} hilos; "
            f"{sistema_operativo()}.", ""]


def sistema_operativo():
    """Nombre del sistema operativo. En Windows 11, platform.release() dice "10": se distingue por la compilacion."""
    import platform
    if platform.system() == "Windows":
        compilacion = int(platform.version().split(".")[-1])
        return f"Windows {11 if compilacion >= 22000 else platform.release()}"
    return f"{platform.system()} {platform.release()}"


def resumen_md(nombre, kappa, prueba, costos, corr, k, kb, val, diag, tab_tarifa, ocup_h, sens_h, sens_d, modelos,
               det, figuras, carpeta, sufijo, extras=()):
    h0, d0 = parametros.HOLGURAS_RECARGA_MIN[0], parametros.DELTA_MIN
    N = nombres.ESCENARIO
    n_jor = {e: int(kb.loc[kb["escenario"] == e, "buses_vsp"].iloc[0]) for e in ("E0", "E1") if e in set(kb["escenario"])}
    t3b = corr.e3.get(float(h0))
    r3 = leer(t3b / "resumen.csv").iloc[0] if t3b is not None else None
    t4b = corr.e4.get((float(h0), d0))
    r4 = leer(t4b / "resumen.csv").iloc[0] if t4b is not None else None
    modelo_e2 = kb.loc[kb["escenario"] == "E2", "modelo"].iloc[0] if (kb["escenario"] == "E2").any() else "-"

    # tabla principal: KPIs en filas, escenarios en columnas
    defs = [
        ("1. Costo total (USD/dia)", "costo_total_comparable", 0),
        ("1. Costo total con espera nocturna (USD/dia)", "costo_total_original", 0),
        ("· flota", "costo_flota", 0), ("· reservas diurnas", "costo_reservas_intermedias", 0),
        ("· reservas nocturnas", "costo_reservas_nocturnas", 0), ("· km vacios", "costo_km_vacios", 0),
        ("· espera", "costo_espera_comparable", 0), ("· espera, con la espera nocturna", "costo_espera_original", 0),
        ("· energia", "costo_energia", 0), ("· eventos de carga", "costo_eventos", 0),
        ("2. N de buses (operativos + reservas)", "buses_totales", 0),
        ("· buses de las jornadas sin bateria", "buses_vsp", 0),
        ("· buses operativos (tras la carga en los casos base; de la Etapa 3 en las propuestas)", "buses_operativos", 0),
        ("3. % km de deadheading", "pct_km_vacios", 2), ("4. Costo medio de la energia (USD/kWh)", "usd_kwh", 4),
        ("4. % de la energia en valle", "pct_valle", 1), ("5. Buses extra por bateria", "buses_extra_bateria", 0),
        ("6. Reservas diurnas", "reservas_intermedias", 0), ("6. Reservas nocturnas", "reservas_nocturnas", 0),
        ("7. Uso maximo de los puestos (%)", "uso_max_pct", 1),
        ("· maximo de buses cargando a la vez (minuto a minuto)", "max_buses_minuto", 1),
        ("7. Horas con todos los puestos ocupados", "horas_saturadas", 1),
        ("· minutos sobre los puestos", "minutos_sobre_puestos", 0),
        ("8. Segundos de computo (sin la Etapa 2)", "segundos", 1),
        ("· energia cargada (MWh)", "kwh_cargados", 1), ("· deficit de energia (kWh)", "kwh_deficit", 2),
        ("· eventos de carga", "eventos", 0), ("· utilizacion del bus (% de 24 h con pasajeros)", "utilizacion_bus_pct", 1),
    ]
    defs = [x for x in defs if x[1] in kb.columns]
    filas = []
    for et, c, d in defs:
        fila = {"KPI": et}
        for e in kb["escenario"]:
            v = kb.loc[kb["escenario"] == e, c].iloc[0]
            fila[N[e]] = fmt(v / 1000 if c == "kwh_cargados" else v, d)
        filas.append(fila)
    tabla_kpi = pd.DataFrame(filas)

    variantes = k[k["variante"] != "base"][["escenario", "variante", "modelo", "buses_operativos", "reservas_intermedias",
                                            "reservas_nocturnas", "buses_totales", "costo_energia", "costo_eventos",
                                            "costo_total_comparable", "costo_total_original"]].round(0)
    reservas = kb[["escenario", "reservas_intermedias", "reservas_nocturnas", "reservas"]]
    diag_p = None
    if diag is not None:
        diag_p = nombres.presentar(diag)
    texto_e2 = {"detallado": "modelo detallado", "agregado": "modelo agregado"}.get(modelo_e2, modelo_e2)
    lineas = [
        f"# Resumen para analisis: instancia {nombre}" + (" (PRUEBA CHICA: no son resultados)" if prueba else ""),
        "",
        "Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de "
        f"`{carpeta.relative_to(RESULTS_DIR.parent).as_posix()}/`. Escenarios: **{N['E0']}** (jornadas por linea + carga "
        f"reactiva); **{N['E1']}** (lo mismo, con interlining en las jornadas); **{N['E2-FIFO']}** (Etapa 3 + carga por "
        f"orden de llegada); **{N['E2']}** (Etapa 3 + Etapa 4, {texto_e2} con bloques de {d0} min). Cada escalon cambia "
        "una sola cosa.",
        "",
        "## 1. Instancia y parametros",
        "",
        f"- Electroterminal **{nombre}** completo: {kappa} puestos de carga; jornadas sin bateria (Etapa 2): "
        + ", ".join(f"{N[e]} {fmt(n)}" for e, n in n_jor.items())
        + (f"; {fmt(r3['jornadas_vsp'])} jornadas del {N['E1']} de entrada a la Etapa 3" if r3 is not None else "") + ".",
        f"- Energia a reponer en las propuestas / capacidad de 24 h de los puestos: "
        f"{fmt(r4['energia_sobre_capacidad_pct'], 1) if r4 is not None else '-'}%.",
        f"- Bateria util entre cargas {costos.bateria_util_ciclica_kwh(1.0):.0f} kWh (ciclo al 100%, minimo "
        f"{costos.min_soc:.0%}); carga a {costos.charge_power_kw:.0f} kW; consumo {parametros.CONSUMO_KWH_KM} kWh/km.",
        f"- Costos: bus {costos.vehicle_fixed_cost:.0f} USD/dia (igual para una reserva), km vacio {costos.cost_per_km} USD, "
        f"espera {costos.waiting_cost_per_min} USD/min, evento de carga {costos.fixed_charge_cost:.0f} USD.",
        "- Tarifa (USD/kWh): " + ", ".join(f"{t} = {p:.2f}" for t, p in zip(tab_tarifa["tramo horario"],
                                                                         tab_tarifa["precio_usd_kwh"])) + ".",
        f"- Deadhead: euclidiana x {parametros.FACTOR_DESVIO} a {parametros.VELOCIDAD_KMH:.0f} km/h; layover "
        f"{parametros.LAYOVER_MIN:.0f} min.",
        f"- Etapa 3: regla de corte {parametros.REGLA_CORTE} (minimos tramos, luego minimos km extra); holgura de recarga "
        f"base {h0} min; sensibilidad {parametros.HOLGURAS_RECARGA_MIN} min.",
        f"- Etapa 4: largo del bloque base {d0} min (sensibilidad {parametros.DELTAS_SENSIBILIDAD} min); Gurobi, brecha "
        f"{parametros.GAP_MIP:.1%}, limite {parametros.TIEMPO_LIMITE_S['agregado']} s el modelo agregado y "
        f"{parametros.TIEMPO_LIMITE_S['detallado']} s el detallado; deficit penalizado con "
        f"{parametros.PENALIZACION_DEFICIT_USD_KWH:,.0f} USD/kWh; desempate {parametros.DESEMPATE_USD_KWH_BLOQUE} "
        "USD/kWh por bloque desde la llegada.",
        "",
        "## 2. Validaciones (re-verificadas desde los CSV)",
        "",
        tabla_md(val),
        "",
        "## 3. KPIs por escenario",
        "",
        f"Costo total = sin la espera nocturna en el patio (la metrica principal). Costo total con espera nocturna = la "
        f"espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). En los casos base todas "
        f"las reservas son nocturnas: si una carga diurna no alcanza, la jornada se parte y el bus nuevo queda en "
        f"'operativos'. La {N['E2']} es el {texto_e2} con bloques de {d0} min.",
        "",
        tabla_md(tabla_kpi),
        "",
        "### Variantes (sensibilidad y modelo agregado)",
        "",
        tabla_md(nombres.presentar(variantes)) if len(variantes) else "Sin variantes corridas.",
        "",
        "## 4. Diagnostico de flota de la Etapa 3",
        "",
        tabla_md(diag_p) if diag_p is not None else "Etapa 3 no corrida.",
        "",
    ]
    if r3 is not None:
        lineas += [
            f"- {fmt(r3['tramos'])} tramos desde {fmt(r3['jornadas_vsp'])} jornadas ({fmt(r3['jornadas_cortadas'])} cortadas; "
            f"{fmt(r3['km_extra_cortes'], 1)} km extra). Ventanas de carga: {fmt(r3['ventanas_intermedias'])} diurnas "
            f"(entre tramos), {fmt(r3['ventanas_nocturnas'])} nocturnas.",
            f"- Nocturnas que no alcanzan la recarga completa ni con puesto libre: {fmt(r3['nocturnas_sin_tiempo_carga'])} "
            f"(de ellas {fmt(r3['cadenas_mas_24h'])} cadenas de mas de 24 h: el flujo, como las jornadas sin bateria, es de "
            "un dia y no ciclico). Son reservas que ninguna programacion de carga puede evitar.",
            "",
        ]
    lineas += [
        "## 5. Reservas por tipo",
        "",
        tabla_md(nombres.presentar(reservas)),
        "",
        "## 6. Energia por tramo horario (kWh y USD)",
        "",
        tabla_md(tab_tarifa.round({c: 0 for c in tab_tarifa if c.startswith(("kWh ", "USD "))})),
        "",
        "## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)",
        "",
        f"Puestos: {kappa}. {N['E2']} = ejecucion minuto a minuto del {texto_e2}.",
        "",
        tabla_md(ocup_h),
        "",
        "## 8. Sensibilidad a la holgura de recarga de la Etapa 3 (modelo agregado, largo del bloque base)",
        "",
        tabla_md(nombres.presentar(sens_h)) if len(sens_h) else "No corrida.",
        "",
        "## 9. Sensibilidad al largo del bloque (modelo agregado, holgura de recarga base)",
        "",
        tabla_md(nombres.presentar(sens_d)) if len(sens_d) else "No corrida.",
        "",
        "## 10. Segundos, estado y brecha de cada modelo",
        "",
        "La Etapa 2 (jornadas sin bateria) no se vuelve a correr: sus jornadas son un archivo.",
        "",
        tabla_md(modelos),
        "",
        "## 11. Modelo detallado frente al modelo agregado",
        "",
        ("Pendiente: correr 13- con --detallado." if det is None else tabla_detallado(det) + "\n\n"
         + conclusion_detallado(det)),
        "",
    ]
    lineas += list(extras)
    lineas += [
        "## Definiciones y supuestos que hay que tener presentes al analizar",
        "",
        f"- La {N['E2-FIFO']} y la {N['E2']} usan las mismas ventanas de la Etapa 3: la diferencia entre ellas es solo la "
        "programacion de la carga.",
        f"- Del {N['E1']} a la {N['E2-FIFO']} se cambia la carga reactiva por la Etapa 3 (cortes + re-encadenamiento con "
        "recarga completa en el patio).",
        "- Parte de la mejora de la Etapa 3 viene de permitir que un bus vuelva al patio y salga de nuevo (paso ii del "
        "diagnostico), algo que ni las jornadas sin bateria ni el caso base permiten.",
        "- Reserva: si la carga de una ventana no termina antes de la siguiente salida del bus, un bus ya cargado cubre esa "
        "salida (250 USD). En una ventana diurna la reserva toma el resto de la cadena (supuesto conservador).",
        "- La Etapa 3 no ve los puestos; la holgura de recarga los anticipa. La Etapa 4 decide con los puestos y la tarifa.",
        "- Los modelos de la Etapa 4 escriben la capacidad en energia por bloque: es exacta salvo en los bloques de borde "
        "('minutos sobre los puestos', en la ejecucion minuto a minuto, mide ese error). Solo la carga por orden de llegada "
        "es exacta al minuto.",
        "- Limitaciones: un solo electroterminal; recarga completa entre tramos; deadhead euclidiano; un dia tipo; "
        "flujo de un dia (no ciclico).",
    ]
    return "\n".join(lineas) + "\n"

if __name__ == "__main__":
    main()
