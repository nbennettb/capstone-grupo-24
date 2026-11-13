# Resumen para analisis: instancia La Reina

Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de `results/instancia_LR/`. Escenarios: **Caso base** (jornadas por linea + carga reactiva); **Caso base con interlining** (lo mismo, con interlining en las jornadas); **Propuesta con carga por orden de llegada** (Etapa 3 + carga por orden de llegada); **Propuesta completa** (Etapa 3 + Etapa 4, programa de carga exacto al minuto). Cada escalon cambia una sola cosa.

## 1. Instancia y parametros

- Electroterminal **La Reina** completo: 100 puestos de carga; jornadas sin bateria (Etapa 2): Caso base 1,333, Caso base con interlining 1,203; 1,203 jornadas del Caso base con interlining de entrada a la Etapa 3.
- Energia a reponer en las propuestas / capacidad de 24 h de los puestos: 79.5%.
- Bateria util entre cargas 315 kWh (ciclo al 100%, minimo 10%); carga a 180 kW; consumo 1.4 kWh/km.
- Costos: bus 250 USD/dia (igual para una reserva), km vacio 0.5 USD, espera 0.03 USD/min, evento de carga 5 USD.
- Tarifa (USD/kWh): 00-08 h = 0.10, 08-14 h = 0.15, 14-17 h = 0.22, 17-19 h = 0.15, 19-22 h = 0.22, 22-24 h = 0.11.
- Deadhead: euclidiana x 1.3 a 20 km/h; layover 3 min.
- Etapa 3: regla de corte min_tramos_km (minimos tramos, luego minimos km extra); holgura de recarga base 0 min; sensibilidad [0, 30, 60] min.
- Etapa 4: largo del bloque base 15 min (sensibilidad [5, 15, 30] min); Gurobi, brecha 0.5%, limite 600 s el modelo relajado y 3600 s el detallado; deficit penalizado con 10,000 USD/kWh; desempate 1e-06 USD/kWh por bloque desde la llegada.

## 2. Validaciones (re-verificadas desde los CSV)

| validacion                                                                                                                                                         | resultado   | detalle                                                                                                                                                       |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Caso base: igual a la red completa filtrada                                                                                                                        | OK          | 1,726 jornadas finales y 319 reservas (red completa filtrada: 1,726 y 319)                                                                                    |
| Caso base: deficit de energia 0                                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                     |
| Caso base con interlining: igual a la red completa filtrada                                                                                                        | OK          | 1,638 jornadas finales y 315 reservas (red completa filtrada: 1,638 y 315)                                                                                    |
| Caso base con interlining: deficit de energia 0                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                     |
| Etapa 3 (holgura de recarga 0 min): cobertura exacta                                                                                                               | OK          | 10,327 expediciones en 1,640 tramos                                                                                                                           |
| Etapa 3 (holgura de recarga 0 min): todo tramo cabe en la bateria util                                                                                             | OK          | maximo 314.9 kWh de 315                                                                                                                                       |
| Etapa 3 (holgura de recarga 0 min): flota = maximo de intervalos superpuestos                                                                                      | OK          | flujo 1,166, intervalos 1,166                                                                                                                                 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): deficit 0                                                                                             | OK          | orden de llegada 0.000 kWh, modelo relajado 0.000 kWh                                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): ocupacion <= 100 por bloque (modelo relajado) y por minuto (orden de llegada)                         | OK          | maximo del modelo relajado por bloque 100.00; orden de llegada por minuto 100; ejecucion minuto a minuto del modelo relajado: 108 min sobre 100 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo relajado <= orden de llegada (energia + reservas)                                              | OK          | 100,905.49 <= 157,504.72 USD                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, deficit 0                                                                         | OK          | 0.000 kWh                                                                                                                                                     |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, buses cargando <= 100 en cada minuto                                              | OK          | maximo 100                                                                                                                                                    |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 1. Buses cargando por minuto <= puestos                                                | OK          | maximo 100 de 100; puestos con dos buses a la vez en algun minuto: 0                                                                                          |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 2. Cada carga: minutos enteros, puesto existente, <= 180 kW                            | OK          | 2,274 cargas en 100 puestos                                                                                                                                   |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 3. Toda carga con el bus en el patio; si termina despues de su salida, hay reserva     | OK          | cargas fuera de [llegada, llegada + 24 h): 0; ventanas que terminan tarde: 225, sin reserva: 0                                                                |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 4. Cada ventana repone la energia de su tramo; ningun tramo supera la bateria util     | OK          | diferencia maxima 5.68e-14 kWh; tramo mas largo 314.9 de 315 kWh                                                                                              |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 5. Simulando 7 dias, cada salida tiene un bus cargado (buses de la Etapa 3 + reservas) | OK          | 1,166 buses + 225 reservas = 1,391 buses; salidas sin bus: 0                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 6. Energia y reservas recalculadas = informadas                                        | OK          | energia 46,423.54 USD (informada 46,423.54); reservas 225 (informadas 225)                                                                                    |

## 3. KPIs por escenario

Costo total = sin la espera nocturna en el patio (la metrica principal). Costo total con espera nocturna = la espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). En los casos base todas las reservas son nocturnas: si una carga diurna no alcanza, la jornada se parte y el bus nuevo queda en 'operativos'. La Propuesta completa es el programa de carga exacto al minuto.

| KPI                                                                                   | Caso base   | Caso base con interlining   | Propuesta con carga por orden de llegada   | Propuesta completa   |
|:--------------------------------------------------------------------------------------|:------------|:----------------------------|:-------------------------------------------|:---------------------|
| 1. Costo total (USD/dia)                                                              | 594,602     | 567,807                     | 480,965                                    | 429,303              |
| 1. Costo total con espera nocturna (USD/dia)                                          | 610,052     | 583,741                     | 490,275                                    | 437,796              |
| · flota                                                                               | 431,500     | 409,500                     | 291,500                                    | 291,500              |
| · reservas diurnas                                                                    | 0           | 0                           | 0                                          | 0                    |
| · reservas nocturnas                                                                  | 79,750      | 78,750                      | 110,500                                    | 56,250               |
| · km vacios                                                                           | 20,240      | 18,699                      | 17,465                                     | 17,465               |
| · espera                                                                              | 6,286       | 5,146                       | 6,295                                      | 6,295                |
| · espera, con la espera nocturna                                                      | 21,736      | 21,080                      | 15,605                                     | 14,788               |
| · energia                                                                             | 48,151      | 47,482                      | 47,005                                     | 46,424               |
| · eventos de carga                                                                    | 8,675       | 8,230                       | 8,200                                      | 11,370               |
| 2. N de buses (operativos + reservas)                                                 | 2,045       | 1,953                       | 1,608                                      | 1,391                |
| · buses de las jornadas sin bateria                                                   | 1,333       | 1,203                       | 1,203                                      | 1,203                |
| · buses operativos (tras la carga en los casos base; de la Etapa 3 en las propuestas) | 1,726       | 1,638                       | 1,166                                      | 1,166                |
| 3. % km de deadheading                                                                | 16.14       | 15.10                       | 14.25                                      | 14.25                |
| 4. Costo medio de la energia (USD/kWh)                                                | 0.1372      | 0.1369                      | 0.1369                                     | 0.1352               |
| 4. % de la energia en valle                                                           | 50.9        | 51.6                        | 52.1                                       | 52.1                 |
| 5. Buses extra por bateria                                                            | 712         | 750                         | 405                                        | 188                  |
| 6. Reservas diurnas                                                                   | 0           | 0                           | 0                                          | 0                    |
| 6. Reservas nocturnas                                                                 | 319         | 315                         | 442                                        | 225                  |
| 7. Uso maximo de los puestos (%)                                                      | 100.0       | 100.0                       | 100.0                                      | 100.0                |
| · maximo de buses cargando a la vez (minuto a minuto)                                 | 100.0       | 100.0                       | 100.0                                      | 100.0                |
| 7. Horas con todos los puestos ocupados                                               | 17.0        | 17.1                        | 15.1                                       | 17.1                 |
| · minutos sobre los puestos                                                           | 0           | 0                           | 0                                          | 0                    |
| 8. Segundos de computo (sin la Etapa 2)                                               | 0.7         | 0.7                         | 1.6                                        | 235.1                |
| · energia cargada (MWh)                                                               | 351.1       | 346.7                       | 343.3                                      | 343.3                |
| · deficit de energia (kWh)                                                            | 0.00        | 0.00                        | 0.00                                       | 0.00                 |
| · eventos de carga                                                                    | 1,735       | 1,646                       | 1,640                                      | 2,274                |
| · utilizacion del bus (% de 24 h con pasajeros)                                       | 27.3        | 28.6                        | 34.8                                       | 40.2                 |

### Variantes (sensibilidad y modelo relajado)

| escenario          | variante        | modelo   |   buses_operativos |   reservas_diurnas |   reservas_nocturnas |   buses_totales |   costo_energia |   costo_eventos |   costo_total |   costo_total_con_espera_nocturna |
|:-------------------|:----------------|:---------|-------------------:|-------------------:|---------------------:|----------------:|----------------:|----------------:|--------------:|----------------------------------:|
| Propuesta completa | modelo relajado | agregado |               1166 |                  0 |                  218 |            1384 |           46405 |           29430 |        445595 |                            449759 |

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
| Propuesta con carga por orden de llegada |                  0 |                  442 |        442 |
| Propuesta completa                       |                  0 |                  225 |        225 |

## 6. Energia por tramo horario (kWh y USD)

| tramo horario   |   precio_usd_kwh |   kWh Caso base |   kWh Caso base con interlining |   kWh Propuesta con carga por orden de llegada |   kWh Propuesta completa |   USD Caso base |   USD Caso base con interlining |   USD Propuesta con carga por orden de llegada |   USD Propuesta completa |
|:----------------|-----------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|
| 00-08 h         |             0.1  |          143053 |                          143012 |                                         142986 |                   142960 |           14305 |                           14301 |                                          14299 |                    14296 |
| 08-14 h         |             0.15 |          103026 |                           99886 |                                          99142 |                    99528 |           15454 |                           14983 |                                          14871 |                    14929 |
| 14-17 h         |             0.22 |            7273 |                            6779 |                                           8980 |                      882 |            1600 |                            1491 |                                           1976 |                      194 |
| 17-19 h         |             0.15 |           10975 |                           10196 |                                           6975 |                    14925 |            1646 |                            1529 |                                           1046 |                     2239 |
| 19-22 h         |             0.22 |           50962 |                           51102 |                                          49460 |                    49241 |           11212 |                           11243 |                                          10881 |                    10833 |
| 22-24 h         |             0.11 |           35767 |                           35765 |                                          35743 |                    35750 |            3934 |                            3934 |                                           3932 |                     3933 |

## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)

Puestos: 100. Propuesta completa = ejecucion minuto a minuto del programa de carga exacto al minuto.

|   hora |   Caso base (promedio) |   Caso base (maximo) |   Caso base + interlining (promedio) |   Caso base + interlining (maximo) |   Propuesta, carga por llegada (promedio) |   Propuesta, carga por llegada (maximo) |   Propuesta completa (promedio) |   Propuesta completa (maximo) |
|-------:|-----------------------:|---------------------:|-------------------------------------:|-----------------------------------:|------------------------------------------:|----------------------------------------:|--------------------------------:|------------------------------:|
|      0 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |
|      1 |                  100   |                  100 |                                100   |                                100 |                                      99.9 |                                     100 |                           100   |                           100 |
|      2 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |
|      3 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |
|      4 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |
|      5 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |
|      6 |                  100   |                  100 |                                100   |                                100 |                                      99.8 |                                     100 |                           100   |                           100 |
|      7 |                  100   |                  100 |                                100   |                                100 |                                      99.8 |                                     100 |                           100   |                           100 |
|      8 |                   99.8 |                  100 |                                 99.8 |                                100 |                                      98.8 |                                     100 |                           100   |                           100 |
|      9 |                   99.4 |                  100 |                                 99.7 |                                100 |                                      98.9 |                                     100 |                           100   |                           100 |
|     10 |                   99.7 |                  100 |                                100   |                                100 |                                      99.5 |                                     100 |                           100   |                           100 |
|     11 |                  100   |                  100 |                                100   |                                100 |                                      99.6 |                                     100 |                           100   |                           100 |
|     12 |                   99.9 |                  100 |                                100   |                                100 |                                      98.8 |                                     100 |                            98.8 |                           100 |
|     13 |                   79.4 |                  100 |                                 61.2 |                                100 |                                      60.2 |                                      90 |                            58.7 |                            86 |
|     14 |                   21.4 |                   41 |                                 10.8 |                                 20 |                                      17.1 |                                      26 |                             3.4 |                             5 |
|     15 |                   10.3 |                   11 |                                 10.8 |                                 13 |                                      17.7 |                                      20 |                             1.1 |                             5 |
|     16 |                    9.2 |                   15 |                                 16.2 |                                 24 |                                      15.5 |                                      20 |                             0.4 |                             2 |
|     17 |                   25.6 |                   34 |                                 23.6 |                                 28 |                                      18.5 |                                      22 |                            59.7 |                            69 |
|     18 |                   35.6 |                   55 |                                 33.2 |                                 56 |                                      20.5 |                                      41 |                            23.8 |                            41 |
|     19 |                   84.6 |                  100 |                                 85.5 |                                100 |                                      76.3 |                                     100 |                            76.3 |                           100 |
|     20 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |
|     21 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                            98.8 |                           100 |
|     22 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |
|     23 |                  100   |                  100 |                                100   |                                100 |                                     100   |                                     100 |                           100   |                           100 |

## 8. Sensibilidad a la holgura de recarga de la Etapa 3 (modelo relajado, largo del bloque base)

|   holgura_de_recarga_min |   buses_etapa3 |   reservas_carga_por_llegada |   reservas_propuesta_completa |   buses_totales_carga_por_llegada |   buses_totales_propuesta_completa |   costo_total_propuesta_completa |   costo_energia_propuesta_completa |   nocturnas_sin_tiempo_carga |
|-------------------------:|---------------:|-----------------------------:|------------------------------:|----------------------------------:|-----------------------------------:|---------------------------------:|-----------------------------------:|-----------------------------:|
|                        0 |           1166 |                          442 |                           218 |                              1608 |                               1384 |                           445595 |                              46405 |                           53 |

## 9. Sensibilidad al largo del bloque (modelo relajado, holgura de recarga base)

|   largo_del_bloque_min |   objetivo_usd |   cota_lp_usd |   reservas |   costo_energia |   eventos |   minutos_sobre_puestos |   variables |   segundos_lp |   segundos_milp |   brecha | estado                 |
|-----------------------:|---------------:|--------------:|-----------:|----------------:|----------:|------------------------:|------------:|--------------:|----------------:|---------:|:-----------------------|
|                     15 |         100905 |        100139 |        218 |         46405.5 |      5886 |                     108 |      163962 |          2.08 |           23.81 | 0.003383 | optimo (brecha pedida) |

## 10. Segundos, estado y brecha de cada modelo

La Etapa 2 (jornadas sin bateria) no se vuelve a correr: sus jornadas son un archivo.

| corrida                                                                                                  | estado                        | brecha   | fuente_brecha   |   segundos |
|:---------------------------------------------------------------------------------------------------------|:------------------------------|:---------|:----------------|-----------:|
| Caso base (simulador reactivo)                                                                           | -                             | -        | -               |       0.7  |
| Caso base con interlining (simulador reactivo)                                                           | -                             | -        | -               |       0.7  |
| Etapa 3 (holgura de recarga 0 min) (DP + flujo)                                                          | optimo (flujo entero)         | 0        | flujo entero    |       1.3  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta con carga por orden de llegada    | heuristica (sin optimizacion) | nan      | -               |       0.25 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado, LP (cota)                  | optimo                        | 0.0      | Gurobi          |       2.08 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado (MILP)                      | optimo (brecha pedida)        | 0.003383 | Gurobi          |      23.81 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, arranque                   | factible                      | nan      | -               |      12.5  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, MILP                       | optimo (brecha pedida)        | 0.002361 | Gurobi          |     158.7  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, final (energia + reservas) | entero y validado             | 0.020487 | Gurobi          |     207.9  |

## 11. Propuesta completa: plan de carga y distancia al optimo

Como se obtiene: (1) el modelo relajado (bloques de 15 min, sin mirar minuto a minuto) elige las reservas de partida y da una cota inferior del costo; (2) un MILP al minuto decide las reservas y cuando carga cada bus, sin superar nunca los puestos; (3) a cada carga se le asigna un puesto; (4) 15- valida el plan por separado.

- Energia + reservas: 102,674 USD/dia, con 225 reservas.
- Cota inferior (modelo relajado): 100,570 USD/dia. El plan esta a lo mas a 2.05% del optimo (en energia + reservas).
- MILP al minuto: optimo (brecha pedida), brecha de Gurobi 0.24%, 159 s; 1,198,436 variables.
- Maximo de buses cargando a la vez: 100 de 100; eventos de carga: 2,274 (1.39 por ventana).
- Tiempo total de la Etapa 4 (relajado + exacto): ver seccion 10.

## Figuras del informe

En `informe/`, cada una en PDF (vectorial, para LaTeX), PNG y CSV con sus datos. Ancho pensado para 0.8 del ancho de texto de LaTeX, letra de 9 pt, sin titulo en la imagen (va en el caption).

| Figura | Caption propuesto | Cifra principal que respalda |
|---|---|---|
| `F0_caso_base_red.pdf` | Buses del caso base en toda la red: jornadas sin batería, después de la carga reactiva (jornadas partidas) y con los buses de reserva que cumplen el ciclo diario. El color identifica el escenario. | Caso base: 8.654 -> 11.259 -> 13.247 buses; Caso base con interlining: 7.366 -> 10.295 -> 12.502 buses |
| `F1_metodologia.pdf` | Metodología en cinco etapas en secuencia. El caso base no es una etapa: toma las jornadas de la Etapa 2 y les aplica la carga reactiva; es la línea base con que se comparan las propuestas. | - |
| `F2_gantt_jornada.pdf` | Un mismo grupo de viajes en el caso base con interlining, donde la jornada se parte y el primer bus queda detenido el resto del día, y en la Etapa 3, donde el bus vuelve al patio, recarga y sale con otro tramo. Las cargas nocturnas terminan pasada la medianoche porque de noche los puestos están llenos. | jornada 5039 (elegida entre 2 con el mismo patrón, la de corte más cercano a la mediana): en el caso base el bus 1 vuelve al patio a las 16:38 y queda detenido desde las 17:58; en la Etapa 3 el bus A recarga y sale con otro tramo a las 18:25 |
| `F3_escalera_buses.pdf` | Buses de cada escenario en La Reina: operativos más reservas diurnas y nocturnas. La Propuesta completa es el plan de carga exacto al minuto. | buses totales: Caso base 2.045; Caso base con interlining 1.953; Propuesta con carga por orden de llegada 1.608; Propuesta completa 1.391 |
| `F4_costo_total.pdf` | Costo total por componente en La Reina (cifra sobre cada barra, en miles de USD por día); el rombo marca el costo total con espera nocturna. | costo total: Caso base 594.602 USD/día (con espera nocturna 610.052); Caso base con interlining 567.807 USD/día (con espera nocturna 583.741); Propuesta con carga por orden de llegada 480.965 USD/día (con espera nocturna 490.275); Propuesta completa 429.303 USD/día (con espera nocturna 437.796) |
| `F5_ocupacion_24h.pdf` | Buses cargando a lo largo del día en La Reina frente a los 100 puestos; en gris, los tramos de tarifa punta. | horas con todos los puestos ocupados: Caso base con interlining 17,1 h; Propuesta con carga por orden de llegada 15,1 h; Propuesta completa 17,1 h; máximo de buses cargando a la vez en la Propuesta completa:100 buses |

## Herramientas y equipo

- Python 3.11.9; Gurobi 13.0.2 (gurobipy, licencia academica); scipy 1.17.1 (HiGHS); pandas 3.0.6; numpy 2.4.6; matplotlib 3.11.2.
- Equipo: Intel(R) Core(TM) i5-1035G4 CPU @ 1.10GHz, 4 nucleos y 8 hilos; Windows 11.

## Definiciones y supuestos que hay que tener presentes al analizar

- La Propuesta con carga por orden de llegada y la Propuesta completa usan las mismas ventanas de la Etapa 3: la diferencia entre ellas es solo la programacion de la carga.
- Del Caso base con interlining a la Propuesta con carga por orden de llegada se cambia la carga reactiva por la Etapa 3 (cortes + re-encadenamiento con recarga completa en el patio).
- Parte de la mejora de la Etapa 3 viene de permitir que un bus vuelva al patio y salga de nuevo (paso ii del diagnostico), algo que ni las jornadas sin bateria ni el caso base permiten.
- Reserva: si la carga de una ventana no termina antes de la siguiente salida del bus, un bus ya cargado cubre esa salida (250 USD). En una ventana diurna la reserva toma el resto de la cadena (supuesto conservador).
- La Etapa 3 no ve los puestos; la holgura de recarga los anticipa. La Etapa 4 decide con los puestos y la tarifa.
- La Propuesta completa es un plan de carga exacto al minuto: cada bus carga en minutos enteros en un puesto identificado y en ningun minuto cargan mas buses que puestos. El modelo relajado (bloques de 15 min, capacidad en energia) solo elige las reservas de partida y da la cota inferior.
- Limitaciones: un solo electroterminal; recarga completa entre tramos; deadhead euclidiano; un dia tipo; flujo de un dia (no ciclico).
