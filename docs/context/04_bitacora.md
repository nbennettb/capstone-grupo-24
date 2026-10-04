# Bitácora

> Registro fechado de lo que se hizo y se decidió, de la entrada más reciente a la más antigua. **No es
> la referencia vigente de la metodología** (para eso, `01_metodologia.md`); es el historial. Las entradas
> del 28/09 describen una ronda anterior cuyo supuesto de batería (SOC inicial 100%) fue rechazado
> después por el profesor, y parte de sus resultados (clustering bajo SOC 100%, Etapa 2 con cifras de
> flota) quedaron como referencia, no como resultado vigente. Esos archivos se conservan fuera del
> repositorio, en `_ronda_anterior/`.
>
> Última edición: **04/10/2026**.

---

### 04/10/2026 — Etapas 2 y 3, calibración del deadhead, y corrección de C2 (C7)

Secuencia de decisiones (cada paso quedó escrito antes del siguiente):
1. **Bloque B (calibración del deadhead).** Con los 839 trazados GTFS se midió el rodeo real: 1,04-1,22 a
   escala de interlining y 1,29-1,38 a escala de pullout/pullin. El 1,3 se mantiene y se contrasta en la
   sensibilidad (`docs/justificaciones/02_factor_desvio_deadhead.md`).
2. **Bloque C (Etapa 2).** Escalera E0 → E1 → E2 → LB (8.654 → 7.460 → 7.366 → 7.055 buses; E2 = C1b con Los Espinos y Santa Rosa unidos).
   El factor de desvío (1,2-1,5) mueve la flota entre −0,8% y +0,7%; el layover (0-10 min) entre −2,7% y +6,0%.
3. **Bloque D (simulador de carga reactiva, nivel 100%).** Carga parcial como decisión (el operador no parte
   una jornada que puede seguir). Resultado: la política casi no recarga a mitad del día y parte la jornada
   (+30% buses en E0); la carga se concentra de noche; Los Espinos tenía déficit de energía.
4. **Hallazgo C7.** Con la energía real de las jornadas, Los Espinos necesitaba 102-104% de su capacidad; la
   Etapa 1 medía solo la energía comercial (89,9%) y por eso "C2 = C1b". Era un artefacto del estimador.
5. **B6: regla del barrido de niveles declarada antes de correrlo** (`02`, B6): grilla 100/90/80/70%,
   admisibilidad (no empeorar ciclos no cumplidos ni déficit), mínimo costo total, empate de 0,5% a favor del
   nivel más alto, término por borde inferior o piso físico.
6. **C7 corregido:** `h_rd = (kWh_r + 2·dist_rd·n_r·1,4)/180` (carga que depende del electroterminal, GAP),
   validado contra la energía real (error de −9/−14% a −0,5/−3%). C2 mueve 5 rutas (Los Espinos 101,6% →
   97,6%). Se regeneraron la Etapa 1, el VSP y el simulador de las variantes con C2 (E1_C2: 7.462 buses, 10.343 con
   carga; E2_C2: 7.366, 10.258).
7. **Nuevo abierto, C8:** C2 con θ = 1 es necesario pero no suficiente (E2 deja 21 MWh sin reponer con Los
   Espinos al 98,5%). Pendiente de decisión.
8. **Decisión B11: C1b + unión como configuración base; C2 como propuesta.** C2 mueve solo 5 rutas (+2 buses en el
   VSP, −0,3% del costo total con carga si además se unen) y no resuelve la capacidad (déficit 21 MWh con Los
   Espinos al 98,5%); la unión sí (déficit 0). Se renombran los escenarios: E2 = C1b + unión; las variantes con C2
   pasan a E1_C2 y E2_C2 (fuera de la escalera). C1a se conserva como control de sensibilidad (se llama "C1" a C1b
   en el relato; la limpieza queda para la entrega final).
9. **B6 documentada:** el escenario que decide el nivel pasa a ser E2 (sin déficit estructural); E0 y E1 son
   robustez. Justificación completa en `docs/justificaciones/04_nivel_carga_ciclico.md`.
10. **Barrido de niveles (regla de B6 aplicada por código).** E2 elige **100%** (3.199.500 USD/día; 90% +13,1%, 80%
   +25,3%, 70% +37,7%); E0 y E1 coinciden. El costo sube por la flota (~1.500 buses por cada 10 puntos menos). La
   energía cargada sube 6% al 70% (traslados de jornadas partidas), así que "la energía total no depende del nivel"
   solo se cumple aproximadamente. Limitación declarada: el costo no paga los ciclos no cumplidos (2.207 al 100%).
11. **Corrección de la lectura del barrido (la condición cíclica es una restricción).** El usuario observó que el
   modelo no terminaba el día con todos los buses al nivel inicial, así que el "100%" no era una solución factible. Se
   confirmó: al 100%, el 21% de las cargas nocturnas termina después de la primera salida del día siguiente (2.207 de
   10.295 en E1). El diagnóstico (en memoria, sin tocar el repo) descartó que fuera el orden de la cola (cargar primero
   al que sale antes baja los incumplimientos solo de 2.199 a 2.160) y mostró que es **capacidad nocturna**: con un LP de
   carga óptima solo cabe el 84% de la energía nocturna (faltan 354 MWh/día). La cota de "139% de holgura" de B6 queda
   refutada: no miraba a qué hora está cada bus en el patio.
12. **Decisiones tomadas con el usuario:** (a) el ciclo se cumple con **buses de reserva** (250 USD/día cada uno, incluidos
   en el costo total), con la factibilidad definida como "sin déficit de energía y atraso < 24 h"; (b) **la unión de Los
   Espinos y Santa Rosa pasa a todos los escenarios operacionales** para que el caso base sea factible (separados hay
   déficit de energía a cualquier nivel); (c) la regla del barrido se **corrige antes de volver a correr**: solo compiten
   soluciones factibles, grilla 100-50% (piso físico), dos familias (con y sin reservas), E1 decide y E0 es robustez.
   **Nomenclatura vigente:** E0 (por línea, unidos), E1 (+ interlining, unidos), LB; E0_sep y E1_sep (separados,
   evidencia); E1_C2 y E1_C2_sep (variantes con C2). Las menciones anteriores de este día a E2, E2b o E2_C2 usan la
   nomenclatura previa (E2 = hoy E1; E2_C2 = hoy E1_C2; E0 y E1 de entonces = hoy E0_sep y E1_sep).
13. **Resultado del barrido corregido.** Ningún nivel entre 100% y 55% cumple el ciclo sin reservas con la política
   reactiva; 100% + reservas es el menor costo (E1: 3.751.250 USD/día; 90% +5,9%, 80% +8,5%, 70% +17,9%, 55% +52,8%; 50%
   infactible por déficit). Con una carga perfecta el ciclo sí sería posible desde 80% hacia abajo, pero costaría
   ≥ 4,0 M USD/día. **Caso base factible: E0 3.958.063 y E1 3.751.250 USD/día.**
- **Pendiente:** MILP de carga en instancias chicas (con reservas o ventanas diurnas, o será infactible)
  (Bloque E), KPIs y justificaciones (Bloque F).

### 03/10/2026 — Reunión con el profesor y reestructuración de la documentación

- **Reunión con el profesor:** respondió las 8 preguntas abiertas (ver `02_supuestos_y_decisiones.md`,
  sección A). Tres respuestas cambian el trabajo existente:
  1. **El supuesto de SOC inicial 100% queda rechazado.** Debe haber ciclo diario (empezar y terminar
     con 80-90%). El escenario `ciclo` de la Etapa 1, que era una sensibilidad, pasa a ser el caso
     principal, y el escenario `soc100` se descarta. Los resultados de la Etapa 1 que decían "la
     capacidad no restringe" eran **válidos solo bajo SOC 100%** y no son el resultado vigente.
  2. **Los buses deben volver a su propio electroterminal**, y los puestos limitan solo la carga
     (estacionar no consume puesto; se puede cargar 24 h). Cierra tres preguntas pendientes.
  3. **El caso base (sin interlining + carga reactiva) es válido**, y se sugiere un segundo caso base
     con interlining para aislar su efecto.
- **Medición del impacto del ciclo diario** sobre las jornadas existentes (ronda del 28/09): las jornadas
  con recarga a mitad del día pasan de 30,1% (SOC 100%) a 45,2% (ciclo 90%) y 59,1% (ciclo 80%) en el
  caso base; y de 38,9% a 57,5% y 76,0% con interlining. Las horas-cargador a recargar pasan de
  ~830-890 a ~12.000 por día (de ~5% a ~72% de los 700 puestos).
- **Dos correcciones a lo documentado antes:**
  - El "Los Espinos al 99,5%" del 28/09 correspondía a un cálculo tipo ciclo diario, no al caso base
    declarado entonces; bajo SOC 100% real usaba ~1%. Esto se corrigió el 30/09 y hoy deja de ser
    relevante porque SOC 100% fue rechazado.
  - Una tabla preliminar de esta sesión decía ~3.000 h-cargador y ~18% de uso para SOC 100%; el valor
    correcto, medido por jornada, es ~830-890 h-cargador y ~5%.
- **Hallazgo:** con ciclo diario, las ventanas en que los buses están fuera de jornada permiten
  ~16.500 h-cargador contra ~11.900 necesarias (139%). La factibilidad no está descartada pero la
  holgura es solo ~28% (cota optimista).
- **Reestructuración de `docs/context/`:** la metodología (antes mezclada con estado y bitácora en
  `01_metodologia_y_avance.md`) pasa a `01_metodologia.md`, ordenada por decisiones y etapas. Los
  supuestos y las preguntas ya respondidas se integran en `02_supuestos_y_decisiones.md`. Esta
  bitácora recibe el histórico fechado. El plan computacional para la presentación queda en
  `05_plan_entrega2.md`. Se eliminan los documentos de preguntas pendientes y de cierre de ronda, ya
  resueltos.
- **Alcance de la Entrega 2 acordado:** caso base completo con KPIs, escalera de escenarios, y MILP de
  carga probado en una instancia chica definida por criterio (ver el plan).

### 03/10/2026 (tarde) — Corrección: el nivel de carga cíclico no viene del profesor

- **Error mío, corregido:** en varios documentos atribuí al profesor el nivel 80-90%. Él lo mencionó como
  **ejemplo**; la condición cíclica sí fue su instrucción. Tampoco es una decisión defendible sin datos: el
  90% lo elegí por razonamiento propio (CC-CV, no verificado).
- **Criterio corregido:** se parte de **100%** (máximo de `max_soc = 1.0` en los datos) y se barre hacia
  abajo (90, 80, 70%). El nivel elegido es el que **minimiza el costo total**, con el criterio declarado
  antes de correr. Si el óptimo es 100%, ese es el resultado. Bajar de 100% requiere una fuente externa citada.
- **Qué no cambia:** la asignación de la Etapa 1. El `h_r` del escenario cíclico depende de la energía
  consumida, no del nivel. Lo que cambia es la Etapa 2 y el simulador de carga.
- **Hipótesis a verificar en el barrido:** la energía total a recargar no depende del nivel bajo la
  condición cíclica, y un nivel más alto reduce recargas intermedias y eventos. No se afirma hasta medirlo.
- **Cifras de la tabla de niveles** (30,1 / 45,2 / 59,1%): son de las jornadas de la ronda anterior
  y se regeneran con el barrido.

### 30/09/2026 — Etapa 1 (clustering de rutas a electroterminales)

- **Diseño de tres estrategias que aíslan un cambio a la vez** (no comparar cosas que difieren en más
  de un aspecto): **C1a** (heurística, distancia al centroide de la ruta — lo que hacía la ronda
  anterior), **C1b** (heurística, distancia esperada a los paraderos terminales reales de la ruta,
  ponderada por cuántas expediciones usan cada uno) y **C2** (MILP con restricción de capacidad,
  misma métrica de distancia que C1b). Así C1a→C1b aísla el efecto de la métrica de distancia, y
  C1b→C2 aísla el efecto de agregar capacidad.
- **C2 ya no depende de la Etapa 2** (decisión tomada antes de correr esta etapa): `n_buses_r` y
  `kwh_dia_r` se leen de `rutas_resumen.csv` (Etapa 0), no de `jornadas_ruta.csv`.
- **C2 se corrió bajo dos supuestos de cuánta energía hay que recargar por día** (ver
  `02_pendientes_profesor.md` #1, la pregunta más crítica del proyecto):
  - `soc100` (**caso base aprobado**): solo se recarga el excedente sobre la batería útil (315 kWh)
    por ruta. Carga total del día: **108 horas-cargador contra 16.800 disponibles (0,6%)**.
  - `ciclo` (sensibilidad): se recarga todo lo consumido. Carga total: **10.464 horas-cargador (62%
    de 16.800)**, con Los Espinos al **89,9%**.
- **Hallazgo central, verificado con un chequeo automático en el propio script:** bajo el caso base,
  **C2 coincide exactamente con C1b** (0 rutas distintas) — la restricción de capacidad no está
  activa con SOC inicial 100%. Esto corrige una lectura de la ronda anterior: el "Los Espinos al
  99,5%" que se reportó el 28/09 correspondía en realidad a una carga de tipo cíclico, no al caso
  base declarado del proyecto.
- **Barrido de θ** (escenario cíclico, H=24h): la capacidad empieza a mover rutas recién en
  θ≈0,8 (11 rutas), se vuelve más exigente en θ=0,7 (21 rutas, El Conquistador al 100%) y es
  **infactible en θ=0,6**. Grilla adicional de horas de carga disponibles (24/18/10h): el escenario
  cíclico con solo 10h de carga nocturna es **infactible** (demanda 149% de la capacidad).
- **C1a vs. C1b, bajo el mismo criterio de evaluación** (para que la comparación sea justa: ambas se
  miden contra la distancia a paraderos reales, no contra la métrica que cada una usó para decidir):
  cambian **41 de 417 rutas (10%)**, pero el costo total de pullout/pullin solo mejora **0,7%**
  (83.843 → 83.271 USD/día). El centroide es una simplificación casi inocua.
- Outputs: `data-processed/rutas_cluster_{c1a,c1b,c2,c2_ciclo}.csv`,
  `data-processed/rutas_clustering_completo.csv` (tabla ancha, 417 filas),
  `results/etapa1_clustering/{reporte.md, tablas/*.csv, graficos/*.png, mapas/*.png}` (11 mapas:
  4 por estrategia, 5 por electroterminal, 1 de paraderos, 1 de diferencias C1a↔C2).
- **Pausa:** se espera revisión y OK explícito de Nicolás antes del documento de preguntas y el
  cierre de ronda.

### 29/09/2026 — Nueva ronda: rehacer Etapa 0 y Etapa 1 paso a paso

- **Motivo:** la ronda del 28/09 corrió Etapas 0-2 de una sola vez. El código y los números cierran,
  pero Nicolás no los entiende y no puede defenderlos frente al profesor ni al ayudante. Se rehace el
  trabajo etapa por etapa, con plan → OK explícito → código → explicación didáctica → revisión, y con
  pausa total entre etapas.
- **Alcance de esta ronda: solo Etapa 0 y Etapa 1.** La Etapa 2 queda explícitamente fuera — tiene
  supuestos fuertes (layover, deadhead euclidiano × factor, SOC inicial, retorno al electroterminal)
  que se quieren discutir primero con el grupo y el profesor (ver `02_pendientes_profesor.md`).
- **Reordenamiento del repo:** los archivos de la Etapa 2 de la ronda anterior
  (`data-processed/jornadas_*.csv`, `rutas_cluster_c1.csv`/`c2.csv`, `results/03_preprocesamiento/`
  a `06_vsp/`) se movieron a `_ronda_anterior/` (agregado a `.gitignore`: no viaja al repo, pero
  queda en disco por si se retoma la Etapa 2). `scripts/6-vsp_asignacion_buses.py` y
  `7-comparar_escenarios.py` no se tocan ni se borran: se leen como referencia de qué supuestos usa
  la Etapa 2, no se ejecutan.
- **Etapa 0 rehecha (no reescrita desde cero):** se revisó `scripts/3-preprocesamiento_expediciones.py`
  completo. La lógica original (expandir `frequencies.txt` por headway a expediciones reales,
  `expedicion_id` único, cast de `stop_sequence` a entero) es necesaria y se mantiene intacta. Se
  agregó lo que le faltaba para que la Etapa 1 no dependa de la Etapa 2:
  - `data-processed/rutas_resumen.csv` (417 filas): buses estimados por ruta (cota inferior, vía
    máximo de expediciones simultáneas de esa ruta — sin layover ni retorno físico), km/día,
    kWh/día, duración media, centroide. Reemplaza la dependencia de `jornadas_ruta.csv`.
  - `data-processed/rutas_ida_vuelta.csv` (300 filas, rutas con ambas direcciones): distancia entre
    el paradero final de la ida y el inicial de la vuelta, con flag `<500 m`. Es la evidencia propia
    (no solo citada de la propuesta) de por qué la unidad de clustering de la Etapa 1 es la ruta:
    mediana 84,8 m, **94,7% de las 300 rutas bajo 500 m**.
  - `data-processed/terminales_por_ruta.csv` (1.356 pares ruta-paradero): insumo de los mapas y de
    la variante de C1 que mide contra el paradero terminal real, no el centroide.
  - Reporte de descartes explícito (`results/etapa0_preprocesamiento/descartes.csv`): 0 descartes en
    todas las categorías en la red completa (ningún viaje sin distancia, ninguna expedición sin
    coordenadas, 0 discrepancias entre la dirección leída del texto del `trip_id` y el campo
    `direction_id` real de GTFS).
  - Se detectó y documentó (no se corrigió esta ronda): 15 de las 300 rutas con ida y vuelta tienen
    más de un paradero distinto usado como fin-de-ida o inicio-de-vuelta — el "paradero
    representativo" que se usa es el más frecuente, no el único.
- **Resultado (red completa), todos los chequeos automáticos en verde:** 64.502 expediciones, 417
  rutas, 641 paraderos terminales, concurrencia máxima 6.539 a las 8:00 — las cuatro cifras calzan
  exactamente con la referencia de la ronda anterior, confirmando que los agregados no cambiaron la
  lógica existente. 1.883,6 MWh/día de energía comercial total.
- Outputs: `data-processed/{expediciones,terminales,rutas_resumen,rutas_ida_vuelta,terminales_por_ruta}.csv`,
  `results/etapa0_preprocesamiento/{reporte.md,conteos.csv,descartes.csv,distribucion_expediciones.csv,
  concurrencia_por_minuto.csv,graficos/}`.
- **Pausa:** se espera revisión y OK explícito de Nicolás antes de correr la Etapa 1.

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

### 28/09/2026 — Etapa 1 (clustering C1 y C2) corrida sobre la red completa
- Se creó `scripts/common/clustering.py` (centroide por ruta, matriz de distancias ruta-electroterminal) y se refactorizó `6-vsp_asignacion_buses.py` para reusarlo en vez de duplicar la lógica del modo `ruta` (verificado que el resultado no cambió tras el refactor: mismo costo, 42.897 USD, en el checkpoint de 3 rutas).
- **C1 (`scripts/4-clustering_nearest.py`, heurística del más cercano):** probado primero en una muestra aleatoria reproducible de 20 rutas (semilla 42), luego sobre las 417. Resultado: las 5 electroterminales reciben entre 59 y 113 rutas cada uno.
- **C2 (`scripts/5-clustering_milp.py`, MILP con capacidad):** la carga de cada ruta (`h_r`, en horas-cargador/día) y su número de buses se leen de `jornadas_ruta.csv` (por eso la Etapa 2 se corrió antes). Se definió explícitamente la unidad de capacidad (horas-cargador/día a ambos lados de la restricción) para no repetir el error de unidades del Informe 1 (ver `02_pendientes_profesor.md` #6).
  - **Checkpoint de reactividad:** con 20 rutas y `--theta 0.05` (capacidad muy reducida a propósito), el modelo movió rutas fuera de Santa Rosa (de 270 a 178 horas-cargador/día asignadas, justo bajo el límite de 180) — confirma que la restricción de capacidad sí es efectiva antes de confiar en la red completa. También se probó un `--theta` extremo (0.001) para confirmar que el manejo de infactibilidad (mensaje claro con las restricciones en conflicto vía `computeIIS`) funciona.
  - **Resultado en la red completa (`--theta 1.0`, sin apretar artificialmente):** **Los Espinos queda al 99,5% de su capacidad estimada** (2.867 de 2.880 horas-cargador/día), mientras Vespucio Norte solo usa 38,8%. Esto es un hallazgo real y presentable: incluso con el supuesto optimista de SOC inicial 100% (que hace la demanda de recarga total baja, ver dimensionamiento en `Propuesta_metodologia_reunion.md`), la proxy de carga total diaria muestra que la capacidad **sí puede ser un problema localizado** en al menos un electroterminal, no uniformemente holgada.
  - Comparado con C1: de las 417 rutas, solo 8 (1,9%) quedan en un electroterminal distinto entre C1 y C2 — la restricción de capacidad mueve pocas rutas, pero las que mueve son las que evitan sobrecargar Los Espinos.
- Outputs: `data-processed/rutas_cluster_c1.csv`, `rutas_cluster_c2.csv`, `results/04_clustering_c1/`, `results/05_clustering_c2/` (reportes + gráficos).
- **Siguiente paso (Fase 6):** re-correr `6-vsp_asignacion_buses.py --modo cluster` con `rutas_cluster_c1.csv` y `rutas_cluster_c2.csv`, y calcular el "precio del clustering" (buses y costo de cada uno frente a `libre`).

### 28/09/2026 — Fase 6: Etapa 2 por clúster + cierre de la ronda de trabajo
- `6-vsp_asignacion_buses.py --modo cluster` probado primero en un subconjunto chico (3 rutas, con `rutas_cluster_c1.csv`) para validar ese modo por primera vez, antes de correr la red completa con C1 y con C2.
- Se creó `scripts/7-comparar_escenarios.py`: lee `resumen_escenarios.csv`, genera el gráfico comparativo final (`comparacion_escenarios.png`) y la tabla `precio_del_clustering.csv`, con un chequeo de sanidad automático (`ruta ≥ cluster ≥ libre ≥ cota inferior teórica`).
- **Resultado final de la ronda (tabla completa en la sección 3):** cluster_c1 = 7.456 buses, cluster_c2 = 7.454 buses — ambos a solo ~5,7% de la cota inferior `libre` (7.055) y muy por debajo del caso base (8.654, +17,2% de costo). Esto **valida cuantitativamente** la metodología jerárquica aprobada en la reunión del 28/09: el clustering por electroterminal captura casi todo el beneficio del interlining con subproblemas mucho más chicos.
- **Alcance de la ronda 28-30/09 completado hoy mismo** (Etapa 0, Etapa 1 C1+C2, Etapa 2 en los 4 escenarios) — antes de lo planificado para el 30/09. Las Etapas 3 (recargas) y 4 (programación de carga) quedan para los próximos días, ahora con las jornadas de `cluster_c1`/`cluster_c2` ya listas como insumo.
- **Pendiente para retomar:** decidir con el equipo si la implementación final usa las jornadas de `cluster_c1` o `cluster_c2` (o ambas, para comparar) como base de las Etapas 3-4.
