"""
Calibracion del factor de desvio del deadhead (Supuesto 2.4.1 del informe).

El modelo calcula todo desplazamiento sin pasajeros como distancia en linea recta x FACTOR_DESVIO (1,3). Este script mide,
con los trazados GTFS de los buses, cuanto mas largo es el camino recorrido que la recta. Se toman pares de puntos
separados por s km de recorrido (s = 1, 3, 5, 10, 15) y se calcula factor = s / distancia en linea recta.

Salvedades: una ruta comercial rodea mas que un traslado en vacio (el factor medido es cota superior del rodeo de un
deadhead); los buses circulan por avenidas principales; los trazados cubren la red de buses, no todo par de puntos.

Input:  resultados/datos_filtrados/{shapes_bus,shape_distances_bus}.csv,
        resultados/datos_procesados/{rutas_cluster_c1b,rutas_resumen}.csv
Output: resultados/etapa0_calibracion_deadhead/tablas/{factor_por_escala,factor_por_trazado,escala_deadhead_pullout_pullin}.csv
        resultados/etapa0_calibracion_deadhead/graficos/{factor_por_escala,ejemplo_trazado}.png
Consola: factor medido por escala y largo del pullout/pullin (menos de 1 min).

Uso:
    python 5-calibracion_deadhead.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import geo, parametros                                            # noqa: E402
from common.rutas import DATA_FILTRADO, DATA_PROCESSED, CSV_SEP, carpeta_resultados  # noqa: E402

RESULTS = carpeta_resultados("etapa0_calibracion_deadhead")
TABLAS = RESULTS / "tablas"
GRAFICOS = RESULTS / "graficos"
TABLAS.mkdir(exist_ok=True)
GRAFICOS.mkdir(exist_ok=True)

ESCALAS_KM = [1, 3, 5, 10, 15]    # largo de recorrido s de cada ventana
PASO_VENTANA_KM = 0.5             # las ventanas parten cada 0,5 km de recorrido
TRAZADOS_ESPERADOS = 839
UMBRAL_CIRCULAR_KM = 0.5          # extremos a menos de esto: trazado circular
TOL_LARGO_REL = 0.01              # largo calculado vs shape_distances_bus.csv
PERCENTILES = [10, 25, 50, 75, 90]

COLOR_CAJA = "#2c6e8f"
COLOR_MODELO = "#b22222"
COLOR_INTERLINING = "#d95f02"


def estilo(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.7)
    ax.set_axisbelow(True)


def cargar_trazados():
    shapes = pd.read_csv(DATA_FILTRADO / "shapes_bus.csv", sep=CSV_SEP)
    shapes["shape_id"] = shapes["shape_id"].astype(str)
    dist = pd.read_csv(DATA_FILTRADO / "shape_distances_bus.csv", sep=CSV_SEP)
    dist["shape_id"] = dist["shape_id"].astype(str)
    shapes = shapes.sort_values(["shape_id", "shape_pt_sequence"])
    return shapes, dist.set_index("shape_id")["distance_km"]


def recorrido_acumulado(P):
    """Largo acumulado (km) a lo largo de la polilinea proyectada P (n x 2)."""
    return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])


def ventanas_trazado(P, s_km, paso_km=PASO_VENTANA_KM):
    """Para un trazado proyectado P, devuelve (inicio_km, recta_km): para cada ventana de
    s_km de recorrido que parte cada paso_km, la distancia en linea recta entre sus extremos.
    Interpolacion lineal sobre el largo acumulado. Array vacio si el trazado es mas corto que s."""
    c = recorrido_acumulado(P)
    inicios = np.arange(0.0, c[-1] - s_km + 1e-9, paso_km)
    if len(inicios) == 0:
        return inicios, inicios
    def en(t):
        return np.column_stack([np.interp(t, c, P[:, 0]), np.interp(t, c, P[:, 1])])
    recta = np.hypot(*(en(inicios + s_km) - en(inicios)).T)
    return inicios, recta


def resumir(valores):
    v = np.asarray(valores, dtype=float)
    out = {"n": len(v), "media": v.mean()}
    for p, x in zip(PERCENTILES, np.percentile(v, PERCENTILES)):
        out[f"p{p}"] = x
    out["pct_hasta_1_3"] = float((v <= parametros.FACTOR_DESVIO).mean() * 100)
    return out


def medir_trazados(shapes, largo_oficial):
    """Devuelve (factores_por_escala, tabla_por_trazado). factores_por_escala[s] = lista de
    (shape_id, factor) de todas las ventanas."""
    factores = {s: [] for s in ESCALAS_KM}
    filas = []
    for sid, g in shapes.groupby("shape_id", sort=False):
        P = geo.xy(g["shape_pt_lat"].values, g["shape_pt_lon"].values)
        c = recorrido_acumulado(P)
        recta_ext = float(np.hypot(*(P[-1] - P[0])))
        circular = recta_ext < UMBRAL_CIRCULAR_KM
        fila = {"shape_id": sid, "largo_calculado_km": c[-1],
                "largo_shape_distances_km": largo_oficial.get(sid, np.nan),
                "recta_extremos_km": recta_ext, "circular": circular,
                "factor_trazado_completo": np.nan if circular else c[-1] / recta_ext}
        for s in ESCALAS_KM:
            _, recta = ventanas_trazado(P, s)
            if len(recta):
                f = s / np.maximum(recta, 1e-6)
                factores[s] += [(sid, v) for v in f]
                fila[f"mediana_{s}km"] = float(np.median(f))
                fila[f"n_ventanas_{s}km"] = len(f)
            else:
                fila[f"mediana_{s}km"] = np.nan
                fila[f"n_ventanas_{s}km"] = 0
        filas.append(fila)
    return factores, pd.DataFrame(filas)


def tabla_por_escala(factores, por_trazado):
    filas = []
    for s in ESCALAS_KM:
        vals = np.array([v for _, v in factores[s]])
        fila = {"escala_km": s, "version": "todas las ventanas", "n_trazados": len({i for i, _ in factores[s]})}
        fila.update(resumir(vals))
        filas.append(fila)
        med = por_trazado[f"mediana_{s}km"].dropna().values
        fila = {"escala_km": s, "version": "mediana por trazado", "n_trazados": len(med)}
        fila.update(resumir(med))
        filas.append(fila)
    return pd.DataFrame(filas).round(3)


def escala_pullout_pullin():
    """Largo del deadhead de salida/regreso de cada ruta (asignacion C1b), ponderado por buses estimados."""
    asig = pd.read_csv(DATA_PROCESSED / "rutas_cluster_c1b.csv", sep=CSV_SEP, dtype={"route_id": str})
    resumen = pd.read_csv(DATA_PROCESSED / "rutas_resumen.csv", sep=CSV_SEP, dtype={"route_id": str})
    asig = asig.merge(resumen[["route_id", "n_buses_estimados"]], on="route_id", how="left")
    d = asig["distancia_km"].values               # ya incluye FACTOR_DESVIO
    w = asig["n_buses_estimados"].values
    orden = np.argsort(d)
    acum = np.cumsum(w[orden]) / w.sum()
    fila = {"base": "rutas (sin ponderar)"}
    fila.update({f"p{p}": np.percentile(d, p) for p in PERCENTILES})
    fila["media"] = d.mean()
    pond = {"base": "ponderado por buses estimados"}
    pond.update({f"p{p}": d[orden][np.searchsorted(acum, p / 100)] for p in PERCENTILES})
    pond["media"] = float((d * w).sum() / w.sum())
    t = pd.DataFrame([fila, pond])
    t.insert(1, "unidad", "km de recorrido modelado (recta x factor)")
    return t.round(2), d, w


def graficar_factor_por_escala(factores, escala_pp, path_png):
    fig, ax = plt.subplots(figsize=(9, 5.2))
    datos = [np.array([v for _, v in factores[s]]) for s in ESCALAS_KM]
    pos = np.arange(len(ESCALAS_KM))
    for i, v in enumerate(datos):
        p10, p25, p50, p75, p90 = np.percentile(v, [10, 25, 50, 75, 90])
        ax.plot([i, i], [p10, p90], color=COLOR_CAJA, linewidth=1.2)
        ax.bar(i, p75 - p25, bottom=p25, width=0.42, color=COLOR_CAJA, alpha=0.85, zorder=3)
        ax.plot([i - 0.21, i + 0.21], [p50, p50], color="white", linewidth=2, zorder=4)
        ax.text(i + 0.26, p50, f"{p50:.2f}", va="center", fontsize=9)
    ax.axhline(parametros.FACTOR_DESVIO, color=COLOR_MODELO, linestyle="--", linewidth=1.4,
               label=f"Factor del modelo ({parametros.FACTOR_DESVIO})")
    ax.axhline(1.0, color="#888888", linewidth=0.8)
    ax.axvspan(-0.5, ESCALAS_KM.index(3) + 0.5, color=COLOR_INTERLINING, alpha=0.07, zorder=0)
    ax.text(-0.45, 3.75, f"escala del interlining\n(radio <= {parametros.RADIO_INTERLINING_KM:g} km)",
            fontsize=8, color=COLOR_INTERLINING, va="top")
    ax.axvspan(ESCALAS_KM.index(5) + 0.5, len(ESCALAS_KM) - 0.5, color=COLOR_CAJA, alpha=0.07, zorder=0)
    ax.text(ESCALAS_KM.index(5) + 0.55, 3.75,
            f"escala del pullout/pullin\n(mediana {escala_pp['mediana']:.0f} km, "
            f"p10-p90: {escala_pp['p10']:.0f}-{escala_pp['p90']:.0f} km)",
            fontsize=8, color=COLOR_CAJA, va="top")
    ax.set_xticks(pos)
    ax.set_xticklabels([f"{s} km" for s in ESCALAS_KM])
    ax.set_xlabel("Largo de recorrido entre los dos puntos (s)")
    ax.set_ylabel("Factor de rodeo = recorrido / linea recta")
    ax.set_ylim(0.9, 3.8)
    ax.set_title("Cuanto mas largo que la recta es el camino real de un bus\n"
                 "(839 trazados GTFS; caja = p25-p75, bigote = p10-p90, trazo blanco = mediana)")
    ax.legend(frameon=False, loc="lower right")
    estilo(ax)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)


def graficar_ejemplo(shapes, factores, por_trazado, path_png, s_km=10):
    """Un trazado real con una ventana de s_km cuyo factor es cercano a la mediana de esa escala."""
    mediana = float(np.median([v for _, v in factores[s_km]]))
    cand = por_trazado.dropna(subset=[f"mediana_{s_km}km"]).copy()
    cand["dif"] = (cand[f"mediana_{s_km}km"] - mediana).abs()
    sid = cand.sort_values(["dif", "shape_id"]).iloc[0]["shape_id"]
    g = shapes[shapes["shape_id"] == sid]
    P = geo.xy(g["shape_pt_lat"].values, g["shape_pt_lon"].values)
    inicios, recta = ventanas_trazado(P, s_km)
    k = int(np.argmin(np.abs(s_km / np.maximum(recta, 1e-6) - mediana)))
    c = recorrido_acumulado(P)
    t0, t1 = inicios[k], inicios[k] + s_km
    m = (c >= t0) & (c <= t1)
    A = np.array([np.interp(t0, c, P[:, 0]), np.interp(t0, c, P[:, 1])])
    B = np.array([np.interp(t1, c, P[:, 0]), np.interp(t1, c, P[:, 1])])

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.plot(P[:, 0], P[:, 1], color="#cfcfcf", linewidth=1.5, label="trazado completo")
    ax.plot(P[m, 0], P[m, 1], color=COLOR_CAJA, linewidth=2.5, label=f"camino recorrido: {s_km} km")
    ax.plot([A[0], B[0]], [A[1], B[1]], color=COLOR_MODELO, linestyle="--", linewidth=2,
            label=f"linea recta: {recta[k]:.1f} km")
    ax.scatter([A[0], B[0]], [A[1], B[1]], color="black", zorder=5, s=25)
    ax.set_aspect("equal")
    ax.set_xlabel("km (este)")
    ax.set_ylabel("km (norte)")
    ax.set_title(f"Ejemplo: trazado {sid}, factor = {s_km} / {recta[k]:.1f} = {s_km / recta[k]:.2f}")
    ax.legend(frameon=False, fontsize=8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    plt.close(fig)
    return sid, s_km / recta[k]


def main():
    print("=== CALIBRACION DEL FACTOR DE DESVIO DEL DEADHEAD ===\n")
    shapes, largo_oficial = cargar_trazados()
    print(f"--- Trazados: {shapes['shape_id'].nunique()} | puntos: {len(shapes):,} ---")

    factores, por_trazado = medir_trazados(shapes, largo_oficial)
    assert len(por_trazado) == TRAZADOS_ESPERADOS, \
        f"Se esperaban {TRAZADOS_ESPERADOS} trazados y hay {len(por_trazado)}."
    for s in ESCALAS_KM:
        v = np.array([x for _, x in factores[s]])
        assert np.isfinite(v).all(), f"Hay factores no finitos a la escala de {s} km."
        assert (v >= 1 - 1e-6).all(), f"Hay un factor < 1 a la escala de {s} km: el recorrido no puede ser menor que la recta."
    err = (por_trazado["largo_calculado_km"] / por_trazado["largo_shape_distances_km"] - 1).abs()
    assert err.max() <= TOL_LARGO_REL, (f"El largo calculado difiere hasta {err.max():.2%} de "
                                        f"shape_distances_bus.csv (tolerancia {TOL_LARGO_REL:.0%}).")
    por_trazado["error_largo_rel"] = err

    por_escala = tabla_por_escala(factores, por_trazado)
    escala_pp, d_pp, w_pp = escala_pullout_pullin()
    pond = escala_pp.iloc[1]
    print("\n--- Factor de rodeo por escala (todas las ventanas) ---")
    print(por_escala[por_escala["version"] == "todas las ventanas"]
          [["escala_km", "n", "p10", "p25", "p50", "p75", "p90", "pct_hasta_1_3"]].to_string(index=False))
    print("\n--- Escala del pullout/pullin de la asignacion C1b (km de recorrido modelado) ---")
    print(escala_pp.to_string(index=False))

    por_escala.to_csv(TABLAS / "factor_por_escala.csv", index=False, sep=CSV_SEP)
    por_trazado.round(4).to_csv(TABLAS / "factor_por_trazado.csv", index=False, sep=CSV_SEP)
    escala_pp.to_csv(TABLAS / "escala_deadhead_pullout_pullin.csv", index=False, sep=CSV_SEP)
    print(f"\n  -> {TABLAS}/ (3 tablas)")

    graficar_factor_por_escala(factores, {"mediana": pond["p50"], "p10": pond["p10"], "p90": pond["p90"]},
                               GRAFICOS / "factor_por_escala.png")
    sid_ej, f_ej = graficar_ejemplo(shapes, factores, por_trazado, GRAFICOS / "ejemplo_trazado.png")
    print(f"  -> {GRAFICOS}/ (2 graficos; ejemplo: trazado {sid_ej}, factor {f_ej:.2f})")

    todas = por_escala[por_escala["version"] == "todas las ventanas"].set_index("escala_km")
    print("\n--- Resultado (Supuesto 2.4.1) ---")
    print(f"  Interlining (1-3 km): mediana del factor {todas.loc[1, 'p50']:.2f} a {todas.loc[3, 'p50']:.2f}; "
          f"el modelo usa {parametros.FACTOR_DESVIO} (conservador).")
    print(f"  Pullout/pullin (5-15 km): mediana del factor {todas.loc[5, 'p50']:.2f} a {todas.loc[15, 'p50']:.2f}; "
          f"el modelo usa {parametros.FACTOR_DESVIO} (cercano a la mediana, puede subestimar a escalas largas).")
    print(f"  Trazados circulares excluidos del cociente completo: {int(por_trazado['circular'].sum())}; "
          f"error maximo del largo calculado: {err.max():.2%}.")

    print("\n  [OK] Chequeos pasaron (839 trazados, factores >= 1, largo consistente con shape_distances_bus.csv).")
    print("\n=== FIN CALIBRACION ===")


if __name__ == "__main__":
    main()
