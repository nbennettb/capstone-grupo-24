# Etapa 4 - Programacion de la carga, Vespucio Norte (holgura de recarga 0 min, largo del bloque 15 min, 150 puestos)

- Ventanas: 1,038; energia a reponer 221.7 MWh = 34.2% de la capacidad de 24 h.

## Propuesta con carga por orden de llegada vs Propuesta completa (modelo relajado)

|                             |    Propuesta con carga por orden de llegada |         Propuesta completa (modelo relajado) |
|:----------------------------|-----------:|-----------:|
| reservas_diurnas        |     0      |     0      |
| reservas_nocturnas          |    33      |    29      |
| costo_energia_usd           | 30663.9    | 24270.5    |
| costo_medio_energia_usd_kwh |     0.1383 |     0.1095 |
| pct_energia_valle           |    64.49   |    85.45   |
| eventos                     |  1038      |  3343      |
| kwh_deficit                 |     0      |     0      |
| uso_maximo_pct              |   100      |   112.9    |
| minutos_saturados           |   331      |   374      |
| minutos_sobre_puestos       |     0      |    24      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |   brecha | fuente_brecha   |   segundos |   variables |   binarias |   restricciones |   desempate_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|---------:|:----------------|-----------:|------------:|-----------:|----------------:|----------------:|
|             0 |          15 | Propuesta con carga por orden de llegada                 | heuristica (sin optimizacion) |        38913.9 |      nan   |      nan | -               |       0.16 |         nan |        nan |             nan |         nan     |
|             0 |          15 | Propuesta completa (modelo relajado) agregado - LP (cota) | optimo                        |        30958.8 |    30958.8 |        0 | Gurobi          |       0.88 |      103777 |          0 |            2172 |         nan     |
|             0 |          15 | Propuesta completa (modelo relajado) agregado - MILP      | optimo (brecha pedida)        |        31520.5 |    31524.3 |        0 | Gurobi          |       2.11 |      103777 |       1038 |            2172 |           3.788 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|
| P1        | 00-08   |              0.1 |    89322.9 |           8932.3 | 187048   |        18704.9 |
| P2        | 08-14   |              0.2 |    17774.6 |           2666.2 |  17774.9 |         2666.2 |
| P3        | 14-17   |              0.2 |     4368.4 |            961   |     26.5 |            5.8 |
| P4        | 17-19   |              0.2 |     3518.2 |            527.7 |   7871.4 |         1180.7 |
| P5        | 19-22   |              0.2 |    53061.7 |          11673.6 |   6583.1 |         1448.3 |
| P6        | 22-24   |              0.1 |    53664.1 |           5903.1 |   2405.4 |          264.6 |

## Validaciones (todas pasaron)
- orden de llegada: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- Propuesta completa (modelo relajado): energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; Propuesta completa (modelo relajado) <= Propuesta con carga por orden de llegada en la grilla.
- Realizacion por minuto de Propuesta completa (modelo relajado): 24 minutos sobre los puestos (maximo 169.35); es el error del agregado en los bloques de borde.

## Tiempo y memoria
- orden de llegada 0.2 s | armado 0.4 s | LP 0.9 s | MILP 2.1 s (1 nodos) | realizacion por minuto 0.8 s | total 5.5 s | pico de memoria 529 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (orden de llegada exacta; Propuesta completa (modelo relajado) = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).