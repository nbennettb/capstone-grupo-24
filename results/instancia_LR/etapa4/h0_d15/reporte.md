# Etapa 4 - Programacion de la carga, La Reina (holgura 0 min, largo del bloque 15 min, 100 puestos)

- Ventanas: 1,640; energia a reponer 343.3 MWh = 79.5% de la capacidad de 24 h.

## Propuesta con carga por orden de llegada vs Propuesta completa (modelo agregado)

|                             |    Propuesta con carga por orden de llegada |         Propuesta completa (modelo agregado) |
|:----------------------------|-----------:|-----------:|
| reservas_diurnas        |    30      |     0      |
| reservas_nocturnas          |   442      |   218      |
| costo_energia_usd           | 47004.7    | 46405.5    |
| costo_medio_energia_usd_kwh |     0.1369 |     0.1352 |
| pct_energia_valle           |    52.06   |    52.43   |
| eventos                     |  1640      |  5866      |
| kwh_deficit                 |     0      |     0      |
| uso_maximo_pct              |   100      |   125.2    |
| minutos_saturados           |   907      |   920      |
| minutos_sobre_puestos       |     0      |   124      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha | fuente_brecha   |   segundos |   variables |   binarias |   restricciones |   desempate_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|:----------------|-----------:|------------:|-----------:|----------------:|----------------:|
|             0 |          15 | Propuesta con carga por orden de llegada                 | heuristica (sin optimizacion) |         165005 |        nan | nan        | -               |       1.06 |         nan |        nan |             nan |        nan      |
|             0 |          15 | Propuesta completa (modelo agregado) agregado - LP (cota) | optimo                        |         100129 |     100129 |   0        | Gurobi          |       8.28 |      163962 |          0 |            3376 |        nan      |
|             0 |          15 | Propuesta completa (modelo agregado) agregado - MILP      | optimo (brecha pedida)        |         100905 |     100591 |   0.003172 | Gurobi          |      89.4  |      163962 |       1640 |            3376 |          5.9113 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|
| P1        | 00-08   |              0.1 |   142986   |          14298.6 | 144000   |        14400   |
| P2        | 08-14   |              0.2 |    99142   |          14871.3 |  97624.7 |        14643.7 |
| P3        | 14-17   |              0.2 |     8980.4 |           1975.7 |    848.3 |          186.6 |
| P4        | 17-19   |              0.2 |     6975.3 |           1046.3 |  14910.3 |         2236.6 |
| P5        | 19-22   |              0.2 |    49459.7 |          10881.1 |  49902.8 |        10978.6 |
| P6        | 22-24   |              0.1 |    35743   |           3931.7 |  36000   |         3960   |

## Validaciones (todas pasaron)
- orden de llegada: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- Propuesta completa (modelo agregado): energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; Propuesta completa (modelo agregado) <= Propuesta con carga por orden de llegada en la grilla.
- Realizacion por minuto de Propuesta completa (modelo agregado): 124 minutos sobre los puestos (maximo 125.18); es el error del agregado en los bloques de borde.

## Tiempo y memoria
- orden de llegada 1.1 s | armado 1.8 s | LP 8.3 s | MILP 89.4 s (1 nodos) | realizacion por minuto 5.1 s | total 3727.0 s | pico de memoria 1,489 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (orden de llegada exacta; Propuesta completa (modelo agregado) = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).