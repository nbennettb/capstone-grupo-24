"""
Cierre de la Etapa 2. No corre ningun modelo: lee los resumenes y las jornadas que deja 6-etapa2_jornadas.py y
compara la escalera de escenarios, la sensibilidad del deadhead y la evidencia de por que se unen Los Espinos y Santa Rosa.

Escalera (cada escalon cambia una decision):
  E0  caso base: operacion por linea, sin interlining
  E1  + interlining dentro del electroterminal
  LB  cota inferior: interlining libre y sin retorno al electroterminal (no es un escenario operacional)
Todos usan la asignacion C1b y tratan Los Espinos y Santa Rosa como un solo electroterminal; E0_sep y E1_sep son los
mismos escenarios con los terminales separados (evidencia).

Requiere haber corrido antes 6-etapa2_jornadas.py (ver correr_todo.py): E0, E1, LB, E0_sep y E1_sep, y las
sensibilidades E1_f1.2, E1_f1.35, E1_f1.5, E1_l0, E1_l10, E1_r1, E1_r2, E1_r4 y E1_r5 (con --sin-jornadas).

Input:  resultados/etapa2_vsp/tablas/{resumen_escenarios,resumen_sensibilidad}.csv,
        resultados/datos_procesados/jornadas_{E0,E1,E0_sep,E1_sep}.csv, resultados/datos_filtrados/depots.csv
Output: resultados/etapa2_vsp/tablas/{escalera_escenarios,precio_del_clustering,evidencia_union,
            energia_vs_capacidad,sensibilidad_deadhead}.csv
        resultados/etapa2_vsp/graficos/{escalera_buses,escalera_costo,sensibilidad_deadhead,energia_por_jornada_E0_E1}.png
Consola: escalera, efecto de cada decision, sensibilidades (Supuestos 2.4.1 y 2.4.2) y evidencia de la union (Seccion 2.3).

Uso:
    python 7-etapa2_comparar_escenarios.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parametros                                              # noqa: E402
from common.rutas import CSV_SEP, DATA_FILTRADO, DATA_PROCESSED, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa2_vsp")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)

# Cota inferior teorica: maximo de expediciones simultaneas (ningun plan puede usar menos buses); lo imprime el script 3.
COTA_INFERIOR_TEORICA = 6539

ESCALERA = ["E0", "E1", "LB"]
SEPARADOS = ["E0_sep", "E1_sep"]
NOMBRES = {
    "E0": "E0\nCaso base\n(por linea, unidos)",
    "E1": "E1\n+ interlining\n(unidos)",
    "LB": "LB\nCota inferior\n(no operacional)",
}
COLORES = {"E0": "#8f4a2c", "E1": "#2c6e8f", "LB": "#9a9a9a"}
C_FLOTA, C_KM, C_ESPERA = "#2c6e8f", "#d95f02", "#7f7f7f"

SENSIBILIDAD = [  # (etiqueta, parametro, valor)
    ("E1_f1.2", "factor de desvio", 1.2),
    ("E1", "factor de desvio", 1.3),
    ("E1_f1.35", "factor de desvio", 1.35),
    ("E1_f1.5", "factor de desvio", 1.5),
    ("E1_l0", "layover (min)", 0),
    ("E1", "layover (min)", 3),
    ("E1_l10", "layover (min)", 10),
    ("E1_r1", "radio de interlining (km)", 1),
    ("E1_r2", "radio de interlining (km)", 2),
    ("E1", "radio de interlining (km)", 3),
    ("E1_r4", "radio de interlining (km)", 4),
    ("E1_r5", "radio de interlining (km)", 5),
]


def estilo(ax, grilla="y"):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis=grilla, color="#e5e5e5", linewidth=0.7)
    ax.set_axisbelow(True)


def cargar_resumenes():
    p1, p2 = TABLAS / "resumen_escenarios.csv", TABLAS / "resumen_sensibilidad.csv"
    for p in (p1, p2):
        if not p.exists():
            raise SystemExit(f"No existe {p}. Correr antes los escenarios de 6-etapa2_jornadas.py (ver docstring).")
    esc = pd.read_csv(p1, sep=CSV_SEP).set_index("etiqueta")
    sens = pd.read_csv(p2, sep=CSV_SEP).set_index("etiqueta")
    faltan = [e for e in ESCALERA + SEPARADOS if e not in esc.index]
    if faltan:
        raise SystemExit(f"Faltan escenarios en {p1.name}: {faltan}.")
    faltan = [e for e, _, _ in SENSIBILIDAD if e != "E1" and e not in sens.index]
    if faltan:
        raise SystemExit(f"Faltan corridas de sensibilidad en {p2.name}: {faltan}.")
    return esc, sens


def construir_escalera(esc):
    t = esc.loc[ESCALERA, ["buses", "km_pullout", "km_interlining", "km_pullin", "km_vacios_total",
                           "pct_km_vacios", "espera_h", "cost_bus_usd", "cost_km_vacios_usd",
                           "cost_espera_usd", "cost_operacion_usd", "jornadas_cruzan_patio",
                           "jornadas_sin_retorno"]].copy()
    suma = t["cost_bus_usd"] + t["cost_km_vacios_usd"] + t["cost_espera_usd"]
    assert ((suma - t["cost_operacion_usd"]).abs() <= 3).all(), \
        "El costo de operacion no es la suma de flota + km vacios + espera en alguna fila."
    t["delta_buses_vs_anterior"] = t["buses"].diff()
    t["delta_costo_vs_anterior_usd"] = t["cost_operacion_usd"].diff()
    t["delta_costo_vs_anterior_pct"] = (t["cost_operacion_usd"].pct_change() * 100).round(2)
    t["brecha_buses_vs_LB"] = t["buses"] - t.loc["LB", "buses"]
    t["brecha_buses_vs_LB_pct"] = (t["brecha_buses_vs_LB"] / t.loc["LB", "buses"] * 100).round(2)
    t["brecha_costo_vs_LB_pct"] = ((t["cost_operacion_usd"] / t.loc["LB", "cost_operacion_usd"] - 1) * 100).round(2)
    t["brecha_buses_vs_cota_teorica"] = t["buses"] - COTA_INFERIOR_TEORICA
    return t


def construir_sensibilidad(esc, sens):
    base = esc.loc["E1"]
    filas = []
    for etq, param, valor in SENSIBILIDAD:
        r = esc.loc[etq] if etq == "E1" else sens.loc[etq]
        filas.append({"parametro": param, "valor": valor, "etiqueta": etq, "buses": int(r["buses"]),
                      "delta_buses_vs_base": int(r["buses"] - base["buses"]),
                      "delta_buses_vs_base_pct": round((r["buses"] / base["buses"] - 1) * 100, 2),
                      "cost_operacion_usd": r["cost_operacion_usd"],
                      "delta_costo_vs_base_pct": round((r["cost_operacion_usd"] / base["cost_operacion_usd"] - 1) * 100, 2),
                      "km_vacios_total": r["km_vacios_total"], "pct_km_vacios": r["pct_km_vacios"],
                      "tiempo_computo_s": round(float(r["tiempo_computo_s"]), 1)})
    return pd.DataFrame(filas)


def graficar_escalera_buses(t, path_png):
    fig, ax = plt.subplots(figsize=(10, 5.3))
    x = np.arange(len(ESCALERA))
    for i, e in enumerate(ESCALERA):
        ax.bar(i, t.loc[e, "buses"], width=0.6, color=COLORES[e], hatch="//" if e == "LB" else None,
               edgecolor="white" if e != "LB" else "#666666", linewidth=0.6)
        ax.text(i, t.loc[e, "buses"] + 60, f"{t.loc[e, 'buses']:,.0f}".replace(",", "."), ha="center",
                fontsize=10, fontweight="bold")
        if i > 0 and e != "LB":
            d = t.loc[e, "delta_buses_vs_anterior"]
            ax.text(i, t.loc[e, "buses"] / 2, f"{d:+,.0f}".replace(",", ".") + "\nvs escalon\nanterior",
                    ha="center", va="center", color="white", fontsize=9)
    ax.axhline(COTA_INFERIOR_TEORICA, color="#b22222", linestyle="--", linewidth=1.3,
               label=f"Cota teorica: maximo de expediciones simultaneas ({COTA_INFERIOR_TEORICA:,})".replace(",", "."))
    ax.set_xticks(x)
    ax.set_xticklabels([NOMBRES[e] for e in ESCALERA], fontsize=9)
    ax.set_ylabel("Buses necesarios")
    ax.set_ylim(0, t["buses"].max() * 1.12)
    ax.set_title("Escalera de escenarios: buses necesarios (Etapa 2, sin bateria)")
    ax.legend(frameon=False, loc="upper right")
    estilo(ax)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_escalera_costo(t, path_png):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.3), gridspec_kw={"width_ratios": [1.2, 1]})
    x = np.arange(len(ESCALERA))
    comp = [("cost_bus_usd", "Flota (250 USD/bus)", C_FLOTA), ("cost_km_vacios_usd", "Km sin pasajeros", C_KM),
            ("cost_espera_usd", "Espera", C_ESPERA)]
    fondo = np.zeros(len(ESCALERA))
    for col, nombre, color in comp:
        v = t[col].values / 1e6
        ax1.bar(x, v, bottom=fondo, width=0.6, color=color, label=nombre, edgecolor="white", linewidth=0.6)
        fondo += v
    for i, e in enumerate(ESCALERA):
        ax1.text(i, fondo[i] + 0.03, f"{t.loc[e, 'cost_operacion_usd'] / 1e6:.2f} M", ha="center", fontsize=9,
                 fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels([e for e in ESCALERA])
    ax1.set_ylabel("Costo de operacion (millones de USD / dia)")
    ax1.set_ylim(0, fondo.max() * 1.12)
    ax1.set_title("Costo de operacion por escenario")
    ax1.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=9)
    estilo(ax1)

    ancho = 0.26
    for j, (col, nombre, color) in enumerate(comp):
        dif = (t[col] - t.loc["E0", col]).values[1:] / 1e3
        ax2.bar(np.arange(1, len(ESCALERA)) + (j - 1) * ancho, dif, width=ancho, color=color, label=nombre)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_xticks(np.arange(1, len(ESCALERA)))
    ax2.set_xticklabels(ESCALERA[1:])
    ax2.set_ylabel("Diferencia respecto de E0 (miles de USD / dia)")
    ax2.set_title("De donde viene el ahorro frente al caso base")
    estilo(ax2)
    fig.suptitle("Etapa 2: costo de operacion = flota + km sin pasajeros + espera (sin energia ni km con pasajeros)")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_sensibilidad(s, path_png):
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, param, xlab in zip(axs, ("factor de desvio", "layover (min)", "radio de interlining (km)"),
                               ("Factor de desvio del deadhead", "Layover minimo (min)", "Radio maximo de interlining (km)")):
        d = s[s["parametro"] == param].sort_values("valor")
        ax.plot(d["valor"], d["buses"], "o-", color="#2c6e8f", linewidth=1.8, markersize=6)
        base = d[d["delta_buses_vs_base"] == 0].iloc[0]
        ax.plot([base["valor"]], [base["buses"]], "o", color="#b22222", markersize=9, zorder=4, label="valor del modelo")
        for _, f in d.iterrows():
            ax.annotate(f"{f['buses']:,.0f}\n({f['delta_buses_vs_base_pct']:+.1f}%)".replace(",", "."),
                        (f["valor"], f["buses"]), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8)
        ax.set_xlabel(xlab)
        ax.set_ylabel("Buses necesarios (E1)")
        ax.set_xticks(d["valor"])
        ymin, ymax = s["buses"].min(), s["buses"].max()
        ax.set_ylim(ymin - (ymax - ymin) * 0.15, ymax + (ymax - ymin) * 0.2)
        estilo(ax)
    axs[0].legend(frameon=False, loc="lower right")
    fig.suptitle("Sensibilidad de la flota (E1): el factor de desvio mueve poco; el layover y el radio de interlining, mucho mas\n"
                 "(mismo eje vertical en los tres paneles)")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_energia(j0, j1, costos, path_png):
    fig, ax = plt.subplots(figsize=(10, 5))
    bins = np.linspace(0, max(j0["kwh_total"].max(), j1["kwh_total"].max()), 50)
    ax.hist(j0["kwh_total"], bins=bins, histtype="step", linewidth=1.8, color=COLORES["E0"],
            label=f"E0 ({len(j0):,} jornadas)".replace(",", "."))
    ax.hist(j1["kwh_total"], bins=bins, histtype="step", linewidth=1.8, color=COLORES["E1"],
            label=f"E1 ({len(j1):,} jornadas)".replace(",", "."))
    ymax = ax.get_ylim()[1]
    ax.set_ylim(0, ymax * 1.18)
    for i, soc in enumerate(parametros.SOC_CICLICO_BARRIDO):
        kwh = costos.bateria_util_ciclica_kwh(soc)
        ax.axvline(kwh, color="#b22222", linestyle="--", linewidth=1)
        # alturas escalonadas para que las etiquetas contiguas (35 kWh de separacion) no se pisen
        ax.text(kwh, ymax * 1.16, f"{soc:.0%}", color="#b22222", fontsize=9, va="top", ha="center",
                bbox=dict(facecolor="white", edgecolor="none", pad=1.0))
    ax.set_xlabel("Energia consumida por jornada (kWh)")
    ax.set_ylabel("Numero de jornadas")
    kwhs = " / ".join(f"{costos.bateria_util_ciclica_kwh(s):.0f}" for s in reversed(parametros.SOC_CICLICO_BARRIDO))
    niveles = " / ".join(f"{s:.0%}" for s in reversed(parametros.SOC_CICLICO_BARRIDO))
    ax.set_title("La bateria no alcanza para el dia: energia por jornada vs bateria util\n"
                 f"lineas rojas = {kwhs} kWh (niveles de partida {niveles})\n"
                 "descriptivo: el nivel se elige con el barrido de la Etapa 3", fontsize=10)
    ax.legend(frameon=False, loc="center right")
    estilo(ax)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def energia_vs_capacidad(costos):
    """Energia de las jornadas de cada electroterminal frente a lo que sus puestos entregan en 24 h, con los terminales
    separados y unidos. Con mas de 100% el electroterminal no alcanza a reponer su energia."""
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP, dtype={"depot_id": str})
    unidos = set(parametros.ELECTROTERMINALES_UNIDOS)
    nombre = dict(zip(depots["depot_id"], depots["nombre"]))
    filas = []
    for etq in ("E0_sep", "E1_sep", "E0", "E1"):
        j = pd.read_csv(DATA_PROCESSED / f"jornadas_{etq}.csv", sep=CSV_SEP, dtype={"depot_salida": str})
        union = not etq.endswith("_sep")
        grupo = j["depot_salida"].map(lambda d: "+".join(sorted(unidos)) if union and d in unidos else d)
        mwh = j.groupby(grupo)["kwh_total"].sum() / 1000
        for g, e in mwh.items():
            ids = g.split("+")
            puestos = int(depots.loc[depots["depot_id"].isin(ids), "capacity"].sum())
            cap = puestos * costos.charge_power_kw * 24 / 1000
            filas.append(dict(escenario=etq, electroterminal=" + ".join(nombre[i] for i in ids), puestos=puestos,
                              energia_mwh=round(e, 1), capacidad_24h_mwh=round(cap, 1), uso_pct=round(e / cap * 100, 1)))
    return pd.DataFrame(filas)


def imprimir_resultados(t, s, esc, ev):
    """Cifras de las Secciones 2.3 y 2.4 del informe."""
    def mi(v):
        return f"{v:,.0f}".replace(",", ".")
    marg = pd.DataFrame([
        {"escalon": f"{a} -> {b}", "buses": t.loc[b, "buses"] - t.loc[a, "buses"],
         "buses_pct": round((t.loc[b, "buses"] / t.loc[a, "buses"] - 1) * 100, 2),
         "costo_operacion_usd": t.loc[b, "cost_operacion_usd"] - t.loc[a, "cost_operacion_usd"],
         "costo_pct": round((t.loc[b, "cost_operacion_usd"] / t.loc[a, "cost_operacion_usd"] - 1) * 100, 2)}
        for a, b in (("E0", "E1"), ("E1", "LB"))])
    print("\n=== Escalera de escenarios (Etapa 2, sin bateria) ===")
    print(t[["buses", "km_vacios_total", "pct_km_vacios", "espera_h", "cost_operacion_usd", "brecha_buses_vs_LB_pct",
             "jornadas_sin_retorno"]].round(2).to_string())
    print("\n=== Efecto de cada decision ===")
    print(marg.to_string(index=False))
    print(f"  E1 queda {mi(t.loc['E1', 'brecha_buses_vs_LB'])} buses ({t.loc['E1', 'brecha_buses_vs_LB_pct']:.1f}%) sobre la cota "
          f"inferior LB; todos quedan sobre la cota teorica de {mi(COTA_INFERIOR_TEORICA)} buses.")
    print("\n=== Terminales separados vs unidos (flota del VSP) ===")
    print(esc.loc[["E0_sep", "E0", "E1_sep", "E1"], ["buses", "cost_operacion_usd", "jornadas_cruzan_patio"]].to_string())
    print("\n=== Energia de las jornadas / capacidad de los puestos en 24 h ===")
    print(ev.to_string(index=False))
    print("\n=== Sensibilidad del deadhead sobre E1 (Supuestos 2.4.1 y 2.4.2) ===")
    print(s[["parametro", "valor", "buses", "delta_buses_vs_base_pct", "cost_operacion_usd", "delta_costo_vs_base_pct",
             "tiempo_computo_s"]].to_string(index=False))
    sob = [c for c in esc.columns if c.startswith("pct_jornadas_sobre_bateria_")]
    print("\n=== % de jornadas cuya energia supera la bateria util segun el nivel de partida ===")
    print(esc.loc[["E0", "E1"], sob].rename(columns=lambda c: c.replace("pct_jornadas_sobre_bateria_", "nivel ") + "%")
          .round(1).to_string())


def main():
    esc, sens = cargar_resumenes()
    costos = parametros.cargar_costos()
    print("=== ETAPA 2 (cierre): escalera de escenarios y sensibilidad ===\n")

    t = construir_escalera(esc)
    s = construir_sensibilidad(esc, sens)
    t.to_csv(TABLAS / "escalera_escenarios.csv", sep=CSV_SEP)
    precio = t.loc[["E1"], ["buses", "brecha_buses_vs_LB", "brecha_buses_vs_LB_pct",
                            "cost_operacion_usd", "brecha_costo_vs_LB_pct"]]
    precio.to_csv(TABLAS / "precio_del_clustering.csv", sep=CSV_SEP)
    cols_var = ["modo", "asignacion", "unir", "buses", "km_vacios_total", "cost_operacion_usd",
                "jornadas_cruzan_patio", "jornadas_sin_retorno"]
    esc.loc[["E0_sep", "E0", "E1_sep", "E1"], cols_var].to_csv(TABLAS / "evidencia_union.csv", sep=CSV_SEP)
    ev = energia_vs_capacidad(costos)
    ev.to_csv(TABLAS / "energia_vs_capacidad.csv", index=False, sep=CSV_SEP)
    s.to_csv(TABLAS / "sensibilidad_deadhead.csv", index=False, sep=CSV_SEP)
    print(f"  -> {TABLAS}/ (escalera_escenarios, precio_del_clustering, evidencia_union, energia_vs_capacidad, sensibilidad_deadhead)")

    graficar_escalera_buses(t, GRAFICOS / "escalera_buses.png")
    graficar_escalera_costo(t, GRAFICOS / "escalera_costo.png")
    graficar_sensibilidad(s, GRAFICOS / "sensibilidad_deadhead.png")
    j0 = pd.read_csv(DATA_PROCESSED / "jornadas_E0.csv", sep=CSV_SEP)
    j1 = pd.read_csv(DATA_PROCESSED / "jornadas_E1.csv", sep=CSV_SEP)
    graficar_energia(j0, j1, costos, GRAFICOS / "energia_por_jornada_E0_E1.png")
    print(f"  -> {GRAFICOS}/ (4 graficos)")

    imprimir_resultados(t, s, esc, ev)

    # --- Chequeos de sanidad ---
    b = t["buses"]
    assert b["E0"] >= b["E1"] >= b["LB"] >= COTA_INFERIOR_TEORICA, (
        "Orden inesperado entre escenarios: se esperaba E0 >= E1 >= LB >= cota teorica. Revisar si algun escenario "
        "se corrio con parametros distintos (radio, factor, layover).")
    assert esc.loc["E0_sep", "buses"] == b["E0"], "En modo ruta unir terminales no debe cambiar el VSP (E0 == E0_sep)."
    assert esc.loc["E1_sep", "buses"] >= b["E1"], "Unir terminales no deberia aumentar la flota del VSP (E1_sep >= E1)."
    operacionales = ["E0", "E1", "E0_sep", "E1_sep"]
    assert (esc.loc[operacionales, "jornadas_sin_retorno"] == 0).all(), \
        "Un escenario operacional tiene jornadas que no vuelven a su electroterminal."
    assert t.loc["LB", "jornadas_sin_retorno"] > 0, \
        "Se esperaba que LB violara el retorno en alguna jornada (si no, no seria una cota inferior)."
    for etq in ESCALERA + SEPARADOS:
        assert esc.loc[etq, "n_expediciones"] == 64502, f"{etq}: {esc.loc[etq, 'n_expediciones']} expediciones, se esperaban 64502."
    for etq in ("E0", "E1"):
        assert esc.loc[etq, "asignacion"] == "rutas_cluster_c1b.csv" and str(esc.loc[etq, "unir"]).strip() == "3,5", \
            f"{etq} debe correr con la asignacion C1b y los electroterminales 3 y 5 unidos."
    print("\n  [OK] Orden de escenarios consistente (E0 >= E1 >= LB >= cota teorica); retorno cumplido en todos los operacionales.")
    print("\n=== FIN ETAPA 2 (cierre) ===")


if __name__ == "__main__":
    main()
