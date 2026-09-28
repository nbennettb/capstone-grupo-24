# Decisiones de filtrado de datos — Buses eléctricos RM (ICS2122)

Pipeline: `scripts/1-filtro_datos_buses.py` → `scripts/2-filtro_tipo_dia.py`
(ambos corren desde cero sobre `data-alumnos/`, generan todo en `data-filtrado/`)

## 1. Archivos excluidos por completo (no se copian a data-filtrado)

| Archivo | Motivo |
|---|---|
| `agency.txt` | Datos de contacto (url, mail) de operadores; no aporta al análisis. |
| `calendar_dates.txt` | Excepciones puntuales por fecha (feriados); trabajamos por tipo de día (service_id), no por fecha exacta. |
| `calendar.txt` | La info (qué días de semana = cada service_id) es necesaria, pero se consulta directo desde `data-alumnos/gtfs/` en el script 2 — no hace falta copiar el archivo. |
| `feed_info.txt` | Metadata del feed (versión, fechas de publicación); no aporta. |
| `levels.txt`, `pathways.txt` | Extensión GTFS para navegación indoor en estaciones grandes; irrelevante para buses. |

## 2. Filtrado a datos de buses (`1-filtro_datos_buses.py`)

**Filas:** se excluyen del universo los route_id de Metro (L1,L2,L3,L4,L4A,L5,L6),
Metrotren (MTN,MTR) y Bus Acercamiento Aeropuerto (BA), y la exclusión se
propaga en cascada: routes → trips (route_id) → stop_times/frequencies
(trip_id) → stops (stop_id usado por buses) → shapes/shape_distances
(shape_id usado por buses).

**Columnas:** el script elimina automáticamente, en cada archivo, las
columnas que quedan 100% vacías o con un único valor constante dentro del
subconjunto de buses (se imprime cuál y por qué al correr el script). No se
hardcodeó una lista fija de columnas a mano — se detectan según los datos
reales de cada corrida. Ejemplos esperados: `route_color`/`route_text_color`
(mismo color en todos los buses), `trip_short_name`/`wheelchair_accessible`/
`bikes_allowed` (propios de Metro), `pickup_type`/`drop_off_type`/`timepoint`
(ídem), `location_type`/`parent_station`/`level_id` en stops (ídem),
`exact_times` en frequencies (siempre 0).

**Columnas protegidas (nunca se eliminan aunque salgan vacías/constantes):**
`block_id` en trips (podría permitir encadenar trips en un mismo vehículo —
relevante para el problema de asignación) y `shape_dist_traveled` en
stop_times (distancia parcial por parada, más precisa que el total de
shape_distances). El script reporta su estado para decidir manualmente si
sirven.

**CSVs ya limpios** (`charger_capacity`, `charging_activities`, `depots`,
`electricity_prices`, `parameters`, `parametros_descripcion`, `vehicles`):
sin contaminación de Metro, no requieren filtro — se copian sin cambios a
`data-filtrado/` para centralizar todos los datos del equipo en una carpeta.

**Conteos:** <completar con el output real del script>

## 3. Filtrado por día tipo (`2-filtro_tipo_dia.py`)

**Decisión:** usar service_id = "L" (laboral, lunes-viernes) como único día
tipo para el Informe 1.

**Justificación:** acota el problema a un tamaño manejable para esta etapa
preliminar. Es el día tipo con mayor volumen de servicio y representa la
operación más exigente en demanda de transporte y energía. Los otros 5
tipos de día (S, D, F, LJ, V) quedan para etapas posteriores si el alcance
del proyecto lo permite.

**Alcance:** solo se filtran por día `trips`, `stop_times` y `frequencies`
(dependen del servicio). `routes_bus`, `stops_bus`, `shapes_bus` y
`shape_distances_bus` NO se filtran por día — son infraestructura física
independiente del día de operación.

**Conteos:** <completar con el output real del script>

## 3.5 Separador de los CSV generados

Todos los archivos escritos en `data-filtrado/` usan `;` como separador de
columnas (no `,`). Motivo: Excel con configuración regional Chile/Latam usa
`,` como separador decimal, por lo que espera `;` como separador de listas
al abrir un CSV — con `,` todo aparecía en una sola columna al doble clic.
Los archivos originales en `data-alumnos/` no se modifican y siguen en `,`.

**Importante para el equipo:** cualquier script nuevo que lea archivos desde
`data-filtrado/` con pandas debe usar `pd.read_csv(path, sep=";")`,
explícitamente — si no, se rompe de la misma forma (todo en una columna).

## 4. Posibles próximos pasos 

4. Expandir los trips a salidas reales (vía headway de frequencies).
5. Mergear tablas de interés (trips + stop_times + frequencies + depots, etc.).
6. Calcular energy_kwh por salida.
7. Definir y calcular KPIs (coordinar con equipo de metodología).