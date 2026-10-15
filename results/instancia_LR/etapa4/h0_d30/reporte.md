# Etapa 4 - Programacion de la carga, La Reina (holgura 0 min, Delta 30 min, 100 puestos)

- Ventanas: 1,640; energia a reponer 343.3 MWh = 79.5% de la capacidad de 24 h.

## E2-FIFO vs E2

|                             |    E2-FIFO |         E2 |   E2-detallado |
|:----------------------------|-----------:|-----------:|---------------:|
| reservas_intermedias        |    30      |     0      |         0      |
| reservas_nocturnas          |   442      |   217      |       220      |
| costo_energia_usd           | 47004.7    | 46424      |     46439.8    |
| costo_medio_energia_usd_kwh |     0.1369 |     0.1352 |         0.1353 |
| pct_energia_valle           |    52.06   |    52.43   |        52.43   |
| eventos                     |  1640      |  3782      |      1653      |
| kwh_deficit                 |     0      |     0      |         0      |
| uso_maximo_pct              |   100      |   150.9    |       128.7    |
| minutos_saturados           |   907      |   886      |       983      |
| minutos_sobre_puestos       |     0      |   155      |        46      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha |   segundos |   variables |   binarias |   restricciones |   desempate_usd |   eventos_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|-----------:|------------:|-----------:|----------------:|----------------:|--------------:|
|             0 |          30 | E2-FIFO                 | heuristica (sin optimizacion) |       165005   |      nan   | nan        |       0.29 |         nan |        nan |             nan |        nan      |           nan |
|             0 |          30 | E2 agregado - LP (cota) | optimo                        |        99854.6 |    99854.6 |   0        |       1.65 |       85242 |          0 |            3328 |        nan      |           nan |
|             0 |          30 | E2 agregado - MILP      | optimo (brecha pedida)        |       100674   |   100238   |   0.004362 |       8.19 |       85242 |       1640 |            3328 |          2.946  |           nan |
|             0 |          30 | E2 detallado - MILP     | limite de tiempo              |       109705   |   105583   |   0.037598 |     900.37 |      245962 |      82000 |          242730 |          2.9513 |          8265 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |   kwh_e2_detallado |   costo_e2_detallado_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|-------------------:|-------------------------:|
| P1        | 00-08   |              0.1 |   142986   |          14298.6 | 144000   |        14400   |           144000   |                  14400   |
| P2        | 08-14   |              0.2 |    99142   |          14871.3 |  97360   |        14604   |            96827.3 |                  14524.1 |
| P3        | 14-17   |              0.2 |     8980.4 |           1975.7 |    848.3 |          186.6 |             1035.8 |                    227.9 |
| P4        | 17-19   |              0.2 |     6975.3 |           1046.3 |  14910.3 |         2236.6 |            15217.8 |                   2282.7 |
| P5        | 19-22   |              0.2 |    49459.7 |          10881.1 |  50167.5 |        11036.8 |            50205.2 |                  11045.1 |
| P6        | 22-24   |              0.1 |    35743   |           3931.7 |  36000   |         3960   |            36000   |                   3960   |

## Validaciones (todas pasaron)
- FIFO: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- E2: energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; E2 <= E2-FIFO en la grilla.
- Realizacion por minuto de E2: 155 minutos sobre los puestos (maximo 150.93); es el error del agregado en los bloques de borde.

## Modelo detallado vs agregado

- Detallado: limite de tiempo, brecha 3.760%, 900.4 s, 82,000 binarias. Objetivo 109,704.78 USD = energia + reservas 101,439.78 + eventos 8,265.00.
- Agregado: energia + reservas 100,674.02 USD; con sus eventos contados despues: 119,584.02 USD.
- Realizacion por minuto del detallado: 46 minutos sobre los puestos (maximo 128.66).

## Tiempo y memoria
- FIFO 0.3 s | armado 0.2 s | LP 1.6 s | MILP 8.2 s (1 nodos) | realizacion por minuto 1.2 s | total 919.2 s | pico de memoria 1,168 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (FIFO exacta; E2 = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).