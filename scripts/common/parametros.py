"""Unica fuente de verdad de los supuestos y costos usados en las Etapas
0-4 y en el caso base (docs/context/01_como_funciona.md); cada valor esta
justificado en docs/context/02_decisiones.md.

Para correr un analisis de sensibilidad, cambiar los valores de aqui (o
pasarlos como override a las funciones de los scripts de cada etapa) en vez
de hardcodearlos de nuevo en cada script.
"""

from dataclasses import dataclass

import pandas as pd

from .rutas import DATA_FILTRADO, CSV_SEP

# --- Supuestos de deadhead / interlining ---
FACTOR_DESVIO = 1.3          # distancia real aprox. = euclidiana * FACTOR_DESVIO
VELOCIDAD_KMH = 20.0         # velocidad promedio de desplazamientos sin pasajeros
LAYOVER_MIN = 3.0            # tiempo minimo de maniobra entre actividades consecutivas
RADIO_INTERLINING_KM = 3.0   # radio maximo para permitir encadenar viajes de distinta ruta

# --- Condicion ciclica de bateria (docs/context/02_decisiones.md) ---
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

# --- Instancia reducida: un electroterminal completo (docs/context/02_decisiones.md) ---
# Tras la Etapa 1 cada electroterminal es un subproblema independiente (sus rutas, sus buses, sus puestos).
# depot_id como texto, igual que en depots.csv. "4" = La Reina. Todos los scripts lo aceptan con --terminal.
TERMINAL_INSTANCIA = "4"

# --- Etapa 3: cortes por bateria y re-encadenamiento por el patio (scripts/12-etapa3_cortes_reencadenamiento.py) ---
# Regla de corte de cada jornada: minimos tramos y, a igualdad, minimos km extra (vuelta al patio + nueva salida
# - conexion que se ahorra).
REGLA_CORTE = "min_tramos_km"
# Holgura h (min) que se suma al tiempo de recarga antes de que el bus pueda tomar otro tramo. La primera es la base;
# las otras son la sensibilidad (mas holgura: mas buses y menos reservas).
HOLGURAS_RECARGA_MIN = [0, 30, 60]

# --- Etapa 4: programacion de la carga (scripts/13-etapa4_programacion_carga.py) ---
DELTA_MIN = 15                   # largo del bloque (min); las tarifas cambian en horas exactas
DELTAS_SENSIBILIDAD = [5, 15, 30]
TIEMPO_LIMITE_S = {"agregado": 600, "detallado": 900}
GAP_MIP = 0.005                  # brecha de optimalidad pedida (0,5% del objetivo de la Etapa 4)
# Penalizacion por kWh no repuesto (M del deficit). Muy por sobre el costo de una reserva (250 USD), para que el
# deficit solo aparezca si la energia no cabe en los puestos en 24 h.
PENALIZACION_DEFICIT_USD_KWH = 10_000.0
# Desempate del modelo agregado: a igual tarifa hay muchos programas optimos y el solver puede repartir la carga en
# bloques sueltos (mas eventos de carga, que el modelo no ve). Se suma este costo por kWh y por bloque transcurrido desde
# la llegada: a igual tarifa, carga lo antes posible y de corrido. Maximo 96 x 1e-6 = 1e-4 USD/kWh, cien veces menos que
# la menor diferencia de tarifas (0,01 USD/kWh), asi que nunca cambia en que periodo se carga. 0 lo apaga.
DESEMPATE_USD_KWH_BLOQUE = 1e-6

# Consumo derivado de vehicles.csv / parameters.csv (350 kWh / 250 km).
CONSUMO_KWH_KM = 1.4

# Campos de data-filtrado/parameters.csv que SI se usan en el modelo.
# 'fleet_size' se excluye deliberadamente: el profesor confirmo que la
# flota es irrestricta (ver docs/context/00_contexto_entrega1.md seccion 3
# y docs/context/02_decisiones.md).
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
              f"(ver docs/context/02_decisiones.md).")

    desconocidos = set(valores) - _CAMPOS_USADOS - _CAMPOS_IGNORADOS_CONOCIDOS
    if desconocidos:
        print(f"  [parametros] Aviso: campo(s) nuevo(s) en {path.name} no contemplados "
              f"todavia en Costos: {sorted(desconocidos)}. Revisar si deben incorporarse.")

    faltantes = _CAMPOS_USADOS - set(valores)
    if faltantes:
        raise ValueError(f"Faltan campos requeridos en {path.name}: {sorted(faltantes)}")

    return Costos(**{campo: valores[campo] for campo in _CAMPOS_USADOS})
