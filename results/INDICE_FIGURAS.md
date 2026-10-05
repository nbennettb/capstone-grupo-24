# Índice de figuras

Cada figura sostiene un mensaje y tiene sus datos (CSV) debajo. **Sección sugerida:** P = presentación, I = informe, A = anexo. Las rutas son relativas a `results/`.
Las figuras marcadas con ★ son las candidatas a la presentación de 10 minutos. Todo lo del MILP es **instancia reducida** (no el resultado de toda la red).

## Datos y preprocesamiento (Etapa 0)

| Figura | Mensaje | Datos | Sección |
|---|---|---|---|
| `etapa0_preprocesamiento/graficos/buses_por_hora.png` | La demanda de buses se concentra en horas punta: 6.539 viajes simultáneos a las 8:00 (cota inferior de flota) | `etapa0_preprocesamiento/concurrencia_por_minuto.csv` | P (datos) / I |
| `etapa0_preprocesamiento/graficos/energia_por_expedicion.png` | La energía por viaje es muy variable; 1.883,6 MWh comerciales al día | `etapa0_preprocesamiento/distribucion_expediciones.csv` | I |
| `etapa0_preprocesamiento/graficos/duracion_y_distancia.png` | Distribución de duración y distancia de las expediciones | `etapa0_preprocesamiento/distribucion_expediciones.csv` | A |
| `etapa0_preprocesamiento/graficos/ida_vuelta_distancia.png` ★ | 94,7% de las rutas cierra la ida a menos de 500 m de donde empieza la vuelta: por eso se agrupa por ruta | `data-processed/rutas_ida_vuelta.csv` | P (por qué clusterizar por ruta) / I |
| `etapa0_calibracion_deadhead/graficos/factor_por_escala.png` ★ | El rodeo real medido (1,04-1,38) respalda el factor 1,3 del deadhead | `etapa0_calibracion_deadhead/tablas/factor_por_escala.csv` | P (responde la crítica anunciada) / I |
| `etapa0_calibracion_deadhead/graficos/ejemplo_trazado.png` | Ejemplo real de cómo se mide el rodeo en un trazado | `etapa0_calibracion_deadhead/tablas/factor_por_trazado.csv` | A |

## Clustering de rutas (Etapa 1)

| Figura | Mensaje | Datos | Sección |
|---|---|---|---|
| `etapa1_clustering/mapas/mapa_c1b.png` | Asignación base C1: cada ruta al electroterminal más cercano a sus paraderos | `data-processed/rutas_cluster_c1b.csv` | I |
| `etapa1_clustering/mapas/mapa_c2.png` | Propuesta C2: con capacidad de carga solo cambian 5 rutas | `data-processed/rutas_cluster_c2.csv` | I |
| `etapa1_clustering/mapas/mapa_diferencias.png` | Las rutas que cambian entre C1 y C2 | `etapa1_clustering/tablas/rutas_que_cambian.csv` | A |
| `etapa1_clustering/mapas/mapa_c1a.png` | Control: criterio del centroide | `data-processed/rutas_cluster_c1a.csv` | A |
| `etapa1_clustering/mapas/mapa_terminal_los_espinos.png` y `mapa_terminal_santa_rosa.png` ★ | Los Espinos y Santa Rosa están a 1,11 km: por eso se pueden unir | `etapa1_clustering/tablas/capacidad_por_terminal.csv` | P (decisión como parte de la historia) / I |
| `etapa1_clustering/mapas/mapa_terminal_{el_conquistador,la_reina,vespucio_norte}.png`, `mapa_paraderos_terminales.png` | Rutas y paraderos por electroterminal | `etapa1_clustering/tablas/resumen_por_terminal.csv` | A |
| `etapa1_clustering/graficos/rutas_por_terminal.png` | Rutas asignadas por electroterminal y estrategia | `etapa1_clustering/tablas/resumen_por_terminal.csv` | A |
| `etapa1_clustering/graficos/distancias.png` | El criterio de distancia (centroide vs paraderos) cambia 0,7% del costo | `etapa1_clustering/tablas/comparacion_estrategias.csv` | I |
| `etapa1_clustering/graficos/capacidad_ciclo.png` | Con la carga real, Los Espinos queda sobre su capacidad si no se mueven rutas | `etapa1_clustering/tablas/capacidad_por_terminal.csv` | I |
| `etapa1_clustering/graficos/capacidad_sin_vs_con_recuperacion.png` | Sin recuperar la batería el modelo no pagaría ~93% de la energía y los puestos usarían 2% de su capacidad | `etapa1_clustering/tablas/capacidad_sin_vs_con_recuperacion.csv` | I (por qué el ciclo diario) |
| `etapa1_clustering/graficos/barrido_theta.png` | Cuándo la holgura de capacidad empieza a mover rutas (θ = 0,9, 0,8; infactible a 0,7) | `etapa1_clustering/tablas/barrido_theta.csv` | A |

## Asignación de buses (Etapa 2)

| Figura | Mensaje | Datos | Sección |
|---|---|---|---|
| `etapa2_vsp/graficos/escalera_buses.png` ★ | Escalera de flota: E0 8.654 → E1 7.366 → LB 7.055; el interlining concentra el 81% de la ganancia | `etapa2_vsp/tablas/escalera_escenarios.csv` | P (caso base y escalera) / I |
| `etapa2_vsp/graficos/escalera_costo.png` | El costo de operación se reduce 14,8% con interlining; viene de la flota | `etapa2_vsp/tablas/escalera_escenarios.csv` | I |
| `etapa2_vsp/graficos/sensibilidad_deadhead.png` ★ | El factor de desvío importa poco (±1% de flota); el layover es el supuesto más sensible (−2,8% a +6,0%) | `etapa2_vsp/tablas/sensibilidad_deadhead.csv` | P (si hay tiempo) / I |
| `etapa2_vsp/graficos/energia_por_jornada_E0_E1.png` | La batería no alcanza para el día: muchas jornadas superan la energía útil | `etapa2_vsp/tablas/resumen_escenarios.csv` | I |
| `etapa2_vsp/graficos/jornadas_{E0,E1,LB,E0_sep,E1_sep,E1_C2,E1_C2_sep}.png` | Histogramas de energía y duración de las jornadas de cada escenario | `data-processed/jornadas_<escenario>.csv` | A |

## Carga reactiva y nivel de batería (Etapa 3)

| Figura | Mensaje | Datos | Sección |
|---|---|---|---|
| `etapa3_carga_reactiva/graficos/ocupacion_E1_soc100.png` ★ | La carga nocturna satura los puestos: casi todos los buses llegan entre 19:00 y 02:00 | `etapa3_carga_reactiva/tablas/ocupacion_E1_soc100.csv` | P (hallazgo central) / I |
| `etapa3_carga_reactiva/graficos/ocupacion_E0_soc100.png` | Lo mismo en el caso base | `etapa3_carga_reactiva/tablas/ocupacion_E0_soc100.csv` | I |
| `etapa3_carga_reactiva/graficos/soc_ejemplo_E1_soc100.png` | Cómo se ve la batería de una jornada con y sin recarga, y una que se parte | `etapa3_carga_reactiva/tablas/jornadas_E1_soc100.csv` | P (explicar la política) / I |
| `etapa3_carga_reactiva/graficos/ocupacion_*_sep_soc100.png`, `ocupacion_E1_C2*_soc100.png`, `soc_ejemplo_*` (otros escenarios) | Evidencia de los escenarios con terminales separados y de las variantes C2 (infactibles sin unir) | `etapa3_carga_reactiva/tablas/ocupacion_<esc>_soc100.csv` | A |
| `etapa3_carga_reactiva/barrido/graficos/barrido_costo_total.png` ★ | 100% con reservas es el menor costo factible; bajar el nivel se paga con flota | `etapa3_carga_reactiva/barrido/tablas/barrido_niveles.csv` | P (por qué 100%) / I |
| `etapa3_carga_reactiva/barrido/graficos/barrido_ciclos_y_cota.png` | Ningún nivel cumple el ciclo sin reservas; la cota LP muestra que al 100% solo cabe el 84% de la energía nocturna | `etapa3_carga_reactiva/barrido/tablas/barrido_niveles.csv` | I |
| `etapa3_carga_reactiva/barrido/graficos/barrido_robustez.png` | E0 y E1 eligen el mismo nivel: la decisión es robusta | `etapa3_carga_reactiva/barrido/tablas/decision_barrido.csv` | A |

## MILP de carga, instancia reducida (Etapa 4)

| Figura | Mensaje | Datos | Sección |
|---|---|---|---|
| `etapa4_milp_carga/graficos/ocupacion_reactiva_vs_milp_N200.png` ★ | El MILP usa los puestos que la reactiva deja ociosos por la tarde y baja el costo de la carga | `etapa4_milp_carga/tablas/ocupacion_N200.csv` | P (resultado del MILP) / I |
| `etapa4_milp_carga/graficos/costo_reactiva_vs_milp.png` ★ | El ahorro viene de las reservas, no de la energía (costo por bus, apilado) | `etapa4_milp_carga/tablas/comparacion_reactiva_milp.csv` | P / I |
| `etapa4_milp_carga/graficos/brecha_vs_N.png` ★ | Solo N = 10 se certifica al óptimo; la brecha crece con el tamaño | `etapa4_milp_carga/tablas/tiempos_resolucion.csv` | P (justifica la instancia chica) / I |
| `etapa4_milp_carga/graficos/energia_por_tarifa.png` | La tarifa casi no se mueve: el MILP no gana por cargar en valle a escala | `etapa4_milp_carga/tablas/energia_por_tarifa.csv` | I |
| `etapa4_milp_carga/graficos/ocupacion_reactiva_vs_milp_N{10,30,50,100,400}.png` | Misma comparación en las demás instancias | `etapa4_milp_carga/tablas/ocupacion_N<n>.csv` | A |

## KPIs de la escalera (Bloque F)

| Figura | Mensaje | Datos | Sección |
|---|---|---|---|
| `etapa5_kpis_comparacion/graficos/costo_desglose_E0_E1.png` ★ | El interlining baja el costo total 5,2%; la flota es ~70% del costo, la energía solo 8% | `etapa5_kpis_comparacion/tablas/desglose_costo.csv` | P (resultados) / I |
| `etapa5_kpis_comparacion/graficos/flota_de_donde_viene.png` ★ | La batería agrega 5.136 buses a E1; el clustering, solo 311 sobre la cota LB (precio de la descomposición) | `etapa5_kpis_comparacion/tablas/precio_descomposicion.csv` | P (hallazgo central) / I |
| `etapa5_kpis_comparacion/graficos/uso_electroterminales.png` | Tres de cuatro electroterminales tienen todos sus puestos ocupados 71-79% del día | `etapa5_kpis_comparacion/tablas/uso_electroterminales.csv` | I |
