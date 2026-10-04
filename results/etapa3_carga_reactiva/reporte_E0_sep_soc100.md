# Reporte Etapa 3 - Carga reactiva, escenario E0_sep, nivel 100%

Politica miope sobre las jornadas del VSP (escenario E0_sep). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 8,654 en el VSP -> **11,259** tras la carga (+2,605; 2,605 jornadas partidas: 2,591 por falta de hueco, 14 por falta de puesto).
- **Recargas intermedias:** 52 eventos en 47 jornadas (0.4% de las jornadas finales; el VSP estimaba 30.0% con energia sobre la bateria util).
- **Cargas finales:** 11,259; **ciclos no cumplidos:** 2,357 (retraso maximo 1001 min); cargas fragmentadas por falta de tramo continuo: 356.
- **Colas:** 8,598 eventos esperaron mas de 1 min por un puesto (maximo 1095 min; 52,660.1 h en total).
- **Energia:** 2,199.6 MWh cargados = 2,247.8 MWh consumidos (diferencia 0.00e+00 kWh). Costo 306,453 USD, 0.1393 USD/kWh, 51.5% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 664 km (de 260,167 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,814,750 | 130,083 | 139,130 | 306,453 | 56,555 | 589,250 | **4,036,222** | 2,311,988 |

- **Factibilidad:** INFACTIBLE (deficit de energia 48.2 MWh; atraso maximo de carga 1001 min). Los 2,357 ciclos no cumplidos se cubren con buses de reserva (589,250 USD/dia); costo sin reservas: 3,446,972 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |            kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|---------------:|------------:|-------------------:|-----------------:|
| final      |     11259 |    2.19408e+06 |   305525    |             289.13 |          1095.16 |
| intermedia |        52 | 5534.95        |      928.32 |               0.6  |             0.99 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal        |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:----------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Vespucio Norte  |       150 |                 150 |              100 |                        368 |               34.9 |
| El Conquistador |       180 |                 180 |              100 |                       1068 |               84.8 |
| Los Espinos     |       120 |                 120 |              100 |                       1440 |              100   |
| La Reina        |       100 |                 100 |              100 |                       1022 |               81.9 |
| Santa Rosa      |       150 |                 150 |              100 |                        892 |               70.8 |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. El costo de energia de esta tabla es lo que el MILP (Etapa 4) debe mejorar.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E0_sep_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E0_sep_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior (insumo del MILP, Bloque E). t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E0_sep_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E0_sep_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E0_sep_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E0_sep_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).