# Reporte caso base - carga reactiva, escenario Caso base con interlining, nivel 100%

Politica miope sobre las jornadas sin bateria (escenario Caso base con interlining). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 2,166 en el VSP -> **3,000** tras la carga (+834; 834 jornadas partidas: 834 por falta de hueco, 0 por falta de puesto).
- **Recargas diurnas:** 14 eventos en 14 jornadas (0.5% de las jornadas finales; el VSP estimaba 38.6% con energia sobre la bateria util).
- **Cargas finales:** 3,000; **ciclos no cumplidos:** 684 (retraso maximo 912 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 2,581 eventos esperaron mas de 1 min por un puesto (maximo 725 min; 17,960.1 h en total).
- **Energia:** 645.0 MWh cargados = 645.0 MWh consumidos (diferencia -0.00e+00 kWh). Costo 89,514 USD, 0.1388 USD/kWh, 49.9% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 245 km (de 72,888 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 750,000 | 36,444 | 43,708 | 89,514 | 15,070 | 171,000 | **1,105,736** | 581,220 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 912 min). Los 684 ciclos no cumplidos se cubren con buses de reserva (171,000 USD/dia); costo sin reservas: 934,736 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |       kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|----------:|------------:|-------------------:|-----------------:|
| final      |      3000 | 643529    |    89271.5  |             359.2  |           724.79 |
| diurna |        14 |   1492.98 |      242.01 |               0.45 |             0.96 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal        |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:----------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| El Conquistador |       180 |                 180 |              100 |                       1084 |               83.5 |

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