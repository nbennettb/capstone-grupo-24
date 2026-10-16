# Etapa 4 - Programacion de la carga, La Reina (holgura 0 min, Delta 15 min, 100 puestos)

- Ventanas: 1,640; energia a reponer 343.3 MWh = 79.5% de la capacidad de 24 h.

## E2-FIFO vs E2

|                             |    E2-FIFO |         E2 |   E2-detallado |
|:----------------------------|-----------:|-----------:|---------------:|
| reservas_intermedias        |    30      |     0      |        30      |
| reservas_nocturnas          |   442      |   218      |       442      |
| costo_energia_usd           | 47004.7    | 46405.5    |     47004.7    |
| costo_medio_energia_usd_kwh |     0.1369 |     0.1352 |         0.1369 |
| pct_energia_valle           |    52.06   |    52.43   |        52.06   |
| eventos                     |  1640      |  5866      |      1640      |
| kwh_deficit                 |     0      |     0      |         0      |
| uso_maximo_pct              |   100      |   125.2    |       100      |
| minutos_saturados           |   907      |   920      |       621      |
| minutos_sobre_puestos       |     0      |   124      |         0      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha | fuente_brecha                                         |   segundos |   variables |   binarias |   restricciones |   desempate_usd |   cota_gurobi_usd |   brecha_gurobi |   cota_valida_usd |   eventos_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|:------------------------------------------------------|-----------:|------------:|-----------:|----------------:|----------------:|------------------:|----------------:|------------------:|--------------:|
|             0 |          15 | E2-FIFO                 | heuristica (sin optimizacion) |         165005 |        nan | nan        | -                                                     |       1.06 |         nan |        nan |             nan |        nan      |               nan |             nan |               nan |           nan |
|             0 |          15 | E2 agregado - LP (cota) | optimo                        |         100129 |     100129 |   0        | Gurobi                                                |       8.28 |      163962 |          0 |            3376 |        nan      |               nan |             nan |               nan |           nan |
|             0 |          15 | E2 agregado - MILP      | optimo (brecha pedida)        |         100905 |     100591 |   0.003172 | Gurobi                                                |      89.4  |      163962 |       1640 |            3376 |          5.9113 |               nan |             nan |               nan |           nan |
|             0 |          15 | E2 detallado - MILP     | limite de tiempo              |         173205 |     108329 |   0.374583 | cota valida (LP del agregado + un evento por ventana) |    3600.9  |      482122 |     160720 |          478938 |          5.9603 |              -inf |             inf |            108329 |          8200 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |   kwh_e2_detallado |   costo_e2_detallado_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|-------------------:|-------------------------:|
| P1        | 00-08   |              0.1 |   142986   |          14298.6 | 144000   |        14400   |           142986   |                  14298.6 |
| P2        | 08-14   |              0.2 |    99142   |          14871.3 |  97624.7 |        14643.7 |            99142   |                  14871.3 |
| P3        | 14-17   |              0.2 |     8980.4 |           1975.7 |    848.3 |          186.6 |             8980.4 |                   1975.7 |
| P4        | 17-19   |              0.2 |     6975.3 |           1046.3 |  14910.3 |         2236.6 |             6975.3 |                   1046.3 |
| P5        | 19-22   |              0.2 |    49459.7 |          10881.1 |  49902.8 |        10978.6 |            49459.7 |                  10881.1 |
| P6        | 22-24   |              0.1 |    35743   |           3931.7 |  36000   |         3960   |            35743   |                   3931.7 |

## Validaciones (todas pasaron)
- FIFO: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- E2: energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; E2 <= E2-FIFO en la grilla.
- Realizacion por minuto de E2: 124 minutos sobre los puestos (maximo 125.18); es el error del agregado en los bloques de borde.

## Modelo detallado vs agregado

- Detallado: limite de tiempo, brecha 37.458% (cota valida (LP del agregado + un evento por ventana)), 3600.9 s, 160,720 binarias. Objetivo 173,204.72 USD = energia + reservas 165,004.72 + eventos 8,200.00.
- Agregado: energia + reservas 100,905.49 USD; con sus eventos contados despues: 130,235.49 USD.
- Realizacion por minuto del detallado: 0 minutos sobre los puestos (maximo 100.00).

## Tiempo y memoria
- FIFO 1.1 s | armado 1.8 s | LP 8.3 s | MILP 89.4 s (1 nodos) | realizacion por minuto 5.1 s | total 3727.0 s | pico de memoria 1,489 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (FIFO exacta; E2 = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).