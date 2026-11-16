"""
Graficos de la presentacion final (entrega 3): implementacion y resultados.

No resuelve ningun modelo: lee lo que ya esta guardado en results/ (cada terminal, la red completa, el caso base y las
Etapas 1-2) y en data-processed/. Cada grafico tiene un solo mensaje, dicho en el titulo, y se entiende sin conocer el
proyecto: sin siglas, escenarios con su nombre completo y numeros con formato chileno (12.502; 24,3%).

La unica funcion de otro script que se usa es minutos_ventana de 13- (cuenta los minutos utiles de cada ventana de
carga), para separar las reservas inevitables (el bus no alcanza a cargar ni con un puesto libre) de las que existen
por falta de puestos.

Output: results/presentacion/entrega3/<nombre>.{png,pdf,csv} (PNG a 200 dpi, 16:9) y catalogo.md, con una linea por
grafico y una propuesta de que grafico va en que lamina.

Uso (desde la raiz del repositorio):
    python scripts/18-graficos_presentacion.py
"""

import importlib.util
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import graficos as gr, nombres, parametros                       # noqa: E402
from common.rutas import CSV_SEP, DATA_FILTRADO, DATA_PROCESSED, RESULTS_DIR  # noqa: E402

SALIDA = RESULTS_DIR / "presentacion" / "entrega3"
TERMINALES = {"VN": "Vespucio Norte", "EC": "El Conquistador", "LESR": "Los Espinos + Santa Rosa", "LR": "La Reina"}
RED = "Red completa"
EXACTO = Path("etapa4") / "h0_d15" / "exacto"
CODIGO = ["E0", "E1", "E2-FIFO", "E2"]
ESC = [nombres.ESCENARIO[c] for c in CODIGO]
COL = {nombres.ESCENARIO[c]: gr.ESCENARIO[c] for c in CODIGO}
ETQ = dict(zip(ESC, ["Caso base", "Caso base\ncon interlining", "Propuesta con\ncarga por orden\nde llegada",
                     "Propuesta\ncompleta"]))
REF, PROP = ESC[1], ESC[3]

ANCHO, ALTO = 12.0, 6.75                      # 16:9
GRIS_OSC, GRIS_1, GRIS_2 = "#4b4b4b", "#8a8984", "#c3c2b7"
VIAJE, OTRO_VIAJE, VACIO, CARGA = gr.ESCENARIO["E1"], "#f2b79c", "#6250d6", "#008300"
PATIO = gr.GRILLA
OK_COLOR = "#008300"
COMPONENTES = [("costo_flota", "Flota (buses que operan)", GRIS_OSC), ("costo_reservas", "Buses de reserva", GRIS_1),
               ("costo_km_vacios", "Km sin pasajeros", "#6250d6"), ("costo_espera", "Espera", "#e87ba4"),
               ("costo_energia", "Energía", "#008300"), ("costo_eventos", "Eventos de carga", "#e34948")]
V_KMH = parametros.VELOCIDAD_KMH
KWH_MIN = 180 / 60                            # carga a 180 kW

CATALOGO = []                                 # (archivo, titulo, que muestra, mensaje, parte)


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def leer(path):
    return pd.read_csv(path, sep=CSV_SEP)


def carpeta(siglas):
    return RESULTS_DIR / f"instancia_{siglas}"


def num(x, d=0):
    """Numero con formato chileno: punto de miles, coma decimal y signo menos tipografico."""
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def pct(x, d=1):
    return f"{num(x, d)}%"


def hora(m, mas_uno=True):
    """Minuto del dia (puede pasar de 1.440) a hh:mm; '(+1)' si es del dia siguiente."""
    m = int(round(m))
    s = f"{(m // 60) % 24:02d}:{m % 60:02d}"
    return s + (" (+1)" if mas_uno and m >= 1440 else "")


def eje_horas(ax, ini_h, fin_h, paso=2, eje="x"):
    ticks = np.arange(np.ceil(ini_h / paso) * paso, fin_h + 1e-9, paso)
    etiquetas = [f"{int(t) % 24:02d}:00" + ("\n(+1)" if t >= 24 else "") for t in ticks]
    if eje == "x":
        ax.set_xticks(ticks, etiquetas)
        ax.set_xlim(ini_h, fin_h)
    else:
        ax.set_yticks(ticks, etiquetas)


def formato_eje(ax, eje="y", d=0, sufijo=""):
    f = FuncFormatter(lambda x, _: num(x, d) + sufijo)
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def estilo_ejes(ax, grilla="y"):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS_1)
    ax.tick_params(colors=gr.TEXTO_SECUNDARIO, labelsize=13)
    if grilla:
        ax.grid(axis=grilla, color=gr.GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)


def encabezado(fig, titulo, subtitulo=None):
    """Titulo (el mensaje) y subtitulo arriba a la izquierda. Devuelve la fraccion de alto libre bajo ellos."""
    alto = fig.get_figheight()
    y = 1 - 0.22 / alto
    lt = textwrap.wrap(titulo, 68)
    fig.text(0.012, y, "\n".join(lt), ha="left", va="top", fontsize=21, fontweight="bold", color=gr.TEXTO,
             linespacing=1.15)
    y -= len(lt) * 21 * 1.22 / 72 / alto
    if subtitulo:
        ls = [l for p in subtitulo.split("\n") for l in textwrap.wrap(p, 112)]
        y -= 0.08 / alto
        fig.text(0.012, y, "\n".join(ls), ha="left", va="top", fontsize=14, color=gr.TEXTO_SECUNDARIO,
                 linespacing=1.3)
        y -= len(ls) * 14 * 1.3 / 72 / alto
    return y - 0.3 / alto


def leyenda_abajo(fig, handles, ncol, y=0.012, fs=13.5):
    fig.legend(handles=handles, loc="lower center", ncol=ncol, frameon=False, bbox_to_anchor=(0.5, y), fontsize=fs,
               columnspacing=1.6, handlelength=1.6)


def guardar(fig, nombre, datos, titulo, muestra, mensaje, parte):
    SALIDA.mkdir(parents=True, exist_ok=True)
    fig.patch.set_facecolor("white")
    for ext, kw in (("png", {"dpi": 200}), ("pdf", {})):
        gr._escribir(lambda p: fig.savefig(p, facecolor="white", **kw), SALIDA / f"{nombre}.{ext}")
    plt.close(fig)
    gr._escribir(lambda p: datos.to_csv(p, index=False, sep=CSV_SEP), SALIDA / f"{nombre}.csv")
    CATALOGO.append((nombre, titulo, muestra, mensaje, parte))
    print(f"  {nombre}")


def figura(titulo, subtitulo=None, nrows=1, ncols=1, abajo=0.1, izq=0.08, der=0.98, **kw):
    fig, axs = plt.subplots(nrows, ncols, figsize=(ANCHO, ALTO), **kw)
    arriba = encabezado(fig, titulo, subtitulo)
    fig.subplots_adjust(top=arriba, bottom=abajo, left=izq, right=der)
    return fig, axs


def puntos_por_unidad(ax):
    """Puntos tipograficos por unidad de datos en x y en y (para escribir texto que calce en cajas)."""
    fig = ax.figure
    b = ax.get_position()
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    return (b.width * fig.get_figwidth() * 72 / (x1 - x0), b.height * fig.get_figheight() * 72 / abs(y1 - y0))


def ancho_letra(fs, negrita=False):
    """Ancho medio de una letra de DejaVu Sans, en puntos (para cortar texto a mano)."""
    return fs * (0.66 if negrita else 0.6)


def escala_cajas(ax, w, h, lista_parrafos, fs=12):
    """Escala de letra comun para una fila de cajas del mismo tamano: la menor que necesita cada una."""
    return min(caja(ax, 0, 0, w, h, None, p, fs=fs, dibujar=False) for p in lista_parrafos)


def caja(ax, x, y, w, h, borde, parrafos, fondo="white", estilo="-", fs=12, escala=None, dibujar=True):
    """Caja redondeada con parrafos [(texto, {kwargs de texto})], cortados al ancho de la caja. Si no caben, baja la
    letra de todos los parrafos en la misma proporcion (o usa la escala dada). Con dibujar=False solo devuelve la
    escala que necesita."""
    px, py = puntos_por_unidad(ax)
    fija = escala is not None
    escala = escala or 1.0
    while True:
        bloques, alto = [], 8 / py
        for texto, kw in parrafos:
            tam = kw.get("fontsize", fs) * escala
            chars = max(8, int((w * px - 18) / ancho_letra(tam, kw.get("fontweight") == "bold")))
            lineas = [l for p in texto.split("\n") for l in textwrap.wrap(p, chars, break_long_words=False)]
            bloques.append((lineas, {"color": gr.TEXTO, **kw, "fontsize": tam}))
            alto += len(lineas) * tam * 1.28 / py + 5 / py
            alto += 1e9 if max(len(l) for l in lineas) > chars else 0      # una palabra no cabe: bajar la letra
        if fija or alto <= h or escala < 0.7:
            break
        escala -= 0.02
    if not dibujar:
        return escala
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.9", facecolor=fondo,
                                edgecolor=borde, linewidth=2.2, linestyle=estilo))
    cursor = y + h - 8 / py
    for lineas, kw in bloques:
        for l in lineas:
            ax.text(x + 8 / px, cursor, l, ha="left", va="top", **kw)
            cursor -= kw["fontsize"] * 1.28 / py
        cursor -= 5 / py


def flecha(ax, x0, y0, x1, y1, color=gr.TEXTO, estilo="-"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=2, linestyle=estilo, mutation_scale=18))


def tabla(ax, encabezados, filas, anchos, alin=None, fs=13, color_celda=None, fondo_col=None):
    """Tabla dibujada a mano: encabezado en negrita, lineas finas entre filas, celdas cortadas al ancho. Si no cabe en
    el alto disponible, baja la letra hasta que quepa."""
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    alin = alin or ["left"] * len(encabezados)
    px, py = puntos_por_unidad(ax)
    todas = [encabezados] + filas

    def cortar(texto, ch):
        return [l for p in str(texto).split("\n") for l in (textwrap.wrap(p, ch, break_long_words=False) or [""])]

    while True:
        chars = [[max(4, int((a * px - 14) / ancho_letra(fs, i == 0))) for a in anchos] for i in range(len(todas))]
        cortadas = [[cortar(c, ch) for c, ch in zip(f, chs)] for f, chs in zip(todas, chars)]
        largo = any(len(l) > ch for f, chs in zip(cortadas, chars) for c, ch in zip(f, chs) for l in c)
        alto_linea, pad = fs * 1.3 / py, 7 / py
        alturas = [max(len(c) for c in f) * alto_linea + 2 * pad for f in cortadas]
        if (sum(alturas) <= 1 and not largo) or fs <= 9:
            break
        fs -= 0.5
    xs = np.concatenate([[0], np.cumsum(anchos)])
    y = 1.0
    for i, (f, h) in enumerate(zip(cortadas, alturas)):
        if fondo_col is not None:
            ax.add_patch(plt.Rectangle((xs[fondo_col], y - h), anchos[fondo_col], h, color="#fbf1d9", zorder=0,
                                       linewidth=0))
        for j, lineas in enumerate(f):
            kw = dict(fontsize=fs, color=gr.TEXTO, fontweight="bold" if i == 0 else "normal")
            if i > 0 and color_celda:
                kw.update(color_celda(i - 1, j, filas[i - 1][j]) or {})
            xa = {"left": xs[j] + 6 / px, "center": (xs[j] + xs[j + 1]) / 2, "right": xs[j + 1] - 6 / px}[alin[j]]
            for k, l in enumerate(lineas):
                ax.text(xa, y - pad - (k + 0.78) * alto_linea, l, ha=alin[j], va="baseline", **kw)
        y -= h
        ax.plot([0, 1], [y, y], color=GRIS_1 if i == 0 else gr.GRILLA, linewidth=1.4 if i == 0 else 0.8)


def barras_tiempo(ax, fila, segmentos, alto=0.56):
    """Segmentos (inicio_min, fin_min, color, hatch) como barras horizontales en horas."""
    for ini, fin, color, *resto in segmentos:
        if fin <= ini:
            continue
        ax.barh(fila, (fin - ini) / 60, left=ini / 60, height=alto, color=color, edgecolor="white", linewidth=1.0,
                hatch=resto[0] if resto else None)


def tarifa_minuto():
    p = leer(DATA_FILTRADO / "electricity_prices.csv")
    t = np.zeros(1440)
    for r in p.itertuples():
        t[int(r.start_hour * 60):int(r.end_hour * 60)] = r.price_usd_kwh
    return t


def sombrear_tarifa(ax, tarifa, techo, valle=True):
    h = np.arange(1441) / 60
    t = np.append(tarifa, tarifa[-1])
    ax.fill_between(h, 0, techo, where=t >= t.max() - 1e-9, step="post", color=GRIS_OSC, alpha=0.13, linewidth=0)
    if valle:
        ax.fill_between(h, 0, techo, where=t <= t.min() * 1.2, step="post", color="#5fb36b", alpha=0.12, linewidth=0)


def modulo_13():
    spec = importlib.util.spec_from_file_location("etapa4", Path(__file__).resolve().parent /
                                                  "13-etapa4_programacion_carga.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------------------- #
# Datos comunes
# --------------------------------------------------------------------------- #

def cargar():
    d = {}
    d["kpis"] = leer(RESULTS_DIR / "red_completa" / "tablas" / "kpis_red.csv")
    d["red"] = d["kpis"][d["kpis"]["terminal"] == RED].set_index("escenario").loc[ESC]
    d["plan"] = leer(RESULTS_DIR / "red_completa" / "tablas" / "plan_de_carga_por_terminal.csv").set_index("terminal")
    d["ahorro"] = leer(RESULTS_DIR / "red_completa" / "tablas" / "costo_por_terminal.csv").set_index("terminal")
    e4 = modulo_13()
    inev, div = {}, {}
    for s, n in TERMINALES.items():
        v = leer(carpeta(s) / "etapa3" / "h0" / "tablas" / "ventanas.csv")
        inev[n] = int(e4.minutos_ventana(v, KWH_MIN)["sin_tiempo"].sum())
        p = leer(carpeta(s) / EXACTO / "programa_puestos.csv").sort_values(["ventana_id", "inicio_min"])
        tramos = p.groupby("ventana_id").size()
        pausa = (p.groupby("ventana_id")["inicio_min"].shift(-1) - p["fin_min"]).dropna()
        div[n] = dict(ventanas=len(v), divididas=int((tramos >= 2).sum()), pausas=pausa.values)
    d["inevitables"], d["divididas"] = inev, div
    return d


# --------------------------------------------------------------------------- #
# Implementacion
# --------------------------------------------------------------------------- #

def g01_cadena(d):
    titulo = "La solución es una cadena: cada etapa usa lo que dejó la anterior"
    sub = ("Etapas 3 y 4 se resuelven por separado en cada electroterminal (4 problemas independientes). "
           "Toda la cadena corre con un comando en unos 47 minutos.")
    fig, ax = figura(titulo, sub, abajo=0.02, izq=0.01, der=0.99)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")
    red, plan = d["red"], d["plan"]
    etapas = [
        ("Etapa 0", "Preproceso", "Arma los viajes del día laboral", f"{num(64502)} viajes con hora, km y kWh",
         "Python · 13 s"),
        ("Etapa 1", "Rutas a electroterminales", "A qué electroterminal va cada ruta",
         "417 rutas en 4 electroterminales", "Python · 3 s"),
        ("Etapa 2", "Jornadas sin batería", "Qué viajes hace cada bus",
         f"{num(red.loc[REF, 'buses_jornadas_sin_bateria'])} jornadas", "Gurobi (flujo de costo mínimo) · 51 s"),
        ("Etapa 3", "Cortes y re-encadenamiento", "Dónde cortar las jornadas para cargar y cómo unir los tramos",
         f"{num(red.loc[PROP, 'buses_operativos'])} buses y {num(plan.loc[RED, 'ventanas'])} ventanas de carga",
         "Python + Gurobi · 4 a 8 s por terminal"),
        ("Etapa 4", "Plan de carga", "Cuándo y en qué puesto carga cada bus, y qué reservas usar",
         f"Plan al minuto con {num(plan.loc[RED, 'reservas'])} reservas",
         "Gurobi (MILP) · 0,5 a 27 min por terminal"),
    ]
    w, gap, y0, h = 18.2, 2.05, 19.5, 40.3
    textos = [[(et, dict(fontsize=12.5, color=gr.TEXTO_SECUNDARIO)), (nom, dict(fontsize=13.5, fontweight="bold")),
               ("Decide: " + decide, {}), ("Sale: " + sale, {}),
               (herr, dict(color=gr.TEXTO_SECUNDARIO, style="italic"))] for et, nom, decide, sale, herr in etapas]
    esc = escala_cajas(ax, w, h, textos)
    for i, parrafos in enumerate(textos):
        x = 0.4 + i * (w + gap)
        col = gr.ESCENARIO["E2"] if i >= 3 else GRIS_OSC
        caja(ax, x, y0, w, h, col, parrafos, escala=esc)
        if i < len(etapas) - 1:
            flecha(ax, x + w + 0.15, y0 + h / 2, x + w + gap - 0.15, y0 + h / 2)
    for i, borde, fondo, estilo, parrafos in [
            (1, GRIS_1, "#f4f4f2", "-", [("Se corre una vez y queda guardada en un archivo.",
                                         dict(color=gr.TEXTO_SECUNDARIO))]),
            (2, gr.ESCENARIO["E0"], "#f4f7fc", "--", [("Caso base (no es etapa)", dict(fontweight="bold",
                                                                                        color=gr.ESCENARIO["E0"])),
                                                      ("Etapa 2 + carga cuando el bus la necesita", {})]),
            (4, OK_COLOR, "white", "-", [("Validación independiente", dict(fontweight="bold", color=OK_COLOR)),
                                         ("6 controles y 7 días simulados", {})])]:
        x = 0.4 + i * (w + gap)
        caja(ax, x, 0.5, w, 15, borde, parrafos, fondo=fondo, estilo=estilo, escala=esc)
        flecha(ax, x + w / 2, y0 - 0.2, x + w / 2, 15.7, color=borde)
    datos = pd.DataFrame(etapas, columns=["etapa", "nombre", "decide", "sale", "herramienta_y_tiempo"])
    guardar(fig, "01_cadena_completa", datos, titulo,
            "Diagrama de las etapas: qué decide cada una, qué sale, con qué se resuelve y cuánto tarda.",
            "5 (reproducible); responde el feedback de explicar la implementación", "Implementación")


def g02_etapa1(d):
    asig = leer(DATA_PROCESSED / "rutas_cluster_c1b.csv")
    asig["terminal"] = asig["depot_nombre"].replace({"Los Espinos": TERMINALES["LESR"], "Santa Rosa": TERMINALES["LESR"]})
    ex = leer(DATA_PROCESSED / "expediciones.csv")[["route_id"]]
    ex = ex.merge(asig[["route_id", "terminal"]], on="route_id", how="left")
    orden = list(TERMINALES.values())
    datos = pd.DataFrame({
        "terminal": orden,
        "rutas": asig.groupby("terminal").size().reindex(orden).values,
        "viajes_por_dia": ex.groupby("terminal").size().reindex(orden).values,
        "puestos_de_carga": [d["plan"].loc[n, "puestos"] for n in orden]})
    titulo = "Etapa 1: cada ruta se asigna al electroterminal más cercano a sus terminales"
    sub = (f"{num(datos['rutas'].sum())} rutas y {num(datos['viajes_por_dia'].sum())} viajes de un día laboral. "
           "Los Espinos y Santa Rosa, a 1,1 km, se tratan como un solo electroterminal.")
    fig, axs = figura(titulo, sub, ncols=3, izq=0.17, abajo=0.05, sharey=True)
    for ax, col, et in zip(axs, ["rutas", "viajes_por_dia", "puestos_de_carga"],
                           ["Rutas", "Viajes con pasajeros por día", "Puestos de carga"]):
        y = np.arange(len(orden))
        v = datos[col].values
        ax.barh(y, v, height=0.55, color=GRIS_OSC)
        for yi, vi in zip(y, v):
            ax.text(vi + v.max() * 0.03, yi, num(vi), va="center", fontsize=14, color=gr.TEXTO)
        ax.set_title(et, loc="left", fontsize=15, color=gr.TEXTO)
        ax.set_xlim(0, v.max() * 1.3)
        ax.set_xticks([])
        ax.spines["bottom"].set_visible(False)
        estilo_ejes(ax, grilla=None)
        ax.set_yticks(y, [o.replace(" + ", " +\n") for o in orden], fontsize=14)
        ax.invert_yaxis() if ax is axs[0] else None
    guardar(fig, "02_etapa1_rutas_por_terminal", datos, titulo,
            "Rutas, viajes por día y puestos de carga de cada electroterminal tras la Etapa 1.",
            "Contexto de la metodología", "Implementación")


def jornada_ejemplo():
    """Jornada de La Reina de la figura F2 del informe (14-), con sus viajes, traslados y esperas."""
    f2 = pd.read_csv(carpeta("LR") / "informe" / "F2_gantt_jornada.csv", sep=CSV_SEP, encoding="utf-8")
    jv = int(f2["jornada_del_ejemplo"].iloc[0])
    j = leer(DATA_PROCESSED / "jornadas_E1.csv").set_index("bus_id").loc[jv]
    ex = leer(DATA_PROCESSED / "expediciones.csv").set_index("expedicion_id")
    ids = j["expedicion_ids"].split(";")
    km = [float(x) for x in str(j["km_deadhead_seq"]).split(";")] if len(ids) > 1 else []
    e = ex.loc[ids]
    seg, energia = [], [(e["dep_min"].iloc[0] - j["km_pullout"] / V_KMH * 60, 0.0)]
    cons = 0.0

    def avanzar(ini, fin, tipo, kwh):
        nonlocal cons
        seg.append((ini, fin, tipo))
        cons += kwh
        energia.append((fin, cons))

    avanzar(energia[0][0], e["dep_min"].iloc[0], "vacio", j["km_pullout"] * parametros.CONSUMO_KWH_KM)
    for i in range(len(ids)):
        avanzar(e["dep_min"].iloc[i], e["arr_min"].iloc[i], "viaje", e["kwh"].iloc[i])
        if i < len(ids) - 1:
            fin_dh = e["arr_min"].iloc[i] + km[i] / V_KMH * 60
            avanzar(e["arr_min"].iloc[i], fin_dh, "vacio", km[i] * parametros.CONSUMO_KWH_KM)
            seg.append((fin_dh, e["dep_min"].iloc[i + 1], "espera"))
            energia.append((e["dep_min"].iloc[i + 1], cons))
    avanzar(e["arr_min"].iloc[-1], e["arr_min"].iloc[-1] + j["km_pullin"] / V_KMH * 60, "vacio",
            j["km_pullin"] * parametros.CONSUMO_KWH_KM)
    assert abs(cons - j["kwh_total"]) < 0.5, f"Energia de la jornada {jv}: {cons:.1f} contra {j['kwh_total']:.1f}"
    return jv, j, e, pd.DataFrame(seg, columns=["inicio_min", "fin_min", "actividad"]), \
        pd.DataFrame(energia, columns=["minuto", "kwh_consumidos"]), f2


def g03_etapa2(d):
    jv, j, e, seg, en, _ = jornada_ejemplo()
    util = 350 * 0.9
    colores = {"viaje": VIAJE, "vacio": VACIO, "espera": PATIO}
    t, c = en["minuto"].values, en["kwh_consumidos"].values
    k = np.argmax(c > util)
    t_cruce = t[k - 1] + (util - c[k - 1]) / (c[k] - c[k - 1]) * (t[k] - t[k - 1])
    titulo = "Etapa 2 arma la jornada de cada bus sin mirar la batería"
    sub = (f"Una jornada real de La Reina: el bus sale del patio a las {hora(seg['inicio_min'].min())}, hace {len(e)} "
           f"viajes con pasajeros y vuelve a las {hora(seg['fin_min'].max(), False)}. Necesita {num(c[-1])} kWh y la "
           f"batería entrega {num(util)} kWh útiles: la Etapa 3 tiene que cortarla para que el bus cargue.")
    fig = plt.figure(figsize=(ANCHO, ALTO))
    arriba = encabezado(fig, titulo, sub)
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2.1], hspace=0.35, top=arriba, bottom=0.2, left=0.1, right=0.97)
    a0, a1 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    barras_tiempo(a0, 0, [(r.inicio_min, r.fin_min, colores[r.actividad]) for r in seg.itertuples()], alto=0.6)
    a0.set_yticks([0], ["Bus"], fontsize=14)
    a0.set_ylim(-0.6, 0.6)
    estilo_ejes(a0, grilla="x")
    a1.plot(t / 60, c, color=GRIS_OSC, linewidth=2.5, solid_joinstyle="round")
    a1.axhline(util, color=gr.PUESTOS, linewidth=2, linestyle="--")
    a1.text(t[0] / 60 + 0.1, util + 10, f"Batería útil: {num(util)} kWh", color=gr.TEXTO, fontsize=14, va="bottom")
    a1.plot([t_cruce / 60], [util], "o", markersize=11, color=gr.PUESTOS, markeredgecolor="white", markeredgewidth=2)
    a1.annotate(f"{hora(t_cruce)}: se acaba la batería", (t_cruce / 60, util), xytext=(25, -70),
                textcoords="offset points", fontsize=14, color=gr.TEXTO,
                arrowprops=dict(arrowstyle="-", color=gr.TEXTO_SECUNDARIO, lw=1.2))
    a1.set_ylabel("Energía consumida\ndesde la salida (kWh)", fontsize=14)
    a1.set_ylim(0, c[-1] * 1.12)
    formato_eje(a1)
    estilo_ejes(a1)
    ini_h, fin_h = np.floor(seg["inicio_min"].min() / 120) * 2, np.ceil(seg["fin_min"].max() / 120) * 2
    for ax in (a0, a1):
        eje_horas(ax, ini_h, fin_h)
    a0.set_xticklabels([])
    leyenda_abajo(fig, [Patch(color=VIAJE, label="Viaje con pasajeros"), Patch(color=VACIO, label="Traslado sin pasajeros"),
                        Patch(color=PATIO, label="Espera entre viajes"),
                        Line2D([], [], color=GRIS_OSC, lw=2.5, label="Energía consumida")], 4)
    datos = seg.assign(inicio=seg["inicio_min"].map(hora), fin=seg["fin_min"].map(hora))
    datos.insert(0, "jornada", jv)
    guardar(fig, "03_etapa2_jornada_de_un_bus", datos, titulo,
            "Línea de tiempo de una jornada real (viajes, traslados, esperas) y la energía que consume frente a la batería.",
            "Contexto de la metodología (por qué hace falta la Etapa 3)", "Implementación")


def actividades_f2(f2, panel_prefijo):
    """Filas del CSV de la figura F2 del informe para un panel."""
    g = f2[f2["panel"].str.startswith(panel_prefijo)].copy()
    def tipo(a):
        a = str(a)
        if a.startswith("viajes"):
            return "viaje"
        if a.startswith("otro"):
            return "otro"
        if a.startswith("cargando"):
            return "carga"
        if a.startswith("detenido"):
            return "detenido"
        return "patio"
    g["tipo"] = g["actividad"].map(tipo)
    return g


COLOR_ACT = {"viaje": VIAJE, "otro": OTRO_VIAJE, "carga": CARGA, "patio": PATIO, "vacio": VACIO, "espera": PATIO,
             "detenido": GRIS_OSC}


def g04_etapa3(d):
    jv, j, e, seg, en, f2 = jornada_ejemplo()
    tramos = leer(carpeta("LR") / "etapa3" / "h0" / "tablas" / "tramos.csv")
    t1 = tramos[(tramos["jornada_vsp"] == jv) & (tramos["parte"] == 1)].iloc[0]
    corte = e["arr_min"].iloc[int(t1["n_expediciones"]) - 1]
    e3 = actividades_f2(f2, "Etapa 3")
    titulo = "Etapa 3 corta la jornada donde se acaba la batería y une cada tramo con otros"
    sub = ("La misma jornada de La Reina. El bus A hace el primer tramo, vuelve al patio, carga y sale con un tramo de "
           "otra jornada. El segundo tramo lo hace el bus B, que ya venía de otro tramo.")
    fig = plt.figure(figsize=(ANCHO, ALTO))
    arriba = encabezado(fig, titulo, sub)
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2], hspace=0.45, top=arriba, bottom=0.2, left=0.17, right=0.97)
    a0, a1 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    barras_tiempo(a0, 0, [(r.inicio_min, r.fin_min, COLOR_ACT[r.actividad]) for r in seg.itertuples()], alto=0.6)
    a0.axvline(corte / 60, color=gr.TEXTO, linewidth=2)
    a0.text(corte / 60 + 0.15, 0.62, f"corte {hora(corte)}: vuelve al patio a cargar", fontsize=13.5, va="bottom",
            color=gr.TEXTO)
    a0.set_yticks([0], ["Etapa 2:\nun bus"], fontsize=14)
    a0.set_ylim(-0.5, 1.3)
    filas = ["Bus A", "Bus B"]
    for i, fila in enumerate(filas):
        g = e3[e3["fila"] == fila]
        barras_tiempo(a1, i, [(r.inicio_h * 60, r.fin_h * 60, COLOR_ACT[r.tipo]) for r in g.itertuples()], alto=0.55)
    a1.set_yticks(range(2), ["Etapa 3:\nbus A", "Etapa 3:\nbus B"], fontsize=14)
    a1.set_ylim(1.6, -0.6)
    fin_h = np.ceil(max(e3["fin_h"].max(), seg["fin_min"].max() / 60) / 2) * 2
    ini_h = np.floor(min(e3["inicio_h"].min(), seg["inicio_min"].min() / 60) / 2) * 2
    for ax in (a0, a1):
        estilo_ejes(ax, grilla="x")
        eje_horas(ax, ini_h, fin_h)
    a0.set_xticklabels([])
    leyenda_abajo(fig, [Patch(color=VIAJE, label="Viajes de esta jornada"),
                        Patch(color=OTRO_VIAJE, label="Viajes de otra jornada"),
                        Patch(color=VACIO, label="Traslado sin pasajeros"), Patch(color=CARGA, label="Cargando"),
                        Patch(color=PATIO, label="En el patio o esperando")], 3)
    datos = pd.concat([seg.assign(fila="Etapa 2: un bus", inicio=seg["inicio_min"].map(hora),
                                  fin=seg["fin_min"].map(hora))[["fila", "actividad", "inicio", "fin"]],
                       e3.assign(inicio=(e3["inicio_h"] * 60).map(hora), fin=(e3["fin_h"] * 60).map(hora))
                       [["fila", "actividad", "inicio", "fin"]]], ignore_index=True)
    datos.insert(0, "jornada", jv)
    guardar(fig, "04_etapa3_corte_y_reencadenamiento", datos, titulo,
            "La jornada del gráfico 03 antes (Etapa 2) y después de cortarla y re-encadenar sus tramos (Etapa 3).",
            "Contexto de la metodología", "Implementación")


def g04b_caso_base_vs_propuesta(d):
    *_, f2 = jornada_ejemplo()
    cb, e3 = actividades_f2(f2, "Caso base"), actividades_f2(f2, "Etapa 3")
    titulo = "Caso base: la jornada se parte y un bus queda detenido. Propuesta: el bus carga y sigue"
    sub = ("Mismos viajes de La Reina en los dos casos. En el caso base el bus carga cuando lo necesita y, si no le "
           "alcanza, sale un bus nuevo. En la propuesta los tramos se planifican con su carga.")
    fig = plt.figure(figsize=(ANCHO, ALTO))
    arriba = encabezado(fig, titulo, sub)
    gs = fig.add_gridspec(2, 1, hspace=0.35, top=arriba, bottom=0.2, left=0.2, right=0.97)
    axs = [fig.add_subplot(gs[0]), fig.add_subplot(gs[1])]
    fin_h = 40
    for ax, g, nombre in [(axs[0], cb, REF), (axs[1], e3, PROP)]:
        filas = list(dict.fromkeys(g["fila"]))
        for i, fila in enumerate(filas):
            gg = g[g["fila"] == fila]
            barras_tiempo(ax, i, [(r.inicio_h * 60, min(r.fin_h, fin_h) * 60, COLOR_ACT[r.tipo]) for r in gg.itertuples()])
        ax.set_yticks(range(len(filas)), [f.replace("(nuevo)", "nuevo") for f in filas], fontsize=14)
        ax.set_ylim(len(filas) - 0.4, -0.95)
        ax.text(4.1, -0.72, nombre, fontsize=15, fontweight="bold", va="center", color=gr.TEXTO)
        estilo_ejes(ax, grilla="x")
        eje_horas(ax, 4, fin_h, paso=4)
    axs[0].set_xticklabels([])
    leyenda_abajo(fig, [Patch(color=VIAJE, label="Viajes de esta jornada"),
                        Patch(color=OTRO_VIAJE, label="Viajes de otra jornada"), Patch(color=CARGA, label="Cargando"),
                        Patch(color=PATIO, label="En el patio"), Patch(color=GRIS_OSC, label="Detenido el resto del día")], 3)
    datos = f2.copy()
    datos["panel"] = datos["panel"].str.replace("Etapa 3 y Propuesta completa", PROP)
    guardar(fig, "04b_caso_base_vs_propuesta_un_bus", datos, titulo,
            "La misma jornada en el caso base con interlining (se parte) y en la Propuesta completa (dos tramos con carga).",
            "Contexto: diferencia entre caso base y propuesta", "Implementación")


def g05_etapa4(d):
    plan = d["plan"]
    lr = leer(carpeta("LR") / EXACTO / "modelo.csv")
    binarias = int(lr.loc[lr["modelo"].str.contains("MILP"), "binarias"].iloc[0])
    titulo = "Etapa 4 en cinco pasos: de un modelo relajado a un plan de carga validado"
    sub = ("Se corre en cada electroterminal. Entra: las ventanas de carga de la Etapa 3 (cuándo llega y cuándo sale cada "
           "bus, y cuánta energía necesita), los puestos y la tarifa por hora.")
    fig, ax = figura(titulo, sub, abajo=0.02, izq=0.01, der=0.99)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")
    pasos = [
        ("1. Modelo relajado", "MILP en bloques de 15 min (Gurobi). Cuenta energía por bloque, no buses por minuto.",
         f"Qué buses probablemente necesitan reserva y una cota inferior del costo ({num(plan.loc[RED, 'cota_inferior_usd'])} "
         "USD/día en la red)."),
        ("2. Plan exacto al minuto", f"MILP con una variable por bus y minuto (Gurobi). Cuenta buses por minuto: nunca "
         f"más que puestos. Solo las reservas son binarias ({num(binarias)} en La Reina).",
         f"Minutos de carga de cada bus y {num(plan.loc[RED, 'reservas'])} reservas."),
        ("3. Ordenar las cargas", "A igual costo, carga primero el bus que llegó primero.",
         "Cargas continuas, con menos cortes."),
        ("4. Asignar puestos", "Cada carga al puesto libre de menor número (coloreo de intervalos).",
         "Para cada bus: puesto, hora de inicio y de fin."),
        ("5. Validación independiente", "Lee solo el plan, sin el código del modelo. 6 controles y 7 días simulados.",
         "Los 6 controles OK en los 4 electroterminales."),
    ]
    w, gap, y0, h = 18.2, 2.05, 6, 52
    textos = [[(nom, dict(fontsize=14.5, fontweight="bold")), ("Cómo: " + como, {}),
               ("Sale: " + sale, dict(fontweight="bold"))] for nom, como, sale in pasos]
    esc = escala_cajas(ax, w, h, textos, fs=13)
    for i, parrafos in enumerate(textos):
        x = 0.4 + i * (w + gap)
        col = OK_COLOR if i == 4 else gr.ESCENARIO["E2"]
        caja(ax, x, y0, w, h, col, parrafos, fs=13, escala=esc)
        if i < len(pasos) - 1:
            flecha(ax, x + w + 0.15, y0 + h / 2, x + w + gap - 0.15, y0 + h / 2)
    ax.text(0.5, 1.5, f"Resultado: el plan queda a {pct(plan.loc[RED, 'brecha_pct'])} de la cota inferior en la red "
            f"({num(plan.loc[RED, 'plan_usd'])} contra {num(plan.loc[RED, 'cota_inferior_usd'])} USD/día en energía + "
            "reservas).", fontsize=14, color=gr.TEXTO)
    datos = pd.DataFrame(pasos, columns=["paso", "como", "sale"])
    guardar(fig, "05_etapa4_pasos", datos, titulo,
            "Diagrama de los pasos de la Etapa 4, con qué entra, cómo se resuelve y qué sale en cada uno.",
            "1 (aplicable) y 2 (casi óptimo)", "Implementación")


def g06_por_que_exacto(d):
    rel = leer(carpeta("LR") / "etapa4" / "h0_d15" / "tablas" / "ocupacion_minutos.csv")
    exa = leer(carpeta("LR") / EXACTO / "ocupacion_minutos.csv")
    puestos = int(exa["puestos"].iloc[0])
    h = rel["minuto"].values / 60
    r, x = rel["e2"].values, exa["e2_exacto"].values
    sobre = int((r > puestos + 1e-6).sum())
    titulo = (f"El modelo relajado llega a {num(r.max())} buses cargando con {puestos} puestos; "
              f"el plan final nunca pasa de {num(x.max())}")
    sub = (f"La Reina, buses cargando en cada minuto del día. El modelo relajado cuenta energía por bloque de 15 min y "
           f"supera los puestos en {num(sobre)} minutos del día: no se puede aplicar. El plan exacto cuenta buses minuto "
           "a minuto.")
    fig, axs = figura(titulo, sub, ncols=2, abajo=0.2, izq=0.08, der=0.98, gridspec_kw=dict(width_ratios=[2.3, 1]))
    fig.subplots_adjust(wspace=0.12)
    for ax, (ini, fin, paso) in zip(axs, [(0, 24, 2), (5, 8, 1)]):
        ax.fill_between(h, puestos, r, where=r > puestos + 1e-6, color=gr.PUESTOS, alpha=0.35, linewidth=0,
                        step="post")
        ax.plot(h, r, color=GRIS_1, linewidth=1.6, drawstyle="steps-post")
        ax.plot(h, x, color=gr.ESCENARIO["E2"], linewidth=2.2, drawstyle="steps-post")
        ax.axhline(puestos, color=gr.PUESTOS, linewidth=2, linestyle="--")
        estilo_ejes(ax)
        eje_horas(ax, ini, fin, paso=paso)
    axs[0].set_ylim(0, r.max() * 1.1)
    axs[0].set_ylabel("Buses cargando", fontsize=14)
    axs[1].set_ylim(70, r.max() * 1.05)
    axs[1].set_title("Acercamiento de 05:00 a 08:00", loc="left", fontsize=14, color=gr.TEXTO)
    axs[0].add_patch(plt.Rectangle((5, 70), 3, r.max() * 1.05 - 70, fill=False, edgecolor=GRIS_OSC, linewidth=1.2))
    leyenda_abajo(fig, [Line2D([], [], color=GRIS_1, lw=2, label="Modelo relajado"),
                        Line2D([], [], color=gr.ESCENARIO["E2"], lw=2.5, label="Plan final (exacto al minuto)"),
                        Line2D([], [], color=gr.PUESTOS, lw=2, ls="--", label=f"{puestos} puestos"),
                        Patch(color=gr.PUESTOS, alpha=0.35, label="Más buses que puestos")], 4)
    datos = pd.DataFrame({"minuto": rel["minuto"], "hora": rel["minuto"].map(lambda m: hora(m, False)),
                          "modelo_relajado": r.round(2), "plan_final": x, "puestos": puestos})
    guardar(fig, "06_por_que_plan_exacto", datos, titulo,
            "Buses cargando por minuto en La Reina: modelo relajado contra plan final, con la línea de puestos.",
            "1 (aplicable); responde la crítica principal de la entrega 2", "Implementación")


def g07_tamano_y_tiempo(d):
    det = leer(carpeta("LR") / "kpis" / "tablas" / "detallado_vs_agregado.csv")
    det = det[det["modelo"] == "detallado"].iloc[0]
    filas = []
    for s, n in TERMINALES.items():
        m = leer(carpeta(s) / EXACTO / "modelo.csv")
        filas.append(dict(terminal=n, binarias=int(m.loc[m["modelo"].str.contains("MILP"), "binarias"].iloc[0]),
                          minutos=d["plan"].loc[n, "segundos_plan_exacto"] / 60))
    t = pd.DataFrame(filas)
    lr = t[t["terminal"] == "La Reina"].iloc[0]
    veces = det["binarias"] / lr["binarias"]
    titulo = (f"Antes: {num(det['binarias'])} binarias y 1 hora sin terminar. Ahora: {num(lr['binarias'])} binarias "
              f"y {num(lr['minutos'], 1)} minutos")
    sub = ("La Reina. Las binarias son las decisiones de sí o no que el solver tiene que combinar. El plan exacto solo "
           "tiene binarias para las reservas; repartir los minutos de carga es un problema de transporte que se resuelve "
           "directo.")
    fig, axs = figura(titulo, sub, ncols=2, abajo=0.15, izq=0.15, der=0.96)
    fig.subplots_adjust(wspace=0.55)
    etiquetas = ["Modelo de la\nentrega 2", "Plan exacto\n(ahora)"]
    for ax, vals, fmt, tit in [(axs[0], [det["binarias"], lr["binarias"]], lambda v: num(v), "Variables binarias"),
                               (axs[1], [det["segundos"] / 60, lr["minutos"]], lambda v: f"{num(v, 1)} min",
                                "Tiempo de cómputo")]:
        y = [0, 1]
        ax.barh(y, vals, height=0.5, color=[GRIS_1, gr.ESCENARIO["E2"]])
        for yi, v in zip(y, vals):
            ax.text(v + max(vals) * 0.03, yi, fmt(v), va="center", fontsize=15, color=gr.TEXTO)
        ax.set_yticks(y, etiquetas, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlim(0, max(vals) * 1.35)
        ax.set_xticks([])
        ax.spines["bottom"].set_visible(False)
        ax.set_title(tit, loc="left", fontsize=15, color=gr.TEXTO)
        estilo_ejes(ax, grilla=None)
    axs[1].text(det["segundos"] / 60 * 0.5, 0.33, "llegó al límite de 1 hora sin terminar", ha="center", va="top",
                fontsize=12.5, color=gr.TEXTO_SECUNDARIO)
    nota = ("Plan exacto en los demás terminales: " + "; ".join(
        f"{r.terminal} {num(r.minutos, 1)} min ({num(r.binarias)} binarias)" for r in t.itertuples()
        if r.terminal != "La Reina") + f". En La Reina son {num(veces)} veces menos binarias que antes.")
    fig.text(0.012, 0.02, "\n".join(textwrap.wrap(nota, 120)), fontsize=13, color=gr.TEXTO_SECUNDARIO, va="bottom")
    datos = pd.concat([pd.DataFrame([dict(terminal="La Reina", modelo="modelo detallado (entrega 2)",
                                          binarias=det["binarias"], minutos=round(det["segundos"] / 60, 1),
                                          estado=det["estado"])]),
                       t.assign(modelo="plan exacto", minutos=t["minutos"].round(1), estado="optimo (brecha pedida)")],
                      ignore_index=True)
    guardar(fig, "07_tamano_y_tiempo", datos, titulo,
            "Binarias y tiempo de cómputo del modelo de la entrega 2 contra el plan exacto en La Reina; los demás "
            "terminales al pie.", "5 (reproducible, en minutos)", "Implementación")


CRITERIOS = ["Nunca hay más buses cargando que puestos, ni dos buses en un puesto",
             "Cada carga dura minutos enteros, en un puesto que existe, a 180 kW como máximo",
             "Cada bus carga solo mientras está en el patio",
             "Cada carga repone la energía de su tramo, y ningún tramo supera la batería útil",
             "Simulando 7 días seguidos, ninguna salida queda sin bus cargado",
             "Los costos recalculados desde cero son iguales a los informados"]


def g08_validacion(d):
    res = {}
    for s, n in TERMINALES.items():
        v = leer(carpeta(s) / EXACTO / "validacion.csv")
        assert len(v) == 6, f"{n}: se esperaban 6 criterios en validacion.csv"
        res[n] = v["resultado"].tolist()
    titulo = "El plan de carga pasa los 6 controles del validador independiente en los 4 electroterminales"
    sub = ("El validador lee solo el plan (bus, puesto, inicio y fin de cada carga) y no usa el código del modelo. "
           "Sin buses de reserva, en una prueba encontró 489 salidas sin bus: sí detecta un plan malo.")
    fig, ax = figura(titulo, sub, abajo=0.03, izq=0.02, der=0.98)
    nombres_t = list(TERMINALES.values())
    filas = [[f"{i + 1}. {c}"] + [("✓ OK" if res[n][i] == "OK" else "✗ FALLA") for n in nombres_t]
             for i, c in enumerate(CRITERIOS)]
    tabla(ax, ["Control"] + ["Vespucio\nNorte", "El\nConquistador", "Los Espinos\n+ Santa Rosa", "La Reina"], filas,
          [0.44, 0.14, 0.14, 0.14, 0.14], alin=["left"] + ["center"] * 4, fs=14,
          color_celda=lambda i, j, v: dict(color=OK_COLOR, fontweight="bold") if j > 0 and "OK" in v else
          (dict(color=gr.PUESTOS, fontweight="bold") if j > 0 else None))
    datos = pd.DataFrame(filas, columns=["control"] + nombres_t)
    guardar(fig, "08_validacion", datos, titulo, "Lista de chequeo: los 6 controles del validador con su resultado "
            "por electroterminal.", "1 (aplicable)", "Implementación")


SUPUESTOS = [
    ("Un día laboral típico que se repite; cada bus parte y termina el día con la batería al 100%",
     "Los horarios son de un día laboral; el plan se repite cada día", "Fines de semana y feriados no se modelan"),
    ("Cada ruta va a un solo electroterminal y cada bus vuelve a cargar a ese electroterminal",
     "Así se opera la red", "Cada electroterminal se resuelve por separado; la suma da la red completa (comprobado)"),
    ("Los Espinos y Santa Rosa son un solo electroterminal (270 puestos)", "Están a 1,1 km",
     "Separados, Los Espinos no alcanza a reponer su energía"),
    ("Traslados sin pasajeros: línea recta × 1,3, a 20 km/h", "No hay distancias por calle para todos los pares",
     "Con 1,2 a 1,5 en vez de 1,3, la flota cambia entre −1,0% y +1,0%"),
    ("Consumo fijo de 1,4 kWh/km; batería de 350 kWh, mínimo 10% (315 kWh útiles)", "Datos del curso",
     "No se modelan clima ni pasajeros a bordo"),
    ("Carga lineal a 180 kW, en minutos enteros", "Dato del curso",
     "En la realidad la carga se frena al final: el plan sería algo optimista"),
    ("Un puesto atiende a un bus a la vez; estacionar no ocupa puesto", "Los puestos limitan la carga, no el patio",
     "El patio no se modela"),
    ("Sin atrasos: el plan está calzado al minuto", "El modelo es determinista",
     "Un atraso puede desordenar las cargas; dejar margen es la primera extensión"),
    ("Flota sin límite; cada bus cuesta 250 USD/día", "El modelo decide cuántos buses hacen falta",
     "La flota resultante es una recomendación, no un dato"),
]


def g09_supuestos(d):
    titulo = "Supuestos y simplificaciones, y qué efecto tienen"
    sub = "Todos aplican igual a los cuatro escenarios, así que la comparación entre ellos es justa."
    fig, ax = figura(titulo, sub, abajo=0.02, izq=0.015, der=0.985)
    tabla(ax, ["Supuesto", "Por qué", "Efecto en los resultados"], [list(s) for s in SUPUESTOS], [0.42, 0.25, 0.33],
          fs=12)
    datos = pd.DataFrame(SUPUESTOS, columns=["supuesto", "por_que", "efecto"])
    guardar(fig, "09_supuestos", datos, titulo, "Tabla de supuestos con su justificación y su efecto.",
            "Responde el feedback de declarar supuestos y simplificaciones", "Implementación")


def g10_reserva(d):
    lr = carpeta("LR")
    v = leer(lr / "etapa3" / "h0" / "tablas" / "ventanas.csv")
    v["sin_tiempo"] = modulo_13().minutos_ventana(v, KWH_MIN)["sin_tiempo"]
    p = leer(lr / EXACTO / "programa_E2_exacto.csv").merge(v[["ventana_id", "sin_tiempo"]], on="ventana_id")
    tramos = leer(lr / "etapa3" / "h0" / "tablas" / "tramos.csv")
    c = p[(p["reserva"] == 1) & (~p["sin_tiempo"])].copy()            # reservas por falta de puestos
    c["espera"] = c["inicio_carga_min"] - c["llegada_min"]
    c["atraso"] = c["fin_carga_min"] - c["limite_min"]
    esp_med = c["espera"].median() / 60
    c = c[(c["eventos"] == 1) & (c["tipo"] != "intermedia")]
    # caso mediano entre las reservas por falta de puestos con salida de 04:00 a 08:00
    c = c[(c["espera"] >= 20) & (c["atraso"] >= 15) & c["limite_min"].between(1440 + 240, 1440 + 480)]
    assert len(c), "No hay una ventana con reserva que cumpla los criterios del ejemplo."
    w = c.iloc[(c["atraso"] - c["atraso"].median()).abs().argsort().iloc[0]]
    previo = tramos[tramos["tramo_id"] == w["tramo_id"]].iloc[0]
    tb = tramos[tramos["bus"] == w["bus"]]
    sig = tb[((tb["salida_patio_min"] + 1440 - w["limite_min"]).abs() < 1)
             | ((tb["salida_patio_min"] - w["limite_min"]).abs() < 1)]
    sig = sig.iloc[0] if len(sig) else tb.sort_values("orden_en_bus").iloc[0]
    sale = w["limite_min"]
    ini, fin = w["llegada_min"] - 150, w["fin_carga_min"] + 150
    titulo = "Un bus de reserva sale en lugar del bus que todavía no termina de cargar"
    sub = (f"Caso típico de La Reina. El bus llega a las {hora(w['llegada_min'], False)}; de noche los puestos los usan "
           f"buses que salen antes, así que carga de {hora(w['inicio_carga_min'], False)} a "
           f"{hora(w['fin_carga_min'], False)}. A su salida, {hora(sale, False)}, sale la reserva ya cargada; al día "
           f"siguiente este bus es la reserva. Las reservas por falta de puestos esperan unas {num(esp_med, 0)} h.")
    fig, ax = figura(titulo, sub, abajo=0.2, izq=0.2, der=0.97)
    bus = [(max(previo["salida_patio_min"], ini), w["llegada_min"], VIAJE),
           (w["llegada_min"], w["inicio_carga_min"], PATIO), (w["inicio_carga_min"], w["fin_carga_min"], CARGA),
           (w["fin_carga_min"], fin, "#fbe3a6")]
    reserva = [(ini, sale, "#fbe3a6"), (sale, min(sig["llegada_patio_min"] + (1440 if sig["salida_patio_min"] < sale - 720
                                                                             else 0), fin), VIAJE)]
    barras_tiempo(ax, 0, bus)
    barras_tiempo(ax, 1, reserva)
    ax.axvline(sale / 60, color=gr.TEXTO, linewidth=2)
    ax.text(sale / 60 - 0.1, -0.5, f"{hora(sale)}: hora de salida del bus", ha="right", va="bottom", fontsize=14,
            color=gr.TEXTO)
    ax.set_yticks([0, 1], ["Bus que llega\na cargar", "Bus de reserva"], fontsize=14)
    ax.set_ylim(1.5, -0.8)
    estilo_ejes(ax, grilla="x")
    eje_horas(ax, ini / 60, fin / 60, paso=2)
    leyenda_abajo(fig, [Patch(color=VIAJE, label="Viajes con pasajeros"), Patch(color=PATIO, label="Esperando puesto"),
                        Patch(color=CARGA, label="Cargando"), Patch(color="#fbe3a6", label="Cargado, esperando en el patio")], 4)
    datos = pd.DataFrame([dict(bus=int(w["bus"]), ventana=int(w["ventana_id"]), llegada=hora(w["llegada_min"]),
                               inicio_carga=hora(w["inicio_carga_min"]), fin_carga=hora(w["fin_carga_min"]),
                               hora_de_salida=hora(sale), kwh=round(w["kwh"], 1), reserva=1)])
    guardar(fig, "10_bus_de_reserva", datos, titulo,
            "Línea de tiempo de una ventana real con reserva: el bus llega, espera, carga y la reserva sale en su lugar.",
            "Explica qué es una reserva (mensaje 4)", "Implementación")


def g11_plan_puestos(d):
    p = leer(carpeta("LR") / EXACTO / "programa_puestos.csv")
    ini, fin, n_p = 12 * 60, 18 * 60, 15
    g = p[(p["puesto"] <= n_p) & (p["fin_min"] > ini) & (p["inicio_min"] < fin)].copy()
    titulo = "Plan de carga: cada puesto atiende a un bus a la vez y en la tarifa cara quedan libres"
    sub = (f"La Reina, puestos 1 a {n_p} de 100, de 12:00 a 18:00. Cada barra es un bus cargando; el número es el bus. "
           "De 14:00 a 17:00 la energía cuesta el doble y el plan casi no carga.")
    fig, ax = figura(titulo, sub, abajo=0.16, izq=0.09, der=0.98)
    ax.axvspan(14, 17, color=GRIS_OSC, alpha=0.13, linewidth=0)
    for r in g.itertuples():
        a, b = max(r.inicio_min, ini), min(r.fin_min, fin)
        ax.barh(r.puesto, (b - a) / 60, left=a / 60, height=0.72, color=gr.ESCENARIO["E2"], edgecolor="white",
                linewidth=1.5)
        if b - a >= 22:
            ax.text((a + b) / 120, r.puesto, str(r.bus), ha="center", va="center", fontsize=10, color=gr.TEXTO)
    ax.set_yticks(range(1, n_p + 1), [str(i) for i in range(1, n_p + 1)], fontsize=12)
    ax.set_ylim(n_p + 0.7, 0.3)
    ax.set_ylabel("Puesto", fontsize=14)
    estilo_ejes(ax, grilla="x")
    eje_horas(ax, ini / 60, fin / 60, paso=1)
    leyenda_abajo(fig, [Patch(color=gr.ESCENARIO["E2"], label="Bus cargando (número del bus)"),
                        Patch(color=GRIS_OSC, alpha=0.13, label="Tarifa cara (0,22 USD/kWh)")], 2)
    datos = g[["puesto", "bus", "inicio_hora", "fin_hora", "kwh"]].sort_values(["puesto", "inicio_hora"])
    guardar(fig, "11_plan_de_puestos", datos, titulo,
            "Gantt de 15 puestos de La Reina durante 6 horas: qué bus carga en cada puesto y cuándo.",
            "1 (aplicable): el plan es concreto, bus por bus", "Implementación")


# --------------------------------------------------------------------------- #
# Resultados
# --------------------------------------------------------------------------- #

def etiquetas_escenarios(ax, x):
    ax.set_xticks(x, [ETQ[e] for e in ESC], fontsize=13.5)


def g12_costo(d):
    red = d["red"]
    m = red["costo_total"].values / 1e6
    ref = m[1]
    ahorro = 100 * (1 - m[3] / ref)
    titulo = f"La Propuesta completa baja el costo diario de la red {pct(ahorro)} frente al caso base con interlining"
    sub = ("Costo diario de operación de la red completa: flota, buses de reserva, km sin pasajeros, espera, energía y "
           "eventos de carga. Los % son contra el caso base con interlining, la comparación justa.")
    fig, ax = figura(titulo, sub, abajo=0.17, izq=0.08)
    x = np.arange(4)
    ax.bar(x, m, width=0.58, color=[COL[e] for e in ESC], edgecolor="white", linewidth=2)
    for xi, v, e in zip(x, m, ESC):
        t = f"{num(v, 2)} M"
        if xi >= 2:
            t += f"\n{num(100 * (v / ref - 1), 1)}%"
        ax.text(xi, v + m.max() * 0.015, t, ha="center", va="bottom", fontsize=16, color=gr.TEXTO,
                fontweight="bold" if xi == 3 else "normal")
    etiquetas_escenarios(ax, x)
    ax.set_ylabel("Millones de USD por día", fontsize=14)
    ax.set_ylim(0, m.max() * 1.25)
    formato_eje(ax, d=1)
    estilo_ejes(ax)
    datos = pd.DataFrame({"escenario": ESC, "costo_total_usd": red["costo_total"].round(0).values,
                          "variacion_vs_caso_base_con_interlining_pct": (100 * (m / ref - 1)).round(2)})
    guardar(fig, "12_costo_red", datos, titulo, "Costo diario de la red por escenario, con el % contra el caso base "
            "con interlining.", "3 (ahorra 24,3%)", "Resultados")


def g13_componentes(d):
    red = d["red"]
    titulo = "El ahorro viene de la flota y de los buses de reserva; la energía cambia poco"
    sub = "Costo diario de la red completa por componente, millones de USD."
    fig, ax = figura(titulo, sub, abajo=0.27, izq=0.08)
    x = np.arange(4)
    base = np.zeros(4)
    for c, et, col in COMPONENTES:
        v = red[c].values / 1e6
        ax.bar(x, v, 0.58, bottom=base, color=col, edgecolor="white", linewidth=2, label=et)
        for xi, b, vi in zip(x, base, v):
            if vi >= 0.2:
                ax.text(xi, b + vi / 2, num(vi, 2), ha="center", va="center", fontsize=14,
                        color="white" if col in (GRIS_OSC, GRIS_1, "#6250d6", "#008300") else gr.TEXTO)
        base += v
    for xi, t in zip(x, base):
        ax.text(xi, t + 0.04, f"{num(t, 2)} M", ha="center", va="bottom", fontsize=15, fontweight="bold")
    etiquetas_escenarios(ax, x)
    ax.set_ylabel("Millones de USD por día", fontsize=14)
    ax.set_ylim(0, base.max() * 1.12)
    formato_eje(ax, d=1)
    estilo_ejes(ax)
    leyenda_abajo(fig, [Patch(color=col, label=et) for _, et, col in COMPONENTES], 3)
    datos = red[[c for c, _, _ in COMPONENTES] + ["costo_total"]].round(0).reset_index()
    guardar(fig, "13_costo_por_componente", datos, titulo, "Barras apiladas del costo de la red por componente y "
            "escenario.", "3 (de dónde sale el ahorro)", "Resultados")


def g14_cascada(d):
    red = d["red"]
    a, b, c = red.loc[REF], red.loc[ESC[2]], red.loc[PROP]
    nombres_c = {k: et for k, et, _ in COMPONENTES}
    color_c = {k: col for k, _, col in COMPONENTES}
    filas = []
    for etapa, desde, hasta in [("Etapa 3", a, b), ("Etapa 4", b, c)]:
        for k, _, _ in COMPONENTES:
            dv = hasta[k] - desde[k]
            if abs(dv) >= 1:
                filas.append((etapa, k, dv))
    df = pd.DataFrame(filas, columns=["etapa", "componente", "cambio_usd"])
    s3 = df.loc[df["etapa"] == "Etapa 3", "cambio_usd"].sum()
    s4 = df.loc[df["etapa"] == "Etapa 4", "cambio_usd"].sum()
    tot = s3 + s4
    titulo = (f"Dos tercios del ahorro vienen de la Etapa 3 (menos buses) y un tercio de la Etapa 4 (menos reservas)")
    sub = (f"Cambio en el costo diario de la red, del caso base con interlining a la Propuesta completa, miles de USD. "
           f"Etapa 3: {num(s3 / 1e3)} ({pct(100 * s3 / tot, 0)}). Etapa 4: {num(s4 / 1e3)} ({pct(100 * s4 / tot, 0)}). "
           f"Total: {num(tot / 1e3)}.")
    fig, ax = figura(titulo, sub, abajo=0.12, izq=0.33, der=0.95)
    etiquetas, y, acum = [], 0, 0.0
    for etapa, sub_e in [("Etapa 3: cortes y re-encadenamiento", "Etapa 3"), ("Etapa 4: plan de carga", "Etapa 4")]:
        etiquetas.append((y, etapa, True))
        y += 1
        for r in df[df["etapa"] == sub_e].itertuples():
            v = r.cambio_usd / 1e3
            ax.barh(y, v, left=acum, height=0.62, color=color_c[r.componente], edgecolor="white")
            ax.text(min(acum, acum + v) - 8 if v < 0 else acum + v + 8, y,
                    ("+" if v > 0 else "") + num(v, 1 if abs(v) < 10 else 0),
                    ha="right" if v < 0 else "left", va="center", fontsize=13.5, color=gr.TEXTO)
            ax.plot([acum + v, acum + v], [y + 0.31, y + 0.69], color=GRIS_1, linewidth=1)
            etiquetas.append((y, nombres_c[r.componente], False))
            acum += v
            y += 1
    ax.barh(y, acum, height=0.62, color=gr.ESCENARIO["E2"], edgecolor="white")
    ax.text(acum - 8, y, num(acum), ha="right", va="center", fontsize=14, fontweight="bold", color=gr.TEXTO)
    etiquetas.append((y, "Ahorro total", True))
    ax.set_yticks([e[0] for e in etiquetas], [e[1] for e in etiquetas], fontsize=13.5)
    for lbl, (_, _, neg) in zip(ax.get_yticklabels(), etiquetas):
        lbl.set_fontweight("bold" if neg else "normal")
    ax.set_ylim(y + 0.6, -0.6)
    ax.axvline(0, color=GRIS_1, linewidth=1)
    ax.set_xlim(acum * 1.18, 260)
    ax.set_xlabel("Miles de USD por día (negativo = ahorro)", fontsize=13)
    formato_eje(ax, "x")
    estilo_ejes(ax, grilla="x")
    df["componente"] = df["componente"].map(nombres_c)
    guardar(fig, "14_de_donde_viene_el_ahorro", df.round(0), titulo,
            "Cascada horizontal: cambio de costo por componente en la Etapa 3 y en la Etapa 4, acumulado hasta el ahorro "
            "total.", "3 (ahorra 24,3%) y qué etapa lo explica", "Resultados")


def g15_buses(d):
    red = d["red"]
    op, res = red["buses_operativos"].values, red["reservas"].values
    tot = op + res
    titulo = f"La propuesta necesita {num(tot[1] - tot[3])} buses menos: {num(tot[3])} en vez de {num(tot[1])}"
    sub = ("Buses de la red completa: los que operan las jornadas y los de reserva, que salen en lugar de un bus que "
           "todavía está cargando.")
    fig, ax = figura(titulo, sub, abajo=0.24, izq=0.1)
    x = np.arange(4)
    ax.bar(x, op, 0.58, color=[COL[e] for e in ESC], edgecolor="white", linewidth=2)
    ax.bar(x, res, 0.58, bottom=op, color=GRIS_2, edgecolor="white", linewidth=2)
    for xi, o, r, t in zip(x, op, res, tot):
        ax.text(xi, o / 2, num(o), ha="center", va="center", fontsize=14, color=gr.TEXTO)
        ax.text(xi, o + r / 2, num(r), ha="center", va="center", fontsize=13, color=gr.TEXTO)
        ax.text(xi, t + tot.max() * 0.015, num(t), ha="center", va="bottom", fontsize=16, fontweight="bold")
    etiquetas_escenarios(ax, x)
    ax.set_ylabel("Buses", fontsize=14)
    ax.set_ylim(0, tot.max() * 1.12)
    formato_eje(ax)
    estilo_ejes(ax)
    leyenda_abajo(fig, [Patch(facecolor="white", edgecolor=GRIS_OSC, label="Buses que operan (color del escenario)"),
                        Patch(color=GRIS_2, label="Buses de reserva")], 2)
    datos = pd.DataFrame({"escenario": ESC, "buses_que_operan": op, "buses_de_reserva": res, "buses_totales": tot})
    guardar(fig, "15_buses_necesarios", datos, titulo, "Buses que operan y buses de reserva por escenario, red completa.",
            "3 (ahorro: 3.507 buses menos)", "Resultados")


def g16_ahorro_terminal(d):
    a = d["ahorro"].reindex(list(TERMINALES.values()) + [RED])
    v = a["ahorro_propuesta_completa_pct"].values
    usd = a["ahorro_propuesta_completa_usd"].values
    titulo = f"Todos los electroterminales ahorran entre {pct(v[:-1].min(), 0)} y {pct(v[:-1].max(), 0)}"
    sub = "Ahorro diario de la Propuesta completa frente al caso base con interlining."
    fig, ax = figura(titulo, sub, abajo=0.06, izq=0.25, der=0.95)
    y = np.arange(len(a))
    colores = [gr.ESCENARIO["E2"]] * (len(a) - 1) + [GRIS_OSC]
    ax.barh(y, v, height=0.58, color=colores)
    for yi, vi, ui in zip(y, v, usd):
        ax.text(vi + 0.4, yi, f"{pct(vi)}  ({num(ui)} USD/día)", va="center", fontsize=14.5, color=gr.TEXTO,
                fontweight="bold" if yi == len(a) - 1 else "normal")
    ax.set_yticks(y, a.index, fontsize=14.5)
    ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.invert_yaxis()
    ax.set_xlim(0, v.max() * 1.6)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    estilo_ejes(ax, grilla=None)
    datos = a[["ahorro_propuesta_completa_pct", "ahorro_propuesta_completa_usd"]].round(2).reset_index()
    guardar(fig, "16_ahorro_por_terminal", datos, titulo, "Ahorro en % y en USD/día de cada electroterminal y de la red.",
            "3 (el ahorro es parejo, no depende de un terminal)", "Resultados")


def g17_distancia_optimo(d):
    p = d["plan"].reindex(list(TERMINALES.values()) + [RED])
    b = p["brecha_pct"].values
    titulo = (f"El plan de carga queda a {pct(b[-1])} del óptimo en la red, y a {pct(b[:-1].max())} como máximo "
              "por terminal")
    sub = ("Distancia = (costo del plan − cota inferior) / costo del plan, en energía + reservas, dados los buses de la "
           "Etapa 3. La cota es el modelo relajado: ningún plan de carga puede costar menos.")
    fig, ax = figura(titulo, sub, abajo=0.06, izq=0.25, der=0.97)
    y = np.arange(len(p))
    ax.barh(y, b, height=0.58, color=[gr.ESCENARIO["E2"]] * (len(p) - 1) + [GRIS_OSC])
    for yi, r in zip(y, p.itertuples()):
        ax.text(r.brecha_pct + 0.04, yi, f"{pct(r.brecha_pct)}   plan {num(r.plan_usd)} · cota {num(r.cota_inferior_usd)} "
                "USD/día", va="center", fontsize=13.5, color=gr.TEXTO, fontweight="bold" if yi == len(p) - 1 else None)
    ax.set_yticks(y, p.index, fontsize=14.5)
    ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.invert_yaxis()
    ax.set_xlim(0, b.max() * 2.6)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    estilo_ejes(ax, grilla=None)
    datos = p[["plan_usd", "cota_inferior_usd", "brecha_pct"]].round(2).reset_index()
    guardar(fig, "17_distancia_al_optimo", datos, titulo, "Distancia del plan a la cota inferior por terminal y en la "
            "red, con el costo del plan y de la cota.", "2 (casi óptimo)", "Resultados")


def g18_reservas(d):
    orden = list(TERMINALES.values())
    inev = np.array([d["inevitables"][n] for n in orden])
    tot = np.array([d["plan"].loc[n, "reservas"] for n in orden])
    falta = tot - inev
    share = 100 * falta.sum() / tot.sum()
    titulo = f"{num(share, 0)}% de los buses de reserva existen por falta de puestos de carga"
    sub = (f"Reservas de la Propuesta completa: {num(tot.sum())} en la red. Inevitables ({num(inev.sum())}): el bus no "
           f"alcanza a cargar antes de su salida ni con un puesto libre. Por falta de puestos ({num(falta.sum())}): "
           "alcanzaría, pero los puestos están ocupados.")
    fig, ax = figura(titulo, sub, abajo=0.2, izq=0.25, der=0.95)
    y = np.arange(len(orden))
    formato_eje(ax, "x")
    ax.barh(y, inev, height=0.58, color=GRIS_1, edgecolor="white", linewidth=2)
    ax.barh(y, falta, left=inev, height=0.58, color=gr.ESCENARIO["E2"], edgecolor="white", linewidth=2)
    for yi, a_, f_, t_ in zip(y, inev, falta, tot):
        ax.text(t_ + tot.max() * 0.015, yi, f"{num(t_)}  ({pct(100 * f_ / t_, 0)} por falta de puestos)", va="center",
                fontsize=14, color=gr.TEXTO)
    ax.set_yticks(y, orden, fontsize=14.5)
    ax.invert_yaxis()
    ax.set_xlim(0, tot.max() * 1.55)
    ax.set_xlabel("Buses de reserva", fontsize=13)
    estilo_ejes(ax, grilla="x")
    leyenda_abajo(fig, [Patch(color=GRIS_1, label="Inevitables"), Patch(color=gr.ESCENARIO["E2"],
                                                                         label="Por falta de puestos")], 2)
    datos = pd.DataFrame({"terminal": orden, "reservas": tot, "inevitables": inev, "por_falta_de_puestos": falta})
    guardar(fig, "18_reservas_por_tipo", datos, titulo, "Reservas inevitables y por falta de puestos, por terminal.",
            "4 (el cuello de botella son los puestos)", "Resultados")


def g19_puestos_y_tarifa(d):
    tarifa = tarifa_minuto()
    h = np.arange(1440) / 60
    titulo = "Con los puestos llenos casi todo el día, la carga no puede irse al horario barato"
    sub = "Buses cargando como % de los puestos, Propuesta completa. Fondo: horario de la tarifa."
    fig = plt.figure(figsize=(ANCHO, ALTO))
    arriba = encabezado(fig, titulo, sub)
    gs = fig.add_gridspec(2, 1, hspace=0.42, top=arriba - 0.04, bottom=0.2, left=0.09, right=0.98)
    filas = []
    for i, s in enumerate(["LESR", "VN"]):
        ax = fig.add_subplot(gs[i])
        o = leer(carpeta(s) / EXACTO / "ocupacion_minutos.csv")
        u = 100 * o["e2_exacto"].values / o["puestos"].values
        sombrear_tarifa(ax, tarifa, 105)
        ax.plot(h, u, color=gr.ESCENARIO["E2"], linewidth=2, drawstyle="steps-post")
        n = TERMINALES[s]
        ax.set_title(f"{n}: la energía del día usa {pct(d['plan'].loc[n, 'energia_sobre_capacidad_pct'], 0)} de la "
                     f"capacidad de 24 h", loc="left", fontsize=15, color=gr.TEXTO)
        ax.set_ylim(0, 105)
        ax.set_yticks([0, 50, 100])
        formato_eje(ax, sufijo="%")
        estilo_ejes(ax)
        eje_horas(ax, 0, 24)
        if i == 0:
            ax.set_xticklabels([])
        filas.append(pd.DataFrame({"terminal": n, "minuto": np.arange(1440), "pct_puestos_ocupados": u.round(1),
                                   "tarifa_usd_kwh": tarifa}))
    leyenda_abajo(fig, [Line2D([], [], color=gr.ESCENARIO["E2"], lw=2.5, label="% de puestos ocupados"),
                        Patch(color=GRIS_OSC, alpha=0.13, label="Tarifa cara (0,22 USD/kWh)"),
                        Patch(color="#5fb36b", alpha=0.12, label="Tarifa barata (0,10–0,11 USD/kWh)")], 3)
    guardar(fig, "19_puestos_llenos_y_tarifa", pd.concat(filas), titulo,
            "Puestos ocupados durante el día en Los Espinos + Santa Rosa (congestionado) y Vespucio Norte (holgado), con "
            "la tarifa de fondo.", "4 (el cuello de botella son los puestos, no la tarifa)", "Resultados")


def g20_valle(d):
    k = d["kpis"]
    orden = list(TERMINALES.values()) + [RED]
    titulo = "Solo Vespucio Norte, con puestos de sobra, lleva la carga al horario barato"
    sub = ("% de la energía cargada en horario barato (22:00 a 08:00), por escenario. En los demás terminales los "
           "puestos están llenos de noche y el % casi no cambia.")
    fig, ax = figura(titulo, sub, abajo=0.24, izq=0.09)
    x = np.arange(len(orden))
    ancho = 0.2
    for i, e in enumerate(ESC):
        v = k[k["escenario"] == e].set_index("terminal").reindex(orden)["pct_valle"].values
        ax.bar(x + (i - 1.5) * ancho, v, width=ancho, color=COL[e], edgecolor="white", linewidth=1.5)
        if e == PROP:
            for xi, vi in zip(x, v):
                ax.text(xi + 1.5 * ancho, vi + 1, num(vi, 0), ha="center", va="bottom", fontsize=13, fontweight="bold")
        if e == ESC[2]:
            for xi, vi in zip(x, v):
                ax.text(xi + 0.5 * ancho, vi + 1, num(vi, 0), ha="center", va="bottom", fontsize=12,
                        color=gr.TEXTO_SECUNDARIO)
    ax.set_xticks(x, [o.replace(" + ", " +\n") for o in orden], fontsize=13.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("% de la energía en horario barato", fontsize=13.5)
    formato_eje(ax, sufijo="%")
    estilo_ejes(ax)
    leyenda_abajo(fig, [Patch(color=COL[e], label=e) for e in ESC], 2)
    datos = k[k["terminal"].isin(orden)][["terminal", "escenario", "pct_valle"]].round(2)
    guardar(fig, "20_energia_en_horario_barato", datos, titulo, "% de la energía en horario barato por escenario y "
            "terminal.", "4 (la tarifa solo se aprovecha donde sobran puestos)", "Resultados")


def g21_uso_flota(d):
    red = d["red"]
    titulo = (f"Cada bus trabaja más: la utilización sube de {pct(red.loc[REF, 'utilizacion_bus_pct'], 0)} "
              f"a {pct(red.loc[PROP, 'utilizacion_bus_pct'], 0)}")
    sub = ("Red completa. Utilización = horas con pasajeros / (buses × 24 h), contando las reservas. Km sin pasajeros = "
           "traslados al patio y entre viajes, como % de los km totales.")
    fig, axs = figura(titulo, sub, ncols=2, abajo=0.17, izq=0.07, der=0.98)
    fig.subplots_adjust(wspace=0.2)
    x = np.arange(4)
    for ax, col, et in [(axs[0], "utilizacion_bus_pct", "Utilización de los buses"),
                        (axs[1], "pct_km_vacios", "Km sin pasajeros")]:
        v = red[col].values
        ax.bar(x, v, 0.6, color=[COL[e] for e in ESC], edgecolor="white", linewidth=2)
        for xi, vi in zip(x, v):
            ax.text(xi, vi + v.max() * 0.02, pct(vi), ha="center", va="bottom", fontsize=14)
        ax.set_title(et, loc="left", fontsize=15, color=gr.TEXTO)
        ax.set_ylim(0, v.max() * 1.25)
        ax.set_xticks([])
        ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(10 if v.max() > 25 else 5))
        formato_eje(ax, sufijo="%")
        estilo_ejes(ax)
    leyenda_abajo(fig, [Patch(color=COL[e], label=e) for e in ESC], 2)
    datos = red[["utilizacion_bus_pct", "pct_km_vacios"]].round(2).reset_index()
    guardar(fig, "21_uso_de_la_flota", datos, titulo, "Utilización de los buses y % de km sin pasajeros por escenario.",
            "3 (por qué hacen falta menos buses)", "Resultados")


def g22_tabla_kpis(d):
    red = d["red"]
    filas_def = [("Costo total (USD/día)", "costo_total", 0, ""), ("   Flota", "costo_flota", 0, ""),
                 ("   Buses de reserva", "costo_reservas", 0, ""), ("   Km sin pasajeros", "costo_km_vacios", 0, ""),
                 ("   Espera", "costo_espera", 0, ""), ("   Energía", "costo_energia", 0, ""),
                 ("   Eventos de carga", "costo_eventos", 0, ""), ("Buses que operan", "buses_operativos", 0, ""),
                 ("Buses de reserva", "reservas", 0, ""), ("Buses totales", "buses_totales", 0, ""),
                 ("Km sin pasajeros (% del total)", "pct_km_vacios", 1, "%"),
                 ("Costo medio de la energía (USD/kWh)", "usd_kwh", 3, ""),
                 ("Energía en horario barato", "pct_valle", 1, "%"), ("Eventos de carga", "eventos", 0, ""),
                 ("Utilización de los buses", "utilizacion_bus_pct", 1, "%")]
    filas = [[n] + [num(red.loc[e, c], dd) + s for e in ESC] for n, c, dd, s in filas_def]
    titulo = "Indicadores de la red completa por escenario"
    sub = f"Día laboral típico. Ahorro de la Propuesta completa contra el caso base con interlining: " \
          f"{pct(100 * (1 - red.loc[PROP, 'costo_total'] / red.loc[REF, 'costo_total']))}."
    fig, ax = figura(titulo, sub, abajo=0.02, izq=0.015, der=0.985)
    tabla(ax, ["Indicador"] + [e for e in ESC], filas, [0.32, 0.15, 0.17, 0.2, 0.16], alin=["left"] + ["right"] * 4,
          fs=12.5, fondo_col=4,
          color_celda=lambda i, j, v: dict(fontweight="bold") if (i in (0, 9) or j == 4) else None)
    datos = pd.DataFrame(filas, columns=["indicador"] + ESC)
    guardar(fig, "22_tabla_kpis", datos, titulo, "Tabla de KPIs de la red completa por escenario.",
            "3 (resumen de resultados)", "Resultados")


def g23a_bateria(d):
    b = leer(RESULTS_DIR / "caso_base" / "barrido" / "tablas" / "barrido_niveles.csv")
    titulo = "Caso base: cargar hasta 100% es lo más barato; con un tope menor se parten más jornadas"
    sub = ("Sensibilidad ya corrida del caso base de la red completa: nivel hasta el que carga cada bus. Con 50% falta "
           "energía (no factible). El costo incluye la espera nocturna en el patio, como en la entrega 2; por eso es "
           "algo mayor que en los demás gráficos.")
    fig, ax = figura(titulo, sub, abajo=0.17, izq=0.08, der=0.97)
    for cod in ["E0", "E1"]:
        g = b[b["escenario"] == cod].sort_values("nivel_pct", ascending=False)
        f = g["factible"].astype(bool).values
        ax.plot(g["nivel_pct"], g["costo_total_usd"] / 1e6, color=gr.ESCENARIO[cod], linewidth=2.2, zorder=2)
        ax.scatter(g["nivel_pct"][f], g["costo_total_usd"][f] / 1e6, s=70, color=gr.ESCENARIO[cod],
                   edgecolor="white", linewidth=2, zorder=3)
        ax.scatter(g["nivel_pct"][~f], g["costo_total_usd"][~f] / 1e6, s=70, facecolor="white",
                   edgecolor=gr.ESCENARIO[cod], linewidth=2, zorder=3)
        fin = g.iloc[0]
        arriba_ = cod == "E0"
        ax.annotate(f"{nombres.ESCENARIO[cod]}: {num(fin['costo_total_usd'] / 1e6, 2)} M",
                    (100, fin["costo_total_usd"] / 1e6), xytext=(-4, 16 if arriba_ else -18),
                    textcoords="offset points", ha="left", va="bottom" if arriba_ else "top", fontsize=13,
                    color=gr.TEXTO)
    ax.set_xlim(103, 48)
    ax.set_ylim(3.2, b["costo_total_usd"].max() / 1e6 * 1.05)
    ax.set_xlabel("Nivel hasta el que carga cada bus", fontsize=13.5)
    ax.set_ylabel("Millones de USD por día", fontsize=13.5)
    formato_eje(ax, d=1)
    formato_eje(ax, "x", sufijo="%")
    estilo_ejes(ax)
    leyenda_abajo(fig, [Line2D([], [], color=gr.ESCENARIO[c], lw=2.2, marker="o", markersize=8,
                               label=nombres.ESCENARIO[c]) for c in ["E0", "E1"]]
                  + [Line2D([], [], color=GRIS_OSC, lw=0, marker="o", markerfacecolor="white", markersize=9,
                            label="No factible (falta energía)")], 3)
    datos = b[["escenario", "nivel_pct", "buses_totales", "buses_reserva", "costo_total_usd", "factible"]].copy()
    datos["escenario"] = datos["escenario"].map(nombres.ESCENARIO)
    guardar(fig, "23a_sensibilidad_bateria_caso_base", datos, titulo,
            "Costo del caso base de la red según el nivel de carga de la batería (sensibilidad de la entrega 2).",
            "Sensibilidad ya corrida (justifica el caso base)", "Resultados")


def g23b_traslados(d):
    s = leer(RESULTS_DIR / "etapa2_vsp" / "tablas" / "sensibilidad_deadhead.csv")
    titulo = "Los traslados en línea recta × 1,3 son un supuesto de bajo impacto: entre 1,2 y 1,5 la flota cambia ±1%"
    sub = ("Sensibilidad ya corrida de la Etapa 2 (jornadas sin batería, con interlining, red completa): cambio en los "
           "buses al mover un parámetro. El punto negro es el valor usado.")
    fig, axs = figura(titulo, sub, ncols=3, abajo=0.15, izq=0.07, der=0.98, sharey=True)
    fig.subplots_adjust(wspace=0.12)
    usados = {"factor de desvio": 1.3, "layover (min)": 3.0, "radio de interlining (km)": 3.0}
    titulos = {"factor de desvio": "Factor de desvío de los traslados", "layover (min)": "Tiempo mínimo entre viajes (min)",
               "radio de interlining (km)": "Radio para encadenar rutas (km)"}
    for ax, (par, g) in zip(axs, s.groupby("parametro", sort=False)):
        g = g.sort_values("valor")
        ax.axhline(0, color=GRIS_1, linewidth=1)
        ax.plot(g["valor"], g["delta_buses_vs_base_pct"], color=GRIS_OSC, linewidth=2.2, marker="o", markersize=9,
                markeredgecolor="white", markeredgewidth=2)
        u = g[g["valor"] == usados[par]]
        ax.plot(u["valor"], u["delta_buses_vs_base_pct"], "o", color=gr.TEXTO, markersize=12)
        for r in g.itertuples():
            neg = r.delta_buses_vs_base_pct < 0
            ax.annotate(f"{'+' if r.delta_buses_vs_base_pct > 0 else ''}{num(r.delta_buses_vs_base_pct, 1)}%",
                        (r.valor, r.delta_buses_vs_base_pct), xytext=(0, -12 if neg else 10),
                        textcoords="offset points", ha="center", va="top" if neg else "bottom", fontsize=12)
        ax.set_title(titulos[par], loc="left", fontsize=14, color=gr.TEXTO)
        ax.set_xticks(g["valor"], [num(v, 2 if par == "factor de desvio" and v * 100 % 10 else
                                       (1 if par == "factor de desvio" else 0)) for v in g["valor"]])
        estilo_ejes(ax)
        ax.margins(x=0.1)
    axs[0].set_ylabel("Cambio en los buses (%)", fontsize=13.5)
    axs[0].set_ylim(-5.5, 13)
    axs[0].yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2))
    formato_eje(axs[0], d=0, sufijo="%")
    datos = s[["parametro", "valor", "buses", "delta_buses_vs_base_pct", "delta_costo_vs_base_pct"]]
    guardar(fig, "23b_sensibilidad_traslados", datos, titulo,
            "Cambio en la flota de la Etapa 2 al variar el factor de desvío, el tiempo entre viajes y el radio de "
            "interlining.", "Sensibilidad ya corrida; responde la pregunta del feedback sobre el deadhead", "Resultados")


def g24_cargas_divididas(d):
    orden = list(TERMINALES.values())
    dv = d["divididas"]
    ven = np.array([dv[n]["ventanas"] for n in orden])
    div = np.array([dv[n]["divididas"] for n in orden])
    pausas = np.concatenate([dv[n]["pausas"] for n in orden])
    bins = [(0, 5, "5 min\no menos"), (5, 15, "5 a\n15 min"), (15, 60, "15 a\n60 min"), (60, 1e9, "Más de\n60 min")]
    cuenta = np.array([((pausas > a) & (pausas <= b)).sum() if a > 0 else (pausas <= b).sum() for a, b, _ in bins])
    titulo = (f"Limitación: {pct(100 * div.sum() / ven.sum(), 0)} de las cargas se hacen en dos o más tramos, y la "
              "mitad de las pausas dura 5 minutos o menos")
    sub = (f"Propuesta completa, red completa: {num(div.sum())} de {num(ven.sum())} ventanas de carga. Entre tramos el "
           "bus cambia de puesto. Cada tramo paga su evento de carga (5 USD), pero la maniobra no está modelada.")
    fig, axs = figura(titulo, sub, ncols=2, abajo=0.12, izq=0.2, der=0.97)
    fig.subplots_adjust(wspace=0.35)
    y = np.arange(len(orden))
    p = 100 * div / ven
    axs[0].barh(y, p, height=0.58, color=gr.ESCENARIO["E2"])
    for yi, pi, di in zip(y, p, div):
        axs[0].text(pi + 0.8, yi, f"{pct(pi, 0)} ({num(di)})", va="center", fontsize=13.5)
    axs[0].set_yticks(y, [o.replace(" + ", " +\n") for o in orden], fontsize=13.5)
    axs[0].invert_yaxis()
    axs[0].set_xlim(0, p.max() * 1.7)
    axs[0].set_title("Ventanas cargadas en dos o más tramos", loc="left", fontsize=14.5, color=gr.TEXTO)
    xb = np.arange(len(bins))
    axs[1].bar(xb, cuenta, 0.6, color=[gr.ESCENARIO["E2"]] + [GRIS_1] * 3)
    for xi, c in zip(xb, cuenta):
        axs[1].text(xi, c + cuenta.max() * 0.02, num(c), ha="center", va="bottom", fontsize=14)
    axs[1].set_xticks(xb, [b[2] for b in bins], fontsize=12.5)
    axs[1].set_ylim(0, cuenta.max() * 1.2)
    axs[1].set_title("Duración de las pausas entre tramos", loc="left", fontsize=14.5, color=gr.TEXTO)
    formato_eje(axs[1])
    for ax, g_ in zip(axs, ("x", "y")):
        estilo_ejes(ax, grilla=g_)
    formato_eje(axs[0], "x", sufijo="%")
    datos = pd.concat([pd.DataFrame({"tabla": "ventanas", "terminal": orden, "ventanas": ven, "divididas": div,
                                     "pct": p.round(1)}),
                       pd.DataFrame({"tabla": "pausas", "duracion": [b[2].replace("\n", " ") for b in bins],
                                     "pausas": cuenta})],
                      ignore_index=True)
    guardar(fig, "24_cargas_divididas", datos, titulo, "Ventanas cargadas en dos o más tramos por terminal y duración "
            "de las pausas entre tramos.", "Limitación declarada (análisis crítico)", "Limitaciones")


def g25_buses_etapa3(d):
    filas = []
    for s, n in TERMINALES.items():
        r = leer(carpeta(s) / "etapa3" / "h0" / "tablas" / "diagnostico_flota.csv")["buses"].values
        filas.append(dict(terminal=n, jornadas_sin_bateria=r[0], cada_tramo_un_bus=r[2], etapa3=r[3]))
    t = pd.DataFrame(filas)
    s = t[["jornadas_sin_bateria", "cada_tramo_un_bus", "etapa3"]].sum()
    cb = d["red"].loc[REF, "buses_operativos"]
    titulo = (f"Re-encadenar los tramos cubre la red con {num(s['etapa3'])} buses, casi los mismos que si no hubiera "
              "batería")
    sub = (f"Red completa, buses que operan (sin contar reservas). En el caso base con interlining la carga reactiva "
           f"parte jornadas y llega a {num(cb)} buses: {num(cb - s['etapa3'])} más que la Etapa 3.")
    fig, ax = figura(titulo, sub, abajo=0.08, izq=0.36, der=0.95)
    etq = ["Jornadas sin batería (Etapa 2)", f"{REF}\n(jornadas partidas por la carga)",
           "Si cada tramo fuera un bus", "Etapa 3: tramos re-encadenados"]
    v = np.array([s["jornadas_sin_bateria"], cb, s["cada_tramo_un_bus"], s["etapa3"]])
    colores = [GRIS_2, COL[REF], GRIS_1, gr.ESCENARIO["E2"]]
    y = np.arange(4)
    ax.barh(y, v, height=0.58, color=colores)
    for yi, vi in zip(y, v):
        ax.text(vi + v.max() * 0.015, yi, num(vi), va="center", fontsize=15, color=gr.TEXTO)
    ax.set_yticks(y, etq, fontsize=14)
    ax.invert_yaxis()
    ax.set_xlim(0, v.max() * 1.15)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    estilo_ejes(ax, grilla=None)
    datos = pd.DataFrame({"concepto": [e.replace("\n", " ") for e in etq], "buses": v})
    guardar(fig, "25_buses_etapa3", datos, titulo, "Buses que operan: jornadas sin batería, caso base con interlining, "
            "cada tramo un bus y Etapa 3.", "3 (de dónde sale el ahorro de flota)", "Resultados")


def g26_datos_costo(d):
    par = leer(DATA_FILTRADO / "parameters.csv").set_index("parameter")["value"]
    tar = leer(DATA_FILTRADO / "electricity_prices.csv")
    tramos = "; ".join(f"{int(r.start_hour):02d}–{int(r.end_hour):02d} h: {num(r.price_usd_kwh, 2)}"
                       for r in tar.itertuples())
    filas = [["Bus (flota o reserva)", f"{num(par['vehicle_fixed_cost'])} USD por bus y día"],
             ["Km sin pasajeros", f"{num(par['cost_per_km'], 2)} USD/km"],
             ["Espera del bus", f"{num(par['waiting_cost_per_min'], 2)} USD/min"],
             ["Evento de carga (cada vez que un bus se conecta)", f"{num(par['fixed_charge_cost'])} USD"],
             ["Energía (USD/kWh, según la hora)", tramos],
             ["Batería", f"{num(par['battery_kwh'])} kWh; mínimo {pct(100 * par['min_soc'], 0)}; "
                         f"consumo {num(parametros.CONSUMO_KWH_KM, 1)} kWh/km"],
             ["Potencia de carga", f"{num(par['charge_power_kw'])} kW por puesto"],
             ["Puestos de carga", "; ".join(f"{n} {num(d['plan'].loc[n, 'puestos'])}" for n in TERMINALES.values())]]
    titulo = "Datos de costo y operación que usa el modelo"
    sub = "Datos entregados por el curso, iguales en todos los escenarios."
    fig, ax = figura(titulo, sub, abajo=0.03, izq=0.015, der=0.985)
    tabla(ax, ["Concepto", "Valor"], filas, [0.4, 0.6], fs=14)
    guardar(fig, "26_datos_de_costo", pd.DataFrame(filas, columns=["concepto", "valor"]), titulo,
            "Tabla de costos y parámetros del modelo.", "Contexto (datos); responde el feedback de mostrar los costos",
            "Datos")


def g27_carga_capacidad(d):
    orden = list(TERMINALES.values())
    p = d["plan"].reindex(orden)
    v = p["energia_sobre_capacidad_pct"].values
    titulo = "Tres de los cuatro electroterminales usan más del 80% de su capacidad de carga del día"
    sub = ("Energía que hay que cargar en el día / energía que pueden entregar todos los puestos en 24 h, Propuesta "
           "completa. Con más de 80%, los puestos están llenos casi toda la noche.")
    fig, ax = figura(titulo, sub, abajo=0.06, izq=0.25, der=0.95)
    y = np.arange(len(orden))
    ax.barh(y, v, height=0.58, color=[GRIS_1 if vi < 60 else gr.ESCENARIO["E2"] for vi in v])
    for yi, vi, pu in zip(y, v, p["puestos"].values):
        ax.text(vi - 1.2, yi, f"{pct(vi, 0)} · {num(pu)} puestos", ha="right", va="center", fontsize=14.5,
                color=gr.TEXTO)
    ax.set_yticks(y, orden, fontsize=14.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 115)
    ax.axvline(100, color=gr.PUESTOS, linewidth=1.5, linestyle="--")
    ax.text(101, -0.35, "100%: la energía\nno cabe en 24 h", fontsize=12.5, color=gr.TEXTO_SECUNDARIO, va="top")
    formato_eje(ax, "x", sufijo="%")
    estilo_ejes(ax, grilla="x")
    datos = p[["puestos", "energia_sobre_capacidad_pct"]].reset_index()
    guardar(fig, "27_carga_sobre_capacidad", datos, titulo, "Energía del día sobre la capacidad de los puestos en 24 h, "
            "por terminal.", "4 (el cuello de botella son los puestos)", "Resultados")


# --------------------------------------------------------------------------- #
# Catalogo
# --------------------------------------------------------------------------- #

LAMINAS = """## Propuesta de láminas

Una fila por lámina: 10 láminas de implementación y resultados, de un minuto cada una. Si falta tiempo, las que primero
se pueden pasar a respaldo son "Caso base frente a la propuesta" y "Supuestos" (si los supuestos ya se dicen en la
metodología). Lo que no está en la columna principal queda para preguntas o para el informe.

| Lámina | Gráfico principal | Apoyo o respaldo |
|---|---|---|
| Metodología: la cadena | `01_cadena_completa` | `03_etapa2_jornada_de_un_bus`, `04_etapa3_corte_y_reencadenamiento` |
| Caso base frente a la propuesta | `04b_caso_base_vs_propuesta_un_bus` | `23a_sensibilidad_bateria_caso_base` |
| Implementación de la Etapa 4 | `05_etapa4_pasos` | `07_tamano_y_tiempo` |
| Por qué el plan es aplicable | `06_por_que_plan_exacto` | `11_plan_de_puestos`, `08_validacion` |
| Supuestos | `09_supuestos` | `23b_sensibilidad_traslados`, `26_datos_de_costo` |
| Resultados: costo y buses | `12_costo_red` | `15_buses_necesarios`, `22_tabla_kpis` |
| Resultados: de dónde sale el ahorro | `14_de_donde_viene_el_ahorro` | `13_costo_por_componente`, `25_buses_etapa3`, `16_ahorro_por_terminal` |
| Resultados: calidad de la solución | `17_distancia_al_optimo` | `08_validacion` |
| Hallazgo: los puestos son el cuello de botella | `18_reservas_por_tipo` | `19_puestos_llenos_y_tarifa`, `27_carga_sobre_capacidad`, `20_energia_en_horario_barato`, `10_bus_de_reserva` |
| Análisis crítico | `24_cargas_divididas` | `21_uso_de_la_flota` |
"""


def escribir_catalogo():
    orden = {"Datos": 0, "Implementación": 1, "Resultados": 2, "Limitaciones": 3}
    filas = "\n".join(f"| `{a}` | {p} | {t} | {m} | {msg} |"
                      for a, t, m, msg, p in sorted(CATALOGO, key=lambda c: (orden[c[4]], c[0])))
    texto = f"""# Gráficos de la presentación final

Generados por `scripts/18-graficos_presentacion.py`, que solo lee lo guardado en `results/` y `data-processed/`. Cada
gráfico está en PNG (200 dpi, 16:9) y PDF, con el CSV de sus datos al lado. Los mensajes son los de
`docs/contexto_entrega_3/03_resultados_y_mensajes.md`, sección 1: 1 aplicable, 2 casi óptimo, 3 ahorra 24,3%,
4 los puestos son el cuello de botella, 5 reproducible.

| Archivo | Parte | Título (mensaje) | Qué muestra | Mensaje que apoya |
|---|---|---|---|---|
{filas}

{LAMINAS}
## Lo que no se pudo hacer sin correr algo nuevo

- Mapa de la Etapa 1: necesita `data-alumnos/chile.gpkg`, que no está en el repositorio. Se puede usar el de la entrega 2,
  `results/etapa1_clustering/mapas/mapa_c1b.png`, que sigue vigente (la Etapa 1 no cambió).
- Sensibilidades del plan exacto (holgura, largo del bloque): no se corrieron, por decisión (J8 y J9 en
  `docs/contexto_entrega_3/02_decisiones.md`). Las sensibilidades de los gráficos 23a y 23b son de la entrega 2 y siguen
  vigentes porque el caso base y la Etapa 2 no cambiaron.
"""
    gr._escribir(lambda p: p.write_text(texto, encoding="utf-8"), SALIDA / "catalogo.md")


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "hatch.color": "white"})
    print("=== Graficos de la presentacion (entrega 3) ===")
    d = cargar()
    for g in [g01_cadena, g02_etapa1, g03_etapa2, g04_etapa3, g04b_caso_base_vs_propuesta, g05_etapa4,
              g06_por_que_exacto, g07_tamano_y_tiempo, g08_validacion, g09_supuestos, g10_reserva, g11_plan_puestos,
              g12_costo, g13_componentes, g14_cascada, g15_buses, g16_ahorro_terminal, g17_distancia_optimo,
              g18_reservas, g19_puestos_y_tarifa, g20_valle, g21_uso_flota, g22_tabla_kpis, g23a_bateria,
              g23b_traslados, g24_cargas_divididas, g25_buses_etapa3, g26_datos_costo, g27_carga_capacidad]:
        g(d)
    escribir_catalogo()
    print(f"\n  {len(CATALOGO)} graficos y catalogo.md en {SALIDA}")


if __name__ == "__main__":
    main()
