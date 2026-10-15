# Reporte caso base - carga reactiva, escenario E0, nivel 100%

Politica miope sobre las jornadas del VSP (escenario E0). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 1,333 en el VSP -> **1,726** tras la carga (+393; 393 jornadas partidas: 392 por falta de hueco, 1 por falta de puesto).
- **Recargas intermedias:** 9 eventos en 9 jornadas (0.5% de las jornadas finales; el VSP estimaba 29.6% con energia sobre la bateria util).
- **Cargas finales:** 1,726; **ciclos no cumplidos:** 319 (retraso maximo 839 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 1,410 eventos esperaron mas de 1 min por un puesto (maximo 684 min; 8,583.6 h en total).
- **Energia:** 351.1 MWh cargados = 351.1 MWh consumidos (diferencia 0.00e+00 kWh). Costo 48,151 USD, 0.1372 USD/kWh, 50.9% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 97 km (de 40,479 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 431,500 | 20,240 | 21,736 | 48,151 | 8,675 | 79,750 | **610,052** | 355,588 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 839 min). Los 319 ciclos no cumplidos se cubren con buses de reserva (79,750 USD/dia); costo sin reservas: 530,302 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |       kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|----------:|------------:|-------------------:|-----------------:|
| final      |      1726 | 349046    |    47838    |             298.38 |           683.48 |
| intermedia |         9 |   2009.95 |      313.47 |               0.75 |             0.91 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal   |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:-----------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| La Reina   |       100 |                 100 |              100 |                       1022 |               81.9 |

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