# Etapa 4 - Programa de carga exacto al minuto, La Reina (60 puestos)

**PRUEBA: no es la instancia real.**

Cada bus carga en minutos enteros en un puesto identificado. En ningun minuto cargan mas buses que puestos.

- Energia + reservas: 70,821.69 USD/dia; 163 reservas (0 diurnas, 163 nocturnas).
- Cota inferior (modelo relajado): 69,384.37 USD/dia. Distancia al optimo: a lo mas 2.03%.
- Eventos de carga: 1,543 (1.51 por ventana).
- Maximo de buses cargando a la vez: 60 de 60; puestos usados: 60.
- Carga por orden de llegada (misma Etapa 3): 107,949.48 USD/dia, 309 reservas.
- Tiempo: 227 s; pico de memoria 1,723 MB.

## Modelos

|   holgura_min |   delta_min | modelo                                      | estado                 |   objetivo_usd |     brecha |   segundos |   variables |   reservas |   binarias |
|--------------:|------------:|:--------------------------------------------|:-----------------------|---------------:|-----------:|-----------:|------------:|-----------:|-----------:|
|             0 |          15 | Modelo relajado, LP (cota inferior)         | optimo                 |        69384.4 | nan        |      nan   |         nan |        nan |        nan |
|             0 |          15 | Programa exacto, arranque                   | factible               |        74682.8 | nan        |       23.1 |      781535 |        178 |        nan |
|             0 |          15 | Programa exacto, MILP                       | optimo (brecha pedida) |        71024.8 |   0.00204  |      156.6 |      781535 |        163 |        379 |
|             0 |          15 | Programa exacto, final (energia + reservas) | entero y validado      |        70821.7 |   0.020295 |      226.6 |         nan |        163 |        nan |

## Energia por tramo horario

| periodo   | horas   |   precio_usd_kwh |     kwh |   costo_usd |
|:----------|:--------|-----------------:|--------:|------------:|
| P1        | 00-08   |              0.1 | 85770.7 |      8577.1 |
| P2        | 08-14   |              0.2 | 64333.9 |      9650.1 |
| P3        | 14-17   |              0.2 |  3448.3 |       758.6 |
| P4        | 17-19   |              0.2 | 13698.9 |      2054.8 |
| P5        | 19-22   |              0.2 | 30315.5 |      6669.4 |
| P6        | 22-24   |              0.1 | 21469.7 |      2361.7 |

## Archivos
- `programa_puestos.csv`: una fila por carga (ventana, bus, puesto, inicio, fin, kWh).
- `programa_E2_exacto.csv`: una fila por ventana (kWh, inicio y fin de la carga, eventos, reserva, costo).
- `buses_cargando_24h.png`, `uso_de_cada_puesto.png` (+ .csv), `ocupacion_minutos.csv`, `resumen.csv`, `modelo.csv`, `energia_por_tarifa.csv`, `gurobi.log`.