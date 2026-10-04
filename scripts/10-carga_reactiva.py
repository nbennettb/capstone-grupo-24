"""
Etapa 3 del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md, seccion 4, Etapa 3).

Simulador de la POLITICA DE CARGA REACTIVA ("miope") sobre las jornadas fijas
de un escenario de la Etapa 2 (E0, E1 y sus variantes): cada bus carga solo cuando lo
necesita, sin mirar la tarifa ni el futuro. Es la linea base contra la que se
mide el valor de optimizar la carga (MILP, Etapa 4) y lo que le agrega energia,
colas y jornadas partidas al caso base.

Supuestos (parametros en scripts/common/parametros.py):
  - Traslados: distancia euclidiana x FACTOR_DESVIO a VELOCIDAD_KMH, igual que el VSP.
  - Consumo CONSUMO_KWH_KM; carga lineal a charge_power_kw; minimo min_soc.
  - Nivel `--soc` (default 1.0, punto de partida de B6): SOC de partida, de llegada
    y TOPE de carga de todo bus (condicion ciclica: inicio = fin).
  - Cada bus carga en SU electroterminal. Con los escenarios de terminales unidos (E0, E1, E1_C2), Los Espinos y Santa Rosa son un
    solo terminal (puestos sumados); el bus va al patio mas cercano de los dos.
  - Los puestos limitan solo la carga simultanea (estacionar no consume puesto).

Reglas de la politica:
  1. El bus parte del electroterminal con SOC = nivel, a tiempo para su primera expedicion.
  2. Antes de cada expedicion k: si no puede hacer [traslado al origen de k + expedicion k +
     volver al electroterminal desde su destino] sin bajar del minimo, va a cargar despues de
     la expedicion k-1: viaja al electroterminal, espera puesto si no hay, carga y vuelve al
     origen de k con LAYOVER_MIN de margen antes de su salida.
  3. [Decision] CARGA PARCIAL: carga hasta el nivel o hasta que se acabe el hueco, lo que
     ocurra primero (un operador no partiria una jornada que puede seguir con una carga
     parcial; ademas la regla estricta favoreceria artificialmente los niveles bajos en el
     barrido, porque su carga completa es mas corta). Si ni asi puede hacer k y volver, la
     JORNADA SE PARTE: el bus se queda en el electroterminal (carga final) y un bus NUEVO sale
     con SOC = nivel a cubrir desde k (+1 bus). Motivo: 'sin_hueco' (el tiempo no alcanza aunque
     hubiera puesto libre) o 'sin_puesto' (habria alcanzado con puesto libre).
  4. Sin puesto libre el bus espera (WAITING_COST por minuto). Los puestos se asignan en orden
     de llegada al electroterminal: primer intervalo continuo con puesto libre.
  5. Al terminar vuelve al electroterminal y carga hasta el nivel. Si no termina antes de su
     primera salida del dia siguiente -> CICLO NO CUMPLIDO (se registra; la energia se carga igual).
  6. Periodicidad: ocupacion de puestos y tarifa son modulo 24 h (el dia siguiente es igual).
  7. Costo de energia: kWh de cada minuto x tarifa de ese minuto + fixed_charge_cost por evento.
  8. BUSES DE RESERVA (condicion ciclica): un bus que no termina su carga antes de su salida del dia siguiente
     (ciclo no cumplido) deja esa salida a un bus de reserva ya cargado; en estado estacionario es una rotacion
     (el atrasado termina de cargar, atraso < 24 h, y es la reserva del dia siguiente). Se necesitan tantas
     reservas como ciclos no cumplidos, a vehicle_fixed_cost cada una, y el costo total las incluye. Es una cota
     superior simple de explicar: lo que la carga no alcanza a reponer a tiempo se paga con flota. Una solucion es
     FACTIBLE si no tiene deficit de energia y todo atraso es menor a 24 h; con deficit, las reservas no la arreglan.

Validacion previa: antes de simular, reconstruye cada jornada sin cargas y exige que calce
con el VSP (km, kWh y espera). Despues: SOC siempre entre minimo y nivel, ocupacion <= puestos,
balance de energia por bus (cargado = consumido), cobertura intacta.

Input:  data-processed/{expediciones,jornadas_<escenario>}.csv, data-filtrado/{depots,
        electricity_prices}.csv, results/etapa2_vsp/tablas/resumen_escenarios.csv
Output: results/etapa3_carga_reactiva/tablas/{eventos,ventanas,jornadas,ocupacion}_<esc>_soc<nivel>.csv
        results/etapa3_carga_reactiva/tablas/resumen_carga.csv  (una fila por escenario y nivel)
        results/etapa3_carga_reactiva/graficos/{ocupacion,soc_ejemplo}_<esc>_soc<nivel>.png
        results/etapa3_carga_reactiva/reporte_<esc>_soc<nivel>.md

Uso:
    python scripts/10-carga_reactiva.py --escenario E0 --jornadas data-processed/jornadas_E0_subset.csv --traza 1
        Checkpoint chico: imprime el SOC paso a paso de la jornada 1 (usar --soc 0.7 para forzar recargas).

    python scripts/10-carga_reactiva.py --escenario E0            # red completa, nivel 100%
    python scripts/10-carga_reactiva.py --escenario E1 --soc 0.9
"""

import argparse
import heapq
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import geo, parametros                                            # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, RESULTS_DIR, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa3_carga_reactiva")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)

DIA_MIN = 1440
EPS = 1e-6


# --------------------------------------------------------------------------- #
# Carga de datos
# --------------------------------------------------------------------------- #

def cargar_tarifa():
    """Tarifa (USD/kWh) por minuto del dia, desde electricity_prices.csv."""
    p = pd.read_csv(DATA_FILTRADO / "electricity_prices.csv", sep=CSV_SEP)
    t = np.zeros(DIA_MIN)
    for _, r in p.iterrows():
        t[int(r["start_hour"]) * 60:int(r["end_hour"]) * 60] = float(r["price_usd_kwh"])
    assert (t > 0).all(), "electricity_prices.csv no cubre las 24 horas."
    return t


class Bus:
    """Una jornada en simulacion (puede ser el resto de una jornada partida)."""
    __slots__ = ("jid", "origen", "parte", "motivo", "rows", "conn", "pullout_km", "pullin_km", "term",
                 "pos", "s", "t_fin_ult", "t_salida", "soc_salida", "km_pullout", "km_conn", "km_carga",
                 "km_pullin", "idle_min", "cola_min", "kwh_exp", "n_inter", "cargado", "ventanas",
                 "trace", "log", "ciclo_ok", "retraso_ciclo", "deficit")

    def __init__(self, jid, origen, parte, motivo, rows, conn, pullout_km, pullin_km, term, log):
        self.jid, self.origen, self.parte, self.motivo = jid, origen, parte, motivo
        self.rows, self.conn, self.pullout_km, self.pullin_km, self.term = rows, conn, pullout_km, pullin_km, term
        self.pos = 0
        self.s = 0.0
        self.t_fin_ult = 0.0
        self.t_salida = 0.0
        self.soc_salida = 0.0
        self.km_pullout = pullout_km
        self.km_conn = self.km_carga = self.km_pullin = 0.0
        self.idle_min = self.cola_min = self.kwh_exp = self.cargado = 0.0
        self.n_inter = 0
        self.ventanas = []
        self.trace = []
        self.log = [] if log else None
        self.ciclo_ok = True
        self.retraso_ciclo = 0.0
        self.deficit = 0.0


class Simulador:
    def __init__(self, ex, depots, costos, soc, unir_ids, tarifa, trazas):
        self.costos = costos
        self.soc = soc
        self.L = soc * costos.battery_kwh
        self.smin = costos.min_soc * costos.battery_kwh
        self.kwh_min = costos.charge_power_kw / 60.0                      # kWh por minuto de carga
        self.consumo = parametros.CONSUMO_KWH_KM
        self.v = parametros.VELOCIDAD_KMH
        self.layover = parametros.LAYOVER_MIN
        self.tarifa = tarifa
        self.trazas = trazas

        self.dep = ex["dep_min"].tolist()
        self.arr = ex["arr_min"].tolist()
        self.kwh = ex["kwh"].tolist()
        f = parametros.FACTOR_DESVIO
        DP = geo.xy(depots["lat"].values, depots["lon"].values)
        self.dist_o = geo.matriz_distancias_planas(geo.xy(ex["o_lat"].values, ex["o_lon"].values), DP) * f
        self.dist_d = geo.matriz_distancias_planas(geo.xy(ex["d_lat"].values, ex["d_lon"].values), DP) * f

        depot_ids = depots["depot_id"].astype(str).tolist()
        self.patio_idx = {d: i for i, d in enumerate(depot_ids)}
        cap = depots["capacity"].astype(int).tolist()
        unidos = [self.patio_idx[d] for d in unir_ids]
        self.term_patios = ([unidos] if unidos else []) + [[i] for i in range(len(depot_ids)) if i not in unidos]
        self.term_nombre = []
        for patios in self.term_patios:
            self.term_nombre.append(" + ".join(depots["nombre"].iloc[patios].tolist()))
        self.kappa = [sum(cap[i] for i in patios) for patios in self.term_patios]
        self.patio_a_term = {i: t for t, patios in enumerate(self.term_patios) for i in patios}
        self.dterm_d = np.column_stack([self.dist_d[:, p].min(axis=1) for p in self.term_patios]).tolist()
        self.occ = [np.zeros(DIA_MIN, dtype=np.int32) for _ in self.term_patios]

        self.heap, self.cuenta = [], 0
        self.eventos, self.nuevos, self.buses_terminados = [], [], []
        self.n_particiones = {"sin_hueco": 0, "sin_puesto": 0}
        self.n_fragmentadas = 0
        self.n_sin_cupo = 0

    # ------------------------------------------------------------------ #
    def nuevo_bus(self, jid, origen, parte, motivo, rows, conn, pullout_km, pullin_km, term):
        return Bus(jid, origen, parte, motivo, rows, conn, pullout_km, pullin_km, term,
                   str(jid) in self.trazas or str(origen) in self.trazas)

    def anotar(self, bus, t, texto, soc=None):
        """Linea de la traza (solo para las jornadas pedidas con --traza). soc: SOC a mostrar si no es bus.s."""
        if bus.log is not None:
            soc = bus.s if soc is None else soc
            bus.log.append(f"  t={t:8.2f} min ({int(t) // 60:02d}:{int(t) % 60:02d})  SOC={soc:7.2f} kWh "
                           f"({soc / self.costos.battery_kwh:6.1%})  {texto}")

    def empujar(self, T, bus, tipo, datos):
        self.cuenta += 1
        heapq.heappush(self.heap, (T, self.cuenta, bus, tipo, datos))

    # ------------------------------------------------------------------ #
    def avanzar(self, bus):
        """Hace avanzar al bus por sus expediciones hasta que necesite cargar (empuja un pedido
        'inter') o termine (empuja un pedido 'final')."""
        rows, n, smin, c = bus.rows, len(bus.rows), self.smin, self.consumo
        if bus.pos == 0:
            r0 = rows[0]
            bus.t_salida = self.dep[r0] - self.layover - bus.pullout_km / self.v * 60
            bus.soc_salida = self.L
            bus.s = self.L
            bus.trace.append((bus.t_salida, bus.s))
            self.anotar(bus, bus.t_salida, f"sale del electroterminal (pullout {bus.pullout_km:.2f} km)")
            s_pre = self.L - bus.pullout_km * c
            res = bus.pullin_km if n == 1 else self.dterm_d[r0][bus.term]
            assert s_pre - self.kwh[r0] - res * c >= smin - EPS, (
                f"La jornada {bus.jid} no puede hacer ni su primera expedicion partiendo con el nivel "
                f"{self.soc:.0%}: revisar el nivel o las distancias.")
            bus.s = s_pre - self.kwh[r0]
            bus.kwh_exp += self.kwh[r0]
            bus.pos, bus.t_fin_ult = 1, self.arr[r0]
            bus.trace.append((self.arr[r0], bus.s))
            self.anotar(bus, self.arr[r0], f"termina expedicion {r0}")
        while bus.pos < n:
            k = bus.pos
            rk, rp = rows[k], rows[k - 1]
            dh = bus.conn[k - 1]
            res = bus.pullin_km if k == n - 1 else self.dterm_d[rk][bus.term]
            if bus.s - (dh * c + self.kwh[rk] + res * c) >= smin - EPS:
                gap = self.dep[rk] - self.arr[rp] - self.layover - dh / self.v * 60
                assert gap >= -EPS, f"Conexion infactible en la jornada {bus.jid} (gap {gap:.3f} min)."
                bus.idle_min += max(gap, 0.0)
                bus.s -= dh * c + self.kwh[rk]
                bus.kwh_exp += self.kwh[rk]
                bus.km_conn += dh
                bus.pos, bus.t_fin_ult = k + 1, self.arr[rk]
                bus.trace.append((self.arr[rk], bus.s))
                self.anotar(bus, self.arr[rk], f"conexion {dh:.2f} km + expedicion {rk}")
                continue
            # --- necesita cargar antes de la expedicion k ---
            patios = self.term_patios[bus.term]
            dd = self.dist_d[rp, patios]
            j = int(np.argmin(dd))
            P, d1 = patios[j], float(dd[j])
            d2 = float(self.dist_o[rk, P])
            T = self.arr[rp] + d1 / self.v * 60
            datos = dict(k=k, P=P, d1=d1, d2=d2, res=res)
            self.anotar(bus, self.arr[rp], f"necesita cargar antes de la expedicion {rk}: va al electroterminal "
                                           f"({d1:.2f} km), llega t={T:.1f}")
            self.empujar(T, bus, "inter", datos)
            return
        # --- fin de jornada: vuelve al electroterminal y carga hasta el nivel ---
        T = bus.t_fin_ult + bus.pullin_km / self.v * 60
        bus.km_pullin = bus.pullin_km
        bus.s -= bus.pullin_km * c
        bus.trace.append((T, bus.s))
        self.anotar(bus, T, f"llega al electroterminal (pullin {bus.pullin_km:.2f} km): carga final")
        patios = self.term_patios[bus.term]
        P = patios[int(np.argmin(self.dist_d[rows[-1], patios]))]
        self.empujar(T, bus, "final", {"patio": P})

    # ------------------------------------------------------------------ #
    def buscar_slot(self, term, t0, tmax, dmin, dwant, ventana_total=None):
        """Primer ts en [t0, tmax] con un tramo continuo de puesto libre de al menos dmin minutos.
        Devuelve (ts, run) con run = largo del tramo libre desde ts, o None."""
        busy = self.occ[term] >= self.kappa[term]
        b3 = np.concatenate([busy, busy, busy])
        largo = len(b3)
        idx = np.where(b3, np.arange(largo), largo)
        nb = np.minimum.accumulate(idx[::-1])[::-1]
        ts = np.arange(t0, tmax + 1)
        a = ts % DIA_MIN
        run = nb[a] - a
        ok = run >= dmin
        if not ok.any():
            return None
        i = int(np.argmax(ok))
        return int(ts[i]), int(run[i])

    def reservar(self, term, minutos):
        self.occ[term][np.asarray(minutos) % DIA_MIN] += 1
        assert self.occ[term].max() <= self.kappa[term], \
            f"Se excedieron los puestos de {self.term_nombre[term]} al reservar una carga."

    def costo_energia(self, minutos, kwh_total):
        """Costo de cargar kwh_total en los minutos dados (kwh_min por minuto, el ultimo parcial)."""
        m = np.asarray(minutos)
        e = np.full(len(m), self.kwh_min)
        e[-1] = kwh_total - self.kwh_min * (len(m) - 1)
        assert e[-1] > -EPS and e[-1] <= self.kwh_min + EPS, "Reparto de energia por minuto inconsistente."
        return float((e * self.tarifa[m % DIA_MIN]).sum())

    # ------------------------------------------------------------------ #
    def resolver_inter(self, bus, T, d):
        k, P, d1, d2, res = d["k"], d["P"], d["d1"], d["d2"], d["res"]
        rows, c = bus.rows, self.consumo
        rk, rp = rows[k], rows[k - 1]
        t1 = d1 / self.v * 60
        t2 = d2 / self.v * 60
        s1 = bus.s - d1 * c
        assert s1 >= self.smin - EPS, "El bus no alcanza a llegar al electroterminal: se rompio el invariante de reserva."
        want = self.L - s1
        emin = d2 * c + self.kwh[rk] + res * c + self.smin - s1
        dwant = int(math.ceil(want / self.kwh_min - 1e-9))
        dmin = max(1, int(math.ceil(emin / self.kwh_min - 1e-9)))
        tl = self.dep[rk] - self.layover - t2
        tl_floor = int(math.floor(tl + 1e-9))
        t0 = int(math.ceil(T - 1e-9))
        tmax = tl_floor - dmin
        motivo = None
        if dmin > dwant or tmax < t0:
            motivo = "sin_hueco"
        else:
            slot = self.buscar_slot(bus.term, t0, tmax, dmin, dwant)
            if slot is None:
                motivo = "sin_puesto"
        if motivo is None:
            ts, run = slot
            dur = min(dwant, tl_floor - ts, run)
            assert dur >= dmin
            cargado = min(self.kwh_min * dur, want)
            minutos = np.arange(ts, ts + dur)
            self.reservar(bus.term, minutos)
            te = ts + cargado / self.kwh_min
            costo = self.costo_energia(minutos, cargado)
            idle = self.dep[rk] - self.layover - (te + t2)
            assert idle >= -EPS
            # ventana de carga: consumo desde que salio por ultima vez del electroterminal
            bus.ventanas.append(dict(t_ini=T, t_fin=tl_floor, tipo="intermedia", term=bus.term,
                                     kwh_consumidos_desde_ventana_anterior=bus.soc_salida - s1))
            self.eventos.append(dict(jornada_id=bus.jid, tipo="intermedia", term=bus.term, patio=P,
                                     t_llegada=T, t_inicio=ts, t_fin=te, espera_cola_min=ts - T, kwh=cargado,
                                     costo_energia_usd=costo, soc_antes=s1, soc_despues=s1 + cargado,
                                     fragmentada=False, ciclo_cumplido=np.nan, retraso_ciclo_min=np.nan))
            bus.cola_min += ts - T
            bus.idle_min += max(idle, 0.0)
            bus.cargado += cargado
            bus.n_inter += 1
            bus.km_carga += d1 + d2
            bus.soc_salida = s1 + cargado
            s_o = s1 + cargado - d2 * c
            assert s_o - self.kwh[rk] - res * c >= self.smin - 1e-6, "La carga no alcanzo para la expedicion siguiente."
            bus.trace += [(T, s1), (ts, s1), (te, s1 + cargado), (te + t2, s_o)]
            bus.s = s_o - self.kwh[rk]
            bus.kwh_exp += self.kwh[rk]
            bus.pos, bus.t_fin_ult = k + 1, self.arr[rk]
            bus.trace.append((self.arr[rk], bus.s))
            self.anotar(bus, T, f"llega al electroterminal con {s1:.1f} kWh; espera puesto hasta t={ts} ({ts - T:.1f} min)", soc=s1)
            self.anotar(bus, te, f"fin de carga intermedia: {cargado:.1f} kWh en {te - ts:.1f} min; vuelve al origen a "
                                 f"t={te + t2:.1f} (expedicion {rk} sale a t={self.dep[rk]:.1f}, tope de carga t={tl_floor})",
                        soc=s1 + cargado)
            self.avanzar(bus)
            return
        # --- la jornada se parte: este bus termina aqui y un bus nuevo cubre desde la expedicion k ---
        self.n_particiones[motivo] += 1
        pullin_original = bus.pullin_km
        conn_resto = bus.conn[k:]                       # conexiones entre las expediciones rows[k:]
        bus.pullin_km = d1
        bus.km_pullin = d1
        bus.s = s1
        bus.rows, bus.conn = rows[:k], bus.conn[:k - 1]
        bus.trace.append((T, s1))
        self.anotar(bus, T, f"SE PARTE la jornada ({motivo}): este bus queda cargando; un bus nuevo cubre desde {rk}")
        self.empujar(T, bus, "final", {"patio": P})
        pat = self.term_patios[bus.term]
        po = pat[int(np.argmin(self.dist_o[rk, pat]))]
        nuevo = self.nuevo_bus(f"{bus.origen}.{bus.parte + 1}", bus.origen, bus.parte + 1, motivo, rows[k:],
                               conn_resto, float(self.dist_o[rk, po]), pullin_original, bus.term)
        self.nuevos.append(nuevo)
        self.avanzar(nuevo)

    # ------------------------------------------------------------------ #
    def resolver_final(self, bus, T, d):
        need = self.L - bus.s
        assert need >= -EPS
        if need < EPS:
            need = 0.0
        s_antes = bus.s
        patio = d.get("patio")
        dwant = max(1, int(math.ceil(need / self.kwh_min - 1e-9)))
        t0 = int(math.ceil(T - 1e-9))
        slot = self.buscar_slot(bus.term, t0, t0 + DIA_MIN - 1, dwant, dwant)
        fragmentada = False
        if slot is not None:
            ts = slot[0]
            minutos = np.arange(ts, ts + dwant)
        else:
            # no hay un tramo continuo en 24 h: carga en los minutos con puesto libre que encuentre
            fragmentada = True
            self.n_fragmentadas += 1
            libres, m = [], t0
            while len(libres) < dwant and m < t0 + DIA_MIN:
                if self.occ[bus.term][m % DIA_MIN] < self.kappa[bus.term]:
                    libres.append(m)
                m += 1
            if not libres:
                # el electroterminal no tiene ni un minuto libre en 24 h: no repone nada
                bus.deficit = need
                bus.ciclo_ok = False
                bus.retraso_ciclo = float("nan")
                self.n_sin_cupo += 1
                self.eventos.append(dict(jornada_id=bus.jid, tipo="final", term=bus.term,
                                         patio=patio if patio is not None else -1, t_llegada=T, t_inicio=np.nan,
                                         t_fin=np.nan, espera_cola_min=np.nan, kwh=0.0, costo_energia_usd=0.0,
                                         soc_antes=s_antes, soc_despues=s_antes, fragmentada=True,
                                         ciclo_cumplido=False, retraso_ciclo_min=np.nan))
                bus.ventanas.append(dict(t_ini=T, t_fin=bus.t_salida + DIA_MIN, tipo="final", term=bus.term,
                                         kwh_consumidos_desde_ventana_anterior=bus.soc_salida - s_antes))
                self.anotar(bus, T, "carga final IMPOSIBLE: el electroterminal no tiene puestos libres en 24 h")
                self.buses_terminados.append(bus)
                return
            minutos = np.asarray(libres)
            ts = int(minutos[0])
            if len(libres) < dwant:
                # capacidad insuficiente: repone solo lo que cabe y el resto queda como deficit de energia
                need_real = self.kwh_min * len(libres)
                bus.deficit = need - need_real
                need = need_real
        self.reservar(bus.term, minutos)
        te = int(minutos[-1]) + 1 - (self.kwh_min * len(minutos) - need) / self.kwh_min
        costo = self.costo_energia(minutos, need)
        salida_sig = bus.t_salida + DIA_MIN
        ok = te <= salida_sig + 1e-9 and bus.deficit < EPS
        bus.ciclo_ok = bool(ok)
        bus.retraso_ciclo = 0.0 if ok else max(te - salida_sig, 0.0)
        bus.cola_min += ts - T
        bus.cargado += need
        bus.ventanas.append(dict(t_ini=T, t_fin=salida_sig, tipo="final", term=bus.term,
                                 kwh_consumidos_desde_ventana_anterior=bus.soc_salida - s_antes))
        self.eventos.append(dict(jornada_id=bus.jid, tipo="final", term=bus.term, patio=patio if patio is not None else -1,
                                 t_llegada=T, t_inicio=ts, t_fin=te, espera_cola_min=ts - T, kwh=need,
                                 costo_energia_usd=costo, soc_antes=s_antes, soc_despues=s_antes + need,
                                 fragmentada=fragmentada, ciclo_cumplido=bool(ok),
                                 retraso_ciclo_min=bus.retraso_ciclo))
        bus.trace += [(ts, s_antes), (te, s_antes + need)]
        bus.s = s_antes + need
        self.anotar(bus, te, f"carga final: llega {T:.1f}, espera {ts - T:.1f} min, carga {need:.1f} kWh hasta t={te:.1f}"
                             f" | salida del dia siguiente t={salida_sig:.1f} -> ciclo {'cumplido' if ok else 'NO cumplido'}"
                             + (f" | DEFICIT {bus.deficit:.1f} kWh (no hay puestos)" if bus.deficit > EPS else ""))
        self.buses_terminados.append(bus)

    # ------------------------------------------------------------------ #
    def correr(self, buses):
        for b in buses:
            self.avanzar(b)
        while self.heap:
            T, _, bus, tipo, datos = heapq.heappop(self.heap)
            if tipo == "inter":
                self.resolver_inter(bus, T, datos)
            else:
                self.resolver_final(bus, T, datos)


# --------------------------------------------------------------------------- #
# Construccion de buses y validacion previa contra el VSP
# --------------------------------------------------------------------------- #

def construir_buses(sim, j, ex_idx):
    buses = []
    for r in j.itertuples(index=False):
        rows = [ex_idx[e] for e in r.expedicion_ids.split(";")]
        conn = [float(x) for x in r.km_deadhead_seq.split(";")] if isinstance(r.km_deadhead_seq, str) else []
        assert len(conn) == len(rows) - 1, f"Jornada {r.bus_id}: {len(conn)} conexiones para {len(rows)} expediciones."
        ps, pl = sim.patio_idx[str(r.depot_salida)], sim.patio_idx[str(r.depot_llegada)]
        assert sim.patio_a_term[ps] == sim.patio_a_term[pl], (
            f"Jornada {r.bus_id}: sale de un electroterminal y vuelve a otro; se viola el retorno [Profesor].")
        buses.append(sim.nuevo_bus(str(r.bus_id), str(r.bus_id), 0, "", rows, conn, float(r.km_pullout),
                                   float(r.km_pullin), sim.patio_a_term[ps]))
    return buses


def validar_reconstruccion(sim, j, buses, esperada_h):
    """Reconstruye cada jornada SIN cargas y exige que calce con el VSP: kWh por jornada y espera total."""
    c = sim.consumo
    kwh_calc, idle_min = np.zeros(len(buses)), 0.0
    for i, b in enumerate(buses):
        rows = b.rows
        e = sum(sim.kwh[r] for r in rows) + (b.pullout_km + sum(b.conn) + b.pullin_km) * c
        kwh_calc[i] = e
        for k in range(1, len(rows)):
            idle_min += sim.dep[rows[k]] - sim.arr[rows[k - 1]] - sim.layover - b.conn[k - 1] / sim.v * 60
    dif = np.abs(kwh_calc - j["kwh_total"].values)
    # tolerancia: el VSP guarda los km de cada conexion con 4 decimales (<= 0,0005 km x 1,4 kWh/km por conexion)
    assert dif.max() < 0.02, (f"La reconstruccion no calza con el VSP: la jornada con mayor diferencia de kWh "
                              f"difiere en {dif.max():.4f} kWh. El simulador no esta leyendo las jornadas como las construyo el VSP.")
    idle_h = idle_min / 60
    print(f"  [OK] Reconstruccion sin cargas calza con el VSP: kWh por jornada (diferencia maxima {dif.max():.2e}), "
          f"espera recalculada {idle_h:,.1f} h", end="")
    if esperada_h is not None and not np.isnan(esperada_h):
        assert abs(idle_h - esperada_h) <= max(0.5, 1e-3 * esperada_h), (
            f"La espera recalculada ({idle_h:,.1f} h) no calza con la del VSP ({esperada_h:,.1f} h).")
        print(f" = VSP ({esperada_h:,.1f} h).")
    else:
        print(" (sin resumen del VSP para comparar).")
    return idle_h


# --------------------------------------------------------------------------- #
# Cota de factibilidad: maximo de energia que cabe en las ventanas de carga (LP)
# --------------------------------------------------------------------------- #

def cota_carga_lp(sim, buses, bloque_min=15):
    """Maximo de energia de las CARGAS FINALES que cabe dentro de la ventana de cada bus (llegada al electroterminal
    hasta su primera salida del dia siguiente), dados los puestos de cada terminal y las cargas intermedias ya fijas,
    repartiendo la carga de la MEJOR forma posible (LP con bloques de `bloque_min` minutos, modulo 24 h). Es una cota
    optimista: responde si algun programa de carga, por bueno que fuera, podria reponer toda la energia a tiempo con las
    jornadas dadas. Devuelve (energia_cargable_kwh, energia_necesaria_kwh)."""
    import scipy.sparse as sps
    from scipy.optimize import linprog
    B = bloque_min
    nb = DIA_MIN // B
    cap_bloque = sim.costos.charge_power_kw * B / 60.0           # kWh por puesto y bloque
    ventana = {}
    for b in buses:
        for w in b.ventanas:
            if w["tipo"] == "final":
                ventana[b.jid] = (w["t_ini"], w["t_fin"])
    cargable = necesaria = 0.0
    for t in range(len(sim.term_patios)):
        base = np.zeros(nb)
        for e in sim.eventos:
            if e["term"] == t and e["tipo"] == "intermedia":
                m0 = int(e["t_inicio"])
                for m in range(m0, m0 + int(math.ceil(e["kwh"] / sim.kwh_min - 1e-9))):
                    base[(m % DIA_MIN) // B] += 1.0 / B
        filas, cols, vals, trabajo, fil_j, necesidad = [], [], [], [], [], []
        nvar = 0
        for e in sim.eventos:
            if e["term"] != t or e["tipo"] != "final":
                continue
            a, d = ventana[e["jornada_id"]]
            kwh_nec = sim.L - e["soc_antes"]
            j = len(necesidad)
            necesidad.append(kwh_nec)
            for blq in range(int(math.ceil(a / B)), int(math.floor(d / B))):
                filas.append(blq % nb)
                cols.append(nvar)
                vals.append(1.0)
                trabajo.append(j)
                fil_j.append(nvar)
                nvar += 1
        necesaria += sum(necesidad)
        if nvar == 0:
            continue
        A_cap = sps.csr_matrix((vals, (filas, cols)), shape=(nb, nvar))
        A_job = sps.csr_matrix((np.ones(nvar), (trabajo, fil_j)), shape=(len(necesidad), nvar))
        A = sps.vstack([A_cap, A_job])
        rhs = np.concatenate([np.maximum(sim.kappa[t] - base, 0.0) * cap_bloque, necesidad])
        res = linprog(-np.ones(nvar), A_ub=A, b_ub=rhs, bounds=(0, cap_bloque), method="highs")
        assert res.status == 0, f"El LP de la cota no resolvio ({res.message})."
        cargable += -res.fun
    return cargable, necesaria


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #

def hora(t):
    if t != t:          # NaN: la carga no pudo realizarse
        return ""
    t = t % DIA_MIN
    return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def tablas_salida(sim, buses, ex, ex_ids, depots, costos, etq, soc_pct, escribir=True):
    nombre_patio = depots["nombre"].tolist()
    c = sim.consumo
    filas_j = []
    for b in sorted(buses, key=lambda b: (int(b.origen), b.parte)):
        km_vac = b.km_pullout + b.km_conn + b.km_carga + b.km_pullin
        filas_j.append(dict(
            jornada_id=b.jid, bus_origen=b.origen, parte=b.parte, motivo_inicio=b.motivo,
            terminal=sim.term_nombre[b.term], n_expediciones=len(b.rows),
            expedicion_ids=";".join(ex_ids[r] for r in b.rows), salida_electroterminal_min=round(b.t_salida, 2),
            dep_min=sim.dep[b.rows[0]], arr_min=sim.arr[b.rows[-1]], km_pullout=b.km_pullout, km_conexion=b.km_conn,
            km_traslado_carga=b.km_carga, km_pullin=b.km_pullin, km_vacios_total=km_vac,
            kwh_consumidos=b.kwh_exp + km_vac * c, kwh_cargados=b.cargado, n_cargas_intermedias=b.n_inter,
            espera_parado_min=b.idle_min, espera_cola_min=b.cola_min, kwh_deficit=b.deficit, ciclo_cumplido=b.ciclo_ok,
            retraso_ciclo_min=b.retraso_ciclo))
    jornadas = pd.DataFrame(filas_j)

    ev = pd.DataFrame(sim.eventos)
    ev["jornada_id"] = ev["jornada_id"].astype(str)
    ev["terminal"] = ev["term"].map(lambda t: sim.term_nombre[t])
    ev["patio"] = ev["patio"].map(lambda p: nombre_patio[p] if p >= 0 else "")
    ev["hora_inicio"] = ev["t_inicio"].map(hora)
    ev["hora_fin"] = ev["t_fin"].map(hora)
    ev["soc_antes_pct"] = ev["soc_antes"] / costos.battery_kwh * 100
    ev["soc_despues_pct"] = ev["soc_despues"] / costos.battery_kwh * 100
    ev = ev[["jornada_id", "terminal", "patio", "tipo", "t_llegada", "t_inicio", "t_fin", "hora_inicio", "hora_fin",
             "espera_cola_min", "kwh", "costo_energia_usd", "soc_antes_pct", "soc_despues_pct", "fragmentada",
             "ciclo_cumplido", "retraso_ciclo_min"]].round(3)

    filas_v = []
    for b in sorted(buses, key=lambda b: (int(b.origen), b.parte)):
        for i, w in enumerate(sorted(b.ventanas, key=lambda w: w["t_ini"]), start=1):
            filas_v.append(dict(jornada_id=b.jid, orden=i, terminal=sim.term_nombre[w["term"]], tipo=w["tipo"],
                                t_ini=w["t_ini"], t_fin=w["t_fin"], t_ini_mod24=w["t_ini"] % DIA_MIN,
                                t_fin_mod24=w["t_fin"] % DIA_MIN,
                                kwh_consumidos_desde_ventana_anterior=w["kwh_consumidos_desde_ventana_anterior"]))
    ventanas = pd.DataFrame(filas_v).round(3)

    filas_o = []
    for t, occ in enumerate(sim.occ):
        filas_o.append(pd.DataFrame({"minuto": np.arange(DIA_MIN), "terminal": sim.term_nombre[t],
                                     "buses_cargando": occ, "puestos": sim.kappa[t]}))
    ocupacion = pd.concat(filas_o, ignore_index=True)

    if escribir:
        sufijo = f"{etq}_soc{soc_pct}"
        jornadas.round(3).to_csv(TABLAS / f"jornadas_{sufijo}.csv", index=False, sep=CSV_SEP)
        ev.to_csv(TABLAS / f"eventos_{sufijo}.csv", index=False, sep=CSV_SEP)
        ventanas.to_csv(TABLAS / f"ventanas_{sufijo}.csv", index=False, sep=CSV_SEP)
        ocupacion.to_csv(TABLAS / f"ocupacion_{sufijo}.csv", index=False, sep=CSV_SEP)
    return jornadas, ev, ventanas, ocupacion


def graficar_ocupacion(sim, path_png, titulo):
    n = len(sim.term_patios)
    fig, axs = plt.subplots(n, 1, figsize=(11, 2.3 * n + 1), sharex=True)
    axs = np.atleast_1d(axs)
    horas = np.arange(DIA_MIN) / 60
    precio = sim.tarifa
    for t, ax in enumerate(axs):
        pico = precio >= precio.max() - 1e-9
        ax.fill_between(horas, 0, sim.kappa[t] * 1.15, where=pico, color="#d95f02", alpha=0.10, step="post", linewidth=0)
        ax.plot(horas, sim.occ[t], color="#2c6e8f", linewidth=1.3, drawstyle="steps-post")
        ax.axhline(sim.kappa[t], color="#b22222", linestyle="--", linewidth=1)
        ax.set_ylim(0, sim.kappa[t] * 1.15)
        ax.set_ylabel("buses")
        ax.set_title(f"{sim.term_nombre[t]} ({sim.kappa[t]} puestos)", fontsize=9, loc="left")
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", linewidth=0.7)
    axs[-1].set_xlabel("Hora del dia (la carga que cruza medianoche vuelve al inicio; sombreado = tarifa punta)")
    axs[-1].set_xlim(0, 24)
    axs[-1].set_xticks(range(0, 25, 2))
    fig.suptitle(titulo, fontsize=11)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_soc(buses, costos, soc, path_png, titulo):
    sin = [b for b in buses if b.n_inter == 0 and b.parte == 0]
    con1 = [b for b in buses if b.n_inter == 1 and b.parte == 0]
    con2 = [b for b in buses if b.n_inter >= 2 and b.parte == 0]
    part = [b for b in buses if b.parte >= 1]
    elegidos = []
    if sin:
        elegidos.append((max(sin, key=lambda b: b.kwh_exp), "sin recarga intermedia"))
    if con1:
        elegidos.append((max(con1, key=lambda b: b.kwh_exp), "con una recarga intermedia"))
    if part:
        origen = part[0].origen
        elegidos.append(([b for b in buses if b.origen == origen and b.parte == 0][0], "jornada que se parte (primera parte)"))
    elif con2:
        elegidos.append((max(con2, key=lambda b: b.n_inter), "con varias recargas intermedias"))
    fig, axs = plt.subplots(len(elegidos), 1, figsize=(11, 2.9 * len(elegidos) + 0.5), sharex=False)
    axs = np.atleast_1d(axs)
    for ax, (b, etiqueta) in zip(axs, elegidos):
        tr = sorted(b.trace)
        t = np.array([p[0] for p in tr]) / 60
        s = np.array([p[1] for p in tr]) / costos.battery_kwh * 100
        ax.plot(t, s, color="#2c6e8f", linewidth=1.6, marker="o", markersize=2.5)
        ax.axhline(costos.min_soc * 100, color="#b22222", linestyle="--", linewidth=1)
        ax.axhline(soc * 100, color="#4a8f6e", linestyle=":", linewidth=1)
        ax.set_ylim(0, 105)
        ax.set_ylabel("SOC (%)")
        ax.set_title(f"Jornada {b.jid}: {etiqueta} ({len(b.rows)} expediciones, {b.n_inter} recargas intermedias)",
                     fontsize=9, loc="left")
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", linewidth=0.7)
    axs[-1].set_xlabel("Hora (h desde las 00:00; rojo = minimo, verde = nivel de partida y tope)")
    fig.suptitle(titulo, fontsize=11)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def resumen_fila(sim, buses, jornadas, ev, costos, etq, soc_pct, n_vsp, op_vsp):
    c = sim.consumo
    ev_i = ev[ev["tipo"] == "intermedia"]
    ev_f = ev[ev["tipo"] == "final"]
    # totales sobre los eventos SIN redondear (los CSV de salida se redondean a 3 decimales)
    kwh_cons = sum(b.kwh_exp + (b.km_pullout + b.km_conn + b.km_carga + b.km_pullin) * c for b in buses)
    kwh_carg = sum(e["kwh"] for e in sim.eventos)
    kwh_def = sum(b.deficit for b in buses)
    energia = sum(e["costo_energia_usd"] for e in sim.eventos)
    km_vac = jornadas["km_vacios_total"].sum()
    espera_min = jornadas["espera_parado_min"].sum() + jornadas["espera_cola_min"].sum()
    flota = len(buses) * costos.vehicle_fixed_cost
    c_km = km_vac * costos.cost_per_km
    c_esp = espera_min * costos.waiting_cost_per_min
    c_ev = len(ev) * costos.fixed_charge_cost
    n_reserva = int((~jornadas["ciclo_cumplido"]).sum())
    c_reserva = n_reserva * costos.vehicle_fixed_cost
    total_sin_reservas = flota + c_km + c_esp + energia + c_ev
    total = total_sin_reservas + c_reserva
    retraso_max = float(np.nanmax(jornadas["retraso_ciclo_min"].values)) if jornadas["retraso_ciclo_min"].notna().any() else 0.0
    factible = bool(kwh_def < 1e-6 and retraso_max < DIA_MIN)
    valle = sim.tarifa <= sim.tarifa.min() * 1.2
    e_dia = sim.kwh_dia
    fila = dict(
        escenario=etq, soc_pct=soc_pct, buses_vsp=n_vsp, buses_final=len(buses),
        jornadas_partidas=int((jornadas["parte"] > 0).sum()), por_sin_hueco=sim.n_particiones["sin_hueco"],
        por_sin_puesto=sim.n_particiones["sin_puesto"],
        jornadas_con_recarga_intermedia=int((jornadas["n_cargas_intermedias"] > 0).sum()),
        pct_jornadas_con_recarga_intermedia=round((jornadas["n_cargas_intermedias"] > 0).mean() * 100, 2),
        eventos_intermedios=len(ev_i), eventos_finales=len(ev_f), eventos_total=len(ev),
        ciclos_no_cumplidos=int((~jornadas["ciclo_cumplido"]).sum()),
        retraso_ciclo_max_min=round(float(np.nanmax(jornadas["retraso_ciclo_min"].values)) if jornadas["retraso_ciclo_min"].notna().any() else 0.0, 1), cargas_fragmentadas=sim.n_fragmentadas,
        espera_cola_h=round(jornadas["espera_cola_min"].sum() / 60, 1),
        espera_cola_max_min=round(ev["espera_cola_min"].max(), 1),
        eventos_con_cola=int((ev["espera_cola_min"] > 1.0).sum()),   # esperas > 1 min (la carga parte en minutos enteros)
        kwh_consumidos=round(kwh_cons, 1), kwh_cargados=round(kwh_carg, 1), kwh_deficit=round(kwh_def, 1),
        pct_deficit=round(kwh_def / kwh_cons * 100, 2), buses_con_deficit=int(sum(b.deficit > EPS for b in buses)),
        buses_sin_ningun_puesto=sim.n_sin_cupo, balance_error_kwh=round(kwh_carg + kwh_def - kwh_cons, 6),
        km_traslado_carga=round(jornadas["km_traslado_carga"].sum(), 1), km_vacios_total=round(km_vac, 1),
        costo_flota_usd=round(flota), costo_km_vacios_usd=round(c_km), costo_espera_usd=round(c_esp),
        costo_energia_usd=round(energia), costo_eventos_usd=round(c_ev),
        buses_reserva=n_reserva, buses_totales=len(buses) + n_reserva, costo_reservas_usd=round(c_reserva),
        costo_sin_reservas_usd=round(total_sin_reservas), factible=int(factible), cota_lp_pct=np.nan,
        costo_total_usd=round(total),
        costo_vsp_operacion_usd=op_vsp, costo_medio_energia_usd_kwh=round(energia / kwh_carg, 4),
        pct_energia_valle=round(e_dia[valle].sum() / e_dia.sum() * 100, 2),
    )
    for t, nom in enumerate(sim.term_nombre):
        occ = sim.occ[t]
        clave = nom.replace(" + ", "_").replace(" ", "_")
        fila[f"uso_max_{clave}_pct"] = round(occ.max() / sim.kappa[t] * 100, 1)
        fila[f"min_saturados_{clave}"] = int((occ >= sim.kappa[t]).sum())
    return fila


def actualizar_resumen(fila):
    path = TABLAS / "resumen_carga.csv"
    nueva = pd.DataFrame([fila])
    if path.exists():
        prev = pd.read_csv(path, sep=CSV_SEP)
        prev = prev[~((prev["escenario"] == fila["escenario"]) & (prev["soc_pct"] == fila["soc_pct"]))]
        nueva = pd.concat([prev, nueva], ignore_index=True)
    nueva.to_csv(path, index=False, sep=CSV_SEP)


def escribir_reporte(sim, fila, ev, jornadas, costos, sufijo, soc, vsp_pct):
    nombre = sim.term_nombre
    uso = []
    for t, nom in enumerate(nombre):
        occ = sim.occ[t]
        uso.append({"terminal": nom, "puestos": sim.kappa[t], "maximo_simultaneo": int(occ.max()),
                    "uso_maximo_pct": round(occ.max() / sim.kappa[t] * 100, 1),
                    "minutos_saturados_al_dia": int((occ >= sim.kappa[t]).sum()),
                    "uso_promedio_pct": round(occ.mean() / sim.kappa[t] * 100, 1)})
    uso = pd.DataFrame(uso)
    por_tipo = ev.groupby("tipo").agg(eventos=("kwh", "size"), kwh=("kwh", "sum"), costo_usd=("costo_energia_usd", "sum"),
                                      espera_media_min=("espera_cola_min", "mean"), espera_max_min=("espera_cola_min", "max")).round(2)
    lineas = [
        f"# Reporte Etapa 3 - Carga reactiva, escenario {fila['escenario']}, nivel {fila['soc_pct']}%",
        "",
        f"Politica miope sobre las jornadas del VSP (escenario {fila['escenario']}). Nivel de partida, de llegada y tope de "
        f"carga: {fila['soc_pct']}% (energia utilizable {costos.bateria_util_ciclica_kwh(soc):.0f} kWh). Carga parcial "
        "cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.",
        "",
        "## Resultado",
        "",
        f"- **Buses:** {fila['buses_vsp']:,} en el VSP -> **{fila['buses_final']:,}** tras la carga "
        f"(+{fila['buses_final'] - fila['buses_vsp']:,}; {fila['jornadas_partidas']:,} jornadas partidas: "
        f"{fila['por_sin_hueco']:,} por falta de hueco, {fila['por_sin_puesto']:,} por falta de puesto).",
        f"- **Recargas intermedias:** {fila['eventos_intermedios']:,} eventos en {fila['jornadas_con_recarga_intermedia']:,} jornadas "
        f"({fila['pct_jornadas_con_recarga_intermedia']:.1f}% de las jornadas finales; el VSP estimaba "
        f"{vsp_pct:.1f}% con energia sobre la bateria util).",
        f"- **Cargas finales:** {fila['eventos_finales']:,}; **ciclos no cumplidos:** {fila['ciclos_no_cumplidos']:,} "
        f"(retraso maximo {fila['retraso_ciclo_max_min']:.0f} min); cargas fragmentadas por falta de tramo continuo: "
        f"{fila['cargas_fragmentadas']:,}.",
        f"- **Colas:** {fila['eventos_con_cola']:,} eventos esperaron mas de 1 min por un puesto (maximo {fila['espera_cola_max_min']:.0f} min; "
        f"{fila['espera_cola_h']:,.1f} h en total).",
        f"- **Energia:** {fila['kwh_cargados'] / 1000:,.1f} MWh cargados = {fila['kwh_consumidos'] / 1000:,.1f} MWh consumidos "
        f"(diferencia {fila['balance_error_kwh']:.2e} kWh). Costo {fila['costo_energia_usd']:,.0f} USD, "
        f"{fila['costo_medio_energia_usd_kwh']:.4f} USD/kWh, {fila['pct_energia_valle']:.1f}% en valle (P1 y P6).",
        f"- **Km sin pasajeros por ir a cargar:** {fila['km_traslado_carga']:,.0f} km (de {fila['km_vacios_total']:,.0f} km vacios).",
        "",
        "## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)",
        "",
        f"| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {fila['costo_flota_usd']:,} | {fila['costo_km_vacios_usd']:,} | {fila['costo_espera_usd']:,} | "
        f"{fila['costo_energia_usd']:,} | {fila['costo_eventos_usd']:,} | {fila['costo_reservas_usd']:,} | "
        f"**{fila['costo_total_usd']:,}** | {fila['costo_vsp_operacion_usd']:,.0f} |",
        "",
        f"- **Factibilidad:** {'FACTIBLE' if fila['factible'] else 'INFACTIBLE'} "
        f"(deficit de energia {fila['kwh_deficit'] / 1000:.1f} MWh; atraso maximo de carga {fila['retraso_ciclo_max_min']:.0f} min). "
        f"Los {fila['buses_reserva']:,} ciclos no cumplidos se cubren con buses de reserva ({fila['costo_reservas_usd']:,} USD/dia); "
        f"costo sin reservas: {fila['costo_sin_reservas_usd']:,} USD/dia.",
        "",
        "## Eventos de carga por tipo",
        "",
        por_tipo.to_markdown(),
        "",
        "## Uso de los puestos por electroterminal (modulo 24 h)",
        "",
        uso.to_markdown(index=False),
        "",
        "## Como leerlo",
        "- La politica es reactiva: no mira tarifa ni el futuro. El costo de energia de esta tabla es lo que el MILP "
        "(Etapa 4) debe mejorar.",
        "- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.",
        "- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia "
        "siguiente; la energia se carga igual (el balance cierra).",
        "",
        "## Archivos (`tablas/` y `graficos/`)",
        f"- `tablas/eventos_{sufijo}.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).",
        f"- `tablas/ventanas_{sufijo}.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la "
        "energia consumida desde la ventana anterior (insumo del MILP, Bloque E). t_fin de la ventana final = primera salida del dia siguiente.",
        f"- `tablas/jornadas_{sufijo}.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.",
        f"- `tablas/ocupacion_{sufijo}.csv`: buses cargando por minuto (modulo 24 h) y terminal.",
        "- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).",
        f"- `graficos/ocupacion_{sufijo}.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.",
        f"- `graficos/soc_ejemplo_{sufijo}.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).",
    ]
    (RESULTS / f"reporte_{sufijo}.md").write_text("\n".join(lineas), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--escenario", required=True, help="Etiqueta del escenario del VSP (E0, E1, E0_sep, E1_sep, E1_C2, E1_C2_sep).")
    parser.add_argument("--soc", type=float, default=1.0, help="Nivel de partida, llegada y tope de carga (0-1).")
    parser.add_argument("--jornadas", type=str, default=None,
                        help="CSV de jornadas (default data-processed/jornadas_<escenario>.csv).")
    parser.add_argument("--unir-electroterminales", nargs="*", default=None, metavar="DEPOT_ID",
                        help="Los depot_id que forman un solo terminal (default: los de la columna `unir` del resumen del VSP).")
    parser.add_argument("--traza", nargs="*", default=[], help="Ids de jornada cuyo SOC paso a paso se imprime.")
    parser.add_argument("--cota-lp", action="store_true",
                        help="Calcula ademas la cota LP: maximo de energia de las cargas finales que cabe en las "
                             "ventanas de los buses (columna cota_lp_pct del resumen). Agrega ~30-60 s.")
    parser.add_argument("--solo-resumen", action="store_true",
                        help="Solo escribe la fila de resumen_carga.csv (sin tablas, graficos ni reporte). Lo usa el "
                             "barrido de niveles (scripts/13-barrido_niveles.py) para no escribir ~4 MB por corrida.")
    args = parser.parse_args()

    etq = args.escenario
    soc_pct = round(args.soc * 100)
    sufijo = f"{etq}_soc{soc_pct}"
    # El terminal unido se lee de la corrida del VSP (columna `unir` de resumen_escenarios.csv), asi el simulador
    # carga con exactamente la misma configuracion con que se armaron las jornadas. --unir-electroterminales la fuerza.
    unir_ids = []
    if args.unir_electroterminales is not None:
        unir_ids = [str(d) for d in (args.unir_electroterminales or parametros.ELECTROTERMINALES_UNIDOS)]
    else:
        path_resumen = TABLAS_VSP / "resumen_escenarios.csv"
        if path_resumen.exists():
            rv = pd.read_csv(path_resumen, sep=CSV_SEP, dtype={"unir": str}).set_index("etiqueta")
            if etq in rv.index and isinstance(rv.loc[etq, "unir"], str) and rv.loc[etq, "unir"].strip():
                unir_ids = [d.strip() for d in rv.loc[etq, "unir"].split(",")]

    print(f"=== ETAPA 3: carga reactiva (escenario={etq}, nivel={soc_pct}%) ===\n")
    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    ex_ids = ex["expedicion_id"].tolist()
    ex_idx = {e: i for i, e in enumerate(ex_ids)}
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    costos = parametros.cargar_costos()
    tarifa = cargar_tarifa()
    path_j = Path(args.jornadas) if args.jornadas else DATA_PROCESSED / f"jornadas_{etq}.csv"
    j = pd.read_csv(path_j, sep=CSV_SEP, dtype={"depot_salida": str, "depot_llegada": str})
    print(f"  Jornadas del VSP: {len(j):,} ({path_j.name}) | terminal unido: {unir_ids if unir_ids else 'no'}")

    sim = Simulador(ex, depots, costos, args.soc, unir_ids, tarifa, set(args.traza))
    sim.kwh_dia = np.zeros(DIA_MIN)
    costo_orig = sim.costo_energia

    def costo_y_acumular(minutos, kwh_total):
        m = np.asarray(minutos)
        e = np.full(len(m), sim.kwh_min)
        e[-1] = kwh_total - sim.kwh_min * (len(m) - 1)
        np.add.at(sim.kwh_dia, m % DIA_MIN, e)
        return costo_orig(minutos, kwh_total)
    sim.costo_energia = costo_y_acumular

    buses = construir_buses(sim, j, ex_idx)
    resumen_vsp = TABLAS_VSP / "resumen_escenarios.csv"
    esperada_h, op_vsp = None, np.nan
    if resumen_vsp.exists():
        r = pd.read_csv(resumen_vsp, sep=CSV_SEP).set_index("etiqueta")
        if etq in r.index:
            esperada_h, op_vsp = float(r.loc[etq, "espera_h"]), float(r.loc[etq, "cost_operacion_usd"])
    validar_reconstruccion(sim, j, buses, esperada_h)
    vsp_pct = float((j["kwh_total"] > costos.bateria_util_ciclica_kwh(args.soc)).mean() * 100)

    print("\n--- Simulando la politica reactiva ---")
    sim.correr(buses)
    finales = sim.buses_terminados
    print(f"  Jornadas simuladas: {len(finales):,} (VSP: {len(buses):,}) | particiones: {sim.n_particiones}")

    # --- Chequeos de sanidad ---
    cubiertas = [ex_ids[r] for b in finales for r in b.rows]
    todas = {e for ids in j["expedicion_ids"] for e in ids.split(";")}
    assert len(cubiertas) == len(set(cubiertas)) == len(todas) and set(cubiertas) == todas, \
        "Cobertura rota tras las particiones: alguna expedicion quedo sin cubrir o cubierta dos veces."
    for b in finales:
        smin_obs = min(p[1] for p in b.trace)
        smax_obs = max(p[1] for p in b.trace)
        assert smin_obs >= sim.smin - 1e-6, f"Jornada {b.jid}: SOC {smin_obs:.2f} kWh bajo el minimo {sim.smin:.2f}."
        assert smax_obs <= sim.L + 1e-6, f"Jornada {b.jid}: SOC {smax_obs:.2f} kWh sobre el tope {sim.L:.2f}."
        consumido = (b.km_pullout + b.km_conn + b.km_carga + b.km_pullin) * sim.consumo + b.kwh_exp
        assert abs(b.cargado + b.deficit - consumido) < 1e-4, (
            f"Balance de energia roto en la jornada {b.jid}: cargo {b.cargado:.4f} kWh (+ deficit {b.deficit:.4f}) y consumio {consumido:.4f} kWh.")
    for t in range(len(sim.occ)):
        assert sim.occ[t].max() <= sim.kappa[t], f"Ocupacion sobre los puestos en {sim.term_nombre[t]}."
    print("  [OK] Cobertura intacta | SOC entre minimo y tope | balance de energia por jornada | ocupacion <= puestos.")

    jornadas, ev, ventanas, ocupacion = tablas_salida(sim, finales, ex, ex_ids, depots, costos, etq, soc_pct,
                                                      escribir=not args.solo_resumen)
    fila = resumen_fila(sim, finales, jornadas, ev, costos, etq, soc_pct, len(buses), op_vsp)
    assert abs(fila["balance_error_kwh"]) < 1e-3, f"Balance global roto: {fila['balance_error_kwh']} kWh."
    if args.cota_lp:
        cargable, necesaria = cota_carga_lp(sim, finales)
        fila["cota_lp_pct"] = round(cargable / necesaria * 100, 2)
        fila["cota_lp_faltante_mwh"] = round((necesaria - cargable) / 1000, 1)
        print(f"  Cota LP: caben {cargable / 1000:,.1f} MWh de {necesaria / 1000:,.1f} MWh de carga final "
              f"({fila['cota_lp_pct']:.1f}%) dentro de las ventanas de los buses.")
    actualizar_resumen(fila)
    if args.solo_resumen:
        print(f"  -> {TABLAS / 'resumen_carga.csv'} (solo la fila de resumen)")
    else:
        graficar_ocupacion(sim, GRAFICOS / f"ocupacion_{sufijo}.png",
                           f"Buses cargando por electroterminal - {etq}, nivel {soc_pct}% (politica reactiva)")
        graficar_soc(finales, costos, args.soc, GRAFICOS / f"soc_ejemplo_{sufijo}.png",
                     f"SOC de jornadas reales - {etq}, nivel {soc_pct}% (politica reactiva)")
        escribir_reporte(sim, fila, ev, jornadas, costos, sufijo, args.soc, vsp_pct)
        print(f"  -> {TABLAS}/ (jornadas, eventos, ventanas, ocupacion, resumen_carga)")
        print(f"  -> {GRAFICOS}/ (ocupacion, soc_ejemplo) | {RESULTS / f'reporte_{sufijo}.md'}")

    print("\n=== Resultado ===")
    for k in ("buses_vsp", "buses_final", "jornadas_partidas", "por_sin_hueco", "por_sin_puesto",
              "pct_jornadas_con_recarga_intermedia", "eventos_intermedios", "eventos_finales", "ciclos_no_cumplidos",
              "retraso_ciclo_max_min", "cargas_fragmentadas", "espera_cola_h", "espera_cola_max_min", "kwh_cargados",
              "costo_energia_usd", "costo_medio_energia_usd_kwh", "pct_energia_valle", "buses_reserva",
              "costo_reservas_usd", "costo_sin_reservas_usd", "costo_total_usd", "factible", "cota_lp_pct",
              "costo_vsp_operacion_usd"):
        print(f"  {k:38s} {fila[k]:,}" if isinstance(fila[k], (int, float, np.integer, np.floating)) and not isinstance(fila[k], str) else f"  {k:38s} {fila[k]}")
    for t, nom in enumerate(sim.term_nombre):
        clave = nom.replace(" + ", "_").replace(" ", "_")
        print(f"  uso maximo {nom:28s} {fila[f'uso_max_{clave}_pct']:5.1f}% | minutos saturados al dia: {fila[f'min_saturados_{clave}']}")

    for b in sorted(finales, key=lambda b: (int(b.origen), b.parte)):
        if b.log:
            print(f"\n--- Traza de la jornada {b.jid} ---")
            print("\n".join(b.log))
    print("\n=== FIN ETAPA 3 (carga reactiva) ===")


TABLAS_VSP = RESULTS_DIR / "etapa2_vsp" / "tablas"

if __name__ == "__main__":
    main()
