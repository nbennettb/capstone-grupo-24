# Reporte Etapa 2 - Asignacion de buses (VSP, sin bateria)

Escalera de escenarios (cada escalon cambia una sola decision) y sensibilidad del deadhead. El costo de operacion es flota + km sin pasajeros + espera; no incluye la energia (Etapa 3) ni los km con pasajeros (iguales en todos los escenarios).

## Escalera de escenarios

| etiqueta   |   buses |   km_vacios_total |   pct_km_vacios |   espera_h |   cost_operacion_usd |   brecha_buses_vs_LB_pct |   brecha_costo_vs_LB_pct |   jornadas_sin_retorno |
|:-----------|--------:|------------------:|----------------:|-----------:|---------------------:|-------------------------:|-------------------------:|-----------------------:|
| E0         |    8654 |            206618 |           13.31 |    25099.3 |          2.31199e+06 |                    22.66 |                    23.39 |                      0 |
| E1         |    7460 |            185681 |           12.13 |    20834.9 |          1.99534e+06 |                     5.74 |                     6.49 |                      0 |
| E2         |    7460 |            185681 |           12.13 |    20834.9 |          1.99534e+06 |                     5.74 |                     6.49 |                      0 |
| E2b        |    7366 |            182834 |           11.96 |    20749.1 |          1.97026e+06 |                     4.41 |                     5.15 |                      0 |
| LB         |    7055 |            146540 |            9.82 |    20365   |          1.87368e+06 |                     0    |                     0    |                   4192 |

## Efecto marginal de cada decision

| escalon   |   buses |   buses_pct |   costo_operacion_usd |   costo_pct |
|:----------|--------:|------------:|----------------------:|------------:|
| E0 -> E1  |   -1194 |      -13.8  |               -316645 |      -13.7  |
| E1 -> E2  |       0 |        0    |                     0 |        0    |
| E2 -> E2b |     -94 |       -1.26 |                -25078 |       -1.26 |
| E2b -> LB |    -311 |       -4.22 |                -96588 |       -4.9  |

- **E0 -> E1 (interlining):** concentra la mayor parte de la ganancia posible: -1.194 buses (-13.7% del costo de operacion), 75% de lo que separa a E0 de LB. Los km de interlining suben (10.088 -> 14.618 km: los buses se desplazan para encadenar viajes), pero los km de pullout/pullin bajan mas (196.530 -> 171.063 km, porque hay menos buses que salgan y vuelvan): el total de km sin pasajeros baja (206.618 -> 185.681 km).
- **E1 -> E2 (clustering con capacidad): IDENTICO.** La asignacion C2 coincide con C1b porque la restriccion de capacidad agregada diaria no esta activa (Etapa 1). Es un resultado valido: la capacidad agregada no condiciona el clustering; la capacidad se manifestara en las colas de carga (Etapa 3).
- **E2 -> E2b (unir Los Espinos y Santa Rosa):** -94 buses (-1.3% del costo). Unirlos habilita encadenar las 186 rutas de ambos en un solo grupo; 1.068 jornadas salen de un patio y vuelven al otro (estan a 1,1 km; no viola el retorno porque es un solo electroterminal).
- **E2b -> LB:** quedan 311 buses sobre la cota inferior (4.4%): es el precio de exigir el retorno al electroterminal y de limitar el interlining al grupo. LB NO es operacional: 4.192 de sus 7.055 jornadas terminan en un electroterminal distinto al de salida.
- Todos quedan sobre la cota teorica de 6.539 (maximo de expediciones simultaneas).

## Sensibilidad del deadhead (sobre E1)

| parametro        |   valor |   buses |   delta_buses_vs_base |   delta_buses_vs_base_pct |   cost_operacion_usd |   delta_costo_vs_base_pct |   km_vacios_total |   pct_km_vacios |
|:-----------------|--------:|--------:|----------------------:|--------------------------:|---------------------:|--------------------------:|------------------:|----------------:|
| factor de desvio |    1.2  |    7403 |                   -57 |                     -0.76 |          1.97321e+06 |                     -1.11 |            170866 |           11.27 |
| factor de desvio |    1.3  |    7460 |                     0 |                      0    |          1.99534e+06 |                      0    |            185681 |           12.13 |
| factor de desvio |    1.35 |    7477 |                    17 |                      0.23 |          2.00349e+06 |                      0.41 |            192978 |           12.54 |
| factor de desvio |    1.5  |    7515 |                    55 |                      0.74 |          2.02429e+06 |                      1.45 |            215037 |           13.78 |
| layover (min)    |    0    |    7257 |                  -203 |                     -2.72 |          1.94243e+06 |                     -2.65 |            181534 |           11.89 |
| layover (min)    |    3    |    7460 |                     0 |                      0    |          1.99534e+06 |                      0    |            185681 |           12.13 |
| layover (min)    |   10    |    7908 |                   448 |                      6.01 |          2.11303e+06 |                      5.9  |            194855 |           12.65 |

- **Factor de desvio** (1,2 a 1,5): la flota varia -0.8% a +0.7% y el costo -1.1% a +1.4%. El 1,3 importa poco para el tamano de la flota. Ojo: el radio de interlining (3 km) se compara contra la distancia ya multiplicada por el factor, asi que cambiarlo tambien cambia que encadenamientos se permiten. 1,35 es el valor medido a la escala de pullout/pullin (Bloque B).
- **Layover** (0 a 10 min): la flota varia -2.7% a +6.0%: el supuesto mas sensible de la Etapa 2. Esta sin calibrar (3 min, decision nuestra); es la mejor candidata a declarar como limitacion y a calibrar despues.

## Energia por jornada (descriptivo)

Porcentaje de jornadas cuya energia supera la bateria util segun el nivel de partida (las que necesitan recargar durante el dia). La eleccion del nivel base se hace con el barrido de la Etapa 3 (costo total), no con esta tabla.

| etiqueta   |   nivel 100% |   nivel 90% |   nivel 80% |   nivel 70% |
|:-----------|-------------:|------------:|------------:|------------:|
| E0         |         30   |        45.4 |        59   |        68.3 |
| E1         |         39.6 |        58.3 |        75.6 |        84.9 |

## Archivos

Tablas (`tablas/`):
- `resumen_escenarios.csv`: una fila por escenario con todos los parametros de la corrida (trazabilidad).
- `resumen_sensibilidad.csv`: corridas de sensibilidad (sin jornadas).
- `escalera_escenarios.csv`: la tabla de la escalera con efectos marginales y brechas contra LB y la cota.
- `precio_del_clustering.csv`: buses y costo de E1, E2 y E2b frente a LB.
- `sensibilidad_deadhead.csv`: la tabla de sensibilidad.

Graficos (`graficos/`):
- `escalera_buses.png`: buses por escenario, con el efecto de cada escalon y la cota teorica.
- `escalera_costo.png`: costo de operacion apilado (flota / km vacios / espera) y de donde viene el ahorro.
- `sensibilidad_deadhead.png`: flota vs factor de desvio y vs layover.
- `energia_por_jornada_E0_E1.png`: energia por jornada contra la bateria util de cada nivel.
- `jornadas_<escenario>.png`: histogramas de energia y duracion de cada escenario.

Jornadas (insumo de la Etapa 3): `data-processed/jornadas_{E0,E1,E2,E2b,LB}.csv`.