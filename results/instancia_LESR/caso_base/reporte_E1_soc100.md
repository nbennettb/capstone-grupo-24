# Reporte caso base - carga reactiva, escenario Caso base con interlining, nivel 100%

Politica miope sobre las jornadas sin bateria (escenario Caso base con interlining). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 3,204 en el VSP -> **4,622** tras la carga (+1,418; 1,418 jornadas partidas: 1,415 por falta de hueco, 3 por falta de puesto).
- **Recargas diurnas:** 26 eventos en 24 jornadas (0.5% de las jornadas finales; el VSP estimaba 44.1% con energia sobre la bateria util).
- **Cargas finales:** 4,622; **ciclos no cumplidos:** 1,205 (retraso maximo 766 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 3,935 eventos esperaron mas de 1 min por un puesto (maximo 817 min; 31,291.6 h en total).
- **Energia:** 1,005.9 MWh cargados = 1,005.9 MWh consumidos (diferencia 0.00e+00 kWh). Costo 142,843 USD, 0.1420 USD/kWh, 48.0% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 266 km (de 114,390 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,155,500 | 57,195 | 72,401 | 142,843 | 23,240 | 301,250 | **1,752,430** | 859,183 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 766 min). Los 1,205 ciclos no cumplidos se cubren con buses de reserva (301,250 USD/dia); costo sin reservas: 1,451,180 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |            kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|---------------:|------------:|-------------------:|-----------------:|
| final      |      4622 |    1.00429e+06 |   142561    |             406.21 |           817.07 |
| diurna |        26 | 1605           |      282.33 |               0.52 |             0.98 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal                 |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:-------------------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Los Espinos + Santa Rosa |       270 |                 270 |              100 |                       1138 |               86.8 |

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