# Planificación de la operación de buses eléctricos — RED Metropolitana de Movilidad

Proyecto Capstone, curso ICS2122 (Taller de Investigación Operativa), 2do semestre 2026.
Grupo 24. Profesor: Agustín Chiu.

## El problema

La RED Metropolitana de Movilidad de Santiago opera la flota de buses eléctricos más grande fuera de
China. A diferencia de la flota diésel, los buses eléctricos tienen autonomía limitada e
infraestructura de carga escasa, lo que convierte la planificación diaria en un problema conjunto de
transporte y energía: un **Electric Vehicle Scheduling Problem (E-VSP)**. Hay que decidir, para un día
laboral representativo, qué bus cubre cada viaje programado, cuándo y dónde recarga, y minimizar el
costo total (flota + desplazamientos sin pasajeros + espera + energía).

El detalle completo del problema, los datos y el feedback de la Entrega 1 está en
[`docs/context/00_contexto_entrega1.md`](docs/context/00_contexto_entrega1.md).

## Metodología

Descomposición jerárquica por tipo de decisión, en 4 etapas — ver el diagnóstico completo y la
formulación matemática de cada etapa en
[`docs/Propuesta_metodologia_reunion.md`](docs/Propuesta_metodologia_reunion.md):

```
Etapa 0            Etapa 1                 Etapa 2                    Etapa 3                 Etapa 4
Preproceso   →   Clustering de      →   Asignación de buses   →   Inserción de       →   Programación de carga
(expediciones,   RUTAS a electro-       por cluster (VSP en        recargas por           por electroterminal
terminales,      terminales             red espacio-tiempo,        jornada (DP/MILP       (MILP con índice temporal,
matriz deadhead) (MILP asignación)      LP entera, exacto)         pequeño, reparación)   tarifas horarias, capacidad)
```

## Estado actual (30/09/2026)

| Etapa | Estado |
|---|---|
| 0 — Preprocesamiento | ✅ Vigente |
| 1 — Clustering de rutas a electroterminales | ✅ Vigente (3 estrategias: C1a, C1b, C2) |
| 2 — Asignación de buses (VSP) | ⏸️ Código existe y funciona, pausado hasta validar supuestos con el profesor |
| 3 — Inserción de recargas | No iniciada |
| 4 — Programación de carga | No iniciada |

Detalle completo, cifras y bitácora fechada: [`docs/context/01_metodologia_y_avance.md`](docs/context/01_metodologia_y_avance.md).
Preguntas abiertas para el profesor/ayudante: [`docs/context/02_pendientes_profesor.md`](docs/context/02_pendientes_profesor.md)
y [`docs/context/04_preguntas_reunion.md`](docs/context/04_preguntas_reunion.md).

## Cómo correr el pipeline

Requiere Python 3 con `pandas numpy scipy matplotlib tabulate gurobipy geopandas shapely` y una
licencia Gurobi activa (académica, gratuita en [gurobi.com](https://www.gurobi.com)). Detalle completo,
checkpoints y troubleshooting: [`docs/context/03_guia_pruebas.md`](docs/context/03_guia_pruebas.md).

```bash
# Etapa 0 — preprocesamiento (expande GTFS por frecuencia a expediciones reales)
python scripts/3-preprocesamiento_expediciones.py

# Etapa 1 — clustering de rutas a electroterminales
python scripts/4-clustering_c1.py          # C1a (centroide) y C1b (terminales reales)
python scripts/5-clustering_c2.py          # C2: MILP con capacidad, dos supuestos de carga
python scripts/8-clustering_comparacion.py # comparación, tabla ancha y mapas
```

Tiempo total: ~1,5 minutos. Los `data-filtrado/*.csv` ya vienen en el repo (no hace falta
`data-alumnos/` para correr desde la Etapa 0 en adelante).

## Estructura del repositorio

Mapa completo y actualizado: [`docs/Estructura_carpeta_proyecto.md`](docs/Estructura_carpeta_proyecto.md).
Resumen:

- **`data-alumnos/`** — datos crudos entregados por el curso (GTFS, parámetros, `chile.gpkg`).
- **`data-filtrado/`** — salida del filtrado GTFS→buses→día laboral (`scripts/1-`, `2-`).
- **`data-processed/`** — expediciones, terminales y asignaciones de clustering (`scripts/3-` a `8-`).
- **`scripts/`** — pipeline numerado por etapa, más `scripts/common/` (parámetros, geometría, tiempo,
  clustering — utilidades compartidas, no lógica de una etapa específica).
- **`results/`** — un reporte, tablas y gráficos por etapa corrida, en subcarpetas `etapaN_*/`.
- **`docs/`** — Informe 1, lineamientos del curso, metodología, y `docs/context/` (documentación viva
  del avance).

## Datos

Tres fuentes: GTFS de RED (rutas, viajes, horarios, paraderos), un GeoPackage de OpenStreetMap
(`chile.gpkg`, red vial de Chile) y CSVs de parámetros del curso (electroterminales, cargadores,
tarifas, características del bus). Decisiones de filtrado documentadas en
[`docs/decisiones_datos.md`](docs/decisiones_datos.md).

Cifras clave del día laboral modelado: 417 rutas, 64.502 expediciones, 641 paraderos terminales,
5 electroterminales (700 puestos de carga en total), flota BYD K9 (350 kWh, 315 kWh útiles,
1,4 kWh/km).
