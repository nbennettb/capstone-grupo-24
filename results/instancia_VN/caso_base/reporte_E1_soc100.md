# Reporte caso base - carga reactiva, escenario Caso base con interlining, nivel 100%

Politica miope sobre las jornadas sin bateria (escenario Caso base con interlining). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 793 en el VSP -> **1,035** tras la carga (+242; 242 jornadas partidas: 241 por falta de hueco, 1 por falta de puesto).
- **Recargas diurnas:** 12 eventos en 11 jornadas (1.1% de las jornadas finales; el VSP estimaba 30.8% con energia sobre la bateria util).
- **Cargas finales:** 1,035; **ciclos no cumplidos:** 3 (retraso maximo 112 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 754 eventos esperaron mas de 1 min por un puesto (maximo 139 min; 1,181.6 h en total).
- **Energia:** 223.8 MWh cargados = 223.8 MWh consumidos (diferencia 0.00e+00 kWh). Costo 30,251 USD, 0.1352 USD/kWh, 70.4% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 44 km (de 16,661 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 258,750 | 8,330 | 6,028 | 30,251 | 5,235 | 750 | **309,344** | 209,004 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 112 min). Los 3 ciclos no cumplidos se cubren con buses de reserva (750 USD/dia); costo sin reservas: 308,594 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |    kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|-------:|------------:|-------------------:|-----------------:|
| final      |      1035 | 223086 |    30116.2  |              68.49 |           139.21 |
| diurna |        12 |    702 |      134.49 |               0.5  |             0.91 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal       |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:---------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Vespucio Norte |       150 |                 150 |              100 |                        382 |               34.8 |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. Es la linea base contra la que se comparan las Etapas 3 y 4.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E1_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E1_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior. t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E1_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E1_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E1_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E1_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).