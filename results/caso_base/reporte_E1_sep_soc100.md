# Reporte Etapa 3 - Carga reactiva, escenario E1_sep, nivel 100%

Politica miope sobre las jornadas del VSP (escenario E1_sep). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 7,460 en el VSP -> **10,415** tras la carga (+2,955; 2,955 jornadas partidas: 2,951 por falta de hueco, 4 por falta de puesto).
- **Recargas intermedias:** 61 eventos en 55 jornadas (0.5% de las jornadas finales; el VSP estimaba 39.6% con energia sobre la bateria util).
- **Cargas finales:** 10,415; **ciclos no cumplidos:** 2,518 (retraso maximo 908 min); cargas fragmentadas por falta de tramo continuo: 342.
- **Colas:** 8,438 eventos esperaron mas de 1 min por un puesto (maximo 1124 min; 56,373.7 h en total).
- **Energia:** 2,182.6 MWh cargados = 2,226.7 MWh consumidos (diferencia 0.00e+00 kWh). Costo 303,180 USD, 0.1389 USD/kWh, 52.1% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 601 km (de 245,058 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,603,750 | 122,529 | 138,132 | 303,180 | 52,380 | 629,500 | **3,849,470** | 1,995,343 |

- **Factibilidad:** INFACTIBLE (deficit de energia 44.1 MWh; atraso maximo de carga 908 min). Los 2,518 ciclos no cumplidos se cubren con buses de reserva (629,500 USD/dia); costo sin reservas: 3,219,970 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |            kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|---------------:|------------:|-------------------:|-----------------:|
| final      |     10415 |    2.17725e+06 |   302230    |             334.79 |          1123.88 |
| intermedia |        61 | 5305.98        |      950.04 |               0.48 |             0.99 |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal        |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:----------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Vespucio Norte  |       150 |                 150 |              100 |                        382 |               34.7 |
| El Conquistador |       180 |                 180 |              100 |                       1090 |               83.7 |
| Los Espinos     |       120 |                 120 |              100 |                       1440 |              100   |
| La Reina        |       100 |                 100 |              100 |                       1027 |               81   |
| Santa Rosa      |       150 |                 150 |              100 |                        876 |               70   |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. El costo de energia de esta tabla es lo que el MILP (Etapa 4) debe mejorar.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E1_sep_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E1_sep_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior (insumo del MILP, Bloque E). t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E1_sep_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E1_sep_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E1_sep_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E1_sep_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).