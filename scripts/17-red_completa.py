"""
Red completa - ICS2122 Capstone Buses Electricos (ver docs/contexto_entrega_3/00_LEEME.md).

No corre ningun modelo: junta lo que dejo correr_terminal.py en cada results/instancia_<siglas>/ (los KPIs de 14- y el
plan de carga de 13- --exacto) y arma la tabla de la red completa, que es la suma de los cuatro electroterminales, para
los cuatro escenarios de la escalera.

Antes de sumar comprueba que:
  - los cuatro terminales esten corridos y su plan de carga validado (15-, los 6 criterios OK);
  - en la Propuesta completa no haya deficit de energia ni mas buses cargando que puestos;
  - los dos casos base, sumados terminal por terminal, sean iguales al caso base de la red completa
    (results/caso_base/, corrido sin --terminal): jornadas, reservas, energia y costo.

Las sumas son directas (costos, buses, km, kWh). Los porcentajes de la red se recalculan con las sumas:
  % km vacios = km vacios / km totales; USD/kWh = costo de energia / kWh cargados; % en valle ponderado por kWh;
  utilizacion del bus = horas con pasajeros / (buses totales x 24 h).
La distancia al optimo es (plan - cota) / plan en energia + reservas, igual que 13-; la de la red usa las sumas de
los cuatro planes y las cuatro cotas.

Output: results/red_completa/tablas/*.csv, graficos/*.png (+ .csv con los datos de cada grafico),
        results/red_completa/resumen_para_analisis.md

Uso:
    python scripts/17-red_completa.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import graficos as gr, nombres                     # noqa: E402
from common.rutas import CSV_SEP, RESULTS_DIR                   # noqa: E402

TERMINALES = {"VN": "Vespucio Norte", "EC": "El Conquistador", "LESR": "Los Espinos + Santa Rosa", "LR": "La Reina"}
CODIGO = ["E0", "E1", "E2-FIFO", "E2"]
ESCENARIOS = [nombres.ESCENARIO[c] for c in CODIGO]
COLOR = {nombres.ESCENARIO[c]: gr.ESCENARIO[c] for c in CODIGO}
REFERENCIA = nombres.ESCENARIO["E1"]          # la comparacion justa de la propuesta
RED = "Red completa"

SUMAS = ["costo_total", "costo_flota", "costo_reservas", "costo_km_vacios", "costo_espera", "costo_energia",
         "costo_eventos", "costo_total_con_espera_nocturna", "buses_jornadas_sin_bateria", "buses_operativos",
         "reservas", "buses_totales", "eventos", "km_vacios", "km_comerciales", "horas_con_pasajeros", "kwh_cargados",
         "kwh_deficit", "puestos"]
SALIDA = RESULTS_DIR / "red_completa"
EXACTO = Path("etapa4") / "h0_d15" / "exacto"


def leer(path):
    return pd.read_csv(path, sep=CSV_SEP)


def fmt(x, d=0):
    return "-" if pd.isna(x) else f"{x:,.{d}f}"


# --------------------------------------------------------------------------- #
# Lectura y validaciones
# --------------------------------------------------------------------------- #

def leer_terminal(siglas, chequeos):
    """KPIs de los cuatro escenarios y datos del plan de carga exacto de un terminal."""
    nombre = TERMINALES[siglas]
    carpeta = RESULTS_DIR / f"instancia_{siglas}"
    kpis_path = carpeta / "kpis" / "tablas" / "kpis_escenarios.csv"
    if not kpis_path.exists():
        sys.exit(f"Falta {kpis_path}. Correr antes: python scripts/correr_terminal.py para {nombre}.")
    k = leer(kpis_path)
    k = k[k["variante"] == "base"].copy()
    assert sorted(k["escenario"]) == sorted(ESCENARIOS), f"{nombre}: escenarios incompletos en {kpis_path}"
    completa = k[k["escenario"] == nombres.ESCENARIO["E2"]].iloc[0]
    assert completa["modelo"] == "exacto", (f"{nombre}: la Propuesta completa no es el plan exacto "
                                           f"(modelo = {completa['modelo']}). Correr el paso 4 de correr_terminal.py.")
    k.insert(0, "terminal", nombre)

    val = leer(carpeta / EXACTO / "validacion.csv")
    ok_val = (val["resultado"] == "OK").all() and len(val) == 6
    chequeos.append((f"{nombre}: plan de carga validado (15-)", ok_val,
                     f"{(val['resultado'] == 'OK').sum()} de 6 criterios OK"))
    ok_cap = completa["max_buses_minuto"] <= completa["puestos"] + 1e-9 and abs(k["kwh_deficit"]).max() < 1e-6
    chequeos.append((f"{nombre}: Propuesta completa sin deficit y con buses cargando <= puestos", ok_cap,
                     f"maximo {completa['max_buses_minuto']:.0f} de {completa['puestos']:.0f} puestos; "
                     f"deficit maximo {abs(k['kwh_deficit']).max():.3f} kWh"))

    modelo = leer(carpeta / EXACTO / "modelo.csv")
    resumen = leer(carpeta / EXACTO / "resumen.csv").iloc[0]
    cota = modelo.loc[modelo["modelo"].str.startswith("Modelo relajado"), "objetivo_usd"].iloc[0]
    plan = modelo.loc[modelo["modelo"].str.startswith("Programa exacto, final"), "objetivo_usd"].iloc[0]
    plan_carga = {
        "terminal": nombre, "puestos": completa["puestos"], "ventanas": resumen["ventanas"],
        "maximo_buses_cargando": resumen["maximo_buses_cargando"], "reservas": completa["reservas"],
        "eventos": completa["eventos"], "eventos_por_ventana": completa["eventos"] / resumen["ventanas"],
        "energia_sobre_capacidad_pct": resumen["energia_sobre_capacidad_pct"],
        "cota_inferior_usd": cota, "plan_usd": plan, "brecha_pct": 100 * (1 - cota / plan),
        "segundos_plan_exacto": resumen["segundos_total_script"], "memoria_mb": resumen["memoria_mb"],
    }
    return k, plan_carga


def chequear_caso_base(kpis, chequeos):
    """Los casos base sumados por terminal deben ser iguales al caso base de la red completa."""
    path = RESULTS_DIR / "caso_base" / "tablas" / "resumen_carga.csv"
    if not path.exists():
        chequeos.append(("Caso base de la red completa disponible", False, f"falta {path}"))
        return
    red = leer(path)
    for codigo in ("E0", "E1"):
        fila = red[(red["escenario"] == codigo) & (red["soc_pct"] == 100)]
        if fila.empty:
            chequeos.append((f"{nombres.ESCENARIO[codigo]}: igual a la red completa", False,
                             f"no hay fila {codigo} al 100% en {path}"))
            continue
        r = fila.iloc[0]
        s = kpis[kpis["escenario"] == nombres.ESCENARIO[codigo]][SUMAS].sum()
        pares = [("jornadas finales", s["buses_operativos"], r["buses_final"], 0.5),
                 ("reservas", s["reservas"], r["buses_reserva"], 0.5),
                 ("kWh cargados", s["kwh_cargados"], r["kwh_cargados"], 1.0),
                 ("costo total (USD)", s["costo_total_con_espera_nocturna"], r["costo_total_usd"], 5.0)]
        ok = all(abs(a - b) <= tol for _, a, b, tol in pares)
        detalle = "; ".join(f"{n} {fmt(a, 0)} (red {fmt(b, 0)})" for n, a, b, _ in pares)
        chequeos.append((f"{nombres.ESCENARIO[codigo]}: suma de los terminales = red completa", ok, detalle))


# --------------------------------------------------------------------------- #
# Tablas
# --------------------------------------------------------------------------- #

def totales_red(kpis):
    """Suma por escenario y porcentajes recalculados con las sumas."""
    s = kpis.groupby("escenario", sort=False)[SUMAS].sum().reindex(ESCENARIOS)
    kwh_valle = (kpis["pct_valle"] * kpis["kwh_cargados"]).groupby(kpis["escenario"]).sum().reindex(ESCENARIOS)
    s["buses_extra_bateria"] = s["buses_totales"] - s["buses_jornadas_sin_bateria"]
    s["pct_km_vacios"] = 100 * s["km_vacios"] / (s["km_vacios"] + s["km_comerciales"])
    s["usd_kwh"] = s["costo_energia"] / s["kwh_cargados"]
    s["pct_valle"] = kwh_valle / s["kwh_cargados"]
    s["utilizacion_bus_pct"] = 100 * s["horas_con_pasajeros"] / (s["buses_totales"] * 24)
    s = s.reset_index()
    s.insert(0, "terminal", RED)
    return s


def tabla_ahorro(largo):
    """Costo total por terminal y escenario, y ahorro de la Propuesta completa contra la referencia."""
    piv = largo.pivot(index="terminal", columns="escenario", values="costo_total")[ESCENARIOS]
    piv = piv.reindex(list(TERMINALES.values()) + [RED])
    completa = nombres.ESCENARIO["E2"]
    piv["ahorro_propuesta_completa_usd"] = piv[REFERENCIA] - piv[completa]
    piv["ahorro_propuesta_completa_pct"] = 100 * (1 - piv[completa] / piv[REFERENCIA])
    return piv.reset_index()


# --------------------------------------------------------------------------- #
# Graficos
# --------------------------------------------------------------------------- #

def grafico_costo(red, path):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    gr.estilo(ax)
    x = np.arange(len(ESCENARIOS))
    millones = red["costo_total"].values / 1e6
    ref = millones[ESCENARIOS.index(REFERENCIA)]
    ax.bar(x, millones, width=0.6, color=[COLOR[e] for e in ESCENARIOS], edgecolor=gr.FONDO, linewidth=2)
    for xi, v, e in zip(x, millones, ESCENARIOS):
        texto = f"{v:,.2f} M".replace(".", ",")
        if e in ESCENARIOS[2:]:
            texto += f"\n{100 * (v / ref - 1):+.0f}%".replace(".", ",")
        ax.text(xi, v + millones.max() * 0.015, texto, ha="center", va="bottom", fontsize=9, color=gr.TEXTO)
    ax.set_xticks(x, [nombres.CORTO[c] for c in CODIGO], fontsize=9)
    ax.set_ylabel("Millones de USD por dia")
    ax.set_ylim(0, millones.max() * 1.22)
    ax.set_title(f"Costo diario de la red completa (los % son contra el {REFERENCIA.lower()})",
                 loc="left", fontsize=10, color=gr.TEXTO)
    datos = pd.DataFrame({"escenario": ESCENARIOS, "costo_total_usd": red["costo_total"].values,
                          "variacion_vs_referencia_pct": 100 * (millones / ref - 1)})
    gr.guardar(fig, path, datos)


def grafico_buses(red, path):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    gr.estilo(ax)
    x = np.arange(len(ESCENARIOS))
    op, res = red["buses_operativos"].values, red["reservas"].values
    c_op, c_res = gr.CATEGORICOS[6], gr.CATEGORICOS[4]
    ax.bar(x, op, width=0.6, color=c_op, edgecolor=gr.FONDO, linewidth=2, label="Buses que operan las jornadas")
    ax.bar(x, res, bottom=op, width=0.6, color=c_res, edgecolor=gr.FONDO, linewidth=2,
           label="Buses de reserva (cubren a los que siguen cargando)")
    for xi, t in zip(x, op + res):
        ax.text(xi, t + (op + res).max() * 0.015, f"{t:,.0f}".replace(",", "."), ha="center", va="bottom",
                fontsize=9, color=gr.TEXTO)
    ax.set_xticks(x, [nombres.CORTO[c] for c in CODIGO], fontsize=9)
    ax.set_ylabel("Buses")
    ax.set_ylim(0, (op + res).max() * 1.15)
    ax.set_title("Buses necesarios en la red completa", loc="left", fontsize=10, color=gr.TEXTO)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    datos = pd.DataFrame({"escenario": ESCENARIOS, "buses_operativos": op, "reservas": res, "buses_totales": op + res})
    gr.guardar(fig, path, datos)


def grafico_terminales(largo, path):
    fig, ax = plt.subplots(figsize=(9, 4.4))
    gr.estilo(ax)
    terminales = list(TERMINALES.values())
    x = np.arange(len(terminales))
    ancho = 0.2
    datos = largo[largo["terminal"].isin(terminales)][["terminal", "escenario", "costo_total"]]
    for i, e in enumerate(ESCENARIOS):
        v = datos[datos["escenario"] == e].set_index("terminal").reindex(terminales)["costo_total"].values / 1e6
        ax.bar(x + (i - 1.5) * ancho, v, width=ancho, color=COLOR[e], edgecolor=gr.FONDO, linewidth=1.5,
               label=nombres.CORTO[CODIGO[i]])
    ax.set_xticks(x, terminales, fontsize=9)
    ax.set_ylabel("Millones de USD por dia")
    ax.set_title("Costo diario por electroterminal", loc="left", fontsize=10, color=gr.TEXTO)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    gr.guardar(fig, path, datos)


# --------------------------------------------------------------------------- #
# Resumen
# --------------------------------------------------------------------------- #

def seccion_kpis(red):
    filas = [
        ("Costo total (USD/dia)", "costo_total", 0), ("  flota", "costo_flota", 0),
        ("  buses de reserva", "costo_reservas", 0), ("  km vacios", "costo_km_vacios", 0),
        ("  espera", "costo_espera", 0), ("  energia", "costo_energia", 0),
        ("  eventos de carga", "costo_eventos", 0),
        ("Buses que operan las jornadas", "buses_operativos", 0), ("Buses de reserva", "reservas", 0),
        ("Buses totales", "buses_totales", 0), ("Buses extra por bateria", "buses_extra_bateria", 0),
        ("% km vacios", "pct_km_vacios", 1), ("Costo medio de la energia (USD/kWh)", "usd_kwh", 4),
        ("% de la energia en horario valle", "pct_valle", 1), ("Eventos de carga", "eventos", 0),
        ("Utilizacion del bus (%)", "utilizacion_bus_pct", 1),
    ]
    r = red.set_index("escenario")
    t = pd.DataFrame([[n] + [fmt(r.loc[e, c], d) for e in ESCENARIOS] for n, c, d in filas],
                     columns=["KPI"] + ESCENARIOS)
    return t.to_markdown(index=False)


def escribir_resumen(red, ahorro, plan, chequeos, path):
    r = red.set_index("escenario")
    ref, prop = r.loc[REFERENCIA], r.loc[nombres.ESCENARIO["E2"]]
    base = r.loc[nombres.ESCENARIO["E0"]]
    p_red = plan[plan["terminal"] == RED].iloc[0]

    a = ahorro.copy()
    for c in a.columns[1:]:
        a[c] = a[c].map(lambda v, c=c: fmt(v, 1) if c.endswith("_pct") else fmt(v, 0))
    a.columns = ["Electroterminal"] + [nombres.CORTO[c] for c in CODIGO] + [
        "Ahorro de la Propuesta completa (USD)", f"Ahorro (%)"]

    p = plan.copy()
    p = p[["terminal", "puestos", "maximo_buses_cargando", "ventanas", "reservas", "eventos_por_ventana",
           "energia_sobre_capacidad_pct", "plan_usd", "cota_inferior_usd", "brecha_pct", "segundos_plan_exacto",
           "memoria_mb"]]
    p.columns = ["Electroterminal", "Puestos", "Maximo de buses cargando a la vez", "Ventanas de carga", "Reservas",
                 "Eventos por ventana", "Energia / capacidad 24 h (%)", "Plan: energia + reservas (USD)",
                 "Cota inferior (USD)", "Distancia a la cota (%)", "Tiempo plan exacto (s)", "Memoria (MB)"]
    for c, d in [("Puestos", 0), ("Maximo de buses cargando a la vez", 0), ("Ventanas de carga", 0),
                 ("Reservas", 0), ("Eventos por ventana", 2), ("Energia / capacidad 24 h (%)", 1),
                 ("Plan: energia + reservas (USD)", 0), ("Cota inferior (USD)", 0), ("Distancia a la cota (%)", 2),
                 ("Tiempo plan exacto (s)", 0), ("Memoria (MB)", 0)]:
        p[c] = p[c].map(lambda v, d=d: fmt(v, d))

    val = "\n".join(f"- [{'OK' if ok else 'FALLA'}] {n}: {d}" for n, ok, d in chequeos)
    texto = f"""# Red completa: resumen para el analisis

Suma de los cuatro electroterminales (Vespucio Norte, El Conquistador, Los Espinos + Santa Rosa y La Reina), cada
uno corrido por separado con `scripts/correr_terminal.py`. Generado por `scripts/17-red_completa.py`.

Todas las cifras son de un dia laboral tipico, en USD por dia. El costo total no incluye la espera nocturna en el
patio (estacionar de noche no es un costo de operacion), igual que en el resumen de cada terminal.

## 1. Validaciones

{val}

## 2. Cifras principales

- Costo total de la red: {fmt(base['costo_total'])} USD/dia en el caso base, {fmt(ref['costo_total'])} con interlining
  y **{fmt(prop['costo_total'])} con la Propuesta completa**. Contra el caso base con interlining, que es la
  comparacion justa, la propuesta ahorra **{fmt(ref['costo_total'] - prop['costo_total'])} USD/dia
  ({fmt(100 * (1 - prop['costo_total'] / ref['costo_total']), 1)}%)**.
- Buses: {fmt(ref['buses_totales'])} con interlining y **{fmt(prop['buses_totales'])}** con la propuesta
  ({fmt(ref['buses_totales'] - prop['buses_totales'])} menos), de los cuales {fmt(prop['reservas'])} son de reserva.
- El plan de carga de la propuesta es aplicable en los cuatro terminales: nunca hay mas buses cargando que puestos,
  y el validador independiente da los 6 criterios OK en todos.
- Distancia al optimo de la red, en energia + reservas: **{fmt(p_red['brecha_pct'], 2)}%** sobre la cota inferior
  ({fmt(p_red['plan_usd'])} contra {fmt(p_red['cota_inferior_usd'])} USD/dia).

## 3. KPIs de la red completa por escenario

{seccion_kpis(red)}

Porcentajes de la red recalculados con las sumas (no son el promedio simple de los terminales).

## 4. Costo total por electroterminal

{a.to_markdown(index=False)}

El ahorro es contra el caso base con interlining.

## 5. Plan de carga de la Propuesta completa por electroterminal

{p.to_markdown(index=False)}

- La cota inferior es el costo del modelo relajado: ningun plan real puede costar menos. Distancia a la cota =
  (plan - cota) / plan.
- La fila de la red suma planes y cotas, y la distancia se calcula con esas sumas.
- Los Espinos + Santa Rosa comparten sus 270 puestos (supuesto declarado, patios a 1,1 km).

## 6. Figuras (`results/red_completa/graficos/`)

- `costo_diario_red.png`: costo total de la red por escenario, con el % contra el caso base con interlining.
- `buses_red.png`: buses que operan las jornadas y buses de reserva, por escenario.
- `costo_por_terminal.png`: costo total de cada electroterminal por escenario.
"""
    gr._escribir(lambda q: q.write_text(texto, encoding="utf-8"), path)


# --------------------------------------------------------------------------- #

def main():
    print("=== Red completa: suma de los cuatro electroterminales ===\n")
    chequeos = []
    kpis, planes = [], []
    for siglas in TERMINALES:
        k, p = leer_terminal(siglas, chequeos)
        kpis.append(k)
        planes.append(p)
    kpis = pd.concat(kpis, ignore_index=True)
    chequear_caso_base(kpis, chequeos)

    red = totales_red(kpis)
    largo = pd.concat([kpis, red], ignore_index=True)
    columnas = ["terminal", "escenario"] + SUMAS + ["buses_extra_bateria", "pct_km_vacios", "usd_kwh", "pct_valle",
                                                     "utilizacion_bus_pct"]
    largo = largo[columnas]

    plan = pd.DataFrame(planes)
    suma = plan[["puestos", "ventanas", "reservas", "eventos", "cota_inferior_usd", "plan_usd"]].sum()
    plan.loc[len(plan)] = {
        "terminal": RED, **suma.to_dict(), "maximo_buses_cargando": np.nan,
        "eventos_por_ventana": suma["eventos"] / suma["ventanas"], "energia_sobre_capacidad_pct": np.nan,
        "brecha_pct": 100 * (1 - suma["cota_inferior_usd"] / suma["plan_usd"]),
        "segundos_plan_exacto": plan["segundos_plan_exacto"].sum(), "memoria_mb": plan["memoria_mb"].max(),
    }
    ahorro = tabla_ahorro(largo)

    tablas, graficos = SALIDA / "tablas", SALIDA / "graficos"
    tablas.mkdir(parents=True, exist_ok=True)
    graficos.mkdir(parents=True, exist_ok=True)
    for df, nombre in [(largo, "kpis_red"), (ahorro, "costo_por_terminal"), (plan, "plan_de_carga_por_terminal"),
                       (pd.DataFrame(chequeos, columns=["criterio", "ok", "detalle"]), "validaciones")]:
        gr._escribir(lambda q, df=df: df.to_csv(q, index=False, sep=CSV_SEP), tablas / f"{nombre}.csv")
    grafico_costo(red, graficos / "costo_diario_red.png")
    grafico_buses(red, graficos / "buses_red.png")
    grafico_terminales(largo, graficos / "costo_por_terminal.png")
    escribir_resumen(red, ahorro, plan, chequeos, SALIDA / "resumen_para_analisis.md")

    print("--- Validaciones ---")
    for n, ok, d in chequeos:
        print(f"  [{'OK' if ok else 'FALLA'}] {n}: {d}")
    r = red.set_index("escenario")
    print("\n--- Red completa ---")
    print(r[["costo_total", "buses_operativos", "reservas", "buses_totales", "pct_km_vacios", "usd_kwh"]]
          .round(2).to_string())
    print(f"\n  Distancia del plan de carga a la cota (red): {plan.iloc[-1]['brecha_pct']:.2f}%")
    print(f"\n  -> {SALIDA}")
    todo_ok = all(ok for _, ok, _ in chequeos)
    print("\n  TODAS LAS VALIDACIONES OK" if todo_ok else "\n  HAY VALIDACIONES QUE FALLAN (ver arriba)")
    print("\n=== FIN RED COMPLETA ===")
    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
