"""
Graficos de los datos y del caso base para el informe. No corre ningun modelo: lee resultados ya calculados. Cada grafico
tiene su CSV con los datos.

  G1  Demanda de buses por hora y periodos tarifarios (Figura 2.1 del informe)
  G2  Cierre ida-vuelta de las rutas (94,7% a menos de 500 m)
  G5  Buses en el patio frente a puestos ocupados, por hora (caso base con interlining)
  G6  Barrido de niveles de bateria (caso base con interlining)
  y la tabla de distancias entre electroterminales (Los Espinos y Santa Rosa distan 1,1 km)

Los graficos de las Etapas 3-4 y de los KPIs (F0-F6) los genera 12-kpis_instancia.py.

Input:  resultados/etapa0_preprocesamiento/concurrencia_por_minuto.csv, resultados/datos_procesados/rutas_ida_vuelta.csv,
        resultados/datos_filtrados/{depots,electricity_prices}.csv,
        resultados/caso_base/tablas/{jornadas,ocupacion}_E1_soc100.csv, resultados/caso_base/barrido/tablas/barrido_niveles.csv
Output: resultados/graficos_datos/graficos/G<k>_<nombre>.png y resultados/graficos_datos/tablas/G<k>_<nombre>.csv

Uso:
    python 13-graficos_datos.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import geo, parametros                                                     # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, RESULTS_DIR, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("graficos_datos")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)
R0 = RESULTS_DIR / "etapa0_preprocesamiento"
R3 = RESULTS_DIR / "caso_base"

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
    print(f"  Maximo de expediciones en curso: {int(conc.max()):,} a las {pico_min // 60}:{pico_min % 60:02d}; "
          f"maximo de la hora 18: {int(hora.loc[18, 'expediciones_en_curso_max']):,}")
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
def distancias_electroterminales():
    """Distancia entre cada par de electroterminales. El par mas cercano (Los Espinos y Santa Rosa) se trata como uno."""
    dep = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    n = len(dep)
    pares = sorted((float(geo.haversine_km(dep.lat[i], dep.lon[i], dep.lat[j], dep.lon[j])), dep.nombre[i], dep.nombre[j])
                   for i in range(n) for j in range(i + 1, n))
    tabla = pd.DataFrame(pares, columns=["distancia_km", "electroterminal_a", "electroterminal_b"]).round(2)
    tabla.to_csv(TABLAS / "G3_distancias_electroterminales.csv", index=False, sep=CSV_SEP)
    assert {pares[0][1], pares[0][2]} == {"Los Espinos", "Santa Rosa"}, "El par mas cercano no es Los Espinos - Santa Rosa."
    print(tabla.to_string(index=False))


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


def main():
    print("=== Graficos de datos y del caso base ===")
    for f in (g1_demanda_y_tarifa, g2_ida_vuelta, distancias_electroterminales, g5_patio_vs_puestos, g6_barrido):
        f()
        print(f"  [OK] {f.__name__}")
    print(f"  -> {GRAFICOS} | {TABLAS}")


if __name__ == "__main__":
    main()
