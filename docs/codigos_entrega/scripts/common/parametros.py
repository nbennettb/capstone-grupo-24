"""Supuestos y costos de todos los scripts (Etapas 0-4 y caso base). Para una sensibilidad se cambia el valor aqui."""

from dataclasses import dataclass

import pandas as pd

from .rutas import DATA_FILTRADO, CSV_SEP

# --- Supuestos de deadhead / interlining ---
FACTOR_DESVIO = 1.3          # distancia real aprox. = euclidiana * FACTOR_DESVIO
VELOCIDAD_KMH = 20.0         # velocidad promedio de desplazamientos sin pasajeros
LAYOVER_MIN = 3.0            # tiempo minimo de maniobra entre actividades consecutivas
RADIO_INTERLINING_KM = 3.0   # radio maximo para permitir encadenar viajes de distinta ruta

# --- Condicion ciclica de bateria ---
# Todo bus parte, termina y se topa de carga en el mismo nivel. Energia utilizable entre cargas =
# battery_kwh * (nivel - min_soc): 315 kWh al 100%, 280 al 90%, 245 al 80%, 210 al 70%.
SOC_CICLICO_BARRIDO = [1.0, 0.9, 0.8, 0.7]
# Niveles del barrido (50% es el piso fisico: con menos, una expedicion no se puede hacer partiendo y volviendo al patio)
SOC_BARRIDO_EXTENDIDO = [1.0, 0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.5]

# --- Los Espinos (3) y Santa Rosa (5), a 1,11 km, se tratan como UN electroterminal (puestos sumados) ---
ELECTROTERMINALES_UNIDOS = ("3", "5")

# --- Instancia reducida: un electroterminal completo (depot_id como texto; "4" = La Reina). Opcion --terminal ---
TERMINAL_INSTANCIA = "4"

# --- Etapa 3 ---
# Regla de corte de cada jornada: minimos tramos y, a igualdad, minimos km extra.
REGLA_CORTE = "min_tramos_km"
# Holgura (min) que se suma al tiempo de recarga antes de que el bus tome otro tramo; la primera es la base.
HOLGURAS_RECARGA_MIN = [0, 30, 60]

# --- Etapa 4 ---
DELTA_MIN = 15                   # largo del bloque (min); las tarifas cambian en horas exactas
DELTAS_SENSIBILIDAD = [5, 15, 30]
# Limites de tiempo (s). El detallado se resuelve en dos fases dentro del total.
TIEMPO_LIMITE_S = {"agregado": 600, "detallado": 3600, "detallado_fase1": 1500}
GAP_MIP = 0.005                  # brecha de optimalidad pedida (0,5% del objetivo de la Etapa 4)
GAP_DETALLADO_FASE1 = 0.01       # la fase 1 solo construye el punto de partida de la fase 2
# Penalizacion por kWh no repuesto: muy sobre el costo de una reserva, para que el deficit solo aparezca si la energia no cabe.
PENALIZACION_DEFICIT_USD_KWH = 10_000.0
# Desempate del agregado: a igual tarifa carga lo antes posible y de corrido (maximo 1e-4 USD/kWh: nunca cambia el periodo
# en que se carga). 0 lo apaga.
DESEMPATE_USD_KWH_BLOQUE = 1e-6

# Consumo derivado de vehicles.csv / parameters.csv (350 kWh / 250 km).
CONSUMO_KWH_KM = 1.4

# Campos de parameters.csv que se usan ('fleet_size' se ignora: la flota es irrestricta).
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
        """Bateria utilizable entre min_soc y max_soc (315 kWh)."""
        return self.battery_kwh * (self.max_soc - self.min_soc)

    def bateria_util_ciclica_kwh(self, soc: float) -> float:
        """Energia utilizable entre cargas cuando el bus parte, termina y se topa en `soc`
        (315 kWh al 100%, 280 al 90%, 245 al 80%, 210 al 70%)."""
        return self.battery_kwh * (soc - self.min_soc)


def cargar_costos(path=None) -> Costos:
    """Lee parameters.csv (datos filtrados) y devuelve los costos como objeto tipado."""
    path = path or (DATA_FILTRADO / "parameters.csv")
    df = pd.read_csv(path, sep=CSV_SEP)
    valores = dict(zip(df["parameter"], df["value"].astype(float)))

    if "fleet_size" in valores:
        print(f"  [parametros] Aviso: 'fleet_size'={valores['fleet_size']:.0f} presente en {path.name} pero se ignora "
              "(flota irrestricta).")

    desconocidos = set(valores) - _CAMPOS_USADOS - _CAMPOS_IGNORADOS_CONOCIDOS
    if desconocidos:
        print(f"  [parametros] Aviso: campo(s) nuevo(s) en {path.name} no contemplados "
              f"todavia en Costos: {sorted(desconocidos)}. Revisar si deben incorporarse.")

    faltantes = _CAMPOS_USADOS - set(valores)
    if faltantes:
        raise ValueError(f"Faltan campos requeridos en {path.name}: {sorted(faltantes)}")

    return Costos(**{campo: valores[campo] for campo in _CAMPOS_USADOS})
