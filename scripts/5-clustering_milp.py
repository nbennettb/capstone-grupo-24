"""
Etapa 1 (C2) del pipeline de modelacion - ICS2122 Capstone Buses Electricos
(ver docs/context/01_metodologia_y_avance.md seccion 1 y
docs/Propuesta_metodologia_reunion.md seccion 5).

Estrategia de clustering con restriccion de capacidad: asignacion
generalizada (cada RUTA a exactamente un electroterminal) minimizando el
costo de deadhead de salida/regreso, sujeto a que la carga horaria
estimada de cada electroterminal no supere su capacidad.

DEFINICION DE UNIDADES (evita el error del Informe 1: mezclar capacidad
de carga simultanea con volumen de expediciones/dia, ver
docs/context/02_pendientes_profesor.md pregunta #6):
  - Carga de una ruta (h_r), en "horas-cargador/dia": energia total diaria
    que demandan los buses de esa ruta (kWh, sumando TODA su energia
    comercial + deadhead, no solo el excedente de bateria) dividida por la
    potencia de un cargador (kW). Es una cota superior conservadora de la
    demanda real de recarga -- con el supuesto vigente de SOC inicial=100%
    (ver docs/context/02_pendientes_profesor.md #1), la demanda real de
    recarga sera bastante menor; se usa este proxy simple para repartir
    capacidad entre electroterminales mientras la Etapa 3 no este lista.
  - n_buses_r y kwh_total_dia por ruta se leen directamente de
    data-processed/jornadas_ruta.csv (Etapa 2, modo 'ruta': la asignacion
    de buses SIN interlining entre rutas, ya optima dentro de cada ruta).
    Por eso la Etapa 2 se corrio antes que esta.
  - Capacidad de un electroterminal, en las MISMAS unidades:
    capacidad_puestos * HORAS_DISPONIBLES * THETA (holgura configurable).

Formulacion (ver Propuesta_metodologia_reunion.md seccion 5, C2):
    min  sum_{r,d} c_rd * x_rd
    s.a. sum_d x_rd = 1                              para toda ruta r
         sum_r h_r * x_rd <= capacidad_puestos_d * HORAS_DISPONIBLES * THETA   para todo electroterminal d
         x_rd in {0,1}
donde c_rd = 2 * distancia(centroide_r, d) * costo_por_km * n_buses_r
(aproximacion del costo diario de pullout+pullin de la ruta si se basa en d).

Uso:
    python scripts/5-clustering_milp.py --theta 1.0
        Red completa (417 rutas), holgura sin apretar (referencia).

    python scripts/5-clustering_milp.py --rutas 101 102 301 ... --theta 0.05
        Checkpoint chico con capacidad MUY ajustada artificialmente, para
        confirmar que el modelo reacciona (mueve rutas) cuando un
        electroterminal se llena, antes de correr la red completa.
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
from common.clustering import distancia_rutas_a_depots                       # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("05_clustering_c2")
RUTAS_ESPERADAS = 417
HORAS_DISPONIBLES_DEFAULT = 24.0


def cargar_carga_por_ruta():
    """n_buses y energia diaria total (kWh) por ruta, leidos de la Etapa 2
    modo 'ruta' (data-processed/jornadas_ruta.csv): cada jornada de ese
    escenario pertenece integramente a una sola ruta (sin interlining), asi
    que basta con mirar la primera expedicion de cada jornada."""
    jornadas_path = DATA_PROCESSED / "jornadas_ruta.csv"
    if not jornadas_path.exists():
        raise SystemExit(f"No se encontro {jornadas_path}. Correr antes: "
                          f"python scripts/6-vsp_asignacion_buses.py --modo ruta")
    jr = pd.read_csv(jornadas_path, sep=CSV_SEP)
    ex_id_a_ruta = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP,
                                usecols=["expedicion_id", "route_id"]).set_index("expedicion_id")["route_id"]
    primera_expedicion = jr["expedicion_ids"].str.split(";").str[0]
    jr = jr.assign(route_id=primera_expedicion.map(ex_id_a_ruta).astype(str))
    return jr.groupby("route_id").agg(n_buses=("bus_id", "size"), kwh_total_dia=("kwh_total", "sum"))


def resolver_asignacion(carga, dist_km, capacidad_puestos, costos, horas_disponibles, theta):
    h_r = (carga["kwh_total_dia"] / costos.charge_power_kw).values          # horas-cargador/dia por ruta
    n_buses_r = carga["n_buses"].values
    c_rd = 2 * dist_km.values * costos.cost_per_km * n_buses_r[:, None]     # costo diario aprox. pullout+pullin
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
            f"El MILP de asignacion quedo INFACTIBLE (status={m.Status}) -- probablemente theta={theta} "
            f"es demasiado bajo para la capacidad disponible. Restricciones en conflicto: "
            f"{restricciones_conflicto[:10]}. Subir --theta o revisar --horas-disponibles.")

    idx = x.X.argmax(axis=1)
    return idx, h_r, capacidad


def graficar_uso_capacidad(carga_por_depot, path_png):
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(carga_por_depot))
    ax.bar(x, carga_por_depot["h_r_asignadas"], color="#2c6e8f", label="Carga asignada (horas-cargador/dia)")
    ax.bar(x, carga_por_depot["capacidad"], color="none", edgecolor="crimson", linewidth=1.5,
           label="Capacidad disponible")
    ax.set_xticks(x)
    ax.set_xticklabels(carga_por_depot.index, rotation=20, ha="right")
    ax.set_ylabel("Horas-cargador / dia")
    ax.set_title("Etapa 1 (C2): carga asignada vs. capacidad por electroterminal")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rutas", nargs="*", default=None,
                         help="Checkpoint chico: lista de route_id a incluir.")
    parser.add_argument("--theta", type=float, default=1.0,
                         help="Holgura de capacidad (0-1]. Default 1.0 = sin apretar. Usar un valor "
                              "chico (ej. 0.05) en el checkpoint para forzar que el modelo reasigne rutas.")
    parser.add_argument("--horas-disponibles", type=float, default=HORAS_DISPONIBLES_DEFAULT,
                         help=f"Horas/dia que un electroterminal esta disponible para cargar (default "
                              f"{HORAS_DISPONIBLES_DEFAULT}).")
    args = parser.parse_args()
    corrida_parcial = bool(args.rutas)

    print(f"=== ETAPA 1 (C2): asignacion con capacidad (theta={args.theta}, "
          f"horas_disponibles={args.horas_disponibles}) ===\n")

    carga = cargar_carga_por_ruta()
    if args.rutas:
        rutas = {str(r) for r in args.rutas}
        carga = carga[carga.index.isin(rutas)]
        if carga.empty:
            raise SystemExit(f"--rutas {rutas} no matchea ninguna ruta en jornadas_ruta.csv")
    print(f"  Rutas a asignar: {len(carga)}")

    ex = pd.read_csv(DATA_PROCESSED / "expediciones.csv", sep=CSV_SEP)
    ex = ex[ex["route_id"].astype(str).isin(carga.index)]
    depots = pd.read_csv(DATA_FILTRADO / "depots.csv", sep=CSV_SEP)
    dist_km = distancia_rutas_a_depots(ex, depots, parametros.FACTOR_DESVIO).loc[carga.index]

    print("\n--- Resolviendo MILP de asignacion ---")
    idx, h_r, capacidad = resolver_asignacion(carga, dist_km, depots["capacity"].astype(float).values,
                                               parametros.cargar_costos(), args.horas_disponibles, args.theta)

    asignacion = pd.DataFrame({
        "route_id": carga.index,
        "depot_id": depots["depot_id"].astype(str).values[idx],
        "depot_nombre": depots["nombre"].values[idx],
        "distancia_km": dist_km.values[np.arange(len(carga)), idx],
        "n_buses": carga["n_buses"].values,
        "h_r_horas_cargador": h_r,
    }).reset_index(drop=True)

    print("\n--- Uso de capacidad por electroterminal ---")
    carga_por_depot = (asignacion.groupby("depot_nombre")["h_r_horas_cargador"].sum()
                        .rename("h_r_asignadas").to_frame())
    cap_por_depot = pd.Series(capacidad, index=depots["nombre"].values, name="capacidad")
    carga_por_depot = carga_por_depot.join(cap_por_depot, how="right").fillna(0.0)
    carga_por_depot["uso_pct"] = (carga_por_depot["h_r_asignadas"] / carga_por_depot["capacidad"] * 100).round(1)
    print(carga_por_depot.round(1).to_string())

    print("\n--- Guardando resultados ---")
    out_path = DATA_PROCESSED / "rutas_cluster_c2.csv"
    asignacion.to_csv(out_path, index=False, sep=CSV_SEP)
    print(f"  -> {out_path} ({len(asignacion)} rutas)")

    png_path = RESULTS / "uso_capacidad.png"
    graficar_uso_capacidad(carga_por_depot, png_path)
    print(f"  -> {png_path}")

    lineas = [
        "# Reporte Etapa 1 - Clustering C2 (MILP con capacidad)",
        "",
        f"Corrida: {'PARCIAL (checkpoint chico, ' + str(len(asignacion)) + ' rutas)' if corrida_parcial else 'RED COMPLETA (417 rutas)'}",
        f"theta (holgura de capacidad): {args.theta} | horas disponibles/dia: {args.horas_disponibles}",
        "",
        "## Uso de capacidad por electroterminal (horas-cargador/dia)",
        "",
        carga_por_depot.round(1).to_markdown(),
        "",
        "## Comparacion contra C1 (heuristica del mas cercano)",
        "",
    ]
    c1_path = DATA_PROCESSED / "rutas_cluster_c1.csv"
    if c1_path.exists() and not corrida_parcial:
        c1 = pd.read_csv(c1_path, sep=CSV_SEP).set_index("route_id")["depot_id"].astype(str)
        c2 = asignacion.set_index("route_id")["depot_id"].astype(str)
        comunes = c1.index.intersection(c2.index)
        distintas = (c1.loc[comunes] != c2.loc[comunes]).sum()
        lineas.append(f"De {len(comunes)} rutas en comun, {distintas} ({distintas / len(comunes) * 100:.1f}%) "
                       f"quedan en un electroterminal distinto entre C1 y C2.")
    else:
        lineas.append("(Comparacion contra C1 solo disponible en la corrida de red completa, "
                       "con rutas_cluster_c1.csv ya generado.)")
    lineas += ["", "## Grafico", "- `uso_capacidad.png`: carga asignada vs. capacidad por electroterminal.",
               "", "*(Generado automaticamente por scripts/5-clustering_milp.py)*"]
    (RESULTS / "reporte.md").write_text("\n".join(lineas), encoding="utf-8")
    print(f"  -> {RESULTS / 'reporte.md'}")

    # --- Chequeos de sanidad ---
    assert asignacion["route_id"].is_unique, "Alguna ruta quedo asignada mas de una vez."
    assert (carga_por_depot["h_r_asignadas"] <= carga_por_depot["capacidad"] + 1e-6).all(), \
        "Algun electroterminal quedo con mas carga asignada que su capacidad (la restriccion no deberia permitirlo)."
    print("\n  [OK] Chequeos de sanidad pasaron (asignacion unica, ninguna capacidad excedida).")

    if not corrida_parcial and len(asignacion) != RUTAS_ESPERADAS:
        print(f"  [aviso] {len(asignacion)} rutas asignadas, se esperaban {RUTAS_ESPERADAS}.")

    print("\n=== FIN ETAPA 1 (C2) ===")


if __name__ == "__main__":
    main()
