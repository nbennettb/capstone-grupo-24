# Etapa 4 - Programacion de la carga, Los Espinos + Santa Rosa (holgura de recarga 0 min, largo del bloque 15 min, 270 puestos)

- Ventanas: 4,623; energia a reponer 989.4 MWh = 84.8% de la capacidad de 24 h.

## Propuesta con carga por orden de llegada vs Propuesta completa (modelo relajado)

|                             |     Propuesta con carga por orden de llegada |          Propuesta completa (modelo relajado) |
|:----------------------------|------------:|------------:|
| reservas_diurnas        |      0      |      0      |
| reservas_nocturnas          |   1533      |    867      |
| costo_energia_usd           | 138819      | 133093      |
| costo_medio_energia_usd_kwh |      0.1403 |      0.1345 |
| pct_energia_valle           |     48.83   |     49.12   |
| eventos                     |   4623      |  16914      |
| kwh_deficit                 |      0      |      0      |
| uso_maximo_pct              |    100      |    124.1    |
| minutos_saturados           |   1000      |   1064      |
| minutos_sobre_puestos       |      0      |    106      |

## Modelos (estado, brecha y tiempos)

|   holgura_min |   delta_min | modelo                  | estado                        |   objetivo_usd |   cota_usd |     brecha | fuente_brecha   |   segundos |   variables |   binarias |   restricciones |   desempate_usd |
|--------------:|------------:|:------------------------|:------------------------------|---------------:|-----------:|-----------:|:----------------|-----------:|------------:|-----------:|----------------:|----------------:|
|             0 |          15 | Propuesta con carga por orden de llegada                 | heuristica (sin optimizacion) |         522069 |        nan | nan        | -               |       0.48 |         nan |        nan |             nan |        nan      |
|             0 |          15 | Propuesta completa (modelo relajado) agregado - LP (cota) | optimo                        |         347574 |     347574 |   0        | Gurobi          |      11.87 |      462149 |          0 |            9342 |        nan      |
|             0 |          15 | Propuesta completa (modelo relajado) agregado - MILP      | optimo (brecha pedida)        |         349843 |     348870 |   0.002841 | Gurobi          |      46.8  |      462149 |       4623 |            9342 |         20.3047 |

## Energia por periodo tarifario

| periodo   | horas   |   precio_usd_kwh |   kwh_fifo |   costo_fifo_usd |   kwh_e2 |   costo_e2_usd |
|:----------|:--------|-----------------:|-----------:|-----------------:|---------:|---------------:|
| P1        | 00-08   |              0.1 |   386416   |          38641.6 | 388800   |        38880   |
| P2        | 08-14   |              0.2 |   288330   |          43249.6 | 291600   |        43740   |
| P3        | 14-17   |              0.2 |    84574   |          18606.3 |   3998.4 |          879.7 |
| P4        | 17-19   |              0.2 |    23572.1 |           3535.8 |  97200   |        14580   |
| P5        | 19-22   |              0.2 |   109775   |          24150.6 | 110553   |        24321.6 |
| P6        | 22-24   |              0.1 |    96683.3 |          10635.2 |  97200   |        10692   |

## Validaciones (todas pasaron)
- orden de llegada: ocupacion <= puestos en cada minuto; energia cargada + deficit = consumida; su costo en la grilla = su costo al minuto.
- Propuesta completa (modelo relajado): energia cargada + deficit = consumida; ocupacion <= puestos en cada bloque; toda carga despues de la hora limite lleva reserva; Propuesta completa (modelo relajado) <= Propuesta con carga por orden de llegada en la grilla.
- Realizacion por minuto de Propuesta completa (modelo relajado): 106 minutos sobre los puestos (maximo 335.06); es el error del agregado en los bloques de borde.

## Tiempo y memoria
- orden de llegada 0.5 s | armado 1.1 s | LP 11.9 s | MILP 46.8 s (1 nodos) | realizacion por minuto 1.7 s | total 65.3 s | pico de memoria 1,481 MB.

## Archivos
- `tablas/programa_FIFO.csv`, `tablas/programa_E2.csv`: por ventana, kWh, inicio y fin de la carga, eventos, reserva, deficit y costo.
- `tablas/ocupacion_minutos.csv` (orden de llegada exacta; Propuesta completa (modelo relajado) = realizacion por minuto), `tablas/ocupacion_bloques.csv`.
- `tablas/energia_por_tarifa.csv`, `tablas/reservas.csv`, `tablas/modelo.csv`, `tablas/resumen.csv`.
- `graficos/ocupacion_24h.png` (+ .csv), `graficos/energia_por_tarifa.png` (+ .csv).