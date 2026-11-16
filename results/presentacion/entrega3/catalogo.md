# Gráficos de la presentación final

Generados por `scripts/18-graficos_presentacion.py`, que solo lee lo guardado en `results/` y `data-processed/`. Cada
gráfico está en PNG (200 dpi, 16:9) y PDF, con el CSV de sus datos al lado. Los mensajes son los de
`docs/contexto_entrega_3/03_resultados_y_mensajes.md`, sección 1: 1 aplicable, 2 casi óptimo, 3 ahorra 24,3%,
4 los puestos son el cuello de botella, 5 reproducible.

| Archivo | Parte | Título (mensaje) | Qué muestra | Mensaje que apoya |
|---|---|---|---|---|
| `26_datos_de_costo` | Datos | Datos de costo y operación que usa el modelo | Tabla de costos y parámetros del modelo. | Contexto (datos); responde el feedback de mostrar los costos |
| `01_cadena_completa` | Implementación | La solución es una cadena: cada etapa usa lo que dejó la anterior | Diagrama de las etapas: qué decide cada una, qué sale, con qué se resuelve y cuánto tarda. | 5 (reproducible); responde el feedback de explicar la implementación |
| `02_etapa1_rutas_por_terminal` | Implementación | Etapa 1: cada ruta se asigna al electroterminal más cercano a sus terminales | Rutas, viajes por día y puestos de carga de cada electroterminal tras la Etapa 1. | Contexto de la metodología |
| `03_etapa2_jornada_de_un_bus` | Implementación | Etapa 2 arma la jornada de cada bus sin mirar la batería | Línea de tiempo de una jornada real (viajes, traslados, esperas) y la energía que consume frente a la batería. | Contexto de la metodología (por qué hace falta la Etapa 3) |
| `04_etapa3_corte_y_reencadenamiento` | Implementación | Etapa 3 corta la jornada donde se acaba la batería y une cada tramo con otros | La jornada del gráfico 03 antes (Etapa 2) y después de cortarla y re-encadenar sus tramos (Etapa 3). | Contexto de la metodología |
| `04b_caso_base_vs_propuesta_un_bus` | Implementación | Caso base: la jornada se parte y un bus queda detenido. Propuesta: el bus carga y sigue | La misma jornada en el caso base con interlining (se parte) y en la Propuesta completa (dos tramos con carga). | Contexto: diferencia entre caso base y propuesta |
| `05_etapa4_pasos` | Implementación | Etapa 4 en cinco pasos: de un modelo relajado a un plan de carga validado | Diagrama de los pasos de la Etapa 4, con qué entra, cómo se resuelve y qué sale en cada uno. | 1 (aplicable) y 2 (casi óptimo) |
| `06_por_que_plan_exacto` | Implementación | El modelo relajado llega a 124 buses cargando con 100 puestos; el plan final nunca pasa de 100 | Buses cargando por minuto en La Reina: modelo relajado contra plan final, con la línea de puestos. | 1 (aplicable); responde la crítica principal de la entrega 2 |
| `07_tamano_y_tiempo` | Implementación | Antes: 160.720 binarias y 1 hora sin terminar. Ahora: 563 binarias y 3,5 minutos | Binarias y tiempo de cómputo del modelo de la entrega 2 contra el plan exacto en La Reina; los demás terminales al pie. | 5 (reproducible, en minutos) |
| `08_validacion` | Implementación | El plan de carga pasa los 6 controles del validador independiente en los 4 electroterminales | Lista de chequeo: los 6 controles del validador con su resultado por electroterminal. | 1 (aplicable) |
| `09_supuestos` | Implementación | Supuestos y simplificaciones, y qué efecto tienen | Tabla de supuestos con su justificación y su efecto. | Responde el feedback de declarar supuestos y simplificaciones |
| `10_bus_de_reserva` | Implementación | Un bus de reserva sale en lugar del bus que todavía no termina de cargar | Línea de tiempo de una ventana real con reserva: el bus llega, espera, carga y la reserva sale en su lugar. | Explica qué es una reserva (mensaje 4) |
| `11_plan_de_puestos` | Implementación | Plan de carga: cada puesto atiende a un bus a la vez y en la tarifa cara quedan libres | Gantt de 15 puestos de La Reina durante 6 horas: qué bus carga en cada puesto y cuándo. | 1 (aplicable): el plan es concreto, bus por bus |
| `12_costo_red` | Resultados | La Propuesta completa baja el costo diario de la red 24,3% frente al caso base con interlining | Costo diario de la red por escenario, con el % contra el caso base con interlining. | 3 (ahorra 24,3%) |
| `13_costo_por_componente` | Resultados | El ahorro viene de la flota y de los buses de reserva; la energía cambia poco | Barras apiladas del costo de la red por componente y escenario. | 3 (de dónde sale el ahorro) |
| `14_de_donde_viene_el_ahorro` | Resultados | Dos tercios del ahorro vienen de la Etapa 3 (menos buses) y un tercio de la Etapa 4 (menos reservas) | Cascada horizontal: cambio de costo por componente en la Etapa 3 y en la Etapa 4, acumulado hasta el ahorro total. | 3 (ahorra 24,3%) y qué etapa lo explica |
| `15_buses_necesarios` | Resultados | La propuesta necesita 3.507 buses menos: 8.995 en vez de 12.502 | Buses que operan y buses de reserva por escenario, red completa. | 3 (ahorro: 3.507 buses menos) |
| `16_ahorro_por_terminal` | Resultados | Todos los electroterminales ahorran entre 21% y 25% | Ahorro en % y en USD/día de cada electroterminal y de la red. | 3 (el ahorro es parejo, no depende de un terminal) |
| `17_distancia_al_optimo` | Resultados | El plan de carga queda a 1,5% del óptimo en la red, y a 2,0% como máximo por terminal | Distancia del plan a la cota inferior por terminal y en la red, con el costo del plan y de la cota. | 2 (casi óptimo) |
| `18_reservas_por_tipo` | Resultados | 77% de los buses de reserva existen por falta de puestos de carga | Reservas inevitables y por falta de puestos, por terminal. | 4 (el cuello de botella son los puestos) |
| `19_puestos_llenos_y_tarifa` | Resultados | Con los puestos llenos casi todo el día, la carga no puede irse al horario barato | Puestos ocupados durante el día en Los Espinos + Santa Rosa (congestionado) y Vespucio Norte (holgado), con la tarifa de fondo. | 4 (el cuello de botella son los puestos, no la tarifa) |
| `20_energia_en_horario_barato` | Resultados | Solo Vespucio Norte, con puestos de sobra, lleva la carga al horario barato | % de la energía en horario barato por escenario y terminal. | 4 (la tarifa solo se aprovecha donde sobran puestos) |
| `21_uso_de_la_flota` | Resultados | Cada bus trabaja más: la utilización sube de 28% a 39% | Utilización de los buses y % de km sin pasajeros por escenario. | 3 (por qué hacen falta menos buses) |
| `22_tabla_kpis` | Resultados | Indicadores de la red completa por escenario | Tabla de KPIs de la red completa por escenario. | 3 (resumen de resultados) |
| `23a_sensibilidad_bateria_caso_base` | Resultados | Caso base: cargar hasta 100% es lo más barato; con un tope menor se parten más jornadas | Costo del caso base de la red según el nivel de carga de la batería (sensibilidad de la entrega 2). | Sensibilidad ya corrida (justifica el caso base) |
| `23b_sensibilidad_traslados` | Resultados | Los traslados en línea recta × 1,3 son un supuesto de bajo impacto: entre 1,2 y 1,5 la flota cambia ±1% | Cambio en la flota de la Etapa 2 al variar el factor de desvío, el tiempo entre viajes y el radio de interlining. | Sensibilidad ya corrida; responde la pregunta del feedback sobre el deadhead |
| `25_buses_etapa3` | Resultados | Re-encadenar los tramos cubre la red con 7.356 buses, casi los mismos que si no hubiera batería | Buses que operan: jornadas sin batería, caso base con interlining, cada tramo un bus y Etapa 3. | 3 (de dónde sale el ahorro de flota) |
| `27_carga_sobre_capacidad` | Resultados | Tres de los cuatro electroterminales usan más del 80% de su capacidad de carga del día | Energía del día sobre la capacidad de los puestos en 24 h, por terminal. | 4 (el cuello de botella son los puestos) |
| `24_cargas_divididas` | Limitaciones | Limitación: 22% de las cargas se hacen en dos o más tramos, y la mitad de las pausas dura 5 minutos o menos | Ventanas cargadas en dos o más tramos por terminal y duración de las pausas entre tramos. | Limitación declarada (análisis crítico) |

## Propuesta de láminas

Una fila por lámina: 10 láminas de implementación y resultados, de un minuto cada una. Si falta tiempo, las que primero
se pueden pasar a respaldo son "Caso base frente a la propuesta" y "Supuestos" (si los supuestos ya se dicen en la
metodología). Lo que no está en la columna principal queda para preguntas o para el informe.

| Lámina | Gráfico principal | Apoyo o respaldo |
|---|---|---|
| Metodología: la cadena | `01_cadena_completa` | `03_etapa2_jornada_de_un_bus`, `04_etapa3_corte_y_reencadenamiento` |
| Caso base frente a la propuesta | `04b_caso_base_vs_propuesta_un_bus` | `23a_sensibilidad_bateria_caso_base` |
| Implementación de la Etapa 4 | `05_etapa4_pasos` | `07_tamano_y_tiempo` |
| Por qué el plan es aplicable | `06_por_que_plan_exacto` | `11_plan_de_puestos`, `08_validacion` |
| Supuestos | `09_supuestos` | `23b_sensibilidad_traslados`, `26_datos_de_costo` |
| Resultados: costo y buses | `12_costo_red` | `15_buses_necesarios`, `22_tabla_kpis` |
| Resultados: de dónde sale el ahorro | `14_de_donde_viene_el_ahorro` | `13_costo_por_componente`, `25_buses_etapa3`, `16_ahorro_por_terminal` |
| Resultados: calidad de la solución | `17_distancia_al_optimo` | `08_validacion` |
| Hallazgo: los puestos son el cuello de botella | `18_reservas_por_tipo` | `19_puestos_llenos_y_tarifa`, `27_carga_sobre_capacidad`, `20_energia_en_horario_barato`, `10_bus_de_reserva` |
| Análisis crítico | `24_cargas_divididas` | `21_uso_de_la_flota` |

## Lo que no se pudo hacer sin correr algo nuevo

- Mapa de la Etapa 1: necesita `data-alumnos/chile.gpkg`, que no está en el repositorio. Se puede usar el de la entrega 2,
  `results/etapa1_clustering/mapas/mapa_c1b.png`, que sigue vigente (la Etapa 1 no cambió).
- Sensibilidades del plan exacto (holgura, largo del bloque): no se corrieron, por decisión (J8 y J9 en
  `docs/contexto_entrega_3/02_decisiones.md`). Las sensibilidades de los gráficos 23a y 23b son de la entrega 2 y siguen
  vigentes porque el caso base y la Etapa 2 no cambiaron.
