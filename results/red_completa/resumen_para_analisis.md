# Red completa: resumen para el analisis

Suma de los cuatro electroterminales (Vespucio Norte, El Conquistador, Los Espinos + Santa Rosa y La Reina), cada
uno corrido por separado con `scripts/correr_terminal.py`. Generado por `scripts/17-red_completa.py`.

Todas las cifras son de un dia laboral tipico, en USD por dia. El costo total no incluye la espera nocturna en el
patio (estacionar de noche no es un costo de operacion), igual que en el resumen de cada terminal.

## 1. Validaciones

- [OK] Vespucio Norte: plan de carga validado (15-): 6 de 6 criterios OK
- [OK] Vespucio Norte: Propuesta completa sin deficit y con buses cargando <= puestos: maximo 150 de 150 puestos; deficit maximo 0.000 kWh
- [OK] El Conquistador: plan de carga validado (15-): 6 de 6 criterios OK
- [OK] El Conquistador: Propuesta completa sin deficit y con buses cargando <= puestos: maximo 180 de 180 puestos; deficit maximo 0.000 kWh
- [OK] Los Espinos + Santa Rosa: plan de carga validado (15-): 6 de 6 criterios OK
- [OK] Los Espinos + Santa Rosa: Propuesta completa sin deficit y con buses cargando <= puestos: maximo 270 de 270 puestos; deficit maximo 0.000 kWh
- [OK] La Reina: plan de carga validado (15-): 6 de 6 criterios OK
- [OK] La Reina: Propuesta completa sin deficit y con buses cargando <= puestos: maximo 100 de 100 puestos; deficit maximo 0.000 kWh
- [OK] Caso base: suma de los terminales = red completa: jornadas finales 11,259 (red 11,259); reservas 1,988 (red 1,988); kWh cargados 2,247,102 (red 2,247,102); costo total (USD) 3,958,063 (red 3,958,063)
- [OK] Caso base con interlining: suma de los terminales = red completa: jornadas finales 10,295 (red 10,295); reservas 2,207 (red 2,207); kWh cargados 2,221,448 (red 2,221,448); costo total (USD) 3,751,250 (red 3,751,250)

## 2. Cifras principales

- Costo total de la red: 3,857,136 USD/dia en el caso base, 3,644,537 con interlining
  y **2,760,492 con la Propuesta completa**. Contra el caso base con interlining, que es la
  comparacion justa, la propuesta ahorra **884,045 USD/dia
  (24.3%)**.
- Buses: 12,502 con interlining y **8,995** con la propuesta
  (3,507 menos), de los cuales 1,639 son de reserva.
- El plan de carga de la propuesta es aplicable en los cuatro terminales: nunca hay mas buses cargando que puestos,
  y el validador independiente da los 6 criterios OK en todos.
- Distancia al optimo de la red, en energia + reservas: **1.47%** sobre la cota inferior
  (700,656 contra 690,325 USD/dia).

## 3. KPIs de la red completa por escenario

| KPI                                 | Caso base   | Caso base con interlining   | Propuesta con carga por orden de llegada   | Propuesta completa   |
|:------------------------------------|:------------|:----------------------------|:-------------------------------------------|:---------------------|
| Costo total (USD/dia)               | 3,857,136   | 3,644,537                   | 3,087,832                                  | 2,760,492            |
| flota                               | 2,814,750   | 2,573,750                   | 1,839,000                                  | 1,839,000            |
| buses de reserva                    | 497,000     | 551,750                     | 739,750                                    | 409,750              |
| km vacios                           | 129,831     | 120,668                     | 109,794                                    | 109,794              |
| espera                              | 44,343      | 36,504                      | 43,387                                     | 43,387               |
| energia                             | 314,652     | 310,090                     | 304,380                                    | 290,906              |
| eventos de carga                    | 56,560      | 51,775                      | 51,520                                     | 67,655               |
| Buses que operan las jornadas       | 11,259      | 10,295                      | 7,356                                      | 7,356                |
| Buses de reserva                    | 1,988       | 2,207                       | 2,959                                      | 1,639                |
| Buses totales                       | 13,247      | 12,502                      | 10,315                                     | 8,995                |
| Buses extra por bateria             | 4,593       | 5,136                       | 2,949                                      | 1,629                |
| % km vacios                         | 16.2        | 15.2                        | 14.0                                       | 14.0                 |
| Costo medio de la energia (USD/kWh) | 0.1400      | 0.1396                      | 0.1389                                     | 0.1328               |
| % de la energia en horario valle    | 50.4        | 51.4                        | 51.4                                       | 53.5                 |
| Eventos de carga                    | 11,312      | 10,355                      | 10,304                                     | 13,531               |
| Utilizacion del bus (%)             | 26.6        | 28.1                        | 34.1                                       | 39.1                 |

Porcentajes de la red recalculados con las sumas (no son el promedio simple de los terminales).

## 4. Costo total por electroterminal

| Electroterminal          | Caso base   | Caso base + interlining   | Propuesta, carga por llegada   | Propuesta completa   | Ahorro de la Propuesta completa (USD)   |   Ahorro (%) |
|:-------------------------|:------------|:--------------------------|:-------------------------------|:---------------------|:----------------------------------------|-------------:|
| Vespucio Norte           | 327,232     | 307,217                   | 249,432                        | 243,242              | 63,975                                  |         20.8 |
| El Conquistador          | 1,154,195   | 1,073,408                 | 920,766                        | 812,855              | 260,553                                 |         24.3 |
| Los Espinos + Santa Rosa | 1,781,108   | 1,696,105                 | 1,436,670                      | 1,275,091            | 421,013                                 |         24.8 |
| La Reina                 | 594,602     | 567,807                   | 480,965                        | 429,303              | 138,504                                 |         24.4 |
| Red completa             | 3,857,136   | 3,644,537                 | 3,087,832                      | 2,760,492            | 884,045                                 |         24.3 |

El ahorro es contra el caso base con interlining.

## 5. Plan de carga de la Propuesta completa por electroterminal

| Electroterminal          |   Puestos | Maximo de buses cargando a la vez   | Ventanas de carga   | Reservas   |   Eventos por ventana | Energia / capacidad 24 h (%)   | Plan: energia + reservas (USD)   | Cota inferior (USD)   |   Distancia a la cota (%) | Tiempo plan exacto (s)   | Memoria (MB)   |
|:-------------------------|----------:|:------------------------------------|:--------------------|:-----------|----------------------:|:-------------------------------|:---------------------------------|:----------------------|--------------------------:|:-------------------------|:---------------|
| Vespucio Norte           |       150 | 150                                 | 1,038               | 29         |                  1.23 | 34.2                           | 31,524                           | 31,524                |                      0    | 23                       | 767            |
| El Conquistador          |       180 | 180                                 | 3,003               | 505        |                  1.33 | 81.9                           | 212,768                          | 209,361               |                      1.6  | 607                      | 3,625          |
| Los Espinos + Santa Rosa |       270 | 270                                 | 4,623               | 880        |                  1.29 | 84.8                           | 353,690                          | 348,870               |                      1.36 | 1,539                    | 3,629          |
| La Reina                 |       100 | 100                                 | 1,640               | 225        |                  1.39 | 79.5                           | 102,674                          | 100,570               |                      2.05 | 209                      | 2,300          |
| Red completa             |       700 | -                                   | 10,304              | 1,639      |                  1.31 | -                              | 700,656                          | 690,325               |                      1.47 | 2,379                    | 3,629          |

- La cota inferior es el costo del modelo relajado: ningun plan real puede costar menos. Distancia a la cota =
  (plan - cota) / plan.
- La fila de la red suma planes y cotas, y la distancia se calcula con esas sumas.
- Los Espinos + Santa Rosa comparten sus 270 puestos (supuesto declarado, patios a 1,1 km).

## 6. Figuras (`results/red_completa/graficos/`)

- `costo_diario_red.png`: costo total de la red por escenario, con el % contra el caso base con interlining.
- `buses_red.png`: buses que operan las jornadas y buses de reserva, por escenario.
- `costo_por_terminal.png`: costo total de cada electroterminal por escenario.
