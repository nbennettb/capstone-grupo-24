"""Figuras finales del informe (F0-F6), en PDF (vectorial, para LaTeX) y PNG, cada una con el CSV de sus datos.

Estilo comun: mismo color por escenario en todas (common/graficos.py), textos en espanol con tildes y coma decimal,
unidades en los ejes, leyenda dentro de la figura y sin titulo (el titulo va en el caption de LaTeX). El ancho es el de
0.8\\textwidth (~12,8 cm) y la letra es de 9 pt, asi que al incluirlas a ese ancho la letra queda en 9 pt.
Cada funcion devuelve (archivo, caption propuesto, cifra principal) para el resumen.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

from . import graficos as gr
from .nombres import ESCENARIO

ANCHO_IN = 5.04                      # 0.8 x 16 cm de \textwidth
GRIS_1, GRIS_2 = "#8a8984", "#c3c2b7"
ETIQUETA_X = {"E0": "Caso base", "E1": "Caso base\ncon interlining", "E2-FIFO": "Propuesta,\ncarga por\norden de llegada",
              "E2": "Propuesta\ncompleta"}
CAPAS_COSTO = [("costo_flota", "flota", "#4b4b4b"), ("costo_reservas_intermedias", "reservas diurnas", GRIS_1),
               ("costo_reservas_nocturnas", "reservas nocturnas", GRIS_2), ("costo_km_vacios", "km vacíos", "#6250d6"),
               ("costo_espera_comparable", "espera", "#e87ba4"), ("costo_energia", "energía", "#008300"),
               ("costo_eventos", "eventos de carga", "#e34948")]


def estilo():
    plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
                         "legend.fontsize": 9, "legend.title_fontsize": 9, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "font.family": "DejaVu Sans"})


def num(x, d=0):
    """Numero en espanol: punto de miles y coma decimal."""
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def eje_es(ax, eje="y", d=0):
    f = FuncFormatter(lambda x, _: num(x, d))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def guardar(fig, carpeta, nombre, datos):
    carpeta.mkdir(parents=True, exist_ok=True)
    fig.patch.set_facecolor("white")
    for ext, kw in (("pdf", {}), ("png", {"dpi": 300})):
        gr._escribir(lambda p: fig.savefig(p, bbox_inches="tight", facecolor="white", **kw), carpeta / f"{nombre}.{ext}")
    plt.close(fig)
    gr._escribir(lambda p: datos.to_csv(p, index=False, sep=";"), carpeta / f"{nombre}.csv")


def _ejes(ax, grilla="y"):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(colors=gr.TEXTO_SECUNDARIO)
    if grilla:
        ax.grid(axis=grilla, color=gr.GRILLA, linewidth=0.7)
    ax.set_axisbelow(True)


def _leyenda_abajo(fig, handles, ncol, alto_rel):
    """Leyenda dentro de la imagen, bajo los ejes, para no tapar datos."""
    fig.legend(handles=handles, loc="lower center", ncol=ncol, frameon=False, bbox_to_anchor=(0.5, 0.0),
               columnspacing=1.2, handlelength=1.6)
    fig.tight_layout(rect=(0, alto_rel, 1, 1))


# --------------------------------------------------------------------------- #
# F0. Caso base en toda la red
# --------------------------------------------------------------------------- #

def f0_caso_base_red(r, carpeta):
    """r: filas E0 y E1 de results/caso_base/tablas/resumen_carga.csv (nivel 100%)."""
    escs = ["E0", "E1"]
    r = r.set_index("escenario").loc[escs]
    sin = r["buses_vsp"].values
    extra = r["buses_final"].values - sin
    res = r["buses_reserva"].values
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 3.3))
    x = np.arange(len(escs))
    cols = [gr.ESCENARIO[e] for e in escs]
    ax.bar(x, sin, 0.5, color=cols, edgecolor="white", linewidth=1.5)
    ax.bar(x, extra, 0.5, bottom=sin, color=cols, alpha=0.45, hatch="///", edgecolor="white", linewidth=1.5)
    ax.bar(x, res, 0.5, bottom=sin + extra, color=GRIS_2, edgecolor="white", linewidth=1.5)
    for xi, a, b, c in zip(x, sin, extra, res):
        ax.text(xi, a / 2, num(a), ha="center", va="center", color="white", fontsize=9)
        ax.text(xi + 0.28, a + b / 2, f"+{num(b)}", ha="left", va="center", fontsize=9)
        ax.text(xi + 0.28, a + b + c / 2, f"+{num(c)}", ha="left", va="center", fontsize=9)
        ax.text(xi, a + b + c + 150, num(a + b + c), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([ESCENARIO[e] for e in escs])
    ax.set_xlim(-0.5, 1.8)
    ax.set_ylim(0, (sin + extra + res).max() * 1.12)
    ax.set_ylabel("buses")
    eje_es(ax)
    _ejes(ax)
    _leyenda_abajo(fig, [Patch(facecolor="#9a9a9a", label="jornadas sin batería"),
                         Patch(facecolor="#9a9a9a", alpha=0.45, hatch="///", label="+ jornadas partidas por la carga"),
                         Patch(facecolor=GRIS_2, label="+ buses de reserva")], 2, 0.13)
    datos = pd.DataFrame({"escenario": [ESCENARIO[e] for e in escs], "buses_jornadas_sin_bateria": sin,
                          "buses_tras_la_carga_reactiva": sin + extra, "buses_de_reserva": res,
                          "buses_totales": sin + extra + res})
    guardar(fig, carpeta, "F0_caso_base_red", datos)
    cifra = "; ".join(f"{ESCENARIO[e]}: {num(a)} -> {num(a + b)} -> {num(a + b + c)} buses"
                      for e, a, b, c in zip(escs, sin, extra, res))
    return ("F0_caso_base_red", "Buses del caso base en toda la red: jornadas sin batería, después de la carga reactiva "
            "(jornadas partidas) y con los buses de reserva que cumplen el ciclo diario. El color identifica el escenario.",
            cifra)


# --------------------------------------------------------------------------- #
# F1. Diagrama de la metodologia (vertical: cada etapa en una fila)
# --------------------------------------------------------------------------- #

ETAPAS = [("Etapa 0", "Preproceso", "viajes, terminales y distancias"),
          ("Etapa 1", "Rutas a electroterminal", "cada ruta a un electroterminal"),
          ("Etapa 2", "Jornadas sin batería", "qué bus hace qué viajes (flujo)"),
          ("Etapa 3", "Cortes y re-encadenamiento", "tramos con recarga y ventanas de carga"),
          ("Etapa 4", "Programación de la carga", "cuándo carga cada bus (puestos y tarifa)")]


def f1_metodologia(carpeta):
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 3.9))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 10.6)
    ax.axis("off")
    x0, w, h, paso = 0.05, 8.75, 1.55, 2.1
    for i, (et, nom, sale) in enumerate(ETAPAS):
        y = 10.4 - h - i * paso
        col = gr.ESCENARIO["E2"] if i >= 3 else "#4b4b4b"
        ax.add_patch(FancyBboxPatch((x0, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", facecolor="white",
                                    edgecolor=col, linewidth=1.6))
        ax.text(x0 + 0.2, y + h * 0.66, f"{et}. {nom}", ha="left", va="center", fontsize=9, fontweight="bold",
                color=col)
        ax.text(x0 + 0.2, y + h * 0.28, sale, ha="left", va="center", fontsize=9, color=gr.TEXTO_SECUNDARIO)
        if i < len(ETAPAS) - 1:
            ax.annotate("", xy=(x0 + w / 2, y - (paso - h) + 0.03), xytext=(x0 + w / 2, y - 0.03),
                        arrowprops=dict(arrowstyle="-|>", color=gr.TEXTO, lw=1.2))
    # caso base aparte: usa las jornadas de la Etapa 2 con la carga reactiva; no es una etapa
    y2 = 10.4 - h - 2 * paso
    xc, wc, hc = 9.15, 3.2, 2.6
    yc = y2 + h / 2 - hc / 2
    ax.add_patch(FancyBboxPatch((xc, yc), wc, hc, boxstyle="round,pad=0.02,rounding_size=0.15", facecolor="#f4f4f2",
                                edgecolor=gr.ESCENARIO["E0"], linewidth=1.4, linestyle="--"))
    ax.text(xc + wc / 2, yc + hc - 0.45, "Caso base", ha="center", va="center", fontsize=9, fontweight="bold",
            color=gr.ESCENARIO["E0"])
    ax.text(xc + wc / 2, yc + hc / 2 - 0.25, "no es etapa:\nEtapa 2 +\ncarga reactiva",
            ha="center", va="center", fontsize=9)
    ax.annotate("", xy=(xc - 0.03, y2 + h / 2), xytext=(x0 + w + 0.03, y2 + h / 2),
                arrowprops=dict(arrowstyle="-|>", color=gr.ESCENARIO["E0"], lw=1.2, linestyle="--"))
    datos = pd.DataFrame([dict(bloque=et, nombre=nom, produce=sale) for et, nom, sale in ETAPAS]
                         + [dict(bloque="Caso base (no es una etapa)", nombre="jornadas de la Etapa 2 + carga reactiva",
                                 produce="línea base de comparación")])
    guardar(fig, carpeta, "F1_metodologia", datos)
    return ("F1_metodologia", "Metodología en cinco etapas en secuencia. El caso base no es una etapa: toma las jornadas "
            "de la Etapa 2 y les aplica la carga reactiva; es la línea base con que se comparan las propuestas.", "-")


# --------------------------------------------------------------------------- #
# F2. Un mismo grupo de viajes: caso base frente a la Etapa 3
# --------------------------------------------------------------------------- #

ACT = {"jornada": ("viajes del grupo", gr.ESCENARIO["E1"]),
       "otro": ("otro tramo (otra jornada)", "#f2b79c"),
       "carga": ("cargando", "#008300"),
       "patio": ("en el patio", gr.GRILLA),
       "detenido": ("detenido el resto del día", "#4b4b4b")}


def elegir_ejemplo(cb_j, cb_ev, tramos, prog):
    """Jornada del caso base con interlining que se parte una sola vez a mitad del dia (entre las 10 y las 17 h, asi el
    primer bus queda detenido el resto del dia) y que en la Etapa 3 se corta en dos tramos, con el bus del primer tramo
    tomando despues otro tramo de otra jornada y todas sus cargas de un solo evento. Entre las que cumplen, la de corte
    mas cercano a la mediana (la mas representativa)."""
    partes = cb_j.groupby("bus_origen")["parte"].max()
    eventos = prog.set_index("tramo_id")["eventos"]
    cand = []
    for jv, g in tramos.groupby("jornada_vsp"):
        if len(g) != 2 or partes.get(jv, 0) != 1:
            continue
        g = g.sort_values("parte")
        b1, b2 = g["bus"].iloc[0], g["bus"].iloc[1]
        c1, c2 = tramos[tramos["bus"] == b1], tramos[tramos["bus"] == b2]
        if b1 == b2 or len(c1) != 2 or g["orden_en_bus"].iloc[0] != 1 or len(c2) > 2:
            continue
        if not (eventos.reindex(pd.concat([c1, c2])["tramo_id"]) == 1).all():
            continue
        p0 = cb_j[(cb_j["bus_origen"] == jv) & (cb_j["parte"] == 0)].iloc[0]
        corte = (p0["arr_min"] + p0["km_pullin"] / 20.0 * 60) / 60
        if not 10 <= corte <= 17 or g["salida_patio_min"].iloc[0] < 300:
            continue
        cand.append((jv, corte))
    assert cand, "No hay una jornada de ejemplo que cumpla los criterios de la figura F2."
    med = np.median([c[1] for c in cand])
    return sorted(cand, key=lambda c: (abs(c[1] - med), int(c[0])))[0][0], len(cand)


def f2_gantt(cb_j, cb_ev, tramos, prog, carpeta):
    jv, n_cand = elegir_ejemplo(cb_j, cb_ev, tramos, prog)
    v = 20.0                                                   # km/h (parametros.VELOCIDAD_KMH)
    seg = []                                                   # (panel, fila, actividad, ini, fin)
    partes = cb_j[cb_j["bus_origen"] == jv].sort_values("parte")
    for k, p in enumerate(partes.itertuples()):
        fila = f"Bus {k + 1}" + (" (nuevo)" if k else "")
        llegada = p.arr_min + p.km_pullin / v * 60
        seg.append(("cb", fila, "jornada", p.salida_electroterminal_min, llegada))
        evs = cb_ev[cb_ev["jornada_id"] == p.jornada_id].sort_values("t_inicio")
        for e in evs.itertuples():
            seg.append(("cb", fila, "carga", e.t_inicio, e.t_fin))
        seg.append(("cb", fila, "patio", llegada, evs.loc[evs["tipo"] == "final", "t_inicio"].min()))
        if k == 0:
            seg.append(("cb", fila, "detenido", evs["t_fin"].max(), None))     # parado el resto del dia
    g = tramos[tramos["jornada_vsp"] == jv].sort_values("parte")
    prog_t = prog.set_index("tramo_id")
    for k, bus in enumerate(g["bus"].values):
        fila = f"Bus {chr(65 + k)}"
        cadena = tramos[tramos["bus"] == bus].sort_values("orden_en_bus")
        for i, t in enumerate(cadena.itertuples()):
            seg.append(("e3", fila, "jornada" if t.jornada_vsp == jv else "otro", t.salida_patio_min,
                        t.llegada_patio_min))
            c = prog_t.loc[t.tramo_id]
            seg.append(("e3", fila, "patio", t.llegada_patio_min, c["inicio_carga_min"]))
            seg.append(("e3", fila, "carga", c["inicio_carga_min"], c["fin_carga_min"]))
            if i + 1 < len(cadena):
                seg.append(("e3", fila, "patio", c["fin_carga_min"], cadena["salida_patio_min"].iloc[i + 1]))
    fin_datos = max(s[4] for s in seg if s[4] is not None)
    fin_eje = np.ceil(fin_datos / 120) * 2                         # horas, en multiplos de 2
    ini_eje = np.floor(min(s[3] for s in seg) / 120) * 2
    df = pd.DataFrame(seg, columns=["panel", "fila", "actividad", "inicio_min", "fin_min"])
    df["fin_min"] = df["fin_min"].fillna(fin_eje * 60)
    df = df[df["fin_min"] > df["inicio_min"]]

    fig, axs = plt.subplots(2, 1, figsize=(ANCHO_IN, 3.9), sharex=True)
    titulos = {"cb": f"{ESCENARIO['E1']}: la jornada se parte", "e3": "Etapa 3 y Propuesta completa: dos tramos"}
    for ax, panel in zip(axs, ("cb", "e3")):
        d = df[df["panel"] == panel]
        filas = list(dict.fromkeys(d["fila"]))
        for act in ("patio", "detenido", "jornada", "otro", "carga"):
            dd = d[d["actividad"] == act]
            ax.barh([filas.index(f) for f in dd["fila"]], (dd["fin_min"] - dd["inicio_min"]) / 60,
                    left=dd["inicio_min"] / 60, height=0.55, color=ACT[act][1], edgecolor="white", linewidth=0.5)
        ax.set_yticks(range(len(filas)))
        ax.set_yticklabels(filas)
        ax.set_ylim(len(filas) - 0.45, -1.05)
        ax.text(ini_eje + 0.1, -0.82, titulos[panel], ha="left", va="center", fontsize=9, fontweight="bold")
        _ejes(ax, grilla="x")
    axs[-1].set_xlim(ini_eje, fin_eje)
    axs[-1].set_xticks(np.arange(ini_eje, fin_eje + 0.1, 2 if fin_eje - ini_eje <= 26 else 4))
    axs[-1].set_xlabel("hora del día (h; más de 24 = madrugada del día siguiente)")
    _leyenda_abajo(fig, [Patch(facecolor=ACT[a][1], label=ACT[a][0])
                         for a in ("jornada", "otro", "carga", "patio", "detenido")], 3, 0.13)
    datos = df.assign(panel=df["panel"].map({"cb": ESCENARIO["E1"], "e3": "Etapa 3 y Propuesta completa"}),
                      actividad=df["actividad"].map(lambda a: ACT[a][0]),
                      inicio_h=(df["inicio_min"] / 60).round(3), fin_h=(df["fin_min"] / 60).round(3)) \
        .drop(columns=["inicio_min", "fin_min"])
    datos.insert(0, "jornada_del_ejemplo", jv)
    guardar(fig, carpeta, "F2_gantt_jornada", datos)
    hh = lambda m: f"{int(m // 60) % 24:02d}:{int(m % 60):02d}"
    corte_cb = df[(df["panel"] == "cb") & (df["fila"] == "Bus 1") & (df["actividad"] == "jornada")]["fin_min"].iloc[0]
    det_cb = df[(df["panel"] == "cb") & (df["actividad"] == "detenido")]["inicio_min"].iloc[0]
    otro = df[(df["panel"] == "e3") & (df["actividad"] == "otro")]["inicio_min"].iloc[0]
    cifra = (f"jornada {jv} (elegida entre {n_cand} con el mismo patrón, la de corte más cercano a la mediana): en el "
             f"caso base el bus 1 vuelve al patio a las {hh(corte_cb)} y queda detenido desde las {hh(det_cb)}; en la "
             f"Etapa 3 el bus A recarga y sale con otro tramo a las {hh(otro)}")
    return ("F2_gantt_jornada", "Un mismo grupo de viajes en el caso base con interlining, donde la jornada se parte y el "
            "primer bus queda detenido el resto del día, y en la Etapa 3, donde el bus vuelve al patio, recarga y sale con "
            "otro tramo. Las cargas nocturnas terminan pasada la medianoche porque de noche los puestos están llenos.",
            cifra)


# --------------------------------------------------------------------------- #
# F3-F6. Instancia La Reina
# --------------------------------------------------------------------------- #

def f3_escalera(kb, carpeta):
    escs = list(kb["escenario"])
    op, rd, rn = (kb[c].values for c in ("buses_operativos", "reservas_intermedias", "reservas_nocturnas"))
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 3.4))
    x = np.arange(len(escs))
    ax.bar(x, op, 0.55, color=[gr.ESCENARIO[e] for e in escs], edgecolor="white", linewidth=1.5)
    ax.bar(x, rd, 0.55, bottom=op, color=GRIS_1, edgecolor="white", linewidth=1.5)
    ax.bar(x, rn, 0.55, bottom=op + rd, color=GRIS_2, edgecolor="white", linewidth=1.5)
    for xi, o, t in zip(x, op, op + rd + rn):
        ax.text(xi, t + 20, num(t), ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax.text(xi, o / 2, num(o), ha="center", va="center", fontsize=9, color="white")
    ax.set_xticks(x)
    ax.set_xticklabels([ETIQUETA_X[e] for e in escs])
    ax.set_ylabel("buses")
    ax.set_ylim(0, (op + rd + rn).max() * 1.1)
    eje_es(ax)
    _ejes(ax)
    _leyenda_abajo(fig, [Patch(facecolor="white", edgecolor=gr.TEXTO_SECUNDARIO, label="operativos (color del escenario)"),
                         Patch(facecolor=GRIS_1, label="reservas diurnas"),
                         Patch(facecolor=GRIS_2, label="reservas nocturnas")], 3, 0.09)
    datos = pd.DataFrame({"escenario": [ESCENARIO[e] for e in escs], "buses_operativos": op, "reservas_diurnas": rd,
                          "reservas_nocturnas": rn, "buses_totales": op + rd + rn})
    guardar(fig, carpeta, "F3_escalera_buses", datos)
    cifra = "; ".join(f"{ESCENARIO[e]} {num(t)}" for e, t in zip(escs, op + rd + rn))
    return ("F3_escalera_buses", "Buses de cada escenario en La Reina: operativos más reservas diurnas y nocturnas. La "
            "Propuesta completa es el modelo detallado con bloques de 15 min.", f"buses totales: {cifra}")


def f4_costo(kb, carpeta):
    escs = list(kb["escenario"])
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 3.9))
    x = np.arange(len(escs))
    base = np.zeros(len(escs))
    for c, et, col in CAPAS_COSTO:
        val = kb[c].values / 1000
        ax.bar(x, val, 0.55, bottom=base, color=col, edgecolor="white", linewidth=0.8, label=et)
        base += val
    orig = kb["costo_total_original"].values / 1000
    ax.scatter(x, orig, marker="D", s=22, color=gr.TEXTO, zorder=3, label="costo total con espera nocturna")
    for xi, t, o in zip(x, base, orig):
        ax.text(xi, max(t, o) + 12, num(t, 1), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([ETIQUETA_X[e] for e in escs])
    ax.set_ylabel("costo total (miles de USD por día)")
    ax.set_ylim(0, max(base.max(), orig.max()) * 1.12)
    eje_es(ax)
    _ejes(ax)
    h, l = ax.get_legend_handles_labels()
    _leyenda_abajo(fig, h, 3, 0.2)
    datos = pd.DataFrame({"escenario": [ESCENARIO[e] for e in escs],
                          **{c.replace("intermedias", "diurnas").replace("_comparable", ""): kb[c].values.round(0)
                             for c, _, _ in CAPAS_COSTO},
                          "costo_total": kb["costo_total_comparable"].values.round(0),
                          "costo_total_con_espera_nocturna": kb["costo_total_original"].values.round(0)})
    guardar(fig, carpeta, "F4_costo_total", datos)
    cifra = "; ".join(f"{ESCENARIO[e]} {num(t * 1000)} USD/día (con espera nocturna {num(o * 1000)})"
                      for e, t, o in zip(escs, base, orig))
    return ("F4_costo_total", "Costo total por componente en La Reina (cifra sobre cada barra, en miles de USD por día); "
            "el rombo marca el costo total con espera nocturna.", f"costo total: {cifra}")


def f5_ocupacion(series, kappa, tarifa, carpeta):
    escs = [e for e in ("E1", "E2-FIFO", "E2") if e in series]
    horas = np.arange(1440) / 60
    techo = max([kappa] + [series[e].max() for e in escs]) * 1.08
    fig, ax = plt.subplots(figsize=(ANCHO_IN, 3.3))
    caro = tarifa >= tarifa.max() - 1e-9
    ax.fill_between(horas, 0, techo, where=caro, color=gr.PUNTA, alpha=0.12, step="post", linewidth=0,
                    label="tarifa punta")
    for e in escs:
        ax.plot(horas, series[e], color=gr.ESCENARIO[e], linewidth=1.5 if e == "E2" else 1.1, drawstyle="steps-post",
                label=ESCENARIO[e])
    ax.axhline(kappa, color=gr.PUESTOS, linestyle="--", linewidth=1, label=f"{kappa} puestos")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_ylim(0, techo)
    ax.set_xlabel("hora del día (h)")
    ax.set_ylabel("buses cargando")
    eje_es(ax)
    _ejes(ax)
    h, l = ax.get_legend_handles_labels()
    _leyenda_abajo(fig, h, 2, 0.2)
    datos = pd.DataFrame({"minuto": np.arange(1440), "precio_usd_kwh": tarifa,
                          **{ESCENARIO[e]: np.round(series[e], 3) for e in escs}, "puestos": kappa})
    guardar(fig, carpeta, "F5_ocupacion_24h", datos)
    sat = {e: (series[e] >= kappa - 1e-6).sum() / 60 for e in escs}
    cifra = ("horas con todos los puestos ocupados: " + "; ".join(f"{ESCENARIO[e]} {num(sat[e], 1)} h" for e in escs)
             + (f"; máximo de la Propuesta completa en la ejecución minuto a minuto: {num(series['E2'].max(), 0)} buses"
                if "E2" in series else ""))
    return ("F5_ocupacion_24h", "Buses cargando a lo largo del día en La Reina frente a los 100 puestos; en gris, los "
            "tramos de tarifa punta. La Propuesta completa es la ejecución minuto a minuto del modelo detallado.", cifra)


def f6_sensibilidades(sens_h, sens_d, carpeta):
    fig = plt.figure(figsize=(ANCHO_IN, 4.9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1], hspace=0.55, wspace=0.45)
    a0 = fig.add_subplot(gs[0, :])
    h = sens_h["holgura_min"].values
    re_ = sens_h["reservas_E2"].values
    op = sens_h["buses_totales_E2"].values - re_
    xh = np.arange(len(h))
    a0.bar(xh, op, 0.45, color=gr.ESCENARIO["E2"], edgecolor="white", label="operativos (Etapa 3)")
    a0.bar(xh, re_, 0.45, bottom=op, color=GRIS_2, edgecolor="white", label="reservas")
    for xi, o, r_ in zip(xh, op, re_):
        a0.text(xi + 0.25, o + r_ / 2, f"{num(r_)} reservas", ha="left", va="center", fontsize=9)
        a0.text(xi, o / 2, num(o), ha="center", va="center", fontsize=9, color="white")
        a0.text(xi, o + r_ + 20, num(o + r_), ha="center", va="bottom", fontsize=9, fontweight="bold")
    a0.set_xticks(xh)
    a0.set_xticklabels([f"{num(v)} min" for v in h])
    a0.set_xlim(-0.5, len(h) - 0.2)
    a0.set_xlabel("holgura de recarga de la Etapa 3")
    a0.set_ylabel("buses")
    a0.set_ylim(0, (op + re_).max() * 1.45)
    eje_es(a0)
    _ejes(a0)
    d = sens_d["delta_min"].values
    a1, a2 = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    costo = sens_d["objetivo_usd"].values
    seg = (sens_d["segundos_lp"] + sens_d["segundos_milp"]).values
    a1.plot(d, costo / 1000, marker="o", markersize=5, linewidth=1.6, color=gr.ESCENARIO["E2"])
    for xi, c in zip(d, costo / 1000):
        a1.annotate(num(c, 1), (xi, c), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=9)
    a1.set_ylim(costo.min() / 1000 - 0.5, costo.max() / 1000 + 0.6)
    a1.set_xlim(d.min() - 4, d.max() + 4)
    a1.set_xticks(d)
    a1.set_ylabel("energía + reservas\n(miles de USD por día)")
    a2.bar(np.arange(len(d)), seg, 0.55, color=GRIS_1)
    for xi, s_ in zip(np.arange(len(d)), seg):
        a2.text(xi, s_ + 2, num(s_), ha="center", va="bottom", fontsize=9)
    a2.set_xticks(np.arange(len(d)))
    a2.set_xticklabels([num(v) for v in d])
    a2.set_ylim(0, seg.max() * 1.25)
    a2.set_ylabel("cómputo (s, LP + MILP)")
    for ax in (a1, a2):
        ax.set_xlabel("largo del bloque (min)")
        _ejes(ax)
    eje_es(a1, d=1)
    eje_es(a2)
    a0.legend(handles=[Patch(facecolor=gr.ESCENARIO["E2"], label="operativos, Propuesta completa (modelo agregado)"),
                       Patch(facecolor=GRIS_2, label="reservas")], loc="upper left", ncol=1, frameon=False)
    fig.subplots_adjust(left=0.13, right=0.98, top=0.98, bottom=0.1)
    datos = pd.concat([
        pd.DataFrame({"sensibilidad": "holgura de recarga (min)", "valor": h, "buses_operativos": op, "reservas": re_,
                      "buses_totales": op + re_}),
        pd.DataFrame({"sensibilidad": "largo del bloque (min)", "valor": d, "energia_mas_reservas_usd": costo.round(2),
                      "segundos_lp_mas_milp": seg.round(2)})], ignore_index=True)
    datos.insert(1, "modelo", "agregado")
    guardar(fig, carpeta, "F6_sensibilidades", datos)
    cifra = ("holgura " + "/".join(num(v) for v in h) + " min: " + "/".join(num(t) for t in op + re_) + " buses y "
             + "/".join(num(r_) for r_ in re_) + " reservas; bloque " + "/".join(num(v) for v in d) + " min: "
             + "/".join(num(c) for c in costo) + " USD/día en " + "/".join(num(s_) for s_ in seg) + " s (LP + MILP)")
    return ("F6_sensibilidades", "Sensibilidad con el modelo agregado: holgura de recarga de la Etapa 3 (arriba; buses "
            "operativos y reservas) y largo del bloque de la Etapa 4 (abajo; costo de energía más reservas y tiempo de "
            "cómputo del LP más el MILP).", cifra)
