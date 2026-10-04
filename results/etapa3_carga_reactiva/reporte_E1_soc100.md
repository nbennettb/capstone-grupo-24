# Reporte Etapa 3 - Carga reactiva, escenario E1, nivel 100%

Politica miope sobre las jornadas del VSP (escenario E1). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 7,366 en el VSP -> **10,295** tras la carga (+2,929; 2,929 jornadas partidas: 2,925 por falta de hueco, 4 por falta de puesto).
- **Recargas intermedias:** 60 eventos en 57 jornadas (0.6% de las jornadas finales; el VSP estimaba 39.7% con energia sobre la bateria util).
- **Cargas finales:** 10,295; **ciclos no cumplidos:** 2,207 (retraso maximo 912 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 8,669 eventos esperaron mas de 1 min por un puesto (maximo 817 min; 59,285.6 h en total).
- **Energia:** 2,221.4 MWh cargados = 2,221.4 MWh consumidos (diferencia -0.00e+00 kWh). Costo 310,089 USD, 0.1396 USD/kWh, 51.4% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 604 km (de 241,336 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,573,750 | 120,668 | 143,218 | 310,089 | 51,775 | 551,750 | **3,751,250** | 1,970,265 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 912 min). Los 2,207 ciclos no cumplidos se cubren con buses de reserva (551,750 USD/dia); costo sin reservas: 3,199,500 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |           kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|--------------:|------------:|-------------------:|-----------------:|
| final      |     10295 |    2.2167e+06 |   309260    |             345.52 |           817.07 |
| intermedia |        60 | 4749.32       |      829.79 |               0.52 |             0.99 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal                 |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:-------------------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Los Espinos + Santa Rosa |       270 |                 270 |              100 |                       1138 |               86.8 |
| Vespucio Norte           |       150 |                 150 |              100 |                        382 |               34.8 |
| El Conquistador          |       180 |                 180 |              100 |                       1084 |               83.5 |
| La Reina                 |       100 |                 100 |              100 |                       1023 |               80.9 |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. El costo de energia de esta tabla es lo que el MILP (Etapa 4) debe mejorar.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E1_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E1_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior (insumo del MILP, Bloque E). t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E1_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E1_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E1_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E1_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).