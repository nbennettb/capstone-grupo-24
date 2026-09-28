# Contexto — Informe 1 (congelado)

> **Este documento no se vuelve a editar.** Es una fotografía de lo que el grupo entregó en el Informe 1 y de todo el feedback recibido hasta el 28/09/2026. Sirve para que cualquier persona (o sesión de IA) que se sume al proyecto entienda el punto de partida sin tener que leer el `.tex` completo ni el hilo de conversación original.
>
> Para el estado **actual** del proyecto (qué se ha hecho desde entonces), ver [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md), que es un documento vivo.

---

## 1. El proyecto

**Curso:** ICS2122 — Taller de Investigación Operativa (Capstone), 2do semestre 2026.
**Grupo 24. Profesor:** Agustín Chiu.
**Integrantes:** Nicolás Bennett, Antonio De Frutos, Claudio Hasbún, Agustín Irarrázaval, Joaquín Jiménez, Alonso Muelas.

**Tema:** Planificación de la operación de los buses eléctricos en la Red Metropolitana de Movilidad (RED) de Santiago.

La Red Metropolitana de Movilidad de Santiago es uno de los sistemas de transporte público más grandes de América Latina y cuenta con la flota de buses eléctricos más grande fuera de China. La incorporación de buses eléctricos introduce restricciones operacionales nuevas (autonomía limitada, necesidad de recarga en infraestructura escasa) que no existían con la flota diésel, por lo que la planificación diaria pasa a ser un problema conjunto de transporte y energía.

## 2. El problema

Se formula como un **Electric Vehicle Scheduling Problem (E-VSP)**: asignar un conjunto de viajes programados (definidos por paradero/hora de inicio y término) a una flota de buses eléctricos homogénea, de modo que:

- Cada viaje se cubra exactamente una vez.
- La secuencia de actividades de cada bus sea una cadena físicamente factible en el tiempo (incluyendo los desplazamientos sin pasajeros necesarios para pasar de un viaje al siguiente).
- La batería se mantenga siempre entre un SOC mínimo y máximo, obligando a recargar en electroterminales antes de quedar en nivel crítico.
- La capacidad de carga simultánea de cada electroterminal no se exceda.

**Tres decisiones centrales:** (1) asignación de viajes a buses, (2) desplazamientos sin pasajeros (*pullout*: electroterminal → primer viaje; *pullin*: último viaje → electroterminal; *deadheading*: entre viajes no contiguos), (3) decisiones de recarga (cuándo, dónde, por cuánto tiempo).

**Objetivo:** minimizar el costo total de operación = costo fijo por bus usado + costo variable de desplazamientos sin pasajeros + costo de tiempos de espera + costo energético de las recargas + costo fijo por evento de carga.

**Entregable esperado:** para un día laboral representativo, (a) número mínimo de buses necesarios, (b) jornada operacional completa de cada bus (CSV), (c) itinerario de recarga de cada bus (CSV), (d) desglose del costo total en sus componentes.

## 3. Datos disponibles

Tres fuentes:
1. **GTFS de RED** (vigente jul-dic 2026): rutas, viajes programados, horarios, paraderos, trazados geométricos.
2. **GeoPackage de OpenStreetMap** (`chile.gpkg`, red vial de Chile) — usado potencialmente para distancias sin pasajeros más realistas.
3. **CSVs de parámetros del proyecto**: ubicación/capacidad de los 5 electroterminales, potencia de cargadores, precios de electricidad por bloque horario, características del bus eléctrico, costos de operación.

### Decisiones de filtrado (ver `docs/decisiones_datos.md` para el detalle completo)
- Se excluyen del GTFS las rutas de Metro (L1-L6), Metrotren (MTN, MTR) y Bus Aeropuerto (BA); solo queda la red de buses RED.
- El feed distingue tipos de día (L=laboral, S=sábado, D=domingo, más variantes F/LJ/V). **Se trabaja únicamente con el día tipo L (laboral, lunes-viernes)**, por ser el de mayor exigencia operacional.
- Pipeline reproducible: `scripts/1-filtro_datos_buses.py` (filtra Metro → bus) → `scripts/2-filtro_tipo_dia.py` (filtra a día L). Output en `data-filtrado/`, separador `;` (por configuración regional de Excel en Chile).
- Los viajes GTFS están definidos por **frecuencias** (`frequencies.txt`), no por horarios fijos: hay que expandir cada patrón por su `headway_secs` para obtener las salidas reales del día ("expediciones").

### Cifras clave (día laboral, red de buses ya filtrada)
| Indicador | Valor |
|---|---|
| Rutas | 417 (300 con ida y regreso identificables) |
| Trazados geométricos | 839 |
| Paraderos | 12.132 |
| Viajes (patrones GTFS) | 6.620 |
| **Expediciones reales** (viajes expandidos por frecuencia) | **64.502** |
| Buses circulando simultáneamente, peak mañana (8:00) | 6.601 |
| Buses circulando simultáneamente, peak tarde (18:00) | 6.523 |

### Flota e infraestructura de carga
- **Un solo modelo de bus:** BYD K9. Batería 350 kWh, autonomía máxima 250 km, potencia de carga 180 kW, SOC entre 10% y 100%, carga completa ~105 min.
- Batería útil (90% del rango): 315 kWh ⇒ autonomía real ≈ 225 km (consumo 1,4 kWh/km).
- **5 electroterminales**, capacidad total **700 espacios simultáneos**: Vespucio Norte (150), El Conquistador (180), Los Espinos (120), La Reina (100), Santa Rosa (150). Los Espinos y Santa Rosa están geográficamente muy cerca (posible fusión a evaluar).
- **Tamaño de flota:** en el Informe 1 se trabajó con el supuesto de **flota irrestricta**. *(Nota importante: el archivo `data-alumnos/parameters.csv` trae un valor `fleet_size = 1200`, que en un inicio del curso reflejaba una restricción real; el profesor posteriormente aclaró explícitamente que la flota debe tratarse como irrestricta, por lo que ese valor quedó obsoleto. Ver seguimiento de esta inconsistencia en `01_metodologia_y_avance.md` / `02_pendientes_profesor.md`.)*

### Costos y tarifas
| Costo | Valor |
|---|---|
| Fijo por uso de bus | 250 USD |
| Por minuto de espera | 0,03 USD/min |
| Por km recorrido | 0,5 USD/km |
| Fijo por evento de recarga | 5 USD |

Tarifa eléctrica por bloque horario: P1 (0-8h) 0,10 USD/kWh — valle; P2 (8-14h) 0,15; **P3 (14-17h) 0,22 — peak**; P4 (17-19h) 0,15; **P5 (19-22h) 0,22 — peak**; P6 (22-24h) 0,11. Los peaks tarifarios coinciden parcialmente con los peaks de demanda.

### Datos no disponibles (deben aproximarse)
- Duración de viajes y distancias de deadheading: velocidad promedio constante, sin congestión ni topografía.
- Turnos de conductores: fuera de alcance (se asume conductor siempre disponible).
- Demanda real de pasajeros: se usa la oferta programada (expediciones) como demanda a cumplir.
- No existe `block_id` de GTFS: la asignación de viajes a buses se construye desde cero.
- No hay distancias/tiempos de deadheading, pullin, pullout precalculados: se calculan (en el Informe 1, desde OSM; en la metodología nueva, con distancia euclidiana × factor de desvío calibrable, ver `Propuesta_metodologia_reunion.md`).
- Energía por viaje: se deriva multiplicando distancia × 1,4 kWh/km.

## 4. KPIs definidos en el Informe 1
1. **Número total de buses usados.**
2. **Costo energético promedio** (costo total energía / kWh totales cargados) — mide si se carga en bloques baratos o caros.
3. **Proporción de deadheading/pullin/pullout** (km sin pasajeros / km totales) — mide eficiencia geográfica de la asignación.
4. **Utilización por bus** (horas con pasajeros / horas totales del turno).

*(Estos KPIs se revisan y amplían en la metodología nueva — ver `Propuesta_metodologia_reunion.md` §7.)*

## 5. Metodologías discutidas en el Informe 1

Se identificaron tres alternativas a partir de la revisión bibliográfica (Alvo et al. 2021; Perumal et al. 2022; Picarelli 2020; van Kooten Niekerk et al. 2017; Zhang et al. 2024):

1. **ALNS (Adaptive Large Neighborhood Search):** metaheurística de destrucción/reparación sobre una solución inicial factible. Buena escalabilidad, no garantiza optimalidad. Validada en problemas similares por Wang et al. (2024) y Zhou et al. (2024).
2. **Set Partitioning + Generación de Columnas + Cortes de Benders:** problema maestro que selecciona jornadas factibles (columnas), generadas dinámicamente, con un subproblema de Benders que verifica factibilidad de carga conjunta. Evita un MILP monolítico gigante, pero de implementación compleja (coordinar maestro + generación de columnas + cortes).
3. **Descomposición espaciotemporal** *(la seleccionada en el Informe 1)*: Fase 1 — asignación espacial de viajes a electroterminales (LP de transporte). Fase 2 — descomposición temporal en ventanas superpuestas de 3 horas con horizonte rodante (se fija la primera hora, las siguientes dos se reoptimizan), resolviendo cada ventana como un E-VSP pequeño (MILP directo o SP+GC en ventanas complejas).

**Esta tercera metodología (descomposición espaciotemporal con horizonte rodante) fue la propuesta original del Informe 1**, pero fue diagnosticada como demasiado compleja para implementar en el plazo disponible y reemplazada el 28/09/2026 — ver `Propuesta_metodologia_reunion.md` para el diagnóstico completo y la metodología nueva.

## 6. Feedback recibido

- **Presentación 1:** los profesores/ayudantes advirtieron que la propuesta (descomposición espaciotemporal con horizonte rodante) era **probablemente demasiado compleja** para implementar en código y llegar a resultados concretos en el plazo del curso. No se recibió una sugerencia explícita de hacia dónde simplificar.
- **Comentario escrito del profesor en el PDF del Informe 1, punto 3.3.1** (Fase 1: Asignación Espacial): *"Revisar en profundidad estrategias para clusterizar."*
- **Aclaración posterior del profesor (verbal, antes del 28/09):** la flota de buses es **irrestricta** (no hay un límite de 1200 buses como sugería `parameters.csv`).

## 7. Estructura de carpetas del proyecto (al cierre del Informe 1)

Ver el detalle completo en [`docs/Estructura_carpeta_proyecto.md`](../Estructura_carpeta_proyecto.md). Resumen de las carpetas relevantes para retomar el trabajo:
- `data-alumnos/`: datos crudos entregados por el curso (GTFS, CSVs de parámetros, `chile.gpkg`).
- `data-filtrado/`: salida del pipeline de filtrado (scripts 1 y 2), separador `;`.
- `scripts/`: pipeline de datos (`1-filtro_datos_buses.py`, `2-filtro_tipo_dia.py`).
- `docs/Informe 1/`: fuente LaTeX completa del Informe 1 (capítulos, figuras, bibliografía).
- `docs/`: PDF del Informe 1, lineamientos de las entregas, presentación 1, y (desde el 28/09) la documentación de contexto y la metodología nueva.
- `archivos_analisis_datos/`: gráficos y tablas Excel usados en el análisis exploratorio y en la presentación 1.

## 8. Cómo continúa la historia

El 28/09/2026 el grupo se reunió para resolver el feedback de complejidad. El resultado de esa sesión de trabajo es [`docs/Propuesta_metodologia_reunion.md`](../Propuesta_metodologia_reunion.md): un diagnóstico crítico de la metodología del Informe 1 (con datos reales medidos, no solo argumentos) y una metodología nueva —descomposición **jerárquica por tipo de decisión** en 4 etapas— que reemplaza la descomposición espaciotemporal. Esa propuesta fue **aprobada por el grupo sin cambios** en la reunión presencial del mismo día.

Para el estado de implementación de esa metodología nueva (qué etapas están hechas, resultados obtenidos, próximos pasos), ver el documento vivo [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md).
