# Reporte Etapa 4 - MILP de programacion de carga (INSTANCIA REDUCIDA)

> **Instancia reducida:** muestra de jornadas del terminal Los Espinos + Santa Rosa (escenario E1, nivel 100%) con semilla 24. **No es el resultado de toda la red**: el MILP sobre la red completa (E3) solo se estima.

## Que se resolvio

Para cada bus, dentro de su ventana en el patio (llegada hasta su primera salida del dia siguiente), el MILP decide en cuales de los 96 bloques de 15 min del dia carga y cuanta energia, minimizando energia (tarifa del bloque) + 5 USD por evento de carga + 250 USD por bus de reserva, sin pasar los puestos. Resuelve las 24 horas de una vez: los bloques son solo la unidad de medida del tiempo, no una descomposicion temporal. Un **bus de reserva** (r = 1) puede terminar de cargar despues de su salida (hasta 24 h desde su llegada) y su salida la cubre otro bus ya cargado: es la misma regla del simulador. La energia se carga igual y ocupa puestos. Las cargas intermedias (0,5% de los buses) quedan fijas como las dejo la reactiva. La espera en cola no esta en el objetivo: se reporta como demora hasta iniciar la carga.

## Instancias

|   N_objetivo |   jornadas_vsp |   buses |   puestos |   puestos_por_bus |   semilla |   jornadas_partidas | jornadas_partidas_igual_que_red   |   cargas_intermedias_fijas |   energia_mwh |   carga_pct_capacidad |   saturacion_reactiva_pct |   saturacion_milp_pct |   cota_lp_pct |   no_trivial |   n_binarias |   n_variables |   n_restricciones |
|-------------:|---------------:|--------:|----------:|------------------:|----------:|--------------------:|:----------------------------------|---------------------------:|--------------:|----------------------:|--------------------------:|----------------------:|--------------:|-------------:|-------------:|--------------:|------------------:|
|           30 |             21 |      34 |         2 |            0.0588 |        24 |                  13 | 21/21                             |                          0 |          6.91 |                  80   |                      82.3 |                  86.5 |          96.1 |            1 |         3298 |          9826 |             11454 |
|           50 |             35 |      55 |         3 |            0.0545 |        24 |                  20 | 35/35                             |                          0 |         11.58 |                  89.3 |                      95.8 |                  94.8 |          81.1 |            1 |         5335 |         15895 |             18603 |
|          100 |             69 |     106 |         6 |            0.0566 |        24 |                  37 | 69/69                             |                          0 |         22.66 |                  87.4 |                      92.7 |                  86.5 |          79.9 |            1 |        10282 |         30634 |             35825 |
|          200 |            139 |     210 |        12 |            0.0571 |        24 |                  71 | 139/139                           |                          2 |         45.2  |                  87.2 |                      91.7 |                  81.2 |          78.5 |            1 |        20370 |         60690 |             70903 |
|          400 |            277 |     404 |        23 |            0.0569 |        24 |                 127 | 277/277                           |                          2 |         88.53 |                  89.1 |                      94.8 |                  88.5 |          76.6 |            1 |        39188 |        116756 |            136732 |

`no_trivial` = puestos saturados en al menos 10% de los bloques en la reactiva. `jornadas_partidas_igual_que_red` = jornadas muestreadas que el simulador parte (o no) igual que en la corrida de la red completa.

## Comparacion reactiva vs MILP (mismos buses, mismos puestos)

`reactiva_minuto` es el simulador de la Etapa 3 (la politica real, al minuto); `reactiva_bloques` es la misma regla en la grilla de 15 min del MILP: es la solucion inicial que se le entrega y la prueba de correctitud (el MILP debe costar menos o igual). **La referencia para el valor de la carga inteligente es `reactiva_minuto`**: la grilla de 15 min es conservadora y encarece la reactiva en bloques (mas reservas), de modo que compararse con ella infla la ganancia. Costo de la carga = energia + eventos + reservas (flota, km y espera del VSP son iguales en ambas).

|   N_objetivo | variante         |   buses |   kwh_cargados |   costo_energia_usd |   usd_por_kwh |   pct_energia_valle |   eventos_carga |   buses_reserva |   costo_reservas_usd |   costo_carga_total_usd |   demora_inicio_carga_h |   saturacion_pct |
|-------------:|:-----------------|--------:|---------------:|--------------------:|--------------:|--------------------:|----------------:|----------------:|---------------------:|------------------------:|------------------------:|-----------------:|
|           30 | milp             |      34 |         6908.2 |              941.29 |        0.1363 |               48.97 |              34 |               2 |                  500 |                 1611.29 |                   263.8 |             86.5 |
|           30 | reactiva_bloques |      34 |         6908.2 |              983.96 |        0.1424 |               48.07 |              34 |               6 |                 1500 |                 2653.96 |                   234.8 |             82.3 |
|           30 | reactiva_minuto  |      34 |         6908.2 |              945.26 |        0.1368 |               51.74 |              34 |               4 |                 1000 |                 2115.26 |                   197.1 |             71.1 |
|           50 | milp             |      55 |        11576.1 |             1663.28 |        0.1437 |               44.23 |              57 |               9 |                 2250 |                 4198.28 |                   489.2 |             94.8 |
|           50 | reactiva_bloques |      55 |        11576.1 |             1684.74 |        0.1455 |               43.1  |              55 |              17 |                 4250 |                 6209.74 |                   481.5 |             95.8 |
|           50 | reactiva_minuto  |      55 |        11576.1 |             1672.4  |        0.1445 |               46.39 |              55 |              12 |                 3000 |                 4947.4  |                   428.2 |             83.1 |
|          100 | milp             |     106 |        22656.8 |             3232.16 |        0.1427 |               44.89 |             113 |              19 |                 4750 |                 8547.16 |                   886.1 |             86.5 |
|          100 | reactiva_bloques |     106 |        22656.8 |             3285.96 |        0.145  |               43.81 |             106 |              33 |                 8250 |                12066    |                   873.3 |             92.7 |
|          100 | reactiva_minuto  |     106 |        22656.8 |             3238.53 |        0.1429 |               47.4  |             106 |              23 |                 5750 |                 9518.53 |                   761.9 |             80.6 |
|          200 | milp             |     210 |        45195.4 |             6448.93 |        0.1427 |               44.79 |             235 |              40 |                10000 |                17623.9  |                  1726   |             81.2 |
|          200 | reactiva_bloques |     210 |        45195.4 |             6551.31 |        0.145  |               44.13 |             212 |              61 |                15250 |                22861.3  |                  1734.2 |             91.7 |
|          200 | reactiva_minuto  |     210 |        45195.4 |             6472.16 |        0.1432 |               47.49 |             212 |              48 |                12000 |                19532.2  |                  1517.6 |             79.8 |
|          400 | milp             |     404 |        88533.3 |            12847.8  |        0.1451 |               43.4  |             446 |              96 |                24000 |                39077.8  |                  3271.4 |             88.5 |
|          400 | reactiva_bloques |     404 |        88533.3 |            12868.4  |        0.1454 |               43.27 |             406 |             130 |                32500 |                47398.4  |                  3377.9 |             94.8 |
|          400 | reactiva_minuto  |     404 |        88533.3 |            12792.6  |        0.1445 |               46.46 |             406 |             107 |                26750 |                41572.6  |                  2961.7 |             80.6 |

### Valor de la carga inteligente (MILP frente a las dos reactivas)

El MILP trabaja en bloques de 15 min, que restringen sus opciones: su costo es una **cota superior** del optimo al minuto, asi que la ganancia frente al simulador real es **al menos** la indicada.

|   N_objetivo |   costo_reactiva_minuto_usd |   costo_reactiva_bloques_usd |   costo_milp_usd |   ganancia_vs_simulador_pct |   ganancia_vs_reactiva_bloques_pct |   reservas_simulador |   reservas_reactiva_bloques |   reservas_milp |
|-------------:|----------------------------:|-----------------------------:|-----------------:|----------------------------:|-----------------------------------:|---------------------:|----------------------------:|----------------:|
|           30 |                     2115.26 |                      2653.96 |          1611.29 |                        23.8 |                               39.3 |                    4 |                           6 |               2 |
|           50 |                     4947.4  |                      6209.74 |          4198.28 |                        15.1 |                               32.4 |                   12 |                          17 |               9 |
|          100 |                     9518.53 |                     12066    |          8547.16 |                        10.2 |                               29.2 |                   23 |                          33 |              19 |
|          200 |                    19532.2  |                     22861.3  |         17623.9  |                         9.8 |                               22.9 |                   48 |                          61 |              40 |
|          400 |                    41572.6  |                     47398.4  |         39077.8  |                         6   |                               17.6 |                  107 |                         130 |              96 |

### Variacion del MILP respecto de la reactiva en bloques

|   N_objetivo |   d_costo_total_usd |   d_costo_total_pct |   d_energia_usd |   d_usd_por_kwh |   d_pct_valle |   d_eventos |   d_reservas |   d_costo_reservas_usd |
|-------------:|--------------------:|--------------------:|----------------:|----------------:|--------------:|------------:|-------------:|-----------------------:|
|           30 |             -1042.7 |              -39.29 |           -42.7 |         -0.0061 |          0.9  |           0 |           -4 |                  -1000 |
|           50 |             -2011.5 |              -32.39 |           -21.5 |         -0.0018 |          1.13 |           2 |           -8 |                  -2000 |
|          100 |             -3518.8 |              -29.16 |           -53.8 |         -0.0023 |          1.08 |           7 |          -14 |                  -3500 |
|          200 |             -5237.4 |              -22.91 |          -102.4 |         -0.0023 |          0.66 |          23 |          -21 |                  -5250 |
|          400 |             -8320.6 |              -17.55 |           -20.5 |         -0.0003 |          0.13 |          40 |          -34 |                  -8500 |

## Tiempo de resolucion

|   N_objetivo |   buses |   segundos | estado           |   brecha_pct |   cota_inferior_usd |   objetivo_usd |
|-------------:|--------:|-----------:|:-----------------|-------------:|--------------------:|---------------:|
|           30 |      34 |      600.1 | limite de tiempo |        3.043 |             1562.27 |        1611.29 |
|           50 |      55 |      600.1 | limite de tiempo |        3.767 |             4040.14 |        4198.28 |
|          100 |     106 |      600.1 | limite de tiempo |        4.833 |             8134.06 |        8547.16 |
|          200 |     210 |      600.3 | limite de tiempo |        5.328 |            16657.9  |       17595.4  |
|          400 |     404 |      600.4 | limite de tiempo |       14.591 |            33351.6  |       39049.3  |


- Instancias que **no** alcanzaron la brecha pedida (1%) en 600 s: [30, 50, 100, 200, 400]. La brecha es la distancia entre la mejor solucion y la cota de Gurobi: la solucion es factible y verificada, pero su optimalidad solo esta certificada hasta esa brecha (la ganancia real es al menos la medida).

## Representatividad de la instancia

| metrica                                  |   red_completa |     N=30 |     N=50 |    N=100 |    N=200 |    N=400 |
|:-----------------------------------------|---------------:|---------:|---------:|---------:|---------:|---------:|
| buses (cargas finales)                   |      4622      |  34      |  55      | 106      | 210      | 404      |
| puestos                                  |       270      |   2      |   3      |   6      |  12      |  23      |
| puestos por bus                          |         0.0584 |   0.0588 |   0.0545 |   0.0566 |   0.0571 |   0.0569 |
| % llegadas entre 19:00 y 02:00           |        90      |  91.2    |  94.5    |  92.5    |  92.4    |  92.3    |
| % salidas entre 04:00 y 08:00            |        62.6    |  47.1    |  52.7    |  57.5    |  59      |  61.6    |
| ventana mediana en el patio (h)          |         8.98   |  10.37   |   9.15   |   9.13   |   9.1    |   8.92   |
| energia media a reponer (kWh)            |       217.3    | 203.2    | 210.5    | 213.7    | 214.7    | 218.9    |
| carga / capacidad de 24 h (%)            |        86.2    |  80      |  89.3    |  87.4    |  87.2    |  89.1    |
| % buses con ciclo no cumplido (reactiva) |        26.1    |  11.8    |  21.8    |  21.7    |  22.9    |  26.5    |
| USD/kWh (reactiva)                       |         0.142  |   0.1368 |   0.1445 |   0.1429 |   0.1432 |   0.1445 |
| % energia en valle (reactiva)            |        48      |  51.74   |  46.39   |  47.4    |  47.49   |  46.46   |

## Chequeos que se hicieron en cada corrida (el script falla si alguno no se cumple)

- Las jornadas reconstruidas sin cargas calzan con el VSP (kWh por jornada).
- Cobertura y balance de energia del simulador sobre la instancia (los de `10-carga_reactiva.py`).
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