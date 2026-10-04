# Metodología — Planificación de la operación de buses eléctricos (RED, Santiago)

> **Documento maestro.** Describe qué problema se resuelve, con qué supuestos, en qué etapas y con
> qué modelos. Está ordenado por decisiones y etapas, sin fechas ni historia (la historia está en
> [`04_bitacora.md`](04_bitacora.md)). Si te sumas al proyecto: lee primero
> [`00_contexto_entrega1.md`](00_contexto_entrega1.md) (qué se entregó en el Informe 1), luego este
> documento, luego [`02_supuestos_y_decisiones.md`](02_supuestos_y_decisiones.md) (por qué cada
> supuesto) y [`05_plan_entrega2.md`](05_plan_entrega2.md) (qué falta hacer).
>
> Cada afirmación lleva su origen: **[Profesor]** lo dijo el profesor, **[Dato]** viene de los datos
> del curso, **[Medido]** lo calculamos con los datos, **[Decisión]** lo decidimos nosotros.

---

## 1. Resumen

**Problema.** Para un día laboral representativo, asignar los 64.502 viajes programados de la red de
buses de RED a una flota de buses eléctricos homogénea (BYD K9), decidiendo también cuándo y dónde
recarga cada bus, de modo que se minimice el costo total (flota + km sin pasajeros + espera + energía
+ cargas). Es un **E-VSP** (Electric Vehicle Scheduling Problem).

**Enfoque.** Descomposición jerárquica por tipo de decisión, en 4 etapas: (0) preprocesar, (1) agrupar
rutas en electroterminales, (2) asignar viajes a buses, (3) insertar recargas, (4) programar la
carga. Reemplaza la descomposición temporal por horizonte rodante del Informe 1, que se descartó por
excesivamente compleja (ver `Propuesta_metodologia_reunion.md` §3, diagnóstico D1-D8).

**Decisión de fondo que condiciona todo [Profesor]:** los buses deben empezar y terminar el día con
batería suficiente para el día siguiente (**ciclo diario**). El supuesto de partir con 100% y no
recuperar la batería fue rechazado porque "nos estaríamos comiendo un montón de costos y la solución
sería miope". Esto convierte la recarga en el problema central del proyecto.

**Alcance mínimo de la Entrega 2 [Profesor]:** (1) caso base completo, con KPIs de una solución
factible; (2) metodología bien propuesta y justificada, incluyendo el modelo de clusterización y el
MILP; (3) haber probado parte de la metodología: aplicar el caso base una vez clusterizado, y probar
el MILP en instancias pequeñas (no se pide el modelo completo ni la solución final).

---

## 2. Problema y datos

Detalle completo en [`00_contexto_entrega1.md`](00_contexto_entrega1.md) y
[`../decisiones_datos.md`](../decisiones_datos.md). Lo esencial:

| | |
|---|---|
| Día modelado | Laboral (service_id = L) **[Decisión]**: es el de mayor exigencia |
| Rutas / expediciones | 417 rutas, 64.502 expediciones (viajes GTFS expandidos por su frecuencia) |
| Paraderos terminales | 641 (origen o destino de alguna expedición) |
| Energía comercial del día | 1.883,6 MWh (1,4 kWh/km constante) |
| Concurrencia máxima | 6.539 expediciones simultáneas a las 8:00 (cota inferior de flota) |
| Electroterminales | 5, **700 puestos de carga en total**: Vespucio Norte 150, El Conquistador 180, Los Espinos 120, La Reina 100, Santa Rosa 150 |
| Bus | BYD K9: batería 350 kWh, mínimo 10%, carga 180 kW, autonomía 250 km |
| Flota | **Irrestricta** [Profesor]. El `fleet_size = 1200` de `parameters.csv` está obsoleto y el código lo ignora a propósito |
| Costos | Bus 250 USD/día · km 0,5 USD · espera 0,03 USD/min · evento de carga 5 USD |
| Tarifa eléctrica (USD/kWh) | P1 0-8 h: 0,10 · P2 8-14: 0,15 · **P3 14-17: 0,22** · P4 17-19: 0,15 · **P5 19-22: 0,22** · P6 22-24: 0,11 |

---

## 3. Supuestos de operación vigentes

### 3.1 Energía y batería

| Supuesto | Valor | Origen |
|---|---|---|
| **Condición cíclica** | Todo bus **empieza y termina** el día con el mismo nivel `SOC_CICLICO` | **[Profesor]** pidió la condición (dejar batería para el día siguiente). Los 80-90% fueron un **ejemplo**. El **nivel** se busca con datos: se parte de 100% (máximo de `parameters.csv`) y se elige el que minimiza el costo total en un barrido 100-70%. Ver `02_supuestos_y_decisiones.md` B6 |
| `SOC_CICLICO` como tope | La batería nunca se carga por sobre `SOC_CICLICO` | **[Dato]** con el base de 100% (es el `max_soc` del curso) |
| Energía utilizable entre cargas | (`SOC_CICLICO` − 10%) × 350 kWh = **315 kWh** al 100%; 280 kWh al 90%; 245 kWh al 80% | Derivado |
| Condición de fin de día | `SOC_fin ≥ SOC_inicio`; con el tope, el bus termina el día exactamente en `SOC_CICLICO` | **[Decisión]** |
| Consumo | 1,4 kWh/km, constante (sin topografía, congestión ni clima) | **[Dato]** (350 kWh / 250 km) |
| Carga | Lineal a 180 kW (sin curva CC-CV) | **[Dato]** + simplificación |
| Energía a pagar | **Toda** la energía recargada, incluida la recarga final que restituye el nivel del día siguiente | Consecuencia del ciclo diario |

Consecuencia **[Medido]**: con inicio = fin, la energía que hay que recargar es la consumida (~2.150
MWh). **[Hipótesis a verificar en el barrido]**: ese total no depende del nivel; el nivel cambia la
**holgura intradía**, es decir, cuántas jornadas necesitan recargar a mitad del día.

### 3.2 Infraestructura

| Supuesto | Valor | Origen |
|---|---|---|
| Retorno | Cada bus **empieza y termina su jornada en el mismo electroterminal** | **[Profesor]** |
| Puestos | Limitan **solo la carga simultánea**. Estacionar buses en el electroterminal no consume puesto y no tiene restricción de horario | **[Profesor]** |
| Horario de carga | Un electroterminal puede cargar las 24 horas. La única restricción son sus puestos | **[Profesor]** |
| Capacidad | Constante durante el día (los datos no traen perfil horario relevante) | **[Dato]** |

### 3.3 Desplazamientos sin pasajeros (deadhead)

| Supuesto | Valor | Origen |
|---|---|---|
| Distancia | Euclidiana × **1,3** | **[Decisión]** tomada por tiempo. El profesor advirtió que "probablemente nos la critiquen". **[Medido]** contra los 839 trazados GTFS: el rodeo real mide 1,04-1,22 a escala de interlining (1-3 km, el 1,3 es conservador) y 1,29-1,38 a escala de pullout/pullin (5-15 km, cota superior del rodeo de un deadhead). Ver `docs/justificaciones/02_factor_desvio_deadhead.md` |
| Velocidad | 20 km/h | **[Decisión]** sin calibrar |
| Layover mínimo entre actividades | 3 min | **[Decisión]** sin calibrar |
| Radio de interlining | 3 km | **[Decisión]** para reducir el tamaño del problema |

Todos los valores viven en [`scripts/common/parametros.py`](../../scripts/common/parametros.py), un único
lugar, para que una sensibilidad sea cambiar un número y volver a correr.

---

## 4. Las cuatro etapas

```
Etapa 0            Etapa 1                 Etapa 2                    Etapa 3                 Etapa 4
Preproceso   →   Clustering de      →   Asignación de buses   →   Inserción de       →   Programación de carga
(expediciones,   RUTAS a electro-       por cluster (VSP en        recargas por           por electroterminal
terminales,      terminales             red espacio-tiempo,        jornada                (MILP con índice temporal,
tablas por ruta) (heurística + MILP)    LP entera, exacto)         (simulador reactivo)   tarifas horarias, capacidad)
```

La idea: **primero se decide qué bus cubre qué viaje (define el costo dominante: la flota), después
dónde y cuándo carga (define energía e infraestructura)**. En la literatura de E-VSP esto se llama
enfoque secuencial, frente al integrado. Su costo es perder optimalidad global; se mide con una cota
inferior (escenario LB, §5).

### Etapa 0 — Preprocesamiento · estado: HECHA y vigente

- **Qué hace.** Expande `frequencies.txt` (cada patrón de viaje con un "sale cada X min entre A y B")
  a **salidas individuales**, porque lo que se asigna a un bus es una salida concreta. Calcula para
  cada una hora de salida/llegada, paraderos de origen y destino con coordenadas, km y kWh.
- **Por qué es necesaria.** Sin salidas individuales no hay nada que asignar. Y `trip_id` no es
  único por expedición (6.620 patrones → 64.502 expediciones), así que se crea `expedicion_id`
  (`trip_id#k`).
- **Tablas por ruta** (insumo de la Etapa 1, sin depender de la Etapa 2): `rutas_resumen.csv`
  (buses estimados, km y kWh por día, centroide), `rutas_ida_vuelta.csv`, `terminales_por_ruta.csv`.
- **Buses estimados por ruta** = máximo de expediciones simultáneas de esa ruta. Es una **cota
  inferior** (ignora layover y retorno); suma 7.388. Solo se usa para ponderar rutas.
- **Script:** `scripts/3-preprocesamiento_expediciones.py` · **Salida:** `data-processed/`,
  `results/etapa0_preprocesamiento/`.
- **Cifras de validación [Medido]:** 64.502 expediciones · 417 rutas · 641 terminales · concurrencia
  6.539 a las 8:00 · 1.883,6 MWh/día · 0 descartes.

### Etapa 1 — Clustering de rutas a electroterminales · estado: HECHA bajo ciclo diario

**Decisión: la unidad de agrupamiento es la ruta, no la expedición.** **[Medido]** El 94,7% de las
300 rutas con ida y vuelta identificables termina la ida a menos de 500 m de donde empieza la vuelta
(mediana 85 m). Asignar cada expedición por separado rompería ese encadenamiento natural. Responde
al comentario del profesor en el Informe 1 (3.3.1): "revisar en profundidad estrategias para
clusterizar".

**Para qué sirve el cluster.** Define el electroterminal base de cada bus (salida, retorno, dónde
carga) y convierte un problema de 5 depósitos en 5 de un depósito.

Tres estrategias, cada una cambia **un solo aspecto** respecto de la anterior:

| | Qué decide | Qué aísla |
|---|---|---|
| **C1a** | Electroterminal más cercano al **centroide** de la ruta | Referencia heredada |
| **C1b** | Más cercano a los **paraderos terminales reales** de la ruta, ponderados por uso | Solo la forma de medir la distancia |
| **C2** | MILP de asignación con restricción de capacidad, misma distancia que C1b | Solo agrega la capacidad |

**Formulación de C2.**

$$\min \sum_{r\in R}\sum_{d\in D} c_{rd}\,x_{rd}\quad\text{s.a.}\quad \sum_{d} x_{rd}=1\;\;\forall r,\qquad \sum_{r} h_r\,x_{rd}\le \theta\,\kappa_d H\;\;\forall d,\qquad x_{rd}\in\{0,1\}$$

- $c_{rd}=2\cdot\text{dist}_{rd}\cdot c^{km}\cdot n_r$: costo diario aproximado de pullout + pullin de la
  ruta $r$ si su base es $d$ (`dist` = distancia esperada a sus paraderos reales, con factor 1,3;
  $n_r$ = buses estimados).
- $h_r$ = horas-cargador por día que demanda la ruta = kWh/día de la ruta ÷ 180 kW. **Bajo el ciclo
  diario se recarga todo lo consumido** (`ciclo`). Ambos lados de la restricción están en
  horas-cargador/día (el Informe 1 mezclaba puestos simultáneos con expediciones/día).
- $\kappa_d$ = puestos, $H$ = horas disponibles (24, **[Profesor]**), $\theta$ = holgura.

**Resultados [Medido, escenario cíclico, θ = 1, H = 24]:**

| Electroterminal | Rutas C1a | Rutas C1b = C2 | Uso de capacidad (h-cargador) |
|---|---|---|---|
| Vespucio Norte | 59 | 56 | 30,9% |
| El Conquistador | 98 | 108 | 69,8% |
| Los Espinos | 85 | 88 | **89,9%** |
| La Reina | 64 | 67 | 68,1% |
| Santa Rosa | 111 | 98 | 58,6% |

- **C2 coincide exactamente con C1b** (0 rutas distintas): con θ = 1 la restricción **agregada diaria**
  no está activa, porque la capacidad total alcanza (62% de uso global). Solo empieza a mover rutas
  con θ ≈ 0,8 (11 rutas), 21 rutas con θ = 0,7, e infactible con θ = 0,6.
- **C1a vs C1b:** cambian 41 de 417 rutas (10%), pero el costo aproximado de pullout/pullin mejora
  solo 0,7% (83.843 → 83.271 USD/día). El centroide es una simplificación casi inocua.
- **Límite de C2 que hay que entender:** su capacidad es un **promedio diario**. La carga real se
  concentra en ciertas horas, así que un electroterminal puede saturarse en las horas punta de carga
  aunque su promedio diario sea 70%. Esa saturación **no** la ve C2; la verá el simulador de la
  Etapa 3 como colas de espera. Por eso es posible que C2 no cambie la asignación (ver §5, E2).
- **Variante Los Espinos + Santa Rosa [Decisión, a implementar]:** están a solo 1,11 km entre sí (el
  resto de los pares a ≥ 5,9 km). La variante los trata como **un solo electroterminal de 270
  puestos** (los dos patios físicos se mantienen para las distancias). Tiene tres efectos, y solo uno
  se ve en la Etapa 1:
  1. *Capacidad combinada en C2.* **[Medido]** No cambia la asignación: separados ya no aprietan
     (Los Espinos 89,9%, Santa Rosa 58,6%; juntos 72,5%). Solo se nota al bajar θ.
  2. ***Un solo grupo de interlining* en la Etapa 2 (el efecto esperado).** Las 186 rutas (88 + 98)
     pasan a poder encadenarse entre sí, lo que en principio reduce buses. Es la parte del
     "precio del clustering" que unir recuperaría.
  3. *Cargadores compartidos* en las Etapas 3-4: menos colas de espera.

  Se reportan resultados **juntos y separados** (E2 vs E2b) para justificar con números si conviene
  unirlos. El profesor dijo que es válido y es decisión nuestra, siempre justificando.
- **Scripts:** `scripts/4-clustering_c1.py`, `5-clustering_c2.py`, `8-clustering_comparacion.py` ·
  **Salida:** `data-processed/rutas_cluster_*.csv`, `results/etapa1_clustering/` (tablas, gráficos y
  10 mapas).

### Etapa 2 — Asignación de buses por cluster (VSP) · estado: HECHA (escalera E0-E2b y LB corrida)

- **Qué decide.** Qué bus cubre qué expedición, y cuántos buses hacen falta. **Todavía sin batería**:
  eso lo corrige la Etapa 3.
- **Modelo.** Flujo de costo mínimo en red espacio-tiempo (Kliewer et al., 2006): un nodo por
  expedición, una línea de tiempo por electroterminal, arcos de espera, de deadhead entre
  expediciones (hasta el radio de interlining), de salida (pullout) y de retorno (pullin).

$$\min \sum_{a\in A_{out}} (c^{bus}+c^{km}\ell_a)x_a+\sum_{a\in A_{dh}\cup A_{in}} c^{km}\ell_a x_a+\sum_{a\in A_{wait}} c^{wait}\tau_a x_a$$

sujeto a que cada expedición sea cubierta exactamente una vez y a conservación de flujo en los nodos
de terminal. La matriz es de red (totalmente unimodular): **la relajación LP entrega solución
entera**, exacta y rápida (~40 s sobre toda la red).
- **Retorno al electroterminal [Profesor]:** en los modos `ruta` y `cluster` pullout y pullin usan el
  mismo electroterminal por construcción. El modo `libre` lo viola → es **cota inferior teórica
  (LB), no un escenario operacional**.
- **Modos:** `ruta` (sin interlining entre rutas) · `cluster` (interlining dentro del electroterminal,
  con opción de unir Los Espinos y Santa Rosa en un solo grupo) · `libre` (cota inferior). En `ruta` y
  `cluster` el electroterminal de cada ruta viene de la asignación de la Etapa 1 (`--asignacion`), y el
  script verifica que toda jornada vuelva a su electroterminal.
- **Resultados [Medido]** (red completa, 64.502 expediciones, factor 1,3, layover 3 min; el costo de
  operación es flota + km sin pasajeros + espera, sin energía):

  | Escenario | Buses | Costo de operación (USD/día) | vs. escalón anterior |
  |---|---|---|---|
  | E0 (sin interlining, C1b) | 8.654 | 2.311.988 | |
  | E1 (+ interlining) | 7.460 | 1.995.343 | −1.194 buses (−13,7%) |
  | E2 (C2) | 7.460 | 1.995.343 | idéntico a E1 |
  | E2b (+ Los Espinos y Santa Rosa unidos) | 7.366 | 1.970.265 | −94 buses (−1,3%) |
  | LB (cota inferior, no operacional) | 7.055 | 1.873.677 | −311 buses |

  E0 y LB reproducen exactamente la ronda anterior (8.654 y 7.055); E1 da 7.460 contra 7.456 con C1a.
  **E2 = E1** porque la asignación C2 coincide con C1b (la restricción agregada de capacidad no está
  activa). El interlining concentra el 75% de lo que separa a E0 de LB. LB viola el retorno: 4.192 de sus
  7.055 jornadas terminan en otro electroterminal. En E2b, 1.068 jornadas salen de un patio y vuelven al
  otro (1,1 km), lo que no viola el retorno porque es un solo electroterminal.
- **Sensibilidad del deadhead (sobre E1) [Medido]:** el factor de desvío (1,2 a 1,5) mueve la flota entre
  −0,8% y +0,7%; el layover (0 a 10 min) entre −2,7% y +6,0%. El 1,3 importa poco para el tamaño de la
  flota; el layover (3 min, sin calibrar) es el supuesto más sensible de la Etapa 2.
- **Script:** `scripts/6-vsp_asignacion_buses.py` (+ `7-comparar_escenarios.py`) · **Salida:**
  `data-processed/jornadas_{E0,E1,E2,E2b,LB}.csv`, `results/etapa2_vsp/`.

### Etapa 3 — Inserción de recargas · estado: POR CONSTRUIR

- **Qué decide.** Para cada jornada ya fija (secuencia de expediciones de un bus), en qué huecos
  recarga, en qué electroterminal y cuánto, respetando el ciclo diario y la capacidad de puestos.
- **Por qué hace falta.** **[Medido]** Con el ciclo diario, de 30% (nivel 100%) a 45% (90%) y 59% (80%) de las
  jornadas del caso base necesitan recargar **a mitad del día**, y de 39% a 76% con interlining.
  La jornada más cara consume 676 kWh contra 350 kWh de batería: **ningún nivel de SOC inicial evita
  la recarga intermedia**.
- **Para el caso base (E0, E1, E2): política reactiva**, implementada como simulador sobre las
  jornadas fijas. Reglas:
  1. El bus parte con `SOC_CICLICO`.
  2. Antes de una expedición, si no podría completarla y volver a su electroterminal sin bajar del
     mínimo (10%), debe cargar **antes**: va a su electroterminal, carga hasta `SOC_CICLICO` **sin
     mirar la tarifa**, y vuelve. Requiere un hueco ≥ traslado de ida + carga + traslado de vuelta +
     layover.
  3. **Sin hueco suficiente, la jornada se parte (+1 bus)** y se reporta cuántas veces ocurre. Es un
     resultado de la política miope, no un error.
  4. Si el electroterminal no tiene puesto libre, el bus espera (costo de espera). Si la espera lo
     atrasa para su siguiente expedición, se aplica la regla de partición.
  5. Al terminar la jornada vuelve al electroterminal y carga hasta `SOC_CICLICO` (condición
     cíclica). Si no alcanza a hacerlo antes de su primera salida del día siguiente, se registra
     como **ciclo no cumplido**.
- **Costo.** Energía por bloque tarifario del instante en que se carga, más 5 USD por evento de carga.
- **Script (a crear):** `scripts/10-carga_reactiva.py`.

### Etapa 4 — Programación de carga (MILP) · estado: POR CONSTRUIR (instancia chica)

- **Qué decide.** Dentro de las ventanas en que cada bus puede estar conectado, **cuánta energía
  carga en cada intervalo de 15 min**, minimizando el costo de la energía (tarifa por bloque) y de los
  eventos de carga, sin exceder los puestos del electroterminal.
- **Por qué un MILP.** Es el lugar donde viven a la vez la dimensión **temporal** (cuándo), la
  **tarifaria** (carga en valle) y la **capacidad** (puestos). La política reactiva no ve ninguna de
  las tres. Con holgura global de solo ~28% **[Medido, cota]**, programar la carga importa.
- **Formulación (un electroterminal).**
  Conjuntos: $B$ buses (jornadas) del electroterminal; $T$ intervalos de $\Delta$=0,25 h que cubren
  un ciclo; $W_b\subseteq T$ intervalos en que el bus $b$ está conectable (en el electroterminal,
  descontados los traslados).
  Parámetros: $P$=180 kW; $Cap$=350 kWh; $s^{min}$=0,10·$Cap$; $s^{c}$=`SOC_CICLICO`·$Cap$ (partida,
  llegada y tope); $p_t$ tarifa (USD/kWh); $c^{fix}$=5 USD; $\kappa$ puestos; $d_{bt}$ consumo del bus
  $b$ en el intervalo $t$ (kWh; 0 si está estacionado).
  Variables: $e_{bt}\ge0$ energía cargada; $y_{bt}\in\{0,1\}$ cargando; $z_{bt}\in\{0,1\}$ inicio de
  evento; $s_{bt}$ energía almacenada.

$$\min \sum_{b,t} p_t\,e_{bt}+c^{fix}\sum_{b,t} z_{bt}$$
$$\begin{aligned}
&e_{bt}\le P\Delta\,y_{bt}\;\;\forall b,t\in W_b, \qquad y_{bt}=0\;\;\forall t\notin W_b\\
&\textstyle\sum_{b} y_{bt}\le \kappa\;\;\forall t, \qquad z_{bt}\ge y_{bt}-y_{b,t-1}\\
&s_{b,t+1}=s_{bt}+e_{bt}-d_{bt}, \qquad s^{min}\le s_{bt}\le s^{c}\\
&s_{b,0}=s^{c}, \qquad s_{b,|T|}\ge s^{c}\quad\text{(ciclo diario)}
\end{aligned}$$

- **Alcance de esta entrega [Profesor]:** probarlo en **instancias pequeñas**, no en el modelo
  completo. La instancia se define por criterio (escala proporcional de puestos por bus, selección
  determinista, tamaño por tratabilidad, no trivialidad verificada); ver
  [`05_plan_entrega2.md`](05_plan_entrega2.md), Bloque E.
- **Qué optimiza y qué no.** Las ventanas $W_b$ vienen de la Etapa 3: el MILP optimiza **cuándo** y
  **cuánto** dentro de ellas; no inventa ventanas ni cambia la flota.
- **Orden de magnitud [Medido, estimación]:** ~2.150 MWh/día × tarifa entre 0,10 y 0,22 USD/kWh ⇒
  215.000-470.000 USD/día de energía. Esa es la banda en que puede moverse el costo energético según
  cuándo se cargue.
- **Script (a crear):** `scripts/11-milp_carga.py`.

---

## 5. Escalera de escenarios

Cada escenario cambia **una sola decisión** respecto del anterior, para medir su efecto marginal
(lo que el profesor pidió: "al prohibir el interlining vamos a obtener toda la ganancia luego por
habilitarlo; sirve para medir el efecto marginal de cada supuesto").

| id | Clustering | Interlining | Carga | Qué aísla |
|---|---|---|---|---|
| **E0** | C1b | No | Reactiva | **Caso base** (validado por el profesor) |
| **E1** | C1b | Sí, dentro del electroterminal | Reactiva | Efecto del interlining (el "segundo caso base" que sugirió el profesor) |
| **E2** | C2 | Sí | Reactiva | Efecto del clustering con capacidad |
| **E2b** | Como E2, con Los Espinos + Santa Rosa como **un solo electroterminal** (un grupo de interlining, cargadores compartidos) | Sí | Reactiva | Efecto de unir los dos terminales cercanos |
| **E3** | El mejor entre E2 y E2b | Sí | **Optimizada (MILP)** | Efecto de la carga inteligente |
| **LB** | — | Libre | — | Cota inferior teórica; viola el retorno al electroterminal |

**Expectativa a verificar, no a asumir.** (i) E1 debería mejorar fuertemente a E0 en flota (el
interlining concentra la ganancia). (ii) **E2 podría ser idéntico a E1** si la restricción agregada de
capacidad no se activa (ver Etapa 1): sería un resultado válido —la capacidad agregada no condiciona el
clustering— y la capacidad se manifestaría después, en las colas del simulador. (iii) E3 contra E2
mide el valor de programar la carga. Si algún resultado no sigue lo esperado, hay que explicar por
qué antes de seguir, no ajustar el modelo para que calce.

Esta escalera responde a la sugerencia del profesor de **aplicar el caso base una vez clusterizado**:
el costo de E1/E2 frente a E0 y LB dice qué tan buena o mala es la clusterización.

---

## 6. Caso base y KPIs

**Caso base [Profesor: "válido"] — "operación por línea + carga reactiva" (E0):** cada ruta usa solo
sus propios buses (sin interlining), despacho FIFO, electroterminal base = el más cercano (C1b), y
carga reactiva según las reglas de la Etapa 3. Es el estándar operacional intuitivo, simple de
explicar, y separa el valor de cada decisión.

**KPIs** (cada uno ligado a una decisión; se reportan para todos los escenarios):

| KPI | Definición | Decisión que evalúa |
|---|---|---|
| Costo total y desglose | Flota + km vacíos + espera + energía + cargas fijas | Todas (es el objetivo) |
| Nº de buses | Jornadas usadas; brecha frente a la cota 6.539 y a LB | Asignación / clustering |
| % de km vacíos | km (deadhead + pullout + pullin) / km totales | Encadenamiento y clustering |
| Costo medio de la energía y % cargado en valle | USD/kWh cargado; % de la energía en P1 y P6 | Programación de carga |
| Uso máximo de electroterminales | máx. de buses cargando / puestos, por electroterminal | Infraestructura |
| Utilización del bus | Horas con pasajeros / duración de la jornada | Calidad de las jornadas |
| Jornadas partidas y ciclos no cumplidos | Cuántas veces la política reactiva no pudo cargar | Cuánto cuesta la miopía |
| Precio de la descomposición | Buses y costo con clustering menos LB | Validez de la metodología |

---

## 7. Limitaciones conocidas (a declarar, no a esconder)

- **Deadhead euclidiano × 1,3.** Se espera crítica. Contrastado con trazados GTFS (script `9-`): es
  conservador para el interlining y, a escala de pullout/pullin, queda cerca del rodeo medido de
  las rutas, que es una cota superior. Puede subestimar algo el costo de pullout/pullin; se mide
  con la sensibilidad de la Etapa 2. Se mantiene para esta entrega.
- **Duración y distancia constantes por patrón**: las salidas de un mismo patrón duran lo mismo a
  cualquier hora (sin efecto de hora punta).
- **Consumo constante** (1,4 kWh/km): sin topografía ni congestión.
- **Carga lineal** a 180 kW: la fase final de una carga real es más lenta (curva CC-CV). El tope en
  `SOC_CICLICO` mantiene el modelo en la zona más fiel.
- **Buses por ruta estimados por concurrencia** (cota inferior) en la Etapa 1; **la capacidad de C2 es
  un promedio diario**, no ve la concentración horaria.
- **15 de las 300 rutas con ida y vuelta** tienen más de un paradero como inicio o fin de un mismo
  sentido; se usa el más frecuente.
- **Sin conductores ni turnos**; la oferta programada hace de demanda.
- **Un solo día** (laboral). El ciclo diario supone que el día siguiente es igual.

---

## 8. Mapa de scripts y archivos

| Etapa | Script | Entrada principal | Salida |
|---|---|---|---|
| Filtrado | `1-filtro_datos_buses.py`, `2-filtro_tipo_dia.py` | `data-alumnos/` | `data-filtrado/` |
| 0 | `3-preprocesamiento_expediciones.py` | `data-filtrado/` | `data-processed/{expediciones,terminales,rutas_resumen,rutas_ida_vuelta,terminales_por_ruta}.csv`, `results/etapa0_preprocesamiento/` |
| 1 | `4-clustering_c1.py` | tablas por ruta | `rutas_cluster_c1a.csv`, `rutas_cluster_c1b.csv` |
| 1 | `5-clustering_c2.py` | tablas por ruta | `rutas_cluster_c2.csv` (ciclo diario), tablas de capacidad, de evidencia del rechazo de SOC 100% y barrido de θ |
| 1 | `8-clustering_comparacion.py` | las 3 asignaciones (C1a, C1b, C2) | `rutas_clustering_completo.csv`, `results/etapa1_clustering/` |
| 2 | `6-vsp_asignacion_buses.py`, `7-comparar_escenarios.py` | expediciones + asignación | `jornadas_{E0,E1,E2,E2b,LB}.csv`, `results/etapa2_vsp/` |
| 3 | `10-carga_reactiva.py` | jornadas | eventos de carga, ocupación, costo *(a crear)* |
| 4 | `11-milp_carga.py` | ventanas de carga | programación óptima *(a crear)* |

Utilidades compartidas en `scripts/common/` (`parametros.py`, `geo.py`, `tiempo.py`, `rutas.py`,
`clustering.py`). `9-calibracion_deadhead.py` calibra el factor de desvío con los trazados GTFS
(salida en `results/etapa0_calibracion_deadhead/`). Los números 12 y 13 están reservados para la
comparación de KPIs y el análisis de recargas según el SOC (ver el plan). Cómo correr y verificar: [`03_guia_pruebas.md`](03_guia_pruebas.md).

---

## 9. Referencias

- Diagnóstico de la metodología del Informe 1, revisión de alternativas y bibliografía:
  [`../Propuesta_metodologia_reunion.md`](../Propuesta_metodologia_reunion.md). Algunos supuestos de ese
  documento (SOC 100%, capacidad holgada) quedaron superados; ver su encabezado.
- Kliewer, N., Mellouli, T., & Suhl, L. (2006). A time–space network based exact optimization model
  for multi-depot bus scheduling. *European Journal of Operational Research*, 175(3), 1616–1627.
- Verificar los datos bibliográficos exactos antes de citarlos en el informe.
