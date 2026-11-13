# Etapa 4 - Programa de carga exacto al minuto, Los Espinos + Santa Rosa (270 puestos)

Cada bus carga en minutos enteros en un puesto identificado. En ningun minuto cargan mas buses que puestos.

- Energia + reservas: 353,690.30 USD/dia; 880 reservas (0 diurnas, 880 nocturnas).
- Cota inferior (modelo relajado): 348,869.63 USD/dia. Distancia al optimo: a lo mas 1.36%.
- Eventos de carga: 5,983 (1.29 por ventana).
- Maximo de buses cargando a la vez: 270 de 270; puestos usados: 270.
- Carga por orden de llegada (misma Etapa 3): 522,068.98 USD/dia, 1533 reservas.
- Tiempo: 1,536 s; pico de memoria 3,629 MB.

## Modelos

|   holgura_min |   delta_min | modelo                                      | estado                 |   objetivo_usd |     brecha |   segundos |     variables |   reservas |   binarias |
|--------------:|------------:|:--------------------------------------------|:-----------------------|---------------:|-----------:|-----------:|--------------:|-----------:|-----------:|
|             0 |          15 | Modelo relajado, LP (cota inferior)         | optimo                 |         348870 | nan        |      nan   | nan           |        nan |        nan |
|             0 |          15 | Programa exacto, arranque                   | factible               |         405599 | nan        |       80.5 |   3.68839e+06 |       1084 |        nan |
|             0 |          15 | Programa exacto, MILP                       | optimo (brecha pedida) |         354599 |   0.002176 |     1185.2 |   3.68839e+06 |        880 |       1912 |
|             0 |          15 | Programa exacto, final (energia + reservas) | entero y validado      |         353690 |   0.01363  |     1536.1 | nan           |        880 |        nan |

## Energia por tramo horario

| periodo   | horas   |   precio_usd_kwh |      kwh |   costo_usd |
|:----------|:--------|-----------------:|---------:|------------:|
| P1        | 00-08   |              0.1 | 386027   |     38602.7 |
| P2        | 08-14   |              0.2 | 289342   |     43401.3 |
| P3        | 14-17   |              0.2 |  11006.9 |      2421.5 |
| P4        | 17-19   |              0.2 |  96484.1 |     14472.6 |
| P5        | 19-22   |              0.2 | 109801   |     24156.3 |
| P6        | 22-24   |              0.1 |  96689.4 |     10635.8 |

## Archivos
- `programa_puestos.csv`: una fila por carga (ventana, bus, puesto, inicio, fin, kWh).
- `programa_E2_exacto.csv`: una fila por ventana (kWh, inicio y fin de la carga, eventos, reserva, costo).
- `buses_cargando_24h.png`, `uso_de_cada_puesto.png` (+ .csv), `ocupacion_minutos.csv`, `resumen.csv`, `modelo.csv`, `energia_por_tarifa.csv`, `gurobi.log`.