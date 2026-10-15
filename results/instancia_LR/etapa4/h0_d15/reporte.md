# Etapa 4 - Programacion de la carga, La Reina (holgura 0 min, Delta 15 min, 100 puestos)

- Ventanas: 1,640; energia a reponer 343.3 MWh = 79.5% de la capacidad de 24 h.

## E2-FIFO vs E2

|                             |    E2-FIFO |         E2 |   E2-detallado |
|:----------------------------|-----------:|-----------:|---------------:|
| reservas_intermedias        |    30      |     0      |         0      |
| reservas_nocturnas          |   442      |   218      |       322      |
| costo_energia_usd           | 47004.7    | 46405.8    |     46426.9    |
| costo_medio_energia_usd_kwh |     0.1369 |     0.1352 |         0.1352 |
| pct_energia_valle           |    52.06   |    52.43   |        52.43   |
| eventos                     |  1640      |  5894      |      1687      |
| kwh_deficit                 |     0      |     0      |         0      |
| uso_maximo_pct              |   100      |   126.2    |       110.5    |
| minutos_saturados           |   907      |   916      |      1005      |
| minutos_sobre_puestos       |     0      |   138      |        23      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha |   segundos |   variables |   binarias |   restricciones |   desempate_usd |   eventos_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|-----------:|------------:|-----------:|----------------:|----------------:|--------------:|
|             0 |          15 | E2-FIFO                 | heuristica (sin optimizacion) |         165005 |        nan | nan        |       0.31 |         nan |        nan |             nan |        nan      |           nan |
|             0 |          15 | E2 agregado - LP (cota) | optimo                        |         100129 |     100129 |   0        |       4.04 |      163962 |          0 |            3376 |        nan      |           nan |
|             0 |          15 | E2 agregado - MILP      | optimo (brecha pedida)        |         100906 |     100591 |   0.003176 |      29.12 |      163962 |       1640 |            3376 |          5.9109 |           nan |
|             0 |          15 | E2 detallado - MILP     | limite de tiempo              |         135342 |     105183 |   0.222871 |     900.33 |      482122 |     160720 |          478938 |          5.9215 |          8415 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |   kwh_e2_detallado |   costo_e2_detallado_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|-------------------:|-------------------------:|
| P1        | 00-08   |              0.1 |   142986   |          14298.6 | 144000   |        14400   |           144000   |                  14400   |
| P2        | 08-14   |              0.2 |    99142   |          14871.3 |  97619.5 |        14642.9 |            97381.5 |                  14607.2 |
| P3        | 14-17   |              0.2 |     8980.4 |           1975.7 |    848.3 |          186.6 |             1167.8 |                    256.9 |
| P4        | 17-19   |              0.2 |     6975.3 |           1046.3 |  14910.3 |         2236.6 |            14848.1 |                   2227.2 |
| P5        | 19-22   |              0.2 |    49459.7 |          10881.1 |  49907.9 |        10979.7 |            49888.6 |                  10975.5 |
| P6        | 22-24   |              0.1 |    35743   |           3931.7 |  36000   |         3960   |            36000   |                   3960   |

## Validaciones (todas pasaron)
- FIFO: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- E2: energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; E2 <= E2-FIFO en la grilla.
- Realizacion por minuto de E2: 138 minutos sobre los puestos (maximo 126.21); es el error del agregado en los bloques de borde.

## Modelo detallado vs agregado

- Detallado: limite de tiempo, brecha 22.287%, 900.3 s, 160,720 binarias. Objetivo 135,341.86 USD = energia + reservas 126,926.86 + eventos 8,415.00.
- Agregado: energia + reservas 100,905.85 USD; con sus eventos contados despues: 130,375.85 USD.
- Realizacion por minuto del detallado: 23 minutos sobre los puestos (maximo 110.47).

## Tiempo y memoria
- FIFO 0.3 s | armado 0.5 s | LP 4.0 s | MILP 29.1 s (1 nodos) | realizacion por minuto 1.3 s | total 945.3 s | pico de memoria 2,118 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (FIFO exacta; E2 = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).