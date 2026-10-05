# Reporte Etapa 2 - Asignacion de buses (VSP, sin bateria)

Escalera de escenarios (cada escalon cambia una sola decision) y sensibilidad del deadhead. La asignacion de electroterminales es C1b (el mas cercano a los paraderos terminales reales de cada ruta) y Los Espinos y Santa Rosa se tratan como UN solo electroterminal en todos los escenarios operacionales. El costo de operacion es flota + km sin pasajeros + espera; no incluye la energia (Etapa 3) ni los km con pasajeros (iguales en todos los escenarios).

## Escalera de escenarios

| etiqueta   |   buses |   km_vacios_total |   pct_km_vacios |   espera_h |   cost_operacion_usd |   brecha_buses_vs_LB_pct |   brecha_costo_vs_LB_pct |   jornadas_sin_retorno |
|:-----------|--------:|------------------:|----------------:|-----------:|---------------------:|-------------------------:|-------------------------:|-----------------------:|
| E0         |    8654 |            206618 |           13.31 |    25099.3 |          2.31199e+06 |                    22.66 |                    23.39 |                      0 |
| E1         |    7366 |            182834 |           11.96 |    20749.1 |          1.97026e+06 |                     4.41 |                     5.15 |                      0 |
| LB         |    7055 |            146540 |            9.82 |    20365   |          1.87368e+06 |                     0    |                     0    |                   4192 |

## Efecto marginal de cada decision

| escalon   |   buses |   buses_pct |   costo_operacion_usd |   costo_pct |
|:----------|--------:|------------:|----------------------:|------------:|
| E0 -> E1  |   -1288 |      -14.88 |               -341723 |      -14.78 |
| E1 -> LB  |    -311 |       -4.22 |                -96588 |       -4.9  |

- **E0 -> E1 (interlining):** concentra la mayor parte de la ganancia posible: -1.288 buses (-14.8% del costo de operacion), 81% de lo que separa a E0 de LB. Los km de interlining suben (10.088 -> 14.851 km: los buses se desplazan para encadenar viajes), pero los km de pullout/pullin bajan mas (196.530 -> 167.984 km, porque hay menos buses que salgan y vuelvan): el total de km sin pasajeros baja (206.618 -> 182.834 km). En E1, 1.068 jornadas salen de un patio y vuelven al otro del terminal unido (estan a 1,1 km; no viola el retorno porque es un solo electroterminal).
- **E1 -> LB:** quedan 311 buses sobre la cota inferior (4.4%): es el precio de exigir el retorno al electroterminal y de limitar el interlining al grupo. LB NO es operacional: 4.192 de sus 7.055 jornadas terminan en un electroterminal distinto al de salida.
- Todos quedan sobre la cota teorica de 6.539 (maximo de expediciones simultaneas).

## Evidencia de por que se unen Los Espinos y Santa Rosa (separados vs unidos)

| etiqueta   |   buses |   cost_operacion_usd |   jornadas_cruzan_patio |
|:-----------|--------:|---------------------:|------------------------:|
| E0_sep     |    8654 |          2.31199e+06 |                       0 |
| E0         |    8654 |          2.31199e+06 |                       0 |
| E1_sep     |    7460 |          1.99534e+06 |                       0 |
| E1         |    7366 |          1.97026e+06 |                    1068 |

En el VSP unir no cambia E0 (cada ruta encadena solo consigo misma) y baja 94 buses en E1: las 186 rutas de ambos terminales pasan a poder encadenarse entre si. El efecto decisivo esta en la carga (Etapa 3): sin unir, Los Espinos tiene deficit de energia por falta de puestos y la solucion es infactible.

## Variantes con C2 (asignacion con restriccion de capacidad; propuesta, fuera de la escalera)

| etiqueta   |   buses |   cost_operacion_usd |   jornadas_cruzan_patio |   delta_buses_vs_escalera |   delta_costo_vs_escalera_usd |
|:-----------|--------:|---------------------:|------------------------:|--------------------------:|------------------------------:|
| E1_C2      |    7366 |          1.97032e+06 |                    1041 |                         0 |                            54 |
| E1_C2_sep  |    7462 |          1.99592e+06 |                       0 |                         2 |                           578 |

C2 mueve 5 rutas respecto de C1b para respetar la capacidad de carga de Los Espinos. En el VSP casi no cambia nada (0 buses en E1_C2 frente a E1; 2 en E1_C2_sep frente a E1_sep): el VSP no ve la capacidad. Su efecto aparece en la carga (Etapa 3). Se mantiene como propuesta y no como base (ver `docs/justificaciones/05_unir_terminales.md`).

## Sensibilidad del deadhead (sobre E1)

| parametro                 |   valor |   buses |   delta_buses_vs_base |   delta_buses_vs_base_pct |   cost_operacion_usd |   delta_costo_vs_base_pct |   km_vacios_total |   pct_km_vacios |   tiempo_computo_s |
|:--------------------------|--------:|--------:|----------------------:|--------------------------:|---------------------:|--------------------------:|------------------:|----------------:|-------------------:|
| factor de desvio          |    1.2  |    7294 |                   -72 |                     -0.98 |          1.94436e+06 |                     -1.32 |            167926 |           11.1  |               54.7 |
| factor de desvio          |    1.3  |    7366 |                     0 |                      0    |          1.97026e+06 |                      0    |            182834 |           11.96 |               23.7 |
| factor de desvio          |    1.35 |    7401 |                    35 |                      0.48 |          1.98272e+06 |                      0.63 |            190362 |           12.4  |               19.7 |
| factor de desvio          |    1.5  |    7441 |                    75 |                      1.02 |          2.00413e+06 |                      1.72 |            212121 |           13.62 |               16.2 |
| layover (min)             |    0    |    7161 |                  -205 |                     -2.78 |          1.91707e+06 |                     -2.7  |            178706 |           11.73 |               17.2 |
| layover (min)             |    3    |    7366 |                     0 |                      0    |          1.97026e+06 |                      0    |            182834 |           11.96 |               23.7 |
| layover (min)             |   10    |    7810 |                   444 |                      6.03 |          2.08694e+06 |                      5.92 |            191992 |           12.49 |               16.1 |
| radio de interlining (km) |    1    |    8198 |                   832 |                     11.3  |          2.18778e+06 |                     11.04 |            198414 |           12.85 |               20.2 |
| radio de interlining (km) |    2    |    7577 |                   211 |                      2.86 |          2.02555e+06 |                      2.81 |            186212 |           12.16 |               38.8 |
| radio de interlining (km) |    3    |    7366 |                     0 |                      0    |          1.97026e+06 |                      0    |            182834 |           11.96 |               23.7 |
| radio de interlining (km) |    4    |    7201 |                  -165 |                     -2.24 |          1.92744e+06 |                     -2.17 |            180457 |           11.83 |               79.3 |
| radio de interlining (km) |    5    |    7118 |                  -248 |                     -3.37 |          1.906e+06   |                     -3.26 |            179198 |           11.75 |              119.5 |

- **Factor de desvio** (1,2 a 1,5): la flota varia -1.0% a +1.0% y el costo -1.3% a +1.7%. El 1,3 importa poco para el tamano de la flota. Ojo: el radio de interlining (3 km) se compara contra la distancia ya multiplicada por el factor, asi que cambiarlo tambien cambia que encadenamientos se permiten. 1,35 es el valor medido a la escala de pullout/pullin (Bloque B).
- **Layover** (0 a 10 min): la flota varia -2.8% a +6.0%: uno de los dos supuestos mas sensibles de la Etapa 2 (con el radio de interlining). Esta sin calibrar (3 min, decision nuestra); es la mejor candidata a declarar como limitacion y a calibrar despues.
- **Radio de interlining** (1 a 5 km): la flota va de 8.198 (+11.3%) con 1 km a 7.118 (-3.4%) con 5 km, frente a 7.366 con el 3 km del modelo; el costo de operacion +11.0% a -3.3%, y el tiempo de computo pasa de 20 s a 120 s. Los retornos son decrecientes (cada km extra ahorra menos buses que el anterior). **No es un supuesto inocuo:** el 3 km es una decision de tamano del modelo (acota los arcos y el tiempo), no una medicion; ampliarlo mejora el VSP y queda como mejora para la entrega final (habria que rehacer la carga con jornadas mas largas).

## Energia por jornada (descriptivo)

Porcentaje de jornadas cuya energia supera la bateria util segun el nivel de partida (las que necesitan recargar durante el dia). La eleccion del nivel base se hace con el barrido de la Etapa 3 (costo total), no con esta tabla.

| etiqueta   |   nivel 100% |   nivel 90% |   nivel 80% |   nivel 70% |
|:-----------|-------------:|------------:|------------:|------------:|
| E0         |         30   |        45.4 |        59   |        68.3 |
| E1         |         39.7 |        59.6 |        77.2 |        86.4 |

## Archivos

Tablas (`tablas/`):
- `resumen_escenarios.csv`: una fila por escenario con todos los parametros de la corrida (trazabilidad).
- `resumen_sensibilidad.csv`: corridas de sensibilidad (sin jornadas).
- `escalera_escenarios.csv`: la tabla de la escalera con efectos marginales y brechas contra LB y la cota.
- `precio_del_clustering.csv`: buses y costo de E1 frente a LB.
- `evidencia_union.csv`: separados vs unidos en el VSP (E0_sep, E0, E1_sep, E1).
- `variantes_c2.csv`: las variantes con C2 (propuesta) frente a la escalera.
- `sensibilidad_deadhead.csv`: la tabla de sensibilidad.

Graficos (`graficos/`):
- `escalera_buses.png`: buses por escenario, con el efecto de cada escalon y la cota teorica.
- `escalera_costo.png`: costo de operacion apilado (flota / km vacios / espera) y de donde viene el ahorro.
- `sensibilidad_deadhead.png`: flota vs factor de desvio, vs layover y vs radio de interlining.
- `energia_por_jornada_E0_E1.png`: energia por jornada contra la bateria util de cada nivel.
- `jornadas_<escenario>.png`: histogramas de energia y duracion de cada escenario.

Jornadas (insumo de la Etapa 3): `data-processed/jornadas_{E0,E1,LB,E0_sep,E1_sep,E1_C2,E1_C2_sep}.csv`.