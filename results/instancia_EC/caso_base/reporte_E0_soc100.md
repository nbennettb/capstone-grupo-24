# Reporte caso base - carga reactiva, escenario Caso base, nivel 100%

Politica miope sobre las jornadas sin bateria (escenario Caso base). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 2,643 en el VSP -> **3,396** tras la carga (+753; 753 jornadas partidas: 753 por falta de hueco, 0 por falta de puesto).
- **Recargas diurnas:** 20 eventos en 18 jornadas (0.5% de las jornadas finales; el VSP estimaba 28.4% con energia sobre la bateria util).
- **Cargas finales:** 3,396; **ciclos no cumplidos:** 574 (retraso maximo 826 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 2,698 eventos esperaron mas de 1 min por un puesto (maximo 697 min; 17,205.9 h en total).
- **Energia:** 654.1 MWh cargados = 654.1 MWh consumidos (diferencia 0.00e+00 kWh). Costo 90,680 USD, 0.1386 USD/kWh, 49.2% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 377 km (de 79,397 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 849,000 | 39,699 | 45,206 | 90,680 | 17,080 | 143,500 | **1,185,165** | 707,253 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 826 min). Los 574 ciclos no cumplidos se cubren con buses de reserva (143,500 USD/dia); costo sin reservas: 1,041,665 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |    kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|-------:|------------:|-------------------:|-----------------:|
| final      |      3396 | 652230 |    90367.2  |             303.99 |           697.4  |
| diurna |        20 |   1905 |      312.63 |               0.6  |             0.99 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal        |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:----------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| El Conquistador |       180 |                 180 |              100 |                       1068 |               84.8 |

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