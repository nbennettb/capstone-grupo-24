# Resumen para analisis: instancia La Reina

Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de `results/instancia_LR/`. Escenarios: **E0** caso base (VSP por linea + carga reactiva); **E1** segundo caso base (con interlining); **E2-FIFO** propuesta con carga por orden de llegada (Etapa 3 + FIFO); **E2** propuesta completa (Etapa 3 + Etapa 4). Cada escalon cambia una sola cosa.

## 1. Instancia y parametros

- Electroterminal **La Reina** completo: 100 puestos de carga, jornadas del VSP: E0 1,333, E1 1,203; 1,203 jornadas E1 de entrada a la Etapa 3.
- Energia a reponer (E2) / capacidad de 24 h de los puestos: 79.5%.
- Bateria util entre cargas 315 kWh (ciclo al 100%, minimo 10%); carga a 180 kW; consumo 1.4 kWh/km.
- Costos: bus 250 USD/dia (igual para una reserva), km vacio 0.5 USD, espera 0.03 USD/min, evento de carga 5 USD.
- Tarifa (USD/kWh): P1 00-08 h = 0.10, P2 08-14 h = 0.15, P3 14-17 h = 0.22, P4 17-19 h = 0.15, P5 19-22 h = 0.22, P6 22-24 h = 0.11.
- Deadhead: euclidiana x 1.3 a 20 km/h; layover 3 min.
- Etapa 3: regla de corte min_tramos_km (minimos tramos, luego minimos km extra); holgura base h = 0 min; sensibilidad [0, 30, 60].
- Etapa 4: bloques de Delta = 15 min (sensibilidad [5, 15, 30]); Gurobi, brecha 0.5%, limite 600 s; deficit penalizado con 10,000 USD/kWh; desempate 1e-06 USD/kWh por bloque desde la llegada.

## 2. Validaciones (re-verificadas desde los CSV)

| validacion                                                                     | resultado   | detalle                                                                                                         |
|:-------------------------------------------------------------------------------|:------------|:----------------------------------------------------------------------------------------------------------------|
| Caso base E0: igual a la red completa filtrada                                 | OK          | 1,726 jornadas finales y 319 reservas (red completa filtrada: 1,726 y 319)                                      |
| Caso base E0: deficit de energia 0                                             | OK          | 0.000 kWh                                                                                                       |
| Caso base E1: igual a la red completa filtrada                                 | OK          | 1,638 jornadas finales y 315 reservas (red completa filtrada: 1,638 y 315)                                      |
| Caso base E1: deficit de energia 0                                             | OK          | 0.000 kWh                                                                                                       |
| Etapa 3 (h=0): cobertura exacta                                                | OK          | 10,327 expediciones en 1,640 tramos                                                                             |
| Etapa 3 (h=0): todo tramo cabe en la bateria util                              | OK          | maximo 314.9 kWh de 315                                                                                         |
| Etapa 3 (h=0): flota = maximo de intervalos superpuestos                       | OK          | flujo 1,166, intervalos 1,166                                                                                   |
| Etapa 3 (h=30): cobertura exacta                                               | OK          | 10,327 expediciones en 1,640 tramos                                                                             |
| Etapa 3 (h=30): todo tramo cabe en la bateria util                             | OK          | maximo 314.9 kWh de 315                                                                                         |
| Etapa 3 (h=30): flota = maximo de intervalos superpuestos                      | OK          | flujo 1,196, intervalos 1,196                                                                                   |
| Etapa 3 (h=60): cobertura exacta                                               | OK          | 10,327 expediciones en 1,640 tramos                                                                             |
| Etapa 3 (h=60): todo tramo cabe en la bateria util                             | OK          | maximo 314.9 kWh de 315                                                                                         |
| Etapa 3 (h=60): flota = maximo de intervalos superpuestos                      | OK          | flujo 1,219, intervalos 1,219                                                                                   |
| Etapa 4 (h=0, Delta=15): deficit 0                                             | OK          | FIFO 0.000 kWh, E2 0.000 kWh                                                                                    |
| Etapa 4 (h=0, Delta=15): ocupacion <= 100 por bloque (E2) y por minuto (FIFO)  | OK          | maximo E2 por bloque 100.00; FIFO por minuto 100; realizacion por minuto de E2: 124 min sobre 100 (informativo) |
| Etapa 4 (h=0, Delta=15): E2 <= E2-FIFO (energia + reservas)                    | OK          | 100,905.49 <= 165,004.72 USD                                                                                    |
| Etapa 4 (h=0, Delta=30): deficit 0                                             | OK          | FIFO 0.000 kWh, E2 0.000 kWh                                                                                    |
| Etapa 4 (h=0, Delta=30): ocupacion <= 100 por bloque (E2) y por minuto (FIFO)  | OK          | maximo E2 por bloque 100.00; FIFO por minuto 100; realizacion por minuto de E2: 101 min sobre 100 (informativo) |
| Etapa 4 (h=0, Delta=30): E2 <= E2-FIFO (energia + reservas)                    | OK          | 100,680.53 <= 165,004.72 USD                                                                                    |
| Etapa 4 (h=0, Delta=5): deficit 0                                              | OK          | FIFO 0.000 kWh, E2 0.000 kWh                                                                                    |
| Etapa 4 (h=0, Delta=5): ocupacion <= 100 por bloque (E2) y por minuto (FIFO)   | OK          | maximo E2 por bloque 100.00; FIFO por minuto 100; realizacion por minuto de E2: 146 min sobre 100 (informativo) |
| Etapa 4 (h=0, Delta=5): E2 <= E2-FIFO (energia + reservas)                     | OK          | 101,148.24 <= 165,004.72 USD                                                                                    |
| Etapa 4 (h=30, Delta=15): deficit 0                                            | OK          | FIFO 0.000 kWh, E2 0.000 kWh                                                                                    |
| Etapa 4 (h=30, Delta=15): ocupacion <= 100 por bloque (E2) y por minuto (FIFO) | OK          | maximo E2 por bloque 100.00; FIFO por minuto 100; realizacion por minuto de E2: 112 min sobre 100 (informativo) |
| Etapa 4 (h=30, Delta=15): E2 <= E2-FIFO (energia + reservas)                   | OK          | 97,097.32 <= 157,004.72 USD                                                                                     |
| Etapa 4 (h=60, Delta=15): deficit 0                                            | OK          | FIFO 0.000 kWh, E2 0.000 kWh                                                                                    |
| Etapa 4 (h=60, Delta=15): ocupacion <= 100 por bloque (E2) y por minuto (FIFO) | OK          | maximo E2 por bloque 100.00; FIFO por minuto 100; realizacion por minuto de E2: 131 min sobre 100 (informativo) |
| Etapa 4 (h=60, Delta=15): E2 <= E2-FIFO (energia + reservas)                   | OK          | 93,840.30 <= 155,754.72 USD                                                                                     |

## 3. KPIs por escenario (configuracion base)

Original = espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). Comparable = sin la espera nocturna en el patio. En el caso base todas las reservas son nocturnas (si una carga intermedia no alcanza, la jornada se parte y el bus nuevo queda en 'operativos').

| KPI                                             | E0      | E1      | E2-FIFO   | E2      |
|:------------------------------------------------|:--------|:--------|:----------|:--------|
| 1. Costo total original (USD/dia)               | 610,052 | 583,741 | 497,774   | 449,668 |
| 1. Costo total comparable (USD/dia)             | 594,602 | 567,807 | 488,464   | 445,495 |
| · flota                                         | 431,500 | 409,500 | 291,500   | 291,500 |
| · reservas intermedias                          | 0       | 0       | 7,500     | 0       |
| · reservas nocturnas                            | 79,750  | 78,750  | 110,500   | 54,500  |
| · km vacios                                     | 20,240  | 18,699  | 17,465    | 17,465  |
| · espera original                               | 21,736  | 21,080  | 15,605    | 10,467  |
| · espera comparable                             | 6,286   | 5,146   | 6,294     | 6,294   |
| · energia                                       | 48,151  | 47,482  | 47,005    | 46,405  |
| · eventos de carga                              | 8,675   | 8,230   | 8,200     | 29,330  |
| 2. N de buses (operativos + reservas)           | 2,045   | 1,953   | 1,638     | 1,384   |
| · buses del VSP                                 | 1,333   | 1,203   | 1,203     | 1,203   |
| · buses operativos (tras la carga / Etapa 3)    | 1,726   | 1,638   | 1,166     | 1,166   |
| 3. % km de deadheading                          | 16.14   | 15.10   | 14.25     | 14.25   |
| 4. Costo medio de la energia (USD/kWh)          | 0.1372  | 0.1369  | 0.1369    | 0.1352  |
| 4. % de la energia en valle                     | 50.9    | 51.6    | 52.1      | 52.4    |
| 5. Buses extra por bateria                      | 712     | 750     | 435       | 181     |
| 6. Reservas intermedias                         | 0       | 0       | 30        | 0       |
| 6. Reservas nocturnas                           | 319     | 315     | 442       | 218     |
| 7. Uso maximo de los puestos (%)                | 100.0   | 100.0   | 100.0     | 125.2   |
| 7. Horas con todos los puestos ocupados         | 17.0    | 17.1    | 15.1      | 15.3    |
| · minutos sobre los puestos                     | 0       | 0       | 0         | 124     |
| 8. Segundos de computo (sin el VSP)             | 1.2     | 1.7     | 4.1       | 100.7   |
| · energia cargada (MWh)                         | 351.1   | 346.7   | 343.3     | 343.3   |
| · deficit de energia (kWh)                      | 0.00    | 0.00    | 0.00      | 0.00    |
| · eventos de carga                              | 1,735   | 1,646   | 1,640     | 5,866   |
| · utilizacion del bus (% de 24 h con pasajeros) | 27.3    | 28.6    | 34.1      | 40.4    |

### Variantes (sensibilidad)

| escenario   | variante   | modelo   |   buses_operativos |   reservas_intermedias |   reservas_nocturnas |   buses_totales |   costo_energia |   costo_eventos |   costo_total_comparable |   costo_total_original |
|:------------|:-----------|:---------|-------------------:|-----------------------:|---------------------:|----------------:|----------------:|----------------:|-------------------------:|-----------------------:|
| E2          | Delta=5    | agregado |               1166 |                      0 |                  219 |            1385 |           46398 |           54440 |                   470848 |                 474770 |
| E2          | Delta=30   | agregado |               1166 |                      0 |                  217 |            1383 |           46431 |           18090 |                   434030 |                 438878 |
| E2-FIFO     | h=30       | -        |               1196 |                      0 |                  440 |            1636 |           47005 |            8200 |                   488670 |                 497980 |
| E2          | h=30       | agregado |               1196 |                      0 |                  203 |            1399 |           46347 |           28300 |                   448862 |                 453211 |
| E2-FIFO     | h=60       | -        |               1219 |                      0 |                  435 |            1654 |           47005 |            8200 |                   493647 |                 502958 |
| E2          | h=60       | agregado |               1219 |                      0 |                  190 |            1409 |           46340 |           29170 |                   452702 |                 456839 |

## 4. Diagnostico de flota de la Etapa 3

| paso                             |   buses | que_mide                                                            |
|:---------------------------------|--------:|:--------------------------------------------------------------------|
| (i) VSP                          |    1203 | Punto de partida: una jornada = un bus                              |
| (ii) Reuso del patio sin bateria |    1130 | Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga |
| (iii) Solo cortes                |    1640 | Cada tramo un bus                                                   |
| (iv) Cortes + re-encadenamiento  |    1166 | La Etapa 3 completa (recarga completa + holgura 0 min)              |

- 1,640 tramos desde 1,203 jornadas (434 cortadas; 5,227.3 km extra). Ventanas: 474 intermedias, 1,166 nocturnas.
- Nocturnas que no alcanzan la recarga completa ni con puesto libre: 53 (de ellas 38 cadenas de mas de 24 h: el flujo, como el VSP, es de un dia y no ciclico). Son reservas que ninguna programacion de carga puede evitar.

## 5. Reservas por tipo

| escenario   |   reservas_intermedias |   reservas_nocturnas |   reservas |
|:------------|-----------------------:|---------------------:|-----------:|
| E0          |                      0 |                  319 |        319 |
| E1          |                      0 |                  315 |        315 |
| E2-FIFO     |                     30 |                  442 |        472 |
| E2          |                      0 |                  218 |        218 |

## 6. Energia por periodo tarifario (kWh y USD)

| periodo   | horas   |   precio_usd_kwh |   kwh_E0 |   kwh_E1 |   kwh_E2-FIFO |   kwh_E2 |   usd_E0 |   usd_E1 |   usd_E2-FIFO |   usd_E2 |
|:----------|:--------|-----------------:|---------:|---------:|--------------:|---------:|---------:|---------:|--------------:|---------:|
| P1        | 00-08   |             0.1  |   143053 |   143012 |        142986 |   144000 |    14305 |    14301 |         14299 |    14400 |
| P2        | 08-14   |             0.15 |   103026 |    99886 |         99142 |    97625 |    15454 |    14983 |         14871 |    14644 |
| P3        | 14-17   |             0.22 |     7273 |     6779 |          8980 |      848 |     1600 |     1491 |          1976 |      187 |
| P4        | 17-19   |             0.15 |    10975 |    10196 |          6975 |    14910 |     1646 |     1529 |          1046 |     2237 |
| P5        | 19-22   |             0.22 |    50962 |    51102 |         49460 |    49903 |    11212 |    11243 |         10881 |    10979 |
| P6        | 22-24   |             0.11 |    35767 |    35765 |         35743 |    36000 |     3934 |     3934 |          3932 |     3960 |

## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)

Puestos: 100. E2 = realizacion por minuto del modelo agregado.

|   hora |   E0_promedio |   E0_maximo |   E1_promedio |   E1_maximo |   E2-FIFO_promedio |   E2-FIFO_maximo |   E2_promedio |   E2_maximo |
|-------:|--------------:|------------:|--------------:|------------:|-------------------:|-----------------:|--------------:|------------:|
|      0 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       100   |
|      1 |         100   |         100 |         100   |         100 |               99.9 |              100 |         100   |       100   |
|      2 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       100   |
|      3 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       100   |
|      4 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       100   |
|      5 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       108.7 |
|      6 |         100   |         100 |         100   |         100 |               99.8 |              100 |         100   |       112.7 |
|      7 |         100   |         100 |         100   |         100 |               99.8 |              100 |         100   |       125.2 |
|      8 |          99.8 |         100 |          99.8 |         100 |               98.8 |              100 |         100   |       103.1 |
|      9 |          99.4 |         100 |          99.7 |         100 |               98.9 |              100 |         100   |       100   |
|     10 |          99.7 |         100 |         100   |         100 |               99.5 |              100 |         100   |       100   |
|     11 |         100   |         100 |         100   |         100 |               99.6 |              100 |         100   |       100   |
|     12 |          99.9 |         100 |         100   |         100 |               98.8 |              100 |         100   |       100   |
|     13 |          79.4 |         100 |          61.2 |         100 |               60.2 |               90 |          42.4 |       100   |
|     14 |          21.4 |          41 |          10.8 |          20 |               17.1 |               26 |           3.3 |         7   |
|     15 |          10.3 |          11 |          10.8 |          13 |               17.7 |               20 |           1   |         6   |
|     16 |           9.2 |          15 |          16.2 |          24 |               15.5 |               20 |           0.4 |         2   |
|     17 |          25.6 |          34 |          23.6 |          28 |               18.5 |               22 |          59   |        69   |
|     18 |          35.6 |          55 |          33.2 |          56 |               20.5 |               41 |          23.9 |        43   |
|     19 |          84.6 |         100 |          85.5 |         100 |               76.3 |              100 |          77.2 |       113.9 |
|     20 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       116.7 |
|     21 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       119.4 |
|     22 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       109.1 |
|     23 |         100   |         100 |         100   |         100 |              100   |              100 |         100   |       100   |

## 8. Sensibilidad a la holgura h de la Etapa 3 (Delta base)

|   holgura_min |   buses_etapa3 |   reservas_FIFO |   reservas_E2 |   buses_totales_FIFO |   buses_totales_E2 |   costo_total_comparable_E2 |   costo_energia_E2 |   nocturnas_sin_tiempo_carga |
|--------------:|---------------:|----------------:|--------------:|---------------------:|-------------------:|----------------------------:|-------------------:|-----------------------------:|
|             0 |           1166 |             472 |           218 |                 1638 |               1384 |                      445495 |              46405 |                           53 |
|            30 |           1196 |             440 |           203 |                 1636 |               1399 |                      448862 |              46347 |                           57 |
|            60 |           1219 |             435 |           190 |                 1654 |               1409 |                      452702 |              46340 |                           50 |

## 9. Sensibilidad al largo del bloque Delta (holgura base)

|   delta_min |   objetivo_usd |   cota_lp_usd |   reservas |   costo_energia |   eventos |   minutos_sobre_puestos |   variables |   segundos_lp |   segundos_milp |   brecha | estado                 |
|------------:|---------------:|--------------:|-----------:|----------------:|----------:|------------------------:|------------:|--------------:|----------------:|---------:|:-----------------------|
|           5 |         101148 |      100351   |        219 |         46398.2 |     10888 |                     146 |      478841 |          8.67 |           93.65 | 0.003662 | optimo (brecha pedida) |
|          15 |         100905 |      100129   |        218 |         46405.5 |      5866 |                     124 |      163962 |          8.28 |           89.4  | 0.003172 | optimo (brecha pedida) |
|          30 |         100681 |       99854.6 |        217 |         46430.5 |      3618 |                     101 |       85242 |          1.51 |           13.34 | 0.003772 | optimo (brecha pedida) |

## 10. Segundos, estado y brecha de cada modelo

El VSP (Etapa 2) no se vuelve a correr: sus jornadas son un archivo.

| corrida                                        | estado                        | brecha   | fuente_brecha   |   segundos |
|:-----------------------------------------------|:------------------------------|:---------|:----------------|-----------:|
| Caso base E0 (simulador reactivo)              | -                             | -        | -               |       1.2  |
| Caso base E1 (simulador reactivo)              | -                             | -        | -               |       1.7  |
| Etapa 3 h=0 (DP + flujo)                       | optimo (flujo entero)         | 0        | flujo entero    |       3    |
| Etapa 3 h=30 (DP + flujo)                      | optimo (flujo entero)         | 0        | flujo entero    |       3.7  |
| Etapa 3 h=60 (DP + flujo)                      | optimo (flujo entero)         | 0        | flujo entero    |       2.2  |
| Etapa 4 h=0 Delta=5: E2-FIFO                   | heuristica (sin optimizacion) | nan      | -               |       0.22 |
| Etapa 4 h=0 Delta=5: E2 agregado - LP (cota)   | optimo                        | 0.0      | Gurobi          |       8.67 |
| Etapa 4 h=0 Delta=5: E2 agregado - MILP        | optimo (brecha pedida)        | 0.003662 | Gurobi          |      93.65 |
| Etapa 4 h=0 Delta=15: E2-FIFO                  | heuristica (sin optimizacion) | nan      | -               |       1.06 |
| Etapa 4 h=0 Delta=15: E2 agregado - LP (cota)  | optimo                        | 0.0      | Gurobi          |       8.28 |
| Etapa 4 h=0 Delta=15: E2 agregado - MILP       | optimo (brecha pedida)        | 0.003172 | Gurobi          |      89.4  |
| Etapa 4 h=0 Delta=30: E2-FIFO                  | heuristica (sin optimizacion) | nan      | -               |       0.31 |
| Etapa 4 h=0 Delta=30: E2 agregado - LP (cota)  | optimo                        | 0.0      | Gurobi          |       1.51 |
| Etapa 4 h=0 Delta=30: E2 agregado - MILP       | optimo (brecha pedida)        | 0.003772 | Gurobi          |      13.34 |
| Etapa 4 h=30 Delta=15: E2-FIFO                 | heuristica (sin optimizacion) | nan      | -               |       0.26 |
| Etapa 4 h=30 Delta=15: E2 agregado - LP (cota) | optimo                        | 0.0      | Gurobi          |       2.38 |
| Etapa 4 h=30 Delta=15: E2 agregado - MILP      | optimo (brecha pedida)        | 0.001547 | Gurobi          |      30.52 |
| Etapa 4 h=60 Delta=15: E2-FIFO                 | heuristica (sin optimizacion) | nan      | -               |       0.35 |
| Etapa 4 h=60 Delta=15: E2 agregado - LP (cota) | optimo                        | 0.0      | Gurobi          |       2.15 |
| Etapa 4 h=60 Delta=15: E2 agregado - MILP      | optimo (brecha pedida)        | 0.003443 | Gurobi          |      23.77 |

## 11. Modelo detallado vs agregado

Pendiente (P2): correr 13- con --detallado.

## 12. Figuras

- `kpis/graficos/escalera_buses.png`: Buses VSP -> operativos -> + reservas en cada escenario de la escalera.
- `kpis/graficos/costo_apilado.png`: Costo total comparable por componente; el rombo marca el total original.
- `kpis/graficos/ocupacion_24h.png`: Buses cargando por minuto en E1, E2-FIFO y E2 frente a los puestos y la tarifa punta.
- `kpis/graficos/energia_por_tarifa.png`: MWh cargados en cada periodo tarifario por escenario.
- `kpis/graficos/sensibilidad_holgura.png`: Efecto de la holgura h en los buses de la Etapa 3 y las reservas.
- `kpis/graficos/sensibilidad_delta.png`: Efecto del largo del bloque Delta en el objetivo de E2 y en el tiempo.
- Por corrida: `etapa3/h<h>/graficos/` (Gantt de cadenas, llegadas al patio por hora) y `etapa4/h<h>_d<Delta>/graficos/` (ocupacion 24 h FIFO vs E2, energia por tarifa).

## 13. Definiciones y supuestos que hay que tener presentes al analizar

- E2-FIFO y E2 usan las mismas ventanas de la Etapa 3: la diferencia entre ellos es solo la programacion de la carga.
- E1 -> E2-FIFO cambia la carga reactiva por la Etapa 3 (cortes + re-encadenamiento con recarga completa en el patio).
- Parte de la mejora de la Etapa 3 viene de permitir que un bus vuelva al patio y salga de nuevo (paso ii del diagnostico), algo que ni el VSP ni el caso base permiten.
- Reserva: si la carga de una ventana no termina antes de la siguiente salida del bus, un bus ya cargado cubre esa salida (250 USD). En una ventana intermedia la reserva toma el resto de la cadena (supuesto conservador).
- La Etapa 3 no ve los puestos; la holgura h los anticipa. La Etapa 4 decide con los puestos y la tarifa.
- El modelo agregado escribe la capacidad en energia por bloque: es exacto salvo en los bloques de borde ('minutos sobre los puestos' mide ese error).
- Limitaciones: un solo electroterminal; recarga completa entre tramos; deadhead euclidiano; un dia tipo; flujo de un dia (no ciclico).
