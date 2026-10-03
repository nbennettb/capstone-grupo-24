"""
Etapa 1 (C2) del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md seccion 4).

Asignacion de rutas a electroterminales con restriccion de CAPACIDAD:
igual que C1b (scripts/4-clustering_c1.py) -- misma metrica de distancia,
a paraderos terminales reales -- pero resuelta como un MILP de asignacion
generalizada, sujeto a que la carga diaria estimada de cada electroterminal
no supere su capacidad. Asi, C1b -> C2 aisla el efecto de agregar la
capacidad (el unico cambio respecto de C1b).

SUPUESTO DE CARGA: CONDICION CICLICA (docs/context/02_supuestos_y_decisiones.md,
B6). Cada bus empieza y termina el dia con el mismo nivel de bateria, asi que
se recarga TODO lo consumido:
    h_r = kwh_dia_r / charge_power_kw            (horas-cargador/dia de la ruta r)
Por eso h_r NO depende del nivel de bateria (el que elige el barrido de niveles
de la Etapa 3): ese nivel cambia cuantas jornadas recargan a mitad del dia, no
la energia total. C2 no usa el nivel y su asignacion es la misma para todos.

EVIDENCIA "SIN RECUPERACION" vs "CON RECUPERACION": sin recuperacion, los buses
parten con el nivel L y no lo recuperan al terminar (solo se paga el excedente
sobre la bateria util de ese nivel); con recuperacion (ciclo) se paga todo lo
consumido. Se compara al MISMO nivel L, para cada nivel de
parametros.SOC_CICLICO_BARRIDO, en capacidad_sin_vs_con_recuperacion.csv; NO
genera ninguna asignacion. Es un proxy POR RUTA (sin deadhead): la medicion por
jornada llega con la Etapa 2.

DEFINICION DE UNIDADES: h_r y la capacidad del electroterminal estan ambas
en horas-cargador/dia.
  capacidad_electroterminal = puestos * 24 h * theta     (24 h: el profesor
  confirmo que se puede cargar todo el dia)

Formulacion:
    min  sum_{r,d} c_rd * x_rd
    s.a. sum_d x_rd = 1                                      para toda ruta r
         sum_r h_r * x_rd <= puestos_d * 24 * theta          para todo electroterminal d
         x_rd in {0,1}
donde c_rd = 2 * distancia_terminales_reales(r,d) * costo_por_km * n_buses_r
(mismo costo aproximado de pullout+pullin que usa C1b).

Variante con Los Espinos + Santa Rosa unidos (parametros.ELECTROTERMINALES_UNIDOS):
la restriccion de ambos se reemplaza por una sola con los puestos sumados
(270). Las distancias siguen siendo a cada patio fisico. Solo se usa en el
barrido de theta, como evidencia secundaria; el efecto real de unir esta en
el interlining de la Etapa 2.

Input:  data-processed/rutas_resumen.csv, terminales_por_ruta.csv,
        terminales.csv, rutas_cluster_c1b.csv (opcional, para validar),
        data-filtrado/{depots,parameters}.csv
Output: data-processed/rutas_cluster_c2.csv
        results/etapa1_clustering/tablas/capacidad_por_terminal.csv
        results/etapa1_clustering/tablas/capacidad_sin_vs_con_recuperacion.csv
        results/etapa1_clustering/tablas/barrido_theta.csv
        results/etapa1_clustering/graficos/capacidad_ciclo.png
        results/etapa1_clustering/graficos/capacidad_sin_vs_con_recuperacion.png
        results/etapa1_clustering/graficos/barrido_theta.png

Uso:
    python scripts/5-clustering_c2.py
        Red completa: asignacion con theta=1, tablas de evidencia y barrido.

    python scripts/5-clustering_c2.py --rutas 203N 203c ... --theta 0.05
        Checkpoint de reactividad: capacidad MUY apretada a proposito, para
        confirmar que el modelo mueve rutas antes de correr la red completa.
"""

import argparse
import sys
from pathlib import Path

import gurobipy as gp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gurobipy import GRB

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parametros                                                # noqa: E402
from common.clustering import distancia_ponderada_a_terminales_reales        # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa1_clustering")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)

RUTAS_ESPERADAS = 417
HORAS_DISPONIBLES = 24.0          # [Profesor] no hay restriccion de horario de carga
H_R_TOTAL_REFERENCIA = 10464.0    # horas-cargador/dia bajo ciclo (referencia del plan)
THETA_BARRIDO = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
NOMBRE_UNIDO = "Los Espinos + Santa Rosa"

COLOR_CARGA = "#2c6e8f"
COLOR_LIMITE = "#b22222"
COLOR_CICLO = "#2c6e8f"
COLOR_SIN_RECUPERACION = "#8f8f8f"
SIN_RECUP = "Sin recuperacion"
CON_RECUP = "Con recuperacion (ciclo)"
COLOR_SEPARADA = "#2c6e8f"
COLOR_COMBINADA = "#d95f02"


def estilo(ax):
    """Grilla y ejes recesivos: lo que importa son los datos."""
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.7)
    ax.set_axisbelow(True)


def cargar_datos(subset_rutas=None):
    rutas_resumen = pd.read_csv(DATA_PROCESSED / "rutas_resumen.csv", sep=CSV_SEP)
    terminales_por_ruta = pd.read_csv(DATA_PROCESSED / "terminales_por_ruta.csv", sep=CSV_SEP)
    terminales = pd.read_csv(DATA_PROCESSED / "terminales.csv", sep=CSV_SEP)
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    depots["depot_id"] = depots["depot_id"].astype(str)

    rutas_resumen["route_id"] = rutas_resumen["route_id"].astype(str)
    terminales_por_ruta["route_id"] = terminales_por_ruta["route_id"].astype(str)

    if subset_rutas:
        subset_rutas = {str(r) for r in subset_rutas}
        rutas_resumen = rutas_resumen[rutas_resumen["route_id"].isin(subset_rutas)].reset_index(drop=True)
        terminales_por_ruta = terminales_por_ruta[terminales_por_ruta["route_id"].isin(subset_rutas)]
        if rutas_resumen.empty:
            raise SystemExit(f"--rutas {subset_rutas} no matchea ninguna ruta en rutas_resumen.csv")
    return rutas_resumen, terminales_por_ruta, terminales, depots


def calcular_h_r(rutas_resumen, costos):
    """Horas-cargador/dia que demanda cada ruta bajo el ciclo diario: se recarga
    todo lo consumido. Array alineado con rutas_resumen."""
    return rutas_resumen["kwh_dia"].values / costos.charge_power_kw


def h_r_sin_recuperacion(rutas_resumen, costos, soc):
    """SOLO EVIDENCIA: los buses parten con nivel `soc` y no lo recuperan al terminar, asi que
    solo se recarga el excedente sobre la bateria util de ese nivel de cada bus estimado.
    Proxy por ruta, sin deadhead; subestima el excedente real (que se mide por jornada en la
    Etapa 2). No se usa para asignar nada."""
    exceso = np.maximum(0.0, rutas_resumen["kwh_dia"].values
                        - rutas_resumen["n_buses_estimados"].values * costos.bateria_util_ciclica_kwh(soc))
    return exceso / costos.charge_power_kw


def resolver_asignacion(h_r, c_rd, capacidad_puestos, horas_disponibles, theta, grupos_capacidad=None):
    """MILP de asignacion generalizada con restriccion de capacidad.
    grupos_capacidad: lista de listas de indices de electroterminal que comparten una
    sola bolsa de puestos (None = una restriccion por electroterminal).
    Devuelve (idx_asignado, capacidad_por_depot). Lanza RuntimeError con el detalle de las
    restricciones en conflicto (via computeIIS) si queda infactible."""
    capacidad = capacidad_puestos * horas_disponibles * theta
    n_depots = len(capacidad_puestos)
    grupos = grupos_capacidad or [[d] for d in range(n_depots)]
    assert sorted(d for g in grupos for d in g) == list(range(n_depots)), \
        "Los grupos de capacidad deben cubrir cada electroterminal exactamente una vez."

    m = gp.Model()
    m.Params.OutputFlag = 0
    x = m.addMVar(c_rd.shape, vtype=GRB.BINARY, obj=c_rd)
    m.addConstr(x.sum(axis=1) == 1, name="una_ruta_un_terminal")
    for g in grupos:
        carga_g = sum((h_r * x[:, d]).sum() for d in g)
        m.addConstr(carga_g <= float(capacidad[g].sum()), name=f"capacidad_terminal_{g}")
    m.optimize()

    if m.Status != GRB.OPTIMAL:
        m.computeIIS()
        restricciones_conflicto = [c.ConstrName for c in m.getConstrs() if c.IISConstr]
        raise RuntimeError(
            f"MILP infactible (status={m.Status}) con theta={theta}. "
            f"Restricciones en conflicto: {restricciones_conflicto[:10]}.")

    return x.X.argmax(axis=1), capacidad


def tabla_uso_capacidad(asignacion, h_r, capacidad, depots):
    carga = (pd.Series(h_r, index=asignacion["depot_nombre"].values).groupby(level=0).sum()
             .rename("h_r_asignadas"))
    cap = pd.Series(capacidad, index=depots["nombre"].values, name="capacidad")
    tabla = carga.to_frame().join(cap, how="right").fillna(0.0)
    tabla["uso_pct"] = (tabla["h_r_asignadas"] / tabla["capacidad"] * 100).round(1)
    return tabla


def agregar_fila_unida(tabla):
    """Fila informativa del terminal combinado (Los Espinos + Santa Rosa)."""
    ids = ["Los Espinos", "Santa Rosa"]
    h, c = tabla.loc[ids, "h_r_asignadas"].sum(), tabla.loc[ids, "capacidad"].sum()
    fila = pd.DataFrame({"h_r_asignadas": [h], "capacidad": [c], "uso_pct": [round(h / c * 100, 1)]},
                        index=[NOMBRE_UNIDO])
    return pd.concat([tabla, fila])


def tabla_evidencia_recuperacion(asignacion, h_ciclo, rutas_resumen, capacidad, depots, costos):
    """Por nivel de bateria, electroterminal y total: horas-cargador, MWh a recargar y uso de la
    capacidad, SIN recuperacion vs CON recuperacion (ciclo) al mismo nivel. Todo con la misma
    asignacion (C2) para comparar lo mismo. Con recuperacion no depende del nivel."""
    filas = []
    for soc in parametros.SOC_CICLICO_BARRIDO:
        for supuesto, h in ((SIN_RECUP, h_r_sin_recuperacion(rutas_resumen, costos, soc)),
                            (CON_RECUP, h_ciclo)):
            t = tabla_uso_capacidad(asignacion, h, capacidad, depots)
            for nombre, f in t.iterrows():
                filas.append({"nivel_soc_pct": round(soc * 100), "supuesto": supuesto,
                              "electroterminal": nombre, "h_cargador_dia": f["h_r_asignadas"],
                              "mwh_a_recargar": f["h_r_asignadas"] * costos.charge_power_kw / 1000,
                              "capacidad_h_cargador": f["capacidad"], "uso_pct": f["uso_pct"]})
            h_tot, c_tot = t["h_r_asignadas"].sum(), t["capacidad"].sum()
            filas.append({"nivel_soc_pct": round(soc * 100), "supuesto": supuesto,
                          "electroterminal": "TOTAL", "h_cargador_dia": h_tot,
                          "mwh_a_recargar": h_tot * costos.charge_power_kw / 1000,
                          "capacidad_h_cargador": c_tot, "uso_pct": round(h_tot / c_tot * 100, 2)})
    out = pd.DataFrame(filas)
    out["nivel_calculo"] = "proxy por ruta (sin deadhead)"
    return out.round(2)


def graficar_capacidad(tabla, path_png):
    t = tabla.drop(index=NOMBRE_UNIDO, errors="ignore")
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(t))
    ax.bar(x, t["h_r_asignadas"], width=0.55, color=COLOR_CARGA, label="Carga asignada (C2)")
    ax.bar(x, t["capacidad"], width=0.55, color="none", edgecolor=COLOR_LIMITE, linewidth=1.4,
           label="Capacidad (puestos x 24 h)")
    for xi, (_, f) in zip(x, t.iterrows()):
        ax.text(xi, f["capacidad"] + 60, f"{f['uso_pct']:.1f}%", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(t.index, rotation=15, ha="right")
    ax.set_ylabel("Horas-cargador / dia")
    ax.set_title("C2 bajo ciclo diario: carga asignada vs. capacidad (theta = 1)")
    ax.legend(frameon=False)
    estilo(ax)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_sin_vs_con_recuperacion(evidencia, path_png):
    """Izquierda: uso por electroterminal al nivel mas alto del barrido (sin vs con recuperacion).
    Derecha: uso global segun el nivel de bateria."""
    nivel0 = int(evidencia["nivel_soc_pct"].max())
    e = evidencia[(evidencia["electroterminal"] != "TOTAL") & (evidencia["nivel_soc_pct"] == nivel0)]
    nombres = list(e["electroterminal"].unique())
    x = np.arange(len(nombres))
    tot = evidencia[evidencia["electroterminal"] == "TOTAL"]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    for i, (sup, color) in enumerate(((SIN_RECUP, COLOR_SIN_RECUPERACION), (CON_RECUP, COLOR_CICLO))):
        v = e[e["supuesto"] == sup].set_index("electroterminal").loc[nombres, "uso_pct"]
        ax.bar(x + (i - 0.5) * 0.36, v.values, width=0.34, color=color, label=sup)
        for xi, val in zip(x + (i - 0.5) * 0.36, v.values):
            ax.text(xi, val + 1.5, f"{val:.1f}%", ha="center", fontsize=8)
    ax.axhline(100, color=COLOR_LIMITE, linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=15, ha="right")
    ax.set_ylabel("Uso de la capacidad de carga (%)")
    ax.set_ylim(0, 125)
    ax.set_title(f"Por electroterminal, nivel {nivel0}%")
    ax.legend(frameon=False, loc="upper left")
    estilo(ax)

    for sup, color in ((SIN_RECUP, COLOR_SIN_RECUPERACION), (CON_RECUP, COLOR_CICLO)):
        t = tot[tot["supuesto"] == sup].sort_values("nivel_soc_pct")
        ax2.plot(t["nivel_soc_pct"], t["uso_pct"], "o-", color=color, linewidth=1.8, markersize=5, label=sup)
    ax2.set_xlabel("Nivel de bateria de partida (%)")
    ax2.set_ylabel("Uso global de la capacidad (%)")
    ax2.set_ylim(0, 100)
    ax2.set_title("Uso global segun el nivel")
    ax2.legend(frameon=False, loc="center right")
    estilo(ax2)

    fig.suptitle("Sin recuperacion vs con recuperacion, al mismo nivel (proxy por ruta, sin deadhead)")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_barrido_theta(barrido, path_png):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    for modo, color, etq in (("separada", COLOR_SEPARADA, "Capacidad separada"),
                              ("combinada", COLOR_COMBINADA, f"Combinada ({NOMBRE_UNIDO})")):
        f = barrido[(barrido["capacidad"] == modo) & barrido["factible"]]
        ax1.plot(f["theta"], f["rutas_movidas"], "o-", color=color, label=etq, linewidth=1.8, markersize=5)
        ax2.plot(f["theta"], f["uso_max_pct"], "o-", color=color, label=etq, linewidth=1.8, markersize=5)
    ax1.set_ylabel("Rutas movidas respecto de la asignacion con theta = 1")
    ax2.set_ylabel("Uso maximo de un electroterminal (%)")
    ax2.axhline(100, color="black", linestyle="--", linewidth=1)
    for ax in (ax1, ax2):
        ax.set_xlabel("theta (holgura de capacidad; menor = mas apretada)")
        ax.invert_xaxis()
        estilo(ax)
    ax1.legend(frameon=False)
    fig.suptitle("Barrido de theta bajo ciclo diario (H = 24 h)")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rutas", nargs="*", default=None,
                         help="Checkpoint chico: lista de route_id a incluir.")
    parser.add_argument("--theta", type=float, default=0.05,
                         help="Solo para el checkpoint chico: holgura de capacidad (chica a proposito).")
    args = parser.parse_args()
    corrida_parcial = bool(args.rutas)

    print("=== ETAPA 1 (C2): asignacion con restriccion de capacidad (ciclo diario) ===\n")
    rutas_resumen, terminales_por_ruta, terminales, depots = cargar_datos(args.rutas)
    costos = parametros.cargar_costos()
    print(f"--- Rutas: {len(rutas_resumen)} | Electroterminales: {len(depots)} | "
          f"potencia cargador: {costos.charge_power_kw:.0f} kW | H = {HORAS_DISPONIBLES:.0f} h ---")

    dist_km = distancia_ponderada_a_terminales_reales(terminales_por_ruta, terminales, depots,
                                                        parametros.FACTOR_DESVIO)
    dist_km = dist_km.loc[rutas_resumen["route_id"].values]
    n_buses_r = rutas_resumen["n_buses_estimados"].values
    c_rd = 2 * dist_km.values * costos.cost_per_km * n_buses_r[:, None]
    capacidad_puestos = depots["capacity"].astype(float).values
    h_r = calcular_h_r(rutas_resumen, costos)

    # grupo de capacidad compartida (Los Espinos + Santa Rosa)
    ids = list(depots["depot_id"])
    idx_unidos = [ids.index(d) for d in parametros.ELECTROTERMINALES_UNIDOS]
    grupos_unidos = [idx_unidos] + [[d] for d in range(len(ids)) if d not in idx_unidos]

    def armar(idx):
        return pd.DataFrame({
            "route_id": rutas_resumen["route_id"].values,
            "depot_id": depots["depot_id"].values[idx],
            "depot_nombre": depots["nombre"].values[idx],
            "distancia_km": dist_km.values[np.arange(len(rutas_resumen)), idx],
            "n_buses_estimados": n_buses_r,
            "h_r_horas_cargador": h_r,
        }).reset_index(drop=True)

    # ------------------------------------------------------------------ #
    # Checkpoint chico: capacidad apretada a proposito
    # ------------------------------------------------------------------ #
    if corrida_parcial:
        print(f"\n[CHECKPOINT CHICO] theta={args.theta}")
        idx, capacidad = resolver_asignacion(h_r, c_rd, capacidad_puestos, HORAS_DISPONIBLES, args.theta)
        asignacion = armar(idx)
        tabla = tabla_uso_capacidad(asignacion, h_r, capacidad, depots)
        print("\n--- Uso de capacidad por electroterminal ---")
        print(tabla.round(1).to_string())

        movidas = int((c_rd.argmin(axis=1) != idx).sum())
        print(f"\n--- Rutas movidas respecto del minimo sin capacidad: {movidas} de {len(asignacion)} ---")
        assert (tabla["h_r_asignadas"] <= tabla["capacidad"] + 1e-6).all(), \
            "Algun electroterminal quedo con mas carga asignada que su capacidad."
        if args.theta < 0.2:
            assert movidas > 0, ("Con theta tan chico se esperaba que el modelo reasignara al menos "
                                  "una ruta -- revisar si la restriccion de capacidad esta activa.")
        print("\n  [OK] Checkpoint de reactividad: capacidad respetada"
              + (" y el modelo reasigno rutas." if movidas else "."))
        print("\n=== FIN ETAPA 1 (C2) -- checkpoint chico ===")
        return

    # ------------------------------------------------------------------ #
    # Red completa: asignacion vigente (ciclo, theta = 1, capacidad separada)
    # ------------------------------------------------------------------ #
    print("\n--- C2: ciclo diario, theta = 1.0 ---")
    idx_c2, capacidad = resolver_asignacion(h_r, c_rd, capacidad_puestos, HORAS_DISPONIBLES, 1.0)
    asig_c2 = armar(idx_c2)
    tabla_c2 = tabla_uso_capacidad(asig_c2, h_r, capacidad, depots)
    print(tabla_c2.round(1).to_string())
    print(f"\n  h_r total = {h_r.sum():,.0f} horas-cargador/dia "
          f"({h_r.sum() * costos.charge_power_kw / 1000:,.0f} MWh) | capacidad total = {capacidad.sum():,.0f}")

    # Chequeo central: con theta = 1 la restriccion agregada diaria no deberia estar activa,
    # asi que C2 debe coincidir EXACTAMENTE con el minimo sin capacidad (= C1b).
    distintas_de_libre = int((c_rd.argmin(axis=1) != idx_c2).sum())
    c1b_path = DATA_PROCESSED / "rutas_cluster_c1b.csv"
    if c1b_path.exists():
        c1b = pd.read_csv(c1b_path, sep=CSV_SEP)
        c1b["route_id"] = c1b["route_id"].astype(str)
        c1b["depot_id"] = c1b["depot_id"].astype(str)
        ref_c1b = c1b.set_index("route_id")["depot_id"].loc[asig_c2["route_id"].values].values
        dif_c1b = int((asig_c2["depot_id"].values != ref_c1b).sum())
        print(f"  Rutas de C2 distintas de C1b: {dif_c1b} | distintas del minimo sin capacidad: {distintas_de_libre}")
        assert dif_c1b == 0, ("Bajo ciclo y theta = 1 se esperaba C2 = C1b; si difiere, la restriccion se "
                              "activo y hay que explicarlo antes de seguir.")
    else:
        print(f"  [aviso] no existe {c1b_path.name}; se valida contra el minimo sin capacidad.")
        assert distintas_de_libre == 0, ("Bajo ciclo y theta = 1 se esperaba C2 = minimo sin capacidad; "
                                         "si difiere, la restriccion se activo y hay que explicarlo.")
    print("  [OK] C2 coincide exactamente con C1b: la restriccion AGREGADA diaria no esta activa con theta = 1.")

    diferencia_h = abs(h_r.sum() - H_R_TOTAL_REFERENCIA) / H_R_TOTAL_REFERENCIA
    if diferencia_h > 0.01:
        print(f"  [aviso] h_r total {h_r.sum():,.0f} difiere {diferencia_h:.1%} de la referencia "
              f"({H_R_TOTAL_REFERENCIA:,.0f}); explicar antes de seguir.")

    print("\n--- Guardando asignacion y tablas ---")
    out_c2 = DATA_PROCESSED / "rutas_cluster_c2.csv"
    asig_c2.to_csv(out_c2, index=False, sep=CSV_SEP)
    print(f"  -> {out_c2} ({len(asig_c2)} rutas)")

    tabla_c2_ext = agregar_fila_unida(tabla_c2)
    tabla_c2_ext.rename_axis("electroterminal").reset_index().round(2).to_csv(
        TABLAS / "capacidad_por_terminal.csv", index=False, sep=CSV_SEP)
    print(f"  -> {TABLAS / 'capacidad_por_terminal.csv'}")
    graficar_capacidad(tabla_c2_ext, GRAFICOS / "capacidad_ciclo.png")
    print(f"  -> {GRAFICOS / 'capacidad_ciclo.png'}")

    # ------------------------------------------------------------------ #
    # Evidencia sin recuperacion vs con recuperacion, al mismo nivel (no genera asignaciones)
    # ------------------------------------------------------------------ #
    evidencia = tabla_evidencia_recuperacion(asig_c2, h_r, rutas_resumen, capacidad, depots, costos)
    evidencia.to_csv(TABLAS / "capacidad_sin_vs_con_recuperacion.csv", index=False, sep=CSV_SEP)
    print(f"  -> {TABLAS / 'capacidad_sin_vs_con_recuperacion.csv'}")
    graficar_sin_vs_con_recuperacion(evidencia, GRAFICOS / "capacidad_sin_vs_con_recuperacion.png")
    print(f"  -> {GRAFICOS / 'capacidad_sin_vs_con_recuperacion.png'}")
    tot = evidencia[evidencia["electroterminal"] == "TOTAL"]
    print("  Evidencia (proxy por ruta, sin deadhead) -- h-cargador/dia y uso global por nivel:")
    for soc in parametros.SOC_CICLICO_BARRIDO:
        pct = round(soc * 100)
        s = tot[(tot["nivel_soc_pct"] == pct) & (tot["supuesto"] == SIN_RECUP)].iloc[0]
        c = tot[(tot["nivel_soc_pct"] == pct) & (tot["supuesto"] == CON_RECUP)].iloc[0]
        print(f"    nivel {pct:3d}%: sin recuperacion {s['h_cargador_dia']:7,.0f} h ({s['uso_pct']:5.2f}%) | "
              f"con recuperacion {c['h_cargador_dia']:7,.0f} h ({c['uso_pct']:5.2f}%)")

    # ------------------------------------------------------------------ #
    # Barrido de theta: capacidad separada y combinada
    # ------------------------------------------------------------------ #
    print("\n--- Barrido de theta (ciclo, H = 24 h) ---")
    ref = asig_c2.set_index("route_id")["depot_id"]
    filas = []
    for modo, grupos in (("separada", None), ("combinada", grupos_unidos)):
        for theta in THETA_BARRIDO:
            try:
                idx, cap = resolver_asignacion(h_r, c_rd, capacidad_puestos, HORAS_DISPONIBLES, theta, grupos)
            except RuntimeError:
                filas.append({"capacidad": modo, "theta": theta, "factible": False, "rutas_movidas": None,
                              "costo_asignacion_usd_dia": None, "uso_max_pct": None, "depot_mas_cargado": None})
                print(f"  {modo:9s} theta={theta:.2f} -> INFACTIBLE")
                break  # apretar mas solo empeora: si este theta es infactible, los menores tambien
            asig = armar(idx)
            tabla = agregar_fila_unida(tabla_uso_capacidad(asig, h_r, cap, depots))
            # en la variante combinada el terminal unido cuenta como uno, no como sus dos patios
            tabla_uso = (tabla.drop(index=["Los Espinos", "Santa Rosa"]) if modo == "combinada"
                         else tabla.drop(index=NOMBRE_UNIDO))
            movidas = int((asig["depot_id"].values != ref.loc[asig["route_id"].values].values).sum())
            costo = float(c_rd[np.arange(len(rutas_resumen)), idx].sum())
            filas.append({"capacidad": modo, "theta": theta, "factible": True, "rutas_movidas": movidas,
                          "costo_asignacion_usd_dia": round(costo, 0), "uso_max_pct": tabla_uso["uso_pct"].max(),
                          "depot_mas_cargado": tabla_uso["uso_pct"].idxmax()})
            print(f"  {modo:9s} theta={theta:.2f} -> {movidas:3d} rutas movidas, "
                  f"uso maximo {tabla_uso['uso_pct'].max():.1f}% ({tabla_uso['uso_pct'].idxmax()})")
    barrido = pd.DataFrame(filas)
    barrido.to_csv(TABLAS / "barrido_theta.csv", index=False, sep=CSV_SEP)
    print(f"  -> {TABLAS / 'barrido_theta.csv'}")
    graficar_barrido_theta(barrido, GRAFICOS / "barrido_theta.png")
    print(f"  -> {GRAFICOS / 'barrido_theta.png'}")

    # --- Chequeos de sanidad finales ---
    assert asig_c2["route_id"].is_unique, "C2: alguna ruta quedo asignada mas de una vez."
    assert (tabla_c2["h_r_asignadas"] <= tabla_c2["capacidad"] + 1e-6).all(), \
        "C2: algun electroterminal quedo con mas carga que su capacidad."
    print("\n  [OK] Chequeos de sanidad pasaron (asignacion unica, ninguna capacidad excedida).")
    if len(asig_c2) != RUTAS_ESPERADAS:
        print(f"  [aviso] {len(asig_c2)} rutas asignadas, se esperaban {RUTAS_ESPERADAS}.")

    print("\n=== FIN ETAPA 1 (C2) ===")


if __name__ == "__main__":
    main()
