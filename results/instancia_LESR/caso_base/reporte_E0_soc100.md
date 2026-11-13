# Reporte caso base - carga reactiva, escenario Caso base, nivel 100%

Politica miope sobre las jornadas sin bateria (escenario Caso base). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 3,789 en el VSP -> **5,034** tras la carga (+1,245; 1,245 jornadas partidas: 1,237 por falta de hueco, 8 por falta de puesto).
- **Recargas diurnas:** 15 eventos en 13 jornadas (0.3% de las jornadas finales; el VSP estimaba 32.7% con energia sobre la bateria util).
- **Cargas finales:** 5,034; **ciclos no cumplidos:** 1,088 (retraso maximo 981 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 4,066 eventos esperaron mas de 1 min por un puesto (maximo 788 min; 29,364.1 h en total).
- **Energia:** 1,017.6 MWh cargados = 1,017.6 MWh consumidos (diferencia 0.00e+00 kWh). Costo 144,781 USD, 0.1423 USD/kWh, 47.5% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 161 km (de 122,728 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,258,500 | 61,364 | 72,073 | 144,781 | 25,245 | 272,000 | **1,833,963** | 1,014,870 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 981 min). Los 1,088 ciclos no cumplidos se cubren con buses de reserva (272,000 USD/dia); costo sin reservas: 1,561,963 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |            kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|---------------:|------------:|-------------------:|-----------------:|
| final      |      5034 |    1.01624e+06 |   144527    |             349.99 |           788.18 |
| diurna |        15 | 1332           |      254.19 |               0.43 |             0.97 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal                 |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:-------------------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Los Espinos + Santa Rosa |       270 |                 270 |              100 |                       1127 |               87.9 |

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