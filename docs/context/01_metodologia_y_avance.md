# Metodología y avance — documento vivo

> **Este documento se edita continuamente.** Cada vez que se corre una etapa nueva se agrega una entrada fechada en la bitácora (§4) — no se borran las entradas anteriores. La "foto actual" (estado por etapa, tabla de resultados) sí se actualiza en su lugar. Si vienes de otra sesión de IA o te acabas de sumar al equipo: lee primero [`00_contexto_entrega1.md`](00_contexto_entrega1.md) (qué se entregó en el Informe 1 y qué feedback se recibió) y luego este documento.
>
> Última edición: **28/09/2026** (Etapa 2 corrida sobre la red completa, modos `ruta` y `libre`).

---

## 1. Qué se decidió en la reunión del 28/09/2026

El grupo se reunió presencialmente para resolver el feedback de "propuesta demasiado compleja" recibido en la presentación 1, y el comentario del profesor sobre revisar estrategias de clustering (Informe 1, punto 3.3.1).

Se preparó un diagnóstico crítico de la metodología del Informe 1 apoyado en un prototipo corrido sobre los datos reales (ver [`Propuesta_metodologia_reunion.md`](../Propuesta_metodologia_reunion.md) para el detalle completo, cifras y formulaciones). Conclusión: la descomposición temporal por horizonte rodante no es necesaria (el VSP completo se resuelve exacto y rápido con la formulación adecuada) y el verdadero cuello de botella es la gestión de energía, no el tamaño de la red.

**Se aprobó, sin cambios, reemplazar la descomposición espaciotemporal del Informe 1 por una descomposición jerárquica por tipo de decisión, en 4 etapas:**

```
Etapa 0            Etapa 1                 Etapa 2                    Etapa 3                 Etapa 4
Preproceso   →   Clustering de      →   Asignación de buses   →   Inserción de       →   Programación de carga
(expediciones,   RUTAS a electro-       por cluster (VSP en        recargas por           por electroterminal
terminales,      terminales             red espacio-tiempo,        jornada (DP/MILP       (MILP con índice temporal,
matriz deadhead) (MILP asignación)      LP entera, exacto)         pequeño, reparación)   tarifas horarias, capacidad)
```

### Parámetros base aprobados (sin cambios respecto a la propuesta)
| Parámetro | Valor | Fuente |
|---|---|---|
| Factor de desvío del deadhead (línea recta → distancia real aproximada) | 1,3 | Supuesto, a calibrar con OSM más adelante |
| Velocidad de deadhead | 20 km/h | Supuesto |
| Layover mínimo entre actividades | 3 min | Supuesto |
| Radio máximo de interlining | 3 km | Supuesto (sparsificación del problema) |
| SOC inicial de los buses | 100% | Supuesto — **ver `02_pendientes_profesor.md`, es el más crítico** |

Estos valores viven en un único lugar del código (`scripts/common/parametros.py`) para que cambiarlos y volver a correr (análisis de sensibilidad) sea trivial.

### Caso base aprobado
"Operación por línea + carga reactiva": cada ruta usa solo sus propios buses (sin interlining), electroterminal base = el más cercano, y la recarga se hace de forma miope (al electroterminal más cercano, al 100%, apenas la batería proyectada no alcanza para el siguiente viaje). Ver `Propuesta_metodologia_reunion.md` §7.

### Alcance de esta ronda de trabajo (28-30/09)
Según la Carta Gantt interna de la propuesta, para el 29-30/09 corresponde: Etapa 0 completa, Etapa 2 (caso base sin clustering + cota inferior con interlining libre), y Etapa 1 (clustering C1 y C2). Las Etapas 3 y 4 (recargas y programación de carga) quedan para los días siguientes (1-2/10).

---

## 2. Estado actual por etapa

| Etapa | Estado | Última actualización | Quién | Script(s) | Resultados |
|---|---|---|---|---|---|
| 0 — Preprocesamiento | `[x]` hecho | 28/09/2026 | Nicolás (sesión IA) | `scripts/3-preprocesamiento_expediciones.py` | `data-processed/expediciones.csv`, `results/03_preprocesamiento/` |
| 1 — Clustering C1 (heurística, más cercano) | `[ ]` pendiente | — | — | `scripts/4-clustering_nearest.py` | `data-processed/rutas_cluster_c1.csv` |
| 1 — Clustering C2 (MILP con capacidad) | `[ ]` pendiente | — | — | `scripts/5-clustering_milp.py` | `data-processed/rutas_cluster_c2.csv` |
| 2 — VSP asignación de buses (caso base + cota inferior, sin batería) | `[~]` hecho para `ruta`/`libre`; falta `cluster` (Fase 6) | 28/09/2026 | Nicolás (sesión IA) | `scripts/6-vsp_asignacion_buses.py` | `data-processed/jornadas_ruta.csv`, `jornadas_libre.csv`, `results/06_vsp/` |
| 3 — Inserción de recargas | Fuera de alcance de esta ronda (próx. semana) | — | — | — | — |
| 4 — Programación de carga | Fuera de alcance de esta ronda (próx. semana) | — | — | — | — |

*(Esta tabla se actualiza a medida que cada script se corre: cambiar `[ ]`→`[~]`→`[x]`, completar fecha/responsable, y agregar una fila a la tabla de resultados de la sección 3.)*

## 3. Tabla de resultados (se llena a medida que se corren los scripts)

| Escenario | Buses | Deadhead total (km) | Costo total (USD) | Espera (h) | % jornadas >315 kWh | Tiempo de cómputo | Archivo |
|---|---|---|---|---|---|---|---|
| **`ruta`** (caso base: cada ruta con sus propios buses) | **8.654** | 207.247 (pullout 98.689 / interlining 10.088 / pullin 98.471) | 2.985.009 | 25.099 | 30,1% | 5 s | `data-processed/jornadas_ruta.csv` |
| **`libre`** (cota inferior C0: interlining sin restricción de electroterminal) | **7.055** (−18,5%) | 146.540 (pullout 66.580 / interlining 15.256 / pullin 64.704) | 2.546.383 (−14,7%) | 20.365 | 39,6% | 39 s | `data-processed/jornadas_libre.csv` |
| Cota inferior teórica (máx. expediciones simultáneas, sin costo de deadhead) | 6.539 | — | — | — | — | — | — |

Gráficos: `results/06_vsp/graficos_ruta.png`, `graficos_libre.png` (distribución de energía y duración por jornada). Cifras completas (desglose de costo por componente): `results/06_vsp/resumen_escenarios.csv`.

**Lectura:** permitir interlining entre rutas cercanas (modo `libre`) reduce la flota necesaria en 18,5% y el costo total en 14,7% frente a que cada ruta use solo sus propios buses. Esto confirma que la Etapa 1 (clustering) tiene margen real donde jugar: el "precio del clustering" de cada estrategia (C1, C2) se mide como cuánto se acerca a este resultado `libre` sin su costo de coordinación entre las 417 rutas. **Advertencia:** ~30-40% de las jornadas superan la batería útil (315 kWh) — la Etapa 3 (inserción de recargas) es indispensable, no un detalle menor; con el supuesto de SOC inicial 100% la mayoría debería resolverse con una sola recarga (ver prototipo exploratorio del 28/09 en `Propuesta_metodologia_reunion.md`), pero esto se valida recién cuando se implemente esa etapa.

## 4. Bitácora

### 28/09/2026 — Reunión y definición de metodología
- Diagnóstico crítico de la metodología del Informe 1 + prototipo exploratorio sobre datos reales (VSP completo en red espacio-tiempo, sin pullout/pullin): caso base 8.654 buses, interlining libre 7.055 buses, cota inferior teórica 6.539.
- Reunión presencial: metodología jerárquica de 4 etapas aprobada sin cambios.
- Se inicializa el repositorio Git, se crea esta documentación de contexto, y se planifica la implementación de las Etapas 0-2.

### 28/09/2026 — Etapa 0 (preprocesamiento) corrida sobre la red completa
- `scripts/3-preprocesamiento_expediciones.py` probado primero en checkpoint chico (ruta 101: 171 expediciones, energía y horarios verificados a mano) y luego sobre la red completa.
- **Bug encontrado y corregido durante la validación:** `stop_times_dia_L.csv` se leía con `dtype=str`, lo que ordenaba `stop_sequence` alfabéticamente ("10" antes que "2") y corrompía el cálculo de paradero de origen/destino en viajes con más de 9 paraderos. Se corrigió casteando `stop_sequence` a `int` antes de ordenar. Detectado porque el conteo de paraderos terminales únicos (988) no calzaba con la cifra de referencia del prototipo (641) — buen ejemplo de por qué los chequeos de sanidad automáticos importan.
- **Resultado (red completa), todos los chequeos automáticos en verde:**
  - 64.502 expediciones (== cifra de referencia).
  - 417 rutas, 641 paraderos terminales únicos (== cifra de referencia).
  - Concurrencia máxima: 6.539 expediciones simultáneas a las 8:00 (== cifra de referencia).
  - 0 NaN en distancia/energía; todas las duraciones y horarios consistentes.
- Outputs: `data-processed/expediciones.csv` (64.502 filas), `data-processed/terminales.csv` (641 filas), `results/03_preprocesamiento/reporte.md` + 2 gráficos (`buses_por_hora.png`, `energia_por_expedicion.png`).
- **Siguiente paso:** Etapa 2 (VSP) sobre la red completa, modos `ruta` (caso base) y `libre` (cota inferior), usando `expediciones.csv` como input.

### 28/09/2026 — Etapa 2 (VSP) corrida sobre la red completa, modos `ruta` y `libre`
- `scripts/6-vsp_asignacion_buses.py` generaliza el prototipo exploratorio (an3.py) agregando arcos de **pullout/pullin reales** a electroterminal (el prototipo original no los tenía). Probado primero en checkpoint chico (3 rutas: 101, 102, 301) verificando a mano una jornada completa (secuencia temporalmente factible, kWh acumulado = suma de expediciones + deadhead), luego corrido sobre la red completa.
- **Dos bugs encontrados y corregidos durante la validación del checkpoint chico** (antes de escalar a la red completa — exactamente para esto sirve el checkpoint):
  1. El output usaba `trip_id` como identificador de cada expedición en las jornadas y en el chequeo de cobertura. `trip_id` **no es único por expedición** (un mismo patrón GTFS se repite muchas veces por frecuencia: 6.620 patrones → 64.502 expediciones). Esto hacía que el chequeo de cobertura fuera inválido (no podía detectar duplicados ni faltantes) y que el CSV de jornadas fuera ambiguo. Se corrigió agregando un `expedicion_id` único (`trip_id#k`) en `scripts/common/tiempo.py` y usándolo en todo `6-vsp_asignacion_buses.py`.
  2. El resumen de resultados sumaba `pullout_km`/`pullin_km` sobre **todas** las expediciones (64.502), no solo sobre las que efectivamente inician/terminan una jornada (~buses). Esto inflaba el costo total reportado en ~4x. Se corrigió desglosando `km_pullout`/`km_interlining`/`km_pullin` directamente en `data-processed/jornadas_*.csv` y sumando desde ahí, con un `assert` que cruza el interlining total contra lo que reporta el solver.
- **Resultado (red completa), ambos escenarios con chequeo de cobertura y consistencia en verde:**

  | Escenario | Buses | Costo total (USD) | Tiempo |
  |---|---|---|---|
  | `ruta` (caso base) | **8.654** | 2.985.009 | 5 s |
  | `libre` (cota inferior C0) | **7.055** (−18,5%) | 2.546.383 (−14,7%) | 39 s |

  El número de buses en ambos modos **calza exactamente** con el prototipo exploratorio del 28/09 (8.654 y 7.055), pese a que ahora el modelo sí paga el costo real de pullout/pullin — buena señal de que el modelo está bien migrado. Ver tabla completa en la sección 3 de este documento.
- Outputs: `data-processed/jornadas_ruta.csv`, `jornadas_libre.csv`, `results/06_vsp/resumen_escenarios.csv`, `results/06_vsp/graficos_{ruta,libre}.png`.
- **Siguiente paso:** Etapa 1 (clustering C1 y C2), y luego re-correr esta Etapa 2 en modo `cluster` (Fase 6 del plan) para calcular el "precio del clustering" frente a `libre`.

## 5. Cómo reproducir (se completa a medida que existan los scripts)

```bash
# Etapa 0 — preprocesamiento
python scripts/3-preprocesamiento_expediciones.py

# Etapa 1 — clustering de rutas a electroterminales
python scripts/4-clustering_nearest.py      # C1
python scripts/5-clustering_milp.py         # C2

# Etapa 2 — asignación de buses (correr una vez por escenario)
python scripts/6-vsp_asignacion_buses.py --modo ruta      # caso base
python scripts/6-vsp_asignacion_buses.py --modo libre     # cota inferior (sin clustering)
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion c1
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion c2
```

Cada corrida de la Etapa 2 agrega una fila a `results/06_vsp/resumen_escenarios.csv` — no lo sobrescribe.

## 6. Referencias

- Documento de metodología completo (diagnóstico, formulaciones, KPIs, plan de trabajo): [`Propuesta_metodologia_reunion.md`](../Propuesta_metodologia_reunion.md).
- Contexto congelado del Informe 1: [`00_contexto_entrega1.md`](00_contexto_entrega1.md).
- Preguntas y supuestos pendientes de validar con el profesor/ayudante: [`02_pendientes_profesor.md`](02_pendientes_profesor.md).
