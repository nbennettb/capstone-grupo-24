# Calibracion del factor de desvio del deadhead

El modelo calcula todo deadhead como linea recta x 1.3. Aqui se mide, con los trazados GTFS de los buses, cuanto mas largo que la recta es el camino real, a la escala de un deadhead. Factor = recorrido s / linea recta entre los dos puntos.

## Factor de rodeo por escala (todas las ventanas de todos los trazados)

|   escala_km | version             |   n_trazados |     n |   media |   p10 |   p25 |   p50 |   p75 |   p90 |   pct_hasta_1_3 |
|------------:|:--------------------|-------------:|------:|--------:|------:|------:|------:|------:|------:|----------------:|
|           1 | todas las ventanas  |          839 | 33175 |   1.211 | 1     | 1.003 | 1.041 | 1.274 | 1.472 |          77.17  |
|           1 | mediana por trazado |          839 |   839 |   1.097 | 1.005 | 1.015 | 1.057 | 1.163 | 1.246 |          94.875 |
|           3 | todas las ventanas  |          838 | 29820 |   1.439 | 1.006 | 1.039 | 1.215 | 1.449 | 1.829 |          59.702 |
|           3 | mediana por trazado |          838 |   838 |   1.262 | 1.031 | 1.094 | 1.238 | 1.379 | 1.481 |          61.575 |
|           5 | todas las ventanas  |          832 | 26471 |   1.671 | 1.019 | 1.086 | 1.287 | 1.546 | 2.025 |          51.698 |
|           5 | mediana por trazado |          832 |   832 |   1.476 | 1.048 | 1.146 | 1.309 | 1.488 | 1.749 |          49.038 |
|          10 | todas las ventanas  |          743 | 18417 |   2.291 | 1.059 | 1.165 | 1.345 | 1.677 | 2.512 |          44.785 |
|          10 | mediana por trazado |          743 |   743 |   1.786 | 1.118 | 1.207 | 1.408 | 1.781 | 2.439 |          38.358 |
|          15 | todas las ventanas  |          592 | 11590 |   3.709 | 1.102 | 1.199 | 1.378 | 1.745 | 3.701 |          40.751 |
|          15 | mediana por trazado |          592 |   592 |   3.483 | 1.154 | 1.241 | 1.446 | 2.012 | 4.434 |          32.601 |

## Escala de cada tipo de deadhead en el modelo

| base                          | unidad                                    |   p10 |   p25 |   p50 |   p75 |   p90 |   media |
|:------------------------------|:------------------------------------------|------:|------:|------:|------:|------:|--------:|
| rutas (sin ponderar)          | km de recorrido modelado (recta x factor) |  5.38 |  7.16 |  9.74 | 13.44 | 15.42 |   10.15 |
| ponderado por buses estimados | km de recorrido modelado (recta x factor) |  6.29 |  8.35 | 11.51 | 14.54 | 15.87 |   11.27 |

- **Interlining** (radio <= 3 km): el rodeo medido a 1-3 km tiene mediana 1.04-1.22; el 1.3 del modelo queda por encima: es conservador.
- **Pullout/pullin** (mediana ~12 km, ponderado por buses): el rodeo medido a 5-15 km tiene mediana 1.29-1.38, algo sobre 1.3. Pero una ruta comercial rodea mas que un traslado en vacio, asi que este valor es una COTA SUPERIOR del rodeo de un deadhead. Lectura honesta: el factor del modelo queda entre un trayecto directo (>= 1) y el rodeo de una ruta con pasajeros; a esa escala no es claramente conservador y podria subestimar algo el costo de pullout/pullin.
- El efecto sobre flota y costo se mide en la sensibilidad del Bloque C (factor 1,2 / 1,3 / 1,5 y el valor medido).

## Chequeos
- 839 trazados procesados; 127 circulares (extremos a < 0.5 km), excluidos solo del cociente 'trazado completo'.
- Largo calculado vs `shape_distances_bus.csv`: error relativo maximo 0.29%.
- Todo factor >= 1.
- Trazado completo (no circulares): mediana 1.55, p90 2.27 (incluye lazos y vueltas largas; no es la escala de un deadhead).

## Salvedades
- Una ruta comercial rodea mas que un deadhead: el factor medido es cota superior.
- Los buses van por avenidas principales: podria subestimar el rodeo por calles menores.
- Los trazados cubren la red de buses, no todo par de puntos de la ciudad.
- Validar contra la red vial de `chile.gpkg` queda como mejora para el informe final.

## Archivos
- `tablas/factor_por_escala.csv`: la tabla de arriba (mediana por trazado: cada trazado pesa igual).
- `tablas/factor_por_trazado.csv`: una fila por trazado (largo, recta entre extremos, factor, mediana por escala, consistencia con `shape_distances_bus.csv`).
- `tablas/escala_deadhead_pullout_pullin.csv`: largo del pullout/pullin de cada ruta en C2.
- `graficos/factor_por_escala.png`: distribucion del factor por escala, con el 1,3 marcado.
- `graficos/ejemplo_trazado.png`: trazado B31NI, un caso real para explicar la idea.