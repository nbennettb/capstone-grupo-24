# Reporte Etapa 1 - Clustering de rutas a electroterminales (ciclo diario)

Compara C1a (heuristica, centroide), C1b (heuristica, paraderos terminales reales) y C2 (MILP con capacidad, bajo ciclo diario: cada bus empieza y termina el dia con el mismo nivel de bateria, asi que se recarga todo lo consumido).

## Comparacion bajo criterio comun (distancia a paraderos terminales reales)

| estrategia                            |   distancia_media_km |   distancia_p90_km |   distancia_max_km |   costo_pullout_pullin_usd_dia |   rutas_distintas_de_c1b |
|:--------------------------------------|---------------------:|-------------------:|-------------------:|-------------------------------:|-------------------------:|
| C1a (centroide)                       |               10.195 |             15.488 |             21.255 |                          83843 |                       41 |
| C1b (terminales reales)               |               10.149 |             15.424 |             20.991 |                          83271 |                        0 |
| C2 (MILP con capacidad, ciclo diario) |               10.149 |             15.424 |             20.991 |                          83271 |                        0 |

## Capacidad bajo ciclo diario (theta = 1, H = 24 h)

| electroterminal          |   h_r_asignadas |   capacidad |   uso_pct |
|:-------------------------|----------------:|------------:|----------:|
| Vespucio Norte           |          1113.7 |        3600 |      30.9 |
| El Conquistador          |          3016.6 |        4320 |      69.8 |
| Los Espinos              |          2589.7 |        2880 |      89.9 |
| La Reina                 |          1635.5 |        2400 |      68.1 |
| Santa Rosa               |          2109   |        3600 |      58.6 |
| Los Espinos + Santa Rosa |          4698.6 |        6480 |      72.5 |

- C2 coincide EXACTAMENTE con C1b: con theta = 1 la restriccion de capacidad AGREGADA DIARIA no esta activa (uso maximo 89.9% en Los Espinos).
- Eso NO significa que la capacidad no importe. C2 ve un promedio diario en horas-cargador; la carga real se concentra en ciertas horas, y esa saturacion horaria la medira el simulador de carga reactiva (colas de espera), no C2.

## Barrido de theta -- a partir de cuando C2 se separa de C1b

| capacidad   |   theta | factible   |   rutas_movidas |   costo_asignacion_usd_dia |   uso_max_pct | depot_mas_cargado        |
|:------------|--------:|:-----------|----------------:|---------------------------:|--------------:|:-------------------------|
| separada    |     1   | True       |               0 |                      83271 |          89.9 | Los Espinos              |
| separada    |     0.9 | True       |               0 |                      83271 |          99.9 | Los Espinos              |
| separada    |     0.8 | True       |              11 |                      83273 |          98.5 | Los Espinos              |
| separada    |     0.7 | True       |              21 |                      83333 |         100   | El Conquistador          |
| separada    |     0.6 | False      |             nan |                        nan |         nan   | nan                      |
| combinada   |     1   | True       |               0 |                      83271 |          72.5 | Los Espinos + Santa Rosa |
| combinada   |     0.9 | True       |               0 |                      83271 |          80.6 | Los Espinos + Santa Rosa |
| combinada   |     0.8 | True       |               0 |                      83271 |          90.6 | Los Espinos + Santa Rosa |
| combinada   |     0.7 | True       |               9 |                      83328 |          99.9 | El Conquistador          |
| combinada   |     0.6 | False      |             nan |                        nan |         nan   | nan                      |

Capacidad `separada` = una restriccion por electroterminal; `combinada` = Los Espinos y Santa Rosa comparten una bolsa de 270 puestos. Las rutas movidas se miden contra la asignacion con theta = 1. Es evidencia secundaria: el efecto real de unir esos dos terminales esta en el interlining (Etapa 2, escenario E2b).

## Evidencia: sin recuperacion vs con recuperacion, al mismo nivel (proxy por ruta, sin deadhead)

Sin recuperacion: los buses parten con el nivel indicado y no lo recuperan al terminar (solo se paga el excedente sobre la bateria util). Con recuperacion: condicion ciclica, se paga todo lo consumido. Totales de los 5 electroterminales (detalle por electroterminal en `tablas/capacidad_sin_vs_con_recuperacion.csv`):

|   nivel_soc_pct |   h_cargador_dia - Con recuperacion (ciclo) |   h_cargador_dia - Sin recuperacion |   uso_pct - Con recuperacion (ciclo) |   uso_pct - Sin recuperacion |
|----------------:|--------------------------------------------:|------------------------------------:|-------------------------------------:|-----------------------------:|
|             100 |                                     10464.3 |                              107.86 |                                62.29 |                         0.64 |
|              90 |                                     10464.3 |                              380.33 |                                62.29 |                         2.26 |
|              80 |                                     10464.3 |                             1085.79 |                                62.29 |                         6.46 |
|              70 |                                     10464.3 |                             2200.75 |                                62.29 |                        13.1  |

- Al nivel 100% (el maximo de los datos), sin recuperacion solo se recargarian 19 MWh de 1,884 MWh consumidos, y los puestos usarian 0.6% de su capacidad (con recuperacion: 62.3%).
- Con recuperacion, la energia a recargar y la asignacion de C2 no dependen del nivel: el nivel solo cambia cuantas jornadas recargan a mitad del dia, y eso se mide en el barrido de niveles con el simulador de carga reactiva (el nivel base lo elige el costo total, ver docs/context/02_supuestos_y_decisiones.md, B6).
- Estas cifras son un PROXY POR RUTA (kWh comerciales, sin pullout/pullin). La medicion por jornada se produce en la Etapa 2, con las jornadas regeneradas.

## Rutas por electroterminal, por estrategia

| depot_nombre    |   C1a (centroide) |   C1b (terminales reales) |   C2 (MILP con capacidad, ciclo diario) |
|:----------------|------------------:|--------------------------:|----------------------------------------:|
| El Conquistador |                98 |                       108 |                                     108 |
| La Reina        |                64 |                        67 |                                      67 |
| Los Espinos     |                85 |                        88 |                                      88 |
| Santa Rosa      |               111 |                        98 |                                      98 |
| Vespucio Norte  |                59 |                        56 |                                      56 |

## Rutas que cambian de electroterminal entre C1a y C2 (mapa de diferencias): 41

## Indice de esta carpeta

Tablas (`tablas/`):
- `comparacion_estrategias.csv`: distancia y costo de pullout/pullin de C1a, C1b y C2 bajo el mismo criterio.
- `resumen_por_terminal.csv`: rutas, buses estimados, km y kWh por electroterminal y estrategia.
- `rutas_que_cambian.csv`: cada ruta que cambia de electroterminal entre estrategias.
- `distancias_ruta_terminal.csv`: distancia de cada ruta a cada electroterminal (centroide y paraderos reales).
- `capacidad_por_terminal.csv`: horas-cargador asignadas vs capacidad, bajo ciclo diario (incluye la fila combinada Los Espinos + Santa Rosa).
- `capacidad_sin_vs_con_recuperacion.csv`: sin recuperacion vs con recuperacion al mismo nivel de bateria (proxy por ruta).
- `barrido_theta.csv`: rutas movidas y uso maximo al apretar la capacidad, separada y combinada.

Graficos (`graficos/`):
- `rutas_por_terminal.png`: rutas por electroterminal en las 3 estrategias.
- `distancias.png`: distancias ruta-electroterminal (C1a vs C1b).
- `capacidad_ciclo.png`: carga asignada vs capacidad bajo ciclo diario.
- `capacidad_sin_vs_con_recuperacion.png`: uso de capacidad sin vs con recuperacion, por electroterminal y segun el nivel.
- `barrido_theta.png`: rutas movidas y uso maximo segun theta.

Mapas (`mapas/`): `mapa_c1a.png`, `mapa_c1b.png`, `mapa_c2.png` (rutas coloreadas por electroterminal), `mapa_terminal_<nombre>.png` (x5, rutas de cada electroterminal bajo C2), `mapa_paraderos_terminales.png` (641 paraderos por electroterminal mas cercano) y `mapa_diferencias.png` (rutas que cambian entre C1a y C2).

Tabla ancha por ruta: `data-processed/rutas_clustering_completo.csv`.

*(Ver docs/context/01_metodologia.md para la interpretacion completa y las decisiones que este resultado habilita o deja pendientes.)*