# Propuesta de metodología — Reunión Grupo 24 (28/09)

> **Objetivo de la reunión:** dejar cerrada hoy la metodología para la Entrega 2 (presentación **06/10**, informe **11/10**), respondiendo al feedback de "propuesta demasiado compleja" y al comentario del profesor en 3.3.1: *"Revisar en profundidad estrategias para clusterizar"*.

---

## 0. TL;DR (la propuesta en 6 puntos)

1. **Los datos muestran que la escala no es el problema.** La asignación de buses a las 64.502 expediciones (sin batería) se resuelve **de forma exacta en ~40 segundos** con Gurobi como flujo de costo mínimo sobre una red espacio-tiempo. Ya lo probamos. La descomposición temporal por horizonte rodante (lo más complejo y riesgoso de nuestra propuesta) **no es necesaria**.
2. **La dificultad real es la energía.** Si los buses parten el día cargados, solo **~25% de las jornadas** supera la batería y casi ninguna necesita más de una recarga. De esas, solo **~50%** tiene hoy un hueco donde insertar la recarga. Ahí debe ir nuestro esfuerzo de modelación.
3. **Propuesta: descomposición jerárquica por decisiones** (en vez de por ventanas de tiempo):
   **Etapa 1** clusterizar *rutas* (no expediciones) a electroterminales → **Etapa 2** asignación de buses exacta (red espacio-tiempo) → **Etapa 3** inserción de recargas por jornada → **Etapa 4** programación de carga en MILP con índice temporal y tarifas horarias.
4. **Mantiene la esencia del Informe 1** (descomposición espacial por electroterminal + tratamiento explícito del tiempo y las tarifas), así que es una **simplificación justificada con evidencia**, no un cambio de rumbo.
5. **Responde directamente al comentario del profesor.** La unidad a clusterizar es la **ruta** (95% de las rutas termina la ida a <500 m de donde empieza la vuelta), y comparamos 3–4 estrategias de clustering midiendo su "precio" exacto contra la solución sin clustering, que podemos calcular.
6. **Cada etapa es un modelo pequeño, estándar y citable**, implementable en Python + Gurobi en los 8 días que quedan para la presentación. Hay un **MVP** claro para el 06/10 y extensiones claras para la entrega final.

---

## 1. Qué nos exige la Entrega 2 (y por qué la metodología define la nota)

| Ítem del informe (135 pts) | Pts | Qué necesitamos tener |
|---|---|---|
| Metodología | 20 | Formalización matemática rigurosa y completa |
| Resultados y análisis | 20 | Resultados **reproducibles** + análisis crítico, sensibilidad |
| Conclusiones | 20 | Robustez bajo distintos supuestos, limitaciones |
| Pasos futuros | 15 | Gantt con hitos, dependencias y **responsables** |
| Caso base | 10 | Línea base sólida y defendible |
| KPI | 10 | Ligados a decisiones, **comparados contra el caso base** |
| Implementación | 10 | Código ordenado, trazable (GitHub/zip) |
| Datos, bibliografía, supuestos | 5+5+5 | Sesgos, fortalezas/debilidades, plan de sensibilidad |

**Implicancia:** ~60 de 135 puntos dependen de tener **resultados reales corriendo** (resultados, caso base, KPIs, implementación). Una metodología que no alcanza a producir números para el 06/10 nos cuesta la entrega. Además, la pauta indica que esta es la última instancia para "ajustar el rumbo", así que cambiar ahora es lo esperado; cambiar después sale caro.

**Calendario real:** hoy 28/09 → presentación 06/10 (**8 días**) → informe 11/10 (**13 días**).

---

## 2. Radiografía del problema con datos (calculado hoy)

| Métrica | Valor | Comentario |
|---|---|---|
| Expediciones día laboral | 64.502 | 6.620 viajes GTFS expandidos por frecuencia |
| Rutas | 417 | 300 con ida (I) y regreso (R) |
| Duración media expedición | 78,6 min | Distancia media 20,9 km |
| Energía media por expedición | 29,2 kWh | Total diario: **1.884 MWh** |
| Máx. expediciones simultáneas | **6.539** (08:00) | **Cota inferior de flota** |
| Dist. fin de ida → inicio de regreso (misma ruta) | mediana **80 m**; 95% < 500 m | Las rutas se encadenan naturalmente consigo mismas |
| Paraderos terminales únicos | 641 | Mediana 6,3 km al electroterminal más cercano |
| Capacidad de carga | 700 puestos × 180 kW | 3.024 MWh/día como máximo teórico (24 h) |

### Prototipo: asignación de buses (VSP) sin batería, red completa

Modelo: flujo de costo mínimo en red espacio-tiempo (Kliewer et al., 2006). Deadhead = distancia euclidiana × 1,3 a 20 km/h, layover mínimo de 3 min, interlining a ≤3 km. La LP resulta **entera** (sin valores fraccionales).

| Escenario | Buses | Deadhead (km) | Tiempo |
|---|---|---|---|
| Cota inferior (máx. simultáneas) | 6.539 | — | — |
| **Cada ruta con sus propios buses** (sin interlining) | **8.654** | 10.078 | 3 s |
| **Interlining libre entre rutas cercanas** | **7.055** (−18%) | 12.344 | ~40 s |

### Energía de las jornadas resultantes (supuesto: SOC inicial 100%, útil 315 kWh)

| | Sin interlining | Con interlining |
|---|---|---|
| Energía por jornada p50 / p90 / máx. (kWh) | 237 / 344 / 653 | 270 / 356 / 600 |
| Jornadas que requieren recarga (>315 kWh) | 1.521 (18%) | 1.759 (25%) |
| Jornadas que requieren ≥2 recargas | 1 | 0 |
| Energía a recargar durante el día | 76 MWh (~425 h-cargador) | 81 MWh (~451 h-cargador) |
| Jornadas con hueco factible para una recarga (sin reoptimizar) | 37% | 54% |

### Tres conclusiones que cambian la estrategia

1. **La escala 64.502 no obliga a descomponer en el tiempo.** El VSP completo es trivial para Gurobi con la formulación adecuada. El horizonte rodante agrega complejidad sin resolver ningún cuello de botella real.
2. **El trade-off central del proyecto está cuantificado.** Minimizar buses (250 USD c/u, la mayor componente de costo) genera jornadas más largas → más jornadas necesitan recarga → sin un buen manejo de la energía, se pierde parte del ahorro. El problema es exactamente "cuántos buses cuesta la batería".
3. **La capacidad de carga diurna holgada depende del supuesto de SOC inicial** (ver §6). Es la decisión de modelación más importante que debemos cerrar y consultar.

---

## 3. Diagnóstico crítico de la metodología del Informe 1

| # | Problema | Severidad | Por qué importa |
|---|---|---|---|
| D1 | **La descomposición temporal (ventanas de 3 h, horizonte rodante) es miope respecto a la batería y la flota.** Una ventana decide sacar buses y gastar energía sin ver el resto del día. El nº de buses (el costo dominante) es una decisión de **día completo**. Tampoco puede aprovechar la carga nocturna barata. | Alta | Soluciones de mala calidad y difíciles de defender |
| D2 | **Complejidad de implementación desproporcionada:** ~120 subproblemas, transmisión de estado entre ventanas, lógica de "commit vs. borrador", y además SP+GC+Benders en ventanas peak. Es lo que advirtieron en la presentación. | Alta | Riesgo real de no tener resultados el 06/10 |
| D3 | **Los subproblemas no son chicos.** Una ventana peak de 3 h por electroterminal contiene ~2.000–2.500 expediciones: un MILP arco-flujo con SOC y big-M de ese tamaño no se resuelve "directo". | Alta | La premisa de la descomposición no se cumple |
| D4 | **La Fase 1 clusteriza expediciones, no rutas.** Asignar cada expedición al electroterminal más cercano puede separar la ida y la vuelta de una misma línea, que es el encadenamiento natural (80 m entre ambas). Probablemente es lo que apunta el comentario del profesor. | Alta | Rompe la estructura del problema y aumenta la flota |
| D5 | **La capacidad de Fase 1 está mal definida.** Se usa la capacidad de carga de `charging_activities` como capacidad de "viajes" asignados. Las unidades no calzan (puestos de carga simultáneos vs. expediciones/día). | Media | Error conceptual visible en la formalización |
| D6 | **Sin cota inferior ni medida de calidad.** No había forma de saber cuánto se pierde por descomponer. | Media | La pauta pide "análisis crítico" de resultados |
| D7 | **Inconsistencias de datos arrastradas:** `fleet_size=1200` sigue en `parameters.csv` (el profesor definió flota irrestricta; hay que declararlo explícitamente), falta la fila en `data-filtrado/parameters.csv`, y el costo por km se aplica también a km comerciales (constante, no afecta decisiones). | Baja | Descuento por "trabajo no corregido" / coherencia |
| D8 | **KPI "utilización por bus"** definido con "horas de turno" sin definir turno. No hay KPI de uso de electroterminales ni de costo total. | Baja | KPIs 10 pts: deben ligarse a decisiones |

**Lo que sí rescatamos:** (i) la descomposición espacial por electroterminal, (ii) la conciencia de que tiempo y tarifas importan, (iii) la revisión bibliográfica (Alvo et al. 2021 es de Santiago; van Kooten Niekerk et al. 2017; Perumal et al. 2022; Gao et al. 2024), y (iv) SP+GC y ALNS como extensiones para la entrega final.

---

## 4. Alternativas evaluadas

| Alternativa | Implementable al 06/10 | Calidad | Escala a red completa | Respaldo bibliográfico | Responde al feedback | Veredicto |
|---|---|---|---|---|---|---|
| **A. Mantener la del Informe 1** (clustering por expedición + horizonte rodante + MILP/SP-GC por ventana) | ❌ Muy difícil | Media-baja (miope) | Dudoso (D3) | Parcial (Kim 2023 es de PDPTW, no de E-VSP) | ❌ Ignora "muy complejo" | Descartar |
| **B. Descomposición jerárquica por decisiones** (clustering de rutas → VSP exacto → recargas → MILP de carga) | ✅ Etapas 0–2 ya prototipadas | Buena, **con cota inferior** para medir la brecha | ✅ Probado | Fuerte (Kliewer 2006; Freling 2001; enfoques secuenciales en Perumal 2022) | ✅ Simplifica + clustering en profundidad | **Recomendada** |
| **C. ALNS puro** sobre solución greedy | ⚠️ Posible, pero con mucho "tuning" | Buena si se afina bien | ✅ | Fuerte (Wen et al. 2016; Wang et al. 2024) | ⚠️ Sigue siendo complejo de depurar | Usar como **mejora** en la entrega final |
| **D. SP + Generación de Columnas (+ Benders)** en todo el problema | ❌ | Muy alta | ❌ A esta escala, no en 2 semanas | Fuerte (van Kooten Niekerk 2017) | ❌ | Extensión opcional **por cluster** para validar calidad |

---

## 5. Metodología propuesta: descomposición jerárquica en 4 etapas

```
 Etapa 0            Etapa 1                 Etapa 2                    Etapa 3                 Etapa 4
 Preproceso   →   Clustering de      →   Asignación de buses   →   Inserción de       →   Programación de carga
 (expediciones,   RUTAS a electro-       por cluster (VSP en        recargas por           por electroterminal
 terminales,      terminales             red espacio-tiempo,        jornada (DP/MILP       (MILP con índice temporal,
 matriz deadhead) (MILP asignación)      LP entera, exacto)         pequeño, reparación)   tarifas horarias, capacidad)
                        ↑                                                  │                        │
                        └──────────── retroalimentación: jornadas infactibles / capacidad excedida ─┘
```

Idea en una frase: **primero decidimos qué buses cubren qué viajes (lo que define el costo dominante), después dónde y cuándo cargan (lo que define energía y uso de infraestructura)**, con retroalimentación si la carga no cabe. En la literatura de E-VSP esta estrategia se conoce como **enfoque secuencial**, en contraste con el enfoque integrado.

### Etapa 0 — Preprocesamiento (ya casi listo)
- Expandir frecuencias → 64.502 expediciones con (origen, destino, hora de salida y llegada, km, kWh = km × 1,4).
- Terminales = paraderos de inicio y fin (641).
- Deadhead: distancia euclidiana × factor de desvío (1,3) a velocidad constante. **Calibrar el factor con OSM** en una muestra de pares (osmnx ya está instalado) → sensibilidad.

### Etapa 1 — Clustering de rutas a electroterminales *(respuesta al comentario 3.3.1)*

**Unidad de clustering = ruta** (o grupo de rutas que comparten terminales), porque 95% de las rutas cierra su ciclo ida-vuelta a <500 m. Clusterizar expediciones rompe ese encadenamiento.

Para qué sirve el cluster: define el **electroterminal base** de cada bus (salida desde el electroterminal, regreso al electroterminal, dónde carga) y convierte un problema multi-depósito en 5 problemas de un solo depósito, cada uno exacto y entero.

Estrategias a comparar (esto es el "en profundidad" que pide el profesor):

| Estrategia | Descripción | Complejidad |
|---|---|---|
| **C0 – Sin clustering** | VSP de toda la red con interlining libre. **Cota/referencia** (7.055 buses) | Ya hecho |
| **C1 – Electroterminal más cercano por ruta** | Heurística geográfica simple | Trivial |
| **C2 – Asignación generalizada con capacidad** | MILP rutas × electroterminales: minimiza el costo esperado de salida/regreso y viajes a cargar, con balance de demanda de carga (horas-cargador) vs. capacidad de cada terminal | 417 × 5 binarias, segundos |
| **C3 – Clustering por compatibilidad** (extensión) | Grafo de rutas con peso = nº de encadenamientos entre rutas en la solución C0; comunidades (Louvain) → asignación a terminales. Preserva el interlining valioso | Medio |

**Métrica clave: "precio del clustering"** = (buses y costo con Cx) − (buses y costo con C0). Como C0 se calcula exacto, podemos **cuantificar** cuánto se pierde por descomponer. Esto no lo tenía el Informe 1 y es un resultado muy defendible.

Formulación C2 (esbozo):

$$\min \sum_{r\in R}\sum_{d\in D} c_{rd}\,x_{rd} \quad \text{s.a.}\quad \sum_{d} x_{rd}=1\;\forall r,\qquad \sum_{r} h_r\,x_{rd} \le \theta\,\kappa_d H\;\forall d,\qquad x_{rd}\in\{0,1\}$$

con $c_{rd}$ el costo estimado de salida/regreso y de viajes a cargar de la ruta $r$ desde $d$, $h_r$ las horas-cargador estimadas de la ruta, $\kappa_d$ la capacidad del terminal, $H$ las horas disponibles y $\theta$ un factor de holgura.

### Etapa 2 — Asignación de buses por cluster: red espacio-tiempo (exacto)

Red (Kliewer et al., 2006): un nodo por expedición + una "línea de tiempo" por terminal con arcos de espera; arcos de deadhead fin → terminal cercano; arcos de salida y regreso desde y hacia el electroterminal. Una unidad de flujo = un bus.

$$\min \; \sum_{a\in A_{out}} (c^{bus} + c^{km}\ell_a)\,x_a + \sum_{a\in A_{dh}\cup A_{in}} c^{km}\ell_a\,x_a + \sum_{a\in A_{wait}} c^{wait}\tau_a\,x_a$$
$$\text{s.a.}\quad \sum_{a\in\delta^-(i)} x_a = \sum_{a\in\delta^+(i)} x_a = 1\;\;\forall i\in\text{expediciones},\qquad \text{conservación de flujo en nodos de terminal},\qquad x_a\ge 0$$

- La matriz es de red (totalmente unimodular), así que **la LP entrega la solución entera**: exacta y rápida (probado: 40 s para toda la red).
- **Nota honesta:** esta etapa no ve la batería. Eso lo corrige la Etapa 3, y en la entrega final se puede incorporar parcialmente (p. ej., penalizar jornadas muy largas o reservar huecos cerca de los terminales).

### Etapa 3 — Inserción de recargas por jornada (reparación)

Para cada jornada (secuencia fija de viajes) con energía >315 kWh:
- Elegir en qué hueco y en qué electroterminal cargar: es un **camino mínimo / programación dinámica** sobre la secuencia (estado = SOC), muy barato.
- Si ningún hueco sirve: (a) **reordenar la descomposición del flujo** (en un terminal, qué bus toma qué salida; asignar los huecos largos a los buses que necesitan cargar), o (b) **dividir la jornada** (+1 bus).
- Hoy, sin reoptimizar, ~54% de estas jornadas ya tiene hueco. El peor caso (dividir todas las demás) suma ~800 buses (~7.870, aún bajo el caso base).

### Etapa 4 — Programación de carga por electroterminal (MILP con índice temporal)

Con las ventanas de carga de cada bus fijadas por la Etapa 3, se decide **cuánto cargar en cada intervalo de 15 min**, respetando capacidad y minimizando costo por tarifa horaria:

$$\min \sum_{b,t} p_t\, e_{bt} + c^{fix}\sum_b z_b \quad\text{s.a.}\quad e_{bt}\le P\Delta t\, y_{bt},\quad \sum_b y_{bt}\le \kappa_d\;\forall t,\quad SOC_{b}^{min}\le SOC_{b,t}\le SOC^{max},\quad y_{bt}\le z_b$$

Tamaño: ~1.800 buses × pocas decenas de intervalos → pequeño. **Aquí vive la dimensión temporal y tarifaria** que queríamos en el Informe 1. Si la capacidad se excede → retroalimentación a la Etapa 3 (mover o dividir).

### Extensiones para la entrega final (priorizadas)
1. Clustering C3 (compatibilidad) + calibración del deadhead con OSM.
2. Escenario "cíclico" (los buses deben terminar el día cargados para el día siguiente) → aquí los 700 puestos sí restringen (ver §6).
3. Mejora local tipo ALNS sobre la solución (mover viajes entre jornadas para crear huecos de carga).
4. Validar la calidad en un cluster pequeño con SP + Generación de Columnas (Metodología 2 del Informe 1).

---

## 6. Supuestos críticos (y plan de sensibilidad)

| Supuesto | Valor base | Sensibilidad | Nota |
|---|---|---|---|
| **SOC al inicio del día** | 100% (cargado de noche) | 80%, 90% | **El más importante.** Con 100%, la carga diurna usa ~4% de la capacidad; exigir ciclo diario (recargar ~1.900 MWh con 700 puestos) vuelve la infraestructura muy restrictiva. **Consultar al ayudante.** |
| Costo de la energía nocturna | Tarifa valle (0,10–0,11) para la energía consumida | — | Define si el costo de energía es una constante o una decisión |
| Flota | Irrestricta (instrucción del profesor) | — | Declarar explícitamente que `fleet_size=1200` del CSV no se usa |
| Factor de desvío deadhead | 1,3 | 1,2 / 1,5, calibrado con OSM | |
| Velocidad deadhead | 20 km/h | 15 / 25 | |
| Layover mínimo | 3 min | 0 / 5 / 10 | Afecta fuertemente la flota |
| Radio de interlining | 3 km | 1 / 5 km, sin interlining | |
| Consumo | 1,4 kWh/km constante | ±15% | Sin topografía ni congestión |
| Carga | Lineal a 180 kW | — | Sin curva CC-CV |
| Capacidad de carga | Constante 24 h (datos) | — | `transformer_mw` no viene en los datos |

---

## 7. Caso base y KPIs

### Caso base: "operación por línea + carga reactiva"
Replica cómo opera intuitivamente un operador:
- **Cada ruta con sus propios buses** (sin interlining), despacho FIFO en los terminales, electroterminal base = el más cercano a la ruta.
- **Carga reactiva:** cuando el SOC proyectado no alcanza para el siguiente viaje, va al electroterminal más cercano y carga al 100%, sin mirar la tarifa. Si no hay puesto, espera.
- Ya tenemos su número de flota sin batería: **8.654 buses** (vs. 7.055 con interlining).

Es defendible porque es el estándar operacional real (buses asignados a un servicio), es simple de explicar y separa bien el valor de cada etapa: interlining (Etapa 2), carga inteligente (Etapas 3–4).

### KPIs (refinados)
| KPI | Definición | Decisión que evalúa |
|---|---|---|
| **Costo total y desglose** | Flota + km vacíos + espera + energía + cargas fijas | Todas (es la función objetivo) |
| **Nº de buses** | Jornadas usadas; brecha vs. cota inferior 6.539 | Asignación de buses / clustering |
| **% km vacíos** | km (deadhead + salida + regreso) / km totales | Encadenamiento y clustering |
| **Costo medio de energía** | USD/kWh cargado y **% de energía cargada en valle** | Programación de carga |
| **Uso máx. de electroterminales** | máx_t (buses cargando / capacidad), por terminal | Infraestructura |
| **Utilización de bus** | Horas con pasajeros / (fin − inicio de la jornada) | Calidad de las jornadas |
| **Precio de la descomposición** *(metodológico)* | Buses/costo con clustering − sin clustering | Validez de la metodología |

---

## 8. Plan de trabajo y reparto (propuesta, para ajustar en la reunión)

| Fecha | Hito |
|---|---|
| Lun 28/09 (hoy) | Metodología cerrada, roles asignados, preguntas enviadas al ayudante |
| Mar 29 – Mié 30 | Etapa 0 limpia en el repo; Etapa 2 (VSP) sobre red completa; caso base (sin batería); Etapa 1 C1 y C2 |
| Jue 01 – Vie 02 | Etapa 3 (inserción de recargas) + Etapa 4 (MILP de carga) en **un electroterminal** (prueba de concepto) → luego los 5 |
| Sáb 03 | Resultados completos + KPIs vs. caso base + 1–2 sensibilidades (SOC inicial, layover) |
| Dom 04 – Lun 05 | Slides + **ensayo cronometrado (10 min estrictos)** |
| **Mar 06/10** | **Presentación** |
| 07 – 11/10 | Informe: formalización completa, resultados, discusión, Gantt con responsables, repo GitHub |

**Parejas sugeridas (6 personas):**
- **Datos e infraestructura** (2): Etapa 0, calibración OSM del deadhead, orden del repo, trazabilidad.
- **Buses y clustering** (2): Etapas 1–2, caso base, precio del clustering.
- **Energía y carga** (2): Etapas 3–4, KPIs de energía y electroterminales.
- Transversal: una persona de cada pareja redacta su sección matemática; una persona coordina formalización, bibliografía y Gantt.

---

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Muchas jornadas sin hueco para cargar → la flota sube | Reordenar la descomposición del flujo; peor caso acotado (~+800 buses); en la entrega final, VSP con conciencia de energía / ALNS |
| El supuesto de SOC inicial resulta distinto al esperado por el curso | Correrlo como escenario desde ya (100% vs. cíclico); consultar hoy |
| Pérdida de optimalidad por la secuencia de etapas | La reportamos con cota inferior (C0) y análisis de brecha: se convierte en resultado, no en debilidad |
| Deadhead euclidiano poco realista | Calibración con OSM en una muestra + sensibilidad del factor |
| "Parece que cambiamos todo" | Narrativa: mantenemos la descomposición espacial (profundizada) y **sustituimos** la temporal por una descomposición por decisiones, respaldada por evidencia numérica |

---

## 10. Decisiones a cerrar hoy

- [ ] ¿Adoptamos la descomposición jerárquica en 4 etapas (Alternativa B)?
- [ ] Unidad de clustering = ruta; estrategias C0/C1/C2 para el 06/10, C3 para la entrega final.
- [ ] Supuesto base de SOC inicial (propuesta: 100%) + escenario cíclico como sensibilidad.
- [ ] Caso base = operación por línea + carga reactiva.
- [ ] Lista de KPIs (§7).
- [ ] Parámetros base: factor 1,3; 20 km/h; layover 3 min; radio 3 km.
- [ ] Parejas y responsables; repo GitHub.

## 11. Preguntas para el ayudante / profesor (enviar hoy)

1. ¿Los buses parten el día con batería completa (carga nocturna fuera del alcance), o debemos garantizar que queden cargados para el día siguiente con los 700 puestos?
2. ¿Cómo debe contabilizarse el costo de la energía consumida con la carga inicial?
3. ¿Se exige que cada bus vuelva a su mismo electroterminal de origen al final del día?
4. Sobre "clusterizar": ¿esperan agrupamiento por ruta/terminal (como proponemos) o algún criterio particular?
5. ¿Es aceptable estimar el deadhead con distancia euclidiana × factor calibrado con OSM?

---

### Referencias clave para la nueva metodología
- Kliewer, N., Mellouli, T., & Suhl, L. (2006). A time–space network based exact optimization model for multi-depot bus scheduling. *European Journal of Operational Research*, 175(3), 1616–1627.
- Freling, R., Wagelmans, A. P. M., & Paixão, J. M. P. (2001). Models and algorithms for single-depot vehicle scheduling. *Transportation Science*, 35(2), 165–180.
- Bunte, S., & Kliewer, N. (2009). An overview on vehicle scheduling models. *Public Transport*, 1(4), 299–317.
- Wen, M., Linde, E., Ropke, S., Mirchandani, P., & Larsen, A. (2016). An adaptive large neighborhood search heuristic for the electric vehicle scheduling problem. *Computers & Operations Research*, 76, 73–83.
- (Ya en el Informe 1) Perumal et al. (2022); van Kooten Niekerk et al. (2017); Alvo et al. (2021); Gao et al. (2024); Wang et al. (2024).

*Verificar los datos bibliográficos exactos antes de citarlos en el informe.*

---
*Cifras obtenidas con un prototipo exploratorio en Python + Gurobi (expansión GTFS + VSP en red espacio-tiempo). Supuestos del prototipo: deadhead euclidiano × 1,3, 20 km/h, layover de 3 min, interlining ≤3 km, sin salida/regreso a electroterminal, SOC inicial 100%. Son órdenes de magnitud para decidir, no resultados finales.*
