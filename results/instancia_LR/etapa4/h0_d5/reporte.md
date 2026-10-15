# Etapa 4 - Programacion de la carga, La Reina (holgura 0 min, Delta 5 min, 100 puestos)

- Ventanas: 1,640; energia a reponer 343.3 MWh = 79.5% de la capacidad de 24 h.

## E2-FIFO vs E2

|                             |    E2-FIFO |         E2 |
|:----------------------------|-----------:|-----------:|
| reservas_intermedias        |    30      |     0      |
| reservas_nocturnas          |   442      |   218      |
| costo_energia_usd           | 47004.7    | 46399.7    |
| costo_medio_energia_usd_kwh |     0.1369 |     0.1352 |
| pct_energia_valle           |    52.06   |    52.43   |
| eventos                     |  1640      | 14586      |
| kwh_deficit                 |     0      |     0      |
| uso_maximo_pct              |   100      |   110.2    |
| minutos_saturados           |   907      |   916      |
| minutos_sobre_puestos       |     0      |   121      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha |   segundos |   variables |   binarias |   restricciones |   desempate_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|-----------:|------------:|-----------:|----------------:|----------------:|
|             0 |           5 | E2-FIFO                 | heuristica (sin optimizacion) |         165005 |        nan | nan        |       0.73 |         nan |        nan |             nan |        nan      |
|             0 |           5 | E2 agregado - LP (cota) | optimo                        |         100351 |     100351 |   0        |       9.06 |      478841 |          0 |            3568 |        nan      |
|             0 |           5 | E2 agregado - MILP      | optimo (brecha pedida)        |         100900 |     100805 |   0.001118 |     157.79 |      478841 |       1640 |            3568 |         17.7654 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|
| P1        | 00-08   |              0.1 |   142986   |          14298.6 | 144000   |        14400   |
| P2        | 08-14   |              0.2 |    99142   |          14871.3 |  97708   |        14656.2 |
| P3        | 14-17   |              0.2 |     8980.4 |           1975.7 |    848.3 |          186.6 |
| P4        | 17-19   |              0.2 |     6975.3 |           1046.3 |  14910.3 |         2236.6 |
| P5        | 19-22   |              0.2 |    49459.7 |          10881.1 |  49819.5 |        10960.3 |
| P6        | 22-24   |              0.1 |    35743   |           3931.7 |  36000   |         3960   |

## Validaciones (todas pasaron)
- FIFO: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- E2: energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; E2 <= E2-FIFO en la grilla.
- Realizacion por minuto de E2: 121 minutos sobre los puestos (maximo 110.25); es el error del agregado en los bloques de borde.

## Tiempo y memoria
- FIFO 0.7 s | armado 1.7 s | LP 9.1 s | MILP 157.8 s (53 nodos) | realizacion por minuto 3.0 s | total 178.4 s | pico de memoria 1,388 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (FIFO exacta; E2 = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).