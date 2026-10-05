"""
Comparacion de KPIs de los escenarios - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md, seccion 6, y docs/context/05_plan_entrega2.md, Bloque F).

No corre ningun modelo: lee los resultados de las Etapas 2, 3 y 4 y arma la tabla de KPIs de E0 (caso base, por linea),
E1 (+ interlining, configuracion propuesta) y LB (cota inferior, NO operacional: solo tiene VSP, sin carga), con el desglose
de costo, el precio de la descomposicion y, aparte y rotulado "instancia reducida", el valor del MILP de carga.

KPIs (cada uno ligado a una decision):
  costo total y desglose (flota, km vacios, espera entre viajes, espera por puesto en el patio, energia, eventos, reservas),
  buses (VSP, tras la carga, reservas; brecha contra la cota 6.539 y contra LB), % de km vacios, costo medio de la energia y
  % cargado en valle, uso de cada electroterminal, utilizacion del bus, jornadas partidas, ciclos no cumplidos,
  precio de la descomposicion (VSP frente a LB; bateria frente al VSP).

La espera se separa en dos: entre viajes (la cobra el VSP) y por puesto en el patio (buses estacionados esperando cargar; solo
la cobra el simulador). La fila "total sin espera por puesto" es una sensibilidad: ver docs/context/02, B12.

Input:  results/etapa2_vsp/tablas/resumen_escenarios.csv, data-processed/{expediciones,jornadas_E0,jornadas_E1,jornadas_LB}.csv,
        results/etapa3_carga_reactiva/tablas/{resumen_carga,jornadas_<esc>_soc100,ocupacion_<esc>_soc100}.csv,
        results/etapa4_milp_carga/tablas/{comparacion_reactiva_milp,tiempos_resolucion,instancias}.csv
Output: results/etapa5_kpis_comparacion/tablas/{kpis_escenarios,desglose_costo,precio_descomposicion,uso_electroterminales,
            milp_instancia}.csv
        results/etapa5_kpis_comparacion/graficos/{costo_desglose_E0_E1,flota_de_donde_viene,uso_electroterminales}.png
        results/etapa5_kpis_comparacion/reporte.md

Uso:
    python scripts/12-kpis_comparacion.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parametros                                                   # noqa: E402
from common.rutas import DATA_PROCESSED, CSV_SEP, RESULTS_DIR, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa5_kpis_comparacion")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)
R2 = RESULTS_DIR / "etapa2_vsp" / "tablas"
R3 = RESULTS_DIR / "etapa3_carga_reactiva" / "tablas"
R4 = RESULTS_DIR / "etapa4_milp_carga" / "tablas"

COTA_BUSES = 6539                  # concurrencia maxima (Etapa 0)
ESC = ["E0", "E1"]
NOMBRE = {"E0": "E0 (por linea)", "E1": "E1 (+ interlining)", "LB": "LB (cota, no operacional)"}
COLORES = {"flota": "#2c6e8f", "km": "#e6ab02", "espera_viajes": "#9aa5ad", "espera_patio": "#6b6b6b",
           "energia": "#4a8f6e", "eventos": "#d95f02", "reservas": "#b22222"}


def estilo(ax, eje="y"):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis=eje, color="#e5e5e5", linewidth=0.7)
    ax.set_axisbelow(True)


def fmt(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #

def cargar():
    vsp = pd.read_csv(R2 / "resumen_escenarios.csv", sep=CSV_SEP).set_index("etiqueta")
    car = pd.read_csv(R3 / "resumen_carga.csv", sep=CSV_SEP)
    car = car[(car["soc_pct"] == 100) & car["escenario"].isin(ESC)].set_index("escenario")
    assert set(ESC) <= set(vsp.index) and set(ESC) == set(car.index), "Faltan corridas de la Etapa 2 o 3 (E0, E1, LB al nivel 100%)."
    return vsp, car


def utilizacion(jornadas, ex, km_vacios_ini="km_pullout", km_fin="km_pullin", dep_ini="dep_min"):
    """Horas con pasajeros / horas de la jornada (del electroterminal al electroterminal), agregado y promedio por jornada."""
    dur_ex = (ex["arr_min"] - ex["dep_min"]).values
    idx = {e: i for i, e in enumerate(ex["expedicion_id"].tolist())}
    com = np.array([dur_ex[[idx[e] for e in s.split(";")]].sum() for s in jornadas["expedicion_ids"]])
    v, lay = parametros.VELOCIDAD_KMH, parametros.LAYOVER_MIN
    salida = jornadas[dep_ini] - lay - jornadas[km_vacios_ini] / v * 60
    llegada = jornadas["arr_min"] + jornadas[km_fin] / v * 60
    dur = (llegada - salida).values
    assert (dur > 0).all() and (com <= dur + 1e-6).all(), "Utilizacion invalida: tiempo con pasajeros mayor que la jornada."
    return com.sum() / dur.sum() * 100, float((com / dur).mean() * 100)


def kpis(vsp, car, ex):
    filas = {}
    for e in ESC + ["LB"]:
        v = vsp.loc[e]
        f = dict(escenario=NOMBRE[e], buses_vsp=int(v["buses"]), brecha_buses_vs_cota_pct=round((v["buses"] / COTA_BUSES - 1) * 100, 1),
                 brecha_buses_vs_LB_pct=round((v["buses"] / vsp.loc["LB", "buses"] - 1) * 100, 1),
                 pct_km_vacios_vsp=round(v["pct_km_vacios"], 2), costo_operacion_vsp_usd=round(v["cost_operacion_usd"]))
        j = pd.read_csv(DATA_PROCESSED / f"jornadas_{e}.csv", sep=CSV_SEP)
        u_agg, u_prom = utilizacion(j, ex)
        f.update(utilizacion_vsp_agregada_pct=round(u_agg, 1), utilizacion_vsp_promedio_jornada_pct=round(u_prom, 1))
        if e in ESC:
            c = car.loc[e]
            cola = c["espera_cola_h"] * 60 * _costo_espera_min()
            espera_viajes = c["costo_espera_usd"] - cola
            total = c["costo_total_usd"]
            sumas = (c["costo_flota_usd"] + c["costo_km_vacios_usd"] + c["costo_espera_usd"] + c["costo_energia_usd"]
                     + c["costo_eventos_usd"] + c["costo_reservas_usd"])
            assert abs(sumas - total) < 2, f"{e}: el desglose ({sumas:,.0f}) no suma el costo total del simulador ({total:,.0f})."
            assert c["buses_vsp"] == v["buses"], f"{e}: los buses del VSP no coinciden entre las Etapas 2 y 3."
            jj = pd.read_csv(R3 / f"jornadas_{e}_soc100.csv", sep=CSV_SEP)
            ua, up = utilizacion(jj, ex, km_vacios_ini="km_pullout", km_fin="km_pullin", dep_ini="dep_min")
            f.update(
                buses_tras_carga=int(c["buses_final"]), jornadas_partidas=int(c["jornadas_partidas"]), buses_reserva=int(c["buses_reserva"]),
                buses_totales=int(c["buses_totales"]), ciclos_no_cumplidos=int(c["ciclos_no_cumplidos"]),
                recargas_intermedias=int(c["eventos_intermedios"]), pct_jornadas_con_recarga_intermedia=c["pct_jornadas_con_recarga_intermedia"],
                pct_km_vacios_tras_carga=round(c["km_vacios_total"] / (c["km_vacios_total"] + v["km_comercial"]) * 100, 2),
                costo_flota_usd=c["costo_flota_usd"], costo_km_vacios_usd=c["costo_km_vacios_usd"],
                costo_espera_entre_viajes_usd=round(espera_viajes), costo_espera_por_puesto_usd=round(cola),
                costo_energia_usd=c["costo_energia_usd"], costo_eventos_usd=c["costo_eventos_usd"], costo_reservas_usd=c["costo_reservas_usd"],
                costo_total_usd=total, costo_total_sin_espera_por_puesto_usd=round(total - cola),
                costo_medio_energia_usd_kwh=c["costo_medio_energia_usd_kwh"], pct_energia_en_valle=c["pct_energia_valle"],
                energia_mwh=round(c["kwh_cargados"] / 1000, 1), factible=int(c["factible"]), cota_lp_pct=c["cota_lp_pct"],
                utilizacion_tras_carga_agregada_pct=round(ua, 1), utilizacion_tras_carga_promedio_jornada_pct=round(up, 1))
        filas[e] = f
    return pd.DataFrame(filas).T.set_index("escenario").T


def _costo_espera_min():
    return parametros.cargar_costos().waiting_cost_per_min


def precio_descomposicion(vsp, car):
    filas = []
    e1, lb, e0 = vsp.loc["E1"], vsp.loc["LB"], vsp.loc["E0"]
    filas.append(dict(concepto="Descomposicion: E1 frente a LB (VSP, exigir retorno al electroterminal y limitar el interlining)",
                      buses=int(e1["buses"] - lb["buses"]), buses_pct=round((e1["buses"] / lb["buses"] - 1) * 100, 1),
                      costo_usd=round(e1["cost_operacion_usd"] - lb["cost_operacion_usd"]),
                      costo_pct=round((e1["cost_operacion_usd"] / lb["cost_operacion_usd"] - 1) * 100, 1)))
    filas.append(dict(concepto="Interlining: E0 frente a E1 (VSP)", buses=int(e0["buses"] - e1["buses"]),
                      buses_pct=round((e0["buses"] / e1["buses"] - 1) * 100, 1),
                      costo_usd=round(e0["cost_operacion_usd"] - e1["cost_operacion_usd"]),
                      costo_pct=round((e0["cost_operacion_usd"] / e1["cost_operacion_usd"] - 1) * 100, 1)))
    for e in ESC:
        c, v = car.loc[e], vsp.loc[e]
        extra_buses = int(c["buses_totales"] - v["buses"])
        costo = c["costo_total_usd"] - v["cost_operacion_usd"]
        desglose = ((c["buses_totales"] - v["buses"]) * 250 + (c["costo_km_vacios_usd"] - v["cost_km_vacios_usd"])
                    + (c["costo_espera_usd"] - v["cost_espera_usd"]) + c["costo_energia_usd"] + c["costo_eventos_usd"])
        assert abs(desglose - costo) < 2, f"{e}: el precio de la bateria no cuadra con el desglose."
        filas.append(dict(concepto=f"Bateria: {e} tras la carga frente a su VSP (jornadas partidas {int(c['jornadas_partidas'])} + reservas {int(c['buses_reserva'])})",
                          buses=extra_buses, buses_pct=round(extra_buses / v["buses"] * 100, 1), costo_usd=round(costo),
                          costo_pct=round(costo / v["cost_operacion_usd"] * 100, 1)))
    return pd.DataFrame(filas)


def uso_electroterminales():
    filas = []
    for e in ESC:
        o = pd.read_csv(R3 / f"ocupacion_{e}_soc100.csv", sep=CSV_SEP)
        for t, g in o.groupby("terminal", sort=False):
            puestos = int(g["puestos"].iloc[0])
            filas.append(dict(escenario=e, terminal=t, puestos=puestos, uso_maximo_pct=round(g["buses_cargando"].max() / puestos * 100, 1),
                              uso_promedio_pct=round(g["buses_cargando"].mean() / puestos * 100, 1),
                              pct_del_dia_saturado=round((g["buses_cargando"] >= puestos).mean() * 100, 1)))
    return pd.DataFrame(filas)


def milp_instancia():
    comp = pd.read_csv(R4 / "comparacion_reactiva_milp.csv", sep=CSV_SEP)
    tiem = pd.read_csv(R4 / "tiempos_resolucion.csv", sep=CSV_SEP).set_index("N_objetivo")
    inst = pd.read_csv(R4 / "instancias.csv", sep=CSV_SEP).set_index("N_objetivo")
    filas = []
    for n in sorted(comp["N_objetivo"].unique()):
        d = comp[comp["N_objetivo"] == n].set_index("variante")
        s, m = d.loc["reactiva_minuto"], d.loc["milp_al_minuto"]
        filas.append(dict(N_objetivo=n, buses=int(s["buses"]), puestos=int(inst.loc[n, "puestos"]),
                          costo_carga_simulador_usd=s["costo_carga_total_usd"], costo_carga_milp_usd=m["costo_carga_total_usd"],
                          ganancia_pct=round((1 - m["costo_carga_total_usd"] / s["costo_carga_total_usd"]) * 100, 1),
                          reservas_simulador=int(s["buses_reserva"]), reservas_milp=int(m["buses_reserva"]), reservas_piso=int(inst.loc[n, "reservas_cota"]),
                          usd_kwh_simulador=s["usd_por_kwh"], usd_kwh_milp=m["usd_por_kwh"], pct_valle_simulador=s["pct_energia_valle"],
                          pct_valle_milp=m["pct_energia_valle"], brecha_pct=tiem.loc[n, "brecha_pct"], resuelta_al_optimo=int(tiem.loc[n, "resuelta_optimo"])))
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Graficos
# --------------------------------------------------------------------------- #

def graficar_desglose(k, path):
    comp = [("costo_flota_usd", "Flota (250 USD/bus)", "flota"), ("costo_km_vacios_usd", "Km sin pasajeros", "km"),
            ("costo_espera_entre_viajes_usd", "Espera entre viajes", "espera_viajes"),
            ("costo_espera_por_puesto_usd", "Espera por puesto en el patio", "espera_patio"),
            ("costo_energia_usd", "Energia", "energia"), ("costo_eventos_usd", "Eventos de carga", "eventos"),
            ("costo_reservas_usd", "Buses de reserva", "reservas")]
    cols = [NOMBRE[e] for e in ESC]
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    base = np.zeros(2)
    for campo, lab, col in comp:
        v = np.array([float(k.loc[campo, c]) for c in cols]) / 1e6
        ax.bar(range(2), v, 0.55, bottom=base, color=COLORES[col], label=lab, edgecolor="white")
        for i in range(2):
            if v[i] > 0.12:
                ax.text(i, base[i] + v[i] / 2, fmt(v[i], 2), ha="center", va="center", fontsize=8, color="white")
        base += v
    for i, t in enumerate(base):
        ax.text(i, t + 0.04, f"{fmt(t, 2)} M USD/dia", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ahorro = (1 - base[1] / base[0]) * 100
    ax.set_xticks(range(2))
    ax.set_xticklabels(cols)
    ax.set_ylabel("Millones de USD por dia")
    ax.set_ylim(0, base.max() * 1.12)
    ax.set_title(f"El interlining baja el costo total {fmt(ahorro, 1)}% (flota: {k.loc['costo_flota_usd', cols[0]] / 1e6 / base[0] * 100:.0f}% del costo de E0)", fontsize=11, loc="left")
    estilo(ax)
    ax.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def graficar_flota(vsp, car, path):
    c = car.loc["E1"]
    etapas = [("Cota: viajes\nsimultaneos", COTA_BUSES, "#9aa5ad"), ("LB\n(no operacional)", vsp.loc["LB", "buses"], "#9aa5ad"),
              ("E1: VSP\n(sin bateria)", vsp.loc["E1", "buses"], COLORES["flota"]),
              ("E1: + jornadas\npartidas por bateria", c["buses_final"], "#4a8f6e"),
              ("E1: + buses de\nreserva (ciclo)", c["buses_totales"], COLORES["reservas"])]
    fig, ax = plt.subplots(figsize=(9.5, 5))
    for i, (lab, v, col) in enumerate(etapas):
        ax.bar(i, v, 0.6, color=col)
        ax.text(i, v + 150, fmt(v), ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xticks(range(len(etapas)))
    ax.set_xticklabels([e[0] for e in etapas], fontsize=9)
    ax.set_ylabel("Buses")
    ax.set_ylim(0, etapas[-1][1] * 1.12)
    extra_bat = c["buses_totales"] - vsp.loc["E1", "buses"]
    extra_clu = vsp.loc["E1", "buses"] - vsp.loc["LB", "buses"]
    ax.set_title(f"La bateria agrega {fmt(extra_bat)} buses a E1; el clustering, solo {fmt(extra_clu)} sobre la cota LB", fontsize=11, loc="left")
    estilo(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def graficar_uso(u, path):
    terms = list(dict.fromkeys(u["terminal"]))
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    x = np.arange(len(terms))
    for ax, campo, tit in ((axs[0], "uso_promedio_pct", "Uso promedio de los puestos en las 24 h"),
                           (axs[1], "pct_del_dia_saturado", "% del dia con todos los puestos ocupados")):
        for k, (e, col) in enumerate((("E0", "#9aa5ad"), ("E1", "#2c6e8f"))):
            d = u[u["escenario"] == e].set_index("terminal").reindex(terms)
            ax.bar(x + (k - 0.5) * 0.38, d[campo].values, 0.38, color=col, label=NOMBRE[e])
            for xi, v in zip(x + (k - 0.5) * 0.38, d[campo].values):
                ax.text(xi, v + 1, f"{v:.0f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([t.replace(" + ", "\n+ ").replace(" ", "\n", 1) if len(t) < 16 else t for t in terms], fontsize=8)
        ax.set_title(tit, fontsize=10, loc="left")
        ax.set_ylim(0, 105)
        estilo(ax)
    axs[0].set_ylabel("%")
    axs[0].legend(frameon=False, fontsize=8, loc="upper left")
    sat = u[u["terminal"] != "Vespucio Norte"]["pct_del_dia_saturado"]
    fig.suptitle(f"Tres de los cuatro electroterminales tienen todos sus puestos ocupados entre {sat.min():.0f}% y {sat.max():.0f}% del dia (nivel 100%)",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Reporte
# --------------------------------------------------------------------------- #

def escribir_reporte(k, desg, prec, uso, milp):
    cols = [NOMBRE[e] for e in ESC]
    e0, e1 = cols
    L = ["# Reporte - KPIs de la escalera de escenarios (E0, E1, LB)", ""]
    L.append("Todos los escenarios operacionales usan C1b y los terminales Los Espinos + Santa Rosa unidos; nivel de bateria 100% con buses de reserva "
             "para la condicion ciclica. **LB es una cota inferior (no operacional)**: solo tiene VSP, sin carga. Cifras en USD por dia.")
    L += ["", "## Tabla de KPIs", "", k.to_markdown(), ""]
    L.append("## Desglose del costo total")
    L += ["", desg.to_markdown(), ""]
    L.append("## Precio de la descomposicion y de cada decision")
    L += ["", prec.to_markdown(index=False), ""]
    L.append("## Uso de los electroterminales (modulo 24 h)")
    L += ["", uso.to_markdown(index=False), ""]
    L.append("## Valor de la carga programada (MILP) - INSTANCIA REDUCIDA, no es el resultado de toda la red")
    L += ["", "Costo de la carga = energia + eventos + reservas, en la instancia (no se suma al total de la red). La ganancia es una cota inferior "
          "(el MILP usa bloques de 15 min y solo N = 10 esta certificada al optimo). Ver `results/etapa4_milp_carga/reporte.md`.", "",
          milp.to_markdown(index=False), ""]
    c0, c1 = k.loc["costo_total_usd", e0], k.loc["costo_total_usd", e1]
    L.append("## Lectura de cada KPI (y si es valido o hay que modificarlo)")
    L += ["",
          f"- **Costo total:** E1 cuesta {fmt(c1)} USD/dia frente a {fmt(c0)} de E0 ({(1 - c1 / c0) * 100:.1f}% menos). La flota es "
          f"{k.loc['costo_flota_usd', e1] / c1 * 100:.0f}% del costo de E1 y las reservas {k.loc['costo_reservas_usd', e1] / c1 * 100:.0f}%; la energia, solo "
          f"{k.loc['costo_energia_usd', e1] / c1 * 100:.0f}%. Valido como objetivo; la energia pesa poco, por eso programar la carga rinde mas por las reservas que por la tarifa.",
          f"- **Buses:** el VSP baja de {fmt(k.loc['buses_vsp', e0])} (E0) a {fmt(k.loc['buses_vsp', e1])} (E1), a {k.loc['brecha_buses_vs_LB_pct', e1]}% de LB; tras la carga, E1 necesita "
          f"{fmt(k.loc['buses_tras_carga', e1])} y con reservas {fmt(k.loc['buses_totales', e1])}. **El KPI \"buses\" del VSP solo no es suficiente**: ignora la bateria; hay que reportar siempre el numero tras la carga.",
          f"- **% km vacios:** {k.loc['pct_km_vacios_vsp', e0]}% (E0) y {k.loc['pct_km_vacios_vsp', e1]}% (E1) en el VSP; sube a {k.loc['pct_km_vacios_tras_carga', e1]}% en E1 tras la carga (traslados de jornadas partidas).",
          f"- **Energia:** {k.loc['costo_medio_energia_usd_kwh', e1]} USD/kWh y {k.loc['pct_energia_en_valle', e1]}% en valle (E1); es la politica reactiva, sin mirar la tarifa.",
          "- **Uso de electroterminales:** el uso maximo es 100% en todos. En Los Espinos + Santa Rosa, El Conquistador y La Reina el uso promedio de las 24 h es 81-88% y los puestos estan todos ocupados "
          "71-79% del dia (la carga nocturna los satura); Vespucio Norte queda holgado (35%, 26% del dia saturado). El KPI util es el % del dia saturado, que mide la congestion; el promedio solo no distingue "
          "un terminal siempre lleno de uno lleno solo de noche. Casi no cambia entre E0 y E1: el interlining no alivia la carga.",
          f"- **Utilizacion del bus:** {k.loc['utilizacion_vsp_agregada_pct', e1]}% de las horas de jornada con pasajeros en el VSP de E1 ({k.loc['utilizacion_tras_carga_agregada_pct', e1]}% tras la carga, que incluye las esperas de carga). Es un KPI descriptivo; no decide nada por si solo.",
          f"- **Jornadas partidas y ciclos no cumplidos:** {fmt(k.loc['jornadas_partidas', e1])} partidas y {fmt(k.loc['ciclos_no_cumplidos', e1])} ciclos no cumplidos en E1: es lo que mide cuanto cuesta la miopia de la politica y de la descomposicion.",
          "- **Espera por puesto en el patio:** el caso base la cobra (0,03 USD/min a buses estacionados esperando puesto) y el VSP no cobra el estacionamiento. Se mantiene como cota conservadora; "
          "la fila \"total sin espera por puesto\" muestra que no cambia ninguna conclusion (decision B12 en `docs/context/02`). Queda como pregunta para el profesor.",
          "- **Precio de la descomposicion:** exigir el retorno al electroterminal y limitar el interlining al grupo cuesta ~4% de flota frente a LB; ignorar la bateria en el VSP cuesta casi 70% de flota. "
          "El segundo es el hallazgo central (C9) y la mejora principal para la entrega final: un VSP que vea la bateria.", ""]
    L.append("## Archivos")
    L += ["", "- `tablas/kpis_escenarios.csv`: tabla de KPIs (columnas E0, E1, LB).", "- `tablas/desglose_costo.csv`: costo total por componente.",
          "- `tablas/precio_descomposicion.csv`: buses y costo de cada decision (interlining, retorno, bateria).",
          "- `tablas/uso_electroterminales.csv`: uso maximo, promedio y % del dia saturado por electroterminal.",
          "- `tablas/milp_instancia.csv`: valor del MILP por tamano de instancia (instancia reducida).",
          "- `graficos/costo_desglose_E0_E1.png`: costo total apilado por componente, E0 frente a E1.",
          "- `graficos/flota_de_donde_viene.png`: de la cota 6.539 a los buses de E1 tras la carga y las reservas.",
          "- `graficos/uso_electroterminales.png`: uso promedio y % del dia saturado por electroterminal."]
    (RESULTS / "reporte.md").write_text("\n".join(L), encoding="utf-8")


def main():
    print("=== KPIs: comparacion de escenarios (E0, E1, LB) ===")
    vsp, car = cargar()
    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    k = kpis(vsp, car, ex)
    assert vsp.loc["E0", "buses"] >= vsp.loc["E1", "buses"] >= vsp.loc["LB", "buses"] >= COTA_BUSES, "Orden de buses E0 >= E1 >= LB >= cota roto."
    for e in ESC:      # ordenes de magnitud (05, Bloque F): flota ~1,9-2,9 M, energia 215.000-470.000 USD/dia
        c = k.loc["costo_energia_usd", NOMBRE[e]]
        assert 215_000 <= c <= 470_000, f"{e}: el costo de energia ({c:,.0f}) sale del orden esperado."
    comp = [i for i in k.index if i.startswith("costo_") and i != "costo_operacion_vsp_usd" and "sin_espera" not in i and i != "costo_total_usd"]
    desg = k.loc[comp + ["costo_total_usd", "costo_total_sin_espera_por_puesto_usd"], [NOMBRE[e] for e in ESC]]
    prec = precio_descomposicion(vsp, car)
    uso = uso_electroterminales()
    milp = milp_instancia()
    k.to_csv(TABLAS / "kpis_escenarios.csv", sep=CSV_SEP)
    desg.to_csv(TABLAS / "desglose_costo.csv", sep=CSV_SEP)
    prec.to_csv(TABLAS / "precio_descomposicion.csv", index=False, sep=CSV_SEP)
    uso.to_csv(TABLAS / "uso_electroterminales.csv", index=False, sep=CSV_SEP)
    milp.to_csv(TABLAS / "milp_instancia.csv", index=False, sep=CSV_SEP)
    graficar_desglose(k, GRAFICOS / "costo_desglose_E0_E1.png")
    graficar_flota(vsp, car, GRAFICOS / "flota_de_donde_viene.png")
    graficar_uso(uso, GRAFICOS / "uso_electroterminales.png")
    escribir_reporte(k.fillna(""), desg, prec, uso, milp)
    print(k.to_string())
    print("\n" + prec.to_string(index=False))
    print(f"\n  [OK] desglose = costo total del simulador | buses de las Etapas 2 y 3 coinciden | E0 >= E1 >= LB >= {COTA_BUSES} | energia en el orden esperado")
    print(f"  -> {TABLAS} | {GRAFICOS} | {RESULTS / 'reporte.md'}")
    print("\n=== FIN KPIs ===")


if __name__ == "__main__":
    main()
