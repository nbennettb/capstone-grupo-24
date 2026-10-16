# Resumen para analisis: instancia La Reina

Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de `results/instancia_LR/`. Escenarios: **Caso base** (jornadas por linea + carga reactiva); **Caso base con interlining** (lo mismo, con interlining en las jornadas); **Propuesta con carga por orden de llegada** (Etapa 3 + carga por orden de llegada); **Propuesta completa** (Etapa 3 + Etapa 4, modelo detallado con bloques de 15 min). Cada escalon cambia una sola cosa.

## 1. Instancia y parametros

- Electroterminal **La Reina** completo: 100 puestos de carga; jornadas sin bateria (Etapa 2): Caso base 1,333, Caso base con interlining 1,203; 1,203 jornadas del Caso base con interlining de entrada a la Etapa 3.
- Energia a reponer en las propuestas / capacidad de 24 h de los puestos: 79.5%.
- Bateria util entre cargas 315 kWh (ciclo al 100%, minimo 10%); carga a 180 kW; consumo 1.4 kWh/km.
- Costos: bus 250 USD/dia (igual para una reserva), km vacio 0.5 USD, espera 0.03 USD/min, evento de carga 5 USD.
- Tarifa (USD/kWh): 00-08 h = 0.10, 08-14 h = 0.15, 14-17 h = 0.22, 17-19 h = 0.15, 19-22 h = 0.22, 22-24 h = 0.11.
- Deadhead: euclidiana x 1.3 a 20 km/h; layover 3 min.
- Etapa 3: regla de corte min_tramos_km (minimos tramos, luego minimos km extra); holgura de recarga base 0 min; sensibilidad [0, 30, 60] min.
- Etapa 4: largo del bloque base 15 min (sensibilidad [5, 15, 30] min); Gurobi, brecha 0.5%, limite 600 s el modelo agregado y 3600 s el detallado; deficit penalizado con 10,000 USD/kWh; desempate 1e-06 USD/kWh por bloque desde la llegada.

## 2. Validaciones (re-verificadas desde los CSV)

| validacion                                                                                                                                  | resultado   | detalle                                                                                                                                                       |
|:--------------------------------------------------------------------------------------------------------------------------------------------|:------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Caso base: igual a la red completa filtrada                                                                                                 | OK          | 1,726 jornadas finales y 319 reservas (red completa filtrada: 1,726 y 319)                                                                                    |
| Caso base: deficit de energia 0                                                                                                             | OK          | 0.000 kWh                                                                                                                                                     |
| Caso base con interlining: igual a la red completa filtrada                                                                                 | OK          | 1,638 jornadas finales y 315 reservas (red completa filtrada: 1,638 y 315)                                                                                    |
| Caso base con interlining: deficit de energia 0                                                                                             | OK          | 0.000 kWh                                                                                                                                                     |
| Etapa 3 (holgura de recarga 0 min): cobertura exacta                                                                                        | OK          | 10,327 expediciones en 1,640 tramos                                                                                                                           |
| Etapa 3 (holgura de recarga 0 min): todo tramo cabe en la bateria util                                                                      | OK          | maximo 314.9 kWh de 315                                                                                                                                       |
| Etapa 3 (holgura de recarga 0 min): flota = maximo de intervalos superpuestos                                                               | OK          | flujo 1,166, intervalos 1,166                                                                                                                                 |
| Etapa 3 (holgura de recarga 30 min): cobertura exacta                                                                                       | OK          | 10,327 expediciones en 1,640 tramos                                                                                                                           |
| Etapa 3 (holgura de recarga 30 min): todo tramo cabe en la bateria util                                                                     | OK          | maximo 314.9 kWh de 315                                                                                                                                       |
| Etapa 3 (holgura de recarga 30 min): flota = maximo de intervalos superpuestos                                                              | OK          | flujo 1,196, intervalos 1,196                                                                                                                                 |
| Etapa 3 (holgura de recarga 60 min): cobertura exacta                                                                                       | OK          | 10,327 expediciones en 1,640 tramos                                                                                                                           |
| Etapa 3 (holgura de recarga 60 min): todo tramo cabe en la bateria util                                                                     | OK          | maximo 314.9 kWh de 315                                                                                                                                       |
| Etapa 3 (holgura de recarga 60 min): flota = maximo de intervalos superpuestos                                                              | OK          | flujo 1,219, intervalos 1,219                                                                                                                                 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): deficit 0                                                                      | OK          | orden de llegada 0.000 kWh, modelo agregado 0.000 kWh                                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): ocupacion <= 100 por bloque (modelo agregado) y por minuto (orden de llegada)  | OK          | maximo del modelo agregado por bloque 100.00; orden de llegada por minuto 100; ejecucion minuto a minuto del modelo agregado: 124 min sobre 100 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo agregado <= orden de llegada (energia + reservas)                       | OK          | 100,905.49 <= 165,004.72 USD                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo detallado, deficit 0                                                    | OK          | -0.000 kWh                                                                                                                                                    |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo detallado <= orden de llegada (energia + reservas + eventos)            | OK          | 109,040.58 <= 173,204.72 USD                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo detallado, ocupacion <= 100 por bloque                                  | OK          | maximo por bloque 100.00; ejecucion minuto a minuto: 32 min sobre 100 (informativo)                                                                           |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 30 min): deficit 0                                                                      | OK          | orden de llegada 0.000 kWh, modelo agregado 0.000 kWh                                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 30 min): ocupacion <= 100 por bloque (modelo agregado) y por minuto (orden de llegada)  | OK          | maximo del modelo agregado por bloque 100.00; orden de llegada por minuto 100; ejecucion minuto a minuto del modelo agregado: 101 min sobre 100 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 30 min): modelo agregado <= orden de llegada (energia + reservas)                       | OK          | 100,680.53 <= 165,004.72 USD                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 5 min): deficit 0                                                                       | OK          | orden de llegada 0.000 kWh, modelo agregado 0.000 kWh                                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 5 min): ocupacion <= 100 por bloque (modelo agregado) y por minuto (orden de llegada)   | OK          | maximo del modelo agregado por bloque 100.00; orden de llegada por minuto 100; ejecucion minuto a minuto del modelo agregado: 146 min sobre 100 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 5 min): modelo agregado <= orden de llegada (energia + reservas)                        | OK          | 101,148.24 <= 165,004.72 USD                                                                                                                                  |
| Etapa 4 (holgura de recarga 30 min, largo del bloque 15 min): deficit 0                                                                     | OK          | orden de llegada 0.000 kWh, modelo agregado 0.000 kWh                                                                                                         |
| Etapa 4 (holgura de recarga 30 min, largo del bloque 15 min): ocupacion <= 100 por bloque (modelo agregado) y por minuto (orden de llegada) | OK          | maximo del modelo agregado por bloque 100.00; orden de llegada por minuto 100; ejecucion minuto a minuto del modelo agregado: 112 min sobre 100 (informativo) |
| Etapa 4 (holgura de recarga 30 min, largo del bloque 15 min): modelo agregado <= orden de llegada (energia + reservas)                      | OK          | 97,097.32 <= 157,004.72 USD                                                                                                                                   |
| Etapa 4 (holgura de recarga 60 min, largo del bloque 15 min): deficit 0                                                                     | OK          | orden de llegada 0.000 kWh, modelo agregado 0.000 kWh                                                                                                         |
| Etapa 4 (holgura de recarga 60 min, largo del bloque 15 min): ocupacion <= 100 por bloque (modelo agregado) y por minuto (orden de llegada) | OK          | maximo del modelo agregado por bloque 100.00; orden de llegada por minuto 100; ejecucion minuto a minuto del modelo agregado: 131 min sobre 100 (informativo) |
| Etapa 4 (holgura de recarga 60 min, largo del bloque 15 min): modelo agregado <= orden de llegada (energia + reservas)                      | OK          | 93,840.30 <= 155,754.72 USD                                                                                                                                   |

## 3. KPIs por escenario

Costo total = sin la espera nocturna en el patio (la metrica principal). Costo total con espera nocturna = la espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). En los casos base todas las reservas son nocturnas: si una carga diurna no alcanza, la jornada se parte y el bus nuevo queda en 'operativos'. La Propuesta completa es el modelo detallado con bloques de 15 min.

| KPI                                                                                   | Caso base   | Caso base con interlining   | Propuesta con carga por orden de llegada   | Propuesta completa   |
|:--------------------------------------------------------------------------------------|:------------|:----------------------------|:-------------------------------------------|:---------------------|
| 1. Costo total (USD/dia)                                                              | 594,602     | 567,807                     | 488,464                                    | 424,300              |
| 1. Costo total con espera nocturna (USD/dia)                                          | 610,052     | 583,741                     | 497,774                                    | 432,525              |
| · flota                                                                               | 431,500     | 409,500                     | 291,500                                    | 291,500              |
| · reservas diurnas                                                                    | 0           | 0                           | 7,500                                      | 0                    |
| · reservas nocturnas                                                                  | 79,750      | 78,750                      | 110,500                                    | 54,250               |
| · km vacios                                                                           | 20,240      | 18,699                      | 17,465                                     | 17,465               |
| · espera                                                                              | 6,286       | 5,146                       | 6,294                                      | 6,294                |
| · espera, con la espera nocturna                                                      | 21,736      | 21,080                      | 15,605                                     | 14,520               |
| · energia                                                                             | 48,151      | 47,482                      | 47,005                                     | 46,416               |
| · eventos de carga                                                                    | 8,675       | 8,230                       | 8,200                                      | 8,375                |
| 2. N de buses (operativos + reservas)                                                 | 2,045       | 1,953                       | 1,638                                      | 1,383                |
| · buses de las jornadas sin bateria                                                   | 1,333       | 1,203                       | 1,203                                      | 1,203                |
| · buses operativos (tras la carga en los casos base; de la Etapa 3 en las propuestas) | 1,726       | 1,638                       | 1,166                                      | 1,166                |
| 3. % km de deadheading                                                                | 16.14       | 15.10                       | 14.25                                      | 14.25                |
| 4. Costo medio de la energia (USD/kWh)                                                | 0.1372      | 0.1369                      | 0.1369                                     | 0.1352               |
| 4. % de la energia en valle                                                           | 50.9        | 51.6                        | 52.1                                       | 52.4                 |
| 5. Buses extra por bateria                                                            | 712         | 750                         | 435                                        | 180                  |
| 6. Reservas diurnas                                                                   | 0           | 0                           | 30                                         | 0                    |
| 6. Reservas nocturnas                                                                 | 319         | 315                         | 442                                        | 217                  |
| 7. Uso maximo de los puestos (%)                                                      | 100.0       | 100.0                       | 100.0                                      | 115.0                |
| · maximo de buses cargando a la vez (minuto a minuto)                                 | 100.0       | 100.0                       | 100.0                                      | 115.0                |
| 7. Horas con todos los puestos ocupados                                               | 17.0        | 17.1                        | 15.1                                       | 16.4                 |
| · minutos sobre los puestos                                                           | 0           | 0                           | 0                                          | 32                   |
| 8. Segundos de computo (sin la Etapa 2)                                               | 1.2         | 1.7                         | 4.1                                        | 3,608.1              |
| · energia cargada (MWh)                                                               | 351.1       | 346.7                       | 343.3                                      | 343.3                |
| · deficit de energia (kWh)                                                            | 0.00        | 0.00                        | 0.00                                       | -0.00                |
| · eventos de carga                                                                    | 1,735       | 1,646                       | 1,640                                      | 1,675                |
| · utilizacion del bus (% de 24 h con pasajeros)                                       | 27.3        | 28.6                        | 34.1                                       | 40.4                 |

### Variantes (sensibilidad y modelo agregado)

| escenario                                | variante                  | modelo   |   buses_operativos |   reservas_diurnas |   reservas_nocturnas |   buses_totales |   costo_energia |   costo_eventos |   costo_total |   costo_total_con_espera_nocturna |
|:-----------------------------------------|:--------------------------|:---------|-------------------:|-------------------:|---------------------:|----------------:|----------------:|----------------:|--------------:|----------------------------------:|
| Propuesta completa                       | largo del bloque 5 min    | agregado |               1166 |                  0 |                  219 |            1385 |           46398 |           54440 |        470848 |                            474770 |
| Propuesta completa                       | modelo agregado           | agregado |               1166 |                  0 |                  218 |            1384 |           46405 |           29330 |        445495 |                            449668 |
| Propuesta completa                       | largo del bloque 30 min   | agregado |               1166 |                  0 |                  217 |            1383 |           46431 |           18090 |        434030 |                            438878 |
| Propuesta con carga por orden de llegada | holgura de recarga 30 min | -        |               1196 |                  0 |                  440 |            1636 |           47005 |            8200 |        488670 |                            497980 |
| Propuesta completa                       | holgura de recarga 30 min | agregado |               1196 |                  0 |                  203 |            1399 |           46347 |           28300 |        448862 |                            453211 |
| Propuesta con carga por orden de llegada | holgura de recarga 60 min | -        |               1219 |                  0 |                  435 |            1654 |           47005 |            8200 |        493647 |                            502958 |
| Propuesta completa                       | holgura de recarga 60 min | agregado |               1219 |                  0 |                  190 |            1409 |           46340 |           29170 |        452702 |                            456839 |

## 4. Diagnostico de flota de la Etapa 3

| paso                             |   buses | que_mide                                                            |
|:---------------------------------|--------:|:--------------------------------------------------------------------|
| (i) Jornadas sin bateria         |    1203 | Punto de partida: una jornada = un bus                              |
| (ii) Reuso del patio sin bateria |    1130 | Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga |
| (iii) Solo cortes                |    1640 | Cada tramo un bus                                                   |
| (iv) Cortes + re-encadenamiento  |    1166 | La Etapa 3 completa (recarga completa + holgura 0 min)              |

- 1,640 tramos desde 1,203 jornadas (434 cortadas; 5,227.3 km extra). Ventanas de carga: 474 diurnas (entre tramos), 1,166 nocturnas.
- Nocturnas que no alcanzan la recarga completa ni con puesto libre: 53 (de ellas 38 cadenas de mas de 24 h: el flujo, como las jornadas sin bateria, es de un dia y no ciclico). Son reservas que ninguna programacion de carga puede evitar.

## 5. Reservas por tipo

| escenario                                |   reservas_diurnas |   reservas_nocturnas |   reservas |
|:-----------------------------------------|-------------------:|---------------------:|-----------:|
| Caso base                                |                  0 |                  319 |        319 |
| Caso base con interlining                |                  0 |                  315 |        315 |
| Propuesta con carga por orden de llegada |                 30 |                  442 |        472 |
| Propuesta completa                       |                  0 |                  217 |        217 |

## 6. Energia por tramo horario (kWh y USD)

| tramo horario   |   precio_usd_kwh |   kWh Caso base |   kWh Caso base con interlining |   kWh Propuesta con carga por orden de llegada |   kWh Propuesta completa |   USD Caso base |   USD Caso base con interlining |   USD Propuesta con carga por orden de llegada |   USD Propuesta completa |
|:----------------|-----------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|
| 00-08 h         |             0.1  |          143053 |                          143012 |                                         142986 |                   144000 |           14305 |                           14301 |                                          14299 |                    14400 |
| 08-14 h         |             0.15 |          103026 |                           99886 |                                          99142 |                    95925 |           15454 |                           14983 |                                          14871 |                    14389 |
| 14-17 h         |             0.22 |            7273 |                            6779 |                                           8980 |                     1036 |            1600 |                            1491 |                                           1976 |                      228 |
| 17-19 h         |             0.15 |           10975 |                           10196 |                                           6975 |                    16465 |            1646 |                            1529 |                                           1046 |                     2470 |
| 19-22 h         |             0.22 |           50962 |                           51102 |                                          49460 |                    49860 |           11212 |                           11243 |                                          10881 |                    10969 |
| 22-24 h         |             0.11 |           35767 |                           35765 |                                          35743 |                    36000 |            3934 |                            3934 |                                           3932 |                     3960 |

## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)

Puestos: 100. Propuesta completa = ejecucion minuto a minuto del modelo detallado.

|   hora |   Caso base (promedio) |   Caso base (maximo) |   Caso base + interlining (promedio) |   Caso base + interlining (maximo) |   Propuesta, carga por llegada (promedio) |   Propuesta, carga por llegada (maximo) |   Propuesta completa (promedio) |   Propuesta completa (maximo) |
|-------:|-----------------------:|---------------------:|-------------------------------------:|-----------------------------------:|------------------------------------------:|----------------------------------------:|--------------------------------:|------------------------------:|
|      0 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |
|      1 |                  100   |                  100 |                                100   |                                100 |                                      99.9 |                                     100 |                           100   |                         100   |
|      2 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |
|      3 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |
|      4 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |
|      5 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |
|      6 |                  100   |                  100 |                                100   |                                100 |                                      99.8 |                                     100 |                           100   |                         100   |
|      7 |                  100   |                  100 |                                100   |                                100 |                                      99.8 |                                     100 |                           100   |                         115   |
|      8 |                   99.8 |                  100 |                                 99.8 |                                100 |                                      98.8 |                                     100 |                           100   |                         106.1 |
|      9 |                   99.4 |                  100 |                                 99.7 |                                100 |                                      98.9 |                                     100 |                           100   |                         101   |
|     10 |                   99.7 |                  100 |                                100   |                                100 |                                      99.5 |                                     100 |                           100   |                         100   |
|     11 |                  100   |                  100 |                                100   |                                100 |                                      99.6 |                                     100 |                           100   |                         100   |
|     12 |                   99.9 |                  100 |                                100   |                                100 |                                      98.8 |                                     100 |                            98.8 |                         104.8 |
|     13 |                   79.4 |                  100 |                                 61.2 |                                100 |                                      60.2 |                                      90 |                            34.1 |                          74.1 |
|     14 |                   21.4 |                   41 |                                 10.8 |                                 20 |                                      17.1 |                                      26 |                             1.3 |                           9   |
|     15 |                   10.3 |                   11 |                                 10.8 |                                 13 |                                      17.7 |                                      20 |                             0   |                           0   |
|     16 |                    9.2 |                   15 |                                 16.2 |                                 24 |                                      15.5 |                                      20 |                             4.5 |                          19   |
|     17 |                   25.6 |                   34 |                                 23.6 |                                 28 |                                      18.5 |                                      22 |                            64   |                          70   |
|     18 |                   35.6 |                   55 |                                 33.2 |                                 56 |                                      20.5 |                                      41 |                            27.4 |                          43   |
|     19 |                   84.6 |                  100 |                                 85.5 |                                100 |                                      76.3 |                                     100 |                            77.2 |                         110.5 |
|     20 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |
|     21 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                            99.8 |                         100   |
|     22 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |
|     23 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                         100   |

## 8. Sensibilidad a la holgura de recarga de la Etapa 3 (modelo agregado, largo del bloque base)

|   holgura_de_recarga_min |   buses_etapa3 |   reservas_carga_por_llegada |   reservas_propuesta_completa |   buses_totales_carga_por_llegada |   buses_totales_propuesta_completa |   costo_total_propuesta_completa |   costo_energia_propuesta_completa |   nocturnas_sin_tiempo_carga |
|-------------------------:|---------------:|-----------------------------:|------------------------------:|----------------------------------:|-----------------------------------:|---------------------------------:|-----------------------------------:|-----------------------------:|
|                        0 |           1166 |                          472 |                           218 |                              1638 |                               1384 |                           445495 |                              46405 |                           53 |
|                       30 |           1196 |                          440 |                           203 |                              1636 |                               1399 |                           448862 |                              46347 |                           57 |
|                       60 |           1219 |                          435 |                           190 |                              1654 |                               1409 |                           452702 |                              46340 |                           50 |

## 9. Sensibilidad al largo del bloque (modelo agregado, holgura de recarga base)

|   largo_del_bloque_min |   objetivo_usd |   cota_lp_usd |   reservas |   costo_energia |   eventos |   minutos_sobre_puestos |   variables |   segundos_lp |   segundos_milp |   brecha | estado                 |
|-----------------------:|---------------:|--------------:|-----------:|----------------:|----------:|------------------------:|------------:|--------------:|----------------:|---------:|:-----------------------|
|                      5 |         101148 |      100351   |        219 |         46398.2 |     10888 |                     146 |      478841 |          8.67 |           93.65 | 0.003662 | optimo (brecha pedida) |
|                     15 |         100905 |      100129   |        218 |         46405.5 |      5866 |                     124 |      163962 |          8.28 |           89.4  | 0.003172 | optimo (brecha pedida) |
|                     30 |         100681 |       99854.6 |        217 |         46430.5 |      3618 |                     101 |       85242 |          1.51 |           13.34 | 0.003772 | optimo (brecha pedida) |

## 10. Segundos, estado y brecha de cada modelo

La Etapa 2 (jornadas sin bateria) no se vuelve a correr: sus jornadas son un archivo.

| corrida                                                                                                | estado                        | brecha   | fuente_brecha                                         |   segundos |
|:-------------------------------------------------------------------------------------------------------|:------------------------------|:---------|:------------------------------------------------------|-----------:|
| Caso base (simulador reactivo)                                                                         | -                             | -        | -                                                     |       1.2  |
| Caso base con interlining (simulador reactivo)                                                         | -                             | -        | -                                                     |       1.7  |
| Etapa 3 (holgura de recarga 0 min) (DP + flujo)                                                        | optimo (flujo entero)         | 0        | flujo entero                                          |       3    |
| Etapa 3 (holgura de recarga 30 min) (DP + flujo)                                                       | optimo (flujo entero)         | 0        | flujo entero                                          |       3.7  |
| Etapa 3 (holgura de recarga 60 min) (DP + flujo)                                                       | optimo (flujo entero)         | 0        | flujo entero                                          |       2.2  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 5 min): Propuesta con carga por orden de llegada   | heuristica (sin optimizacion) | nan      | -                                                     |       0.22 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 5 min): Modelo agregado, LP (cota)                 | optimo                        | 0.0      | Gurobi                                                |       8.67 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 5 min): Modelo agregado (MILP)                     | optimo (brecha pedida)        | 0.003662 | Gurobi                                                |      93.65 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta con carga por orden de llegada  | heuristica (sin optimizacion) | nan      | -                                                     |       1.06 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo agregado, LP (cota)                | optimo                        | 0.0      | Gurobi                                                |       8.28 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo agregado (MILP)                    | optimo (brecha pedida)        | 0.003172 | Gurobi                                                |      89.4  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo detallado, fase 1 (reservas fijas) | limite de tiempo              | 0.043684 | Gurobi, con las reservas fijas                        |    1506.46 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo detallado (MILP)                   | limite de tiempo              | 0.006581 | cota valida (LP del agregado + un evento por ventana) |    3605.12 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 30 min): Propuesta con carga por orden de llegada  | heuristica (sin optimizacion) | nan      | -                                                     |       0.31 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 30 min): Modelo agregado, LP (cota)                | optimo                        | 0.0      | Gurobi                                                |       1.51 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 30 min): Modelo agregado (MILP)                    | optimo (brecha pedida)        | 0.003772 | Gurobi                                                |      13.34 |
| Etapa 4 (holgura de recarga 30 min, largo del bloque 15 min): Propuesta con carga por orden de llegada | heuristica (sin optimizacion) | nan      | -                                                     |       0.26 |
| Etapa 4 (holgura de recarga 30 min, largo del bloque 15 min): Modelo agregado, LP (cota)               | optimo                        | 0.0      | Gurobi                                                |       2.38 |
| Etapa 4 (holgura de recarga 30 min, largo del bloque 15 min): Modelo agregado (MILP)                   | optimo (brecha pedida)        | 0.001547 | Gurobi                                                |      30.52 |
| Etapa 4 (holgura de recarga 60 min, largo del bloque 15 min): Propuesta con carga por orden de llegada | heuristica (sin optimizacion) | nan      | -                                                     |       0.35 |
| Etapa 4 (holgura de recarga 60 min, largo del bloque 15 min): Modelo agregado, LP (cota)               | optimo                        | 0.0      | Gurobi                                                |       2.15 |
| Etapa 4 (holgura de recarga 60 min, largo del bloque 15 min): Modelo agregado (MILP)                   | optimo (brecha pedida)        | 0.003443 | Gurobi                                                |      23.77 |

## 11. Modelo detallado frente al modelo agregado

|   largo del bloque (min) | modelo    |   reservas |   eventos | energia + reservas (USD)   | total carga = + eventos (USD)   |   minutos sobre los puestos | segundos   | brecha   | fuente de la brecha                                   |
|-------------------------:|:----------|-----------:|----------:|:---------------------------|:--------------------------------|----------------------------:|:-----------|:---------|:------------------------------------------------------|
|                       15 | agregado  |        218 |      5866 | 100,905                    | 130,235                         |                         124 | 89         | 0.32%    | Gurobi                                                |
|                       15 | detallado |        217 |      1675 | 100,666                    | 109,041                         |                          32 | 3,605      | 0.66%    | cota valida (LP del agregado + un evento por ventana) |

**Conclusion:** con bloques de 15 min, la programacion del modelo detallado cuesta 109,041 USD/dia contra 130,235 del modelo agregado con sus eventos contados despues (-16.3%), con 217 reservas contra 218 y 1,675 eventos contra 5,866; el modelo agregado se resuelve en 89 s y el modelo detallado en 3,605 s, con brecha 0.66%.

## Figuras del informe

En `informe/`, cada una en PDF (vectorial, para LaTeX), PNG y CSV con sus datos. Ancho pensado para 0.8 del ancho de texto de LaTeX, letra de 9 pt, sin titulo en la imagen (va en el caption).

| Figura | Caption propuesto | Cifra principal que respalda |
|---|---|---|
| `F0_caso_base_red.pdf` | Buses del caso base en toda la red: jornadas sin batería, después de la carga reactiva (jornadas partidas) y con los buses de reserva que cumplen el ciclo diario. El color identifica el escenario. | Caso base: 8.654 -> 11.259 -> 13.247 buses; Caso base con interlining: 7.366 -> 10.295 -> 12.502 buses |
| `F1_metodologia.pdf` | Metodología en cinco etapas en secuencia. El caso base no es una etapa: toma las jornadas de la Etapa 2 y les aplica la carga reactiva; es la línea base con que se comparan las propuestas. | - |
| `F2_gantt_jornada.pdf` | Un mismo grupo de viajes en el caso base con interlining, donde la jornada se parte y el primer bus queda detenido el resto del día, y en la Etapa 3, donde el bus vuelve al patio, recarga y sale con otro tramo. Las cargas nocturnas terminan pasada la medianoche porque de noche los puestos están llenos. | jornada 5039 (elegida entre 2 con el mismo patrón, la de corte más cercano a la mediana): en el caso base el bus 1 vuelve al patio a las 16:38 y queda detenido desde las 17:58; en la Etapa 3 el bus A recarga y sale con otro tramo a las 18:25 |
| `F3_escalera_buses.pdf` | Buses de cada escenario en La Reina: operativos más reservas diurnas y nocturnas. La Propuesta completa es el modelo detallado con bloques de 15 min. | buses totales: Caso base 2.045; Caso base con interlining 1.953; Propuesta con carga por orden de llegada 1.638; Propuesta completa 1.383 |
| `F4_costo_total.pdf` | Costo total por componente en La Reina (cifra sobre cada barra, en miles de USD por día); el rombo marca el costo total con espera nocturna. | costo total: Caso base 594.602 USD/día (con espera nocturna 610.052); Caso base con interlining 567.807 USD/día (con espera nocturna 583.741); Propuesta con carga por orden de llegada 488.464 USD/día (con espera nocturna 497.774); Propuesta completa 424.300 USD/día (con espera nocturna 432.525) |
| `F5_ocupacion_24h.pdf` | Buses cargando a lo largo del día en La Reina frente a los 100 puestos; en gris, los tramos de tarifa punta. La Propuesta completa es la ejecución minuto a minuto del modelo detallado. | horas con todos los puestos ocupados: Caso base con interlining 17,1 h; Propuesta con carga por orden de llegada 15,1 h; Propuesta completa 16,4 h; máximo de la Propuesta completa en la ejecución minuto a minuto: 115 buses |
| `F6_sensibilidades.pdf` | Sensibilidad con el modelo agregado: holgura de recarga de la Etapa 3 (arriba; buses operativos y reservas) y largo del bloque de la Etapa 4 (abajo; costo de energía más reservas y tiempo de cómputo del LP más el MILP). | holgura 0/30/60 min: 1.384/1.399/1.409 buses y 218/203/190 reservas; bloque 5/15/30 min: 101.148/100.905/100.681 USD/día en 102/98/15 s (LP + MILP) |

## Herramientas y equipo

- Python 3.11.9; Gurobi 13.0.2 (gurobipy, licencia academica); scipy 1.15.3 (HiGHS); pandas 2.2.3; numpy 2.1.1; matplotlib 3.9.2.
- Equipo: Intel(R) Core(TM) i5-1035G4 CPU @ 1.10GHz, 4 nucleos y 8 hilos; Windows 11.

## Definiciones y supuestos que hay que tener presentes al analizar

- La Propuesta con carga por orden de llegada y la Propuesta completa usan las mismas ventanas de la Etapa 3: la diferencia entre ellas es solo la programacion de la carga.
- Del Caso base con interlining a la Propuesta con carga por orden de llegada se cambia la carga reactiva por la Etapa 3 (cortes + re-encadenamiento con recarga completa en el patio).
- Parte de la mejora de la Etapa 3 viene de permitir que un bus vuelva al patio y salga de nuevo (paso ii del diagnostico), algo que ni las jornadas sin bateria ni el caso base permiten.
- Reserva: si la carga de una ventana no termina antes de la siguiente salida del bus, un bus ya cargado cubre esa salida (250 USD). En una ventana diurna la reserva toma el resto de la cadena (supuesto conservador).
- La Etapa 3 no ve los puestos; la holgura de recarga los anticipa. La Etapa 4 decide con los puestos y la tarifa.
- Los modelos de la Etapa 4 escriben la capacidad en energia por bloque: es exacta salvo en los bloques de borde ('minutos sobre los puestos', en la ejecucion minuto a minuto, mide ese error). Solo la carga por orden de llegada es exacta al minuto.
- Limitaciones: un solo electroterminal; recarga completa entre tramos; deadhead euclidiano; un dia tipo; flujo de un dia (no ciclico).
