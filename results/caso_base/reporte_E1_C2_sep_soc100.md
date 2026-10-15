# Reporte Etapa 3 - Carga reactiva, escenario E1_C2_sep, nivel 100%

Politica miope sobre las jornadas del VSP (escenario E1_C2_sep). Nivel de partida, de llegada y tope de carga: 100% (energia utilizable 315 kWh). Carga parcial cuando el hueco no alcanza; la jornada se parte solo si ni asi puede seguir.

## Resultado

- **Buses:** 7,462 en el VSP -> **10,343** tras la carga (+2,881; 2,881 jornadas partidas: 2,875 por falta de hueco, 6 por falta de puesto).
- **Recargas intermedias:** 56 eventos en 54 jornadas (0.5% de las jornadas finales; el VSP estimaba 38.7% con energia sobre la bateria util).
- **Cargas finales:** 10,343; **ciclos no cumplidos:** 2,363 (retraso maximo 939 min); cargas fragmentadas por falta de tramo continuo: 156.
- **Colas:** 8,576 eventos esperaron mas de 1 min por un puesto (maximo 1090 min; 58,685.0 h en total).
- **Energia:** 2,203.1 MWh cargados = 2,224.4 MWh consumidos (diferencia -0.00e+00 kWh). Costo 306,984 USD, 0.1393 USD/kWh, 51.7% en valle (P1 y P6).
- **Km sin pasajeros por ir a cargar:** 644 km (de 243,438 km vacios).

## Costo total (flota + km vacios + espera + energia + eventos de carga + buses de reserva)

| Flota | Km vacios | Espera | Energia | Eventos | Reservas | **Total** | Operacion del VSP (sin energia) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,585,750 | 121,719 | 142,358 | 306,984 | 51,995 | 590,750 | **3,799,556** | 1,995,921 |

- **Factibilidad:** INFACTIBLE (deficit de energia 21.3 MWh; atraso maximo de carga 939 min). Los 2,363 ciclos no cumplidos se cubren con buses de reserva (590,750 USD/dia); costo sin reservas: 3,208,806 USD/dia.

## Eventos de carga por tipo

| tipo       |   eventos |            kwh |   costo_usd |   espera_media_min |   espera_max_min |
|:-----------|----------:|---------------:|------------:|-------------------:|-----------------:|
| final      |     10343 |    2.19721e+06 |   305947    |             344.6  |          1090.18 |
| intermedia |        56 | 5883.66        |     1037.18 |               0.47 |             1    |

## Uso de los puestos por electroterminal (modulo 24 h)

| terminal        |   puestos |   maximo_simultaneo |   uso_maximo_pct |   minutos_saturados_al_dia |   uso_promedio_pct |
|:----------------|----------:|--------------------:|-----------------:|---------------------------:|-------------------:|
| Vespucio Norte  |       150 |                 150 |              100 |                        386 |               34.7 |
| El Conquistador |       180 |                 180 |              100 |                       1115 |               85.4 |
| Los Espinos     |       120 |                 120 |              100 |                       1440 |              100   |
| La Reina        |       100 |                 100 |              100 |                       1028 |               80.8 |
| Santa Rosa      |       150 |                 150 |              100 |                        903 |               71.3 |

## Como leerlo
- La politica es reactiva: no mira tarifa ni el futuro. El costo de energia de esta tabla es lo que el MILP (Etapa 4) debe mejorar.
- 'Espera' del costo total = tiempo parado entre expediciones (igual que en el VSP) + espera en cola por un puesto.
- Un 'ciclo no cumplido' es un bus que no alcanza a terminar su carga final antes de su primera salida del dia siguiente; la energia se carga igual (el balance cierra).

## Archivos (`tablas/` y `graficos/`)
- `tablas/eventos_E1_C2_sep_soc100.csv`: cada carga (jornada, terminal, tipo, llegada, inicio, fin, espera, kWh, costo, SOC).
- `tablas/ventanas_E1_C2_sep_soc100.csv`: ventanas en que cada bus esta en el electroterminal y puede cargar, con la energia consumida desde la ventana anterior (insumo del MILP, Bloque E). t_fin de la ventana final = primera salida del dia siguiente.
- `tablas/jornadas_E1_C2_sep_soc100.csv`: jornadas tras las particiones (id `<bus>.<parte>`), con km, kWh y esperas.
- `tablas/ocupacion_E1_C2_sep_soc100.csv`: buses cargando por minuto (modulo 24 h) y terminal.
- `tablas/resumen_carga.csv`: una fila por escenario y nivel (todas las cifras de este reporte).
- `graficos/ocupacion_E1_C2_sep_soc100.png`: buses cargando durante el dia vs. puestos, con la tarifa punta sombreada.
- `graficos/soc_ejemplo_E1_C2_sep_soc100.png`: SOC a lo largo del dia de jornadas reales (con y sin recarga).