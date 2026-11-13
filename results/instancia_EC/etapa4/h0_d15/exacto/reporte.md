# Etapa 4 - Programa de carga exacto al minuto, El Conquistador (180 puestos)

Cada bus carga en minutos enteros en un puesto identificado. En ningun minuto cargan mas buses que puestos.

- Energia + reservas: 212,767.56 USD/dia; 505 reservas (1 diurnas, 504 nocturnas).
- Cota inferior (modelo relajado): 209,361.17 USD/dia. Distancia al optimo: a lo mas 1.60%.
- Eventos de carga: 3,996 (1.33 por ventana).
- Maximo de buses cargando a la vez: 180 de 180; puestos usados: 180.
- Carga por orden de llegada (misma Etapa 3): 325,642.81 USD/dia, 951 reservas.
- Tiempo: 605 s; pico de memoria 3,625 MB.

## Modelos

|   holgura_min |   delta_min | modelo                                      | estado                 |   objetivo_usd |     brecha |   segundos |     variables |   reservas |   binarias |
|--------------:|------------:|:--------------------------------------------|:-----------------------|---------------:|-----------:|-----------:|--------------:|-----------:|-----------:|
|             0 |          15 | Modelo relajado, LP (cota inferior)         | optimo                 |         209361 | nan        |      nan   | nan           |        nan |        nan |
|             0 |          15 | Programa exacto, arranque                   | factible               |         256948 | nan        |       43.6 |   2.30667e+06 |        689 |        nan |
|             0 |          15 | Programa exacto, MILP                       | optimo (brecha pedida) |         213423 |   0.003431 |      458.9 |   2.30667e+06 |        505 |       1172 |
|             0 |          15 | Programa exacto, final (energia + reservas) | entero y validado      |         212768 |   0.01601  |      604.5 | nan           |        505 |        nan |

## Energia por tramo horario

| periodo   | horas   |   precio_usd_kwh |      kwh |   costo_usd |
|:----------|:--------|-----------------:|---------:|------------:|
| P1        | 00-08   |              0.1 | 257317   |     25731.7 |
| P2        | 08-14   |              0.2 | 192875   |     28931.3 |
| P3        | 14-17   |              0.2 |   8034   |      1767.5 |
| P4        | 17-19   |              0.2 |  29769.2 |      4465.4 |
| P5        | 19-22   |              0.2 |  84266   |     18538.5 |
| P6        | 22-24   |              0.1 |  64392.6 |      7083.2 |

## Archivos
- `programa_puestos.csv`: una fila por carga (ventana, bus, puesto, inicio, fin, kWh).
- `programa_E2_exacto.csv`: una fila por ventana (kWh, inicio y fin de la carga, eventos, reserva, costo).
- `buses_cargando_24h.png`, `uso_de_cada_puesto.png` (+ .csv), `ocupacion_minutos.csv`, `resumen.csv`, `modelo.csv`, `energia_por_tarifa.csv`, `gurobi.log`.