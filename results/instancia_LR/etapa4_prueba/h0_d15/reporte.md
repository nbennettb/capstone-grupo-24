# Etapa 4 - Programacion de la carga, La Reina (holgura de recarga 0 min, largo del bloque 15 min, 60 puestos)

**PRUEBA: no es la instancia real.**

- Ventanas: 1,025; energia a reponer 219.0 MWh = 84.5% de la capacidad de 24 h.

## Propuesta con carga por orden de llegada vs Propuesta completa (modelo agregado)

|                             |    Propuesta con carga por orden de llegada |         Propuesta completa (modelo agregado) |
|:----------------------------|-----------:|-----------:|
| reservas_diurnas        |     0      |     0      |
| reservas_nocturnas          |   309      |   158      |
| costo_energia_usd           | 30699.5    | 30064.3    |
| costo_medio_energia_usd_kwh |     0.1402 |     0.1373 |
| pct_energia_valle           |    48.96   |    49.31   |
| eventos                     |  1025      |  3787      |
| kwh_deficit                 |     0      |     0      |
| uso_maximo_pct              |   100      |   124.4    |
| minutos_saturados           |   967      |  1021      |
| minutos_sobre_puestos       |     0      |   117      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha | fuente_brecha   |   segundos |   variables |   binarias |   restricciones |   desempate_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|:----------------|-----------:|------------:|-----------:|----------------:|----------------:|
|             0 |          15 | Propuesta con carga por orden de llegada                 | heuristica (sin optimizacion) |       107949   |      nan   | nan        | -               |       0.74 |         nan |        nan |             nan |        nan      |
|             0 |          15 | Propuesta completa (modelo agregado) agregado - LP (cota) | optimo                        |        68859.1 |    68859.1 |   0        | Gurobi          |       3.35 |      102468 |          0 |            2146 |        nan      |
|             0 |          15 | Propuesta completa (modelo agregado) agregado - MILP      | optimo (brecha pedida)        |        69564.3 |    69384.4 |   0.002646 | Gurobi          |      30.45 |      102468 |       1025 |            2146 |          4.1247 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|
| P1        | 00-08   |              0.1 |    85764.4 |           8576.4 |  86400   |         8640   |
| P2        | 08-14   |              0.2 |    63673.4 |           9551   |  64800   |         9720   |
| P3        | 14-17   |              0.2 |    12229.7 |           2690.5 |   3390.8 |          746   |
| P4        | 17-19   |              0.2 |     5407.1 |            811.1 |  12054.7 |         1808.2 |
| P5        | 19-22   |              0.2 |    30496.1 |           6709.1 |  30791.5 |         6774.1 |
| P6        | 22-24   |              0.1 |    21466.3 |           2361.3 |  21600   |         2376   |

## Validaciones (todas pasaron)
- orden de llegada: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- Propuesta completa (modelo agregado): energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; Propuesta completa (modelo agregado) <= Propuesta con carga por orden de llegada en la grilla.
- Realizacion por minuto de Propuesta completa (modelo agregado): 117 minutos sobre los puestos (maximo 74.66); es el error del agregado en los bloques de borde.

## Tiempo y memoria
- orden de llegada 0.7 s | armado 0.8 s | LP 3.4 s | MILP 30.4 s (1 nodos) | realizacion por minuto 2.9 s | total 41.9 s | pico de memoria 716 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (orden de llegada exacta; Propuesta completa (modelo agregado) = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).