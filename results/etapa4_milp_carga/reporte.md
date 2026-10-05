# Reporte Etapa 4 - MILP de programacion de carga (INSTANCIA REDUCIDA)

> **Instancia reducida:** muestra de jornadas del terminal Los Espinos + Santa Rosa (escenario E1, nivel 100%) con semilla 24. **No es el resultado de toda la red**: el MILP sobre la red completa (E3) solo se estima.

## Que se resolvio

Para cada bus, dentro de su ventana en el patio (llegada hasta su primera salida del dia siguiente), el MILP decide en cuales de los 96 bloques de 15 min del dia carga y cuanta energia, minimizando energia (tarifa del bloque) + 5 USD por evento de carga + 250 USD por bus de reserva, sin pasar los puestos. Resuelve las 24 horas de una vez: los bloques son solo la unidad de medida del tiempo, no una descomposicion temporal. Un **bus de reserva** (r = 1) puede terminar de cargar despues de su salida (hasta 24 h desde su llegada) y su salida la cubre otro bus ya cargado: es la misma regla del simulador. La energia se carga igual y ocupa puestos. Las cargas intermedias (0,5% de los buses) quedan fijas como las dejo la reactiva. La espera en cola no esta en el objetivo: se reporta como demora hasta iniciar la carga.

## Instancias

|   N_objetivo |   jornadas_vsp |   buses |   puestos |   puestos_por_bus |   semilla |   jornadas_partidas | jornadas_partidas_igual_que_red   |   cargas_intermedias_fijas |   energia_mwh |   carga_pct_capacidad |   saturacion_reactiva_pct |   saturacion_milp_pct |   cota_lp_pct |   no_trivial |   n_binarias |   n_variables |   n_restricciones |   reservas_cota |   reservas_milp_bloques |   reservas_milp_al_minuto |
|-------------:|---------------:|--------:|----------:|------------------:|----------:|--------------------:|:----------------------------------|---------------------------:|--------------:|----------------------:|--------------------------:|----------------------:|--------------:|-------------:|-------------:|--------------:|------------------:|----------------:|------------------------:|--------------------------:|
|           10 |              7 |       9 |         1 |            0.1111 |        24 |                   2 | 7/7                               |                          0 |          1.92 |                  44.5 |                      49   |                  49   |         100   |            1 |          873 |          2601 |              3130 |               0 |                       0 |                         0 |
|           30 |             21 |      34 |         2 |            0.0588 |        24 |                  13 | 21/21                             |                          0 |          6.91 |                  80   |                      82.3 |                  85.4 |          96.1 |            1 |         3298 |          9826 |             11488 |               1 |                       2 |                         2 |
|           50 |             35 |      55 |         3 |            0.0545 |        24 |                  20 | 35/35                             |                          0 |         11.58 |                  89.3 |                      95.8 |                  94.8 |          81.1 |            1 |         5335 |         15895 |             18658 |               8 |                       9 |                         9 |
|          100 |             69 |     106 |         6 |            0.0566 |        24 |                  37 | 69/69                             |                          0 |         22.66 |                  87.4 |                      92.7 |                  83.3 |          79.9 |            1 |        10282 |         30634 |             35931 |              15 |                      19 |                        19 |
|          200 |            139 |     210 |        12 |            0.0571 |        24 |                  71 | 139/139                           |                          2 |         45.2  |                  87.2 |                      91.7 |                  83.3 |          78.5 |            1 |        20370 |         60690 |             71113 |              32 |                      39 |                        39 |
|          400 |            277 |     404 |        23 |            0.0569 |        24 |                 127 | 277/277                           |                          2 |         88.53 |                  89.1 |                      94.8 |                  84.4 |          76.6 |            1 |        39188 |        116756 |            137136 |              68 |                      82 |                        82 |

`no_trivial` = puestos saturados en al menos 10% de los bloques en la reactiva. `jornadas_partidas_igual_que_red` = jornadas muestreadas que el simulador parte (o no) igual que en la corrida de la red completa.

## Comparacion reactiva vs MILP (mismos buses, mismos puestos)

`reactiva_minuto` es el simulador de la Etapa 3 (la politica real, al minuto); `reactiva_bloques` es la misma regla en la grilla de 15 min del MILP: es la solucion inicial que se le entrega y la prueba de correctitud (el MILP debe costar menos o igual). **La referencia para el valor de la carga inteligente es `reactiva_minuto`**: la grilla de 15 min es conservadora y encarece la reactiva en bloques (mas reservas), de modo que compararse con ella infla la ganancia. Costo de la carga = energia + eventos + reservas (flota, km y espera del VSP son iguales en ambas).

|   N_objetivo | variante         |   buses |   kwh_cargados |   costo_energia_usd |   usd_por_kwh |   pct_energia_valle |   eventos_carga |   buses_reserva |   costo_reservas_usd |   costo_carga_total_usd |   demora_inicio_carga_h |   saturacion_pct |
|-------------:|:-----------------|--------:|---------------:|--------------------:|--------------:|--------------------:|----------------:|----------------:|---------------------:|------------------------:|------------------------:|-----------------:|
|           10 | milp             |       9 |         1923.3 |              207.84 |        0.1081 |               87.44 |               9 |               0 |                    0 |                  252.84 |                    63.3 |             49   |
|           10 | milp_al_minuto   |       9 |         1923.3 |              207.84 |        0.1081 |               87.44 |               9 |               0 |                    0 |                  252.84 |                    63.3 |             49   |
|           10 | reactiva_bloques |       9 |         1923.3 |              230.58 |        0.1199 |               84.95 |               9 |               0 |                    0 |                  275.58 |                    37.3 |             49   |
|           10 | reactiva_minuto  |       9 |         1923.3 |              237.48 |        0.1235 |               81.99 |               9 |               0 |                    0 |                  282.48 |                    32   |             44.9 |
|           30 | milp             |      34 |         6908.2 |              937.12 |        0.1357 |               49.33 |              35 |               2 |                  500 |                 1612.12 |                   255.3 |             85.4 |
|           30 | milp_al_minuto   |      34 |         6908.2 |              937.12 |        0.1357 |               49.33 |              35 |               2 |                  500 |                 1612.12 |                   255.3 |             85.4 |
|           30 | reactiva_bloques |      34 |         6908.2 |              983.96 |        0.1424 |               48.07 |              34 |               6 |                 1500 |                 2653.96 |                   234.8 |             82.3 |
|           30 | reactiva_minuto  |      34 |         6908.2 |              945.26 |        0.1368 |               51.74 |              34 |               4 |                 1000 |                 2115.26 |                   197.1 |             71.1 |
|           50 | milp             |      55 |        11576.1 |             1663.51 |        0.1437 |               44.49 |              57 |               9 |                 2250 |                 4198.51 |                   485   |             94.8 |
|           50 | milp_al_minuto   |      55 |        11576.1 |             1663.51 |        0.1437 |               44.49 |              57 |               9 |                 2250 |                 4198.51 |                   485   |             94.8 |
|           50 | reactiva_bloques |      55 |        11576.1 |             1684.74 |        0.1455 |               43.1  |              55 |              17 |                 4250 |                 6209.74 |                   481.5 |             95.8 |
|           50 | reactiva_minuto  |      55 |        11576.1 |             1672.4  |        0.1445 |               46.39 |              55 |              12 |                 3000 |                 4947.4  |                   428.2 |             83.1 |
|          100 | milp             |     106 |        22656.8 |             3207.35 |        0.1416 |               45.21 |             110 |              19 |                 4750 |                 8507.35 |                   916.8 |             83.3 |
|          100 | milp_al_minuto   |     106 |        22656.8 |             3207.35 |        0.1416 |               45.21 |             110 |              19 |                 4750 |                 8507.35 |                   916.8 |             83.3 |
|          100 | reactiva_bloques |     106 |        22656.8 |             3285.96 |        0.145  |               43.81 |             106 |              33 |                 8250 |                12066    |                   873.3 |             92.7 |
|          100 | reactiva_minuto  |     106 |        22656.8 |             3238.53 |        0.1429 |               47.4  |             106 |              23 |                 5750 |                 9518.53 |                   761.9 |             80.6 |
|          200 | milp             |     210 |        45195.4 |             6413.95 |        0.1419 |               45.26 |             226 |              39 |                 9750 |                17294    |                  1786.2 |             83.3 |
|          200 | milp_al_minuto   |     210 |        45195.4 |             6413.95 |        0.1419 |               45.26 |             226 |              39 |                 9750 |                17294    |                  1786.2 |             83.3 |
|          200 | reactiva_bloques |     210 |        45195.4 |             6551.31 |        0.145  |               44.13 |             212 |              61 |                15250 |                22861.3  |                  1734.2 |             91.7 |
|          200 | reactiva_minuto  |     210 |        45195.4 |             6472.16 |        0.1432 |               47.49 |             212 |              48 |                12000 |                19532.2  |                  1517.6 |             79.8 |
|          400 | milp             |     404 |        88533.3 |            12777.8  |        0.1443 |               43.53 |             466 |              82 |                20500 |                35607.8  |                  3400.6 |             84.4 |
|          400 | milp_al_minuto   |     404 |        88533.3 |            12777.8  |        0.1443 |               43.53 |             466 |              82 |                20500 |                35607.8  |                  3400.6 |             84.4 |
|          400 | reactiva_bloques |     404 |        88533.3 |            12868.4  |        0.1454 |               43.27 |             406 |             130 |                32500 |                47398.4  |                  3377.9 |             94.8 |
|          400 | reactiva_minuto  |     404 |        88533.3 |            12792.6  |        0.1445 |               46.46 |             406 |             107 |                26750 |                41572.6  |                  2961.7 |             80.6 |

### Valor de la carga inteligente (MILP frente a las dos reactivas)

El MILP trabaja en bloques de 15 min (restringen sus opciones) y su programa se **ejecuta al minuto** (`milp_al_minuto`): se verifica que respeta los puestos minuto a minuto y se recalculan sus reservas reales. Esa es la ganancia frente al simulador real; es una **cota inferior** del valor de optimizar, porque el optimo al minuto seria igual o mejor y la brecha deja margen.

|   N_objetivo |   costo_reactiva_minuto_usd |   costo_reactiva_bloques_usd |   costo_milp_bloques_usd |   costo_milp_al_minuto_usd |   ganancia_vs_simulador_pct |   ganancia_vs_reactiva_bloques_pct |   reservas_simulador |   reservas_reactiva_bloques |   reservas_milp_bloques |   reservas_milp_al_minuto |
|-------------:|----------------------------:|-----------------------------:|-------------------------:|---------------------------:|----------------------------:|-----------------------------------:|---------------------:|----------------------------:|------------------------:|--------------------------:|
|           10 |                      282.48 |                       275.58 |                   252.84 |                     252.84 |                        10.5 |                                8.3 |                    0 |                           0 |                       0 |                         0 |
|           30 |                     2115.26 |                      2653.96 |                  1612.12 |                    1612.12 |                        23.8 |                               39.3 |                    4 |                           6 |                       2 |                         2 |
|           50 |                     4947.4  |                      6209.74 |                  4198.51 |                    4198.51 |                        15.1 |                               32.4 |                   12 |                          17 |                       9 |                         9 |
|          100 |                     9518.53 |                     12066    |                  8507.35 |                    8507.35 |                        10.6 |                               29.5 |                   23 |                          33 |                      19 |                        19 |
|          200 |                    19532.2  |                     22861.3  |                 17294    |                   17294    |                        11.5 |                               24.4 |                   48 |                          61 |                      39 |                        39 |
|          400 |                    41572.6  |                     47398.4  |                 35607.8  |                   35607.8  |                        14.3 |                               24.9 |                  107 |                         130 |                      82 |                        82 |

### Variacion del MILP respecto de la reactiva en bloques

|   N_objetivo |   d_costo_total_usd |   d_costo_total_pct |   d_energia_usd |   d_usd_por_kwh |   d_pct_valle |   d_eventos |   d_reservas |   d_costo_reservas_usd |
|-------------:|--------------------:|--------------------:|----------------:|----------------:|--------------:|------------:|-------------:|-----------------------:|
|           10 |               -22.7 |               -8.25 |           -22.7 |         -0.0118 |          2.49 |           0 |            0 |                      0 |
|           30 |             -1041.8 |              -39.26 |           -46.8 |         -0.0067 |          1.26 |           1 |           -4 |                  -1000 |
|           50 |             -2011.2 |              -32.39 |           -21.2 |         -0.0018 |          1.39 |           2 |           -8 |                  -2000 |
|          100 |             -3558.6 |              -29.49 |           -78.6 |         -0.0034 |          1.4  |           4 |          -14 |                  -3500 |
|          200 |             -5567.4 |              -24.35 |          -137.4 |         -0.0031 |          1.13 |          14 |          -22 |                  -5500 |
|          400 |            -11790.6 |              -24.88 |           -90.6 |         -0.0011 |          0.26 |          60 |          -48 |                 -12000 |

## Tiempo de resolucion

|   N_objetivo |   buses |   segundos | estado           |   brecha_pct |   cota_inferior_usd |   objetivo_usd |   brecha_usd |   resuelta_optimo |
|-------------:|--------:|-----------:|:-----------------|-------------:|--------------------:|---------------:|-------------:|------------------:|
|           10 |       9 |        2.6 | optimo           |        0.262 |              252.18 |         252.84 |         0.66 |                 1 |
|           30 |      34 |      600.1 | limite de tiempo |        1.377 |             1589.92 |        1612.12 |        22.2  |                 0 |
|           50 |      55 |      600.1 | limite de tiempo |        2.023 |             4113.57 |        4198.51 |        84.94 |                 0 |
|          100 |     106 |      600.2 | limite de tiempo |        2.707 |             8277.06 |        8507.35 |       230.29 |                 0 |
|          200 |     210 |      600.3 | limite de tiempo |        1.935 |            16931.3  |       17265.4  |       334.17 |                 0 |
|          400 |     404 |      601.9 | limite de tiempo |        8.606 |            32517.1  |       35579.2  |      3062.11 |                 0 |


- Instancias que **no** alcanzaron la brecha pedida (1%) en 600 s: [30, 50, 100, 200, 400]. **Resueltas al optimo (brecha <= 1%): [10].** La brecha es la distancia entre la mejor solucion y la cota de Gurobi: la solucion es factible y verificada, pero su optimalidad solo esta certificada hasta esa brecha (la ganancia real es al menos la medida).
- **Regla declarada antes de correr:** solo se llama 'resuelta al optimo' a una instancia con brecha <= 1% certificada por Gurobi; las demas son soluciones factibles verificadas, con su brecha en % y en USD y la cota de reservas (`reservas_cota`: ningun programa de carga puede tener menos reservas, calculada con una relajacion en segundos).

## Representatividad de la instancia

| metrica                                  |   red_completa |     N=10 |     N=30 |     N=50 |    N=100 |    N=200 |    N=400 |
|:-----------------------------------------|---------------:|---------:|---------:|---------:|---------:|---------:|---------:|
| buses (cargas finales)                   |      4622      |   9      |  34      |  55      | 106      | 210      | 404      |
| puestos                                  |       270      |   1      |   2      |   3      |   6      |  12      |  23      |
| puestos por bus                          |         0.0584 |   0.1111 |   0.0588 |   0.0545 |   0.0566 |   0.0571 |   0.0569 |
| % llegadas entre 19:00 y 02:00           |        90      | 100      |  91.2    |  94.5    |  92.5    |  92.4    |  92.3    |
| % salidas entre 04:00 y 08:00            |        62.6    |  66.7    |  47.1    |  52.7    |  57.5    |  59      |  61.6    |
| ventana mediana en el patio (h)          |         8.98   |  10.36   |  10.37   |   9.15   |   9.13   |   9.1    |   8.92   |
| energia media a reponer (kWh)            |       217.3    | 213.7    | 203.2    | 210.5    | 213.7    | 214.7    | 218.9    |
| carga / capacidad de 24 h (%)            |        86.2    |  44.5    |  80      |  89.3    |  87.4    |  87.2    |  89.1    |
| % buses con ciclo no cumplido (reactiva) |        26.1    |   0      |  11.8    |  21.8    |  21.7    |  22.9    |  26.5    |
| USD/kWh (reactiva)                       |         0.142  |   0.1235 |   0.1368 |   0.1445 |   0.1429 |   0.1432 |   0.1445 |
| % energia en valle (reactiva)            |        48      |  81.99   |  51.74   |  46.39   |  47.4    |  47.49   |  46.46   |

## Chequeos que se hicieron en cada corrida (el script falla si alguno no se cumple)

- Las jornadas reconstruidas sin cargas calzan con el VSP (kWh por jornada).
- Cobertura y balance de energia del simulador sobre la instancia (los de `10-carga_reactiva.py`).
- El programa del MILP se ejecuta minuto a minuto: respeta los puestos y sus reservas reales son menores o iguales a las de bloques; la cota de reservas es menor o igual a las del MILP.
- La reactiva en bloques es factible para el MILP y se evalua con la misma funcion que la solucion del MILP.
- Solucion del MILP: energia exacta por bus, no mas de 45 kWh por bloque, bloques dentro de las 24 h desde la llegada, fuera de la ventana solo con reserva, puestos respetados en cada bloque, costo recalculado coherente con el objetivo y la cota de Gurobi.
- **Costo del MILP <= costo de la reactiva en bloques.**

## Limitaciones

- Instancia reducida: muestra aleatoria con semilla fija de un solo terminal; extrapolar a toda la red es una estimacion.
- Bloques de 15 min: un bus solo puede usar bloques que su ventana cubre completos (error conservador de hasta 15 min en los bordes).
- Las cargas intermedias quedan fijas (0,5% de los buses); no se re-optimizan.
- Las ventanas vienen de las jornadas del VSP, que ignora la bateria: el MILP optimiza cuando cargar, no cambia la flota ni las jornadas.
- Carga lineal a 180 kW; un solo dia laboral.

## Archivos

- `tablas/instancias.csv`: una fila por tamano: muestra, puestos, carga, saturacion, cota LP, tamano del modelo.
- `tablas/comparacion_reactiva_milp.csv`: tabla de comparacion (reactiva al minuto, reactiva en bloques, MILP).
- `tablas/tiempos_resolucion.csv`: tiempo, estado y brecha del MILP por N.
- `tablas/representatividad.csv`: la instancia contra el terminal completo de la red.
- `tablas/energia_por_tarifa.csv`: energia cargada por periodo tarifario, reactiva vs MILP.
- `tablas/ocupacion_N<n>.csv`: buses cargando por bloque de 15 min (reactiva y MILP), puestos y tarifa.
- `tablas/programa_reactiva_N<n>.csv` y `programa_milp_N<n>.csv`: bloques de carga de cada bus.
- `graficos/ocupacion_reactiva_vs_milp_N<n>.png`: buses cargando durante el dia, reactiva vs MILP, contra los puestos.
- `graficos/energia_por_tarifa.png`: % de la energia por periodo tarifario (mayor N).
- `graficos/costo_reactiva_vs_milp.png`: costo de la carga por bus, apilado, simulador real vs MILP, por N.
- `graficos/brecha_vs_N.png`: brecha de optimalidad alcanzada en el limite de tiempo, por tamano de instancia.