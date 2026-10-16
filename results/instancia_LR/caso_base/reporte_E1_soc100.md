# Reporte caso base - carga reactiva, escenario Caso base con interlining, nivel 100%

Politica miope sobre las jornadas sin bateria (escenario Caso base con interlining). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 1,203 en el VSP -> **1,638** tras la carga (+435; 435 jornadas partidas: 435 por falta de hueco, 0 por falta de puesto).
- **Recargas diurnas:** 8 eventos en 8 jornadas (0.5% de las jornadas finales; el VSP estimaba 36.1% con energia sobre la bateria util).
- **Cargas finales:** 1,638; **ciclos no cumplidos:** 315 (retraso maximo 627 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 1,399 eventos esperaron mas de 1 min por un puesto (maximo 672 min; 8,852.3 h en total).
- **Energia:** 346.7 MWh cargados = 346.7 MWh consumidos (diferencia -0.00e+00 kWh). Costo 47,482 USD, 0.1369 USD/kWh, 51.6% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 49 km (de 37,397 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 409,500 | 18,699 | 21,080 | 47,482 | 8,230 | 78,750 | **583,740** | 320,858 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 627 min). Los 315 ciclos no cumplidos se cubren con buses de reserva (78,750 USD/dia); costo sin reservas: 504,990 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |       kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|----------:|------------:|-------------------:|-----------------:|
| final      |      1638 | 345791    |    47310.6  |             324.26 |           671.51 |
| diurna |         8 |    949.34 |      170.96 |               0.65 |             0.99 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal   |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:-----------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| La Reina   |       100 |                 100 |              100 |                       1023 |               80.9 |

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