# Reporte - KPIs de la escalera de escenarios (E0, E1, LB)

Todos los escenarios operacionales usan C1b y los terminales Los Espinos + Santa Rosa unidos; nivel de bateria 100% con buses de reserva para la condicion ciclica. **LB es una cota inferior (no operacional)**: solo tiene VSP, sin carga. Cifras en USD por dia.

## Tabla de KPIs

|                                             |   E0 (por linea) |   E1 (+ interlining) | LB (cota, no operacional)   |
|:--------------------------------------------|-----------------:|---------------------:|:----------------------------|
| buses_vsp                                   |   8654           |       7366           | 7055                        |
| brecha_buses_vs_cota_pct                    |     32.3         |         12.6         | 7.9                         |
| brecha_buses_vs_LB_pct                      |     22.7         |          4.4         | 0.0                         |
| pct_km_vacios_vsp                           |     13.31        |         11.96        | 9.82                        |
| costo_operacion_vsp_usd                     |      2.31199e+06 |          1.97026e+06 | 1873677                     |
| utilizacion_vsp_agregada_pct                |     68.6         |         71.8         | 73.2                        |
| utilizacion_vsp_promedio_jornada_pct        |     66.6         |         70.9         | 72.7                        |
| buses_tras_carga                            |  11259           |      10295           |                             |
| jornadas_partidas                           |   2605           |       2929           |                             |
| buses_reserva                               |   1988           |       2207           |                             |
| buses_totales                               |  13247           |      12502           |                             |
| ciclos_no_cumplidos                         |   1988           |       2207           |                             |
| recargas_intermedias                        |     53           |         60           |                             |
| pct_jornadas_con_recarga_intermedia         |      0.43        |          0.55        |                             |
| pct_km_vacios_tras_carga                    |     16.18        |         15.21        |                             |
| costo_flota_usd                             |      2.81475e+06 |          2.57375e+06 |                             |
| costo_km_vacios_usd                         | 129830           |     120668           |                             |
| costo_espera_entre_viajes_usd               |  44342           |      36504           |                             |
| costo_espera_por_puesto_usd                 | 100928           |     106714           |                             |
| costo_energia_usd                           | 314653           |     310089           |                             |
| costo_eventos_usd                           |  56560           |      51775           |                             |
| costo_reservas_usd                          | 497000           |     551750           |                             |
| costo_total_usd                             |      3.95806e+06 |          3.75125e+06 |                             |
| costo_total_sin_espera_por_puesto_usd       |      3.85714e+06 |          3.64454e+06 |                             |
| costo_medio_energia_usd_kwh                 |      0.14        |          0.1396      |                             |
| pct_energia_en_valle                        |     50.44        |         51.39        |                             |
| energia_mwh                                 |   2247.1         |       2221.4         |                             |
| factible                                    |      1           |          1           |                             |
| cota_lp_pct                                 |     89.51        |         84.02        |                             |
| utilizacion_tras_carga_agregada_pct         |     67.4         |         70.3         |                             |
| utilizacion_tras_carga_promedio_jornada_pct |     65.2         |         67.9         |                             |

## Desglose del costo total

|                                       |   E0 (por linea) |   E1 (+ interlining) |
|:--------------------------------------|-----------------:|---------------------:|
| costo_flota_usd                       |      2.81475e+06 |          2.57375e+06 |
| costo_km_vacios_usd                   | 129830           |     120668           |
| costo_espera_entre_viajes_usd         |  44342           |      36504           |
| costo_espera_por_puesto_usd           | 100928           |     106714           |
| costo_energia_usd                     | 314653           |     310089           |
| costo_eventos_usd                     |  56560           |      51775           |
| costo_reservas_usd                    | 497000           |     551750           |
| costo_medio_energia_usd_kwh           |      0.14        |          0.1396      |
| costo_total_usd                       |      3.95806e+06 |          3.75125e+06 |
| costo_total_sin_espera_por_puesto_usd |      3.85714e+06 |          3.64454e+06 |

## Precio de la descomposicion y de cada decision

| concepto                                                                                         |   buses |   buses_pct |   costo_usd |   costo_pct |
|:-------------------------------------------------------------------------------------------------|--------:|------------:|------------:|------------:|
| Descomposicion: E1 frente a LB (VSP, exigir retorno al electroterminal y limitar el interlining) |     311 |         4.4 |       96588 |         5.2 |
| Interlining: E0 frente a E1 (VSP)                                                                |    1288 |        17.5 |      341723 |        17.3 |
| Bateria: E0 tras la carga frente a su VSP (jornadas partidas 2605 + reservas 1988)               |    4593 |        53.1 |     1646075 |        71.2 |
| Bateria: E1 tras la carga frente a su VSP (jornadas partidas 2929 + reservas 2207)               |    5136 |        69.7 |     1780985 |        90.4 |

## Uso de los electroterminales (modulo 24 h)

| escenario   | terminal                 |   puestos |   uso_maximo_pct |   uso_promedio_pct |   pct_del_dia_saturado |
|:------------|:-------------------------|----------:|-----------------:|-------------------:|-----------------------:|
| E0          | Los Espinos + Santa Rosa |       270 |              100 |               87.9 |                   78.3 |
| E0          | Vespucio Norte           |       150 |              100 |               34.9 |                   25.6 |
| E0          | El Conquistador          |       180 |              100 |               84.8 |                   74.2 |
| E0          | La Reina                 |       100 |              100 |               81.9 |                   71   |
| E1          | Los Espinos + Santa Rosa |       270 |              100 |               86.8 |                   79   |
| E1          | Vespucio Norte           |       150 |              100 |               34.8 |                   26.5 |
| E1          | El Conquistador          |       180 |              100 |               83.5 |                   75.3 |
| E1          | La Reina                 |       100 |              100 |               80.9 |                   71   |

## Valor de la carga programada (MILP) - INSTANCIA REDUCIDA, no es el resultado de toda la red

Costo de la carga = energia + eventos + reservas, en la instancia (no se suma al total de la red). La ganancia es una cota inferior (el MILP usa bloques de 15 min y solo N = 10 esta certificada al optimo). Ver `results/etapa4_milp_carga/reporte.md`.

|   N_objetivo |   buses |   puestos |   costo_carga_simulador_usd |   costo_carga_milp_usd |   ganancia_pct |   reservas_simulador |   reservas_milp |   reservas_piso |   usd_kwh_simulador |   usd_kwh_milp |   pct_valle_simulador |   pct_valle_milp |   brecha_pct |   resuelta_al_optimo |
|-------------:|--------:|----------:|----------------------------:|-----------------------:|---------------:|---------------------:|----------------:|----------------:|--------------------:|---------------:|----------------------:|-----------------:|-------------:|---------------------:|
|           10 |       9 |         1 |                      282.48 |                 252.84 |           10.5 |                    0 |               0 |               0 |              0.1235 |         0.1081 |                 81.99 |            87.44 |        0.262 |                    1 |
|           30 |      34 |         2 |                     2115.26 |                1612.12 |           23.8 |                    4 |               2 |               1 |              0.1368 |         0.1357 |                 51.74 |            49.33 |        1.377 |                    0 |
|           50 |      55 |         3 |                     4947.4  |                4198.51 |           15.1 |                   12 |               9 |               8 |              0.1445 |         0.1437 |                 46.39 |            44.49 |        2.023 |                    0 |
|          100 |     106 |         6 |                     9518.53 |                8507.35 |           10.6 |                   23 |              19 |              15 |              0.1429 |         0.1416 |                 47.4  |            45.21 |        2.707 |                    0 |
|          200 |     210 |        12 |                    19532.2  |               17294    |           11.5 |                   48 |              39 |              32 |              0.1432 |         0.1419 |                 47.49 |            45.26 |        1.935 |                    0 |
|          400 |     404 |        23 |                    41572.6  |               35607.8  |           14.3 |                  107 |              82 |              68 |              0.1445 |         0.1443 |                 46.46 |            43.53 |        8.606 |                    0 |

## Lectura de cada KPI (y si es valido o hay que modificarlo)

- **Costo total:** E1 cuesta 3.751.250 USD/dia frente a 3.958.063 de E0 (5.2% menos). La flota es 69% del costo de E1 y las reservas 15%; la energia, solo 8%. Valido como objetivo; la energia pesa poco, por eso programar la carga rinde mas por las reservas que por la tarifa.
- **Buses:** el VSP baja de 8.654 (E0) a 7.366 (E1), a 4.4% de LB; tras la carga, E1 necesita 10.295 y con reservas 12.502. **El KPI "buses" del VSP solo no es suficiente**: ignora la bateria; hay que reportar siempre el numero tras la carga.
- **% km vacios:** 13.31% (E0) y 11.96% (E1) en el VSP; sube a 15.21% en E1 tras la carga (traslados de jornadas partidas).
- **Energia:** 0.1396 USD/kWh y 51.39% en valle (E1); es la politica reactiva, sin mirar la tarifa.
- **Uso de electroterminales:** el uso maximo es 100% en todos. En Los Espinos + Santa Rosa, El Conquistador y La Reina el uso promedio de las 24 h es 81-88% y los puestos estan todos ocupados 71-79% del dia (la carga nocturna los satura); Vespucio Norte queda holgado (35%, 26% del dia saturado). El KPI util es el % del dia saturado, que mide la congestion; el promedio solo no distingue un terminal siempre lleno de uno lleno solo de noche. Casi no cambia entre E0 y E1: el interlining no alivia la carga.
- **Utilizacion del bus:** 71.8% de las horas de jornada con pasajeros en el VSP de E1 (70.3% tras la carga, que incluye las esperas de carga). Es un KPI descriptivo; no decide nada por si solo.
- **Jornadas partidas y ciclos no cumplidos:** 2.929 partidas y 2.207 ciclos no cumplidos en E1: es lo que mide cuanto cuesta la miopia de la politica y de la descomposicion.
- **Espera por puesto en el patio:** el caso base la cobra (0,03 USD/min a buses estacionados esperando puesto) y el VSP no cobra el estacionamiento. Se mantiene como cota conservadora; la fila "total sin espera por puesto" muestra que no cambia ninguna conclusion (decision B12 en `docs/context/02`). Queda como pregunta para el profesor.
- **Precio de la descomposicion:** exigir el retorno al electroterminal y limitar el interlining al grupo cuesta ~4% de flota frente a LB; ignorar la bateria en el VSP cuesta casi 70% de flota. El segundo es el hallazgo central (C9) y la mejora principal para la entrega final: un VSP que vea la bateria.

## Archivos

- `tablas/kpis_escenarios.csv`: tabla de KPIs (columnas E0, E1, LB).
- `tablas/desglose_costo.csv`: costo total por componente.
- `tablas/precio_descomposicion.csv`: buses y costo de cada decision (interlining, retorno, bateria).
- `tablas/uso_electroterminales.csv`: uso maximo, promedio y % del dia saturado por electroterminal.
- `tablas/milp_instancia.csv`: valor del MILP por tamano de instancia (instancia reducida).
- `graficos/costo_desglose_E0_E1.png`: costo total apilado por componente, E0 frente a E1.
- `graficos/flota_de_donde_viene.png`: de la cota 6.539 a los buses de E1 tras la carga y las reservas.
- `graficos/uso_electroterminales.png`: uso promedio y % del dia saturado por electroterminal.