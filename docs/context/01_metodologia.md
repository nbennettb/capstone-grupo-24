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
| **Condición cíclica** (`SOC_CICLICO` es solo el nombre del nivel en estos textos; en el código es el argumento `--soc` y la grilla `SOC_CICLICO_BARRIDO`) | Todo bus **empieza y termina** el día con el mismo nivel `SOC_CICLICO` | **[Profesor]** pidió la condición (dejar batería para el día siguiente). Los 80-90% fueron un **ejemplo**. El **nivel** se busca con datos: se parte de 100% (máximo de `parameters.csv`) y se elige el que minimiza el costo total en un barrido 100-70%. **Resultado: 100%, con buses de reserva para cumplir el ciclo** (robusto en E0 y E1). Ver `02_supuestos_y_decisiones.md` B6 |
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

Tres criterios, cada uno cambia **un solo aspecto** respecto del anterior. **La asignación base de la entrega es
C1b** (en el relato se llama simplemente **C1**); C1a es un control de sensibilidad y C2 es la **propuesta**:

| | Qué decide | Rol en la entrega |
|---|---|---|
| **C1a** | Electroterminal más cercano al **centroide** de la ruta | Control: cambia 41 rutas y solo 0,7% del costo de pullout/pullin, así que la métrica de distancia importa poco. No la usa ninguna etapa posterior |
| **C1b = C1** | Más cercano a los **paraderos terminales reales** de la ruta, ponderados por uso | **Asignación base** (E0, E1) |
| **C2** | MILP de asignación con restricción de capacidad, misma distancia que C1b | **Propuesta**: formulada, probada y validada; fuera del caso base (ver `02`, B11) |

**Formulación de C2.**

$$\min \sum_{r\in R}\sum_{d\in D} c_{rd}\,x_{rd}\quad\text{s.a.}\quad \sum_{d} x_{rd}=1\;\;\forall r,\qquad \sum_{r} h_{rd}\,x_{rd}\le \theta\,\kappa_d H\;\;\forall d,\qquad x_{rd}\in\{0,1\}$$

- $c_{rd}=2\cdot\text{dist}_{rd}\cdot c^{km}\cdot n_r$: costo diario aproximado de pullout + pullin de la
  ruta $r$ si su base es $d$ (`dist` = distancia esperada a sus paraderos reales, con factor 1,3;
  $n_r$ = buses estimados).
- $h_{rd}$ = horas-cargador por día que la ruta $r$ demanda en el electroterminal $d$:
  $h_{rd}=\big(\text{kWh}_r + 2\cdot\text{dist}_{rd}\cdot n_r\cdot 1{,}4\big)/180$. **Bajo la condición cíclica
  se recarga todo lo consumido, y lo consumido incluye salir del electroterminal y volver** (pullout y
  pullin), con la misma distancia y el mismo $n_r$ que ya definen $c_{rd}$. Por eso la carga **depende del
  electroterminal**: mandar una ruta lejos no solo cuesta más km, también exige más carga ahí. Es un problema
  de asignación generalizada (GAP). Ambos lados de la restricción están en horas-cargador/día (el Informe 1
  mezclaba puestos simultáneos con expediciones/día). *(Corrección C7: antes $h_r$ era solo la energía
  comercial de la ruta, que subestimaba la carga 9-14%.)*
- $\kappa_d$ = puestos, $H$ = horas disponibles (24, **[Profesor]**), $\theta$ = holgura.

**Validación del estimador de carga [Medido].** Contra la energía real de las jornadas del VSP (E0 y E1, que
usan la asignación C1b), la energía comercial sola subestima 9-14% por electroterminal; el estimador con pullout
y pullin (fórmula de arriba) subestima solo 0,5-3,1% (el resto son los traslados entre viajes y la diferencia
entre buses estimados y reales). Detalle: `results/etapa1_clustering/tablas/validacion_carga_c2.csv` y
`docs/justificaciones/08_carga_real_en_clustering.md`.

**Resultados [Medido, θ = 1, H = 24]:**

| Electroterminal | Rutas C1a | Rutas C1b | Rutas C2 | Uso de capacidad con C1b | Uso de capacidad con C2 |
|---|---|---|---|---|---|
| Vespucio Norte | 59 | 56 | 56 | 33,7% | 33,7% |
| El Conquistador | 98 | 108 | 109 | 79,1% | 80,8% |
| Los Espinos | 85 | 88 | 83 | **101,6%** | **97,6%** |
| La Reina | 64 | 67 | 67 | 76,2% | 76,2% |
| Santa Rosa | 111 | 98 | 102 | 65,9% | 67,1% |

- **Con la carga corregida, la restricción de capacidad sí se activa:** la asignación C1b (la más cercana, sin
  capacidad) deja a Los Espinos al 101,6% y C2 mueve **5 rutas** (4 a Santa Rosa, a 1,1 km; 1 a El Conquistador)
  para respetarla. Cuesta casi nada (pullout/pullin 83.271 → 83.276 USD/día). Carga total: 11.760 h-cargador
  (70% de las 16.800) y 2.117 MWh. Con θ menor: 8 rutas movidas con θ = 0,9, 14 con 0,8 e infactible con 0,7
  (capacidad separada); con Los Espinos + Santa Rosa combinados, 5 rutas con θ = 1 y 0,9, 8 con 0,8 e infactible
  con 0,7.
- **C1a vs C1b:** cambian 41 de 417 rutas (10%), pero el costo aproximado de pullout/pullin mejora
  solo 0,7% (83.843 → 83.271 USD/día). El centroide es una simplificación casi inocua.
- **Límite de C2 que hay que entender:** su capacidad es un **promedio diario**. La carga real se
  concentra en ciertas horas, así que un electroterminal puede saturarse en las horas punta de carga
  aunque su promedio diario sea 70%. Esa saturación **no** la ve C2; la ve el simulador de la
  Etapa 3 como colas y déficit. **Medido:** con C2 sin unir (E1_C2_sep) Los Espinos usa 98,5% de su capacidad real (energía de las
  jornadas) y aun así el simulador reactivo deja 21 MWh sin reponer: respetar el 100% diario es **necesario,
  no suficiente** (ver `02`, C8).
- **Variante Los Espinos + Santa Rosa [Decisión, a implementar]:** están a solo 1,11 km entre sí (el
  resto de los pares a ≥ 5,9 km). La variante los trata como **un solo electroterminal de 270
  puestos** (los dos patios físicos se mantienen para las distancias). Tiene tres efectos, y solo uno
  se ve en la Etapa 1:
  1. *Capacidad combinada en C2.* **[Medido]** Con la carga corregida, Los Espinos separado queda al 97,6%
     y Santa Rosa al 67,1%; combinados, 81,8%: la bolsa de 270 puestos tiene holgura. Con θ = 0,8 la
     capacidad combinada sigue siendo factible.
  2. ***Un solo grupo de interlining* en la Etapa 2 (el efecto esperado).** Las 186 rutas (88 + 98 con C1b)
     pasan a poder encadenarse entre sí, lo que reduce buses (−94 en el VSP: E1_sep → E1).
  3. *Cargadores compartidos* en las Etapas 3-4: menos colas de espera.

  Se reportan resultados **juntos y separados** (E1_sep vs E1) para justificar con números si conviene
  unirlos. **Decisión:** todos los escenarios operacionales los unen (`02`, B11). El profesor dijo que es válido y es decisión
  nuestra, siempre justificando (`docs/justificaciones/05_unir_terminales.md`).
- **Scripts:** `scripts/4-clustering_c1.py`, `5-clustering_c2.py`, `8-clustering_comparacion.py` ·
  **Salida:** `data-processed/rutas_cluster_*.csv`, `results/etapa1_clustering/` (tablas, gráficos y
  10 mapas).

### Etapa 2 — Asignación de buses por cluster (VSP) · estado: HECHA (escalera E0-E1 y LB corrida)

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
  operación es flota + km sin pasajeros + espera, sin energía). Todos los escenarios operacionales usan **C1b** y
  tratan **Los Espinos y Santa Rosa como un solo electroterminal** (decisión B11, justificada por la carga: Etapa 3):

  | Escenario | Buses | Costo de operación (USD/día) | vs. escalón anterior |
  |---|---|---|---|
  | E0 (por línea, sin interlining, unidos) | 8.654 | 2.311.988 | |
  | E1 (+ interlining, unidos) | 7.366 | 1.970.265 | −1.288 buses (−14,9%) |
  | LB (cota inferior, no operacional) | 7.055 | 1.873.677 | −311 buses |
  | *Evidencia de la unión: E0_sep / E1_sep (separados)* | 8.654 / 7.460 | 2.311.988 / 1.995.343 | unir no cambia E0 y baja 94 buses en E1 |
  | *Variantes con C2 (propuesta): E1_C2 / E1_C2_sep* | 7.366 / 7.462 | 1.970.319 / 1.995.921 | +0 frente a E1; +2 frente a E1_sep |

  E0 y LB reproducen exactamente la ronda anterior (8.654 y 7.055). El interlining concentra el 81% de lo que separa
  a E0 de LB. LB viola el retorno: 4.192 de sus 7.055 jornadas terminan en otro electroterminal. En E1, 1.068
  jornadas salen de un patio y vuelven al otro (1,1 km), lo que no viola el retorno porque es un solo electroterminal.
  Unir no cambia el VSP de E0 (cada ruta encadena solo consigo misma): su efecto importante es en la carga. C2 mueve
  solo 5 rutas respecto de C1b, así que el VSP casi no cambia: el VSP no ve la capacidad.
- **Sensibilidad del deadhead (sobre E1) [Medido]:** el factor de desvío (1,2 a 1,5) mueve la flota entre
  −1,0% y +1,0%; el layover (0 a 10 min) entre −2,8% y +6,0%. El 1,3 importa poco para el tamaño de la
  flota; el layover (3 min, sin calibrar) es el supuesto más sensible de la Etapa 2.
- **Script:** `scripts/6-vsp_asignacion_buses.py` (+ `7-comparar_escenarios.py`) · **Salida:**
  `data-processed/jornadas_{E0,E1,LB,E0_sep,E1_sep,E1_C2,E1_C2_sep}.csv`, `results/etapa2_vsp/`.

### Etapa 3 — Inserción de recargas · estado: HECHA (simulador con buses de reserva y barrido de niveles; nivel base 100%)

- **Qué decide.** Para cada jornada ya fija (secuencia de expediciones de un bus), en qué huecos
  recarga, en qué electroterminal y cuánto, respetando la condición cíclica y la capacidad de puestos.
- **Por qué hace falta.** **[Medido]** Con la condición cíclica, de 30% (nivel 100%) a 45% (90%) y 59% (80%) de las
  jornadas del caso base necesitan recargar **a mitad del día**, y de 39% a 76% con interlining.
  La jornada más cara consume 676 kWh contra 350 kWh de batería: **ningún nivel de SOC inicial evita
  la recarga intermedia**.
- **Para el caso base (E0, E1 y las variantes): política reactiva**, implementada como simulador sobre las
  jornadas fijas (`scripts/10-carga_reactiva.py`). Reglas:
  1. El bus parte del electroterminal con el nivel de partida (`--soc`, base 100%), que es también el
     nivel de llegada y el tope de carga.
  2. Antes de una expedición, si no podría completarla y volver a su electroterminal sin bajar del
     mínimo (10%), debe cargar **antes**: va a su electroterminal (traslado de ida), carga **sin mirar la
     tarifa**, y vuelve con el layover de margen.
  3. **[Decisión] Carga parcial:** carga hasta el nivel **o hasta que se acabe el hueco**, lo que ocurra
     primero. Razón: un operador no partiría una jornada que puede continuar con una carga parcial, y la
     regla estricta (cargar completo o partir) favorecería artificialmente los niveles bajos en el
     barrido, porque su carga completa es más corta. Si ni así puede hacer la expedición y volver, **la
     jornada se parte**: el bus queda en el electroterminal (carga final) y un **bus nuevo** sale con el
     nivel completo a cubrir desde esa expedición (+1 bus). Se reporta el motivo: `sin_hueco` (el tiempo no
     alcanza aunque hubiera puesto libre) o `sin_puesto`.
  4. **Puestos:** se asignan en orden de llegada al electroterminal, al primer tramo continuo con puesto
     libre. Si no hay, el bus espera (0,03 USD/min). El terminal unido comparte sus 270 puestos.
  5. Al terminar la jornada vuelve al electroterminal y carga hasta el nivel. Si no termina antes de su
     primera salida del día siguiente, es un **ciclo no cumplido**. Si el electroterminal no tiene
     capacidad para reponer toda la energía, el faltante es un **déficit de energía** (la solución es infactible).
  6. **Periodicidad módulo 24 h:** la ocupación de puestos y la tarifa son circulares; una carga que cruza
     medianoche comparte puestos con las de la madrugada.
  7. **[Decisión] La condición cíclica es una restricción y se cumple con buses de reserva.** Un ciclo no cumplido
     se cubre con un **bus de reserva** ya cargado: en estado estacionario es una rotación (el bus atrasado termina
     de cargar, con atraso < 24 h, y es la reserva del día siguiente). Se necesitan tantas reservas como ciclos no
     cumplidos, a 250 USD/día cada una, y el costo total las incluye. Es una cota superior simple: lo que la carga
     no alcanza a reponer a tiempo se paga con flota. Una solución es **factible** si no tiene déficit de energía y
     todo atraso es menor a 24 h; con déficit, las reservas no la arreglan.
- **Costo.** Energía por bloque tarifario del minuto en que se carga (primer uso de `electricity_prices.csv`),
  más 5 USD por evento de carga, más los km de ir a cargar, la espera en cola y las reservas.
- **Cota de factibilidad (LP) [Medido].** Para cada nivel se calcula el máximo de energía de las cargas finales que
  cabe dentro de la ventana de cada bus (llegada al patio hasta su primera salida del día siguiente), dados los
  puestos y repartiendo la carga de la **mejor forma posible** (LP con bloques de 15 min, módulo 24 h). Si es menor
  a 100%, ningún programa de carga cierra el ciclo con esas jornadas.
- **Validación [Medido].** Antes de simular, cada jornada se reconstruye sin cargas y calza con el VSP (kWh por
  jornada y espera total: 25.099,3 h en E0, 20.749,1 h en E1, idénticas a las del VSP). Después: cobertura intacta,
  SOC entre el mínimo y el tope, ocupación ≤ puestos y balance de energía por jornada (cargado + déficit = consumido).
- **Resultados al nivel 100% [Medido]** (red completa; todos con C1b salvo las variantes C2):

  | | **E0** (por línea, unidos) | **E1** (+ interlining, unidos) | *E0_sep* | *E1_sep* | *E1_C2* | *E1_C2_sep* |
  |---|---|---|---|---|---|---|
  | Buses del VSP → tras la carga | 8.654 → 11.259 | 7.366 → **10.295** | 8.654 → 11.259 | 7.460 → 10.415 | 7.366 → 10.258 | 7.462 → 10.343 |
  | Jornadas partidas | 2.605 | 2.929 | 2.605 | 2.955 | 2.892 | 2.881 |
  | Ciclos no cumplidos = buses de reserva | 1.988 | 2.207 | 2.357 | 2.518 | 2.204 | 2.363 |
  | Déficit de energía (no hay puestos) | **0** | **0** | 48,2 MWh | 44,1 MWh | 0 | 21,3 MWh |
  | Cota LP: % de la carga final que cabe | 89,5% | 84,0% | 89,4% | 84,4% | 84,0% | 84,3% |
  | Costo sin reservas (USD/día) | 3.461.063 | 3.199.500 | 3.446.972 | 3.219.970 | 3.189.069 | 3.208.806 |
  | Costo de las reservas (USD/día) | 497.000 | 551.750 | 589.250 | 629.500 | 551.000 | 590.750 |
  | **Costo total (USD/día)** | **3.958.063** | **3.751.250** | 4.036.222 | 3.849.470 | 3.740.069 | 3.799.556 |
  | **Factible** | **sí** | **sí** | no | no | sí | no |

  *Los escenarios `_sep` y `E1_C2_sep` (terminales separados) son infactibles: son la evidencia de por qué se unen.
  E1_C2 es la variante con C2 (propuesta); con la unión mejora el costo total solo 0,3% frente a E1.*
- **Lectura.**
  - **La política reactiva casi no recarga a mitad del día: parte la jornada.** Los huecos entre expediciones
    de las jornadas largas son cortos (mediana 12,7 min; solo 3% supera 70 min) y ir al electroterminal
    (~10 km a 20 km/h) y volver cuesta ~63 min. Casi toda jornada que supera la batería se parte: la flota
    sube 30% en E0 (+2.605 buses, +651.250 USD/día) y 40% en E1. **El VSP que minimiza la flota ignorando la
    batería produce jornadas que no se pueden recargar:** es el precio de la descomposición secuencial.
  - **La carga nocturna no cabe y el ciclo se paga con reservas.** Casi todos los buses vuelven al patio entre las
    19:00 y las 02:00 y la capacidad de puestos no alcanza en esas horas: 21% de las cargas finales de E1 termina
    después de la primera salida del día siguiente (atraso mediano 3,2 h). **La cota LP lo confirma:** con una carga
    perfecta solo cabe el **84%** de la energía nocturna de E1 (faltan 354 MWh/día) y el 89,5% en E0; ningún programa
    de carga, ni el MILP, cierra el ciclo con estas jornadas al 100%. No es el orden de la cola (cargar primero al
    que sale antes baja los incumplimientos solo de 2.199 a 2.160). El 73% de uso diario promedio de los puestos
    lo ocultaba, porque los buses solo están en el patio de noche. *(Esto refuta la cota "139% de holgura" de B6,
    que no miraba a qué hora está cada bus en el patio.)*
  - **Capacidad y unión (ver `02`, C7, C8 y B11):** sin unir, Los Espinos necesita 104% (E0) y 102,6% (E1) de su
    capacidad de 24 h y queda con déficit de 44-48 MWh: infactible, y ni las reservas ni bajar el nivel lo arreglan.
    Unido a Santa Rosa necesita 82,5% y el déficit es 0.
- **Barrido de niveles [Medido]** (`scripts/13-barrido_niveles.py`; regla corregida en `02`, B6, la condición cíclica
  como restricción). En E1, política reactiva (USD/día; reservas = ciclos no cumplidos; `n.c.` = cota LP no calculada):

  | Nivel | Buses tras la carga | Reservas | Cota LP | Costo total (con reservas) | vs. 100% | Factible |
  |---|---|---|---|---|---|---|
  | **100%** | 10.295 | 2.207 | 84,0% | **3.751.250** | | sí |
  | 90% | 11.791 | 1.417 | 95,5% | 3.973.783 | +5,9% | sí |
  | 80% | 13.267 | 246 | 100% | 4.069.352 | +8,5% | sí |
  | 70% | 14.747 | 73 | 100% | 4.424.005 | +17,9% | sí |
  | 65% | 15.936 | 50 | 100% | 4.737.923 | +26,3% | sí |
  | 60% | 17.717 | 20 | n.c. | 5.206.564 | +38,8% | sí |
  | 55% | 19.671 | 13 | n.c. | 5.732.581 | +52,8% | sí |
  | 50% | 22.549 | 274 (déficit 25,3 MWh) | n.c. | 6.573.732 | | **no** |

  **El nivel base es 100%** (con reservas) y E0 elige lo mismo (robusto). Hallazgos: (1) **ningún nivel entre 100% y
  55% cierra el ciclo sin reservas** con la política reactiva; el que más se acerca (55%) deja 13 reservas pero
  cuesta 52,8% más; (2) **la cota LP dice que con una carga perfecta el ciclo sí sería posible desde 80% hacia
  abajo**, pero esa solución costaría ≥ 4,0 M USD/día (sin reservas), más que 100% con reservas (3,75 M); (3) bajar
  el nivel no "arregla" el ciclo: lo paga con flota (cada 10 puntos menos agregan ~1.500 buses); (4) el 50% (piso
  físico) ya es infactible por déficit. Detalle: `docs/justificaciones/04_nivel_carga_ciclico.md` y
  `results/etapa3_carga_reactiva/barrido/`.
- **Para el MILP (Etapa 4):** con las ventanas fijas de estas jornadas la restricción cíclica es infactible al 100%
  (la cota LP es 84%). El MILP debe poder usar reservas, o ventanas de carga de día, o será infactible; su valor está en
  reducir las reservas y el costo de la energía, no en cerrar el ciclo por sí solo.
- **Script:** `scripts/10-carga_reactiva.py` (+ `13-barrido_niveles.py`) · **Salida:** `results/etapa3_carga_reactiva/`
  (eventos, ventanas, jornadas, ocupación, `resumen_carga.csv` y `barrido/`). Las `ventanas` son el insumo del MILP.

### Etapa 4 — Programación de carga (MILP) · estado: HECHA en instancia reducida (N = 10 a 400 buses; óptimo certificado solo en N = 10, brecha 1,4-8,6% en las demás)

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
- **Formulación implementada (por ventanas, ver `02`, B12).** Se resuelven las 24 h de una vez; los 96 bloques de 15 min son solo la
  unidad de medida del tiempo (no hay descomposición temporal). Por bus: `Σ_t e_bt = E_b` (vuelve exactamente al nivel),
  `e_bt ≤ q y_bt` (q = 45 kWh), `y_bt ≤ r_b` fuera de su ventana en el patio, puestos `Σ_b y_bt ≤ κ − f_t` (módulo 24 h), `z_bt ≥ y_bt −
  y_b,t−1`, y evento continuo a plena potencia (`e_bt ≥ q (y_bt + y_b,t+1 − 1)`) y al menos un evento por bus (`Σ_t z_bt ≥ 1`). **`r_b` es el bus de reserva** (250 USD): puede
  terminar de cargar hasta 24 h desde su llegada, y su salida la cubre otro bus; es la regla del simulador y hace el modelo siempre
  factible. Objetivo: tarifa × energía + 5 USD × eventos + 250 USD × reservas. Las cargas intermedias (0,5% de los buses) quedan fijas.
- **Instancia reducida (rotularla siempre así, no es el resultado de toda la red).** Terminal unido Los Espinos + Santa Rosa en E1 al
  100%; muestra de jornadas del VSP con semilla fija (24) y anidada; puestos = N × 270 / 4.622 (0,0584 por bus). Representativa
  [Medido]: carga/capacidad 80-89% (red 86%), 91-95% de las llegadas entre 19:00 y 02:00 (red 90%), USD/kWh 0,137-0,145 (red 0,142), reservas de
  la reactiva 12-27% (red 26%); puestos saturados en 82-96% de los bloques (no trivial).
- **Resultado [Medido]** (costo de la carga = energía + eventos + reservas; ganancia frente al simulador real, al minuto, es una
  cota inferior porque el MILP usa bloques de 15 min):

  | N (buses) | Puestos | Costo de la carga: simulador → MILP (USD/día en la instancia) | Ganancia | Reservas: simulador → MILP (cota) | Brecha en 600 s |
  |---|---|---|---|---|---|
  | 9 (N=10) | 1 | 283 → 253 | ≥ 10,5% | 0 → 0 (0) | 0,26%: **óptimo** (2,6 s) |
  | 34 (N=30) | 2 | 2.115 → 1.612 | ≥ 23,8% | 4 → 2 (1) | 1,4% |
  | 55 (N=50) | 3 | 4.947 → 4.199 | ≥ 15,1% | 12 → 9 (8) | 2,0% |
  | 106 (N=100) | 6 | 9.519 → 8.507 | ≥ 10,6% | 23 → 19 (15) | 2,7% |
  | 210 (N=200) | 12 | 19.532 → 17.294 | ≥ 11,5% | 48 → 39 (32) | 1,9% |
  | 404 (N=400) | 23 | 41.573 → 35.608 | ≥ 14,3% | 107 → 82 (68) | 8,6% |

  Lectura: (1) el MILP **siempre cuesta menos que la reactiva en bloques** (prueba de correctitud) y menos que el simulador real, y su programa **se ejecuta al minuto** respetando los
  puestos y con las mismas reservas; (2) **a escala, la ganancia viene de las reservas, no de la tarifa**: el costo medio de la energía casi no cambia (0,1445 → 0,1443 USD/kWh en N=400); el MILP usa los
  puestos que la reactiva deja ociosos entre las 16:00 y las 19:00 para cargar buses que de otro modo exigirían reserva. En N=10, donde no hay reservas, la ganancia sí es de tarifa (0,1235 → 0,1081 USD/kWh); (3) **certificado de reservas**: ningún programa
  de carga puede tener menos de 1 / 8 / 15 / 32 / 68 reservas (N = 30 a 400); el MILP logra 2 / 9 / 19 / 39 / 82, es decir, está a 1-14 reservas del mínimo posible y recorre 2/3 del potencial en N=400 (107 → 82 de un piso de 68);
  (4) solo N=10 certifica el óptimo (brecha ≤ 1%); en las demás la brecha es 1,4-8,6% y crece con N, y esa es la evidencia de por qué no se corre sobre los 4.622 buses; (5) la grilla de 15 min **no es inocua**: la misma regla reactiva en bloques deja 21-50% más reservas que el simulador
  al minuto, por eso la referencia es el simulador (`02`, C11). **No se extrapola a toda la red**: E3 solo se estima.
- **Script:** `scripts/11-milp_carga.py` · **Salida:** `results/etapa4_milp_carga/` (instancias, comparación, tiempos, representatividad, programas
  por bus, ocupación, energía por tarifa y 8 gráficos; `reporte.md`).

---

## 5. Escalera de escenarios

Cada escenario cambia **una sola decisión** respecto del anterior, para medir su efecto marginal
(lo que el profesor pidió: "al prohibir el interlining vamos a obtener toda la ganancia luego por
habilitarlo; sirve para medir el efecto marginal de cada supuesto").

Todos los escenarios operacionales usan **C1b** y tratan **Los Espinos y Santa Rosa como un solo electroterminal**
(la unión es parte de la infraestructura: sin ella el caso base es infactible en energía; ver `02`, B11).

| id | Interlining | Terminales | Carga | Qué aísla |
|---|---|---|---|---|
| **E0** | No (por línea) | Unidos | Reactiva + reservas | **Caso base** (operación por línea + carga reactiva, factible) |
| **E1** | Sí, dentro del electroterminal | Unidos | Reactiva + reservas | Efecto del interlining (el "segundo caso base" que sugirió el profesor; configuración propuesta) |
| **E3** | Sí | Unidos | **Optimizada (MILP)** | Efecto de la carga inteligente (sobre E1) |
| **LB** | Libre | — | — | Cota inferior teórica; viola el retorno al electroterminal |
| *E0_sep, E1_sep* | Como E0 y E1 | **Separados** | Reactiva | **Evidencia de por qué se unen:** infactibles (déficit de energía 44-48 MWh) |
| *E1_C2, E1_C2_sep* | Sí | Unidos / separados | Reactiva | Variantes con la asignación C2 (propuesta): no son parte de la escalera |

**Expectativa a verificar, no a asumir.** (i) E1 debería mejorar fuertemente a E0 en flota (el interlining concentra la
ganancia). **Resultado:** −1.288 buses en el VSP y −207.000 USD/día de costo total con carga (3.958.063 → 3.751.250). (ii) **Unir los terminales
debería eliminar el déficit de carga de Los Espinos.** **Resultado:** déficit 44-48 MWh → 0; el VSP baja 94 buses en
E1. (iii) **El ciclo debería poder cumplirse.** **Resultado:** no con la política reactiva a ningún nivel evaluado: se
cumple pagando buses de reserva (2.207 en E1), y la cota LP muestra que al 100% ni una carga perfecta lo cerraría.
(iv) E3 contra E1 mide el valor de programar la carga. **Resultado (iv), a escala de instancia:** el MILP baja el costo de la carga al menos 10-24% frente al simulador reactivo (según el tamaño de la instancia; cota inferior, brecha 1,4-8,6% salvo N=10, que es óptimo), casi todo por menos buses de reserva. Si algún resultado no sigue lo esperado, hay que explicar por
qué antes de seguir, no ajustar el modelo para que calce.

Esta escalera responde a la sugerencia del profesor de **aplicar el caso base una vez clusterizado**:
el costo de E1 frente a E0 y LB dice qué tan buena o mala es la clusterización.

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
| 2 | `6-vsp_asignacion_buses.py`, `7-comparar_escenarios.py` | expediciones + asignación | `jornadas_{E0,E1,LB,E0_sep,E1_sep,E1_C2,E1_C2_sep}.csv`, `results/etapa2_vsp/` |
| 3 | `10-carga_reactiva.py` | jornadas del VSP | `results/etapa3_carga_reactiva/` (eventos, ventanas, jornadas, ocupación, resumen) |
| 4 | `11-milp_carga.py` | jornadas del VSP + simulador de la Etapa 3 | `results/etapa4_milp_carga/` (instancia reducida: programa por bus, comparación con la reactiva, tiempos) |

Utilidades compartidas en `scripts/common/` (`parametros.py`, `geo.py`, `tiempo.py`, `rutas.py`,
`clustering.py`). `9-calibracion_deadhead.py` calibra el factor de desvío con los trazados GTFS
(salida en `results/etapa0_calibracion_deadhead/`). `13-barrido_niveles.py` aplica la regla de B6 y elige el nivel
de batería. El número 12 está reservado para la comparación de KPIs (ver el plan). Cómo correr y verificar: [`03_guia_pruebas.md`](03_guia_pruebas.md).

---

## 9. Referencias

- Diagnóstico de la metodología del Informe 1, revisión de alternativas y bibliografía:
  [`../Propuesta_metodologia_reunion.md`](../Propuesta_metodologia_reunion.md). Algunos supuestos de ese
  documento (SOC 100%, capacidad holgada) quedaron superados; ver su encabezado.
- Kliewer, N., Mellouli, T., & Suhl, L. (2006). A time–space network based exact optimization model
  for multi-depot bus scheduling. *European Journal of Operational Research*, 175(3), 1616–1627.
- Verificar los datos bibliográficos exactos antes de citarlos en el informe.
