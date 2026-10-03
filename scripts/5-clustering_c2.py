"""
Etapa 1 (C2) del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia.md seccion 4 y
docs/Propuesta_metodologia_reunion.md seccion 5).

Asignacion de rutas a electroterminales con restriccion de CAPACIDAD:
igual que C1b (scripts/4-clustering_c1.py) -- misma metrica de distancia,
a paraderos terminales reales -- pero resuelta como un MILP de asignacion
generalizada, sujeto a que la carga horaria estimada de cada electroterminal
no supere su capacidad. Asi, C1b -> C2 aisla el efecto de agregar la
capacidad (el unico cambio respecto de C1b).

DOS SUPUESTOS DE CUANTA ENERGIA HAY QUE RECARGAR POR DIA (ver
docs/context/02_supuestos_y_decisiones.md seccion B6, la mas critica del
proyecto):
  - 'soc100' (CASO BASE aprobado el 28/09): los buses parten el dia con
    bateria llena. Solo se recarga el EXCEDENTE sobre la bateria util
    (315 kWh) que le sobra a la energia diaria de la ruta repartida entre
    sus buses estimados: h_r = max(0, kwh_dia_r - n_buses_r*bateria_util) / charge_power_kw.
    LIMITACION A DECLARAR: sumar el excedente A NIVEL DE RUTA subestima el
    excedente real (que se calcula bus por bus, jornada por jornada, y
    requeriria la Etapa 2). Se usa como proxy simple mientras esa etapa no
    este lista.
  - 'ciclo' (escenario de sensibilidad): se recarga TODO lo consumido, como
    si cada bus tuviera que terminar el dia con la bateria llena para el
    dia siguiente: h_r = kwh_dia_r / charge_power_kw.

DEFINICION DE UNIDADES (evita el error del Informe 1: mezclar capacidad de
carga simultanea con volumen de expediciones/dia, ver
docs/context/02_supuestos_y_decisiones.md seccion B5): h_r y la capacidad del
electroterminal estan ambas en horas-cargador/dia.
  capacidad_electroterminal = capacidad_puestos * horas_disponibles * theta

Formulacion (ver Propuesta_metodologia_reunion.md seccion 5, C2):
    min  sum_{r,d} c_rd * x_rd
    s.a. sum_d x_rd = 1                                          para toda ruta r
         sum_r h_r * x_rd <= capacidad_puestos_d * horas_disp * theta   para todo electroterminal d
         x_rd in {0,1}
donde c_rd = 2 * distancia_terminales_reales(r,d) * costo_por_km * n_buses_r
(mismo costo aproximado de pullout+pullin que usa C1b).

Input:  data-processed/rutas_resumen.csv, terminales_por_ruta.csv,
        terminales.csv, data-filtrado/{depots,parameters}.csv
Output: data-processed/rutas_cluster_c2.csv        (caso base, soc100)
        data-processed/rutas_cluster_c2_ciclo.csv  (escenario ciclico)
        results/etapa1_clustering/tablas/capacidad_dos_supuestos.csv
        results/etapa1_clustering/tablas/barrido_theta.csv
        results/etapa1_clustering/graficos/capacidad.png
        results/etapa1_clustering/graficos/barrido_theta.png

Uso:
    python scripts/5-clustering_c2.py
        Red completa: corre los dos supuestos (theta=1, H=24), la grilla de
        H y el barrido de theta.

    python scripts/5-clustering_c2.py --rutas 101 102 301 ... --carga ciclo --theta 0.05
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
HORAS_DISPONIBLES_DEFAULT = 24.0
H_GRILLA = [24.0, 18.0, 10.0]
THETA_BARRIDO = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]


def cargar_datos(subset_rutas=None):
    rutas_resumen = pd.read_csv(DATA_PROCESSED / "rutas_resumen.csv", sep=CSV_SEP)
    terminales_por_ruta = pd.read_csv(DATA_PROCESSED / "terminales_por_ruta.csv", sep=CSV_SEP)
    terminales = pd.read_csv(DATA_PROCESSED / "terminales.csv", sep=CSV_SEP)
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)

    rutas_resumen["route_id"] = rutas_resumen["route_id"].astype(str)
    terminales_por_ruta["route_id"] = terminales_por_ruta["route_id"].astype(str)

    if subset_rutas:
        subset_rutas = {str(r) for r in subset_rutas}
        rutas_resumen = rutas_resumen[rutas_resumen["route_id"].isin(subset_rutas)].reset_index(drop=True)
        terminales_por_ruta = terminales_por_ruta[terminales_por_ruta["route_id"].isin(subset_rutas)]
        if rutas_resumen.empty:
            raise SystemExit(f"--rutas {subset_rutas} no matchea ninguna ruta en rutas_resumen.csv")
    return rutas_resumen, terminales_por_ruta, terminales, depots


def calcular_h_r(rutas_resumen, costos, supuesto):
    """Horas-cargador/dia que demanda cada ruta, segun el supuesto de carga
    (ver docstring del modulo). Devuelve un array alineado con rutas_resumen."""
    kwh_dia = rutas_resumen["kwh_dia"].values
    if supuesto == "soc100":
        exceso = np.maximum(0.0, kwh_dia - rutas_resumen["n_buses_estimados"].values * costos.bateria_util_kwh)
        return exceso / costos.charge_power_kw
    elif supuesto == "ciclo":
        return kwh_dia / costos.charge_power_kw
    raise ValueError(f"supuesto de carga desconocido: {supuesto} (usar 'soc100' o 'ciclo')")


def resolver_asignacion(h_r, c_rd, capacidad_puestos, horas_disponibles, theta):
    """MILP de asignacion generalizada con restriccion de capacidad.
    Devuelve (idx_asignado, capacidad_por_depot). Lanza RuntimeError con el
    detalle de las restricciones en conflicto (via computeIIS) si el modelo
    queda infactible -- no deja que Gurobi falle en silencio."""
    capacidad = capacidad_puestos * horas_disponibles * theta

    m = gp.Model()
    m.Params.OutputFlag = 0
    x = m.addMVar(c_rd.shape, vtype=GRB.BINARY, obj=c_rd)
    m.addConstr(x.sum(axis=1) == 1, name="una_ruta_un_terminal")
    m.addConstr((h_r[:, None] * x).sum(axis=0) <= capacidad, name="capacidad_terminal")
    m.optimize()

    if m.Status != GRB.OPTIMAL:
        m.computeIIS()
        restricciones_conflicto = [c.ConstrName for c in m.getConstrs() if c.IISConstr]
        raise RuntimeError(
            f"MILP infactible (status={m.Status}) con horas_disponibles={horas_disponibles}, theta={theta}. "
            f"Restricciones en conflicto: {restricciones_conflicto[:10]}.")

    idx = x.X.argmax(axis=1)
    return idx, capacidad


def tabla_uso_capacidad(asignacion, h_r, capacidad, depots):
    carga = (pd.Series(h_r, index=asignacion["depot_nombre"].values).groupby(level=0).sum()
             .rename("h_r_asignadas"))
    cap = pd.Series(capacidad, index=depots["nombre"].values, name="capacidad")
    tabla = carga.to_frame().join(cap, how="right").fillna(0.0)
    tabla["uso_pct"] = (tabla["h_r_asignadas"] / tabla["capacidad"] * 100).round(1)
    return tabla


def graficar_capacidad(tabla_soc100, tabla_ciclo, path_png):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, tabla, titulo in [(axes[0], tabla_soc100, "Caso base (SOC inicial 100%)"),
                               (axes[1], tabla_ciclo, "Escenario ciclico (recargar todo lo consumido)")]:
        x = np.arange(len(tabla))
        ax.bar(x, tabla["h_r_asignadas"], color="#2c6e8f", label="Carga asignada")
        ax.bar(x, tabla["capacidad"], color="none", edgecolor="crimson", linewidth=1.5, label="Capacidad")
        ax.set_xticks(x)
        ax.set_xticklabels(tabla.index, rotation=25, ha="right")
        ax.set_title(titulo)
    axes[0].set_ylabel("Horas-cargador / dia")
    axes[0].legend()
    fig.suptitle("Etapa 1 (C2): carga asignada vs. capacidad, bajo los dos supuestos (H=24h, theta=1.0)")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_barrido_theta(barrido, path_png):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    factibles = barrido[barrido["factible"]]
    ax1.plot(factibles["theta"], factibles["rutas_movidas"], "o-", color="#2c6e8f")
    ax1.set_xlabel("theta (holgura de capacidad)")
    ax1.set_ylabel("Rutas movidas respecto de theta=1.0")
    ax1.invert_xaxis()
    ax2.plot(factibles["theta"], factibles["uso_max_pct"], "o-", color="#8f4a2c")
    ax2.axhline(100, color="black", linestyle="--", linewidth=1)
    ax2.set_xlabel("theta (holgura de capacidad)")
    ax2.set_ylabel("Uso maximo de un electroterminal (%)")
    ax2.invert_xaxis()
    fig.suptitle("Barrido de theta -- escenario ciclico, H=24h")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rutas", nargs="*", default=None,
                         help="Checkpoint chico: lista de route_id a incluir.")
    parser.add_argument("--carga", choices=["soc100", "ciclo"], default="ciclo",
                         help="Solo para el checkpoint chico (--rutas): que supuesto usar. Default 'ciclo' "
                              "porque es el que tiene capacidad activa para probar reactividad.")
    parser.add_argument("--theta", type=float, default=0.05,
                         help="Solo para el checkpoint chico: holgura de capacidad (chica a proposito).")
    parser.add_argument("--horas-disponibles", type=float, default=HORAS_DISPONIBLES_DEFAULT)
    args = parser.parse_args()
    corrida_parcial = bool(args.rutas)

    print("=== ETAPA 1 (C2): asignacion con restriccion de capacidad ===\n")
    rutas_resumen, terminales_por_ruta, terminales, depots = cargar_datos(args.rutas)
    costos = parametros.cargar_costos()
    print(f"--- Rutas: {len(rutas_resumen)} | Electroterminales: {len(depots)} | "
          f"bateria util: {costos.bateria_util_kwh:.0f} kWh | potencia cargador: {costos.charge_power_kw:.0f} kW ---")

    dist_km = distancia_ponderada_a_terminales_reales(terminales_por_ruta, terminales, depots,
                                                        parametros.FACTOR_DESVIO)
    dist_km = dist_km.loc[rutas_resumen["route_id"].values]
    n_buses_r = rutas_resumen["n_buses_estimados"].values
    c_rd = 2 * dist_km.values * costos.cost_per_km * n_buses_r[:, None]
    capacidad_puestos = depots["capacity"].astype(float).values

    def resolver_y_armar(supuesto, theta, horas_disponibles):
        h_r = calcular_h_r(rutas_resumen, costos, supuesto)
        idx, capacidad = resolver_asignacion(h_r, c_rd, capacidad_puestos, horas_disponibles, theta)
        asignacion = pd.DataFrame({
            "route_id": rutas_resumen["route_id"].values,
            "depot_id": depots["depot_id"].astype(str).values[idx],
            "depot_nombre": depots["nombre"].values[idx],
            "distancia_km": dist_km.values[np.arange(len(rutas_resumen)), idx],
            "n_buses_estimados": n_buses_r,
            "h_r_horas_cargador": h_r,
        }).reset_index(drop=True)
        return asignacion, h_r, capacidad

    # ------------------------------------------------------------------ #
    # Checkpoint chico: un solo supuesto, capacidad apretada a proposito
    # ------------------------------------------------------------------ #
    if corrida_parcial:
        print(f"\n[CHECKPOINT CHICO] carga={args.carga}, theta={args.theta}, "
              f"horas_disponibles={args.horas_disponibles}")
        asignacion, h_r, capacidad = resolver_y_armar(args.carga, args.theta, args.horas_disponibles)
        tabla = tabla_uso_capacidad(asignacion, h_r, capacidad, depots)
        print("\n--- Uso de capacidad por electroterminal ---")
        print(tabla.round(1).to_string())

        idx_libre = c_rd.argmin(axis=1)
        movidas = int((depots["nombre"].values[idx_libre] != asignacion["depot_nombre"].values).sum())
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
    # Red completa: caso base (soc100) y escenario ciclico, theta=1, H=24
    # ------------------------------------------------------------------ #
    print("\n--- Caso base: soc100, theta=1.0, H=24h ---")
    asig_base, h_r_base, cap_base = resolver_y_armar("soc100", 1.0, HORAS_DISPONIBLES_DEFAULT)
    tabla_base = tabla_uso_capacidad(asig_base, h_r_base, cap_base, depots)
    print(tabla_base.round(1).to_string())

    print("\n--- Escenario ciclico: recargar todo lo consumido, theta=1.0, H=24h ---")
    asig_ciclo, h_r_ciclo, cap_ciclo = resolver_y_armar("ciclo", 1.0, HORAS_DISPONIBLES_DEFAULT)
    tabla_ciclo = tabla_uso_capacidad(asig_ciclo, h_r_ciclo, cap_ciclo, depots)
    print(tabla_ciclo.round(1).to_string())

    # Chequeo central: bajo el caso base, la capacidad no deberia estar activa,
    # por lo que C2 debe coincidir EXACTAMENTE con el minimo sin restriccion
    # (que es la misma metrica de distancia que usa C1b).
    idx_libre = c_rd.argmin(axis=1)
    distintas_de_libre = int((depots["nombre"].values[idx_libre] != asig_base["depot_nombre"].values).sum())
    if distintas_de_libre == 0:
        print("\n  [OK] Caso base: C2 coincide EXACTAMENTE con la asignacion sin capacidad (C1b) -- "
              "confirma que la restriccion de capacidad no esta activa bajo SOC inicial 100%.")
    else:
        print(f"\n  [aviso] Caso base: {distintas_de_libre} rutas de C2 difieren del minimo sin capacidad "
              f"-- revisar si la restriccion SI se esta activando (no se esperaba bajo soc100).")

    print("\n--- Guardando asignaciones ---")
    out_base = DATA_PROCESSED / "rutas_cluster_c2.csv"
    out_ciclo = DATA_PROCESSED / "rutas_cluster_c2_ciclo.csv"
    asig_base.to_csv(out_base, index=False, sep=CSV_SEP)
    asig_ciclo.to_csv(out_ciclo, index=False, sep=CSV_SEP)
    print(f"  -> {out_base} ({len(asig_base)} rutas)")
    print(f"  -> {out_ciclo} ({len(asig_ciclo)} rutas)")

    graficar_capacidad(tabla_base, tabla_ciclo, GRAFICOS / "capacidad.png")
    print(f"  -> {GRAFICOS / 'capacidad.png'}")

    # ------------------------------------------------------------------ #
    # Grilla: los dos supuestos x 3 niveles de horas disponibles de carga
    # ------------------------------------------------------------------ #
    print("\n--- Grilla: supuesto de carga x horas disponibles ---")
    filas_grilla = []
    for supuesto in ("soc100", "ciclo"):
        for H in H_GRILLA:
            try:
                asignacion, h_r, capacidad = resolver_y_armar(supuesto, 1.0, H)
                tabla = tabla_uso_capacidad(asignacion, h_r, capacidad, depots)
                for depot_nombre, fila in tabla.iterrows():
                    filas_grilla.append({"supuesto": supuesto, "horas_disponibles": H,
                                          "depot_nombre": depot_nombre, "h_r_asignadas": fila["h_r_asignadas"],
                                          "capacidad": fila["capacidad"], "uso_pct": fila["uso_pct"],
                                          "factible": True})
                print(f"  {supuesto:7s} H={H:4.0f}h -> factible, uso maximo "
                      f"{tabla['uso_pct'].max():.1f}% ({tabla['uso_pct'].idxmax()})")
            except RuntimeError as e:
                filas_grilla.append({"supuesto": supuesto, "horas_disponibles": H, "depot_nombre": None,
                                      "h_r_asignadas": None, "capacidad": depots["capacity"].sum() * H,
                                      "uso_pct": None, "factible": False})
                print(f"  {supuesto:7s} H={H:4.0f}h -> INFACTIBLE ({e})")
    tabla_grilla = pd.DataFrame(filas_grilla)
    tabla_grilla.to_csv(TABLAS / "capacidad_dos_supuestos.csv", index=False, sep=CSV_SEP)
    print(f"  -> {TABLAS / 'capacidad_dos_supuestos.csv'}")

    # ------------------------------------------------------------------ #
    # Barrido de theta: escenario ciclico, H=24h, de holgura completa hacia
    # la infactibilidad. Responde "a partir de cuando C2 se separa de C1b".
    # ------------------------------------------------------------------ #
    print("\n--- Barrido de theta (escenario ciclico, H=24h) ---")
    filas_barrido = []
    depots_nombre_por_idx = asig_ciclo.set_index("route_id")["depot_nombre"]
    for theta in THETA_BARRIDO:
        try:
            asignacion, h_r, capacidad = resolver_y_armar("ciclo", theta, HORAS_DISPONIBLES_DEFAULT)
            tabla = tabla_uso_capacidad(asignacion, h_r, capacidad, depots)
            movidas = int((asignacion.set_index("route_id")["depot_nombre"] != depots_nombre_por_idx).sum())
            idx_asignado = asignacion["depot_id"].map({v: i for i, v in
                                                         enumerate(depots["depot_id"].astype(str))}).values
            costo_total = float(c_rd[np.arange(len(rutas_resumen)), idx_asignado].sum())
            filas_barrido.append({"theta": theta, "factible": True, "rutas_movidas": movidas,
                                   "costo_asignacion_usd_dia": round(costo_total, 0),
                                   "uso_max_pct": tabla["uso_pct"].max(),
                                   "depot_mas_cargado": tabla["uso_pct"].idxmax()})
            print(f"  theta={theta:.2f} -> factible, {movidas} rutas movidas, "
                  f"uso maximo {tabla['uso_pct'].max():.1f}% ({tabla['uso_pct'].idxmax()})")
        except RuntimeError as e:
            filas_barrido.append({"theta": theta, "factible": False, "rutas_movidas": None,
                                   "costo_asignacion_usd_dia": None, "uso_max_pct": None,
                                   "depot_mas_cargado": None})
            print(f"  theta={theta:.2f} -> INFACTIBLE ({e})")
            break  # tightening es monotono: si theta ya es infactible, uno mas chico tambien lo sera
    tabla_barrido = pd.DataFrame(filas_barrido)
    tabla_barrido.to_csv(TABLAS / "barrido_theta.csv", index=False, sep=CSV_SEP)
    print(f"  -> {TABLAS / 'barrido_theta.csv'}")

    if tabla_barrido["factible"].any():
        graficar_barrido_theta(tabla_barrido, GRAFICOS / "barrido_theta.png")
        print(f"  -> {GRAFICOS / 'barrido_theta.png'}")

    # --- Chequeos de sanidad finales ---
    for etiqueta, asignacion in [("C2 base", asig_base), ("C2 ciclo", asig_ciclo)]:
        assert asignacion["route_id"].is_unique, f"{etiqueta}: alguna ruta quedo asignada mas de una vez."
    assert (tabla_base["h_r_asignadas"] <= tabla_base["capacidad"] + 1e-6).all(), \
        "Caso base: algun electroterminal quedo con mas carga que su capacidad."
    assert (tabla_ciclo["h_r_asignadas"] <= tabla_ciclo["capacidad"] + 1e-6).all(), \
        "Escenario ciclico: algun electroterminal quedo con mas carga que su capacidad."
    print("\n  [OK] Chequeos de sanidad pasaron (asignacion unica, ninguna capacidad excedida en las "
          "corridas factibles).")

    if len(asig_base) != RUTAS_ESPERADAS:
        print(f"  [aviso] {len(asig_base)} rutas asignadas, se esperaban {RUTAS_ESPERADAS}.")

    print("\n=== FIN ETAPA 1 (C2) ===")


if __name__ == "__main__":
    main()
