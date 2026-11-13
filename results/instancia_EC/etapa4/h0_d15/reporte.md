# Etapa 4 - Programacion de la carga, El Conquistador (holgura de recarga 0 min, largo del bloque 15 min, 180 puestos)

- Ventanas: 3,003; energia a reponer 636.7 MWh = 81.9% de la capacidad de 24 h.

## Propuesta con carga por orden de llegada vs Propuesta completa (modelo relajado)

|                             |    Propuesta con carga por orden de llegada |         Propuesta completa (modelo relajado) |
|:----------------------------|-----------:|-----------:|
| reservas_diurnas        |     0      |     2      |
| reservas_nocturnas          |   951      |   492      |
| costo_energia_usd           | 87892.8    | 86487.9    |
| costo_medio_energia_usd_kwh |     0.1381 |     0.1358 |
| pct_energia_valle           |    50.55   |    50.89   |
| eventos                     |  3003      | 10863      |
| kwh_deficit                 |     0      |     0      |
| uso_maximo_pct              |   100      |   120.9    |
| minutos_saturados           |   977      |   998      |
| minutos_sobre_puestos       |     0      |    95      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha | fuente_brecha   |   segundos |   variables |   binarias |   restricciones |   desempate_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|:----------------|-----------:|------------:|-----------:|----------------:|----------------:|
|             0 |          15 | Propuesta con carga por orden de llegada                 | heuristica (sin optimizacion) |         325643 |        nan | nan        | -               |       0.71 |         nan |        nan |             nan |        nan      |
|             0 |          15 | Propuesta completa (modelo relajado) agregado - LP (cota) | optimo                        |         208548 |     208548 |   0        | Gurobi          |       5.82 |      300229 |          0 |            6102 |        nan      |
|             0 |          15 | Propuesta completa (modelo relajado) agregado - MILP      | optimo (brecha pedida)        |         209988 |     209361 |   0.003044 | Gurobi          |      37.62 |      300229 |       3003 |            6102 |         12.4595 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|
| P1        | 00-08   |              0.1 |   257453   |          25745.3 | 259200   |        25920   |
| P2        | 08-14   |              0.2 |   191431   |          28714.7 | 194400   |        29160   |
| P3        | 14-17   |              0.2 |    27208.4 |           5985.8 |   7903.1 |         1738.7 |
| P4        | 17-19   |              0.2 |    11344.8 |           1701.7 |  24799.2 |         3719.9 |
| P5        | 19-22   |              0.2 |    84831.2 |          18662.9 |  85551.7 |        18821.4 |
| P6        | 22-24   |              0.1 |    64385.1 |           7082.4 |  64800   |         7128   |

## Validaciones (todas pasaron)
- orden de llegada: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- Propuesta completa (modelo relajado): energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; Propuesta completa (modelo relajado) <= Propuesta con carga por orden de llegada en la grilla.
- Realizacion por minuto de Propuesta completa (modelo relajado): 95 minutos sobre los puestos (maximo 217.65); es el error del agregado en los bloques de borde.

## Tiempo y memoria
- orden de llegada 0.7 s | armado 1.2 s | LP 5.8 s | MILP 37.6 s (1 nodos) | realizacion por minuto 1.3 s | total 49.4 s | pico de memoria 1,022 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (orden de llegada exacta; Propuesta completa (modelo relajado) = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).