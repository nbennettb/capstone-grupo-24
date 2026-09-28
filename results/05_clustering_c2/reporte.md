# Reporte Etapa 1 - Clustering C2 (MILP con capacidad)

Corrida: RED COMPLETA (417 rutas)
theta (holgura de capacidad): 1.0 | horas disponibles/dia: 24.0

## Uso de capacidad por electroterminal (horas-cargador/dia)

|                 |   h_r_asignadas |   capacidad |   uso_pct |
|:----------------|----------------:|------------:|----------:|
| Vespucio Norte  |          1397.1 |        3600 |      38.8 |
| El Conquistador |          3236.1 |        4320 |      74.9 |
| Los Espinos     |          2866.7 |        2880 |      99.5 |
| La Reina        |          1591.4 |        2400 |      66.3 |
| Santa Rosa      |          2984.9 |        3600 |      82.9 |

## Comparacion contra C1 (heuristica del mas cercano)

De 417 rutas en comun, 8 (1.9%) quedan en un electroterminal distinto entre C1 y C2.

## Grafico
- `uso_capacidad.png`: carga asignada vs. capacidad por electroterminal.

*(Generado automaticamente por scripts/5-clustering_milp.py)*