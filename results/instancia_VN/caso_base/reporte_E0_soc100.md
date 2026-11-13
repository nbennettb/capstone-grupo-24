# Reporte caso base - carga reactiva, escenario Caso base, nivel 100%

Politica miope sobre las jornadas sin bateria (escenario Caso base). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 889 en el VSP -> **1,103** tras la carga (+214; 214 jornadas partidas: 209 por falta de hueco, 5 por falta de puesto).
- **Recargas diurnas:** 9 eventos en 8 jornadas (0.7% de las jornadas finales; el VSP estimaba 24.0% con energia sobre la bateria util).
- **Cargas finales:** 1,103; **ciclos no cumplidos:** 7 (retraso maximo 198 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 757 eventos esperaron mas de 1 min por un puesto (maximo 109 min; 917.4 h en total).
- **Energia:** 224.3 MWh cargados = 224.3 MWh consumidos (diferencia 0.00e+00 kWh). Costo 31,040 USD, 0.1384 USD/kWh, 66.9% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 46 km (de 17,056 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 275,750 | 8,528 | 6,255 | 31,040 | 5,560 | 1,750 | **328,884** | 234,277 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 198 min). Los 7 ciclos no cumplidos se cubren con buses de reserva (1,750 USD/dia); costo sin reservas: 327,134 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |    kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|-------:|------------:|-------------------:|-----------------:|
| final      |      1103 | 224011 |    30983.2  |               49.9 |           108.57 |
| diurna |         9 |    330 |       57.27 |                0.7 |             0.89 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal       |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:---------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Vespucio Norte |       150 |                 150 |              100 |                        368 |               34.9 |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. Es la linea base contra la que se comparan las Etapas 3 y 4.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E0_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E0_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior. t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E0_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E0_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E0_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E0_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).