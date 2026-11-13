# Etapa 4 - Programa de carga exacto al minuto, Vespucio Norte (150 puestos)

Cada bus carga en minutos enteros en un puesto identificado. En ningun minuto cargan mas buses que puestos.

- Energia + reservas: 31,524.49 USD/dia; 29 reservas (0 diurnas, 29 nocturnas).
- Cota inferior (modelo relajado): 31,524.30 USD/dia. Distancia al optimo: a lo mas 0.00%.
- Eventos de carga: 1,278 (1.23 por ventana).
- Maximo de buses cargando a la vez: 150 de 150; puestos usados: 150.
- Carga por orden de llegada (misma Etapa 3): 38,913.87 USD/dia, 33 reservas.
- Tiempo: 22 s; pico de memoria 767 MB.

## Modelos

|   holgura_min |   delta_min | modelo                                      | estado                 |   objetivo_usd |     brecha |   segundos |   variables |   reservas |   binarias |
|--------------:|------------:|:--------------------------------------------|:-----------------------|---------------:|-----------:|-----------:|------------:|-----------:|-----------:|
|             0 |          15 | Modelo relajado, LP (cota inferior)         | optimo                 |        31524.3 | nan        |      nan   |         nan |        nan |        nan |
|             0 |          15 | Programa exacto, arranque                   | factible               |        31708   | nan        |        4.2 |      425632 |         29 |        nan |
|             0 |          15 | Programa exacto, MILP                       | optimo (brecha pedida) |        31708   |   0.004751 |        7.9 |      425632 |         29 |         33 |
|             0 |          15 | Programa exacto, final (energia + reservas) | entero y validado      |        31524.5 |   6e-06    |       22.4 |         nan |         29 |        nan |

## Energia por tramo horario

| periodo   | horas   |   precio_usd_kwh |      kwh |   costo_usd |
|:----------|:--------|-----------------:|---------:|------------:|
| P1        | 00-08   |              0.1 | 187014   |     18701.4 |
| P2        | 08-14   |              0.2 |  17774.6 |      2666.2 |
| P3        | 14-17   |              0.2 |     30   |         6.6 |
| P4        | 17-19   |              0.2 |   7856.6 |      1178.5 |
| P5        | 19-22   |              0.2 |   6618.1 |      1456   |
| P6        | 22-24   |              0.1 |   2417   |       265.9 |

## Archivos
- `programa_puestos.csv`: una fila por carga (ventana, bus, puesto, inicio, fin, kWh).
- `programa_E2_exacto.csv`: una fila por ventana (kWh, inicio y fin de la carga, eventos, reserva, costo).
- `buses_cargando_24h.png`, `uso_de_cada_puesto.png` (+ .csv), `ocupacion_minutos.csv`, `resumen.csv`, `modelo.csv`, `energia_por_tarifa.csv`, `gurobi.log`.