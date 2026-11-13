"""
Validacion independiente del plan de carga de la Propuesta completa - ICS2122 Capstone Buses Electricos
(ver docs/contexto_entrega_3/).

No corre ningun modelo y no usa funciones de 13-: lee solo los CSV de la Etapa 3 (tramos, cadenas, ventanas) y el
plan de carga (programa_puestos.csv) y comprueba que el plan se puede ejecutar tal cual:

  1. Puestos: en cada minuto cargan a lo mas tantos buses como puestos, y cada puesto atiende un bus a la vez.
  2. Cada carga es un intervalo de minutos enteros en un puesto existente, a lo mas a 180 kW.
  3. El bus esta en el patio: toda carga ocurre desde que llega y dentro de 24 h; si termina despues de su salida,
     esa ventana tiene un bus de reserva.
  4. Energia: cada ventana recibe exactamente la energia de su tramo (recalculada desde tramos.csv), y ningun tramo
     consume mas que la bateria util (315 kWh); asi cada bus sale lleno y nunca baja del minimo.
  5. Reservas: simulando 7 dias seguidos, cada salida de cada bus tiene un bus cargado en el patio, usando solo el bus
     de la cadena mas sus reservas (la reserva es una rotacion: mientras uno termina de cargar, el otro sale).
  6. Costos: la energia y las reservas recalculadas desde el plan coinciden con las informadas.

Uso:
    python scripts/15-validar_plan_carga.py --terminal 4
    python scripts/15-validar_plan_carga.py --prueba            # valida la prueba chica de 13- --prueba --exacto
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import instancia, parametros                       # noqa: E402
from common.rutas import DATA_FILTRADO, CSV_SEP                 # noqa: E402

DIA_MIN = 1440
DIAS_SIMULADOS = 7


def tarifa_por_minuto():
    precios = pd.read_csv(DATA_FILTRADO / "electricity_prices.csv", sep=CSV_SEP)
    t = np.zeros(DIA_MIN)
    for r in precios.itertuples():
        t[int(r.start_hour) * 60:int(r.end_hour) * 60] = r.price_usd_kwh
    return t


def simular_reservas(cadenas, tramos, fin_carga, reserva_de_tramo):
    """Simula DIAS_SIMULADOS dias del plan periodico, cadena por cadena. Cada cadena tiene 1 + sus reservas buses.
    En cada salida sale el bus que hizo el tramo anterior si ya termino de cargar; si no, otro bus de la cadena que este
    lleno en el patio. Devuelve la lista de fallas (cadena, dia, tramo)."""
    sal = dict(zip(tramos["tramo_id"], tramos["salida_patio_min"]))
    fallas = []
    for c in cadenas.itertuples():
        ids = c.tramo_ids.split(";")
        listos = [-math.inf] * (1 + sum(reserva_de_tramo[k] for k in ids))   # hora en que cada bus queda lleno
        anterior = None
        for dia in range(DIAS_SIMULADOS):
            for k in ids:
                salida = sal[k] + DIA_MIN * dia
                if anterior is not None and listos[anterior] <= salida + 1e-6:
                    b = anterior
                else:
                    disponibles = [i for i, t in enumerate(listos) if t <= salida + 1e-6]
                    if not disponibles:
                        fallas.append((c.bus, dia + 1, k))
                        break
                    b = min(disponibles, key=lambda i: listos[i])
                listos[b] = fin_carga[k] + DIA_MIN * dia        # vuelve, carga segun el plan y queda lleno
                anterior = b
    return fallas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terminal", default=parametros.TERMINAL_INSTANCIA, help="depot_id del electroterminal.")
    parser.add_argument("--holgura", type=float, default=parametros.HOLGURAS_RECARGA_MIN[0])
    parser.add_argument("--delta", type=int, default=parametros.DELTA_MIN)
    parser.add_argument("--prueba", action="store_true", help="Valida las carpetas *_prueba.")
    args = parser.parse_args()
    h_txt = f"{args.holgura:g}"

    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    costos = parametros.cargar_costos()
    carpeta = instancia.carpeta_instancia(depots, args.terminal)
    e3 = carpeta / ("etapa3_prueba" if args.prueba else "etapa3") / f"h{h_txt}" / "tablas"
    e4 = carpeta / ("etapa4_prueba" if args.prueba else "etapa4") / f"h{h_txt}_d{args.delta}" / "exacto"
    assert (e4 / "programa_puestos.csv").exists(), f"No existe el plan de carga en {e4}: correr antes 13- con --exacto."
    tramos = pd.read_csv(e3 / "tramos.csv", sep=CSV_SEP, dtype={"tramo_id": str})
    cadenas = pd.read_csv(e3 / "cadenas.csv", sep=CSV_SEP, dtype={"tramo_ids": str})
    v = pd.read_csv(e3 / "ventanas.csv", sep=CSV_SEP, dtype={"tramo_id": str})
    plan = pd.read_csv(e4 / "programa_puestos.csv", sep=CSV_SEP)
    res = pd.read_csv(e4 / "resumen.csv", sep=CSV_SEP).iloc[0]
    kappa = int(res["puestos"])
    q = costos.charge_power_kw / 60
    util = costos.bateria_util_ciclica_kwh(1.0)
    print(f"=== Validacion del plan de carga: {res['terminal']}, {kappa} puestos, {len(v):,} ventanas, "
          f"{len(plan):,} cargas ===\n")
    filas = []

    def anotar(criterio, ok, detalle):
        filas.append(dict(criterio=criterio, resultado="OK" if ok else "FALLA", detalle=detalle))
        print(f"  [{'OK' if ok else 'FALLA'}] {criterio}: {detalle}")

    # 1. Puestos
    minutos = [np.arange(r.inicio_min, r.fin_min) % DIA_MIN for r in plan.itertuples()]
    occ = np.zeros(DIA_MIN, int)
    por_puesto = np.zeros((kappa + 1, DIA_MIN), int)
    for r, ms in zip(plan.itertuples(), minutos):
        np.add.at(occ, ms, 1)
        np.add.at(por_puesto[min(max(r.puesto, 0), kappa)], ms, 1)
    anotar("1. Buses cargando por minuto <= puestos", occ.max() <= kappa,
           f"maximo {occ.max()} de {kappa}; puestos con dos buses a la vez en algun minuto: "
           f"{int((por_puesto.max(axis=1) > 1).sum())}")
    if por_puesto.max() > 1:
        filas[-1]["resultado"] = "FALLA"

    # 2. Cargas enteras en puestos existentes, a lo mas 180 kW
    enteras = np.allclose(plan["inicio_min"], plan["inicio_min"].round()) and np.allclose(plan["fin_min"],
                                                                                          plan["fin_min"].round())
    potencia = (plan["kwh"] <= (plan["fin_min"] - plan["inicio_min"]) * q + 1e-6).all()
    puestos_ok = plan["puesto"].between(1, kappa).all() and (plan["fin_min"] > plan["inicio_min"]).all()
    anotar("2. Cada carga: minutos enteros, puesto existente, <= 180 kW", enteras and potencia and puestos_ok,
           f"{len(plan):,} cargas en {plan['puesto'].nunique()} puestos")

    # 3. El bus esta en el patio; si termina despues de salir, hay reserva
    p = plan.merge(v[["ventana_id", "tramo_id", "llegada_min", "limite_min"]], on="ventana_id", how="left")
    dentro = (p["inicio_min"] >= np.ceil(p["llegada_min"] - 1e-9)) & (p["fin_min"] <= p["llegada_min"] + DIA_MIN + 1e-9)
    ultima = p.sort_values(["ventana_id", "inicio_min"]).groupby("ventana_id").tail(1)
    fin_carga_v = (ultima["fin_min"] - 1 + (ultima["kwh"] - q * (ultima["fin_min"] - ultima["inicio_min"] - 1)) / q)
    fin_carga = pd.Series(fin_carga_v.values, index=ultima["ventana_id"].values)
    lim = v.set_index("ventana_id")["limite_min"]
    reserva_v = p.groupby("ventana_id")["reserva"].max().reindex(v["ventana_id"], fill_value=0)
    tarde = fin_carga > lim.reindex(fin_carga.index) + 1e-6
    sin_reserva = tarde & (reserva_v.reindex(fin_carga.index) == 0)
    anotar("3. Toda carga con el bus en el patio; si termina despues de su salida, hay reserva",
           bool(dentro.all()) and not sin_reserva.any(),
           f"cargas fuera de [llegada, llegada + 24 h): {int((~dentro).sum())}; ventanas que terminan tarde: "
           f"{int(tarde.sum())}, sin reserva: {int(sin_reserva.sum())}")

    # 4. Energia: cada ventana repone su tramo, y ningun tramo supera la bateria util
    kwh_tramo = tramos.set_index("tramo_id")["kwh"]
    cargado = p.groupby("ventana_id")["kwh"].sum().reindex(v["ventana_id"], fill_value=0.0)
    necesita = kwh_tramo.reindex(v["tramo_id"]).values
    dif = np.abs(cargado.values - necesita).max()
    anotar("4. Cada ventana repone la energia de su tramo; ningun tramo supera la bateria util",
           dif < 1e-3 and (tramos["kwh"] <= util + 1e-6).all(),
           f"diferencia maxima {dif:.2e} kWh; tramo mas largo {tramos['kwh'].max():.1f} de {util:.0f} kWh")

    # 5. Reservas como rotacion, 7 dias
    tramo_de_v = dict(zip(v["ventana_id"], v["tramo_id"]))
    fin_por_tramo = {tramo_de_v[w]: f for w, f in fin_carga.items()}
    reserva_de_tramo = {tramo_de_v[w]: int(r) for w, r in reserva_v.items()}
    fallas = simular_reservas(cadenas, tramos, fin_por_tramo, reserva_de_tramo)
    n_res = int(reserva_v.sum())
    anotar(f"5. Simulando {DIAS_SIMULADOS} dias, cada salida tiene un bus cargado (buses de la Etapa 3 + reservas)",
           not fallas, f"{len(cadenas):,} buses + {n_res} reservas = {len(cadenas) + n_res:,} buses; salidas sin bus: "
           f"{len(fallas)}" + (f" (primera: bus {fallas[0][0]}, dia {fallas[0][1]}, tramo {fallas[0][2]})" if fallas else ""))

    # 6. Costos
    tar = tarifa_por_minuto()
    costo = 0.0
    for r, ms in zip(plan.itertuples(), minutos):
        e = np.full(len(ms), q)
        e[-1] = r.kwh - q * (len(ms) - 1)
        costo += float(tar[ms] @ e)
    ok6 = abs(costo - res["costo_energia_usd"]) < 1e-2 * max(1, len(v)) and n_res == int(res["reservas"])
    anotar("6. Energia y reservas recalculadas = informadas", ok6,
           f"energia {costo:,.2f} USD (informada {res['costo_energia_usd']:,.2f}); reservas {n_res} "
           f"(informadas {int(res['reservas'])})")

    out = pd.DataFrame(filas)
    out.to_csv(e4 / "validacion.csv", index=False, sep=CSV_SEP)
    todo = (out["resultado"] == "OK").all()
    print(f"\n  -> {e4 / 'validacion.csv'}")
    print("\n=== PLAN DE CARGA FACTIBLE: TODAS LAS VALIDACIONES OK ===" if todo else
          "\n=== HAY VALIDACIONES QUE FALLAN: revisar el detalle ===")
    if not todo:
        sys.exit(1)


if __name__ == "__main__":
    main()
