"""
Barrido de niveles de bateria de la condicion ciclica (Etapa 3) - ICS2122 Capstone Buses Electricos.

Aplica POR CODIGO la regla de B6 (docs/context/02_supuestos_y_decisiones.md; justificacion en
docs/justificaciones/04_nivel_carga_ciclico.md). La condicion ciclica (inicio = fin) es una RESTRICCION: el nivel se
elige entre las soluciones que la cumplen.

Version corregida el 04/10/2026, antes de volver a correr (la regla original comparaba contra el 100%, que es
infactible: dejaba ~21% de las cargas nocturnas sin terminar a tiempo):

  Escenario que decide: E1 (C1b, con interlining, Los Espinos y Santa Rosa unidos). E0 (por linea, unidos) es
  robustez. E0_sep y E1_sep (terminales separados) no compiten: son infactibles por deficit de energia y solo se
  muestran como evidencia de por que se unen.
  1. Grilla obligatoria: 100, 90, 80, 70, 65, 60, 55 y 50% (parametros.SOC_BARRIDO_EXTENDIDO; 50% es el piso fisico:
     el menor nivel con que toda expedicion puede hacerse partiendo y volviendo al electroterminal sin bajar del minimo).
  2. Factibilidad: solo compiten las soluciones FACTIBLES (sin deficit de energia y con todo atraso de carga menor a
     24 h). Un ciclo no cumplido se cubre con un BUS DE RESERVA ya cargado (250 USD cada uno): el costo total lo incluye.
  3. Dos familias, reportadas lado a lado:
       (a) ciclica SIN reservas: niveles con 0 ciclos no cumplidos;
       (b) CON reservas: todos los niveles factibles, con el costo de las reservas.
  4. Criterio: menor costo total (flota + km vacios + espera + energia + eventos de carga + reservas) entre todas las
     soluciones factibles de (a) y (b).
  5. Empate: si dos niveles difieren en menos de 0,5% del costo total, se elige el MAS ALTO.
  6. Robustez (no decide): se aplica la misma regla a E0.
Ademas se calcula, para cada nivel, la cota LP: maximo de energia de las cargas finales que cabe en las ventanas de
los buses con una carga PERFECTA. Si es menor a 100%, ningun programa de carga cierra el ciclo con esas jornadas.

Cada nivel se simula con scripts/10-carga_reactiva.py (en modo --solo-resumen, para no escribir tablas por nivel). Al
final se corre completo el nivel elegido para dejar todas sus tablas y graficos.

Input:  results/etapa3_carga_reactiva/tablas/resumen_carga.csv (lo llena 10-), results/etapa2_vsp/tablas/
        resumen_escenarios.csv, data-processed/{expediciones,jornadas_<esc>,rutas_cluster_c1b}.csv
Output: results/etapa3_carga_reactiva/barrido/tablas/{barrido_niveles,decision_barrido}.csv
        results/etapa3_carga_reactiva/barrido/graficos/{barrido_costo_total,barrido_ciclos_y_cota,
            barrido_robustez}.png
        results/etapa3_carga_reactiva/barrido/reporte_barrido.md

Uso:
    python scripts/13-barrido_niveles.py        # ~10 min: 16 simulaciones con cota LP + la corrida completa
"""

import math
import subprocess
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

SCRIPT_SIM = Path(__file__).resolve().parent / "10-carga_reactiva.py"
CARPETA = carpeta_resultados("etapa3_carga_reactiva")
RESUMEN_CARGA = CARPETA / "tablas" / "resumen_carga.csv"
RESUMEN_VSP = RESULTS_DIR / "etapa2_vsp" / "tablas" / "resumen_escenarios.csv"
SALIDA = CARPETA / "barrido"
TABLAS = SALIDA / "tablas"
GRAFICOS = SALIDA / "graficos"
TABLAS.mkdir(parents=True, exist_ok=True)
GRAFICOS.mkdir(parents=True, exist_ok=True)

ESCENARIO_PRINCIPAL = "E1"
ESCENARIOS_ROBUSTEZ = ["E0"]
ESCENARIOS_INFACTIBLES = ["E0_sep", "E1_sep"]      # se leen al 100% del resumen; no compiten
TOL_EMPATE = 0.005          # 0,5% del costo total
PASO_NIVEL = 10             # redondeo del piso fisico (puntos porcentuales)
NIVEL_MIN_COTA = 65         # la cota LP solo se calcula hasta este nivel (a niveles menores ya alcanza 100%)

COMPONENTES = [("costo_flota_usd", "Flota", "#2c6e8f"), ("costo_km_vacios_usd", "Km sin pasajeros", "#d95f02"),
               ("costo_espera_usd", "Espera", "#7f7f7f"), ("costo_energia_usd", "Energia", "#4a8f6e"),
               ("costo_eventos_usd", "Eventos de carga", "#8f4a2c"), ("costo_reservas_usd", "Buses de reserva", "#b22222")]
COLORES_ESC = {"E0": "#8f4a2c", "E1": "#2c6e8f"}


def estilo(ax, grilla="y"):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis=grilla, color="#e5e5e5", linewidth=0.7)
    ax.set_axisbelow(True)


# --------------------------------------------------------------------------- #
# Piso fisico y simulacion por nivel
# --------------------------------------------------------------------------- #

def piso_fisico_pct(esc, costos):
    """Menor nivel (multiplo de 10%) con que TODA expedicion puede hacerse partiendo de un electroterminal de su
    terminal y volviendo a el sin bajar del minimo: energia = (pullout + pullin) * consumo + kWh de la expedicion +
    minimo. Es el nivel desde el cual ningun bus nuevo (jornada partida) puede quedar sin poder cubrirla."""
    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    resumen = pd.read_csv(RESUMEN_VSP, sep=CSV_SEP, dtype={"unir": str}).set_index("etiqueta")
    asignacion = pd.read_csv(DATA_PROCESSED / resumen.loc[esc, "asignacion"], sep=CSV_SEP,
                             dtype={"route_id": str, "depot_id": str}).set_index("route_id")["depot_id"]
    unir = resumen.loc[esc, "unir"]
    unidos = {d.strip() for d in unir.split(",")} if isinstance(unir, str) and unir.strip() else set()
    depot_ids = depots["depot_id"].astype(str).tolist()
    DP = geo.xy(depots["lat"].values, depots["lon"].values)
    f = parametros.FACTOR_DESVIO
    dist_o = geo.matriz_distancias_planas(geo.xy(ex["o_lat"].values, ex["o_lon"].values), DP) * f
    dist_d = geo.matriz_distancias_planas(geo.xy(ex["d_lat"].values, ex["d_lon"].values), DP) * f
    depot_exp = ex["route_id"].astype(str).map(asignacion).values
    patios_de = np.zeros(dist_o.shape, dtype=bool)
    for i, d in enumerate(depot_ids):
        if d in unidos:
            patios_de[np.isin(depot_exp, list(unidos)), i] = True
        else:
            patios_de[depot_exp == d, i] = True
    po = np.where(patios_de, dist_o, np.inf).min(axis=1)
    pd_ = np.where(patios_de, dist_d, np.inf).min(axis=1)
    necesaria = (po + pd_) * parametros.CONSUMO_KWH_KM + ex["kwh"].values + costos.min_soc * costos.battery_kwh
    nivel = necesaria.max() / costos.battery_kwh
    return int(math.ceil(nivel * 100 / PASO_NIVEL - 1e-9) * PASO_NIVEL), float(nivel)


def fila_existente(esc, nivel_pct, cota):
    """Fila ya simulada en resumen_carga.csv (el simulador es determinista), si existe y trae la cota LP cuando se pide."""
    if not RESUMEN_CARGA.exists():
        return None
    resumen = pd.read_csv(RESUMEN_CARGA, sep=CSV_SEP)
    fila = resumen[(resumen["escenario"] == esc) & (resumen["soc_pct"] == nivel_pct)]
    if len(fila) != 1 or "buses_reserva" not in fila.columns or pd.isna(fila.iloc[0]["buses_reserva"]):
        return None
    if cota and pd.isna(fila.iloc[0].get("cota_lp_pct")):
        return None
    return fila.iloc[0].to_dict()


def simular_nivel(esc, nivel_pct, completo=False, cota=True):
    """Corre el simulador de carga para (escenario, nivel) y devuelve (fila_resumen o None, mensaje_error). Reutiliza
    la fila si ya se simulo (salvo en la corrida completa, que escribe tablas y graficos)."""
    if not completo:
        previa = fila_existente(esc, nivel_pct, cota)
        if previa is not None:
            return previa, ""
    cmd = [sys.executable, str(SCRIPT_SIM), "--escenario", esc, "--soc", f"{nivel_pct / 100:.2f}"]
    if not completo:
        cmd.append("--solo-resumen")
    if cota:
        cmd.append("--cota-lp")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        cola = " | ".join([l for l in (r.stderr or r.stdout).strip().splitlines() if l.strip()][-3:])
        return None, cola
    resumen = pd.read_csv(RESUMEN_CARGA, sep=CSV_SEP)
    fila = resumen[(resumen["escenario"] == esc) & (resumen["soc_pct"] == nivel_pct)]
    assert len(fila) == 1, f"No aparecio la fila de resumen de {esc} al {nivel_pct}%."
    return fila.iloc[0].to_dict(), ""


def linea_progreso(esc, n, f):
    estado = "factible" if f["factible"] else "INFACTIBLE"
    return (f"    {esc} {n:3d}%: buses {int(f['buses_final']):>6,} | reservas {int(f['buses_reserva']):>5,} | deficit "
            f"{f['kwh_deficit'] / 1000:5.1f} MWh | cota LP {f['cota_lp_pct']:5.1f}% | costo total {f['costo_total_usd']:>12,.0f} | {estado}")


def barrer(esc, niveles, piso, con_cota=True):
    """Simula cada nivel. La cota LP (cara: crece al bajar el nivel) se calcula solo hasta NIVEL_MIN_COTA y solo si
    con_cota; a niveles menores ya alcanza 100% y no aporta."""
    filas = []
    for n in niveles:
        if n < piso:
            print(f"    {esc} {n:3d}%: bajo el piso fisico ({piso}%), no se simula.")
            continue
        fila, err = simular_nivel(esc, n, cota=con_cota and n >= NIVEL_MIN_COTA)
        if fila is None:
            print(f"    {esc} {n:3d}%: no se pudo simular ({err}).")
            continue
        filas.append(fila)
        print(linea_progreso(esc, n, fila))
    return pd.DataFrame(filas).rename(columns={"soc_pct": "nivel_pct"})


# --------------------------------------------------------------------------- #
# Regla
# --------------------------------------------------------------------------- #

def aplicar_regla(df):
    """Reglas 2-5 sobre las filas de UN escenario (una por nivel). Agrega factible_b, ciclica_sin_reservas,
    es_minimo, en_empate, elegido. Devuelve (df, nivel_minimo, nivel_elegido)."""
    df = df.sort_values("nivel_pct", ascending=False).reset_index(drop=True)
    df["factible"] = df["factible"].astype(bool)
    df["ciclica_sin_reservas"] = df["factible"] & (df["buses_reserva"] == 0)
    feas = df[df["factible"]]
    assert len(feas), "Ningun nivel dio una solucion factible: el caso base no es factible con estas jornadas."
    cmin = feas["costo_total_usd"].min()
    nivel_min = int(feas.loc[feas["costo_total_usd"].idxmin(), "nivel_pct"])
    df["es_minimo"] = df["nivel_pct"] == nivel_min
    df["en_empate"] = df["factible"] & (df["costo_total_usd"] <= cmin * (1 + TOL_EMPATE))
    elegido = int(df.loc[df["en_empate"], "nivel_pct"].max())
    df["elegido"] = df["nivel_pct"] == elegido
    return df, nivel_min, elegido


def mejor_sin_reservas(df):
    """Familia (a): el mejor nivel ciclico sin reservas (menor costo; empate: el mas alto), o None."""
    a = df[df["ciclica_sin_reservas"]]
    if a.empty:
        return None
    cmin = a["costo_total_usd"].min()
    return a[a["costo_total_usd"] <= cmin * (1 + TOL_EMPATE)].sort_values("nivel_pct", ascending=False).iloc[0]


# --------------------------------------------------------------------------- #
# Graficos
# --------------------------------------------------------------------------- #

def graficar_costo_total(df, esc, elegido, path_png):
    df = df.sort_values("nivel_pct", ascending=False).reset_index(drop=True)
    x = np.arange(len(df))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.6), gridspec_kw={"width_ratios": [1.35, 1]})
    fondo = np.zeros(len(df))
    for col, nombre, color in COMPONENTES:
        v = df[col].values / 1e6
        ax1.bar(x, v, bottom=fondo, width=0.64, color=color, label=nombre, edgecolor="white", linewidth=0.6)
        fondo += v
    for i, (_, f) in enumerate(df.iterrows()):
        marca = " (elegido)" if int(f["nivel_pct"]) == elegido else ""
        ax1.text(i, fondo[i] + 0.05, f"{f['costo_total_usd'] / 1e6:.2f} M{marca}", ha="center", fontsize=8.5,
                 fontweight="bold" if int(f["nivel_pct"]) == elegido else "normal")
        if not f["factible"]:
            ax1.text(i, fondo[i] / 2, "infact.", ha="center", va="center", color="white", fontsize=8, rotation=90)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{int(n)}%" for n in df["nivel_pct"]])
    ax1.set_xlabel("Nivel de partida, llegada y tope de carga")
    ax1.set_ylabel("Costo total (millones de USD / dia)")
    ax1.set_ylim(0, fondo.max() * 1.12)
    ax1.set_title(f"Costo total por nivel - {esc} (con buses de reserva)")
    ax1.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=6, fontsize=8)
    estilo(ax1)

    ax2.plot(df["nivel_pct"], df["costo_total_usd"] / 1e6, "o-", color="#b22222", linewidth=1.8, label="Con reservas (ciclo pagado)")
    ax2.plot(df["nivel_pct"], df["costo_sin_reservas_usd"] / 1e6, "o--", color="#7f7f7f", linewidth=1.5,
             label="Sin reservas (ciclo NO pagado)")
    ciclicos = df[df["ciclica_sin_reservas"]]
    if len(ciclicos):
        ax2.plot(ciclicos["nivel_pct"], ciclicos["costo_total_usd"] / 1e6, "s", markersize=10, markerfacecolor="none",
                 markeredgecolor="#2c6e8f", markeredgewidth=2, label="Ciclica sin reservas")
    el = df[df["nivel_pct"] == elegido].iloc[0]
    ax2.plot([elegido], [el["costo_total_usd"] / 1e6], "*", markersize=16, color="#b22222", zorder=5)
    ax2.set_xlabel("Nivel de bateria (%)")
    ax2.set_ylabel("Costo total (millones de USD / dia)")
    ax2.invert_xaxis()
    ax2.set_title("El costo del ciclo: reservas vs. bajar el nivel")
    ax2.legend(frameon=False, fontsize=8, loc="upper left")
    estilo(ax2)
    fig.suptitle(f"Barrido de niveles de bateria - escenario {esc} (politica reactiva); estrella = nivel elegido")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_ciclos_y_cota(df, esc, path_png):
    df = df.sort_values("nivel_pct", ascending=False)
    niveles = [f"{int(n)}%" for n in df["nivel_pct"]]
    fig, axs = plt.subplots(1, 4, figsize=(16, 4.2))
    series = [("buses_final", "Buses tras la carga", "#2c6e8f"), ("jornadas_partidas", "Jornadas partidas", "#d95f02"),
              ("buses_reserva", "Ciclos no cumplidos = buses de reserva", "#b22222"),
              ("cota_lp_pct", "Cota LP: % de la carga final que cabe", "#4a8f6e")]
    for ax, (col, titulo, color) in zip(axs, series):
        v = df[col].values
        ax.bar(niveles, v, color=color, width=0.6)
        for i, val in enumerate(v):
            if not np.isnan(val):
                ax.text(i, val, f"{val:,.0f}".replace(",", "."), ha="center", va="bottom", fontsize=7.5)
        ax.set_title(titulo, fontsize=9)
        ax.set_xlabel("Nivel")
        ax.tick_params(axis="x", labelsize=8)
        estilo(ax)
    axs[3].axhline(100, color="#b22222", linestyle="--", linewidth=1)
    axs[3].set_ylim(0, 112)
    fig.suptitle(f"Que cambia al bajar el nivel de bateria - {esc}")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_robustez(tabla, decisiones, path_png):
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    for esc in [ESCENARIO_PRINCIPAL] + ESCENARIOS_ROBUSTEZ:
        d = tabla[tabla["escenario"] == esc].sort_values("nivel_pct")
        ax.plot(d["nivel_pct"], d["costo_total_usd"] / 1e6, "o-", color=COLORES_ESC[esc], linewidth=1.8, markersize=5,
                label=f"{esc}" + (" (decide)" if esc == ESCENARIO_PRINCIPAL else " (robustez)"))
        el = decisiones[decisiones["escenario"] == esc].iloc[0]["nivel_elegido_pct"]
        fila = d[d["nivel_pct"] == el].iloc[0]
        ax.plot([el], [fila["costo_total_usd"] / 1e6], "*", markersize=15, color=COLORES_ESC[esc])
    ax.set_xlabel("Nivel de bateria (%)")
    ax.set_ylabel("Costo total con reservas (millones de USD / dia)")
    ax.set_title("Costo total por nivel en E1 y E0 (estrella = nivel elegido por la regla)")
    ax.invert_xaxis()
    ax.legend(frameon=False)
    estilo(ax)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    costos = parametros.cargar_costos()
    niveles = [round(n * 100) for n in parametros.SOC_BARRIDO_EXTENDIDO]
    print("=== BARRIDO DE NIVELES DE BATERIA (regla B6 corregida: la condicion ciclica es una restriccion) ===\n")

    tablas, decisiones, dfs = [], [], {}
    for rol, esc in [("decide", ESCENARIO_PRINCIPAL)] + [("robustez", e) for e in ESCENARIOS_ROBUSTEZ]:
        piso, piso_exacto = piso_fisico_pct(esc, costos)
        print(f"--- {esc} ({rol}); piso fisico {piso}% (la expedicion mas exigente necesita {piso_exacto:.1%} de la bateria) ---")
        df = barrer(esc, niveles, piso, con_cota=(rol == "decide"))
        df, nivel_min, elegido = aplicar_regla(df)
        df["escenario"] = esc
        dfs[esc] = df
        tablas.append(df)
        el = df[df["elegido"]].iloc[0]
        sr = mejor_sin_reservas(df)
        c100 = float(df[df["nivel_pct"] == 100].iloc[0]["costo_total_usd"])
        decisiones.append(dict(
            escenario=esc, rol=rol, niveles_evaluados=",".join(str(n) for n in df["nivel_pct"]), piso_fisico_pct=piso,
            nivel_minimo_costo_pct=nivel_min, nivel_elegido_pct=elegido, costo_elegido_usd=float(el["costo_total_usd"]),
            reservas_en_elegido=int(el["buses_reserva"]), buses_totales_elegido=int(el["buses_totales"]),
            ciclica_sin_reservas_nivel_pct=int(sr["nivel_pct"]) if sr is not None else np.nan,
            ciclica_sin_reservas_costo_usd=float(sr["costo_total_usd"]) if sr is not None else np.nan,
            costo_vs_100_pct=round((float(el["costo_total_usd"]) / c100 - 1) * 100, 2)))
    decisiones = pd.DataFrame(decisiones)
    principal = dfs[ESCENARIO_PRINCIPAL]
    elegido_p = int(decisiones.iloc[0]["nivel_elegido_pct"])
    decisiones["coincide_con_principal"] = decisiones["nivel_elegido_pct"] == elegido_p

    # --- evidencia: escenarios con terminales separados (no compiten) al 100% ---
    resumen = pd.read_csv(RESUMEN_CARGA, sep=CSV_SEP)
    separados = resumen[resumen["escenario"].isin(ESCENARIOS_INFACTIBLES) & (resumen["soc_pct"] == 100)].copy()
    separados = separados.rename(columns={"soc_pct": "nivel_pct"})

    tabla = pd.concat(tablas, ignore_index=True)
    cols = ["escenario", "nivel_pct", "buses_vsp", "buses_final", "jornadas_partidas", "por_sin_hueco", "por_sin_puesto",
            "eventos_intermedios", "ciclos_no_cumplidos", "retraso_ciclo_max_min", "kwh_deficit", "cota_lp_pct",
            "buses_reserva", "buses_totales", "espera_cola_h", "kwh_cargados", "costo_flota_usd", "costo_km_vacios_usd",
            "costo_espera_usd", "costo_energia_usd", "costo_eventos_usd", "costo_reservas_usd", "costo_sin_reservas_usd",
            "costo_total_usd", "factible", "ciclica_sin_reservas", "es_minimo", "en_empate", "elegido"]
    tabla = tabla[cols].round(3)
    tabla.to_csv(TABLAS / "barrido_niveles.csv", index=False, sep=CSV_SEP)
    decisiones.round(3).to_csv(TABLAS / "decision_barrido.csv", index=False, sep=CSV_SEP)
    separados[["escenario", "nivel_pct", "buses_final", "kwh_deficit", "ciclos_no_cumplidos", "cota_lp_pct", "factible",
               "costo_total_usd"]].round(3).to_csv(TABLAS / "evidencia_terminales_separados.csv", index=False, sep=CSV_SEP)
    print(f"\n  -> {TABLAS}/ (barrido_niveles, decision_barrido, evidencia_terminales_separados)")

    graficar_costo_total(principal, ESCENARIO_PRINCIPAL, elegido_p, GRAFICOS / "barrido_costo_total.png")
    graficar_ciclos_y_cota(principal, ESCENARIO_PRINCIPAL, GRAFICOS / "barrido_ciclos_y_cota.png")
    graficar_robustez(tabla, decisiones, GRAFICOS / "barrido_robustez.png")
    print(f"  -> {GRAFICOS}/ (3 graficos)")

    print(f"\n--- Corrida completa de {ESCENARIO_PRINCIPAL} al nivel elegido ({elegido_p}%) ---")
    fila, err = simular_nivel(ESCENARIO_PRINCIPAL, elegido_p, completo=True, cota=elegido_p >= NIVEL_MIN_COTA)
    assert fila is not None, f"No se pudo correr completo el nivel elegido: {err}"

    escribir_reporte(principal, decisiones, separados, elegido_p)
    print(f"  -> {SALIDA / 'reporte_barrido.md'}")

    print("\n=== Decision ===")
    print(decisiones[["escenario", "rol", "piso_fisico_pct", "nivel_minimo_costo_pct", "nivel_elegido_pct",
                      "costo_elegido_usd", "reservas_en_elegido", "ciclica_sin_reservas_nivel_pct",
                      "ciclica_sin_reservas_costo_usd", "coincide_con_principal"]].to_string(index=False))
    # --- chequeos ---
    assert principal["elegido"].sum() == 1 and principal.loc[principal["elegido"], "factible"].all(), \
        "La regla no dejo exactamente un nivel elegido y factible."
    print("\n=== FIN BARRIDO ===")


def escribir_reporte(df_p, decisiones, separados, elegido):
    esc = ESCENARIO_PRINCIPAL
    d = df_p.sort_values("nivel_pct", ascending=False)
    base = d.iloc[0]
    el = d[d["nivel_pct"] == elegido].iloc[0]
    sr = mejor_sin_reservas(d)
    resumen = d[["nivel_pct", "buses_final", "jornadas_partidas", "buses_reserva", "kwh_deficit", "cota_lp_pct",
                 "costo_sin_reservas_usd", "costo_reservas_usd", "costo_total_usd", "factible", "ciclica_sin_reservas",
                 "elegido"]].copy()
    resumen["kwh_deficit"] = (resumen["kwh_deficit"] / 1000).round(1)
    resumen = resumen.rename(columns={"kwh_deficit": "deficit_mwh"}).round(1)
    d_tabla = d.copy()
    d_tabla["delta_costo_vs_100_pct"] = ((d_tabla["costo_total_usd"] / base["costo_total_usd"] - 1) * 100).round(2)
    dd = decisiones.copy()
    lineas = [
        f"# Reporte - barrido de niveles de bateria (escenario {esc})",
        "",
        "La condicion ciclica (inicio = fin) es una **restriccion**: el nivel se elige entre las soluciones que la cumplen. "
        "Un bus que no termina de cargar antes de su salida del dia siguiente (ciclo no cumplido) se reemplaza por un bus de "
        "reserva ya cargado (250 USD/dia); el costo total incluye las reservas. Regla completa en `docs/context/"
        "02_supuestos_y_decisiones.md` (B6) y `docs/justificaciones/04_nivel_carga_ciclico.md`.",
        "",
        f"## Resultado: el nivel base es **{elegido}%**",
        "",
        f"- Niveles evaluados en {esc}: {', '.join(str(int(n)) + '%' for n in d['nivel_pct'])}. Piso fisico: "
        f"{int(decisiones.iloc[0]['piso_fisico_pct'])}%.",
        f"- Costo total al {elegido}% (con {int(el['buses_reserva']):,} buses de reserva): **{el['costo_total_usd']:,.0f} USD/dia** "
        f"({int(el['buses_totales']):,} buses en total); frente al 100%: "
        f"{(el['costo_total_usd'] / base['costo_total_usd'] - 1) * 100:+.2f}%.",
        ("- **Familia (a), ciclica sin reservas:** " + (
            f"el mejor nivel es {int(sr['nivel_pct'])}% con {sr['costo_total_usd']:,.0f} USD/dia "
            f"({(sr['costo_total_usd'] / el['costo_total_usd'] - 1) * 100:+.1f}% frente a la elegida)."
            if sr is not None else "ningun nivel evaluado cierra el ciclo sin reservas.")),
        f"- **Familia (b), con reservas:** el mejor es {int(decisiones.iloc[0]['nivel_minimo_costo_pct'])}% "
        f"({d[d['nivel_pct'] == decisiones.iloc[0]['nivel_minimo_costo_pct']].iloc[0]['costo_total_usd']:,.0f} USD/dia).",
        "",
        "## Tabla del escenario que decide",
        "",
        resumen.to_markdown(index=False),
        "",
        "Cota LP: porcentaje de la energia de las cargas finales que cabe dentro de las ventanas de los buses con una carga "
        "perfecta (si es menor a 100%, ningun programa de carga cierra el ciclo con esas jornadas).",
        "",
        "Diferencia del costo total respecto del nivel mas alto:",
        "",
        d_tabla[["nivel_pct", "delta_costo_vs_100_pct"]].to_markdown(index=False),
        "",
        "## Robustez y decision por escenario",
        "",
        dd.to_markdown(index=False),
        "",
        ("La eleccion es **robusta**: E0 elige el mismo nivel que E1." if decisiones["coincide_con_principal"].all()
         else "La eleccion **no es del todo robusta**: E0 elige un nivel distinto (ver tabla); se reporta tal cual."),
        "",
        "## Evidencia: terminales separados (no compiten; infactibles)",
        "",
        separados[["escenario", "nivel_pct", "buses_final", "kwh_deficit", "cota_lp_pct", "factible",
                   "costo_total_usd"]].round(1).to_markdown(index=False),
        "",
        "Sin unir Los Espinos y Santa Rosa, Los Espinos no tiene puestos para reponer toda su energia (deficit); las reservas no "
        "lo arreglan. Por eso la union es parte de la configuracion base.",
        "",
        "## Limitaciones",
        "- Politica reactiva y miope; con una carga programada (Etapa 4) la capacidad nocturna se usaria mejor, pero la cota LP "
        "muestra que no alcanza para cerrar el ciclo con las jornadas actuales.",
        "- Los buses de reserva son una cota superior simple (no comparten reservas entre atrasos cortos).",
        "- Carga lineal a 180 kW, sin curva CC-CV; un solo dia laboral; el ciclo supone que el dia siguiente es igual.",
        "",
        "## Archivos",
        "- `tablas/barrido_niveles.csv`: una fila por escenario y nivel (factibilidad, reservas, cota LP, minimo, empate, elegido).",
        "- `tablas/decision_barrido.csv`: la decision por escenario, las dos familias y si coincide con el principal.",
        "- `tablas/evidencia_terminales_separados.csv`: E0_sep y E1_sep al 100% (infactibles).",
        "- `graficos/barrido_costo_total.png`: costo total apilado por nivel (con reservas) y el costo del ciclo.",
        "- `graficos/barrido_ciclos_y_cota.png`: buses, jornadas partidas, reservas y cota LP por nivel.",
        "- `graficos/barrido_robustez.png`: costo total por nivel en E1 y E0.",
        f"- Corrida completa del nivel elegido: `../tablas/*_{esc}_soc{elegido}.csv`, `../graficos/*_{esc}_soc{elegido}.png`, "
        f"`../reporte_{esc}_soc{elegido}.md`.",
    ]
    (SALIDA / "reporte_barrido.md").write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    main()
