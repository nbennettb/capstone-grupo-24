# Reporte Etapa 3 - Carga reactiva, escenario E1_C2, nivel 100%

Politica miope sobre las jornadas del VSP (escenario E1_C2). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 7,366 en el VSP -> **10,258** tras la carga (+2,892; 2,892 jornadas partidas: 2,887 por falta de hueco, 5 por falta de puesto).
- **Recargas intermedias:** 60 eventos en 55 jornadas (0.5% de las jornadas finales; el VSP estimaba 39.2% con energia sobre la bateria util).
- **Cargas finales:** 10,258; **ciclos no cumplidos:** 2,204 (retraso maximo 932 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 8,640 eventos esperaron mas de 1 min por un puesto (maximo 799 min; 58,635.6 h en total).
- **Energia:** 2,221.0 MWh cargados = 2,221.0 MWh consumidos (diferencia 0.00e+00 kWh). Costo 310,362 USD, 0.1397 USD/kWh, 51.2% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 557 km (de 241,022 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,564,500 | 120,511 | 142,106 | 310,362 | 51,590 | 551,000 | **3,740,069** | 1,970,319 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 932 min). Los 2,204 ciclos no cumplidos se cubren con buses de reserva (551,000 USD/dia); costo sin reservas: 3,189,069 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |            kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|---------------:|------------:|-------------------:|-----------------:|
| final      |     10258 |    2.21559e+06 |   309405    |             342.96 |            799.2 |
| intermedia |        60 | 5418.72        |      956.73 |               0.52 |              1   |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal                 |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:-------------------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Los Espinos + Santa Rosa |       270 |                 270 |              100 |                       1120 |               85.6 |
| Vespucio Norte           |       150 |                 150 |              100 |                        378 |               34.7 |
| El Conquistador          |       180 |                 180 |              100 |                       1110 |               85.3 |
| La Reina                 |       100 |                 100 |              100 |                       1025 |               80.8 |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. El costo de energia de esta tabla es lo que el MILP (Etapa 4) debe mejorar.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E1_C2_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E1_C2_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior (insumo del MILP, Bloque E). t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E1_C2_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E1_C2_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E1_C2_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E1_C2_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).