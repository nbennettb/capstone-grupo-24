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

Descomposición jerárquica por tipo de decisión, en 4 etapas. Formulación, supuestos y justificación
completos en [`docs/context/01_metodologia.md`](docs/context/01_metodologia.md):

```
Etapa 0            Etapa 1                 Etapa 2                    Etapa 3                 Etapa 4
Preproceso   →   Clustering de      →   Asignación de buses   →   Inserción de       →   Programación de carga
(expediciones,   RUTAS a electro-       por cluster (VSP en        recargas por           por electroterminal
terminales,      terminales             red espacio-tiempo,        jornada (simulador     (MILP con índice temporal,
tablas por ruta) (heurística + MILP)    LP entera, exacto)         reactivo)              tarifas horarias, capacidad)
```

**Supuestos centrales** (con su origen en
[`docs/context/02_supuestos_y_decisiones.md`](docs/context/02_supuestos_y_decisiones.md)):
- **Ciclo diario:** todo bus empieza y termina el día con el mismo nivel de batería. Nivel base 100%
  (máximo de los datos del curso), con barrido 100-50%; el ciclo se cumple con buses de reserva. El supuesto
  de partir al 100% sin recuperar la batería fue descartado.
- Cada bus **vuelve a su propio electroterminal**. Los puestos limitan solo la carga simultánea;
  estacionar no consume puesto y se puede cargar las 24 horas.
- Flota irrestricta.
- Los Espinos y Santa Rosa (a 1,1 km) se tratan como un solo electroterminal en todos los escenarios.
- Caso base: operación por línea (sin interlining) con carga reactiva.

## Estado

| Etapa | Estado |
|---|---|
| 0 — Preprocesamiento | ✅ Hecha y vigente |
| 1 — Clustering de rutas a electroterminales | ✅ Hecha (C1, C2 como propuesta) |
| 2 — Asignación de buses (VSP) | ✅ Hecha (escalera E0 / E1 / LB y evidencias) |
| 3 — Inserción de recargas (simulador reactivo y barrido de niveles) | ✅ Hecha; nivel base 100% con buses de reserva |
| 4 — Programación de carga (MILP, instancia chica) | ⏳ Pendiente |

Caso base factible (USD/día): E0 3.958.063 · E1 3.751.250.

Qué falta, en qué orden y por qué: [`docs/context/05_plan_entrega2.md`](docs/context/05_plan_entrega2.md).
Historial de lo hecho y decidido: [`docs/context/04_bitacora.md`](docs/context/04_bitacora.md).

## Cómo correr lo que existe

Requiere Python 3 con `pandas numpy scipy matplotlib tabulate gurobipy geopandas shapely` y una
licencia Gurobi activa (académica, gratuita en [gurobi.com](https://www.gurobi.com)). Detalle,
checkpoints y troubleshooting: [`docs/context/03_guia_pruebas.md`](docs/context/03_guia_pruebas.md).

```bash
# Etapa 0 — preprocesamiento (expande el GTFS por frecuencia a expediciones reales)
python scripts/3-preprocesamiento_expediciones.py

# Etapa 1 — clustering de rutas a electroterminales
python scripts/4-clustering_c1.py          # C1a (centroide) y C1b (terminales reales)
python scripts/5-clustering_c2.py          # C2: MILP con capacidad
python scripts/8-clustering_comparacion.py # comparación, tabla ancha y mapas
```

Los `data-filtrado/*.csv` ya vienen en el repo (no hace falta `data-alumnos/` para correr desde la
Etapa 0 en adelante). Los mapas necesitan `data-alumnos/chile.gpkg`, que no viaja en el repo por
tamaño.

> Nota: `5-clustering_c2.py` y `8-clustering_comparacion.py` todavía describen el supuesto anterior
> (batería al 100%). Se actualizan al ejecutar el Bloque A del plan.

## Estructura del repositorio

Mapa completo: [`docs/Estructura_carpeta_proyecto.md`](docs/Estructura_carpeta_proyecto.md). Resumen:

- **`data-alumnos/`** — datos crudos entregados por el curso (GTFS, parámetros, `chile.gpkg`).
- **`data-filtrado/`** — salida del filtrado GTFS → buses → día laboral (`scripts/1-`, `2-`).
- **`data-processed/`** — expediciones, terminales, tablas por ruta y asignaciones de clustering.
- **`scripts/`** — pipeline numerado por etapa, más `scripts/common/` (parámetros, geometría, tiempo,
  clustering: utilidades compartidas, no lógica de una etapa).
- **`results/`** — reporte, tablas y gráficos por etapa corrida, en subcarpetas `etapaN_*/`.
- **`docs/`** — Informe 1, lineamientos del curso, propuesta de metodología, y `docs/context/`
  (documentación del proyecto, en orden de lectura 00 → 05).

## Datos

Tres fuentes: GTFS de RED (rutas, viajes, horarios, paraderos), un GeoPackage de OpenStreetMap
(`chile.gpkg`, red vial de Chile) y CSVs de parámetros del curso (electroterminales, cargadores,
tarifas, características del bus). Decisiones de filtrado en
[`docs/decisiones_datos.md`](docs/decisiones_datos.md).

Cifras clave del día laboral modelado: 417 rutas, 64.502 expediciones, 641 paraderos terminales,
5 electroterminales (700 puestos de carga en total), flota BYD K9 (350 kWh, 315 kWh utilizables al
100%, 1,4 kWh/km).
