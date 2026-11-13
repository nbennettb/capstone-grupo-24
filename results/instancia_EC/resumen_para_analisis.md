# Resumen para analisis: instancia El Conquistador

Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de `results/instancia_EC/`. Escenarios: **Caso base** (jornadas por linea + carga reactiva); **Caso base con interlining** (lo mismo, con interlining en las jornadas); **Propuesta con carga por orden de llegada** (Etapa 3 + carga por orden de llegada); **Propuesta completa** (Etapa 3 + Etapa 4, programa de carga exacto al minuto). Cada escalon cambia una sola cosa.

## 1. Instancia y parametros

- Electroterminal **El Conquistador** completo: 180 puestos de carga; jornadas sin bateria (Etapa 2): Caso base 2,643, Caso base con interlining 2,166; 2,166 jornadas del Caso base con interlining de entrada a la Etapa 3.
- Energia a reponer en las propuestas / capacidad de 24 h de los puestos: 81.9%.
- Bateria util entre cargas 315 kWh (ciclo al 100%, minimo 10%); carga a 180 kW; consumo 1.4 kWh/km.
- Costos: bus 250 USD/dia (igual para una reserva), km vacio 0.5 USD, espera 0.03 USD/min, evento de carga 5 USD.
- Tarifa (USD/kWh): 00-08 h = 0.10, 08-14 h = 0.15, 14-17 h = 0.22, 17-19 h = 0.15, 19-22 h = 0.22, 22-24 h = 0.11.
- Deadhead: euclidiana x 1.3 a 20 km/h; layover 3 min.
- Etapa 3: regla de corte min_tramos_km (minimos tramos, luego minimos km extra); holgura de recarga base 0 min; sensibilidad [0, 30, 60] min.
- Etapa 4: largo del bloque base 15 min (sensibilidad [5, 15, 30] min); Gurobi, brecha 0.5%, limite 600 s el modelo relajado y 3600 s el detallado; deficit penalizado con 10,000 USD/kWh; desempate 1e-06 USD/kWh por bloque desde la llegada.

## 2. Validaciones (re-verificadas desde los CSV)

| validacion                                                                                                                                                         | resultado   | detalle                                                                                                                                                      |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Caso base: igual a la red completa filtrada                                                                                                                        | OK          | 3,396 jornadas finales y 574 reservas (red completa filtrada: 3,396 y 574)                                                                                   |
| Caso base: deficit de energia 0                                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                    |
| Caso base con interlining: igual a la red completa filtrada                                                                                                        | OK          | 3,000 jornadas finales y 684 reservas (red completa filtrada: 3,000 y 684)                                                                                   |
| Caso base con interlining: deficit de energia 0                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                    |
| Etapa 3 (holgura de recarga 0 min): cobertura exacta                                                                                                               | OK          | 16,386 expediciones en 3,003 tramos                                                                                                                          |
| Etapa 3 (holgura de recarga 0 min): todo tramo cabe en la bateria util                                                                                             | OK          | maximo 315.0 kWh de 315                                                                                                                                      |
| Etapa 3 (holgura de recarga 0 min): flota = maximo de intervalos superpuestos                                                                                      | OK          | flujo 2,137, intervalos 2,137                                                                                                                                |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): deficit 0                                                                                             | OK          | orden de llegada 0.000 kWh, modelo relajado 0.000 kWh                                                                                                        |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): ocupacion <= 180 por bloque (modelo relajado) y por minuto (orden de llegada)                         | OK          | maximo del modelo relajado por bloque 180.00; orden de llegada por minuto 180; ejecucion minuto a minuto del modelo relajado: 95 min sobre 180 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo relajado <= orden de llegada (energia + reservas)                                              | OK          | 209,987.95 <= 325,642.81 USD                                                                                                                                 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, deficit 0                                                                         | OK          | 0.000 kWh                                                                                                                                                    |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, buses cargando <= 180 en cada minuto                                              | OK          | maximo 180                                                                                                                                                   |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 1. Buses cargando por minuto <= puestos                                                | OK          | maximo 180 de 180; puestos con dos buses a la vez en algun minuto: 0                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 2. Cada carga: minutos enteros, puesto existente, <= 180 kW                            | OK          | 3,996 cargas en 180 puestos                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 3. Toda carga con el bus en el patio; si termina despues de su salida, hay reserva     | OK          | cargas fuera de [llegada, llegada + 24 h): 0; ventanas que terminan tarde: 505, sin reserva: 0                                                               |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 4. Cada ventana repone la energia de su tramo; ningun tramo supera la bateria util     | OK          | diferencia maxima 5.68e-14 kWh; tramo mas largo 315.0 de 315 kWh                                                                                             |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 5. Simulando 7 dias, cada salida tiene un bus cargado (buses de la Etapa 3 + reservas) | OK          | 2,137 buses + 505 reservas = 2,642 buses; salidas sin bus: 0                                                                                                 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 6. Energia y reservas recalculadas = informadas                                        | OK          | energia 86,517.56 USD (informada 86,517.56); reservas 505 (informadas 505)                                                                                   |

## 3. KPIs por escenario

Costo total = sin la espera nocturna en el patio (la metrica principal). Costo total con espera nocturna = la espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). En los casos base todas las reservas son nocturnas: si una carga diurna no alcanza, la jornada se parte y el bus nuevo queda en 'operativos'. La Propuesta completa es el programa de carga exacto al minuto.

| KPI                                                                                   | Caso base   | Caso base con interlining   | Propuesta con carga por orden de llegada   | Propuesta completa   |
|:--------------------------------------------------------------------------------------|:------------|:----------------------------|:-------------------------------------------|:---------------------|
| 1. Costo total (USD/dia)                                                              | 1,154,195   | 1,073,408                   | 920,766                                    | 812,855              |
| 1. Costo total con espera nocturna (USD/dia)                                          | 1,185,165   | 1,105,736                   | 941,497                                    | 831,747              |
| · flota                                                                               | 849,000     | 750,000                     | 534,250                                    | 534,250              |
| · reservas diurnas                                                                    | 0           | 0                           | 0                                          | 250                  |
| · reservas nocturnas                                                                  | 143,500     | 171,000                     | 237,750                                    | 126,000              |
| · km vacios                                                                           | 39,699      | 36,444                      | 33,456                                     | 33,456               |
| · espera                                                                              | 14,236      | 11,380                      | 12,402                                     | 12,402               |
| · espera, con la espera nocturna                                                      | 45,206      | 43,708                      | 33,134                                     | 31,294               |
| · energia                                                                             | 90,680      | 89,514                      | 87,893                                     | 86,518               |
| · eventos de carga                                                                    | 17,080      | 15,070                      | 15,015                                     | 19,980               |
| 2. N de buses (operativos + reservas)                                                 | 3,970       | 3,684                       | 3,088                                      | 2,642                |
| · buses de las jornadas sin bateria                                                   | 2,643       | 2,166                       | 2,166                                      | 2,166                |
| · buses operativos (tras la carga en los casos base; de la Etapa 3 en las propuestas) | 3,396       | 3,000                       | 2,137                                      | 2,137                |
| 3. % km de deadheading                                                                | 16.99       | 15.82                       | 14.71                                      | 14.71                |
| 4. Costo medio de la energia (USD/kWh)                                                | 0.1386      | 0.1388                      | 0.1381                                     | 0.1359               |
| 4. % de la energia en valle                                                           | 49.2        | 49.9                        | 50.5                                       | 50.5                 |
| 5. Buses extra por bateria                                                            | 1,327       | 1,518                       | 922                                        | 476                  |
| 6. Reservas diurnas                                                                   | 0           | 0                           | 0                                          | 1                    |
| 6. Reservas nocturnas                                                                 | 574         | 684                         | 951                                        | 504                  |
| 7. Uso maximo de los puestos (%)                                                      | 100.0       | 100.0                       | 100.0                                      | 100.0                |
| · maximo de buses cargando a la vez (minuto a minuto)                                 | 180.0       | 180.0                       | 180.0                                      | 180.0                |
| 7. Horas con todos los puestos ocupados                                               | 17.8        | 18.1                        | 16.3                                       | 18.0                 |
| · minutos sobre los puestos                                                           | 0           | 0                           | 0                                          | 0                    |
| 8. Segundos de computo (sin la Etapa 2)                                               | 1.4         | 1.4                         | 4.3                                        | 651.6                |
| · energia cargada (MWh)                                                               | 654.1       | 645.0                       | 636.7                                      | 636.7                |
| · deficit de energia (kWh)                                                            | 0.00        | 0.00                        | 0.00                                       | 0.00                 |
| · eventos de carga                                                                    | 3,416       | 3,014                       | 3,003                                      | 3,996                |
| · utilizacion del bus (% de 24 h con pasajeros)                                       | 25.4        | 27.4                        | 32.7                                       | 38.2                 |

### Variantes (sensibilidad y modelo relajado)

| escenario          | variante        | modelo   |   buses_operativos |   reservas_diurnas |   reservas_nocturnas |   buses_totales |   costo_energia |   costo_eventos |   costo_total |   costo_total_con_espera_nocturna |
|:-------------------|:----------------|:---------|-------------------:|-------------------:|---------------------:|----------------:|----------------:|----------------:|--------------:|----------------------------------:|
| Propuesta completa | modelo relajado | agregado |               2137 |                  2 |                  492 |            2631 |           86488 |           54315 |        844411 |                            854732 |

## 4. Diagnostico de flota de la Etapa 3

| paso                             |   buses | que_mide                                                            |
|:---------------------------------|--------:|:--------------------------------------------------------------------|
| (i) Jornadas sin bateria         |    2166 | Punto de partida: una jornada = un bus                              |
| (ii) Reuso del patio sin bateria |    2045 | Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga |
| (iii) Solo cortes                |    3003 | Cada tramo un bus                                                   |
| (iv) Cortes + re-encadenamiento  |    2137 | La Etapa 3 completa (recarga completa + holgura 0 min)              |

- 3,003 tramos desde 2,166 jornadas (835 cortadas; 10,765.0 km extra). Ventanas de carga: 866 diurnas (entre tramos), 2,137 nocturnas.
- Nocturnas que no alcanzan la recarga completa ni con puesto libre: 108 (de ellas 71 cadenas de mas de 24 h: el flujo, como las jornadas sin bateria, es de un dia y no ciclico). Son reservas que ninguna programacion de carga puede evitar.

## 5. Reservas por tipo

| escenario                                |   reservas_diurnas |   reservas_nocturnas |   reservas |
|:-----------------------------------------|-------------------:|---------------------:|-----------:|
| Caso base                                |                  0 |                  574 |        574 |
| Caso base con interlining                |                  0 |                  684 |        684 |
| Propuesta con carga por orden de llegada |                  0 |                  951 |        951 |
| Propuesta completa                       |                  1 |                  504 |        505 |

## 6. Energia por tramo horario (kWh y USD)

| tramo horario   |   precio_usd_kwh |   kWh Caso base |   kWh Caso base con interlining |   kWh Propuesta con carga por orden de llegada |   kWh Propuesta completa |   USD Caso base |   USD Caso base con interlining |   USD Propuesta con carga por orden de llegada |   USD Propuesta completa |
|:----------------|-----------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|
| 00-08 h         |             0.1  |          257366 |                          257516 |                                         257453 |                   257317 |           25737 |                           25752 |                                          25745 |                    25732 |
| 08-14 h         |             0.15 |          191024 |                          192669 |                                         191431 |                   192875 |           28654 |                           28900 |                                          28715 |                    28931 |
| 14-17 h         |             0.22 |           21714 |                           28639 |                                          27208 |                     8034 |            4777 |                            6301 |                                           5986 |                     1767 |
| 17-19 h         |             0.15 |           27108 |                           13160 |                                          11345 |                    29769 |            4066 |                            1974 |                                           1702 |                     4465 |
| 19-22 h         |             0.22 |           92590 |                           88663 |                                          84831 |                    84266 |           20370 |                           19506 |                                          18663 |                    18539 |
| 22-24 h         |             0.11 |           64333 |                           64376 |                                          64385 |                    64393 |            7077 |                            7081 |                                           7082 |                     7083 |

## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)

Puestos: 180. Propuesta completa = ejecucion minuto a minuto del programa de carga exacto al minuto.

|   hora |   Caso base (promedio) |   Caso base (maximo) |   Caso base + interlining (promedio) |   Caso base + interlining (maximo) |   Propuesta, carga por llegada (promedio) |   Propuesta, carga por llegada (maximo) |   Propuesta completa (promedio) |   Propuesta completa (maximo) |
|-------:|-----------------------:|---------------------:|-------------------------------------:|-----------------------------------:|------------------------------------------:|----------------------------------------:|--------------------------------:|------------------------------:|
|      0 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |
|      1 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |
|      2 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |
|      3 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |
|      4 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |
|      5 |                  180   |                  180 |                                180   |                                180 |                                     179.9 |                                     180 |                           180   |                           180 |
|      6 |                  180   |                  180 |                                180   |                                180 |                                     179.9 |                                     180 |                           180   |                           180 |
|      7 |                  180   |                  180 |                                180   |                                180 |                                     179.8 |                                     180 |                           180   |                           180 |
|      8 |                  179.9 |                  180 |                                179.7 |                                180 |                                     179.1 |                                     180 |                           180   |                           180 |
|      9 |                  179.9 |                  180 |                                180   |                                180 |                                     179.4 |                                     180 |                           180   |                           180 |
|     10 |                  179.9 |                  180 |                                179.9 |                                180 |                                     179.6 |                                     180 |                           180   |                           180 |
|     11 |                  180   |                  180 |                                180   |                                180 |                                     179.6 |                                     180 |                           180   |                           180 |
|     12 |                  180   |                  180 |                                180   |                                180 |                                     179.7 |                                     180 |                           180   |                           180 |
|     13 |                  171.1 |                  180 |                                180   |                                180 |                                     175.2 |                                     180 |                           180   |                           180 |
|     14 |                   60.4 |                  124 |                                117   |                                180 |                                      88.2 |                                     146 |                            27.8 |                            42 |
|     15 |                   26.1 |                   33 |                                 25.8 |                                 48 |                                      32   |                                      40 |                            16   |                            25 |
|     16 |                   35.6 |                   45 |                                 18.1 |                                 20 |                                      32.6 |                                      40 |                             1.1 |                             4 |
|     17 |                   56   |                   77 |                                 22.5 |                                 34 |                                      30.9 |                                      38 |                           117.4 |                           158 |
|     18 |                   95.8 |                  114 |                                 50.9 |                                 76 |                                      32.6 |                                      57 |                            49.4 |                            80 |
|     19 |                  158.3 |                  180 |                                135.3 |                                180 |                                     113.9 |                                     180 |                           113.4 |                           180 |
|     20 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |
|     21 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           177.2 |                           180 |
|     22 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |
|     23 |                  180   |                  180 |                                180   |                                180 |                                     180   |                                     180 |                           180   |                           180 |

## 8. Sensibilidad a la holgura de recarga de la Etapa 3 (modelo relajado, largo del bloque base)

|   holgura_de_recarga_min |   buses_etapa3 |   reservas_carga_por_llegada |   reservas_propuesta_completa |   buses_totales_carga_por_llegada |   buses_totales_propuesta_completa |   costo_total_propuesta_completa |   costo_energia_propuesta_completa |   nocturnas_sin_tiempo_carga |
|-------------------------:|---------------:|-----------------------------:|------------------------------:|----------------------------------:|-----------------------------------:|---------------------------------:|-----------------------------------:|-----------------------------:|
|                        0 |           2137 |                          951 |                           494 |                              3088 |                               2631 |                           844411 |                              86488 |                          108 |

## 9. Sensibilidad al largo del bloque (modelo relajado, holgura de recarga base)

|   largo_del_bloque_min |   objetivo_usd |   cota_lp_usd |   reservas |   costo_energia |   eventos |   minutos_sobre_puestos |   variables |   segundos_lp |   segundos_milp |   brecha | estado                 |
|-----------------------:|---------------:|--------------:|-----------:|----------------:|----------:|------------------------:|------------:|--------------:|----------------:|---------:|:-----------------------|
|                     15 |         209988 |        208548 |        494 |         86487.9 |     10863 |                      95 |      300229 |          5.82 |           37.62 | 0.003044 | optimo (brecha pedida) |

## 10. Segundos, estado y brecha de cada modelo

La Etapa 2 (jornadas sin bateria) no se vuelve a correr: sus jornadas son un archivo.

| corrida                                                                                                  | estado                        | brecha   | fuente_brecha   |   segundos |
|:---------------------------------------------------------------------------------------------------------|:------------------------------|:---------|:----------------|-----------:|
| Caso base (simulador reactivo)                                                                           | -                             | -        | -               |       1.4  |
| Caso base con interlining (simulador reactivo)                                                           | -                             | -        | -               |       1.4  |
| Etapa 3 (holgura de recarga 0 min) (DP + flujo)                                                          | optimo (flujo entero)         | 0        | flujo entero    |       3.6  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta con carga por orden de llegada    | heuristica (sin optimizacion) | nan      | -               |       0.71 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado, LP (cota)                  | optimo                        | 0.0      | Gurobi          |       5.82 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado (MILP)                      | optimo (brecha pedida)        | 0.003044 | Gurobi          |      37.62 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, arranque                   | factible                      | nan      | -               |      43.6  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, MILP                       | optimo (brecha pedida)        | 0.003431 | Gurobi          |     458.9  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, final (energia + reservas) | entero y validado             | 0.01601  | Gurobi          |     604.5  |

## 11. Propuesta completa: plan de carga y distancia al optimo

Como se obtiene: (1) el modelo relajado (bloques de 15 min, sin mirar minuto a minuto) elige las reservas de partida y da una cota inferior del costo; (2) un MILP al minuto decide las reservas y cuando carga cada bus, sin superar nunca los puestos; (3) a cada carga se le asigna un puesto; (4) 15- valida el plan por separado.

- Energia + reservas: 212,768 USD/dia, con 505 reservas.
- Cota inferior (modelo relajado): 209,361 USD/dia. El plan esta a lo mas a 1.60% del optimo (en energia + reservas).
- MILP al minuto: optimo (brecha pedida), brecha de Gurobi 0.34%, 459 s; 2,306,668 variables.
- Maximo de buses cargando a la vez: 180 de 180; eventos de carga: 3,996 (1.33 por ventana).
- Tiempo total de la Etapa 4 (relajado + exacto): ver seccion 10.

## Figuras del informe

En `informe/`, cada una en PDF (vectorial, para LaTeX), PNG y CSV con sus datos. Ancho pensado para 0.8 del ancho de texto de LaTeX, letra de 9 pt, sin titulo en la imagen (va en el caption).

| Figura | Caption propuesto | Cifra principal que respalda |
|---|---|---|
| `F0_caso_base_red.pdf` | Buses del caso base en toda la red: jornadas sin batería, después de la carga reactiva (jornadas partidas) y con los buses de reserva que cumplen el ciclo diario. El color identifica el escenario. | Caso base: 8.654 -> 11.259 -> 13.247 buses; Caso base con interlining: 7.366 -> 10.295 -> 12.502 buses |
| `F1_metodologia.pdf` | Metodología en cinco etapas en secuencia. El caso base no es una etapa: toma las jornadas de la Etapa 2 y les aplica la carga reactiva; es la línea base con que se comparan las propuestas. | - |
| `F3_escalera_buses.pdf` | Buses de cada escenario en El Conquistador: operativos más reservas diurnas y nocturnas. La Propuesta completa es el plan de carga exacto al minuto. | buses totales: Caso base 3.970; Caso base con interlining 3.684; Propuesta con carga por orden de llegada 3.088; Propuesta completa 2.642 |
| `F4_costo_total.pdf` | Costo total por componente en El Conquistador (cifra sobre cada barra, en miles de USD por día); el rombo marca el costo total con espera nocturna. | costo total: Caso base 1.154.195 USD/día (con espera nocturna 1.185.165); Caso base con interlining 1.073.408 USD/día (con espera nocturna 1.105.736); Propuesta con carga por orden de llegada 920.766 USD/día (con espera nocturna 941.497); Propuesta completa 812.855 USD/día (con espera nocturna 831.747) |
| `F5_ocupacion_24h.pdf` | Buses cargando a lo largo del día en El Conquistador frente a los 180 puestos; en gris, los tramos de tarifa punta. | horas con todos los puestos ocupados: Caso base con interlining 18,1 h; Propuesta con carga por orden de llegada 16,3 h; Propuesta completa 18,0 h; máximo de buses cargando a la vez en la Propuesta completa:180 buses |

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
