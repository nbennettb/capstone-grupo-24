# Resumen para analisis: instancia Los Espinos + Santa Rosa

Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de `results/instancia_LESR/`. Escenarios: **Caso base** (jornadas por linea + carga reactiva); **Caso base con interlining** (lo mismo, con interlining en las jornadas); **Propuesta con carga por orden de llegada** (Etapa 3 + carga por orden de llegada); **Propuesta completa** (Etapa 3 + Etapa 4, programa de carga exacto al minuto). Cada escalon cambia una sola cosa.

## 1. Instancia y parametros

- Electroterminal **Los Espinos + Santa Rosa** completo: 270 puestos de carga; jornadas sin bateria (Etapa 2): Caso base 3,789, Caso base con interlining 3,204; 3,204 jornadas del Caso base con interlining de entrada a la Etapa 3.
- Energia a reponer en las propuestas / capacidad de 24 h de los puestos: 84.8%.
- Bateria util entre cargas 315 kWh (ciclo al 100%, minimo 10%); carga a 180 kW; consumo 1.4 kWh/km.
- Costos: bus 250 USD/dia (igual para una reserva), km vacio 0.5 USD, espera 0.03 USD/min, evento de carga 5 USD.
- Tarifa (USD/kWh): 00-08 h = 0.10, 08-14 h = 0.15, 14-17 h = 0.22, 17-19 h = 0.15, 19-22 h = 0.22, 22-24 h = 0.11.
- Deadhead: euclidiana x 1.3 a 20 km/h; layover 3 min.
- Etapa 3: regla de corte min_tramos_km (minimos tramos, luego minimos km extra); holgura de recarga base 0 min; sensibilidad [0, 30, 60] min.
- Etapa 4: largo del bloque base 15 min (sensibilidad [5, 15, 30] min); Gurobi, brecha 0.5%, limite 600 s el modelo relajado y 3600 s el detallado; deficit penalizado con 10,000 USD/kWh; desempate 1e-06 USD/kWh por bloque desde la llegada.

## 2. Validaciones (re-verificadas desde los CSV)

| validacion                                                                                                                                                         | resultado   | detalle                                                                                                                                                       |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Caso base: igual a la red completa filtrada                                                                                                                        | OK          | 5,034 jornadas finales y 1,088 reservas (red completa filtrada: 5,034 y 1,088)                                                                                |
| Caso base: deficit de energia 0                                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                     |
| Caso base con interlining: igual a la red completa filtrada                                                                                                        | OK          | 4,622 jornadas finales y 1,205 reservas (red completa filtrada: 4,622 y 1,205)                                                                                |
| Caso base con interlining: deficit de energia 0                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                     |
| Etapa 3 (holgura de recarga 0 min): cobertura exacta                                                                                                               | OK          | 30,560 expediciones en 4,623 tramos                                                                                                                           |
| Etapa 3 (holgura de recarga 0 min): todo tramo cabe en la bateria util                                                                                             | OK          | maximo 315.0 kWh de 315                                                                                                                                       |
| Etapa 3 (holgura de recarga 0 min): flota = maximo de intervalos superpuestos                                                                                      | OK          | flujo 3,280, intervalos 3,280                                                                                                                                 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): deficit 0                                                                                             | OK          | orden de llegada 0.000 kWh, modelo relajado 0.000 kWh                                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): ocupacion <= 270 por bloque (modelo relajado) y por minuto (orden de llegada)                         | OK          | maximo del modelo relajado por bloque 270.00; orden de llegada por minuto 270; ejecucion minuto a minuto del modelo relajado: 106 min sobre 270 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo relajado <= orden de llegada (energia + reservas)                                              | OK          | 349,843.22 <= 522,068.98 USD                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, deficit 0                                                                         | OK          | 0.000 kWh                                                                                                                                                     |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, buses cargando <= 270 en cada minuto                                              | OK          | maximo 270                                                                                                                                                    |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 1. Buses cargando por minuto <= puestos                                                | OK          | maximo 270 de 270; puestos con dos buses a la vez en algun minuto: 0                                                                                          |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 2. Cada carga: minutos enteros, puesto existente, <= 180 kW                            | OK          | 5,983 cargas en 270 puestos                                                                                                                                   |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 3. Toda carga con el bus en el patio; si termina despues de su salida, hay reserva     | OK          | cargas fuera de [llegada, llegada + 24 h): 0; ventanas que terminan tarde: 880, sin reserva: 0                                                                |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 4. Cada ventana repone la energia de su tramo; ningun tramo supera la bateria util     | OK          | diferencia maxima 5.68e-14 kWh; tramo mas largo 315.0 de 315 kWh                                                                                              |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 5. Simulando 7 dias, cada salida tiene un bus cargado (buses de la Etapa 3 + reservas) | OK          | 3,280 buses + 880 reservas = 4,160 buses; salidas sin bus: 0                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 6. Energia y reservas recalculadas = informadas                                        | OK          | energia 133,690.30 USD (informada 133,690.30); reservas 880 (informadas 880)                                                                                  |

## 3. KPIs por escenario

Costo total = sin la espera nocturna en el patio (la metrica principal). Costo total con espera nocturna = la espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). En los casos base todas las reservas son nocturnas: si una carga diurna no alcanza, la jornada se parte y el bus nuevo queda en 'operativos'. La Propuesta completa es el programa de carga exacto al minuto.

| KPI                                                                                   |        Caso base |   Caso base con interlining |   Propuesta con carga por orden de llegada |   Propuesta completa |
|:--------------------------------------------------------------------------------------|-----------------:|----------------------------:|-------------------------------------------:|---------------------:|
| 1. Costo total (USD/dia)                                                              |      1.78111e+06 |                 1.6961e+06  |                                1.43667e+06 |          1.27509e+06 |
| 1. Costo total con espera nocturna (USD/dia)                                          |      1.83396e+06 |                 1.75243e+06 |                                1.46887e+06 |          1.30428e+06 |
| · flota                                                                               |      1.2585e+06  |                 1.1555e+06  |                           820000           |     820000           |
| · reservas diurnas                                                                    |      0           |                 0           |                                0           |          0           |
| · reservas nocturnas                                                                  | 272000           |            301250           |                           383250           |     220000           |
| · km vacios                                                                           |  61364           |             57195           |                            51285           |      51285           |
| · espera                                                                              |  19218           |             16077           |                            20201           |      20201           |
| · espera, con la espera nocturna                                                      |  72073           |             72401           |                            52400           |      49388           |
| · energia                                                                             | 144781           |            142843           |                           138819           |     133690           |
| · eventos de carga                                                                    |  25245           |             23240           |                            23115           |      29915           |
| 2. N de buses (operativos + reservas)                                                 |   6122           |              5827           |                             4813           |       4160           |
| · buses de las jornadas sin bateria                                                   |   3789           |              3204           |                             3204           |       3204           |
| · buses operativos (tras la carga en los casos base; de la Etapa 3 en las propuestas) |   5034           |              4622           |                             3280           |       3280           |
| 3. % km de deadheading                                                                |     16.89        |                15.92        |                               14.51        |         14.51        |
| 4. Costo medio de la energia (USD/kWh)                                                |      0.1423      |                 0.142       |                                0.1403      |          0.1351      |
| 4. % de la energia en valle                                                           |     47.5         |                48           |                               48.8         |         48.8         |
| 5. Buses extra por bateria                                                            |   2333           |              2623           |                             1609           |        956           |
| 6. Reservas diurnas                                                                   |      0           |                 0           |                                0           |          0           |
| 6. Reservas nocturnas                                                                 |   1088           |              1205           |                             1533           |        880           |
| 7. Uso maximo de los puestos (%)                                                      |    100           |               100           |                              100           |        100           |
| · maximo de buses cargando a la vez (minuto a minuto)                                 |    270           |               270           |                              270           |        270           |
| 7. Horas con todos los puestos ocupados                                               |     18.8         |                19           |                               16.7         |         19.5         |
| · minutos sobre los puestos                                                           |      0           |                 0           |                                0           |          0           |
| 8. Segundos de computo (sin la Etapa 2)                                               |      1.1         |                 1.3         |                                3           |       1597.3         |
| · energia cargada (MWh)                                                               |   1017.6         |              1005.9         |                              989.4         |        989.4         |
| · deficit de energia (kWh)                                                            |      0           |                 0           |                                0           |          0           |
| · eventos de carga                                                                    |   5049           |              4648           |                             4623           |       5983           |
| · utilizacion del bus (% de 24 h con pasajeros)                                       |     25.7         |                27           |                               32.7         |         37.9         |

### Variantes (sensibilidad y modelo relajado)

| escenario          | variante        | modelo   |   buses_operativos |   reservas_diurnas |   reservas_nocturnas |   buses_totales |   costo_energia |   costo_eventos |   costo_total |   costo_total_con_espera_nocturna |
|:-------------------|:----------------|:---------|-------------------:|-------------------:|---------------------:|----------------:|----------------:|----------------:|--------------:|----------------------------------:|
| Propuesta completa | modelo relajado | agregado |               3280 |                  0 |                  867 |            4147 |          133093 |           84570 |    1.3259e+06 |                       1.34213e+06 |

## 4. Diagnostico de flota de la Etapa 3

| paso                             |   buses | que_mide                                                            |
|:---------------------------------|--------:|:--------------------------------------------------------------------|
| (i) Jornadas sin bateria         |    3204 | Punto de partida: una jornada = un bus                              |
| (ii) Reuso del patio sin bateria |    3157 | Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga |
| (iii) Solo cortes                |    4623 | Cada tramo un bus                                                   |
| (iv) Cortes + re-encadenamiento  |    3280 | La Etapa 3 completa (recarga completa + holgura 0 min)              |

- 4,623 tramos desde 3,204 jornadas (1,413 cortadas; 19,164.3 km extra). Ventanas de carga: 1,343 diurnas (entre tramos), 3,280 nocturnas.
- Nocturnas que no alcanzan la recarga completa ni con puesto libre: 194 (de ellas 151 cadenas de mas de 24 h: el flujo, como las jornadas sin bateria, es de un dia y no ciclico). Son reservas que ninguna programacion de carga puede evitar.

## 5. Reservas por tipo

| escenario                                |   reservas_diurnas |   reservas_nocturnas |   reservas |
|:-----------------------------------------|-------------------:|---------------------:|-----------:|
| Caso base                                |                  0 |                 1088 |       1088 |
| Caso base con interlining                |                  0 |                 1205 |       1205 |
| Propuesta con carga por orden de llegada |                  0 |                 1533 |       1533 |
| Propuesta completa                       |                  0 |                  880 |        880 |

## 6. Energia por tramo horario (kWh y USD)

| tramo horario   |   precio_usd_kwh |   kWh Caso base |   kWh Caso base con interlining |   kWh Propuesta con carga por orden de llegada |   kWh Propuesta completa |   USD Caso base |   USD Caso base con interlining |   USD Propuesta con carga por orden de llegada |   USD Propuesta completa |
|:----------------|-----------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|
| 00-08 h         |             0.1  |          386257 |                          386538 |                                         386416 |                   386027 |           38626 |                           38654 |                                          38642 |                    38603 |
| 08-14 h         |             0.15 |          288846 |                          289124 |                                         288331 |                   289342 |           43327 |                           43369 |                                          43250 |                    43401 |
| 14-17 h         |             0.22 |           84339 |                          102491 |                                          84574 |                    11007 |           18555 |                           22548 |                                          18606 |                     2422 |
| 17-19 h         |             0.15 |           26999 |                           17115 |                                          23572 |                    96484 |            4050 |                            2567 |                                           3536 |                    14473 |
| 19-22 h         |             0.22 |          134542 |                          113969 |                                         109775 |                   109801 |           29599 |                           25073 |                                          24151 |                    24156 |
| 22-24 h         |             0.11 |           96588 |                           96660 |                                          96683 |                    96689 |           10625 |                           10633 |                                          10635 |                    10636 |

## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)

Puestos: 270. Propuesta completa = ejecucion minuto a minuto del programa de carga exacto al minuto.

|   hora |   Caso base (promedio) |   Caso base (maximo) |   Caso base + interlining (promedio) |   Caso base + interlining (maximo) |   Propuesta, carga por llegada (promedio) |   Propuesta, carga por llegada (maximo) |   Propuesta completa (promedio) |   Propuesta completa (maximo) |
|-------:|-----------------------:|---------------------:|-------------------------------------:|-----------------------------------:|------------------------------------------:|----------------------------------------:|--------------------------------:|------------------------------:|
|      0 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|      1 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|      2 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|      3 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|      4 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|      5 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|      6 |                  269.8 |                  270 |                                270   |                                270 |                                     269.9 |                                     270 |                           270   |                           270 |
|      7 |                  270   |                  270 |                                270   |                                270 |                                     269.9 |                                     270 |                           270   |                           270 |
|      8 |                  269.8 |                  270 |                                269.4 |                                270 |                                     267.6 |                                     270 |                           270   |                           270 |
|      9 |                  269.8 |                  270 |                                269.9 |                                270 |                                     269.2 |                                     270 |                           270   |                           270 |
|     10 |                  269.8 |                  270 |                                270   |                                270 |                                     269.5 |                                     270 |                           270   |                           270 |
|     11 |                  270   |                  270 |                                270   |                                270 |                                     269.7 |                                     270 |                           270   |                           270 |
|     12 |                  270   |                  270 |                                270   |                                270 |                                     269.8 |                                     270 |                           270   |                           270 |
|     13 |                  270   |                  270 |                                270   |                                270 |                                     269.9 |                                     270 |                           270   |                           270 |
|     14 |                  270   |                  270 |                                270   |                                270 |                                     261   |                                     270 |                            57.2 |                            76 |
|     15 |                  164.9 |                  270 |                                239.1 |                                270 |                                     144.2 |                                     214 |                             4.2 |                            20 |
|     16 |                   39.2 |                   56 |                                 67   |                                133 |                                      68.7 |                                      88 |                             0   |                             0 |
|     17 |                   48.8 |                   70 |                                 46.9 |                                 51 |                                      72.6 |                                      83 |                           270   |                           270 |
|     18 |                  101.7 |                  142 |                                 48.6 |                                 56 |                                      59.3 |                                      68 |                           270   |                           270 |
|     19 |                  211.3 |                  270 |                                105.3 |                                193 |                                      98   |                                     153 |                            98   |                           153 |
|     20 |                  270   |                  270 |                                260.8 |                                270 |                                     245   |                                     270 |                           245   |                           270 |
|     21 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|     22 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |
|     23 |                  270   |                  270 |                                270   |                                270 |                                     270   |                                     270 |                           270   |                           270 |

## 8. Sensibilidad a la holgura de recarga de la Etapa 3 (modelo relajado, largo del bloque base)

|   holgura_de_recarga_min |   buses_etapa3 |   reservas_carga_por_llegada |   reservas_propuesta_completa |   buses_totales_carga_por_llegada |   buses_totales_propuesta_completa |   costo_total_propuesta_completa |   costo_energia_propuesta_completa |   nocturnas_sin_tiempo_carga |
|-------------------------:|---------------:|-----------------------------:|------------------------------:|----------------------------------:|-----------------------------------:|---------------------------------:|-----------------------------------:|-----------------------------:|
|                        0 |           3280 |                         1533 |                           867 |                              4813 |                               4147 |                       1.3259e+06 |                             133093 |                          194 |

## 9. Sensibilidad al largo del bloque (modelo relajado, holgura de recarga base)

|   largo_del_bloque_min |   objetivo_usd |   cota_lp_usd |   reservas |   costo_energia |   eventos |   minutos_sobre_puestos |   variables |   segundos_lp |   segundos_milp |   brecha | estado                 |
|-----------------------:|---------------:|--------------:|-----------:|----------------:|----------:|------------------------:|------------:|--------------:|----------------:|---------:|:-----------------------|
|                     15 |         349843 |        347574 |        867 |          133093 |     16914 |                     106 |      462149 |         11.87 |            46.8 | 0.002841 | optimo (brecha pedida) |

## 10. Segundos, estado y brecha de cada modelo

La Etapa 2 (jornadas sin bateria) no se vuelve a correr: sus jornadas son un archivo.

| corrida                                                                                                  | estado                        | brecha   | fuente_brecha   |   segundos |
|:---------------------------------------------------------------------------------------------------------|:------------------------------|:---------|:----------------|-----------:|
| Caso base (simulador reactivo)                                                                           | -                             | -        | -               |       1.1  |
| Caso base con interlining (simulador reactivo)                                                           | -                             | -        | -               |       1.3  |
| Etapa 3 (holgura de recarga 0 min) (DP + flujo)                                                          | optimo (flujo entero)         | 0        | flujo entero    |       2.5  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta con carga por orden de llegada    | heuristica (sin optimizacion) | nan      | -               |       0.48 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado, LP (cota)                  | optimo                        | 0.0      | Gurobi          |      11.87 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado (MILP)                      | optimo (brecha pedida)        | 0.002841 | Gurobi          |      46.8  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, arranque                   | factible                      | nan      | -               |      80.5  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, MILP                       | optimo (brecha pedida)        | 0.002176 | Gurobi          |    1185.2  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, final (energia + reservas) | entero y validado             | 0.01363  | Gurobi          |    1536.1  |

## 11. Propuesta completa: plan de carga y distancia al optimo

Como se obtiene: (1) el modelo relajado (bloques de 15 min, sin mirar minuto a minuto) elige las reservas de partida y da una cota inferior del costo; (2) un MILP al minuto decide las reservas y cuando carga cada bus, sin superar nunca los puestos; (3) a cada carga se le asigna un puesto; (4) 15- valida el plan por separado.

- Energia + reservas: 353,690 USD/dia, con 880 reservas.
- Cota inferior (modelo relajado): 348,870 USD/dia. El plan esta a lo mas a 1.36% del optimo (en energia + reservas).
- MILP al minuto: optimo (brecha pedida), brecha de Gurobi 0.22%, 1,185 s; 3,688,387 variables.
- Maximo de buses cargando a la vez: 270 de 270; eventos de carga: 5,983 (1.29 por ventana).
- Tiempo total de la Etapa 4 (relajado + exacto): ver seccion 10.

## Figuras del informe

En `informe/`, cada una en PDF (vectorial, para LaTeX), PNG y CSV con sus datos. Ancho pensado para 0.8 del ancho de texto de LaTeX, letra de 9 pt, sin titulo en la imagen (va en el caption).

| Figura | Caption propuesto | Cifra principal que respalda |
|---|---|---|
| `F0_caso_base_red.pdf` | Buses del caso base en toda la red: jornadas sin batería, después de la carga reactiva (jornadas partidas) y con los buses de reserva que cumplen el ciclo diario. El color identifica el escenario. | Caso base: 8.654 -> 11.259 -> 13.247 buses; Caso base con interlining: 7.366 -> 10.295 -> 12.502 buses |
| `F1_metodologia.pdf` | Metodología en cinco etapas en secuencia. El caso base no es una etapa: toma las jornadas de la Etapa 2 y les aplica la carga reactiva; es la línea base con que se comparan las propuestas. | - |
| `F3_escalera_buses.pdf` | Buses de cada escenario en Los Espinos + Santa Rosa: operativos más reservas diurnas y nocturnas. La Propuesta completa es el plan de carga exacto al minuto. | buses totales: Caso base 6.122; Caso base con interlining 5.827; Propuesta con carga por orden de llegada 4.813; Propuesta completa 4.160 |
| `F4_costo_total.pdf` | Costo total por componente en Los Espinos + Santa Rosa (cifra sobre cada barra, en miles de USD por día); el rombo marca el costo total con espera nocturna. | costo total: Caso base 1.781.108 USD/día (con espera nocturna 1.833.963); Caso base con interlining 1.696.105 USD/día (con espera nocturna 1.752.429); Propuesta con carga por orden de llegada 1.436.670 USD/día (con espera nocturna 1.468.869); Propuesta completa 1.275.091 USD/día (con espera nocturna 1.304.278) |
| `F5_ocupacion_24h.pdf` | Buses cargando a lo largo del día en Los Espinos + Santa Rosa frente a los 270 puestos; en gris, los tramos de tarifa punta. | horas con todos los puestos ocupados: Caso base con interlining 19,0 h; Propuesta con carga por orden de llegada 16,7 h; Propuesta completa 19,5 h; máximo de buses cargando a la vez en la Propuesta completa:270 buses |

## Herramientas y equipo

- Python 3.11.9; Gurobi 13.0.1 (gurobipy, licencia academica); scipy 1.15.3 (HiGHS); pandas 2.2.2; numpy 2.2.6; matplotlib 3.9.2.
- Equipo: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 8 nucleos y 16 hilos; Windows 11.

## Definiciones y supuestos que hay que tener presentes al analizar

- La Propuesta con carga por orden de llegada y la Propuesta completa usan las mismas ventanas de la Etapa 3: la diferencia entre ellas es solo la programacion de la carga.
- Del Caso base con interlining a la Propuesta con carga por orden de llegada se cambia la carga reactiva por la Etapa 3 (cortes + re-encadenamiento con recarga completa en el patio).
- Parte de la mejora de la Etapa 3 viene de permitir que un bus vuelva al patio y salga de nuevo (paso ii del diagnostico), algo que ni las jornadas sin bateria ni el caso base permiten.
- Reserva: si la carga de una ventana no termina antes de la siguiente salida del bus, un bus ya cargado cubre esa salida (250 USD). En una ventana diurna la reserva toma el resto de la cadena (supuesto conservador).
- La Etapa 3 no ve los puestos; la holgura de recarga los anticipa. La Etapa 4 decide con los puestos y la tarifa.
- La Propuesta completa es un plan de carga exacto al minuto: cada bus carga en minutos enteros en un puesto identificado y en ningun minuto cargan mas buses que puestos. El modelo relajado (bloques de 15 min, capacidad en energia) solo elige las reservas de partida y da la cota inferior.
- Limitaciones: un solo electroterminal; recarga completa entre tramos; deadhead euclidiano; un dia tipo; flujo de un dia (no ciclico).
