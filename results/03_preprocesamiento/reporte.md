# Reporte de preprocesamiento (Etapa 0)

Corrida: RED COMPLETA

## Conteos
- Rutas: 417
- Viajes (patrones GTFS): 6620
- Expediciones (viajes expandidos por frecuencia): 64502
- Paraderos terminales unicos (origen/destino de alguna expedicion): 641
- Expediciones sin distancia (descartadas antes de este punto): ver log de consola

## Estadisticas descriptivas

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

## Supuestos aplicados
- Consumo energetico: 1.4 kWh/km (constante, sin congestion ni topografia).
- Dia tipo: L (laboral, lunes-viernes) — unico dia modelado en esta ronda.

## Graficos
- `buses_por_hora.png`: expediciones simultaneas por hora.
- `energia_por_expedicion.png`: distribucion de energia por expedicion.

*(Generado automaticamente por scripts/3-preprocesamiento_expediciones.py)*