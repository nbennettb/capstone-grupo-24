"""
Graficos especificos para la presentacion de la Entrega 2 - ICS2122 Capstone Buses Electricos
(ver docs/presentacion/plan_presentacion.md, seccion 6, y results/INDICE_FIGURAS.md).

No corre ningun modelo: lee resultados ya calculados y genera versiones simplificadas, legibles en una lamina (un solo eje,
el mensaje en el titulo, leyenda y coma decimal), cada una con su CSV.

  G1  Demanda de buses por hora y periodos tarifarios        (lamina 1)
  G2  Cierre ida-vuelta de las rutas                          (lamina 2)
  G3  Mapa simple de los 5 electroterminales                  (lamina 2)
  G4  Diagrama de la metodologia por etapas                   (lamina 3)
  G5  Buses en el patio vs puestos ocupados, por hora         (lamina 8)
  G6  Barrido de niveles de bateria en un panel               (lamina 9)
  G7  Reservas por tamano de instancia: simulador, MILP, piso (lamina 10)

Input:  results/etapa0_preprocesamiento/concurrencia_por_minuto.csv, data-processed/rutas_ida_vuelta.csv,
        data-filtrado/{depots,electricity_prices}.csv, results/etapa3_carga_reactiva/tablas/{jornadas,ocupacion}_E1_soc100.csv,
        results/etapa3_carga_reactiva/barrido/tablas/barrido_niveles.csv,
        results/etapa4_milp_carga/tablas/{comparacion_reactiva_milp,instancias,tiempos_resolucion}.csv
Output: results/presentacion/graficos/G<k>_<nombre>.png y results/presentacion/tablas/G<k>_<nombre>.csv, reporte.md

Uso:
    python scripts/14-graficos_presentacion.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import geo, parametros                                                     # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, RESULTS_DIR, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("presentacion")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)
R0 = RESULTS_DIR / "etapa0_preprocesamiento"
R3 = RESULTS_DIR / "etapa3_carga_reactiva"
R4 = RESULTS_DIR / "etapa4_milp_carga" / "tablas"

DIA = 1440
AZUL, NARANJO, ROJO, GRIS, VERDE = "#2c6e8f", "#d95f02", "#b22222", "#9aa5ad", "#4a8f6e"
plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12, "legend.fontsize": 11,
                     "axes.formatter.use_locale": False})


def coma(x, d=1):
    """Numero con coma decimal y punto de miles (formato de la presentacion)."""
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def estilo(ax, eje="y"):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    if eje:
        ax.grid(axis=eje, color="#e5e5e5", linewidth=0.8)
    ax.set_axisbelow(True)


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(GRAFICOS / f"{nombre}.png", dpi=200)
    plt.close(fig)


def tarifa():
    p = pd.read_csv(DATA_FILTRADO / "electricity_prices.csv", sep=CSV_SEP)
    assert p["start_hour"].min() == 0 and p["end_hour"].max() == 24, "La tarifa no cubre las 24 horas."
    return p


# --------------------------------------------------------------------------- #
def g1_demanda_y_tarifa():
    c = pd.read_csv(R0 / "concurrencia_por_minuto.csv", sep=CSV_SEP)
    conc = np.zeros(DIA)
    np.add.at(conc, c["t_min"].values % DIA, c["concurrencia"].values)    # el dia se repite: lo de pasada la medianoche cae en la madrugada
    pico_min = int(conc.argmax())
    hora = pd.DataFrame({"hora": np.arange(24), "expediciones_en_curso_max": conc.reshape(24, 60).max(axis=1).astype(int)})
    hora.to_csv(TABLAS / "G1_demanda_y_tarifa.csv", index=False, sep=CSV_SEP)
    assert int(conc.max()) == 6539, f"La concurrencia maxima ({conc.max():.0f}) no es la de la Etapa 0 (6.539)."
    p = tarifa()
    colores = {0.10: "#d9ead3", 0.11: "#d9ead3", 0.15: "#fff2cc", 0.22: "#f4cccc"}
    fig, ax = plt.subplots(figsize=(12, 5))
    for r in p.itertuples():
        ax.axvspan(r.start_hour, r.end_hour, color=colores.get(round(r.price_usd_kwh, 2), "#eeeeee"), alpha=0.8, linewidth=0)
        ax.text((r.start_hour + r.end_hour) / 2, 7150, f"{coma(r.price_usd_kwh, 2)}\nUSD/kWh", ha="center", va="bottom", fontsize=9.5)
    ax.plot(np.arange(DIA) / 60, conc, color=AZUL, linewidth=2, label="Buses en servicio (expediciones en curso)")
    ax.axhline(6539, color="#555555", linestyle=":", linewidth=1)
    ax.annotate(f"6.539 a las {pico_min // 60}:{pico_min % 60:02d}\n(cota inferior de la flota)", xy=(pico_min / 60, 6539),
                xytext=(10.2, 6100), fontsize=10, arrowprops=dict(arrowstyle="->", color="#555555"))
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 8300)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xlabel("Hora del dia (dia laboral)")
    ax.set_ylabel("Buses en servicio")
    ax.set_title("Los buses se necesitan de dia: solo pueden cargar de noche, cuando la tarifa es mas baja", loc="left")
    ax.plot([], [], color="#d9ead3", linewidth=8, label="Tarifa valle")
    ax.plot([], [], color="#fff2cc", linewidth=8, label="Tarifa media")
    ax.plot([], [], color="#f4cccc", linewidth=8, label="Tarifa punta")
    ax.legend(loc="lower left", bbox_to_anchor=(0.36, 0.02), frameon=True, facecolor="white", edgecolor="none", fontsize=10)
    estilo(ax, None)
    guardar(fig, "G1_demanda_y_tarifa")


# --------------------------------------------------------------------------- #
def g2_ida_vuelta():
    r = pd.read_csv(DATA_PROCESSED / "rutas_ida_vuelta.csv", sep=CSV_SEP)
    d = r["distancia_fin_ida_inicio_vuelta_m"]
    pct, med, n = (d < 500).mean() * 100, d.median(), len(d)
    assert abs(pct - 94.7) < 0.05, f"El % de rutas bajo 500 m ({pct:.2f}) no es el documentado (94,7%)."
    tope = 1500
    bins = np.arange(0, tope + 50, 50)
    cnt, _ = np.histogram(d.clip(upper=tope), bins=bins)
    pd.DataFrame({"desde_m": bins[:-1], "hasta_m": bins[1:], "rutas": cnt}).to_csv(TABLAS / "G2_ida_vuelta.csv", index=False, sep=CSV_SEP)
    fig, ax = plt.subplots(figsize=(10, 5))
    col = [AZUL if b < 500 else GRIS for b in bins[:-1]]
    ax.bar(bins[:-1], cnt, width=48, align="edge", color=col)
    ax.axvline(500, color="#333333", linestyle="--", linewidth=1.2)
    ax.text(520, cnt.max() * 0.85, f"{coma(pct)}% de las {n} rutas\ncierra a menos de 500 m\n(mediana {coma(med, 0)} m)", fontsize=12)
    ax.set_xlim(0, tope + 50)
    ax.set_xlabel(f"Distancia entre el fin de la ida y el inicio de la vuelta (m; la ultima barra agrupa > {coma(tope, 0)} m)")
    ax.set_ylabel("Numero de rutas")
    ax.set_title("Las rutas cierran su ida y vuelta: por eso se agrupan rutas completas, no viajes sueltos", loc="left")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AZUL, label="< 500 m"), Patch(color=GRIS, label=">= 500 m")], frameon=False, loc="center right")
    estilo(ax)
    guardar(fig, "G2_ida_vuelta")


# --------------------------------------------------------------------------- #
def g3_mapa_electroterminales():
    dep = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    n = len(dep)
    dist = np.array([[geo.haversine_km(dep.lat[i], dep.lon[i], dep.lat[j], dep.lon[j]) for j in range(n)] for i in range(n)])
    pares = [(dist[i, j], dep.nombre[i], dep.nombre[j]) for i in range(n) for j in range(i + 1, n)]
    pares.sort()
    pd.DataFrame(pares, columns=["distancia_km", "electroterminal_a", "electroterminal_b"]).round(2).to_csv(
        TABLAS / "G3_distancias_electroterminales.csv", index=False, sep=CSV_SEP)
    d1, a1, b1 = pares[0]
    d2 = pares[1][0]
    assert {a1, b1} == {"Los Espinos", "Santa Rosa"}, "El par mas cercano no es Los Espinos - Santa Rosa."
    fig, ax = plt.subplots(figsize=(8.5, 7))
    lat0 = dep.lat.mean()
    X = (dep.lon - dep.lon.mean()) * 111.32 * np.cos(np.radians(lat0))
    Y = (dep.lat - lat0) * 110.57
    i_le, i_sr = dep.index[dep.nombre == "Los Espinos"][0], dep.index[dep.nombre == "Santa Rosa"][0]
    for i in range(n):
        unido = i in (i_le, i_sr)
        ax.scatter(X[i], Y[i], s=dep.capacity[i] * (3.5 if unido else 6), color=ROJO if unido else AZUL, alpha=0.85, zorder=2, edgecolor="white", linewidth=1.5)
        dx = {"Los Espinos": (-1.0, 0.9), "Santa Rosa": (-1.0, -1.3)}.get(dep.nombre[i], (1.2, 0.4))
        ax.text(X[i] + dx[0], Y[i] + dx[1], f"{dep.nombre[i]}\n{dep.capacity[i]} puestos", fontsize=11,
                ha="right" if dep.nombre[i] in ("Los Espinos", "Santa Rosa") else "left", va="center")
    ax.text((X[i_le] + X[i_sr]) / 2 + 1.0, (Y[i_le] + Y[i_sr]) / 2, f"{coma(d1, 1)} km", color=ROJO, fontsize=13, fontweight="bold", va="center")
    ax.set_aspect("equal")
    ax.set_xlim(X.min() - 9, X.max() + 9)
    ax.set_ylim(Y.min() - 4, Y.max() + 4)
    ax.set_xlabel("km (oeste - este)")
    ax.set_ylabel("km (sur - norte)")
    ax.set_title(f"Los Espinos y Santa Rosa estan a {coma(d1, 1)} km (el siguiente par, a {coma(d2, 1)} km):\n"
                 f"se tratan como un solo electroterminal de {dep.capacity[i_le] + dep.capacity[i_sr]} puestos", loc="left")
    ax.scatter([], [], s=80, color=AZUL, label="Electroterminal (tamano = puestos)")
    ax.scatter([], [], s=80, color=ROJO, label="Unidos en el modelo")
    ax.legend(frameon=False, loc="upper right", fontsize=10)
    estilo(ax, None)
    guardar(fig, "G3_mapa_electroterminales")


# --------------------------------------------------------------------------- #
def g4_diagrama_metodologia():
    etapas = [
        ("1. Clustering", "Electroterminal de\ncada ruta", "Mas cercano a los\nparaderos reales\n(MILP con capacidad:\npropuesta)", "Energia real\nde las jornadas"),
        ("2. Asignacion de\nbuses (VSP)", "Que bus hace\nque viaje", "Flujo de costo\nminimo en red\nespacio-tiempo\n(exacto)", "Cota LB y\ncota 6.539"),
        ("3. Carga reactiva\n(caso base)", "Cuando y donde\ncarga cada bus", "Simulador: carga\ncuando lo necesita\n+ buses de reserva", "Cota LP de la\ncarga nocturna"),
        ("4. Programacion\nde carga", "Cuando y cuanto\ncarga (tarifa y\npuestos)", "MILP\n(instancia reducida)", "Piso de reservas;\nMILP <= reactiva"),
    ]
    filas = ["Que decide", "Modelo", "Como se valida"]
    pd.DataFrame([dict(etapa=e[0].replace("\n", " "), que_decide=e[1].replace("\n", " "), modelo=e[2].replace("\n", " "),
                       validacion=e[3].replace("\n", " ")) for e in etapas]).to_csv(TABLAS / "G4_diagrama_metodologia.csv", index=False, sep=CSV_SEP)
    fig, ax = plt.subplots(figsize=(13, 6.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    x0, w, gap = 1.6, 2.55, 0.28
    colores = [GRIS, AZUL, NARANJO, VERDE]
    for k, (tit, dec, mod, val) in enumerate(etapas):
        x = x0 + k * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 4.55), w, 1.15, boxstyle="round,pad=0.03", color=colores[k]))
        ax.text(x + w / 2, 5.12, tit, ha="center", va="center", color="white", fontsize=12, fontweight="bold")
        for j, (txt, y) in enumerate(((dec, 3.75), (mod, 2.45), (val, 1.05))):
            ax.add_patch(FancyBboxPatch((x, y - 0.55), w, 1.1, boxstyle="round,pad=0.03", facecolor="#f5f5f5", edgecolor="#cccccc"))
            ax.text(x + w / 2, y, txt, ha="center", va="center", fontsize=10.5)
        if k < len(etapas) - 1:
            ax.annotate("", xy=(x + w + gap - 0.02, 5.12), xytext=(x + w + 0.02, 5.12), arrowprops=dict(arrowstyle="->", lw=2, color="#555555"))
    for j, (lab, y) in enumerate(zip(filas, (3.75, 2.45, 1.05))):
        ax.text(x0 - 0.15, y, lab, ha="right", va="center", fontsize=11, fontweight="bold")
    ax.text(0.1, 0.12, "Entrega 1: horizonte rodante sobre todo el dia (demasiado complejo)  ->  Entrega 2: primero la flota, despues la carga; "
                       "cada etapa resoluble y con su verificacion", fontsize=10, color="#444444")
    ax.text(0.1, 6.0, "La metodologia divide el problema por tipo de decision", fontsize=14, fontweight="bold")
    guardar(fig, "G4_diagrama_metodologia")


# --------------------------------------------------------------------------- #
def g5_patio_vs_puestos():
    j = pd.read_csv(R3 / "tablas" / "jornadas_E1_soc100.csv", sep=CSV_SEP)
    o = pd.read_csv(R3 / "tablas" / "ocupacion_E1_soc100.csv", sep=CSV_SEP)
    v = parametros.VELOCIDAD_KMH
    salida = j["salida_electroterminal_min"].values
    llegada = (j["arr_min"] + j["km_pullin"] / v * 60).values
    fuera = np.zeros(DIA)
    for s, l in zip(salida, llegada):
        m = np.arange(int(np.floor(s)), int(np.ceil(l)))
        np.add.at(fuera, m % DIA, 1)
    nb = len(j)
    pct_patio = (1 - fuera / nb) * 100
    occ = o.groupby("minuto")["buses_cargando"].sum().reindex(range(DIA)).values
    puestos = o.groupby("terminal")["puestos"].first().sum()
    assert puestos == 700, f"Los puestos suman {puestos}, no 700."
    pct_puestos = occ / puestos * 100
    hora = pd.DataFrame({"hora": np.arange(24), "pct_buses_en_patio": pct_patio.reshape(24, 60).mean(axis=1).round(1),
                         "pct_puestos_ocupados": pct_puestos.reshape(24, 60).mean(axis=1).round(1),
                         "buses_en_patio": ((1 - fuera / nb) * nb).reshape(24, 60).mean(axis=1).round(0),
                         "buses_cargando": occ.reshape(24, 60).mean(axis=1).round(0)})
    hora.to_csv(TABLAS / "G5_patio_vs_puestos.csv", index=False, sep=CSV_SEP)
    p = tarifa()
    fig, ax = plt.subplots(figsize=(12, 5))
    for r in p[p["price_usd_kwh"] >= p["price_usd_kwh"].max() - 1e-9].itertuples():
        ax.axvspan(r.start_hour, r.end_hour, color="#f4cccc", alpha=0.6, linewidth=0)
    h = np.arange(DIA) / 60
    ax.plot(h, pct_patio, color=GRIS, linewidth=2.2, label=f"% de los {coma(nb, 0)} buses estacionados en su patio")
    ax.plot(h, pct_puestos, color=ROJO, linewidth=2.2, label="% de los 700 puestos de carga ocupados")
    ax.axhline(100, color="#555555", linestyle=":", linewidth=1)
    ax.plot([], [], color="#f4cccc", linewidth=8, label="Tarifa punta")
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 110)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xlabel("Hora del dia (E1, nivel 100%, politica reactiva)")
    ax.set_ylabel("%")
    ax.set_title(f"De noche casi todos los buses estan en el patio y los 700 puestos se llenan:\n"
                 f"{coma(2207, 0)} buses no alcanzan a cargar antes de salir (solo cabe el 84% de la energia nocturna)", loc="left")
    ax.legend(frameon=False, loc="lower left", fontsize=10)
    estilo(ax)
    guardar(fig, "G5_patio_vs_puestos")


# --------------------------------------------------------------------------- #
def g6_barrido():
    b = pd.read_csv(R3 / "barrido" / "tablas" / "barrido_niveles.csv", sep=CSV_SEP)
    b = b[b["escenario"] == "E1"].sort_values("nivel_pct", ascending=False)
    b[["nivel_pct", "buses_final", "buses_reserva", "costo_sin_reservas_usd", "costo_reservas_usd", "costo_total_usd", "factible", "elegido"]].to_csv(
        TABLAS / "G6_barrido.csv", index=False, sep=CSV_SEP)
    el = b[b["elegido"]]
    assert len(el) == 1 and int(el["nivel_pct"].iloc[0]) == 100, "El nivel elegido del barrido no es 100%."
    base = b["costo_total_usd"].iloc[0]
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(b))
    op = b["costo_sin_reservas_usd"].values / 1e6
    res = b["costo_reservas_usd"].values / 1e6
    fact = b["factible"].astype(str).str.lower().eq("true").values
    ax.bar(x, op, 0.62, color=[AZUL if f else GRIS for f in fact], label="Operacion (flota, km, espera, energia)")
    ax.bar(x, res, 0.62, bottom=op, color=ROJO, label="Buses de reserva (ciclo diario)")
    for i, (t, n, f) in enumerate(zip(b["costo_total_usd"].values, b["nivel_pct"].values, fact)):
        txt = f"{coma(t / 1e6, 2)} M" + ("" if n == 100 else f"\n+{coma((t / base - 1) * 100, 1)}%") + ("" if f else "\ninfactible")
        ax.text(i, t / 1e6 + 0.05, txt, ha="center", va="bottom", fontsize=10, fontweight="bold" if n == 100 else "normal")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}%" for n in b["nivel_pct"]])
    ax.set_xlabel("Nivel de bateria al partir y al terminar el dia")
    ax.set_ylabel("Millones de USD por dia")
    ax.set_ylim(0, b["costo_total_usd"].max() / 1e6 * 1.18)
    ax.set_title("100% con buses de reserva es el menor costo factible: bajar el nivel se paga con mas flota (E1)", loc="left")
    ax.legend(frameon=False, loc="upper left")
    estilo(ax)
    guardar(fig, "G6_barrido")


# --------------------------------------------------------------------------- #
def g7_reservas_milp():
    c = pd.read_csv(R4 / "comparacion_reactiva_milp.csv", sep=CSV_SEP)
    i = pd.read_csv(R4 / "instancias.csv", sep=CSV_SEP).set_index("N_objetivo")
    t = pd.read_csv(R4 / "tiempos_resolucion.csv", sep=CSV_SEP).set_index("N_objetivo")
    ns = sorted(c["N_objetivo"].unique())
    filas = []
    for n in ns:
        d = c[c["N_objetivo"] == n].set_index("variante")
        filas.append(dict(N_objetivo=n, buses=int(d.loc["reactiva_minuto", "buses"]), reservas_simulador=int(d.loc["reactiva_minuto", "buses_reserva"]),
                          reservas_milp=int(d.loc["milp_al_minuto", "buses_reserva"]), reservas_piso=int(i.loc[n, "reservas_cota"]),
                          ganancia_pct=round((1 - d.loc["milp_al_minuto", "costo_carga_total_usd"] / d.loc["reactiva_minuto", "costo_carga_total_usd"]) * 100, 1),
                          brecha_pct=t.loc[n, "brecha_pct"], resuelta_optimo=int(t.loc[n, "resuelta_optimo"])))
    f = pd.DataFrame(filas)
    assert (f["reservas_piso"] <= f["reservas_milp"]).all() and (f["reservas_milp"] <= f["reservas_simulador"]).all(), \
        "Orden piso <= MILP <= simulador roto."
    f.to_csv(TABLAS / "G7_reservas_milp.csv", index=False, sep=CSV_SEP)
    f = f[f["reservas_simulador"] > 0]                                  # N = 10 no tiene reservas: va en la tabla de la lamina
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(f))
    w = 0.27
    ax.bar(x - w, f["reservas_simulador"], w, color=NARANJO, label="Politica reactiva (simulador)")
    ax.bar(x, f["reservas_milp"], w, color=AZUL, label="MILP")
    ax.bar(x + w, f["reservas_piso"], w, color=GRIS, label="Piso: ningun programa puede tener menos")
    for k, r in enumerate(f.itertuples()):
        for dx, v in ((-w, r.reservas_simulador), (0, r.reservas_milp), (w, r.reservas_piso)):
            ax.text(k + dx, v + 1, str(v), ha="center", va="bottom", fontsize=9.5)
        ax.text(k, max(r.reservas_simulador, 5) * 1 + 12, f"-{coma(r.ganancia_pct, 1)}% costo de carga\nbrecha {coma(r.brecha_pct, 1)}%",
                ha="center", va="bottom", fontsize=9, color="#333333")
    ax.set_xticks(x)
    ax.set_xticklabels([f"N = {n}\n({b} buses)" for n, b in zip(f["N_objetivo"], f["buses"])])
    ax.set_ylabel("Buses de reserva")
    ax.set_ylim(0, f["reservas_simulador"].max() * 1.35)
    ax.set_title("El MILP reduce los buses de reserva y queda cerca del piso posible\n"
                 "(instancia reducida de Los Espinos + Santa Rosa; con N = 10 se certifica el optimo)", loc="left")
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    estilo(ax)
    guardar(fig, "G7_reservas_milp")


def reporte():
    L = ["# Graficos para la presentacion (Entrega 2)", "",
         "Versiones simplificadas para las laminas (ver `docs/presentacion/plan_presentacion.md`). Cada grafico tiene su CSV en `tablas/`.", "",
         "| Grafico | Lamina | Mensaje |", "|---|---|---|",
         "| `graficos/G1_demanda_y_tarifa.png` | 1 | Los buses se necesitan de dia; solo pueden cargar de noche, cuando la tarifa es mas baja |",
         "| `graficos/G2_ida_vuelta.png` | 2 | 94,7% de las rutas cierra su ida y vuelta a < 500 m: se agrupan rutas |",
         "| `graficos/G3_mapa_electroterminales.png` | 2 | Los Espinos y Santa Rosa a 1,1 km: un solo electroterminal de 270 puestos |",
         "| `graficos/G4_diagrama_metodologia.png` | 3 | Cuatro etapas por tipo de decision, cada una con su validacion |",
         "| `graficos/G5_patio_vs_puestos.png` | 8 | De noche los buses estan en el patio y los puestos se llenan |",
         "| `graficos/G6_barrido.png` | 9 | 100% con reservas es el menor costo factible |",
         "| `graficos/G7_reservas_milp.png` | 10 | El MILP reduce las reservas y queda cerca del piso (instancia reducida) |", "",
         "## Archivos", "",
         "- `tablas/G1_demanda_y_tarifa.csv`: maximo de expediciones en curso por hora (modulo 24 h).",
         "- `tablas/G2_ida_vuelta.csv`: histograma de la distancia fin de ida - inicio de vuelta.",
         "- `tablas/G3_distancias_electroterminales.csv`: distancia entre cada par de electroterminales.",
         "- `tablas/G4_diagrama_metodologia.csv`: contenido de cada caja del diagrama.",
         "- `tablas/G5_patio_vs_puestos.csv`: % y numero de buses en el patio y cargando, por hora (E1, 100%).",
         "- `tablas/G6_barrido.csv`: costo por nivel de bateria (E1).",
         "- `tablas/G7_reservas_milp.csv`: reservas, ganancia y brecha por tamano de instancia."]
    (RESULTS / "reporte.md").write_text("\n".join(L), encoding="utf-8")


def main():
    print("=== Graficos para la presentacion ===")
    for f in (g1_demanda_y_tarifa, g2_ida_vuelta, g3_mapa_electroterminales, g4_diagrama_metodologia, g5_patio_vs_puestos,
              g6_barrido, g7_reservas_milp):
        f()
        print(f"  [OK] {f.__name__}")
    reporte()
    print(f"  -> {GRAFICOS} | {TABLAS} | {RESULTS / 'reporte.md'}")


if __name__ == "__main__":
    main()
