"""Unica fuente de verdad de los supuestos y costos usados en las Etapas
0-4, tal como quedaron aprobados en la reunion del 28/09/2026 (ver
docs/context/01_metodologia.md seccion 4 y
docs/Propuesta_metodologia_reunion.md seccion 6).

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

# --- Supuesto de bateria (el mas critico, ver docs/context/02_supuestos_y_decisiones.md B6) ---
# OBSOLETO: SOC_INICIAL = 1.0 (bateria llena al comenzar el dia, sin recuperarla al terminar).
# El profesor lo rechazo: con ese supuesto el modelo no paga ~93% de la energia que los buses
# consumen y los 700 puestos de carga casi no se usan (~5%). Nada vigente debe depender de el.
#
# VIGENTE (pendiente de implementar, Bloque A de docs/context/05_plan_entrega2.md):
#   SOC_CICLICO = 0.9              # nivel de partida, de llegada Y tope de carga (ciclo diario)
#   SOC_CICLICO_SENSIBILIDAD = 0.8
# Todo bus empieza y termina el dia con SOC_CICLICO. Energia utilizable entre cargas =
# battery_kwh * (SOC_CICLICO - min_soc) = 280 kWh al 90% (245 kWh al 80%), no los 315 kWh de
# `Costos.bateria_util_kwh`, que corresponden a una carga fisica del 100%. Con inicio = fin se recarga
# TODO lo consumido, asi que el nivel (80% vs 90%) no cambia la energia total a cargar: cambia cuantas
# jornadas necesitan recargar a mitad del dia.
SOC_INICIAL = 1.0            # OBSOLETO, ver arriba. Se elimina al implementar el Bloque A.

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
        """Bateria realmente utilizable entre min_soc y max_soc."""
        return self.battery_kwh * (self.max_soc - self.min_soc)


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
