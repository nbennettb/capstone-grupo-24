# Reporte Etapa 3 - Carga reactiva, escenario E0, nivel 100%

Politica miope sobre las jornadas del VSP (escenario E0). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 8,654 en el VSP -> **11,259** tras la carga (+2,605; 2,605 jornadas partidas: 2,591 por falta de hueco, 14 por falta de puesto).
- **Recargas intermedias:** 53 eventos en 48 jornadas (0.4% de las jornadas finales; el VSP estimaba 30.0% con energia sobre la bateria util).
- **Cargas finales:** 11,259; **ciclos no cumplidos:** 1,988 (retraso maximo 981 min); cargas fragmentadas por falta de tramo continuo: 0.
- **Colas:** 8,931 eventos esperaron mas de 1 min por un puesto (maximo 788 min; 56,071.0 h en total).
- **Energia:** 2,247.1 MWh cargados = 2,247.1 MWh consumidos (diferencia -0.00e+00 kWh). Costo 314,653 USD, 0.1400 USD/kWh, 50.4% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 680 km (de 259,660 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,814,750 | 129,830 | 145,270 | 314,653 | 56,560 | 497,000 | **3,958,063** | 2,311,988 |

- **Factibilidad:** FACTIBLE (deficit de energia 0.0 MWh; atraso maximo de carga 981 min). Los 1,988 ciclos no cumplidos se cubren con buses de reserva (497,000 USD/dia); costo sin reservas: 3,461,063 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |            kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|---------------:|------------:|-------------------:|-----------------:|
| final      |     11259 |    2.24152e+06 |   313715    |             298.8  |           788.18 |
| intermedia |        53 | 5576.95        |      937.56 |               0.59 |             0.99 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal                 |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:-------------------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Los Espinos + Santa Rosa |       270 |                 270 |              100 |                       1127 |               87.9 |
| Vespucio Norte           |       150 |                 150 |              100 |                        368 |               34.9 |
| El Conquistador          |       180 |                 180 |              100 |                       1068 |               84.8 |
| La Reina                 |       100 |                 100 |              100 |                       1022 |               81.9 |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. El costo de energia de esta tabla es lo que el MILP (Etapa 4) debe mejorar.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E0_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E0_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior (insumo del MILP, Bloque E). t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E0_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E0_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E0_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E0_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).