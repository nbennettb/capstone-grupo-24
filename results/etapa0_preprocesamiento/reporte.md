# Reporte de preprocesamiento (Etapa 0)

Corrida: RED COMPLETA

## Conteos
- Rutas: 417
- Viajes (patrones GTFS): 6620
- Expediciones (viajes expandidos por frecuencia): 64502
- Paraderos terminales unicos (origen/destino de alguna expedicion): 641
- Energia total del dia: 1883.6 MWh

## Estadisticas descriptivas (ver tambien distribucion_expediciones.csv)

|       |   dur_min |   distance_km |      kwh |
|:------|----------:|--------------:|---------:|
| count |  64502    |      64502    | 64502    |
| mean  |     78.57 |         20.86 |    29.2  |
| std   |     36.09 |          8.56 |    11.99 |
| min   |      8.23 |          2.35 |     3.29 |
| 25%   |     51.1  |         14.48 |    20.27 |
| 50%   |     72.02 |         19.67 |    27.54 |
| 75%   |     99.8  |         26.44 |    37.02 |
| max   |    198.17 |         57.64 |    80.7  |

## Concurrencia
- Maximo de expediciones simultaneas: 6539 a las 8.00 h
- (referencia red completa, prototipo 28/09: 6539 a las 8.0 h)
- Suma de la concurrencia maxima POR RUTA (rutas_resumen.csv): 7388 -- es una cota inferior de la flota real (ignora layover y el viaje de vuelta al deposito); se usa solo para ponderar rutas en la Etapa 1.

## Por que se clusteriza por ruta y no por expedicion (ver rutas_ida_vuelta.csv)
- Rutas con ida y vuelta identificables: 300 de 417.
- De esas, 284 (94.7%) terminan la ida a menos de 500 m de donde empieza la vuelta.
- 15 rutas tienen mas de un paradero distinto usado como fin-de-ida o inicio-de-vuelta (el 'paradero representativo' es el mas frecuente, no el unico).

## Descartes y chequeos (detalle completo en descartes.csv)

| etapa        | motivo                                                          |   cantidad |
|:-------------|:----------------------------------------------------------------|-----------:|
| viajes       | direccion (texto trip_id) distinta de direction_id              |          0 |
| viajes       | sin distance_km (shape_id sin match en shape_distances_bus.csv) |          0 |
| expediciones | trip_id de frequencies sin viaje calculado (dropeado antes)     |          0 |
| expediciones | sin coordenadas de origen/destino                               |          0 |

## Supuestos aplicados
- Consumo energetico: 1.4 kWh/km (constante, sin congestion ni topografia).
- Dia tipo: L (laboral, lunes-viernes) — unico dia modelado en esta ronda.
- Duracion y distancia de una expedicion son las de su patron GTFS: iguales para todas las salidas del mismo patron a lo largo del dia (no hay variacion por hora peak).

## Tablas generadas
- `conteos.csv`, `descartes.csv`, `distribucion_expediciones.csv`, `concurrencia_por_minuto.csv`.
- `../../data-processed/rutas_resumen.csv`, `rutas_ida_vuelta.csv`, `terminales_por_ruta.csv`.

## Graficos
- `graficos/buses_por_hora.png`: expediciones simultaneas por hora.
- `graficos/energia_por_expedicion.png`: distribucion de energia por expedicion.
- `graficos/duracion_y_distancia.png`: duracion y distancia por expedicion.
- `graficos/ida_vuelta_distancia.png`: distancia fin de ida -> inicio de vuelta, por ruta.
