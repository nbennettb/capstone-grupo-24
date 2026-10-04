# Reporte Etapa 1 - Clustering de rutas a electroterminales (ciclo diario)

**C1b** (el electroterminal mas cercano a los paraderos terminales reales de cada ruta) es la asignacion base de la entrega y se llama simplemente 'C1' en el relato. **C1a** (distancia al centroide) es un control de sensibilidad: no la usa ninguna etapa posterior. **C2** (MILP con capacidad bajo la condicion ciclica) es la **propuesta** que se formula y se prueba, pero no entra al caso base.

## Comparacion bajo criterio comun (distancia a paraderos terminales reales)

| estrategia                            |   distancia_media_km |   distancia_p90_km |   distancia_max_km |   costo_pullout_pullin_usd_dia |   rutas_distintas_de_c1b |
|:--------------------------------------|---------------------:|-------------------:|-------------------:|-------------------------------:|-------------------------:|
| C1a (centroide)                       |               10.195 |             15.488 |             21.255 |                          83843 |                       41 |
| C1b (terminales reales)               |               10.149 |             15.424 |             20.991 |                          83271 |                        0 |
| C2 (MILP con capacidad, ciclo diario) |               10.149 |             15.424 |             20.991 |                          83276 |                        5 |

## Capacidad bajo ciclo diario (theta = 1, H = 24 h)

| electroterminal          |   h_r_asignadas |   capacidad |   uso_pct |   uso_c1b_con_carga_corregida_pct |
|:-------------------------|----------------:|------------:|----------:|----------------------------------:|
| Vespucio Norte           |          1213.1 |        3600 |      33.7 |                              33.7 |
| El Conquistador          |          3490.8 |        4320 |      80.8 |                              79.1 |
| Los Espinos              |          2810.2 |        2880 |      97.6 |                             101.6 |
| La Reina                 |          1829   |        2400 |      76.2 |                              76.2 |
| Santa Rosa               |          2416.6 |        3600 |      67.1 |                              65.9 |
| Los Espinos + Santa Rosa |          5226.8 |        6480 |      80.7 |                              81.8 |

La carga de cada ruta incluye su pullout y pullin (depende del electroterminal): ver `tablas/validacion_carga_c2.csv`. Con esa carga, la asignacion C1b (mas cercano, sin capacidad) excede la capacidad donde `uso_c1b_con_carga_corregida_pct` pasa de 100%; C2 mueve 5 rutas para respetarla (uso maximo de C2: 97.6% en Los Espinos).
- C2 ve un promedio diario en horas-cargador; la carga real se concentra en ciertas horas, y esa saturacion horaria la mide el simulador de carga reactiva (colas de espera), no C2.

## Validacion del estimador de carga contra la energia real de las jornadas (asignacion C1b)

| escenario   | electroterminal   |   capacidad_mwh_dia |   energia_real_jornadas_mwh |   solo_comercial_mwh |   estimador_c2_mwh |   error_solo_comercial_pct |   error_estimador_c2_pct |   uso_real_pct |   uso_solo_comercial_pct |   uso_estimador_c2_pct |
|:------------|:------------------|--------------------:|----------------------------:|---------------------:|-------------------:|---------------------------:|-------------------------:|---------------:|-------------------------:|-----------------------:|
| E0          | Vespucio Norte    |               648   |                      221.08 |               200.46 |             218.36 |                      -9.33 |                    -1.23 |          34.12 |                    30.94 |                  33.7  |
| E0          | El Conquistador   |               777.6 |                      632.57 |               542.98 |             615.45 |                     -14.16 |                    -2.71 |          81.35 |                    69.83 |                  79.15 |
| E0          | Los Espinos       |               518.4 |                      539.39 |               466.14 |             526.47 |                     -13.58 |                    -2.4  |         104.05 |                    89.92 |                 101.56 |
| E0          | La Reina          |               432   |                      338.93 |               294.38 |             329.22 |                     -13.14 |                    -2.87 |          78.46 |                    68.14 |                  76.21 |
| E0          | Santa Rosa        |               648   |                      440.87 |               379.61 |             427.24 |                     -13.89 |                    -3.09 |          68.04 |                    58.58 |                  65.93 |
| E1          | Vespucio Norte    |               648   |                      219.47 |               200.46 |             218.36 |                      -8.66 |                    -0.51 |          33.87 |                    30.94 |                  33.7  |
| E1          | El Conquistador   |               777.6 |                      621.58 |               542.98 |             615.45 |                     -12.65 |                    -0.99 |          79.94 |                    69.83 |                  79.15 |
| E1          | Los Espinos       |               518.4 |                      531.7  |               466.14 |             526.47 |                     -12.33 |                    -0.98 |         102.57 |                    89.92 |                 101.56 |
| E1          | La Reina          |               432   |                      335.97 |               294.38 |             329.22 |                     -12.38 |                    -2.01 |          77.77 |                    68.14 |                  76.21 |
| E1          | Santa Rosa        |               648   |                      434.8  |               379.61 |             427.24 |                     -12.69 |                    -1.74 |          67.1  |                    58.58 |                  65.93 |

## Barrido de theta (rutas movidas respecto de C2 con theta = 1)

| capacidad   |   theta | factible   |   rutas_movidas |   costo_asignacion_usd_dia |   uso_max_pct | depot_mas_cargado        |
|:------------|--------:|:-----------|----------------:|---------------------------:|--------------:|:-------------------------|
| separada    |     1   | True       |               0 |                      83276 |          97.6 | Los Espinos              |
| separada    |     0.9 | True       |               8 |                      83273 |          99.8 | Los Espinos              |
| separada    |     0.8 | True       |              14 |                      83304 |          99.9 | Los Espinos              |
| separada    |     0.7 | False      |             nan |                        nan |         nan   | nan                      |
| combinada   |     1   | True       |               5 |                      83271 |          81.8 | Los Espinos + Santa Rosa |
| combinada   |     0.9 | True       |               5 |                      83271 |          90.8 | Los Espinos + Santa Rosa |
| combinada   |     0.8 | True       |               8 |                      83299 |         100   | El Conquistador          |
| combinada   |     0.7 | False      |             nan |                        nan |         nan   | nan                      |

Capacidad `separada` = una restriccion por electroterminal; `combinada` = Los Espinos y Santa Rosa comparten una bolsa de 270 puestos. Las rutas movidas se miden contra la asignacion con theta = 1. Es evidencia secundaria: el efecto real de unir esos dos terminales esta en el interlining (Etapa 2, E1 frente a E1_sep) y en la carga (Etapa 3).

## Evidencia: sin recuperacion vs con recuperacion, al mismo nivel (proxy por ruta, sin deadhead)

Sin recuperacion: los buses parten con el nivel indicado y no lo recuperan al terminar (solo se paga el excedente sobre la bateria util). Con recuperacion: condicion ciclica, se paga todo lo consumido. Totales de los 5 electroterminales (detalle por electroterminal en `tablas/capacidad_sin_vs_con_recuperacion.csv`):

|   nivel_soc_pct |   h_cargador_dia - Con recuperacion (ciclo) |   h_cargador_dia - Sin recuperacion |   uso_pct - Con recuperacion (ciclo) |   uso_pct - Sin recuperacion |
|----------------:|--------------------------------------------:|------------------------------------:|-------------------------------------:|-----------------------------:|
|             100 |                                     11759.7 |                              374.65 |                                   70 |                         2.23 |
|              90 |                                     11759.7 |                             1053.66 |                                   70 |                         6.27 |
|              80 |                                     11759.7 |                             2105.56 |                                   70 |                        12.53 |
|              70 |                                     11759.7 |                             3352.5  |                                   70 |                        19.96 |

- Al nivel 100% (el maximo de los datos), sin recuperacion solo se recargarian 67 MWh de 2,117 MWh consumidos, y los puestos usarian 2.2% de su capacidad (con recuperacion: 70.0%).
- Con recuperacion, la energia a recargar y la asignacion de C2 no dependen del nivel: el nivel solo cambia cuantas jornadas recargan a mitad del dia, y eso se mide en el barrido de niveles con el simulador de carga reactiva (el nivel base lo elige el costo total, ver docs/context/02_supuestos_y_decisiones.md, B6).
- Estas cifras son un PROXY POR RUTA (kWh comerciales, sin pullout/pullin). La medicion por jornada se produce en la Etapa 2, con las jornadas regeneradas.

## Rutas por electroterminal, por estrategia

| depot_nombre    |   C1a (centroide) |   C1b (terminales reales) |   C2 (MILP con capacidad, ciclo diario) |
|:----------------|------------------:|--------------------------:|----------------------------------------:|
| El Conquistador |                98 |                       108 |                                     109 |
| La Reina        |                64 |                        67 |                                      67 |
| Los Espinos     |                85 |                        88 |                                      83 |
| Santa Rosa      |               111 |                        98 |                                     102 |
| Vespucio Norte  |                59 |                        56 |                                      56 |

## Rutas que la capacidad obliga a mover, de C1b a C2 (mapa de diferencias): 5

## Indice de esta carpeta

Tablas (`tablas/`):
- `comparacion_estrategias.csv`: distancia y costo de pullout/pullin de C1a, C1b y C2 bajo el mismo criterio.
- `resumen_por_terminal.csv`: rutas, buses estimados, km y kWh por electroterminal y estrategia.
- `rutas_que_cambian.csv`: cada ruta que cambia de electroterminal entre estrategias.
- `distancias_ruta_terminal.csv`: distancia de cada ruta a cada electroterminal (centroide y paraderos reales).
- `capacidad_por_terminal.csv`: horas-cargador asignadas vs capacidad, bajo ciclo diario, y el uso que tendria la asignacion C1b con la misma carga (incluye la fila combinada Los Espinos + Santa Rosa).
- `validacion_carga_c2.csv`: energia por electroterminal estimada por C2 vs la real de las jornadas del VSP.
- `capacidad_sin_vs_con_recuperacion.csv`: sin recuperacion vs con recuperacion al mismo nivel de bateria (proxy por ruta).
- `barrido_theta.csv`: rutas movidas y uso maximo al apretar la capacidad, separada y combinada.

Graficos (`graficos/`):
- `rutas_por_terminal.png`: rutas por electroterminal en las 3 estrategias.
- `distancias.png`: distancias ruta-electroterminal (C1a vs C1b).
- `capacidad_ciclo.png`: carga asignada vs capacidad bajo ciclo diario.
- `capacidad_sin_vs_con_recuperacion.png`: uso de capacidad sin vs con recuperacion, por electroterminal y segun el nivel.
- `barrido_theta.png`: rutas movidas y uso maximo segun theta.

Mapas (`mapas/`): `mapa_c1a.png`, `mapa_c1b.png`, `mapa_c2.png` (rutas coloreadas por electroterminal), `mapa_terminal_<nombre>.png` (x5, rutas de cada electroterminal bajo C2), `mapa_paraderos_terminales.png` (641 paraderos por electroterminal mas cercano) y `mapa_diferencias.png` (rutas que cambian de C1b a C2: las que la capacidad obliga a mover).

Tabla ancha por ruta: `data-processed/rutas_clustering_completo.csv`.

*(Ver docs/context/01_metodologia.md para la interpretacion completa y las decisiones que este resultado habilita o deja pendientes.)*