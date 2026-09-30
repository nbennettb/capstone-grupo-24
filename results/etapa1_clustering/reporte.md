# Reporte Etapa 1 - Clustering de rutas a electroterminales

Compara C1a (heuristica, centroide), C1b (heuristica, paraderos terminales reales), C2 caso base (MILP con capacidad, SOC inicial 100%) y C2 ciclico (MILP con capacidad, se recarga todo lo consumido).

## Comparacion bajo criterio comun (distancia a paraderos terminales reales)

| estrategia              |   distancia_media_km |   distancia_p90_km |   distancia_max_km |   costo_pullout_pullin_usd_dia |   rutas_distintas_de_c1b |
|:------------------------|---------------------:|-------------------:|-------------------:|-------------------------------:|-------------------------:|
| C1a (centroide)         |               10.195 |             15.488 |             21.255 |                          83843 |                       41 |
| C1b (terminales reales) |               10.149 |             15.424 |             20.991 |                          83271 |                        0 |
| C2 caso base (soc100)   |               10.149 |             15.424 |             20.991 |                          83271 |                        0 |
| C2 escenario ciclico    |               10.149 |             15.424 |             20.991 |                          83271 |                        0 |

## Resultado central: bajo el caso base, la capacidad no restringe
- C2 caso base coincide EXACTAMENTE con C1b: la restriccion de capacidad no esta activa bajo SOC inicial 100% (ver `results/etapa1_clustering/tablas/capacidad_dos_supuestos.csv`).
- Bajo el escenario ciclico (H=24h), el uso maximo llega a 89.9% en Los Espinos.
- Con horas de carga restringidas a 10h/dia, el escenario ciclico es INFACTIBLE (ver `tablas/capacidad_dos_supuestos.csv`).

## Barrido de theta (escenario ciclico) -- a partir de cuando C2 se separa de C1b

|   theta | factible   |   rutas_movidas |   costo_asignacion_usd_dia |   uso_max_pct | depot_mas_cargado   |
|--------:|:-----------|----------------:|---------------------------:|--------------:|:--------------------|
|     1   | True       |               0 |                      83271 |          89.9 | Los Espinos         |
|     0.9 | True       |               0 |                      83271 |          99.9 | Los Espinos         |
|     0.8 | True       |              11 |                      83273 |          98.5 | Los Espinos         |
|     0.7 | True       |              21 |                      83333 |         100   | El Conquistador     |
|     0.6 | False      |             nan |                        nan |         nan   | nan                 |

## Rutas por electroterminal, por estrategia

| depot_nombre    |   C1a (centroide) |   C1b (terminales reales) |   C2 caso base (soc100) |   C2 escenario ciclico |
|:----------------|------------------:|--------------------------:|------------------------:|-----------------------:|
| El Conquistador |                98 |                       108 |                     108 |                    108 |
| La Reina        |                64 |                        67 |                      67 |                     67 |
| Los Espinos     |                85 |                        88 |                      88 |                     88 |
| Santa Rosa      |               111 |                        98 |                      98 |                     98 |
| Vespucio Norte  |                59 |                        56 |                      56 |                     56 |

## Rutas que cambian de electroterminal entre C1a y C2 (mapa de diferencias): 41

## Archivos generados
- `data-processed/rutas_clustering_completo.csv`: tabla ancha, una fila por ruta.
- `tablas/`: resumen_por_terminal.csv, comparacion_estrategias.csv, rutas_que_cambian.csv, distancias_ruta_terminal.csv, capacidad_dos_supuestos.csv, barrido_theta.csv.
- `graficos/`: rutas_por_terminal.png, distancias.png, capacidad.png, barrido_theta.png.
- `mapas/`: mapa_c1a.png, mapa_c1b.png, mapa_c2.png, mapa_c2_ciclo.png, mapa_terminal_<nombre>.png (x5), mapa_paraderos_terminales.png, mapa_diferencias.png.

*(Ver docs/context/01_metodologia_y_avance.md para la interpretacion completa y las decisiones que este resultado habilita o deja pendientes.)*