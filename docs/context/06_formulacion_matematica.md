# Formulación matemática del problema

> Documento dedicado solo a los modelos: qué decide cada uno, su formulación completa, qué significa cada restricción y por qué
> está ahí. Los resultados están en [`01_metodologia.md`](01_metodologia.md) y las decisiones con su respaldo en
> [`02_supuestos_y_decisiones.md`](02_supuestos_y_decisiones.md). Cada supuesto lleva su origen: **[Profesor]**, **[Dato]**,
> **[Medido]** o **[Propio]**. La formulación describe lo que hace el código (se indica el script de cada modelo).

---

## 0. El problema completo, en una frase y en símbolos

Para un día laboral, asignar cada uno de los 64.502 viajes programados a un bus eléctrico y decidir cuándo y dónde carga cada
bus, minimizando

$$\text{costo total} = \underbrace{250\cdot(\text{buses} + \text{reservas})}_{\text{flota}} + \underbrace{0{,}5\cdot \text{km vacíos}}_{\text{deadhead}} + \underbrace{0{,}03\cdot \text{min de espera}}_{\text{espera}} + \underbrace{\textstyle\sum p_t\, e_t}_{\text{energía}} + \underbrace{5\cdot \text{eventos de carga}}_{\text{cargas}} \quad [\text{USD/día}]$$

sujeto a que (i) cada viaje se cubra exactamente una vez, (ii) cada bus salga y vuelva a su electroterminal **[Profesor]**, (iii) la batería nunca
baje del 10%, (iv) no haya más buses cargando que puestos en cada electroterminal, y (v) cada bus termine el día con la misma batería con que lo empezó
(**condición cíclica [Profesor]**).

Resolver todo junto es un E-VSP integrado, intratable a esta escala. Se descompone **por tipo de decisión** en cuatro modelos encadenados:

| Etapa | Modelo | Decide | Tipo |
|---|---|---|---|
| 1 | Asignación de rutas a electroterminales (C1 heurística; C2 MILP) | El electroterminal base de cada ruta | Heurística / asignación generalizada |
| 2 | VSP en red espacio-tiempo | Qué bus hace qué viaje (jornadas) | Flujo de costo mínimo (LP con solución entera) |
| 3 | Política de carga reactiva (caso base) | Cuándo y dónde carga cada bus, de forma miope | Simulación por eventos |
| 4 | MILP de programación de carga | Cuándo y cuánto carga cada bus, mirando tarifa y puestos | MILP (instancia reducida) |

Cada etapa recibe la salida de la anterior **como dato fijo**. El costo de esa decisión se mide con cotas: LB en la Etapa 2, la cota LP en la Etapa 3
y el piso de reservas en la Etapa 4.

---

## 1. Notación común

| Símbolo | Significado | Valor | Origen |
|---|---|---|---|
| $V$ | Viajes (expediciones) del día, cada uno con hora de salida $a_v$, de llegada $b_v$, paraderos de origen y destino, km y energía $\epsilon_v$ | 64.502 | [Dato] GTFS expandido |
| $R$ | Rutas | 417 | [Dato] |
| $D$ | Electroterminales (depósitos); Los Espinos y Santa Rosa se tratan como uno | 5 → 4 terminales | [Dato] + [Propio] |
| $\kappa_d$ | Puestos de carga del electroterminal $d$ | 150 / 180 / 120 / 100 / 150 (270 unidos) | [Dato] |
| $C$ | Capacidad de batería | 350 kWh | [Dato] |
| $s^{min}$ | Batería mínima | 10% = 35 kWh | [Dato] |
| $L$ | Nivel cíclico: de partida, de llegada y tope de carga | 100% = 350 kWh | [Medido] barrido 100-50% |
| $P$ | Potencia de carga | 180 kW (3 kWh/min) | [Dato] |
| $\rho$ | Consumo | 1,4 kWh/km | [Dato] |
| $c^{bus}, c^{km}, c^{wait}, c^{fix}$ | Costo por bus-día, por km vacío, por minuto de espera, por evento de carga | 250 / 0,5 / 0,03 / 5 USD | [Dato] |
| $p_t$ | Tarifa eléctrica en el instante $t$ | 0,10 / 0,15 / 0,22 / 0,15 / 0,22 / 0,11 USD/kWh | [Dato] |
| $\ell(i,j)$ | Distancia de un traslado vacío: línea recta × 1,3 | — | [Propio], respaldado [Medido] |
| $\tau(i,j)$ | Tiempo de ese traslado: $\ell/20$ km/h | — | [Propio] |
| $\lambda$ | Layover mínimo entre actividades | 3 min | [Propio] |
| $r^{max}$ | Radio máximo de interlining (sobre $\ell$) | 3 km | [Propio], sensibilidad [Medido] |

---

## 2. Etapa 1 — Asignación de rutas a electroterminales

**Qué decide.** El electroterminal base de cada ruta, que es desde donde salen y adonde vuelven sus buses y donde cargan. Convierte un problema de
5 depósitos en problemas de un depósito.

**Por qué rutas y no viajes [Medido].** El 94,7% de las rutas termina la ida a menos de 500 m de donde empieza la vuelta. Asignar viajes sueltos
rompería ese encadenamiento natural.

### 2.1 C1 (asignación base): heurística del más cercano

$$d(r) = \arg\min_{d\in D} \; \bar\ell_{rd},\qquad \bar\ell_{rd} = \sum_{k\in T_r} w_{rk}\, \ell(k, d)$$

donde $T_r$ son los paraderos terminales reales de la ruta $r$ y $w_{rk}$ la fracción de sus viajes que empieza o termina en $k$. *En palabras:* cada
ruta va al electroterminal más cercano a donde sus buses de verdad empiezan y terminan. **Por qué no el centroide:** el centroide (C1a) cambia 41 rutas
pero solo 0,7% del costo de pullout/pullin; se usan los paraderos reales porque son lo que el bus recorre.

### 2.2 C2 (propuesta): asignación generalizada con capacidad de carga

**Variables:** $x_{rd}\in\{0,1\}$ vale 1 si la ruta $r$ se asigna al electroterminal $d$.

$$\min \sum_{r\in R}\sum_{d\in D} c_{rd}\,x_{rd}$$

$$\text{s.a.}\quad \sum_{d\in D} x_{rd} = 1 \quad \forall r \qquad \text{(1) cada ruta tiene exactamente un electroterminal}$$

$$\sum_{r\in R} h_{rd}\,x_{rd} \le \theta\,\kappa_d\,H \quad \forall d \qquad \text{(2) la carga diaria asignada cabe en sus puestos}$$

| Parámetro | Fórmula | Significado |
|---|---|---|
| $c_{rd}$ | $2\,\bar\ell_{rd}\,c^{km}\,n_r$ | Costo diario de salir y volver al electroterminal: ida y vuelta × km × buses de la ruta |
| $n_r$ | Máximo de viajes simultáneos de la ruta | Buses estimados (cota inferior; solo pondera) |
| $h_{rd}$ | $(\text{kWh}_r + 2\,\bar\ell_{rd}\,n_r\,\rho)/P$ | Horas-cargador que la ruta exige en $d$: su energía comercial más la de salir y volver |
| $H$ | 24 h | El electroterminal puede cargar todo el día **[Profesor]** |
| $\theta$ | 1 (sensibilidad 0,9-0,7) | Holgura de capacidad **[Propio]**, sin calibrar |

**Por qué cada pieza:**
- **(1)** es la definición de asignación.
- **(2)** es la razón de existir de C2: que ningún electroterminal reciba más carga de la que sus puestos pueden reponer en 24 h. Ambos lados están en
  horas-cargador por día (el Informe 1 mezclaba unidades).
- **$h_{rd}$ depende de $d$:** mandar una ruta lejos no solo cuesta más km, también exige más energía ahí. Por eso es una asignación generalizada (GAP)
  y no un problema de transporte. La energía de salir y volver se agregó al medir que solo la comercial subestimaba la carga real 9-14% **[Medido]**.

**Límite.** (2) es un **promedio diario**: no ve que la carga se concentra de noche. Respetarla es necesario, no suficiente: con C2 sin unir terminales,
Los Espinos usa 98,5% de su capacidad y aun así quedan 21 MWh sin reponer. Por eso C2 queda como propuesta y la base es C1 con los terminales unidos.

*Script:* `scripts/4-clustering_c1.py` (C1), `scripts/5-clustering_c2.py` (C2, Gurobi).

---

## 3. Etapa 2 — Asignación de buses a viajes (VSP en red espacio-tiempo)

**Qué decide.** Qué secuencia de viajes hace cada bus (su **jornada**) y cuántos buses hacen falta. **Sin batería:** esa restricción la agrega la Etapa 3.

### 3.1 La red

Un bus es una **unidad de flujo** que sale de una fuente (el electroterminal), recorre viajes y vuelve a un sumidero (el electroterminal).

| Elemento | Qué representa |
|---|---|
| Nodo $v$ por cada viaje | El viaje debe ser recorrido por exactamente un bus |
| **Línea de tiempo** por (paradero, grupo): eventos ordenados en el tiempo | Un "andén virtual" donde los buses esperan entre viajes. El grupo es la ruta (E0), el electroterminal (E1) o uno solo (LB) |
| Arco de **llegada** $v\to$ línea de tiempo del paradero $k$ | El bus termina $v$ y se traslada vacío a $k$; llega en $b_v + \lambda + \tau(\text{destino}_v, k)$. Solo si $\ell \le r^{max}$ |
| Arco de **espera** entre eventos consecutivos de una línea de tiempo | El bus espera en el paradero |
| Arco de **salida** línea de tiempo → viaje $w$ | El bus toma el viaje $w$ que sale de ese paradero |
| Arco de **pullout** fuente $\to v$ | Un bus nuevo sale de su electroterminal a hacer $v$ (cuesta un bus) |
| Arco de **pullin** $v\to$ sumidero | El bus termina su jornada y vuelve a su electroterminal |

### 3.2 Formulación

**Variables:** $x_a \ge 0$, el flujo (número de buses) por cada arco $a$.

$$\min \sum_{a\in A_{out}} \big(c^{bus} + c^{km}\,\ell_a\big)\,x_a + \sum_{a\in A_{dh}\cup A_{in}} c^{km}\,\ell_a\,x_a + \sum_{a\in A_{wait}} c^{wait}\,\tau_a\,x_a$$

$$\sum_{a\in\delta^{-}(v)} x_a = 1 \quad\text{y}\quad \sum_{a\in\delta^{+}(v)} x_a = 1 \qquad \forall v\in V \qquad \text{(3) cada viaje: exactamente un bus entra y uno sale}$$

$$\sum_{a\in\delta^{-}(u)} x_a = \sum_{a\in\delta^{+}(u)} x_a \qquad \forall u \text{ evento de una línea de tiempo} \qquad \text{(4) conservación de flujo}$$

$$x_a \ge 0 \qquad \text{(5)}$$

| Término | Significado |
|---|---|
| $A_{out}$ (pullout) | Cada unidad de flujo que sale es un bus: paga 250 USD más los km hasta el primer viaje. **Buses $=\sum_{a\in A_{out}} x_a$** |
| $A_{dh}$, $A_{in}$ | Km vacíos de traslado entre viajes (interlining) y de vuelta al electroterminal |
| $A_{wait}$ | Minutos esperando entre viajes |

**Por qué cada pieza:**
- **(3)** es la cobertura: ningún viaje queda sin bus y ninguno lo hacen dos buses.
- **(4)** dice que un bus que llega a un paradero o sale de él, o espera ahí; no aparece ni desaparece.
- El arco de llegada solo existe si el bus **alcanza** a trasladarse antes de que salga el siguiente viaje (el orden en el tiempo de la línea lo garantiza)
  y si el traslado mide hasta $r^{max}$.
- **El retorno [Profesor]** está garantizado por construcción: en E0 y E1 el pullout y el pullin de una jornada usan el electroterminal de su ruta o grupo, y el
  script lo verifica. LB permite volver a cualquiera, y por eso es solo una cota.
- **Por qué no hace falta declarar variables enteras:** la matriz de (3)-(5) es la de una red de flujo, que es **totalmente unimodular**. Todo vértice del LP
  es entero, así que el LP entrega directamente un número entero de buses por arco. El óptimo es exacto y se obtiene en 5-55 s por escenario.

**Qué no ve.** La batería: produce jornadas que consumen hasta 676 kWh (la batería tiene 350). Eso lo corrige la Etapa 3, y su costo es el hallazgo
central (C9 en `02`).

*Script:* `scripts/6-vsp_asignacion_buses.py` (Gurobi, LP). *Nota:* en `01` se describe "una línea de tiempo por electroterminal"; en el código las
líneas de tiempo son por paradero y grupo, y la fuente y el sumidero representan el electroterminal. Es la red de Kliewer et al. (2006), adaptada.

---

## 4. Etapa 3 — Política de carga reactiva (caso base)

**Qué decide.** Para cada jornada fija, cuándo y dónde recarga, respetando batería y puestos. **No es un modelo de optimización:** es una
**política miope** (cada bus carga cuando lo necesita, sin mirar tarifa ni futuro) que se simula por eventos. Es el caso base contra el que se mide el MILP.

**Estado de un bus:** batería $s$, posición en su jornada, hora. **Reglas** (en orden):

1. **Partida.** El bus sale de su electroterminal con $s = L$.
2. **Antes de cada viaje $v$:** si $s - \rho\,\ell(\cdot, v) - \epsilon_v - \rho\,\ell(v, d) < s^{min}$ (no podría hacer $v$ y volver), va a cargar: viaja a su electroterminal $d$,
   espera un puesto si no hay y carga a potencia $P$ hasta $L$ **o hasta que se acabe el hueco** (carga parcial), y vuelve con margen $\lambda$.
3. **Si ni así alcanza, la jornada se parte:** el bus se queda cargando y un **bus nuevo** cubre desde $v$ (+1 bus).
4. **Puestos:** se asignan por orden de llegada; nunca más de $\kappa_d$ buses cargando a la vez (ocupación módulo 24 h).
5. **Fin de jornada:** vuelve y carga hasta $L$. Si no termina antes de su primera salida del día siguiente, el ciclo **no se cumple**.
6. **Bus de reserva:** cada ciclo no cumplido se cubre con un bus ya cargado (250 USD/día). En estado estacionario es una rotación: el bus atrasado termina de
   cargar (atraso menor a 24 h) y es la reserva del día siguiente.

**Costo:** energía $\sum_t p_t\, e_t$ por minuto efectivamente cargado, más 5 USD por evento, más los km para ir a cargar, la espera y las reservas.

**Por qué esta política:**
- Es lo que haría un operador sin optimizar, y el profesor la validó como caso base.
- La carga parcial evita partir jornadas que pueden seguir; además, la regla estricta favorecería artificialmente los niveles bajos en el barrido.
- Las reservas hacen que la condición cíclica sea una **restricción cumplida**, no un indicador.

### 4.1 Cota LP de la carga nocturna (¿algún programa podría cerrar el ciclo?)

Con las ventanas reales $[\text{llegada}_b, \text{salida}_b]$ de cada bus y bloques de 15 min:

$$\max \sum_{b,t} e_{bt} \quad\text{s.a.}\quad \sum_t e_{bt}\le E_b\;\;\forall b,\qquad \sum_b e_{bt}\le q\,(\kappa - f_t)\;\;\forall t,\qquad 0\le e_{bt}\le q,\;\; e_{bt}=0 \text{ fuera de la ventana}$$

($q = 45$ kWh por puesto y bloque; $f_t$ = cargas intermedias fijas). *En palabras:* repartiendo la carga de la mejor forma posible, ¿cuánta energía de las
cargas finales cabe a tiempo? **Resultado [Medido]:** 84% en E1 y 89,5% en E0. Ningún programa de carga, ni el MILP, cierra el ciclo al 100% con estas jornadas.

*Script:* `scripts/10-carga_reactiva.py` (simulador; cota LP con scipy/HiGHS).

---

## 5. Etapa 4 — MILP de programación de carga

**Qué decide.** Dentro de la ventana en que cada bus está en el patio, en cuáles de los 96 bloques de 15 min carga y cuánta energía, para que el costo de energía,
eventos y reservas sea mínimo sin exceder los puestos. **Las 24 horas se resuelven de una vez:** los bloques son la unidad con que se mide el tiempo, no una
descomposición temporal.

### 5.1 Conjuntos, parámetros y variables

| | Símbolo | Significado |
|---|---|---|
| Conjuntos | $B$ | Buses de la instancia (uno por jornada tras la Etapa 3) |
| | $T=\{0,\dots,95\}$ | Bloques de 15 min del día (módulo 24 h) |
| | $W_b\subseteq T$ | Bloques **completos** dentro de la ventana $[\text{llegada}_b,\ \text{salida}_b)$ |
| Parámetros | $E_b$ | Energía a reponer (consumo desde su última salida) |
| | $q = P\cdot\Delta$ | 45 kWh por bloque |
| | $p_t$ | Tarifa del bloque |
| | $\kappa$, $f_t$ | Puestos y puestos ocupados por cargas intermedias fijas |
| | $c^{fix}=5$, $c^{res}=250$ | Costo por evento y por bus de reserva |
| Variables | $e_{bt}\ge 0$ | Energía que carga el bus $b$ en el bloque $t$ |
| | $y_{bt}\in\{0,1\}$ | El bus está enchufado en $t$ |
| | $z_{bt}\in\{0,1\}$ | Empieza un evento de carga en $t$ |
| | $r_b\in\{0,1\}$ | **Bus de reserva:** el bus termina de cargar después de su salida |

### 5.2 Formulación

$$\min \sum_{b\in B}\sum_{t\in T} p_t\,e_{bt} + c^{fix}\sum_{b,t} z_{bt} + c^{res}\sum_{b} r_b$$

| # | Restricción | En palabras | Por qué |
|---|---|---|---|
| (6) | $\sum_t e_{bt} = E_b \quad \forall b$ | Cada bus repone exactamente lo que consumió | **Condición cíclica:** termina en $L$. Con igualdad nunca pasa del tope |
| (7) | $e_{bt}\le q\,y_{bt}$ | Solo carga si está enchufado, y a lo más 45 kWh por bloque | Potencia del cargador |
| (8) | $y_{bt}\le r_b \quad \forall t\notin W_b$ | Fuera de su ventana solo puede cargar si es bus de reserva | Si no termina a tiempo, su salida la hace otro bus (misma regla que el simulador; hasta 24 h desde su llegada) |
| (9) | $\sum_b y_{bt}\le \kappa - f_t \quad \forall t$ | Nunca más buses enchufados que puestos libres | Capacidad del electroterminal, módulo 24 h |
| (10) | $z_{bt}\ge y_{bt}-y_{b,t-1}$ | Cuenta un evento cada vez que el bus se enchufa | Paga los 5 USD por evento |
| (11) | $e_{bt}\ge q\,(y_{bt}+y_{b,t+1}-1)$ | Si sigue enchufado en el bloque siguiente, este bloque va a plena potencia | Evita que el modelo deje buses "enchufados sin cargar" ocupando puestos para ahorrarse eventos (detectado en el checkpoint) |

**Desigualdades válidas** (no cambian las soluciones, solo ajustan la relajación para que Gurobi resuelva más rápido):

$$\sum_{t\notin W_b} e_{bt}\le E_b\,r_b, \qquad \sum_t y_{bt}\ge \lceil E_b/q\rceil, \qquad \sum_t z_{bt}\ge 1 \qquad \forall b$$

*En palabras:* la energía fuera de la ventana no puede superar la del bus si es reserva; el bus necesita al menos los bloques que su energía exige; y todo bus
se enchufa al menos una vez. La última bajó la brecha de N = 30 de 3,0% a 1,4%.

**Por qué no hace falta la variable de batería por bloque.** Durante la ventana el bus está estacionado: su batería solo sube, desde lo que trae hasta $L$.
No puede bajar del mínimo ni pasar el tope si se cumple (6). Es la formulación "por ventanas", más chica que la general de `01`.

**Por qué la holgura es una reserva y no una multa por energía faltante.** Con las ventanas fijas el ciclo es infactible al 100% (cota LP 77-96% en las
instancias), así que hace falta una holgura. Si fuera "energía no cargada con multa", el MILP se ahorraría energía y puestos que la reactiva sí paga y saldría
artificialmente mejor. Con $r_b$ la energía se carga igual y ocupa puestos: la comparación es justa.

### 5.3 Piso de reservas (cota inferior)

Se relaja (9) a energía, $\sum_b e_{bt}\le q\,(\kappa - f_t)$, y se dejan solo $r_b$ binarias:

$$\min \sum_b r_b \quad\text{s.a. (6), } \sum_{t\notin W_b} e_{bt}\le E_b\,r_b,\; \sum_b e_{bt}\le q(\kappa-f_t),\; 0\le e_{bt}\le q$$

Es una relajación válida: (7) y (9) implican la restricción en energía. Su óptimo es entonces el **mínimo de reservas que cualquier programa de carga
necesita** con esas ventanas y puestos, y se resuelve en segundos. **[Medido]** 1 / 8 / 15 / 32 / 68 para N = 30 a 400, contra 2 / 9 / 19 / 39 / 82 del MILP.

### 5.4 Cómo se valida y qué se compara

- **Correctitud:** la misma regla reactiva en la grilla de 15 min es factible para el MILP y se le entrega como solución inicial. El MILP debe costar
  **≤** y lo hace en todas las instancias.
- **Ejecutable:** la solución del MILP se reproduce minuto a minuto, respeta los puestos y conserva las mismas reservas.
- **Referencia:** la ganancia se mide contra el simulador al minuto (la grilla encarece la reactiva en bloques).
- **Instancia reducida:** terminal Los Espinos + Santa Rosa, puestos proporcionales (0,0584 por bus). Óptimo certificado en N = 10; brecha 1,4-8,6% en N = 30 a 400.

*Script:* `scripts/11-milp_carga.py` (Gurobi).

---

## 6. Cómo encajan las etapas

```
Etapa 1  rutas → electroterminal d(r)              (C1; C2 propuesta)
   │  dato fijo: electroterminal base de cada ruta (pullout/pullin, dónde carga)
   ▼
Etapa 2  viajes → jornadas (flujo exacto)          buses del VSP, km vacíos, espera
   │  dato fijo: secuencia de viajes de cada bus
   ▼
Etapa 3  jornadas → cargas (política reactiva)     energía, jornadas partidas, reservas  ← CASO BASE
   │  dato fijo: ventanas en el patio y energía a reponer de cada bus
   ▼
Etapa 4  ventanas → programa de carga (MILP)       menos reservas y costo de carga (instancia reducida)
```

**El precio de descomponer** se mide con una cota por etapa:
- **LB (Etapa 2):** el clustering y el retorno cuestan +311 buses (+4,4%).
- **Cota LP (Etapa 3):** con estas jornadas la carga nocturna no cabe (84%).
- **Piso de reservas (Etapa 4):** cuánto le falta al MILP para el mínimo posible.

El costo mayor está entre la Etapa 2 y la 3: ignorar la batería en el VSP agrega 5.136 buses en E1.

---

## 7. Resumen para explicar en voz alta (una página)

1. **Agrupamos rutas en electroterminales** porque las rutas cierran su ida y vuelta. Cada ruta va al más cercano a sus paraderos reales. La versión con
   capacidad (C2) es una asignación generalizada: la carga de cada ruta depende del electroterminal, porque incluye salir y volver.
2. **Asignamos viajes a buses con un flujo:** cada bus es una unidad de flujo que sale del electroterminal, pasa por viajes y vuelve. Las restricciones dicen
   "cada viaje lo hace un bus" y "un bus no aparece ni desaparece". Como es una red, el LP da solución entera: es exacto y rápido.
3. **Simulamos la carga con una política simple** (el caso base): el bus carga cuando no le alcanza la batería, sin mirar la tarifa. Si no alcanza, la jornada
   se parte; si no termina de cargar antes de salir, un bus de reserva toma su lugar.
4. **Optimizamos la carga con un MILP:** en bloques de 15 min decide si cada bus está enchufado y cuánto carga. Las restricciones son: reponer exactamente lo
   consumido, no pasar de 45 kWh por bloque, no superar los puestos y cargar fuera de la ventana solo como reserva. Minimiza tarifa, eventos y reservas.
5. **Cada etapa tiene una cota** que mide cuánto se pierde por dividir el problema. La mayor pérdida viene de que el VSP no ve la batería.

---

## Referencias

- Kliewer, N., Mellouli, T., & Suhl, L. (2006). A time–space network based exact optimization model for multi-depot bus scheduling. *European Journal of
  Operational Research*, 175(3), 1616–1627. *(Verificar los datos bibliográficos antes de citar.)*
- Resultados y cifras: [`01_metodologia.md`](01_metodologia.md). Supuestos y su respaldo: [`02_supuestos_y_decisiones.md`](02_supuestos_y_decisiones.md).
