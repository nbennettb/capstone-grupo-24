# Etapa 4 - Programacion de la carga, La Reina (holgura 0 min, Delta 30 min, 100 puestos)

- Ventanas: 1,640; energia a reponer 343.3 MWh = 79.5% de la capacidad de 24 h.

## E2-FIFO vs E2

|                             |    E2-FIFO |         E2 |   E2-detallado |
|:----------------------------|-----------:|-----------:|---------------:|
| reservas_intermedias        |    30      |     0      |        30      |
| reservas_nocturnas          |   442      |   217      |       442      |
| costo_energia_usd           | 47004.7    | 46430.5    |     47004.7    |
| costo_medio_energia_usd_kwh |     0.1369 |     0.1353 |         0.1369 |
| pct_energia_valle           |    52.06   |    52.43   |        52.06   |
| eventos                     |  1640      |  3618      |      1640      |
| kwh_deficit                 |     0      |     0      |         0      |
| uso_maximo_pct              |   100      |   142      |       100      |
| minutos_saturados           |   907      |   929      |       681      |
| minutos_sobre_puestos       |     0      |   101      |         0      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha | fuente_brecha                                         |   segundos |   variables |   binarias |   restricciones |   desempate_usd |   cota_gurobi_usd |   brecha_gurobi |   cota_valida_usd |   eventos_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|:------------------------------------------------------|-----------:|------------:|-----------:|----------------:|----------------:|------------------:|----------------:|------------------:|--------------:|
|             0 |          30 | E2-FIFO                 | heuristica (sin optimizacion) |       165005   |      nan   | nan        | -                                                     |       0.31 |         nan |        nan |             nan |        nan      |               nan |             nan |               nan |           nan |
|             0 |          30 | E2 agregado - LP (cota) | optimo                        |        99854.6 |    99854.6 |   0        | Gurobi                                                |       1.51 |       85242 |          0 |            3328 |        nan      |               nan |             nan |               nan |           nan |
|             0 |          30 | E2 agregado - MILP      | optimo (brecha pedida)        |       100681   |   100304   |   0.003772 | Gurobi                                                |      13.34 |       85242 |       1640 |            3328 |          2.9431 |               nan |             nan |               nan |           nan |
|             0 |          30 | E2 detallado - MILP     | limite de tiempo              |       173205   |   108055   |   0.376156 | cota valida (LP del agregado + un evento por ventana) |    3603.37 |      245962 |      82000 |          242730 |          2.9795 |              -inf |             inf |            108055 |          8200 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |   kwh_e2_detallado |   costo_e2_detallado_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|-------------------:|-------------------------:|
| P1        | 00-08   |              0.1 |   142986   |          14298.6 | 144000   |        14400   |           142986   |                  14298.6 |
| P2        | 08-14   |              0.2 |    99142   |          14871.3 |  97267   |        14590   |            99142   |                  14871.3 |
| P3        | 14-17   |              0.2 |     8980.4 |           1975.7 |    848.3 |          186.6 |             8980.4 |                   1975.7 |
| P4        | 17-19   |              0.2 |     6975.3 |           1046.3 |  14910.3 |         2236.6 |             6975.3 |                   1046.3 |
| P5        | 19-22   |              0.2 |    49459.7 |          10881.1 |  50260.5 |        11057.3 |            49459.7 |                  10881.1 |
| P6        | 22-24   |              0.1 |    35743   |           3931.7 |  36000   |         3960   |            35743   |                   3931.7 |

## Validaciones (todas pasaron)
- FIFO: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- E2: energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; E2 <= E2-FIFO en la grilla.
- Realizacion por minuto de E2: 101 minutos sobre los puestos (maximo 141.99); es el error del agregado en los bloques de borde.

## Modelo detallado vs agregado

- Detallado: limite de tiempo, brecha 37.616% (cota valida (LP del agregado + un evento por ventana)), 3603.4 s, 82,000 binarias. Objetivo 173,204.72 USD = energia + reservas 165,004.72 + eventos 8,200.00.
- Agregado: energia + reservas 100,680.53 USD; con sus eventos contados despues: 118,770.53 USD.
- Realizacion por minuto del detallado: 0 minutos sobre los puestos (maximo 100.00).

## Tiempo y memoria
- FIFO 0.3 s | armado 0.2 s | LP 1.5 s | MILP 13.3 s (1 nodos) | realizacion por minuto 1.7 s | total 3636.3 s | pico de memoria 1,035 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (FIFO exacta; E2 = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).