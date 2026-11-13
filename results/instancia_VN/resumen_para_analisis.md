# Resumen para analisis: instancia Vespucio Norte

Archivo generado por `scripts/14-kpis_instancia.py`. Todas las cifras salen de los CSV de `results/instancia_VN/`. Escenarios: **Caso base** (jornadas por linea + carga reactiva); **Caso base con interlining** (lo mismo, con interlining en las jornadas); **Propuesta con carga por orden de llegada** (Etapa 3 + carga por orden de llegada); **Propuesta completa** (Etapa 3 + Etapa 4, programa de carga exacto al minuto). Cada escalon cambia una sola cosa.

## 1. Instancia y parametros

- Electroterminal **Vespucio Norte** completo: 150 puestos de carga; jornadas sin bateria (Etapa 2): Caso base 889, Caso base con interlining 793; 793 jornadas del Caso base con interlining de entrada a la Etapa 3.
- Energia a reponer en las propuestas / capacidad de 24 h de los puestos: 34.2%.
- Bateria util entre cargas 315 kWh (ciclo al 100%, minimo 10%); carga a 180 kW; consumo 1.4 kWh/km.
- Costos: bus 250 USD/dia (igual para una reserva), km vacio 0.5 USD, espera 0.03 USD/min, evento de carga 5 USD.
- Tarifa (USD/kWh): 00-08 h = 0.10, 08-14 h = 0.15, 14-17 h = 0.22, 17-19 h = 0.15, 19-22 h = 0.22, 22-24 h = 0.11.
- Deadhead: euclidiana x 1.3 a 20 km/h; layover 3 min.
- Etapa 3: regla de corte min_tramos_km (minimos tramos, luego minimos km extra); holgura de recarga base 0 min; sensibilidad [0, 30, 60] min.
- Etapa 4: largo del bloque base 15 min (sensibilidad [5, 15, 30] min); Gurobi, brecha 0.5%, limite 600 s el modelo relajado y 3600 s el detallado; deficit penalizado con 10,000 USD/kWh; desempate 1e-06 USD/kWh por bloque desde la llegada.

## 2. Validaciones (re-verificadas desde los CSV)

| validacion                                                                                                                                                         | resultado   | detalle                                                                                                                                                      |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Caso base: igual a la red completa filtrada                                                                                                                        | OK          | 1,103 jornadas finales y 7 reservas (red completa filtrada: 1,103 y 7)                                                                                       |
| Caso base: deficit de energia 0                                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                    |
| Caso base con interlining: igual a la red completa filtrada                                                                                                        | OK          | 1,035 jornadas finales y 3 reservas (red completa filtrada: 1,035 y 3)                                                                                       |
| Caso base con interlining: deficit de energia 0                                                                                                                    | OK          | 0.000 kWh                                                                                                                                                    |
| Etapa 3 (holgura de recarga 0 min): cobertura exacta                                                                                                               | OK          | 7,229 expediciones en 1,038 tramos                                                                                                                           |
| Etapa 3 (holgura de recarga 0 min): todo tramo cabe en la bateria util                                                                                             | OK          | maximo 314.7 kWh de 315                                                                                                                                      |
| Etapa 3 (holgura de recarga 0 min): flota = maximo de intervalos superpuestos                                                                                      | OK          | flujo 773, intervalos 773                                                                                                                                    |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): deficit 0                                                                                             | OK          | orden de llegada 0.000 kWh, modelo relajado 0.000 kWh                                                                                                        |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): ocupacion <= 150 por bloque (modelo relajado) y por minuto (orden de llegada)                         | OK          | maximo del modelo relajado por bloque 150.00; orden de llegada por minuto 150; ejecucion minuto a minuto del modelo relajado: 24 min sobre 150 (informativo) |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): modelo relajado <= orden de llegada (energia + reservas)                                              | OK          | 31,520.51 <= 38,913.87 USD                                                                                                                                   |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, deficit 0                                                                         | OK          | 0.000 kWh                                                                                                                                                    |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta completa, buses cargando <= 150 en cada minuto                                              | OK          | maximo 150                                                                                                                                                   |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 1. Buses cargando por minuto <= puestos                                                | OK          | maximo 150 de 150; puestos con dos buses a la vez en algun minuto: 0                                                                                         |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 2. Cada carga: minutos enteros, puesto existente, <= 180 kW                            | OK          | 1,278 cargas en 150 puestos                                                                                                                                  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 3. Toda carga con el bus en el patio; si termina despues de su salida, hay reserva     | OK          | cargas fuera de [llegada, llegada + 24 h): 0; ventanas que terminan tarde: 29, sin reserva: 0                                                                |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 4. Cada ventana repone la energia de su tramo; ningun tramo supera la bateria util     | OK          | diferencia maxima 5.68e-14 kWh; tramo mas largo 314.7 de 315 kWh                                                                                             |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 5. Simulando 7 dias, cada salida tiene un bus cargado (buses de la Etapa 3 + reservas) | OK          | 773 buses + 29 reservas = 802 buses; salidas sin bus: 0                                                                                                      |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): plan de carga, 6. Energia y reservas recalculadas = informadas                                        | OK          | energia 24,274.49 USD (informada 24,274.49); reservas 29 (informadas 29)                                                                                     |

## 3. KPIs por escenario

Costo total = sin la espera nocturna en el patio (la metrica principal). Costo total con espera nocturna = la espera como la cobra el caso base (incluye la espera nocturna hasta empezar a cargar). En los casos base todas las reservas son nocturnas: si una carga diurna no alcanza, la jornada se parte y el bus nuevo queda en 'operativos'. La Propuesta completa es el programa de carga exacto al minuto.

| KPI                                                                                   | Caso base   | Caso base con interlining   | Propuesta con carga por orden de llegada   | Propuesta completa   |
|:--------------------------------------------------------------------------------------|:------------|:----------------------------|:-------------------------------------------|:---------------------|
| 1. Costo total (USD/dia)                                                              | 327,232     | 307,217                     | 249,432                                    | 243,242              |
| 1. Costo total con espera nocturna (USD/dia)                                          | 328,883     | 309,344                     | 250,245                                    | 249,153              |
| · flota                                                                               | 275,750     | 258,750                     | 193,250                                    | 193,250              |
| · reservas diurnas                                                                    | 0           | 0                           | 0                                          | 0                    |
| · reservas nocturnas                                                                  | 1,750       | 750                         | 8,250                                      | 7,250                |
| · km vacios                                                                           | 8,528       | 8,330                       | 7,588                                      | 7,588                |
| · espera                                                                              | 4,604       | 3,901                       | 4,490                                      | 4,490                |
| · espera, con la espera nocturna                                                      | 6,255       | 6,028                       | 5,302                                      | 10,401               |
| · energia                                                                             | 31,040      | 30,251                      | 30,664                                     | 24,274               |
| · eventos de carga                                                                    | 5,560       | 5,235                       | 5,190                                      | 6,390                |
| 2. N de buses (operativos + reservas)                                                 | 1,110       | 1,038                       | 806                                        | 802                  |
| · buses de las jornadas sin bateria                                                   | 889         | 793                         | 793                                        | 793                  |
| · buses operativos (tras la carga en los casos base; de la Etapa 3 en las propuestas) | 1,103       | 1,035                       | 773                                        | 773                  |
| 3. % km de deadheading                                                                | 10.64       | 10.42                       | 9.58                                       | 9.58                 |
| 4. Costo medio de la energia (USD/kWh)                                                | 0.1384      | 0.1352                      | 0.1383                                     | 0.1095               |
| 4. % de la energia en valle                                                           | 66.9        | 70.4                        | 64.5                                       | 85.4                 |
| 5. Buses extra por bateria                                                            | 221         | 245                         | 13                                         | 9                    |
| 6. Reservas diurnas                                                                   | 0           | 0                           | 0                                          | 0                    |
| 6. Reservas nocturnas                                                                 | 7           | 3                           | 33                                         | 29                   |
| 7. Uso maximo de los puestos (%)                                                      | 100.0       | 100.0                       | 100.0                                      | 100.0                |
| · maximo de buses cargando a la vez (minuto a minuto)                                 | 150.0       | 150.0                       | 150.0                                      | 150.0                |
| 7. Horas con todos los puestos ocupados                                               | 6.1         | 6.4                         | 5.5                                        | 6.5                  |
| · minutos sobre los puestos                                                           | 0           | 0                           | 0                                          | 0                    |
| 8. Segundos de computo (sin la Etapa 2)                                               | 1.9         | 0.6                         | 1.5                                        | 26.7                 |
| · energia cargada (MWh)                                                               | 224.3       | 223.8                       | 221.7                                      | 221.7                |
| · deficit de energia (kWh)                                                            | 0.00        | 0.00                        | 0.00                                       | 0.00                 |
| · eventos de carga                                                                    | 1,112       | 1,047                       | 1,038                                      | 1,278                |
| · utilizacion del bus (% de 24 h con pasajeros)                                       | 33.8        | 36.1                        | 46.6                                       | 46.8                 |

### Variantes (sensibilidad y modelo relajado)

| escenario          | variante        | modelo   |   buses_operativos |   reservas_diurnas |   reservas_nocturnas |   buses_totales |   costo_energia |   costo_eventos |   costo_total |   costo_total_con_espera_nocturna |
|:-------------------|:----------------|:---------|-------------------:|-------------------:|---------------------:|----------------:|----------------:|----------------:|--------------:|----------------------------------:|
| Propuesta completa | modelo relajado | agregado |                773 |                  0 |                   29 |             802 |           24271 |           16715 |        253563 |                            257869 |

## 4. Diagnostico de flota de la Etapa 3

| paso                             |   buses | que_mide                                                            |
|:---------------------------------|--------:|:--------------------------------------------------------------------|
| (i) Jornadas sin bateria         |     793 | Punto de partida: una jornada = un bus                              |
| (ii) Reuso del patio sin bateria |     753 | Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga |
| (iii) Solo cortes                |    1038 | Cada tramo un bus                                                   |
| (iv) Cortes + re-encadenamiento  |     773 | La Etapa 3 completa (recarga completa + holgura 0 min)              |

- 1,038 tramos desde 793 jornadas (244 cortadas; 1,597.3 km extra). Ventanas de carga: 265 diurnas (entre tramos), 773 nocturnas.
- Nocturnas que no alcanzan la recarga completa ni con puesto libre: 29 (de ellas 23 cadenas de mas de 24 h: el flujo, como las jornadas sin bateria, es de un dia y no ciclico). Son reservas que ninguna programacion de carga puede evitar.

## 5. Reservas por tipo

| escenario                                |   reservas_diurnas |   reservas_nocturnas |   reservas |
|:-----------------------------------------|-------------------:|---------------------:|-----------:|
| Caso base                                |                  0 |                    7 |          7 |
| Caso base con interlining                |                  0 |                    3 |          3 |
| Propuesta con carga por orden de llegada |                  0 |                   33 |         33 |
| Propuesta completa                       |                  0 |                   29 |         29 |

## 6. Energia por tramo horario (kWh y USD)

| tramo horario   |   precio_usd_kwh |   kWh Caso base |   kWh Caso base con interlining |   kWh Propuesta con carga por orden de llegada |   kWh Propuesta completa |   USD Caso base |   USD Caso base con interlining |   USD Propuesta con carga por orden de llegada |   USD Propuesta completa |
|:----------------|-----------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|----------------:|--------------------------------:|-----------------------------------------------:|-------------------------:|
| 00-08 h         |             0.1  |           96339 |                          103970 |                                          89323 |                   187014 |            9634 |                           10397 |                                           8932 |                    18701 |
| 08-14 h         |             0.15 |            8242 |                            5159 |                                          17775 |                    17775 |            1236 |                             774 |                                           2666 |                     2666 |
| 14-17 h         |             0.22 |            3091 |                            3257 |                                           4368 |                       30 |             680 |                             717 |                                            961 |                        7 |
| 17-19 h         |             0.15 |            3894 |                            3448 |                                           3518 |                     7857 |             584 |                             517 |                                            528 |                     1178 |
| 19-22 h         |             0.22 |           59099 |                           54284 |                                          53062 |                     6618 |           13002 |                           11942 |                                          11674 |                     1456 |
| 22-24 h         |             0.11 |           53675 |                           53670 |                                          53664 |                     2417 |            5904 |                            5904 |                                           5903 |                      266 |

## 7. Ocupacion de los puestos por hora (buses cargando: promedio y maximo de la hora)

Puestos: 150. Propuesta completa = ejecucion minuto a minuto del programa de carga exacto al minuto.

|   hora |   Caso base (promedio) |   Caso base (maximo) |   Caso base + interlining (promedio) |   Caso base + interlining (maximo) |   Propuesta, carga por llegada (promedio) |   Propuesta, carga por llegada (maximo) |   Propuesta completa (promedio) |   Propuesta completa (maximo) |
|-------:|-----------------------:|---------------------:|-------------------------------------:|-----------------------------------:|------------------------------------------:|----------------------------------------:|--------------------------------:|------------------------------:|
|      0 |                  150   |                  150 |                                150   |                                150 |                                     150   |                                     150 |                           150   |                           150 |
|      1 |                  150   |                  150 |                                150   |                                150 |                                     150   |                                     150 |                           150   |                           150 |
|      2 |                  149.7 |                  150 |                                150   |                                150 |                                     137.2 |                                     150 |                           150   |                           150 |
|      3 |                   76.6 |                  137 |                                114.1 |                                150 |                                      50.5 |                                      96 |                           150   |                           150 |
|      4 |                    7   |                   24 |                                 16.9 |                                 44 |                                       3.2 |                                      12 |                           150   |                           150 |
|      5 |                    1.4 |                    2 |                                  0   |                                  0 |                                       1.4 |                                       2 |                           150   |                           150 |
|      6 |                    2.3 |                    3 |                                  0.1 |                                  1 |                                       2.9 |                                       6 |                           121.6 |                           150 |
|      7 |                    2.5 |                    3 |                                  1.7 |                                  3 |                                       4.7 |                                      10 |                            23.9 |                            58 |
|      8 |                    8   |                   15 |                                  2.5 |                                  5 |                                       8.3 |                                      14 |                             8.3 |                            14 |
|      9 |                    8.2 |                   11 |                                  7.1 |                                  9 |                                      19.9 |                                      24 |                            19.9 |                            24 |
|     10 |                   14.8 |                   19 |                                  9.4 |                                 14 |                                      26.6 |                                      35 |                            26.6 |                            35 |
|     11 |                    7.2 |                   12 |                                  3   |                                  5 |                                      16.7 |                                      20 |                            16.7 |                            20 |
|     12 |                    3   |                    5 |                                  3   |                                  4 |                                      14.6 |                                      17 |                            14.6 |                            17 |
|     13 |                    5.4 |                    7 |                                  4.2 |                                  6 |                                      14.1 |                                      17 |                            14.1 |                            17 |
|     14 |                    6.5 |                    8 |                                  4.8 |                                  6 |                                       9.8 |                                      12 |                             0.2 |                             1 |
|     15 |                    6.6 |                    9 |                                  4.3 |                                  7 |                                       9.3 |                                      11 |                             0   |                             0 |
|     16 |                    4.2 |                    7 |                                  9.1 |                                 12 |                                       5.4 |                                       9 |                             0   |                             0 |
|     17 |                    6   |                    8 |                                  8.3 |                                 11 |                                       7.6 |                                       9 |                            30.8 |                            35 |
|     18 |                   15.7 |                   32 |                                 11   |                                 19 |                                      12.1 |                                      19 |                            13.2 |                            22 |
|     19 |                   56.3 |                   87 |                                 46.1 |                                 85 |                                      46.2 |                                      84 |                            29.6 |                            35 |
|     20 |                  123.7 |                  150 |                                106.9 |                                148 |                                     100.5 |                                     135 |                             7.5 |                            24 |
|     21 |                  150   |                  150 |                                150   |                                150 |                                     149.5 |                                     150 |                             0   |                             0 |
|     22 |                  150   |                  150 |                                150   |                                150 |                                     150   |                                     150 |                            10.8 |                            13 |
|     23 |                  150   |                  150 |                                150   |                                150 |                                     150   |                                     150 |                             2.6 |                             6 |

## 8. Sensibilidad a la holgura de recarga de la Etapa 3 (modelo relajado, largo del bloque base)

|   holgura_de_recarga_min |   buses_etapa3 |   reservas_carga_por_llegada |   reservas_propuesta_completa |   buses_totales_carga_por_llegada |   buses_totales_propuesta_completa |   costo_total_propuesta_completa |   costo_energia_propuesta_completa |   nocturnas_sin_tiempo_carga |
|-------------------------:|---------------:|-----------------------------:|------------------------------:|----------------------------------:|-----------------------------------:|---------------------------------:|-----------------------------------:|-----------------------------:|
|                        0 |            773 |                           33 |                            29 |                               806 |                                802 |                           253563 |                              24271 |                           29 |

## 9. Sensibilidad al largo del bloque (modelo relajado, holgura de recarga base)

|   largo_del_bloque_min |   objetivo_usd |   cota_lp_usd |   reservas |   costo_energia |   eventos |   minutos_sobre_puestos |   variables |   segundos_lp |   segundos_milp |   brecha | estado                 |
|-----------------------:|---------------:|--------------:|-----------:|----------------:|----------:|------------------------:|------------:|--------------:|----------------:|---------:|:-----------------------|
|                     15 |        31520.5 |       30958.8 |         29 |         24270.5 |      3343 |                      24 |      103777 |          0.88 |            2.11 |        0 | optimo (brecha pedida) |

## 10. Segundos, estado y brecha de cada modelo

La Etapa 2 (jornadas sin bateria) no se vuelve a correr: sus jornadas son un archivo.

| corrida                                                                                                  | estado                        | brecha   | fuente_brecha   |   segundos |
|:---------------------------------------------------------------------------------------------------------|:------------------------------|:---------|:----------------|-----------:|
| Caso base (simulador reactivo)                                                                           | -                             | -        | -               |       1.9  |
| Caso base con interlining (simulador reactivo)                                                           | -                             | -        | -               |       0.6  |
| Etapa 3 (holgura de recarga 0 min) (DP + flujo)                                                          | optimo (flujo entero)         | 0        | flujo entero    |       1.3  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Propuesta con carga por orden de llegada    | heuristica (sin optimizacion) | nan      | -               |       0.16 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado, LP (cota)                  | optimo                        | 0.0      | Gurobi          |       0.88 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Modelo relajado (MILP)                      | optimo (brecha pedida)        | 0.0      | Gurobi          |       2.11 |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, arranque                   | factible                      | nan      | -               |       4.2  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, MILP                       | optimo (brecha pedida)        | 0.004751 | Gurobi          |       7.9  |
| Etapa 4 (holgura de recarga 0 min, largo del bloque 15 min): Programa exacto, final (energia + reservas) | entero y validado             | 6e-06    | Gurobi          |      22.4  |

## 11. Propuesta completa: plan de carga y distancia al optimo

Como se obtiene: (1) el modelo relajado (bloques de 15 min, sin mirar minuto a minuto) elige las reservas de partida y da una cota inferior del costo; (2) un MILP al minuto decide las reservas y cuando carga cada bus, sin superar nunca los puestos; (3) a cada carga se le asigna un puesto; (4) 15- valida el plan por separado.

- Energia + reservas: 31,524 USD/dia, con 29 reservas.
- Cota inferior (modelo relajado): 31,524 USD/dia. El plan esta a lo mas a 0.00% del optimo (en energia + reservas).
- MILP al minuto: optimo (brecha pedida), brecha de Gurobi 0.48%, 8 s; 425,632 variables.
- Maximo de buses cargando a la vez: 150 de 150; eventos de carga: 1,278 (1.23 por ventana).
- Tiempo total de la Etapa 4 (relajado + exacto): ver seccion 10.

## Figuras del informe

En `informe/`, cada una en PDF (vectorial, para LaTeX), PNG y CSV con sus datos. Ancho pensado para 0.8 del ancho de texto de LaTeX, letra de 9 pt, sin titulo en la imagen (va en el caption).

| Figura | Caption propuesto | Cifra principal que respalda |
|---|---|---|
| `F0_caso_base_red.pdf` | Buses del caso base en toda la red: jornadas sin batería, después de la carga reactiva (jornadas partidas) y con los buses de reserva que cumplen el ciclo diario. El color identifica el escenario. | Caso base: 8.654 -> 11.259 -> 13.247 buses; Caso base con interlining: 7.366 -> 10.295 -> 12.502 buses |
| `F1_metodologia.pdf` | Metodología en cinco etapas en secuencia. El caso base no es una etapa: toma las jornadas de la Etapa 2 y les aplica la carga reactiva; es la línea base con que se comparan las propuestas. | - |
| `F3_escalera_buses.pdf` | Buses de cada escenario en Vespucio Norte: operativos más reservas diurnas y nocturnas. La Propuesta completa es el plan de carga exacto al minuto. | buses totales: Caso base 1.110; Caso base con interlining 1.038; Propuesta con carga por orden de llegada 806; Propuesta completa 802 |
| `F4_costo_total.pdf` | Costo total por componente en Vespucio Norte (cifra sobre cada barra, en miles de USD por día); el rombo marca el costo total con espera nocturna. | costo total: Caso base 327.232 USD/día (con espera nocturna 328.883); Caso base con interlining 307.217 USD/día (con espera nocturna 309.344); Propuesta con carga por orden de llegada 249.432 USD/día (con espera nocturna 250.245); Propuesta completa 243.242 USD/día (con espera nocturna 249.153) |
| `F5_ocupacion_24h.pdf` | Buses cargando a lo largo del día en Vespucio Norte frente a los 150 puestos; en gris, los tramos de tarifa punta. | horas con todos los puestos ocupados: Caso base con interlining 6,4 h; Propuesta con carga por orden de llegada 5,5 h; Propuesta completa 6,5 h; máximo de buses cargando a la vez en la Propuesta completa:150 buses |

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
