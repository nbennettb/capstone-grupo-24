# Resumen para analisis: instancia La Reina (PRUEBA CHICA: no son resultados)

Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de `results/instancia_LR/`. Escenarios: **Caso base** (jornadas por linea + carga reactiva); **Caso base con interlining** (lo mismo, con interlining en las jornadas); **Propuesta con carga por orden de llegada** (Etapa 3 + carga por orden de llegada); **Propuesta completa** (Etapa 3 + Etapa 4, programa de carga exacto al minuto). Cada escalon cambia una sola cosa.

## 1. Instancia y parametros

- Electroterminal **La Reina** completo: 60 puestos de carga; jornadas sin bateria (Etapa 2): ; 735 jornadas del Caso base con interlining de entrada a la Etapa 3.
- Energia a reponer en las propuestas / capacidad de 24 h de los puestos: 84.5%.
- Bateria util entre cargas 315 kWh (ciclo al 100%, minimo 10%); carga a 180 kW; consumo 1.4 kWh/km.
- Costos: bus 250 USD/dia (igual para una reserva), km vacio 0.5 USD, espera 0.03 USD/min, evento de carga 5 USD.
- Tarifa (USD/kWh): 00-08 h = 0.10, 08-14 h = 0.15, 14-17 h = 0.22, 17-19 h = 0.15, 19-22 h = 0.22, 22-24 h = 0.11.
- Deadhead: euclidiana x 1.3 a 20 km/h; layover 3 min.
- Etapa 3: regla de corte min_tramos_km (minimos tramos, luego minimos km extra); holgura de recarga base 0 min; sensibilidad [0, 30, 60] min.
- Etapa 4: largo del bloque base 15 min (sensibilidad [5, 15, 30] min); Gurobi, brecha 0.5%, limite 600 s el modelo relajado y 3600 s el detallado; deficit penalizado con 10,000 USD/kWh; desempate 1e-06 USD/kWh por bloque desde la llegada.

## 2. Validaciones (re-verificadas desde los CSV)

| validacion                                                                                                                                                         | resultado   | detalle                                                                                                                                                    |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Caso base: igual a la red completa filtrada                                                                                                                        | NO CORRIDO  | falta correr 10-                                                                                                                                           |
| Caso base con interlining: igual a la red completa filtrada                                                                                                        | NO CORRIDO  | falta correr 10-                                                                                                                                           |
| Etapa 3 (holgura de recarga 0 min): cobertura exacta                                                                                                               | OK          | 6,867 expediciones en 1,025 tramos                                                                                                                         |
| Etapa 3 (holgura de recarga 0 min): todo tramo cabe en la bateria util                                                                                             | OK          | maximo 314.9 kWh de 315                                                                                                                                    |
| Etapa 3 (holgura de recarga 0 min): flota = maximo de intervalos superpuestos                                                                                      | OK          | flujo 735, intervalos 735                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): deficit 0                                                                                             | OK          | orden de llegada 0.000 kWh, modelo relajado 0.000 kWh                                                                                                      |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): ocupacion <= 60 por bloque (modelo relajado) y por minuto (orden de llegada)                          | OK          | maximo del modelo relajado por bloque 60.00; orden de llegada por minuto 60; ejecucion minuto a minuto del modelo relajado: 117 min sobre 60 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo relajado <= orden de llegada (energia + reservas)                                              | OK          | 69,564.31 <= 107,949.48 USD                                                                                                                                |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, deficit 0                                                                         | OK          | 0.000 kWh                                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, buses cargando <= 60 en cada minuto                                               | OK          | maximo 60                                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 1. Buses cargando por minuto <= puestos                                                | OK          | maximo 60 de 60; puestos con dos buses a la vez en algun minuto: 0                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 2. Cada carga: minutos enteros, puesto existente, <= 180 kW                            | OK          | 1,543 cargas en 60 puestos                                                                                                                                 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 3. Toda carga con el bus en el patio; si termina despues de su salida, hay reserva     | OK          | cargas fuera de [llegada, llegada + 24 h): 0; ventanas que terminan tarde: 163, sin reserva: 0                                                             |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 4. Cada ventana repone la energia de su tramo; ningun tramo supera la bateria util     | OK          | diferencia maxima 5.68e-14 kWh; tramo mas largo 314.9 de 315 kWh                                                                                           |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 5. Simulando 7 dias, cada salida tiene un bus cargado (buses de la Etapa 3 + reservas) | OK          | 735 buses + 163 reservas = 898 buses; salidas sin bus: 0                                                                                                   |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 6. Energia y reservas recalculadas = informadas                                        | OK          | energia 30,071.69 USD (informada 30,071.69); reservas 163 (informadas 163)                                                                                 |

## 3. KPIs por escenario

Costo total = sin la espera nocturna en el patio (la metrica principal). Costo total con espera nocturna = la espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). En los casos base todas las reservas son nocturnas: si una carga diurna no alcanza, la jornada se parte y el bus nuevo queda en 'operativos'. La Propuesta completa es el programa de carga exacto al minuto.

| KPI                                                                                   | Propuesta con carga por orden de llegada   | Propuesta completa   |
|:--------------------------------------------------------------------------------------|:-------------------------------------------|:---------------------|
| 1. Costo total (USD/dia)                                                              | 312,160                                    | 277,622              |
| 1. Costo total con espera nocturna (USD/dia)                                          | 318,817                                    | 283,798              |
| · flota                                                                               | 183,750                                    | 183,750              |
| · reservas diurnas                                                                    | 0                                          | 0                    |
| · reservas nocturnas                                                                  | 77,250                                     | 40,750               |
| · km vacios                                                                           | 11,477                                     | 11,477               |
| · espera                                                                              | 3,859                                      | 3,859                |
| · espera, con la espera nocturna                                                      | 10,516                                     | 10,035               |
| · energia                                                                             | 30,699                                     | 30,072               |
| · eventos de carga                                                                    | 5,125                                      | 7,715                |
| 2. N de buses (operativos + reservas)                                                 | 1,044                                      | 898                  |
| · buses de las jornadas sin bateria                                                   | 735                                        | 735                  |
| · buses operativos (tras la carga en los casos base; de la Etapa 3 en las propuestas) | 735                                        | 735                  |
| 3. % km de deadheading                                                                | 14.67                                      | 14.67                |
| 4. Costo medio de la energia (USD/kWh)                                                | 0.1402                                     | 0.1373               |
| 4. % de la energia en valle                                                           | 49.0                                       | 49.0                 |
| 5. Buses extra por bateria                                                            | 309                                        | 163                  |
| 6. Reservas diurnas                                                                   | 0                                          | 0                    |
| 6. Reservas nocturnas                                                                 | 309                                        | 163                  |
| 7. Uso maximo de los puestos (%)                                                      | 100.0                                      | 100.0                |
| · maximo de buses cargando a la vez (minuto a minuto)                                 | 60.0                                       | 60.0                 |
| 7. Horas con todos los puestos ocupados                                               | 16.1                                       | 18.8                 |
| · minutos sobre los puestos                                                           | 0                                          | 0                    |
| 8. Segundos de computo (sin la Etapa 2)                                               | 2.6                                        | 201.7                |
| · energia cargada (MWh)                                                               | 219.0                                      | 219.0                |
| · deficit de energia (kWh)                                                            | 0.00                                       | 0.00                 |
| · eventos de carga                                                                    | 1,025                                      | 1,543                |
| · utilizacion del bus (% de 24 h con pasajeros)                                       | 33.9                                       | 39.5                 |

### Variantes (sensibilidad y modelo relajado)

| escenario          | variante        | modelo   |   buses_operativos |   reservas_diurnas |   reservas_nocturnas |   buses_totales |   costo_energia |   costo_eventos |   costo_total |   costo_total_con_espera_nocturna |
|:-------------------|:----------------|:---------|-------------------:|-------------------:|---------------------:|----------------:|----------------:|----------------:|--------------:|----------------------------------:|
| Propuesta completa | modelo relajado | agregado |                735 |                  0 |                  158 |             893 |           30064 |           18935 |        287585 |                            290821 |

## 4. Diagnostico de flota de la Etapa 3

| paso                             |   buses | que_mide                                                            |
|:---------------------------------|--------:|:--------------------------------------------------------------------|
| (i) Jornadas sin bateria         |     735 | Punto de partida: una jornada = un bus                              |
| (ii) Reuso del patio sin bateria |     707 | Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga |
| (iii) Solo cortes                |    1025 | Cada tramo un bus                                                   |
| (iv) Cortes + re-encadenamiento  |     735 | La Etapa 3 completa (recarga completa + holgura 0 min)              |

- 1,025 tramos desde 735 jornadas (289 cortadas; 3,054.8 km extra). Ventanas de carga: 290 diurnas (entre tramos), 735 nocturnas.
- Nocturnas que no alcanzan la recarga completa ni con puesto libre: 42 (de ellas 32 cadenas de mas de 24 h: el flujo, como las jornadas sin bateria, es de un dia y no ciclico). Son reservas que ninguna programacion de carga puede evitar.

## 5. Reservas por tipo

| escenario                                |   reservas_diurnas |   reservas_nocturnas |   reservas |
|:-----------------------------------------|-------------------:|---------------------:|-----------:|
| Propuesta con carga por orden de llegada |                  0 |                  309 |        309 |
| Propuesta completa                       |                  0 |                  163 |        163 |

## 6. Energia por tramo horario (kWh y USD)

| tramo horario   |   precio_usd_kwh |   kWh Propuesta con carga por orden de llegada |   kWh Propuesta completa |   USD Propuesta con carga por orden de llegada |   USD Propuesta completa |
|:----------------|-----------------:|-----------------------------------------------:|-------------------------:|-----------------------------------------------:|-------------------------:|
| 00-08 h         |             0.1  |                                          85764 |                    85771 |                                           8576 |                     8577 |
| 08-14 h         |             0.15 |                                          63673 |                    64334 |                                           9551 |                     9650 |
| 14-17 h         |             0.22 |                                          12230 |                     3448 |                                           2691 |                      759 |
| 17-19 h         |             0.15 |                                           5407 |                    13699 |                                            811 |                     2055 |
| 19-22 h         |             0.22 |                                          30496 |                    30315 |                                           6709 |                     6669 |
| 22-24 h         |             0.11 |                                          21466 |                    21470 |                                           2361 |                     2362 |

## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)

Puestos: 60. Propuesta completa = ejecucion minuto a minuto del programa de carga exacto al minuto.

|   hora |   Propuesta, carga por llegada (promedio) |   Propuesta, carga por llegada (maximo) |   Propuesta completa (promedio) |   Propuesta completa (maximo) |
|-------:|------------------------------------------:|----------------------------------------:|--------------------------------:|------------------------------:|
|      0 |                                      60   |                                      60 |                            60   |                            60 |
|      1 |                                      60   |                                      60 |                            60   |                            60 |
|      2 |                                      60   |                                      60 |                            60   |                            60 |
|      3 |                                      59.9 |                                      60 |                            60   |                            60 |
|      4 |                                      60   |                                      60 |                            60   |                            60 |
|      5 |                                      60   |                                      60 |                            60   |                            60 |
|      6 |                                      59.8 |                                      60 |                            60   |                            60 |
|      7 |                                      59.8 |                                      60 |                            60   |                            60 |
|      8 |                                      58.8 |                                      60 |                            60   |                            60 |
|      9 |                                      59.7 |                                      60 |                            60   |                            60 |
|     10 |                                      59.6 |                                      60 |                            60   |                            60 |
|     11 |                                      59.6 |                                      60 |                            60   |                            60 |
|     12 |                                      59.7 |                                      60 |                            60   |                            60 |
|     13 |                                      59.2 |                                      60 |                            60   |                            60 |
|     14 |                                      40.7 |                                      55 |                            11.8 |                            14 |
|     15 |                                      16.4 |                                      22 |                             6.7 |                            15 |
|     16 |                                      11.4 |                                      15 |                             0.8 |                             2 |
|     17 |                                      14.4 |                                      18 |                            52.4 |                            60 |
|     18 |                                      15.8 |                                      30 |                            24.2 |                            37 |
|     19 |                                      50.4 |                                      60 |                            50.4 |                            60 |
|     20 |                                      60   |                                      60 |                            60   |                            60 |
|     21 |                                      60   |                                      60 |                            59   |                            60 |
|     22 |                                      60   |                                      60 |                            60   |                            60 |
|     23 |                                      60   |                                      60 |                            60   |                            60 |

## 8. Sensibilidad a la holgura de recarga de la Etapa 3 (modelo relajado, largo del bloque base)

|   holgura_de_recarga_min |   buses_etapa3 |   reservas_carga_por_llegada |   reservas_propuesta_completa |   buses_totales_carga_por_llegada |   buses_totales_propuesta_completa |   costo_total_propuesta_completa |   costo_energia_propuesta_completa |   nocturnas_sin_tiempo_carga |
|-------------------------:|---------------:|-----------------------------:|------------------------------:|----------------------------------:|-----------------------------------:|---------------------------------:|-----------------------------------:|-----------------------------:|
|                        0 |            735 |                          309 |                           158 |                              1044 |                                893 |                           287585 |                              30064 |                           42 |

## 9. Sensibilidad al largo del bloque (modelo relajado, holgura de recarga base)

|   largo_del_bloque_min |   objetivo_usd |   cota_lp_usd |   reservas |   costo_energia |   eventos |   minutos_sobre_puestos |   variables |   segundos_lp |   segundos_milp |   brecha | estado                 |
|-----------------------:|---------------:|--------------:|-----------:|----------------:|----------:|------------------------:|------------:|--------------:|----------------:|---------:|:-----------------------|
|                     15 |        69564.3 |       68859.1 |        158 |         30064.3 |      3787 |                     117 |      102468 |          3.35 |           30.45 | 0.002646 | optimo (brecha pedida) |

## 10. Segundos, estado y brecha de cada modelo

La Etapa 2 (jornadas sin bateria) no se vuelve a correr: sus jornadas son un archivo.

| corrida                                                                                                  | estado                        |     brecha | fuente_brecha   |   segundos |
|:---------------------------------------------------------------------------------------------------------|:------------------------------|-----------:|:----------------|-----------:|
| Etapa 3 (holgura de recarga 0 min) (DP + flujo)                                                          | optimo (flujo entero)         |   0        | flujo entero    |       1.9  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta con carga por orden de llegada    | heuristica (sin optimizacion) | nan        | -               |       0.74 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado, LP (cota)                  | optimo                        |   0        | Gurobi          |       3.35 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado (MILP)                      | optimo (brecha pedida)        |   0.002646 | Gurobi          |      30.45 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, arranque                   | factible                      | nan        | -               |      11.7  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, MILP                       | optimo (brecha pedida)        |   0.00204  | Gurobi          |     120.5  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, final (energia + reservas) | entero y validado             |   0.020295 | Gurobi          |     166    |

## 11. Propuesta completa: plan de carga y distancia al optimo

Como se obtiene: (1) el modelo relajado (bloques de 15 min, sin mirar minuto a minuto) elige las reservas de partida y da una cota inferior del costo; (2) un MILP al minuto decide las reservas y cuando carga cada bus, sin superar nunca los puestos; (3) a cada carga se le asigna un puesto; (4) 15- valida el plan por separado.

- Energia + reservas: 70,822 USD/dia, con 163 reservas.
- Cota inferior (modelo relajado): 69,384 USD/dia. El plan esta a lo mas a 2.03% del optimo (en energia + reservas).
- MILP al minuto: optimo (brecha pedida), brecha de Gurobi 0.20%, 120 s; 781,535 variables.
- Maximo de buses cargando a la vez: 60 de 60; eventos de carga: 1,543 (1.51 por ventana).
- Tiempo total de la Etapa 4 (relajado + exacto): ver seccion 10.

## Definiciones y supuestos que hay que tener presentes al analizar

- La Propuesta con carga por orden de llegada y la Propuesta completa usan las mismas ventanas de la Etapa 3: la diferencia entre ellas es solo la programacion de la carga.
- Del Caso base con interlining a la Propuesta con carga por orden de llegada se cambia la carga reactiva por la Etapa 3 (cortes + re-encadenamiento con recarga completa en el patio).
- Parte de la mejora de la Etapa 3 viene de permitir que un bus vuelva al patio y salga de nuevo (paso ii del diagnostico), algo que ni las jornadas sin bateria ni el caso base permiten.
- Reserva: si la carga de una ventana no termina antes de la siguiente salida del bus, un bus ya cargado cubre esa salida (250 USD). En una ventana diurna la reserva toma el resto de la cadena (supuesto conservador).
- La Etapa 3 no ve los puestos; la holgura de recarga los anticipa. La Etapa 4 decide con los puestos y la tarifa.
- La Propuesta completa es un plan de carga exacto al minuto: cada bus carga en minutos enteros en un puesto identificado y en ningun minuto cargan mas buses que puestos. El modelo relajado (bloques de 15 min, capacidad en energia) solo elige las reservas de partida y da la cota inferior.
- Limitaciones: un solo electroterminal; recarga completa entre tramos; deadhead euclidiano; un dia tipo; flujo de un dia (no ciclico).
