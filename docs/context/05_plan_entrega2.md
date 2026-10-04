# Plan computacional para la presentación del 06/10

> Qué código falta, en qué orden, con qué entradas y salidas, cómo se valida, y **por qué** se hace cada
> cosa. Lo ejecuta quien continúe el trabajo; está pensado para que se entienda sin haber visto cómo se
> llegó hasta acá. Metodología y supuestos: [`01_metodologia.md`](01_metodologia.md) y
> [`02_supuestos_y_decisiones.md`](02_supuestos_y_decisiones.md). Cómo correr lo que ya existe:
> [`03_guia_pruebas.md`](03_guia_pruebas.md).
>
> Presentación: **06/10**. Informe: **11/10**. Última edición: **04/10/2026**.
>
> **Nomenclatura vigente de escenarios (04/10):** E0 (por línea, terminales unidos), E1 (+ interlining, unidos), LB; E0_sep y
> E1_sep (separados: evidencia, infactibles); E1_C2 y E1_C2_sep (variantes con C2). Las referencias a E2, E2b o E2_C2 en este
> plan usan la nomenclatura previa (E2 = hoy E1; E2_C2 = hoy E1_C2). Lo vigente está en `01_metodologia.md` (§5).

---

## 0. Qué se busca y qué NO se busca

**Alcance mínimo acordado con el profesor:**
1. **Caso base completo**, con KPIs de una solución factible.
2. **Metodología justificada** (qué se hace y por qué): clusterización y MILP.
3. **Algo probado**: aplicar el caso base una vez clusterizado, y probar el MILP en **instancias
   pequeñas**. No se pide el problema completo resuelto.

**Quien ejecuta este plan no prepara slides ni escribe el informe.** Prepara el material para que otros
lo hagan fácil: gráficos con sus CSV debajo, justificaciones concisas en archivos `.md`, las
modelaciones escritas, y un índice que diga qué figura sostiene qué mensaje (§6).

**Principio de trabajo:** cada resultado se contrasta con lo que se esperaba. Si no coincide, se
explica por qué **antes** de seguir; no se ajusta el modelo para que calce. Un resultado inesperado
bien explicado vale más para la presentación que uno limpio sin explicación.

---

## 1. Punto de partida

**Existe y es vigente:** Etapa 0 completa; Etapa 1 (C1a, C1b, C2) corrida **pero bajo el supuesto
anterior** (ver abajo); el código de la Etapa 2 (VSP), que funciona y no depende del SOC.

**Está obsoleto por el rechazo del SOC 100%:** `SOC_INICIAL = 1.0`, el escenario `soc100` de C2, y las
conclusiones del tipo "la capacidad no restringe". Los archivos `rutas_cluster_c2.csv` y
`rutas_cluster_c2_ciclo.csv` actuales hay que regenerarlos (ver Bloque A).

**No existe aún:** simulador de carga reactiva, MILP de carga, KPIs de todos los escenarios,
calibración del deadhead, análisis de recargas según el SOC, justificaciones.

### Cifras de referencia para validar (no forzar; si algo difiere, explicar)

| Qué | Valor | Origen |
|---|---|---|
| Etapa 0 | 64.502 expediciones · 417 rutas · 641 terminales · concurrencia 6.539 a las 8:00 · 1.883,6 MWh | Medido, vigente |
| Cierre ida-vuelta | 94,7% de 300 rutas a < 500 m; mediana 85 m | Medido, vigente |
| C1a / C1b | Cambian 41 de 417 rutas; costo aprox. pullout/pullin 83.843 → 83.271 USD/día | Medido, vigente |
| C2 (ciclo, θ = 1, carga con pullout/pullin) | Mueve 5 rutas respecto de C1b; uso: Vespucio Norte 33,7% · El Conquistador 80,8% · Los Espinos 97,6% · La Reina 76,2% · Santa Rosa 67,1% (con C1b, Los Espinos 101,6%) | Medido, vigente (corregido el 04/10, C7) |
| Barrido de θ (ciclo) | 8 rutas movidas con θ = 0,9; 14 con 0,8; infactible con 0,7 | Medido, vigente |
| Etapa 2 (ronda anterior) | sin interlining 8.654 buses · con clustering 7.456 (C1) / 7.454 (C2) · libre 7.055 · cota 6.539 | **Referencia**: debería reproducirse (el VSP no usa batería), salvo diferencias menores por usar C1b |
| Jornadas con recarga a mitad del día (sin interlining) | 30,1% (nivel 100%), 45,2% (90%), 59,1% (80%) | Medido sobre las jornadas anteriores; debe reproducirse con el barrido |
| Holgura de carga | ~16.500 h-cargador posibles contra ~11.900 necesarias (cota, 139%) | Medido, cota optimista |

---

## 2. Calendario sugerido y prioridades

| Día | Bloques | Nota |
|---|---|---|
| **Sáb 03/10** | **A** (verificar) → **B** (deadhead, independiente) → **C** (Etapa 2 en E0-LB) | Las jornadas de C no dependen del nivel de batería, así que pueden correrse antes de decidirlo |
| **Dom 04/10** | **D** (simulador reactivo) → **barrido de niveles** por costo total → fijar el caso base | **D es la pieza de mayor riesgo** y bloquea la elección del nivel |
| **Lun 05/10** | **E** (MILP) → **F** (KPIs con el caso base fijado) → justificaciones → índice de figuras → verificación | |
| **Mar 06/10** | Presentación | |

**Orden de dependencias (acordado el 03/10):** el nivel de carga se elige por **costo total**, y ese costo
solo existe con el simulador (D). Por eso el barrido de niveles va después de D, no dentro de C. El caso
base no se fija hasta tener ese barrido.

**Orden de corte si el tiempo no alcanza** (de lo último que se sacrifica a lo primero):
**A → B → C → D → barrido → F** cubre el mínimo exigido (caso base completo con KPIs, nivel elegido por
costo y clusterización probada). **E** eleva la entrega de "mínimo" a "lo que el profesor dijo esperar".
Se sacrifican primero: las variantes C2 (E1_C2, E2_C2), la sensibilidad de niveles por debajo de 90%, la variante del MILP con
terminales unidos.

**Versión mínima de D si aprieta el tiempo:** simular sin colas (cada bus carga en cuanto puede),
calcular la ocupación resultante y **reportar cuántos minutos supera los puestos** en vez de hacer
esperar a los buses. Es menos fiel pero entrega el caso base completo. La versión completa agrega la
espera y la regla de partición por atraso.

---

## 3. Bloques de trabajo

### Bloque A — Parámetros y Etapa 1 bajo el supuesto nuevo
*Prioridad máxima: es la base de todo lo demás.*

**Por qué.** El profesor rechazó SOC 100%. Todo lo que dependa de `SOC_INICIAL` o del escenario
`soc100` es incorrecto, y la Etapa 1 hay que regenerarla para que los mapas, tablas y la asignación
que alimenta la Etapa 2 sean coherentes con lo que se va a presentar.

**Cambios de código.**
1. `scripts/common/parametros.py`: eliminar `SOC_INICIAL`. El nivel cíclico **base sale de los datos**
   (`max_soc` de `parameters.csv` = 1.0). Se define la lista de barrido `[1.0, 0.9, 0.8, 0.7]`. El nivel
   base NO se fija en el código: lo elige el barrido (criterio: mínimo costo total, ver `02` B6). Agregar a `Costos` una función `bateria_util_ciclica_kwh(soc)` = `battery_kwh × (soc − min_soc)`
   (315 kWh al 100%, 280 al 90%, 245 al 80%).
   `bateria_util_kwh` (315, física) deja de usarse en código operacional. Documentar en el docstring
   que `SOC_CICLICO` es nivel de partida, de llegada y **tope de carga** (ver `02`, B6 y C3).
2. `scripts/5-clustering_c2.py`:
   - `ciclo` pasa a ser **el** escenario; `soc100` deja de generar asignaciones. Se conserva **solo**
     el cálculo de uso de capacidad bajo `soc100` como **tabla de evidencia** de por qué se rechazó
     (`capacidad_sin_vs_con_recuperacion.csv`: ~5% contra ~72%).
   - `rutas_cluster_c2.csv` pasa a contener la asignación bajo ciclo (θ = 1). Se elimina
     `rutas_cluster_c2_ciclo.csv`.
   - Se elimina la grilla de horas disponibles (24/18/10): el profesor dijo que no hay restricción de
     horas. Se conserva el barrido de θ.
   - Barrido de θ con capacidad **separada y combinada** (Los Espinos + Santa Rosa en una bolsa de
     270) para mostrar a partir de qué θ divergen. Es evidencia secundaria: la asignación a θ = 1 es la
     misma. **El efecto real de unir está en el Bloque C (E2)**, no acá.
   - Nota de documentación: `h_r` bajo ciclo **no depende** del nivel de SOC (se recarga todo lo
     consumido), así que C2 no usa `SOC_CICLICO`.
3. `scripts/8-clustering_comparacion.py`: dejar tres estrategias (C1a, C1b, C2); reescribir los textos
   fijos del reporte que hablan del "caso base bajo SOC 100%"; quedan 3 mapas de estrategia en vez de 4.

**Salidas.** `data-processed/rutas_cluster_{c1a,c1b,c2}.csv`, `rutas_clustering_completo.csv`,
`results/etapa1_clustering/` regenerado.

**Validación.** *(Versión original del Bloque A, con la carga medida solo con energía comercial: C2 = C1b, 10.464
horas-cargador. Superada por la corrección C7 del 04/10: la carga incluye pullout y pullin, C2 mueve 5 rutas y la
carga total es 11.760 horas-cargador; ver `02_supuestos_y_decisiones.md`, C7.)* Las 417 rutas se asignan una sola vez.

---

### Bloque C — Etapa 2 (VSP) bajo la escalera de escenarios
*El código existe; hay que ajustarlo y correrlo.*

**Por qué.** Entrega los escenarios E0, E1, E2 (C1b + unión) y LB (y las variantes C2, propuesta), que son el "aplicar el caso base una vez
clusterizado" que el profesor pidió, y mide el costo de cada decisión.

**Cambios de código en `scripts/6-vsp_asignacion_buses.py`.**
1. **Modo `ruta` debe aceptar `--asignacion`** (hoy fuerza el electroterminal más cercano al
   *centroide*, o sea C1a). Sin esto, E0 y E1 usarían depósitos distintos y la comparación no aislaría
   solo el interlining.
2. **Opción para unir electroterminales** (p. ej. `--unir-electroterminales 3 5`, con los `depot_id`
   de Los Espinos y Santa Rosa): las rutas de ambos pasan a formar **un solo grupo de interlining**
   (hoy el grupo es el electroterminal). Los costos de pullout y pullin siguen yendo al patio asignado
   a cada ruta.
   *Consecuencia a dejar explícita:* en el terminal unido, una jornada puede salir de un patio y
   volver al otro (están a 1,1 km); no viola el retorno porque es **un solo electroterminal**.
3. **Chequeo automático de retorno:** en `ruta` y `cluster`, `depot_salida == depot_llegada` en toda
   jornada (o pertenecen al mismo terminal unido). Debe fallar con mensaje claro si no se cumple.
4. El reporte de jornadas que superan la batería debe usar 280 kWh (y 245 en la sensibilidad), no 315.
5. `resumen_escenarios.csv` hoy **agrega** una fila por corrida y deja duplicados al repetir una
   etiqueta: reemplazar la fila de la misma etiqueta.

**Escenarios a correr.**

| Etiqueta | Modo | Asignación | Notas |
|---|---|---|---|
| E0 | `ruta` + unir 3 y 5 | `rutas_cluster_c1b.csv` | Caso base (por línea, terminales unidos) |
| E1 | `cluster` + unir 3 y 5 | `rutas_cluster_c1b.csv` | Con interlining (**configuración propuesta**) |
| LB | `libre` | — | Cota inferior; viola el retorno |
| *E0_sep, E1_sep* | `ruta` / `cluster` | `rutas_cluster_c1b.csv` | Terminales separados: evidencia (infactibles en la carga) |
| *E1_C2, E1_C2_sep* | `cluster` (+ unir) | `rutas_cluster_c2.csv` | Variantes C2 (propuesta) |

**Expectativa a verificar.** E1 debería bajar fuertemente la flota respecto de E0; unir los terminales debería bajar la
flota de E1 (más encadenamientos dentro de un grupo de 186 rutas) y eliminar el déficit de carga. LB queda por debajo de
todos. **Resultado:** E0 8.654 → E1 7.366 → LB 7.055 (E1_sep 7.460: unir baja 94 buses); las variantes C2 casi no cambian
el VSP (+0 / +2 buses). *(Nota histórica: la primera versión de este plan esperaba
"E2 = E1" con C2; era un artefacto del estimador de carga de C2, corregido en C7.)*

**Sensibilidades del Etapa 2** (el VSP corre en ~1 min, es barato): sobre E1, factor de desvío 1,2 y
1,5 (además del 1,3), y layover 0 y 10 min. Responde a la crítica anunciada sobre el deadhead: si la
flota casi no cambia, el 1,3 importa poco.

**Análisis de recargas según el nivel** (nuevo, `scripts/13-analisis_soc.py`; se ejecuta **después de D**, junto con el barrido de niveles). Sobre las jornadas de E0
y E1: para los niveles 100% (base, datos), 90%, 80% y 70%, cuántas jornadas necesitan 0, 1 o 2+
recargas intermedias, y la distribución de energía por jornada con las líneas de 245, 280 y 315 kWh.
**Por qué:** es el análisis que decide el nivel con datos: la curva completa del barrido (costo, buses,
eventos, jornadas partidas, % con recarga intermedia), con el criterio declarado en `02`, B6.

**Salidas.** `data-processed/jornadas_{E0,E1,E2,LB,E1_C2,E2_C2}.csv`; `results/etapa2_vsp/` con
`resumen_escenarios.csv`, tabla de sensibilidades, gráficos, `precio_del_clustering.csv`.

**Validación.** Cobertura exacta (cada `expedicion_id` en una sola jornada); buses E0 ≈ 8.654 y LB ≈
7.055 (referencia); orden `E0 ≥ E1 ≥ E2 ≥ LB ≥ 6.539`; retorno cumplido; recargas del análisis de SOC
reproducen 45,2% / 59,1% (E0) y 57,5% / 76,0% (E1).

---

### Bloque B — Justificación empírica del deadhead
*Barato y responde a una crítica que el profesor anunció.*

**Por qué.** El profesor dijo que si el deadhead es euclidiano "probablemente nos la critiquen". El
grupo decidió mantenerlo por tiempo, pero necesita una justificación **concisa y fácil de entender**,
no un 1,3 que aparece de la nada ni una caja negra de OSM.

**Qué hacer** (`scripts/9-calibracion_deadhead.py`, nuevo). Con los 839 trazados GTFS
(`shapes_bus.csv`, ya en el repo, y `shape_distances_bus.csv`):
1. Para cada trazado, tomar pares de puntos separados por un **largo de recorrido** *s* (3, 5, 10 y
   15 km) y calcular el cociente `s / distancia en línea recta` entre ellos. Es el factor de rodeo
   observado **a la escala de un deadhead**. **[Medido]** En el VSP anterior los pullout y pullin
   tienen mediana ~11 km (p10 ≈ 5 km, p90 ≈ 18,5 km), y el deadhead entre expediciones encadenadas
   (interlining) promedia solo ~0,3 km por conexión. O sea: el factor de desvío afecta sobre todo el
   **costo** de salir y volver al electroterminal, y casi nada la **factibilidad** del interlining.
2. Reportar mediana y percentiles por escala, y compararlos con 1,3.
3. Gráfico: distribución del factor de rodeo por escala, con el 1,3 marcado.

**Salvedades honestas, a declarar tal cual.**
- Una ruta comercial **rodea más** que un deadhead (va sirviendo paraderos), así que el factor
  medido es una **cota superior** del rodeo de un deadhead. Si sale cercano o menor que 1,3, el 1,3 es
  razonable y conservador.
- Los buses circulan por avenidas principales, así que el factor podría subestimar el de un par
  origen-destino arbitrario por calles menores. Se declara como limitación.
- Con más tiempo (informe), se puede validar contra la red vial de `chile.gpkg`, pero **no** es
  necesario para la presentación y vuelve opaca la explicación.

**Salidas.** `results/etapa0_calibracion_deadhead/`: tabla de factores por escala, gráficos, y el
insumo de `docs/justificaciones/02_factor_desvio_deadhead.md`.

**Validación.** Los factores deben ser ≥ 1 (el recorrido nunca es menor que la recta); el cociente de
cada trazado completo debe coincidir con `distancia del trazado / distancia entre extremos`.

---

### Bloque D — Simulador de carga reactiva (política miope)
*La pieza nueva más importante: completa el caso base.*

**Por qué.** Sin esto el caso base **no tiene energía**: no hay costo de carga, ni colas, ni jornadas
partidas. El profesor exigió KPIs de una solución factible; una solución sin batería no lo es. Además
es la política contra la cual se mide el valor de optimizar la carga.

**Qué hacer** (`scripts/10-carga_reactiva.py`, nuevo). Entrada: las jornadas de un escenario
(`jornadas_<etiqueta>.csv`) más `expediciones.csv`. Para cada jornada se reconstruye la secuencia de
expediciones, con los tiempos de deadhead calculados **igual que en el VSP** (misma función de
distancia, factor y velocidad, para que sean consistentes). Reglas, detalladas en `01_metodologia.md`
(Etapa 3):

1. El bus parte con `SOC_CICLICO` (base 100%, de los datos).
2. Antes de cada expedición, si no podría completarla **y volver a su electroterminal** sin bajar del
   10%, debe cargar antes: va al electroterminal, carga hasta `SOC_CICLICO` sin mirar la tarifa, y
   vuelve. Necesita un hueco ≥ traslado + carga + traslado + layover.
3. **Sin hueco suficiente → la jornada se parte (+1 bus).** Se cuenta y se reporta.
4. Sin puesto libre → el bus espera (0,03 USD/min). Si la espera lo atrasa para su siguiente
   expedición → también se parte.
5. Al terminar, vuelve al electroterminal y carga hasta `SOC_CICLICO`. Si no alcanza antes de su
   primera salida del día siguiente → **ciclo no cumplido**, se registra.
6. **La ocupación y la tarifa son periódicas (módulo 24 h).** El día siguiente es igual a éste, así
   que la carga nocturna de después de medianoche comparte puestos con la de las primeras horas del
   día. Esto es fácil de olvidar y distorsiona la ocupación si no se hace.
7. Costo de energía: kWh por la tarifa del bloque en que se carga (`electricity_prices.csv`, que
   **ningún script usa todavía**) más 5 USD por evento de carga.

**Salidas.** `results/etapa3_carga_reactiva/`:
- `eventos_<etiqueta>.csv`: bus, electroterminal, inicio, fin, kWh, costo de energía, tipo
  (intermedia o final), espera.
- `ventanas_<etiqueta>.csv`: por bus, ventanas en que está conectable, con la energía consumida desde
  la ventana anterior (**es el insumo del Bloque E**).
- `jornadas_<etiqueta>.csv`: jornadas tras las particiones, con ids nuevos.
- `ocupacion_<etiqueta>.csv`: ocupación por minuto (módulo 24 h) y por electroterminal.
- Resumen: nº de recargas, buses extra por partición, ciclos no cumplidos, minutos de espera, uso
  máximo de cada electroterminal, costo de energía.

**Validación.**
- La energía total cargada ≈ la total consumida (ciclo: se recarga todo lo consumido). Si no, hay un
  error de contabilidad.
- El SOC nunca baja del 10% ni sube del tope; toda jornada termina en su electroterminal.
- **Cobertura intacta:** tras las particiones, cada `expedicion_id` aparece en exactamente una
  jornada.
- Checkpoint chico antes de correr la red: 3 rutas (`101 102 301`) revisando a mano **una jornada
  completa** con su SOC paso a paso.

**Riesgo.** Es código nuevo y complejo. Si aprieta el tiempo, usar la versión mínima (§2).

---

### Bloque E — MILP de programación de carga, instancia chica
*Lo que el profesor dijo esperar de un MILP: probarlo en instancias pequeñas.*

**Por qué un MILP y por qué acá.** Es el único lugar donde conviven la dimensión **temporal**, la
**tarifaria** y la **capacidad de puestos**; la política reactiva no ve ninguna de las tres. Se
escoge este subproblema (y no la asignación de buses, que ya es exacta por flujo) porque es donde
existe una decisión que la política miope toma mal: *cuándo* cargar.

**Qué hacer** (`scripts/11-milp_carga.py`, nuevo). Un electroterminal; formulación en
`01_metodologia.md`, Etapa 4. Entrada: `ventanas_<etiqueta>.csv` del Bloque D. Variables por
bus × intervalo de 15 min: energía cargada, cargando, inicio de evento, energía almacenada.
Minimiza tarifa × energía + 5 USD por evento, con puestos por intervalo, límites de energía y
condición cíclica. Con el tope en `SOC_CICLICO`, el bus termina el día exactamente en ese nivel.

**Detalles que no hay que olvidar.**
- **Capacidad y tarifa periódicas (módulo 24 h):** una carga nocturna que cruza medianoche usa los
  mismos puestos que las de la madrugada. Igual que en el Bloque D.
- Se puede formular por intervalos (con el consumo por intervalo) o **por ventanas** (el consumo entre
  una ventana y la siguiente es una constante): la segunda tiene bastantes menos restricciones y se
  recomienda.
- El MILP optimiza **cuándo y cuánto dentro de ventanas ya decididas** por el simulador: no inventa
  ventanas ni cambia la flota.

**Definición de la instancia chica.** Se define por criterio, no por un tamaño arbitrario. El riesgo a
evitar es una instancia **trivial**: con 100 buses y los 150 puestos de un electroterminal real, la
capacidad nunca aprieta y el MILP se reduce a "cada bus carga en la hora más barata", sin decidir nada
interesante, lo que no probaría el modelo.

1. **Escala proporcional.** La instancia conserva la congestión del sistema real: en E1 tras la carga, **~0,058
   puestos por bus** en el terminal unido Los Espinos + Santa Rosa (270 puestos / 4.622 buses; red completa 0,068 =
   700 / 10.295). Para N buses, puestos = `round(N × 0,058)`.
2. **Selección determinista.** Muestra de N jornadas de **un** electroterminal, con **semilla fija**
   (fijarla en el script y documentarla). **Electroterminal sugerido: el terminal unido Los Espinos +
   Santa Rosa**, el más exigido (82,5% de su capacidad de 24 h con la energía real y ~17 buses por puesto; los demás en
   E1: Vespucio Norte 6,9 · La Reina 16,4 · El Conquistador 16,7). Es donde el MILP tiene más que decidir.
   **Ojo con el ciclo:** con ventanas fijas el ciclo es infactible al 100% (cota LP 84%), así que el MILP necesita una
   holgura de reserva (binaria "este bus necesita reserva", 250 USD) para ser siempre factible y comparable con el
   simulador.
3. **Tamaño por tratabilidad, definido operacionalmente.** "Chica" = resuelve a optimalidad (brecha
   < 1%) en menos de ~10 min con la licencia académica. Cada bus aporta ~37 intervalos de 15 min:

   | N buses | Binarias aprox. | Puestos proporcionales |
   |---|---|---|
   | 50 | ~1.900 | 5 |
   | 100 | ~3.700 | 9 |
   | 200 | ~7.500 | 19 |
   | 400 | ~15.000 | 38 |
   | 800 | ~30.000 | 75 |

   Se corre una **escalera de tres tamaños (50 / 200 / 400)**. El profesor habló de "instancias
   pequeñas", en plural; y mostrar cómo escala el tiempo es un resultado en sí mismo y la
   justificación honesta de por qué no se corre sobre los ~10.300 buses de E1 tras la carga. Si 400 no resuelve en el
   límite, se reporta tal cual (también es evidencia) y se baja a 300.
4. **No trivialidad, con chequeo automático.** La capacidad debe estar saturada en al menos una
   fracción mínima de intervalos (umbral a fijar, p. ej. ≥ 10%). Si no, se descarta la instancia y se
   reducen los puestos o se aumenta N. No se reporta una instancia donde el MILP no tenía nada que
   decidir.
5. **Comparación en la misma instancia.** Mismos buses y mismos puestos para el MILP y la política
   reactiva. Eso da el **valor de la carga inteligente en miniatura**, con la salvedad declarada de
   que es a escala reducida.

**Variante opcional (si sobra tiempo):** repetir una instancia con Los Espinos y Santa Rosa como un
solo electroterminal (puestos sumados) para ver, en miniatura, si compartir cargadores mejora el
resultado.

**Salidas.** `results/etapa4_milp_carga/`: programación óptima por bus, ocupación horaria
(reactiva vs óptima), distribución de la energía por bloque tarifario, tabla de tiempos de
resolución por N, costo reactivo vs óptimo en la misma instancia.

**Validación.**
- **Prueba de correctitud fuerte:** si el programa reactivo respeta la capacidad en la instancia,
  es una solución factible del MILP, así que el costo del MILP debe ser **≤** el reactivo. Si es mayor,
  hay un error.
- Ningún puesto excedido, SOC dentro de límites, ciclo cumplido, brecha del solver < 1%.
- Instancia no trivial (chequeo 4).

**Lectura honesta del resultado.** E3 existe **a escala de instancia**. La comparación válida es
reactiva vs MILP sobre los mismos buses. Extrapolar a toda la red es una estimación y debe rotularse
como tal en cualquier gráfico o texto.

---

### Bloque F — KPIs, comparación y material para el equipo
*El entregable real: que los demás puedan armar la presentación y el informe sin rehacer análisis.*

**Qué hacer.**
1. `scripts/12-kpis_comparacion.py` (nuevo): tabla de KPIs de todos los escenarios (definidos en
   `01_metodologia.md` §6), con el desglose de costo (flota + km vacíos + espera + energía + cargas
   fijas), buses, % de km vacíos, costo medio de la energía, % cargado en valle, uso máximo por
   electroterminal, utilización por bus, jornadas partidas y ciclos no cumplidos. CSV, tabla en
   markdown y gráficos.
2. **Orden de magnitud para sanear los resultados:** la flota cuesta ~250 USD × ~7.500-8.700 buses ≈
   1,9-2,2 millones de USD/día, y la energía ~215.000-470.000 USD/día (2.150 MWh × 0,10-0,22). Si algún
   KPI queda fuera de esos órdenes, revisar antes de presentar.
3. **Justificaciones** en `docs/justificaciones/`: archivos cortos (~1 página), lo que se pega en el
   informe. Cada uno separa **medido / dicho por el profesor / razonamiento propio**:
   - `01_clusterizar_por_ruta.md`
   - `02_factor_desvio_deadhead.md`
   - `03_caso_base_y_escalera.md`
   - `04_soc_ciclico.md` (contenido en `02_supuestos_y_decisiones.md`, B6)
   - `05_unir_terminales.md` (juntos vs separados, con números de E1 vs E2; por qué C2 queda como propuesta)
   - `06_eleccion_metodologia.md` (por qué MILP, por qué clustering espacial)
   - `07_instancia_chica_milp.md` (los 5 criterios del Bloque E)
4. **Índice de figuras** (§6) en `results/INDICE_FIGURAS.md`.
5. Actualizar `01_metodologia.md` y `02_supuestos_y_decisiones.md` con los resultados reales (hoy
   dicen "a regenerar" o "a crear"), `03_guia_pruebas.md` con los comandos y cifras nuevas,
   `04_bitacora.md` con una entrada, y `docs/Estructura_carpeta_proyecto.md`.

---

## 4. Contratos entre bloques

Para que las piezas encajen sin adivinar:

| Archivo | Lo produce | Lo consume | Columnas clave |
|---|---|---|---|
| `jornadas_<etq>.csv` | Bloque C (script 6) | D, 13 | `bus_id; expedicion_ids ("a;b;c"); depot_salida; depot_llegada; dep_min; arr_min; km_pullout; km_interlining; km_pullin; kwh_total` |
| `ventanas_<etq>.csv` | Bloque D | E | bus, electroterminal, `t_ini`, `t_fin`, tipo (intermedia/final), `kwh_consumidos_desde_ventana_anterior` |
| `eventos_<etq>.csv` | Bloque D | F | bus, electroterminal, `t_ini`, `t_fin`, `kwh`, costo, tipo, espera |
| `ocupacion_<etq>.csv` | Bloque D | F | minuto (módulo 24 h), electroterminal, buses cargando |
| `resumen_escenarios.csv` | Bloque C | F | etiqueta, buses, costos, km |

Claves de unión: usar siempre `expedicion_id` (**no** `trip_id`, que no es único por expedición).

---

## 5. Convenciones del repositorio (mantenerlas)

- CSV con separador `;`. `matplotlib.use("Agg")` en todos los scripts.
- Cada script es autocontenido, con docstring (qué hace, entradas, salidas, uso) y lo común en
  `scripts/common/`. Parámetros en `parametros.py`, nunca repetidos.
- **Checkpoint chico antes de la red completa** (`--rutas` o `--subset`), verificado a mano, y
  `assert` con mensajes en español para los chequeos de sanidad.
- Resultados en `results/etapaN_<nombre>/` con subcarpetas `tablas/`, `graficos/` y `mapas/`.
  **Siempre los CSV subyacentes**, no solo el gráfico.
- Nada de tratar los resultados de `_ronda_anterior/` como vigentes: son referencia para validar.

---

## 6. Catálogo de figuras para presentación e informe

Cada figura sostiene un mensaje concreto. `results/INDICE_FIGURAS.md` debe listar archivo, mensaje y
sección sugerida.

| Mensaje | Figura | Estado |
|---|---|---|
| Por qué se agrupa por ruta (94,7% a < 500 m) | `etapa0_preprocesamiento/graficos/ida_vuelta_distancia.png` | Existe |
| Cuánta energía exige la red y cuándo | `etapa0_preprocesamiento/graficos/buses_por_hora.png`, `energia_por_expedicion.png` | Existe |
| Resultado del clustering | `etapa1_clustering/mapas/mapa_c2.png` y `mapa_diferencias.png` | Regenerar |
| El centroide casi no importa (0,7%) | `etapa1_clustering/tablas/comparacion_estrategias.csv` + gráfico | Regenerar |
| Los dos terminales cercanos (1,1 km) | `mapa_terminal_los_espinos.png` / `mapa_terminal_santa_rosa.png` | Regenerar |
| Por qué SOC 100% no sirve (5% vs 72%) | gráfico de `capacidad_sin_vs_con_recuperacion.csv` | **Nuevo** |
| La batería no alcanza para el día (energía por jornada vs 245/280/315 kWh) | `13-analisis_soc` | **Nuevo** |
| Cuántas recargas intermedias según el SOC | `13-analisis_soc` | **Nuevo** |
| El factor de desvío tiene respaldo | `9-calibracion_deadhead` | **Nuevo** |
| El resultado casi no depende del 1,3 | sensibilidad de E1 (Bloque C) | **Nuevo** |
| Escalera de escenarios: flota y costo desglosado E0 → E1 → E2 → LB | `12-kpis_comparacion` | **Nuevo** |
| Costo de la miopía: jornadas partidas y colas | `10-carga_reactiva` | **Nuevo** |
| Ocupación horaria de cargadores, reactiva vs MILP | `11-milp_carga` | **Nuevo** |
| Energía por bloque tarifario (valle vs punta) | `11-milp_carga` | **Nuevo** |
| Cómo escala el MILP (tiempo vs N) | `11-milp_carga` | **Nuevo** |

**Historia que conviene contar (pedido del profesor):** los análisis que sirvieron para decidir la
metodología forman parte del relato. Por ejemplo: la distancia ida-vuelta justificó clusterizar por
ruta; la cercanía de Los Espinos y Santa Rosa motivó probar unirlos; el rechazo de SOC 100% se
sostiene con "no pagaríamos ~93% de la energía".

---

## 7. Qué se considera terminado

- [x] Etapa 1 regenerada bajo ciclo diario; C2 con la carga corregida (C7) validada contra la energía real de las jornadas; mapas y tablas actualizados.
- [x] Escenarios E0 y E1 (C1b, terminales unidos), LB, las evidencias de terminales separados (E0_sep, E1_sep) y las variantes C2 (E1_C2, E1_C2_sep) corridos, con retorno verificado y cobertura exacta.
- [x] Simulador reactivo corrido sobre los escenarios, con energía, colas, jornadas partidas, buses de reserva (condición cíclica como restricción) y cota LP. **Caso base factible: E0 (3.958.063 USD/día) y E1 (3.751.250).**
- [ ] MILP resuelto en la escalera de instancias, no trivial, con costo ≤ reactivo.
- [x] Calibración del deadhead (Bloque B) y sensibilidad de la flota al factor y al layover (Bloque C).
- [x] Análisis de recargas según el nivel: barrido de niveles con la regla de B6 (`13-barrido_niveles.py`); nivel base 100%.
- [ ] Tabla de KPIs de todos los escenarios, con CSV y gráficos.
- [ ] Siete justificaciones en `docs/justificaciones/`, concisas y con las tres etiquetas de respaldo.
- [ ] `results/INDICE_FIGURAS.md`.
- [ ] Documentos de `docs/context/` al día, sin afirmaciones que contradigan los resultados.
- [ ] Cada resultado contrastado con lo esperado, y lo inesperado explicado.

## 8. Qué no hacer

- No usar el supuesto de SOC 100% en ningún resultado vigente.
- No tratar `libre` como un escenario operacional (viola el retorno): es cota inferior.
- No presentar el MILP en la instancia chica como si fuera el resultado de toda la red.
- No ajustar parámetros para que un resultado calce con lo esperado.
- No preparar slides ni escribir el informe.
- No usar `trip_id` como clave de una expedición.
