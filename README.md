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

El detalle del problema, los datos y el feedback de la Entrega 1 está en
[`docs/context/00_contexto_entrega1.md`](docs/context/00_contexto_entrega1.md).

## Metodología

Descomposición jerárquica por tipo de decisión: primero la flota, después la carga. Resumen en una página:
[`docs/context/01_como_funciona.md`](docs/context/01_como_funciona.md). Cada decisión con su porqué:
[`docs/context/02_decisiones.md`](docs/context/02_decisiones.md).

```
Etapa 0 Preproceso -> Etapa 1 Rutas -> electroterminal -> Etapa 2 VSP sin batería (jornadas)
   -> Etapa 3 Cortes y re-encadenamiento con recarga -> Etapa 4 Programación de la carga en el patio
Caso base (aparte, no es una etapa): jornadas de la Etapa 2 + carga reactiva + ciclo al 100% con buses de reserva
```

**Supuestos centrales:**
- **Ciclo diario:** todo bus empieza y termina el día al 100%. Lo que la carga no alcanza a reponer a tiempo se cubre con
  buses de reserva.
- Cada bus **vuelve a su propio electroterminal** y carga ahí. Los puestos limitan solo la carga simultánea.
- Flota irrestricta.
- Los Espinos y Santa Rosa (a 1,1 km) son un solo electroterminal.
- Traslados sin pasajeros: línea recta × 1,3 a 20 km/h en todas las etapas.

**Escenarios:**
- caso base: E0 (por línea) y E1 (con interlining), con carga reactiva;
- evaluación: E2-FIFO (Etapa 3 + carga por orden de llegada) y E2 (Etapas 3 + 4).

## Estado

| Etapa | Estado |
|---|---|
| 0 — Preprocesamiento | Hecha (red completa) |
| 1 — Rutas a electroterminales | Hecha (C1; C2 como propuesta) |
| 2 — VSP sin batería | Hecha (E0, E1, LB y evidencias) |
| Caso base | Hecho en la red completa (E0 3.958.063 · E1 3.751.250 USD/día) y filtrable por terminal |
| 3 — Cortes y re-encadenamiento | Implementada; instancia La Reina |
| 4 — Programación de la carga | Modelo agregado y detallado implementados; instancia La Reina |

**Alcance de esta entrega:** las Etapas 3 y 4 se prueban con su caso base en el terminal La Reina completo (100 puestos).
La red completa queda para la entrega final; se corre con el mismo código, terminal por terminal.

## Cómo correr

Requiere Python 3 con `pandas numpy scipy matplotlib tabulate gurobipy psutil geopandas shapely` y una licencia de Gurobi
activa (académica, gratuita en [gurobi.com](https://www.gurobi.com)).

- **Instancia La Reina (caso base, Etapas 3-4, KPIs):** comandos en orden, tiempos, qué debe imprimir cada uno y qué hacer
  si falla en [`docs/context/03_como_correr.md`](docs/context/03_como_correr.md).
- **Etapas 0-2** (ya corridas; sus archivos están en `data-processed/`):

```bash
python scripts/3-preprocesamiento_expediciones.py    # Etapa 0
python scripts/4-clustering_c1.py                    # Etapa 1: C1a y C1 (c1b)
python scripts/5-clustering_c2.py                    # Etapa 1: C2, MILP con capacidad (propuesta)
python scripts/8-clustering_comparacion.py           # Etapa 1: comparación y mapas
python scripts/6-vsp_asignacion_buses.py --modo ruta    --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --etiqueta E0
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --etiqueta E1
python scripts/7-comparar_escenarios.py              # Etapa 2: escalera de escenarios
```

Los `data-filtrado/*.csv` ya vienen en el repo. Los mapas necesitan `data-alumnos/chile.gpkg`, que no viaja en el repo
por su tamaño.

## Estructura del repositorio

Mapa completo: [`docs/Estructura_carpeta_proyecto.md`](docs/Estructura_carpeta_proyecto.md). Resumen:

- **`data-alumnos/`** — datos crudos entregados por el curso (GTFS, parámetros, `chile.gpkg`).
- **`data-filtrado/`** — salida del filtrado GTFS → buses → día laboral (`scripts/1-`, `2-`).
- **`data-processed/`** — expediciones, terminales, tablas por ruta y asignaciones de clustering.
- **`scripts/`** — pipeline numerado por etapa, más `scripts/common/` (parámetros, geometría, tiempo,
  clustering: utilidades compartidas, no lógica de una etapa).
- **`results/`** — reporte, tablas y gráficos: `etapa0_*` a `etapa2_vsp` (red completa), `caso_base/` (red completa)
  e `instancia_LR/` (caso base, Etapas 3-4, KPIs y `resumen_para_analisis.md` del terminal La Reina).
- **`docs/`** — Informe 1, lineamientos del curso, plan de las Etapas 3-4, y `docs/context/` (documentación del
  proyecto, en orden de lectura 00 → 03).

## Datos

Tres fuentes: GTFS de RED (rutas, viajes, horarios, paraderos), un GeoPackage de OpenStreetMap
(`chile.gpkg`, red vial de Chile) y CSVs de parámetros del curso (electroterminales, cargadores,
tarifas, características del bus). Decisiones de datos en
[`docs/context/02_decisiones.md`](docs/context/02_decisiones.md).

Cifras clave del día laboral modelado: 417 rutas, 64.502 expediciones, 641 paraderos terminales,
5 electroterminales (700 puestos de carga en total), flota BYD K9 (350 kWh, 315 kWh utilizables al
100%, 1,4 kWh/km).
