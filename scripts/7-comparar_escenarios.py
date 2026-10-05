"""
Cierre de la Etapa 2 (ver docs/context/01_metodologia.md, seccion 5): compara la escalera de escenarios
E0 -> E1 -> LB y la sensibilidad del deadhead, y calcula el "precio del clustering" (cuanto paga cada configuracion
frente a la cota inferior LB).

No corre ningun modelo: lee los resumenes que va llenando scripts/6-vsp_asignacion_buses.py y las jornadas de E0 y E1.

TODOS los escenarios operacionales usan la asignacion C1b (el electroterminal mas cercano a los paraderos terminales
reales de cada ruta) y tratan Los Espinos y Santa Rosa como UN solo electroterminal (infraestructura de carga
compartida; sin unirlos, Los Espinos no tiene puestos para reponer su energia: ver Etapa 3).

Escalera (cada escalon cambia UNA decision):
  E0  caso base: operacion por linea (sin interlining), terminales unidos
  E1  + interlining dentro del electroterminal (configuracion propuesta)
  LB  cota inferior: interlining libre y sin retorno al electroterminal (NO es un escenario operacional)

Evidencia de por que se unen: E0_sep y E1_sep (mismos escenarios con terminales separados). En el VSP unir baja la flota
solo con interlining (E1_sep -> E1); el efecto fuerte esta en la carga (deficit de energia, Etapa 3).

Variantes con C2 (la asignacion con restriccion de capacidad, PROPUESTA; fuera de la escalera): E1_C2 (unidos) y
E1_C2_sep (separados).

Sensibilidad (sobre E1): factor de desvio del deadhead y layover.

Requiere haber corrido antes (ver docstring de 6-):
    E0, E1, LB, E0_sep, E1_sep, E1_C2, E1_C2_sep -> tablas/resumen_escenarios.csv
    E1_f1.2, E1_f1.35, E1_f1.5, E1_l0, E1_l10, E1_r1, E1_r2, E1_r4, E1_r5 (con --sin-jornadas y --unir-electroterminales)
                                                  -> tablas/resumen_sensibilidad.csv

Input:  results/etapa2_vsp/tablas/{resumen_escenarios,resumen_sensibilidad}.csv,
        data-processed/{jornadas_E0,jornadas_E1,rutas_cluster_c1b,rutas_cluster_c2}.csv
Output: results/etapa2_vsp/tablas/{escalera_escenarios,precio_del_clustering,variantes_c2,evidencia_union,
            sensibilidad_deadhead}.csv
        results/etapa2_vsp/graficos/{escalera_buses,escalera_costo,
            sensibilidad_deadhead,energia_por_jornada_E0_E1}.png
        results/etapa2_vsp/reporte.md

Uso:
    python scripts/7-comparar_escenarios.py
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
from common.rutas import CSV_SEP, DATA_PROCESSED, carpeta_resultados      # noqa: E402

RESULTS = carpeta_resultados("etapa2_vsp")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)

# Cota inferior teorica: maximo de expediciones simultaneas (ningun plan puede usar menos
# buses), ver results/etapa0_preprocesamiento/reporte.md.
COTA_INFERIOR_TEORICA = 6539

ESCALERA = ["E0", "E1", "LB"]
VARIANTES_C2 = ["E1_C2", "E1_C2_sep"]
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
            raise SystemExit(f"No existe {p}. Correr antes los escenarios de scripts/6-vsp_asignacion_buses.py "
                              f"(ver docstring de este script).")
    esc = pd.read_csv(p1, sep=CSV_SEP).set_index("etiqueta")
    sens = pd.read_csv(p2, sep=CSV_SEP).set_index("etiqueta")
    faltan = [e for e in ESCALERA + VARIANTES_C2 + SEPARADOS if e not in esc.index]
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


def escribir_reporte(t, s, esc):
    def fila_marg(a, b):
        return {"escalon": f"{a} -> {b}", "buses": t.loc[b, "buses"] - t.loc[a, "buses"],
                "buses_pct": round((t.loc[b, "buses"] / t.loc[a, "buses"] - 1) * 100, 2),
                "costo_operacion_usd": t.loc[b, "cost_operacion_usd"] - t.loc[a, "cost_operacion_usd"],
                "costo_pct": round((t.loc[b, "cost_operacion_usd"] / t.loc[a, "cost_operacion_usd"] - 1) * 100, 2)}
    marg = pd.DataFrame([fila_marg("E0", "E1"), fila_marg("E1", "LB")])
    sob = [c for c in esc.columns if c.startswith("pct_jornadas_sobre_bateria_")]
    sobre = esc.loc[["E0", "E1"], sob].rename(columns=lambda c: c.replace("pct_jornadas_sobre_bateria_", "nivel ") + "%")

    def mi(v):   # miles con punto, como se escribe en espanol
        return f"{v:,.0f}".replace(",", ".")
    share_e1 = (t.loc["E0", "buses"] - t.loc["E1", "buses"]) / (t.loc["E0", "buses"] - t.loc["LB", "buses"])
    c2 = pd.read_csv(DATA_PROCESSED / "rutas_cluster_c2.csv", sep=CSV_SEP, dtype={"depot_id": str})
    c1b = pd.read_csv(DATA_PROCESSED / "rutas_cluster_c1b.csv", sep=CSV_SEP, dtype={"depot_id": str})
    movidas = int((c2["depot_id"].values != c1b.set_index("route_id").loc[c2["route_id"].values, "depot_id"].values).sum())
    n_unidas = int(c1b["depot_id"].isin(parametros.ELECTROTERMINALES_UNIDOS).sum())
    unir = esc.loc[["E0_sep", "E0", "E1_sep", "E1"], ["buses", "cost_operacion_usd", "jornadas_cruzan_patio"]]
    var = esc.loc[VARIANTES_C2, ["buses", "cost_operacion_usd", "jornadas_cruzan_patio"]].copy()
    var["delta_buses_vs_escalera"] = [esc.loc["E1_C2", "buses"] - t.loc["E1", "buses"],
                                      esc.loc["E1_C2_sep", "buses"] - esc.loc["E1_sep", "buses"]]
    var["delta_costo_vs_escalera_usd"] = [esc.loc["E1_C2", "cost_operacion_usd"] - t.loc["E1", "cost_operacion_usd"],
                                          esc.loc["E1_C2_sep", "cost_operacion_usd"] - esc.loc["E1_sep", "cost_operacion_usd"]]
    base_f = s[s["parametro"] == "factor de desvio"]
    base_l = s[s["parametro"] == "layover (min)"]
    base_r = s[s["parametro"] == "radio de interlining (km)"].set_index("valor")
    lineas = [
        "# Reporte Etapa 2 - Asignacion de buses (VSP, sin bateria)",
        "",
        "Escalera de escenarios (cada escalon cambia una sola decision) y sensibilidad del deadhead. La asignacion de "
        "electroterminales es C1b (el mas cercano a los paraderos terminales reales de cada ruta) y Los Espinos y Santa "
        "Rosa se tratan como UN solo electroterminal en todos los escenarios operacionales. El costo de operacion es "
        "flota + km sin pasajeros + espera; no incluye la energia (Etapa 3) ni los km con pasajeros (iguales en todos los "
        "escenarios).",
        "",
        "## Escalera de escenarios",
        "",
        t[["buses", "km_vacios_total", "pct_km_vacios", "espera_h", "cost_operacion_usd",
           "brecha_buses_vs_LB_pct", "brecha_costo_vs_LB_pct", "jornadas_sin_retorno"]].round(2).to_markdown(),
        "",
        "## Efecto marginal de cada decision",
        "",
        marg.to_markdown(index=False),
        "",
        f"- **E0 -> E1 (interlining):** concentra la mayor parte de la ganancia posible: {mi(marg.iloc[0]['buses'])} buses "
        f"({marg.iloc[0]['costo_pct']:.1f}% del costo de operacion), {share_e1:.0%} de lo que separa a E0 de LB. "
        f"Los km de interlining suben ({mi(t.loc['E0', 'km_interlining'])} -> {mi(t.loc['E1', 'km_interlining'])} km: "
        f"los buses se desplazan para encadenar viajes), pero los km de pullout/pullin bajan mas "
        f"({mi(t.loc['E0', 'km_pullout'] + t.loc['E0', 'km_pullin'])} -> "
        f"{mi(t.loc['E1', 'km_pullout'] + t.loc['E1', 'km_pullin'])} km, porque hay menos buses que salgan y vuelvan): "
        f"el total de km sin pasajeros baja ({mi(t.loc['E0', 'km_vacios_total'])} -> {mi(t.loc['E1', 'km_vacios_total'])} km). "
        f"En E1, {mi(t.loc['E1', 'jornadas_cruzan_patio'])} jornadas salen de un patio y vuelven al otro del terminal unido "
        "(estan a 1,1 km; no viola el retorno porque es un solo electroterminal).",
        f"- **E1 -> LB:** quedan {mi(t.loc['E1', 'brecha_buses_vs_LB'])} buses sobre la cota inferior "
        f"({t.loc['E1', 'brecha_buses_vs_LB_pct']:.1f}%): es el precio de exigir el retorno al electroterminal y de limitar el "
        f"interlining al grupo. LB NO es operacional: {mi(esc.loc['LB', 'jornadas_sin_retorno'])} de sus "
        f"{mi(t.loc['LB', 'buses'])} jornadas terminan en un electroterminal distinto al de salida.",
        f"- Todos quedan sobre la cota teorica de {mi(COTA_INFERIOR_TEORICA)} (maximo de expediciones simultaneas).",
        "",
        "## Evidencia de por que se unen Los Espinos y Santa Rosa (separados vs unidos)",
        "",
        unir.to_markdown(),
        "",
        f"En el VSP unir no cambia E0 (cada ruta encadena solo consigo misma) y baja {mi(esc.loc['E1_sep', 'buses'] - t.loc['E1', 'buses'])} "
        f"buses en E1: las {n_unidas} rutas de ambos terminales pasan a poder encadenarse entre si. El efecto decisivo esta en la "
        "carga (Etapa 3): sin unir, Los Espinos tiene deficit de energia por falta de puestos y la solucion es infactible.",
        "",
        "## Variantes con C2 (asignacion con restriccion de capacidad; propuesta, fuera de la escalera)",
        "",
        var.to_markdown(),
        "",
        f"C2 mueve {movidas} rutas respecto de C1b para respetar la capacidad de carga de Los Espinos. En el VSP casi no "
        f"cambia nada ({mi(var.loc['E1_C2', 'delta_buses_vs_escalera'])} buses en E1_C2 frente a E1; "
        f"{mi(var.loc['E1_C2_sep', 'delta_buses_vs_escalera'])} en E1_C2_sep frente a E1_sep): el VSP no ve la capacidad. Su "
        "efecto aparece en la carga (Etapa 3). Se mantiene como propuesta y no como base (ver "
        "`docs/justificaciones/05_unir_terminales.md`).",
        "",
        "## Sensibilidad del deadhead (sobre E1)",
        "",
        s.drop(columns=["etiqueta"]).to_markdown(index=False),
        "",
        f"- **Factor de desvio** (1,2 a 1,5): la flota varia {base_f['delta_buses_vs_base_pct'].min():+.1f}% a "
        f"{base_f['delta_buses_vs_base_pct'].max():+.1f}% y el costo {base_f['delta_costo_vs_base_pct'].min():+.1f}% a "
        f"{base_f['delta_costo_vs_base_pct'].max():+.1f}%. El 1,3 importa poco para el tamano de la flota. "
        "Ojo: el radio de interlining (3 km) se compara contra la distancia ya multiplicada por el factor, asi que "
        "cambiarlo tambien cambia que encadenamientos se permiten. 1,35 es el valor medido a la escala de pullout/pullin "
        "(Bloque B).",
        f"- **Layover** (0 a 10 min): la flota varia {base_l['delta_buses_vs_base_pct'].min():+.1f}% a "
        f"{base_l['delta_buses_vs_base_pct'].max():+.1f}%: uno de los dos supuestos mas sensibles de la Etapa 2 (con el radio de interlining). Esta sin calibrar "
        "(3 min, decision nuestra); es la mejor candidata a declarar como limitacion y a calibrar despues.",
        f"- **Radio de interlining** (1 a 5 km): la flota va de {mi(base_r.loc[1, 'buses'])} ({base_r.loc[1, 'delta_buses_vs_base_pct']:+.1f}%) con 1 km a "
        f"{mi(base_r.loc[5, 'buses'])} ({base_r.loc[5, 'delta_buses_vs_base_pct']:+.1f}%) con 5 km, frente a {mi(base_r.loc[3, 'buses'])} con el 3 km del modelo; el costo de operacion "
        f"{base_r.loc[1, 'delta_costo_vs_base_pct']:+.1f}% a {base_r.loc[5, 'delta_costo_vs_base_pct']:+.1f}%, y el tiempo de computo pasa de {base_r.loc[1, 'tiempo_computo_s']:.0f} s a "
        f"{base_r.loc[5, 'tiempo_computo_s']:.0f} s. Los retornos son decrecientes (cada km extra ahorra menos buses que el anterior). **No es un supuesto inocuo:** "
        "el 3 km es una decision de tamano del modelo (acota los arcos y el tiempo), no una medicion; ampliarlo mejora el VSP y queda como mejora para la entrega final "
        "(habria que rehacer la carga con jornadas mas largas).",
        "",
        "## Energia por jornada (descriptivo)",
        "",
        "Porcentaje de jornadas cuya energia supera la bateria util segun el nivel de partida (las que necesitan "
        "recargar durante el dia). La eleccion del nivel base se hace con el barrido de la Etapa 3 (costo total), "
        "no con esta tabla.",
        "",
        sobre.round(1).to_markdown(),
        "",
        "## Archivos",
        "",
        "Tablas (`tablas/`):",
        "- `resumen_escenarios.csv`: una fila por escenario con todos los parametros de la corrida (trazabilidad).",
        "- `resumen_sensibilidad.csv`: corridas de sensibilidad (sin jornadas).",
        "- `escalera_escenarios.csv`: la tabla de la escalera con efectos marginales y brechas contra LB y la cota.",
        "- `precio_del_clustering.csv`: buses y costo de E1 frente a LB.",
        "- `evidencia_union.csv`: separados vs unidos en el VSP (E0_sep, E0, E1_sep, E1).",
        "- `variantes_c2.csv`: las variantes con C2 (propuesta) frente a la escalera.",
        "- `sensibilidad_deadhead.csv`: la tabla de sensibilidad.",
        "",
        "Graficos (`graficos/`):",
        "- `escalera_buses.png`: buses por escenario, con el efecto de cada escalon y la cota teorica.",
        "- `escalera_costo.png`: costo de operacion apilado (flota / km vacios / espera) y de donde viene el ahorro.",
        "- `sensibilidad_deadhead.png`: flota vs factor de desvio, vs layover y vs radio de interlining.",
        "- `energia_por_jornada_E0_E1.png`: energia por jornada contra la bateria util de cada nivel.",
        "- `jornadas_<escenario>.png`: histogramas de energia y duracion de cada escenario.",
        "",
        "Jornadas (insumo de la Etapa 3): `data-processed/jornadas_{E0,E1,LB,E0_sep,E1_sep,E1_C2,E1_C2_sep}.csv`.",
    ]
    (RESULTS / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")


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
    esc.loc[VARIANTES_C2, cols_var].to_csv(TABLAS / "variantes_c2.csv", sep=CSV_SEP)
    esc.loc[["E0_sep", "E0", "E1_sep", "E1"], cols_var].to_csv(TABLAS / "evidencia_union.csv", sep=CSV_SEP)
    s.to_csv(TABLAS / "sensibilidad_deadhead.csv", index=False, sep=CSV_SEP)
    print(f"  -> {TABLAS}/ (escalera_escenarios, precio_del_clustering, variantes_c2, evidencia_union, sensibilidad_deadhead)")

    graficar_escalera_buses(t, GRAFICOS / "escalera_buses.png")
    graficar_escalera_costo(t, GRAFICOS / "escalera_costo.png")
    graficar_sensibilidad(s, GRAFICOS / "sensibilidad_deadhead.png")
    j0 = pd.read_csv(DATA_PROCESSED / "jornadas_E0.csv", sep=CSV_SEP)
    j1 = pd.read_csv(DATA_PROCESSED / "jornadas_E1.csv", sep=CSV_SEP)
    graficar_energia(j0, j1, costos, GRAFICOS / "energia_por_jornada_E0_E1.png")
    print(f"  -> {GRAFICOS}/ (4 graficos)")

    escribir_reporte(t, s, esc)
    print(f"  -> {RESULTS / 'reporte.md'}")

    print("\n=== Escalera ===")
    print(t[["buses", "delta_buses_vs_anterior", "cost_operacion_usd", "brecha_buses_vs_LB_pct",
             "jornadas_sin_retorno"]].to_string())
    print("\n=== Separados vs unidos y variantes C2 ===")
    print(esc.loc[["E0_sep", "E0", "E1_sep", "E1"] + VARIANTES_C2, ["buses", "cost_operacion_usd", "jornadas_cruzan_patio"]].to_string())
    print("\n=== Sensibilidad (E1) ===")
    print(s[["parametro", "valor", "buses", "delta_buses_vs_base_pct", "delta_costo_vs_base_pct"]].to_string(index=False))

    # --- Chequeos de sanidad ---
    b = t["buses"]
    assert b["E0"] >= b["E1"] >= b["LB"] >= COTA_INFERIOR_TEORICA, (
        "Orden inesperado entre escenarios: se esperaba E0 >= E1 >= LB >= cota teorica. Revisar si algun escenario "
        "se corrio con parametros distintos (radio, factor, layover, subset).")
    assert esc.loc["E0_sep", "buses"] == b["E0"], "En modo ruta unir terminales no debe cambiar el VSP (E0 == E0_sep)."
    assert esc.loc["E1_sep", "buses"] >= b["E1"], "Unir terminales no deberia aumentar la flota del VSP (E1_sep >= E1)."
    operacionales = ["E0", "E1", "E0_sep", "E1_sep"] + VARIANTES_C2
    assert (esc.loc[operacionales, "jornadas_sin_retorno"] == 0).all(), \
        "Un escenario operacional tiene jornadas que no vuelven a su electroterminal."
    assert t.loc["LB", "jornadas_sin_retorno"] > 0, \
        "Se esperaba que LB violara el retorno en alguna jornada (si no, no seria una cota inferior)."
    for etq in ESCALERA + VARIANTES_C2 + SEPARADOS:
        assert pd.isna(esc.loc[etq, "subset"]) or esc.loc[etq, "subset"] == "", \
            f"{etq} se corrio sobre un subconjunto de rutas (checkpoint), no sobre la red completa."
        assert esc.loc[etq, "n_expediciones"] == 64502, f"{etq}: {esc.loc[etq, 'n_expediciones']} expediciones, se esperaban 64502."
    for etq in ("E0", "E1"):
        assert esc.loc[etq, "asignacion"] == "rutas_cluster_c1b.csv" and str(esc.loc[etq, "unir"]).strip() == "3,5", \
            f"{etq} debe correr con la asignacion C1b y los electroterminales 3 y 5 unidos."
    print("\n  [OK] Orden de escenarios consistente (E0 >= E1 >= LB >= cota teorica); retorno cumplido en todos los operacionales.")
    print("\n=== FIN ETAPA 2 (cierre) ===")


if __name__ == "__main__":
    main()
