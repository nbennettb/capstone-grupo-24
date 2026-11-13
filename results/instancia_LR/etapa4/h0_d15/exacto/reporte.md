# Etapa 4 - Programa de carga exacto al minuto, La Reina (100 puestos)

Cada bus carga en minutos enteros en un puesto identificado. En ningun minuto cargan mas buses que puestos.

- Energia + reservas: 102,673.54 USD/dia; 225 reservas (0 diurnas, 225 nocturnas).
- Cota inferior (modelo relajado): 100,570.07 USD/dia. Distancia al optimo: a lo mas 2.05%.
- Eventos de carga: 2,274 (1.39 por ventana).
- Maximo de buses cargando a la vez: 100 de 100; puestos usados: 100.
- Carga por orden de llegada (misma Etapa 3): 157,504.72 USD/dia, 442 reservas.
- Tiempo: 208 s; pico de memoria 2,300 MB.

## Modelos

|   holgura_min |   delta_min | modelo                                      | estado                 |   objetivo_usd |     brecha |   segundos |     variables |   reservas |   binarias |
|--------------:|------------:|:--------------------------------------------|:-----------------------|---------------:|-----------:|-----------:|--------------:|-----------:|-----------:|
|             0 |          15 | Modelo relajado, LP (cota inferior)         | optimo                 |         100570 | nan        |      nan   | nan           |        nan |        nan |
|             0 |          15 | Programa exacto, arranque                   | factible               |         126387 | nan        |       12.5 |   1.19844e+06 |        325 |        nan |
|             0 |          15 | Programa exacto, MILP                       | optimo (brecha pedida) |         103018 |   0.002361 |      158.7 |   1.19844e+06 |        225 |        563 |
|             0 |          15 | Programa exacto, final (energia + reservas) | entero y validado      |         102674 |   0.020487 |      207.9 | nan           |        225 |        nan |

## Energia por tramo horario

| periodo   | horas   |   precio_usd_kwh |      kwh |   costo_usd |
|:----------|:--------|-----------------:|---------:|------------:|
| P1        | 00-08   |              0.1 | 142960   |     14296   |
| P2        | 08-14   |              0.2 |  99527.7 |     14929.2 |
| P3        | 14-17   |              0.2 |    882   |       194   |
| P4        | 17-19   |              0.2 |  14925.2 |      2238.8 |
| P5        | 19-22   |              0.2 |  49241.2 |     10833.1 |
| P6        | 22-24   |              0.1 |  35750.2 |      3932.5 |

## Archivos
- `programa_puestos.csv`: una fila por carga (ventana, bus, puesto, inicio, fin, kWh).
- `programa_E2_exacto.csv`: una fila por ventana (kWh, inicio y fin de la carga, eventos, reserva, costo).
- `buses_cargando_24h.png`, `uso_de_cada_puesto.png` (+ .csv), `ocupacion_minutos.csv`, `resumen.csv`, `modelo.csv`, `energia_por_tarifa.csv`, `gurobi.log`.