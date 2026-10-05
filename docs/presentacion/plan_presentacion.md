# Plan de la presentación — Entrega 2 (06/10/2026)

> 10 minutos estrictos (más de 60 s de exceso interrumpe la presentación), máximo 3 presentadores. La evalúan el profesor guía, el
> ayudante y dos profesores de otros proyectos: **se explica todo lo que se decidió con el profesor, porque los demás no lo saben**.
> Rúbrica (60 pts): problema 10 · datos 5 · KPIs 4 · caso base 7 · metodología 9 · implementación 5 · resultados 15 · cierre 5.
> Descuentos: no considerar el feedback de la Entrega 1, elementos que no se explican solos (leyendas, unidades) y el tiempo.
> Todas las cifras salen de `results/*/reporte.md` y de `results/etapa5_kpis_comparacion/tablas/`. Figuras: `results/INDICE_FIGURAS.md`.

---

## 1. Hilo narrativo

**En una frase:** *planificamos 64.502 viajes diarios con buses eléctricos dividiendo el problema por tipo de decisión. Cada decisión
de modelación la tomamos con datos. El caso base es factible, pero muestra que planificar los buses sin mirar la batería cuesta casi
70% más flota, y que programar la carga recupera una parte.*

Orden de la historia:
1. **Problema** (qué, para qué, qué se entrega).
2. **Datos que decidieron la metodología.**
3. **Metodología por etapas:** responde "propuesta demasiado compleja".
4. **Formulación.**
5. **Caso base y KPIs.**
6. **Implementación.**
7. **Resultados:** interlining → hallazgo de la batería → nivel 100% → MILP.
8. **Cierre.**

**Feedback de la Entrega 1 y dónde se responde:**

| Feedback | Respuesta | Lámina |
|---|---|---|
| La propuesta (descomposición espaciotemporal con horizonte rodante) era demasiado compleja | Descomposición jerárquica por tipo de decisión: 4 etapas, cada una resoluble y con su cota o su verificación | 3 |
| "Revisar en profundidad estrategias para clusterizar" | Se clusteriza por **ruta** (dato: 94,7% cierra su ida-vuelta) y se comparan tres criterios: centroide, paraderos reales (base) y MILP con capacidad (propuesta) | 2 y 3 |

**Decisiones contadas como parte de la historia** (lo pidió el profesor): unir Los Espinos y Santa Rosa (están a 1,1 km y separados no
alcanzan los puestos); el factor 1,3 del deadhead (medido con los trazados GTFS); el ciclo diario como restricción, cumplido con buses
de reserva; el nivel 100% elegido con un barrido.

**Estilo** (tomado de la Presentación 1): secciones numeradas ("01. Problema", …), cifras grandes en recuadros, **una idea por lámina**,
título = mensaje, texto mínimo. Paleta común: azul = E1 / MILP, naranjo = reactiva, rojo = reservas, gris = cotas y LB. Fuente
grande (los números ≥ 28 pt).

---

## 2. Lámina por lámina

Presentadores: **P1**, **P2** y **P3** (los nombres los asigna el grupo). Guion a ~130 palabras por minuto.

| # | Título | s | Quién | Acumulado |
|---|---|---|---|---|
| 0 | Portada | 5 | P1 | 0:05 |
| 1 | El problema | 55 | P1 | 1:00 |
| 2 | Tres datos que decidieron la metodología | 60 | P1 | 2:00 |
| 3 | Metodología por tipo de decisión | 75 | P1 | 3:15 |
| 4 | Formulación | 50 | P2 | 4:05 |
| 5 | Caso base y KPIs | 55 | P2 | 5:00 |
| 6 | Implementación y verificación | 30 | P2 | 5:30 |
| 7 | Resultado 1: el interlining | 45 | P2 | 6:15 |
| 8 | Resultado 2: el precio de ignorar la batería | 65 | P3 | 7:20 |
| 9 | Resultado 3: el nivel de batería | 30 | P3 | 7:50 |
| 10 | Resultado 4: MILP de carga (instancia reducida) | 65 | P3 | 8:55 |
| 11 | Conclusiones y pasos a seguir | 40 | P3 | 9:35 |

Margen: 25 s.

---

### Lámina 0 — Portada (5 s, P1)
- Título del proyecto, Grupo 24, profesor Agustín Chiu, integrantes.
- **Frase:** "Somos el grupo 24 y les presentamos cómo planificamos la operación de los buses eléctricos de RED."

---

### Lámina 1 — 01. Problema: cubrir todos los viajes al menor costo, y que cada bus termine el día con la batería con que empezó (55 s, P1)
**Mensaje:** el problema es asignar buses a viajes y decidir cuándo carga cada uno; la batería y los puestos de carga lo hacen difícil.

**Contenido:**
- Recuadros con cifras: **64.502 viajes** en un día laboral · **417 rutas** · **5 electroterminales, 700 puestos de carga** ·
  bus BYD K9, **350 kWh**, ~225 km útiles · flota **irrestricta**.
- Objetivo, en una línea: minimizar **flota + km sin pasajeros + espera + energía + eventos de carga**.
- Restricciones, en tres viñetas cortas:
  - cada viaje se cubre una vez;
  - cada bus sale y vuelve a su electroterminal;
  - **ciclo diario**: termina el día con la misma batería con que lo empezó.
- Entregable: qué bus hace cada viaje, cuándo y dónde carga, cuántos buses hacen falta, y los KPIs frente a un caso base.

**Figura:** **G1:** `results/presentacion/graficos/G1_demanda_y_tarifa.png` expediciones en curso por hora, con los 6 períodos tarifarios como franjas rotuladas
(0,10 / 0,15 / 0,22 / 0,15 / 0,22 / 0,11 USD/kWh). 

**Frase:** "Cada día laboral hay 64.502 viajes. Hay que decidir qué bus hace cada uno y cuándo carga, al menor costo: flota, kilómetros
sin pasajeros, espera y energía. Hay tres restricciones que importan. Cada bus vuelve a su electroterminal. Hay solo 700 puestos de
carga. Y, como pidió el profesor, cada bus termina el día con la misma batería con que lo empezó, para que el día siguiente sea igual.
Fíjense en el gráfico: los buses se necesitan de día, así que solo pueden cargar cuando no están en servicio."

**Transición:** "Antes de modelar, miramos los datos para decidir cómo dividir el problema."

---

### Lámina 2 — 02. Datos: tres datos que decidieron la metodología (60 s, P1)
**Mensaje:** cada decisión de modelación sale de un dato.

**Contenido:** tres columnas, cada una con **dato → decisión**:
1. **El 94,7% de las rutas termina la ida a menos de 500 m de donde empieza la vuelta** (mediana 85 m) → **agrupamos rutas, no
   viajes sueltos** (respuesta a "revisar estrategias para clusterizar").
2. **Los Espinos y Santa Rosa están a 1,1 km**; el siguiente par más cercano, a 5,9 km → **los tratamos como un solo electroterminal
   de 270 puestos**. Separados, Los Espinos necesita 102-104% de su capacidad y no alcanza a reponer la energía.
3. **Los trazados GTFS reales rodean 1,04-1,38 veces la línea recta** a la escala de un traslado → **usamos línea recta × 1,3**, con
   respaldo medido.

**Figuras:**
- **G2:** `results/presentacion/graficos/G2_ida_vuelta.png` cierre ida-vuelta (eje cortado en 1.500 m, con "94,7% < 500 m" anotado).
- **G3:** `results/presentacion/graficos/G3_mapa_electroterminales.png` mapa de los 5 electroterminales sobre la red de buses de Santiago (fondo gris), con sus puestos, las distancias en línea recta de la red mínima (5,9 / 12,0 / 13,5 km), el par cercano de 1,1 km en rojo, un zoom de los dos patios, escala de 5 km, norte y el centro de Santiago como referencia.
- El dato 3 va como recuadro con la cifra; la figura `results/etapa0_calibracion_deadhead/graficos/factor_por_escala.png` queda en respaldo.

**Frase:** "Tres datos decidieron cómo dividir el problema. Primero, casi todas las rutas terminan la ida donde empieza la vuelta: por eso
agrupamos rutas completas y no viajes sueltos, que era lo que nos pidió revisar la entrega pasada. Segundo, dos electroterminales están
a un kilómetro: separados, a uno no le alcanzan los puestos para recargar su energía, así que los unimos. Tercero, medimos con los
trazados reales cuánto rodea un bus respecto de la línea recta. Da entre 1,04 y 1,38, y respalda el factor 1,3 que usamos para los
traslados sin pasajeros."

**Transición:** "Con eso armamos la metodología."

---

### Lámina 3 — 03. Metodología: dividimos el problema por tipo de decisión (75 s, P1)
**Mensaje:** cuatro etapas simples, cada una resoluble y con su verificación. Reemplaza la propuesta de la Entrega 1, que era
demasiado compleja.

**Figura:** **G4:** `results/presentacion/graficos/G4_diagrama_metodologia.png`. Cuatro cajas en fila:

| | 1. Clustering | 2. Asignación de buses (VSP) | 3. Carga reactiva | 4. Programación de carga |
|---|---|---|---|---|
| Qué decide | Electroterminal de cada ruta | Qué bus hace qué viaje | Cuándo y dónde carga cada bus (caso base) | Cuándo y cuánto carga, mirando tarifa y puestos |
| Modelo | Más cercano a los paraderos reales (base) · MILP con capacidad (propuesta) | Flujo de costo mínimo en red espacio-tiempo (exacto) | Simulador: carga cuando lo necesita | MILP (instancia reducida) |
| Cómo se valida | Contra la energía real de las jornadas | Cota inferior LB y cota 6.539 | Cota LP de la carga nocturna | Cota de reservas y MILP ≤ reactiva |

Debajo, una línea: *"Entrega 1: horizonte rodante sobre todo el día (demasiado complejo) → ahora: primero la flota, después la carga."*

**Frase:** "La entrega pasada proponíamos dividir el día en ventanas de tiempo, y se nos dijo que era demasiado complejo. Ahora dividimos
por tipo de decisión. Primero asignamos cada ruta a un electroterminal. Después decidimos qué bus hace qué viaje, con un modelo de flujo
que da el óptimo exacto en segundos. Luego simulamos cómo cargan los buses con una política simple, que es nuestro caso base. Al final,
un MILP decide cuándo cargar mirando la tarifa y los puestos. Cada etapa tiene una cota que mide cuánto perdemos por dividir el
problema. Ese es el costo de este enfoque, y lo vamos a mostrar."

**Transición:** "Así se ven las dos formulaciones centrales."

---

### Lámina 4 — 04. Formulación: el VSP es un flujo exacto; la carga es un MILP con buses de reserva (50 s, P2)
**Mensaje:** el modelo está escrito con precisión; el VSP se resuelve exacto y el MILP tiene una holgura que lo deja siempre factible.

**Contenido** (dos recuadros con ecuaciones, sin figura):

*VSP (Etapa 2), flujo de costo mínimo en red espacio-tiempo:*

$$\min \sum_{a\in A_{out}} (c^{bus}+c^{km}\ell_a)\,x_a+\sum_{a\in A_{dh}\cup A_{in}} c^{km}\ell_a\,x_a+\sum_{a\in A_{wait}} c^{wait}\tau_a\,x_a$$

Sujeto a: cada viaje cubierto una vez y conservación de flujo. La matriz es de red, así que el LP da solución entera.

*MILP de carga (Etapa 4), un electroterminal, bloques de 15 min del día:*

$$\min \sum_{b,t} p_t\,e_{bt} + 5\sum_{b,t} z_{bt} + 250\sum_b r_b$$

$$\sum_t e_{bt}=E_b \quad(\text{vuelve al 100\%}),\qquad e_{bt}\le 45\,y_{bt},\qquad \sum_b y_{bt}\le \kappa,\qquad y_{bt}\le r_b \;\;(t \text{ fuera de la ventana}),\qquad z_{bt}\ge y_{bt}-y_{b,t-1}$$

Una línea bajo la fórmula: *`r_b` = bus de reserva: si el bus no alcanza a cargar antes de salir, su salida la hace otro bus ya
cargado (250 USD).*

**Frase:** "El VSP es un flujo de costo mínimo: cada viaje es un nodo y los arcos son esperas o traslados. Como la matriz es de red, el
óptimo sale exacto en unos 40 segundos para toda la red. El MILP de carga decide, en bloques de 15 minutos, si cada bus está enchufado y
cuánto carga, sin pasarse de los puestos. Si un bus no alcanza a cargar antes de su salida, la variable r lo marca como bus de reserva:
otro bus ya cargado hace su salida, a 250 dólares. Así el ciclo diario siempre se cumple."

---

### Lámina 5 — 05. Caso base y KPIs: cada escenario cambia una sola decisión (55 s, P2)
**Mensaje:** el caso base es la operación intuitiva, y la escalera aísla el efecto de cada decisión.

**Contenido:** dos tablas.

*Escalera de escenarios:*

| | Interlining | Carga | Rol |
|---|---|---|---|
| **E0** | No (cada ruta con sus buses) | Reactiva + reservas | **Caso base** (validado por el profesor) |
| **E1** | Sí, dentro del electroterminal | Reactiva + reservas | Configuración propuesta |
| **LB** | Libre, sin volver al electroterminal | — | Cota inferior, **no operacional** |

Todas usan C1 y Los Espinos + Santa Rosa unidos; el nivel de batería es 100%.

*KPIs, cada uno ligado a una decisión:*

| KPI | Decisión que evalúa |
|---|---|
| Costo total y desglose | Todas |
| Buses (VSP, tras la carga, reservas) | Asignación y clustering |
| % de km sin pasajeros | Encadenamiento de viajes |
| Costo medio de la energía y % en valle | Programación de la carga |
| % del día con puestos saturados | Infraestructura |
| Jornadas partidas y ciclos no cumplidos | Costo de la carga miope |

**Frase:** "El caso base es lo que haría un operador sin optimizar: cada ruta con sus propios buses, y cada bus carga cuando lo necesita,
sin mirar la tarifa. El profesor lo validó como línea base. Para medir el efecto de cada decisión cambiamos una sola cosa por escalón: E1
permite que un bus haga viajes de distintas rutas. LB es una cota inferior que deja que los buses vuelvan a cualquier electroterminal;
no es operable, solo mide cuánto perdemos. Cada KPI está ligado a una decisión."

---

### Lámina 6 — 06. Implementación: Python + Gurobi, y cada etapa se verifica antes de la siguiente (30 s, P2)
**Mensaje:** la implementación es reproducible y tiene chequeos automáticos.

**Contenido** (tabla compacta):

| Etapa | Herramienta | Tiempo | Verificación automática |
|---|---|---|---|
| Datos | Python (pandas) | ~20 s | 64.502 viajes, 0 descartes |
| VSP | Gurobi (LP) | 5-55 s por escenario | Cada viaje en una sola jornada; todo bus vuelve a su electroterminal |
| Carga reactiva | Simulador propio | ~10 s | Balance de energía exacto; ocupación ≤ puestos |
| MILP | Gurobi 13 | hasta 600 s por instancia | MILP ≤ reactiva; ejecutable al minuto |

Una línea: *"13 scripts en GitHub, todos con una prueba chica antes de la red completa."*

**Frase:** "Todo está en Python con Gurobi, en scripts que corren en orden. Cada uno tiene chequeos automáticos: por ejemplo, que cada viaje
quede cubierto una sola vez, o que la energía cargada sea igual a la consumida. Y cada etapa se probó primero en un caso chico revisado a
mano."

---

### Lámina 7 — 07. El interlining baja 14,9% la flota del VSP y 5,2% el costo total (45 s, P2)
**Mensaje:** E1 es mejor que el caso base, y el clustering queda a solo 4,4% de la cota inferior.

**Figura:** `results/etapa5_kpis_comparacion/graficos/costo_desglose_E0_E1.png` (existe).

**Contenido** (recuadros):
- **VSP:** E0 **8.654** → E1 **7.366** buses (LB 7.055).
- **Costo total:** E0 **3,96 M** → E1 **3,75 M USD/día**.
- La flota es **~70%** del costo; la energía, **8%**.

**Frase:** "Primer resultado. Permitir que un bus haga viajes de distintas rutas baja la flota del VSP de 8.654 a 7.366 buses, a solo 4%
de la cota inferior. Con la carga incluida, el costo total baja de 3,96 a 3,75 millones de dólares al día. Fíjense que la flota es el
70% del costo y la energía solo el 8%. Y fíjense en la parte roja: los buses de reserva."

**Transición:** "¿De dónde salen esos buses de reserva? Ese es el hallazgo central."

---

### Lámina 8 — 08. Hallazgo: planificar los buses sin mirar la batería cuesta 5.136 buses (65 s, P3)
**Mensaje:** el precio de dividir el problema no está en el clustering (+311 buses) sino en ignorar la batería en el VSP (+5.136 buses).

**Figuras:**
- `results/etapa5_kpis_comparacion/graficos/flota_de_donde_viene.png` (existe).
- **G5:** `results/presentacion/graficos/G5_patio_vs_puestos.png` % de buses estacionados en su patio por hora vs % de los 700 puestos ocupados.

**Contenido:**
- **7.366 buses del VSP → 10.295 tras partir jornadas → 12.502 con reservas (+70%)**.
- Por qué:
  - los viajes de una jornada larga tienen huecos cortos (mediana 12,7 min) e ir a cargar cuesta ~63 min, así que la jornada se parte;
  - casi todos los buses vuelven de noche y los puestos no alcanzan, así que 2.207 no terminan de cargar antes de salir.
- **Ni con una carga perfecta cabe:** solo el **84%** de la energía nocturna entra en las ventanas (cota LP).

**Frase:** "Este es el hallazgo central. El VSP encuentra 7.366 buses, pero sin mirar la batería. Cuando simulamos la carga pasan dos cosas.
Las jornadas largas tienen huecos de minutos e ir a cargar toma una hora, así que la jornada se parte y entra otro bus. Y casi todos los
buses vuelven de noche, cuando los puestos ya están llenos: 2.207 no alcanzan a cargar antes de salir y hay que cubrirlos con reservas.
Calculamos que ni con una carga perfecta cabe más del 84% de la energía nocturna. Dividir el problema costó 311 buses en el clustering,
pero 5.136 por ignorar la batería. Esa es la principal mejora para la entrega final."

---

### Lámina 9 — 09. Nivel de batería: 100% con reservas es el menor costo factible (30 s, P3)
**Mensaje:** el nivel no se supuso: se eligió con un barrido entre 100% y 50%, y bajar el nivel se paga con más flota.

**Figura:** **G6:** `results/presentacion/graficos/G6_barrido.png` un solo panel: costo total por nivel (operación + reservas apiladas), estrella en 100% y 50% marcado
como infactible.

**Contenido:** 100% → **3,75 M** · 90% +5,9% · 80% +8,5% · 70% +17,9% · 50% infactible. Ningún nivel cumple el ciclo sin reservas.

**Frase:** "¿Y si los buses parten con menos batería? Lo probamos entre 100% y 50%. Cada 10 puntos menos agregan unos 1.500 buses, porque
se parten más jornadas. Ningún nivel cumple el ciclo sin reservas, así que el menor costo factible es partir al 100% y pagar las reservas."

---

### Lámina 10 — 10. MILP de carga en instancia reducida: al menos 10-24% menos costo de carga, casi todo por menos reservas (65 s, P3)
**Mensaje:** el MILP funciona, se certifica al óptimo en la instancia chica, y la brecha crece con el tamaño, lo que justifica probarlo
en instancias reducidas.

**Figuras:**
- `results/etapa4_milp_carga/graficos/ocupacion_reactiva_vs_milp_N200.png` (existe).
- **G7:** `results/presentacion/graficos/G7_reservas_milp.png` reservas por tamaño N: simulador, MILP y piso (mínimo posible), con "óptimo" en N = 10 y la brecha en el resto.

**Contenido** (rótulo grande: **"Instancia reducida — no es el resultado de toda la red"**):
- Instancia: el terminal Los Espinos + Santa Rosa, una muestra con semilla fija y **puestos proporcionales** (misma congestión que la red).
- Tabla mínima:

| N buses | Ganancia vs simulador | Reservas simulador → MILP (piso) | Brecha |
|---|---|---|---|
| 9 | ≥ 10,5% | 0 → 0 (0) | **óptimo** |
| 55 | ≥ 15,1% | 12 → 9 (8) | 2,0% |
| 210 | ≥ 11,5% | 48 → 39 (32) | 1,9% |
| 404 | ≥ 14,3% | 107 → 82 (68) | 8,6% |

**Frase:** "Probamos el MILP en instancias reducidas de nuestro terminal más exigido, como pidió el profesor, con los puestos reducidos
en proporción para mantener la congestión real. El MILP siempre cuesta menos que la política simple, y su programa se puede ejecutar minuto
a minuto. La ganancia viene casi toda de las reservas: usa los puestos que quedan libres en la tarde. En la instancia chica se certifica
el óptimo. A medida que crece, la brecha llega a 8,6%, y por eso no lo corremos sobre toda la red."

---

### Lámina 11 — 11. Conclusiones y pasos a seguir (40 s, P3)
**Conclusiones** (tres viñetas):
1. **El caso base es factible y medible:** E0 3,96 M y E1 3,75 M USD/día; el interlining ahorra 5,2%.
2. **El cuello de botella es la batería, no la asignación:** ignorarla agrega 70% de flota; la carga nocturna no cabe.
3. **Programar la carga ayuda** (≥ 10-24% en instancias reducidas), sobre todo porque reduce las reservas.

**Pasos a seguir** (hoja de ruta con hitos, hasta la entrega final):

| Hito | Qué | Por qué |
|---|---|---|
| 1 | VSP que vea la batería (jornadas con pausas de carga) | Ataca los +5.136 buses |
| 2 | MILP de carga a mayor escala (por terminal, romper simetría) | Hoy solo hay óptimo certificado en N = 10 |
| 3 | Calibrar el layover, elegir el radio de interlining por costo total y validar el deadhead con la red vial | Son los supuestos más sensibles (layover −2,8% a +6,0% de flota; radio +11,3% a −3,4%) |
| 4 | Informe final y KPIs de E3 (carga programada) | Cierre |

**Frase:** "En resumen: el caso base es factible y lo medimos completo. El cuello de botella no es asignar los viajes sino la batería, que
hoy cuesta un 70% más de flota. Y programar la carga ayuda, sobre todo porque reduce las reservas. Para la entrega final, el paso más
importante es que la asignación de buses considere la batería. Gracias."

---

## 3. Cifras a memorizar

| Cifra | Qué es |
|---|---|
| 64.502 viajes, 417 rutas, 700 puestos | El problema |
| 6.539 | Viajes simultáneos a las 8:00: cota inferior de flota |
| 94,7% | Rutas cuya ida y vuelta cierra a menos de 500 m |
| 1,1 km | Distancia entre Los Espinos y Santa Rosa (el siguiente par, 5,9 km) |
| 1,04-1,38 | Rodeo medido; respalda el 1,3 |
| 8.654 / 7.366 / 7.055 | Buses del VSP: E0 / E1 / LB |
| 3,96 M / 3,75 M | Costo total E0 / E1 (USD/día) |
| 10.295 + 2.207 = 12.502 | Buses de E1 tras la carga + reservas |
| +311 vs +5.136 | Precio del clustering vs precio de ignorar la batería |
| 84% | Energía nocturna que cabe con una carga perfecta (E1) |
| 12,7 min / ~63 min | Hueco mediano entre viajes / ir y volver de cargar |
| ~70% / 8% | Participación de la flota / la energía en el costo |
| −2,8% a +6,0% | Sensibilidad de la flota al layover (0 a 10 min) |
| +11,3% a −3,4% | Sensibilidad de la flota de E1 al radio de interlining (1 a 5 km; modelo: 3 km) |
| ≥ 10-24% | Ganancia del MILP en las instancias reducidas |
| N = 10 óptimo; brecha ≤ 8,6% | Certificación del MILP |

---

## 4. Preguntas probables y respuestas cortas

- **¿Por qué distancia euclidiana para los traslados?**
  Usamos línea recta × 1,3 y lo medimos con los 839 trazados GTFS: el rodeo real es 1,04-1,38 a la escala de un traslado. Además, la
  flota cambia solo ±1% entre 1,2 y 1,5. Para el informe lo validaremos con la red vial.
- **¿Por qué buses de reserva y no bajar el nivel de batería?**
  Lo probamos. Bajar el nivel parte más jornadas (+1.500 buses cada 10 puntos) y ningún nivel cumple el ciclo sin reservas; 100% con
  reservas es lo más barato entre las soluciones factibles.
- **¿Por qué 100%?**
  Es el máximo de los datos del curso y el barrido lo confirma como el menor costo, tanto en E0 como en E1. Bajarlo exigiría una razón
  externa citada (vida útil, curva de carga) que hoy no tenemos.
- **¿Por qué la asignación con capacidad (C2) no es la base?**
  Mueve solo 5 de 417 rutas, mejora el costo 0,3% y no resuelve la falta de puestos. Lo que sí la resuelve es unir los dos terminales.
  Queda como metodología propuesta.
- **¿Qué tan representativa es la instancia del MILP?**
  Tiene la misma razón puestos/bus, la misma carga sobre la capacidad (80-89% contra 86% en la red) y el mismo patrón de llegadas
  nocturnas (91-95% contra 90%). Igual es una muestra de un terminal; no la extrapolamos a toda la red.
- **¿Por qué el MILP no se resuelve al óptimo a escala?**
  El costo lo dominan las reservas y hay mucha simetría entre buses. Certificamos el óptimo en N = 10. En el resto damos la brecha y un
  piso de reservas, así que la ganancia que reportamos es mínima.
- **¿La espera en cola cuenta como costo?**
  En el total oficial sí, como opción conservadora (~100.000 USD/día). Sin ella, E1 queda en 3,64 M y E0 en 3,86 M, y ninguna
  conclusión cambia. Preguntamos: ¿debería cobrarse la espera de un bus estacionado en el patio?
- **¿Qué es LB y por qué no es operacional?**
  Deja que un bus vuelva a cualquier electroterminal (4.192 de sus jornadas lo hacen), lo que viola el retorno. Solo sirve como cota de
  lo que se pierde al dividir el problema.
- **¿Por qué es válido unir terminales?**
  Están a 1,1 km y el profesor lo validó como decisión de modelación. Separados, Los Espinos no alcanza a reponer 44-48 MWh por día;
  unidos, el déficit es 0.
- **¿Por qué el radio de interlining es 3 km y no 5?**
  Lo fijamos para acotar el tamaño del modelo, no por una medición, y después lo probamos: con 5 km la flota de E1 baja 3,4% (7.366 → 7.118) y el tiempo de cómputo pasa de ~24 s a ~120 s; con 1 km sube 11%. Los retornos son decrecientes. Mantuvimos 3 km porque ampliarlo exige rehacer la carga con jornadas más largas; es una mejora para la entrega final, y significa que el ahorro del interlining que mostramos es un piso.
- **¿La flota tiene límite?**
  No: el profesor confirmó que es irrestricta. El valor de 1.200 de los datos está obsoleto.
- **¿Por qué las jornadas se parten en vez de recargar a mitad del día?**
  El hueco mediano entre viajes es 12,7 min e ir y volver de cargar toma ~63 min. Solo 0,6% de las jornadas alcanza a recargar a mitad
  del día.

---

## 5. Láminas de respaldo (anexo, no se presentan)

| Tema | Figura |
|---|---|
| Calibración del deadhead | `results/etapa0_calibracion_deadhead/graficos/factor_por_escala.png` |
| Sensibilidad de la flota (factor, layover y radio de interlining) | `results/etapa2_vsp/graficos/sensibilidad_deadhead.png` (ahora con tres paneles) |
| C2: formulación y resultado | Ecuación de `docs/context/01_metodologia.md` (Etapa 1) + `results/etapa1_clustering/mapas/mapa_diferencias.png` |
| Terminales separados: infactibles | Tabla de `results/etapa3_carga_reactiva/barrido/tablas/evidencia_terminales_separados.csv` |
| Por qué no "100% sin recuperar la batería" (2% vs 70% de uso de los puestos) | `results/etapa1_clustering/graficos/capacidad_sin_vs_con_recuperacion.png` |
| Cota LP y ciclos por nivel | `results/etapa3_carga_reactiva/barrido/graficos/barrido_ciclos_y_cota.png` |
| Representatividad de la instancia del MILP | Tabla de `results/etapa4_milp_carga/tablas/representatividad.csv` |
| Brecha y costo del MILP por N | `results/etapa4_milp_carga/graficos/brecha_vs_N.png`, `costo_reactiva_vs_milp.png` |
| Costo con y sin espera por puesto | `results/etapa5_kpis_comparacion/tablas/desglose_costo.csv` |
| Ejemplo de la batería de un bus durante el día | `results/etapa3_carga_reactiva/graficos/soc_ejemplo_E1_soc100.png` |
| Uso de cada electroterminal | `results/etapa5_kpis_comparacion/graficos/uso_electroterminales.png` |

---

## 6. Gráficos de la presentación (generados: `python scripts/14-graficos_presentacion.py`)

Generados el 05/10 en `results/presentacion/graficos/` con su CSV en `results/presentacion/tablas/`. G4 también puede rehacerse editable en la herramienta de slides con el mismo contenido.

| Id | Lámina | Qué muestra | Datos |
|---|---|---|---|
| G1 | 1 | Expediciones en curso por hora, con los 6 períodos tarifarios como franjas rotuladas | `results/etapa0_preprocesamiento/concurrencia_por_minuto.csv`, `data-filtrado/electricity_prices.csv` |
| G2 | 2 | Cierre ida-vuelta: eje hasta 1.500 m y "94,7% < 500 m (mediana 85 m)" anotado | `data-processed/rutas_ida_vuelta.csv` |
| G3 | 2 | Mapa sobre la red de buses: 5 electroterminales, distancias entre ellos (red mínima), zoom de los dos unidos, escala y norte | `data-filtrado/{depots,shapes_bus,trips_dia_L}.csv`, `data-alumnos/chile.gpkg` |
| G4 | 3 | Diagrama de 4 etapas (mejor en la herramienta de slides; el contenido está en la lámina 3) | — |
| G5 | 8 | % de buses estacionados en su patio por hora vs % de los 700 puestos ocupados, con la tarifa punta sombreada | `results/etapa3_carga_reactiva/tablas/{jornadas,ocupacion}_E1_soc100.csv` |
| G6 | 9 | Barrido en un panel: costo total por nivel (operación + reservas), estrella en 100% y 50% infactible | `results/etapa3_carga_reactiva/barrido/tablas/barrido_niveles.csv` |
| G7 | 10 | Reservas por N: simulador, MILP y piso, con "óptimo" en N = 10 y la brecha en el resto | `results/etapa4_milp_carga/tablas/{comparacion_reactiva_milp,instancias,tiempos_resolucion}.csv` |
| — | 7 y 8 | Coma decimal en `costo_desglose_E0_E1.png` y `flota_de_donde_viene.png` (aplicada) | `scripts/12-kpis_comparacion.py` |

---

## 7. Ensayo cronometrado

1. **Primera pasada** con cronómetro y sin cortar. Controles: fin de P1 en **3:15**, fin de P2 en **6:15**, fin de P3 en **9:35**.
   Si un presentador se pasa más de 15 s en su tramo, recorta su lámina más larga.
2. **Qué recortar si falta tiempo**, en este orden:
   - lámina 9 (queda una línea en la 8: "100% con reservas es el menor costo; ver anexo");
   - lámina 6 (queda una línea en la 5);
   - el dato 3 de la lámina 2.
   **No se recortan** la 3, la 8 ni la 10.
3. **Cambios de presentador:** el que termina dice la frase de transición; el que entra no repite el título.
4. **Segunda pasada**, solo para fluidez y transiciones. Revisar que cada gráfico tenga leyenda y unidades, y que la lámina 10 diga
   "instancia reducida".
5. **Preguntas:** cada presentador se prepara las preguntas de su tramo (P1: deadhead, unir terminales y C2; P2: LB y espera en
   cola; P3: reservas, nivel 100% y MILP).
