# Reporte - barrido de niveles de bateria (escenario E1)

La condicion ciclica (inicio = fin) es una **restriccion**: el nivel se elige entre las soluciones que la cumplen. Un bus que no termina de cargar antes de su salida del dia siguiente (ciclo no cumplido) se reemplaza por un bus de reserva ya cargado (250 USD/dia); el costo total incluye las reservas. Regla completa en `docs/context/02_supuestos_y_decisiones.md` (B6) y `docs/justificaciones/04_nivel_carga_ciclico.md`.

## Resultado: el nivel base es **100%**

- Niveles evaluados en E1: 100%, 90%, 80%, 70%, 65%, 60%, 55%, 50%. Piso fisico: 50%.
- Costo total al 100% (con 2,207 buses de reserva): **3,751,250 USD/dia** (12,502 buses en total); frente al 100%: +0.00%.
- **Familia (a), ciclica sin reservas:** ningun nivel evaluado cierra el ciclo sin reservas.
- **Familia (b), con reservas:** el mejor es 100% (3,751,250 USD/dia).

## Tabla del escenario que decide

|   nivel_pct |   buses_final |   jornadas_partidas |   buses_reserva |   deficit_mwh |   cota_lp_pct |   costo_sin_reservas_usd |   costo_reservas_usd |   costo_total_usd | factible   | ciclica_sin_reservas   | elegido   |
|------------:|--------------:|--------------------:|----------------:|--------------:|--------------:|-------------------------:|---------------------:|------------------:|:-----------|:-----------------------|:----------|
|         100 |         10295 |                2929 |            2207 |           0   |          84   |                  3199500 |               551750 |           3751250 | True       | False                  | True      |
|          90 |         11791 |                4425 |            1417 |           0   |          95.5 |                  3619533 |               354250 |           3973783 | True       | False                  | False     |
|          80 |         13267 |                5901 |             246 |           0   |         100   |                  4007852 |                61500 |           4069352 | True       | False                  | False     |
|          70 |         14747 |                7381 |              73 |           0   |         100   |                  4405755 |                18250 |           4424005 | True       | False                  | False     |
|          65 |         15936 |                8570 |              50 |           0   |         100   |                  4725423 |                12500 |           4737923 | True       | False                  | False     |
|          60 |         17717 |               10351 |              20 |           0   |         nan   |                  5201564 |                 5000 |           5206564 | True       | False                  | False     |
|          55 |         19671 |               12305 |              13 |           0   |         nan   |                  5729331 |                 3250 |           5732581 | True       | False                  | False     |
|          50 |         22549 |               15183 |             274 |          25.3 |         nan   |                  6505232 |                68500 |           6573732 | False      | False                  | False     |

Cota LP: porcentaje de la energia de las cargas finales que cabe dentro de las ventanas de los buses con una carga perfecta (si es menor a 100%, ningun programa de carga cierra el ciclo con esas jornadas).

Diferencia del costo total respecto del nivel mas alto:

|   nivel_pct |   delta_costo_vs_100_pct |
|------------:|-------------------------:|
|         100 |                     0    |
|          90 |                     5.93 |
|          80 |                     8.48 |
|          70 |                    17.93 |
|          65 |                    26.3  |
|          60 |                    38.8  |
|          55 |                    52.82 |
|          50 |                    75.24 |

## Robustez y decision por escenario

| escenario   | rol      | niveles_evaluados        |   piso_fisico_pct |   nivel_minimo_costo_pct |   nivel_elegido_pct |   costo_elegido_usd |   reservas_en_elegido |   buses_totales_elegido |   ciclica_sin_reservas_nivel_pct |   ciclica_sin_reservas_costo_usd |   costo_vs_100_pct | coincide_con_principal   |
|:------------|:---------|:-------------------------|------------------:|-------------------------:|--------------------:|--------------------:|----------------------:|------------------------:|---------------------------------:|---------------------------------:|-------------------:|:-------------------------|
| E1          | decide   | 100,90,80,70,65,60,55,50 |                50 |                      100 |                 100 |         3.75125e+06 |                  2207 |                   12502 |                              nan |                              nan |                  0 | True                     |
| E0          | robustez | 100,90,80,70,65,60,55,50 |                50 |                      100 |                 100 |         3.95806e+06 |                  1988 |                   13247 |                              nan |                              nan |                  0 | True                     |

La eleccion es **robusta**: E0 elige el mismo nivel que E1.

## Evidencia: terminales separados (no compiten; infactibles)

| escenario   |   nivel_pct |   buses_final |   kwh_deficit |   cota_lp_pct |   factible |   costo_total_usd |
|:------------|------------:|--------------:|--------------:|--------------:|-----------:|------------------:|
| E0_sep      |         100 |         11259 |       48196.9 |          89.4 |          0 |           4036222 |
| E1_sep      |         100 |         10415 |       44099.6 |          84.4 |          0 |           3849470 |

Sin unir Los Espinos y Santa Rosa, Los Espinos no tiene puestos para reponer toda su energia (deficit); las reservas no lo arreglan. Por eso la union es parte de la configuracion base.

## Limitaciones
- Politica reactiva y miope; con una carga programada (Etapa 4) la capacidad nocturna se usaria mejor, pero la cota LP muestra que no alcanza para cerrar el ciclo con las jornadas actuales.
- Los buses de reserva son una cota superior simple (no comparten reservas entre atrasos cortos).
- Carga lineal a 180 kW, sin curva CC-CV; un solo dia laboral; el ciclo supone que el dia siguiente es igual.

## Archivos
- `tablas/barrido_niveles.csv`: una fila por escenario y nivel (factibilidad, reservas, cota LP, minimo, empate, elegido).
- `tablas/decision_barrido.csv`: la decision por escenario, las dos familias y si coincide con el principal.
- `tablas/evidencia_terminales_separados.csv`: E0_sep y E1_sep al 100% (infactibles).
- `graficos/barrido_costo_total.png`: costo total apilado por nivel (con reservas) y el costo del ciclo.
- `graficos/barrido_ciclos_y_cota.png`: buses, jornadas partidas, reservas y cota LP por nivel.
- `graficos/barrido_robustez.png`: costo total por nivel en E1 y E0.
- Corrida completa del nivel elegido: `../tablas/*_E1_soc100.csv`, `../graficos/*_E1_soc100.png`, `../reporte_E1_soc100.md`.