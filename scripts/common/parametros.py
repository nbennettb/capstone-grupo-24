"""Unica fuente de verdad de los supuestos y costos usados en las Etapas
0-4, segun la metodologia vigente (docs/context/01_metodologia.md) y las
decisiones de docs/context/02_supuestos_y_decisiones.md.

Para correr un analisis de sensibilidad, cambiar los valores de aqui (o
pasarlos como override a las funciones de los scripts de cada etapa) en vez
de hardcodearlos de nuevo en cada script.
"""

from dataclasses import dataclass

import pandas as pd

from .rutas import DATA_FILTRADO, CSV_SEP

# --- Supuestos de deadhead / interlining (aprobados 28/09, sin cambios) ---
FACTOR_DESVIO = 1.3          # distancia real aprox. = euclidiana * FACTOR_DESVIO
VELOCIDAD_KMH = 20.0         # velocidad promedio de desplazamientos sin pasajeros
LAYOVER_MIN = 3.0            # tiempo minimo de maniobra entre actividades consecutivas
RADIO_INTERLINING_KM = 3.0   # radio maximo para permitir encadenar viajes de distinta ruta

# --- Condicion ciclica de bateria (docs/context/02_supuestos_y_decisiones.md, B6 y C3) ---
# El profesor pidio la condicion ciclica (inicio = fin); los 80-90% fueron un ejemplo suyo, no una
# exigencia. El NIVEL no se fija aqui: se busca con un barrido que parte del maximo de los datos
# (max_soc = 1.0 en parameters.csv) y baja mientras convenga; el nivel base lo elige el costo total
# (criterio y regla de termino en B6). En cada nivel, ese valor es el SOC de partida, de llegada y
# el TOPE de carga de todo bus.
# Energia utilizable entre cargas = battery_kwh * (nivel - min_soc): 315 kWh al 100%, 280 al 90%,
# 245 al 80%, 210 al 70%. Con inicio = fin se recarga TODO lo consumido, asi que el nivel no cambia
# la energia total a cargar: cambia cuantas jornadas necesitan recargar a mitad del dia.
SOC_CICLICO_BARRIDO = [1.0, 0.9, 0.8, 0.7]
# Grilla extendida del barrido de niveles (scripts/13-barrido_niveles.py): llega al piso fisico (50%), por debajo del cual
# ningun bus puede cubrir la expedicion mas exigente partiendo y volviendo a su electroterminal.
SOC_BARRIDO_EXTENDIDO = [1.0, 0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.5]

# --- Union de electroterminales (decision B9): Los Espinos (3) y Santa Rosa (5), a 1,11 km ---
# Se tratan como UN solo electroterminal (puestos sumados, un grupo de interlining). Los patios
# fisicos se mantienen para las distancias. depot_id como texto, igual que en depots.csv.
ELECTROTERMINALES_UNIDOS = ("3", "5")

# --- MILP de programacion de carga en instancia reducida (Etapa 4, scripts/11-milp_carga.py; docs/context/02, B12) ---
# El MILP resuelve el dia completo en un solo modelo; los bloques son solo la unidad con que se mide el tiempo
# (96 bloques de 15 min, igual que la cota LP de la Etapa 3).
BLOQUE_MILP_MIN = 15           # minutos por bloque
N_MILP = [30, 50, 100, 200, 400]   # escalera de tamanos de la instancia (buses tras la carga, aprox.); si no resuelve al 1% en el limite, se reporta tal cual
SEMILLA_MILP = 24              # semilla fija del muestreo de jornadas (el muestreo es anidado: 50 dentro de 200 dentro de 400)
TIEMPO_LIMITE_MILP_S = 600     # limite de resolucion por instancia
GAP_MILP = 0.01                # brecha de optimalidad pedida (1%)
UMBRAL_NO_TRIVIAL = 0.10       # la instancia debe tener los puestos saturados en al menos este % de los bloques
ESCENARIO_MILP = "E1"          # escenario cuyas jornadas y ventanas se muestrean (configuracion propuesta, nivel 100%)

# Consumo derivado de vehicles.csv / parameters.csv (350 kWh / 250 km).
CONSUMO_KWH_KM = 1.4

# Campos de data-filtrado/parameters.csv que SI se usan en el modelo.
# 'fleet_size' se excluye deliberadamente: el profesor confirmo que la
# flota es irrestricta (ver docs/context/00_contexto_entrega1.md seccion 3
# y docs/context/02_supuestos_y_decisiones.md, A9).
_CAMPOS_USADOS = {
    "battery_kwh", "range_km", "charge_power_kw", "min_soc", "max_soc",
    "cost_per_km", "waiting_cost_per_min", "vehicle_fixed_cost",
    "fixed_charge_cost",
}
_CAMPOS_IGNORADOS_CONOCIDOS = {"fleet_size"}


@dataclass(frozen=True)
class Costos:
    battery_kwh: float
    range_km: float
    charge_power_kw: float
    min_soc: float
    max_soc: float
    cost_per_km: float
    waiting_cost_per_min: float
    vehicle_fixed_cost: float
    fixed_charge_cost: float

    @property
    def bateria_util_kwh(self) -> float:
        """Bateria utilizable entre min_soc y max_soc (315 kWh); equivale a
        bateria_util_ciclica_kwh(max_soc). El codigo nuevo debe usar bateria_util_ciclica_kwh con
        el nivel que corresponda."""
        return self.battery_kwh * (self.max_soc - self.min_soc)

    def bateria_util_ciclica_kwh(self, soc: float) -> float:
        """Energia utilizable entre cargas cuando el bus parte, termina y se topa en `soc`
        (315 kWh al 100%, 280 al 90%, 245 al 80%, 210 al 70%)."""
        return self.battery_kwh * (soc - self.min_soc)


def cargar_costos(path=None) -> Costos:
    """Lee data-filtrado/parameters.csv y devuelve los costos como objeto
    tipado. Advierte explicitamente si aparece 'fleet_size' (para recordar
    por que se ignora) o si aparece algun campo nuevo no contemplado.
    """
    path = path or (DATA_FILTRADO / "parameters.csv")
    df = pd.read_csv(path, sep=CSV_SEP)
    valores = dict(zip(df["parameter"], df["value"].astype(float)))

    if "fleet_size" in valores:
        print(f"  [parametros] Aviso: 'fleet_size'={valores['fleet_size']:.0f} presente en "
              f"{path.name} pero SE IGNORA: el profesor confirmo flota irrestricta "
              f"(ver docs/context/02_supuestos_y_decisiones.md, A9).")

    desconocidos = set(valores) - _CAMPOS_USADOS - _CAMPOS_IGNORADOS_CONOCIDOS
    if desconocidos:
        print(f"  [parametros] Aviso: campo(s) nuevo(s) en {path.name} no contemplados "
              f"todavia en Costos: {sorted(desconocidos)}. Revisar si deben incorporarse.")

    faltantes = _CAMPOS_USADOS - set(valores)
    if faltantes:
        raise ValueError(f"Faltan campos requeridos en {path.name}: {sorted(faltantes)}")

    return Costos(**{campo: valores[campo] for campo in _CAMPOS_USADOS})
