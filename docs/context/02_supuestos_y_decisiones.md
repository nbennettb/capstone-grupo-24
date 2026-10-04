# Supuestos y decisiones

> Cada supuesto del proyecto con su estado y su respaldo. Reemplaza a los antiguos documentos de
> preguntas pendientes: todas las preguntas que se llevaron a la reunión con el profesor ya fueron
> respondidas y están integradas acá.
>
> Tres tipos de respaldo, que **no hay que mezclar** en el informe:
> - **[Profesor]**: lo dijo el profesor en la reunión.
> - **[Medido]**: lo calculamos con los datos del proyecto (hay archivo que lo respalda).
> - **[Propio]**: razonamiento del grupo. Es defendible, pero es nuestro, no un hecho.
>
> Metodología completa: [`01_metodologia.md`](01_metodologia.md).

---

## A. Resuelto por el profesor

Respuestas de la reunión, ordenadas según las preguntas que se llevaron.

| # | Tema | Respuesta | Qué implica para el modelo |
|---|---|---|---|
| A1 | **Alcance de la Entrega 2** | Mínimo: (1) caso base completo, con KPIs de una solución factible; (2) metodología bien propuesta, con énfasis en justificar qué se hace y por qué (clusterización y MILP). Se espera haber **probado** parte de la metodología: por ejemplo, aplicar el caso base una vez clusterizado y mirar los costos, para saber qué tan buena es la clusterización. Si se modela un MILP, esperan que se haya **testeado en instancias pequeñas**, no en el modelo completo. | Define el alcance: escalera de escenarios (caso base → con clustering) y MILP de carga en instancia chica |
| A2 | **Caso base** | La operación por línea (sin interlining) con carga reactiva **es válida**. Hay que ser muy conscientes de qué esperamos que pase y verificar si el caso base lo refleja. Al prohibir el interlining, toda la ganancia aparece al habilitarlo: sirve para medir el efecto marginal de cada supuesto. Si no es difícil, conviene un **segundo caso base con interlining** para ver el efecto aislado de esa decisión (puede ser igual de complejo computacionalmente). | Escalera E0 → E1: sin interlining y con interlining, ambos con carga reactiva |
| A3 | **Batería al cerrar el día** | **[Profesor]** Debe quedar batería para el día siguiente: la solución no puede terminar el día sin recuperar la energía consumida. Como **ejemplo**, mencionó 80%-90% al inicio y al final; **no fue una instrucción de nivel**. Con SOC 100% sin recuperación, "nos estaríamos comiendo un montón de costos y la solución sería miope". | `SOC_INICIAL = 1.0` queda obsoleto. Se adopta la condición cíclica (inicio = fin). El **nivel** se decide con datos (B6) |
| A4 | **Deadhead euclidiano** | Depende de la modelación (decisión nuestra), pero "si es euclidiana probablemente nos la critiquen". El grupo decidió, por tiempo, mantenerla para la presentación y esperar feedback; el informe puede cambiarla. | Se mantiene el factor 1,3, pero con una justificación concisa y verificable, no una caja negra (ver B2) |
| A5 | **Retorno al electroterminal** | Sí: cada bus debe volver a su terminal. Debe comenzar y terminar su jornada en su terminal, y eso **no usa un puesto de carga** a menos que se decida cargarlo. | Pullout y pullin en el mismo electroterminal. El modo `libre` pasa a ser solo cota inferior |
| A6 | **Puestos del electroterminal** | Los puestos limitados son **de carga**; se pueden guardar buses ahí sin restricción en cualquier horario. | La capacidad es solo de carga simultánea. No hay problema de estacionamiento |
| A7 | **Horas de carga al día** | No hay restricción: el electroterminal puede cargar todo el tiempo. La única restricción son los puestos. | Ventana de 24 h (H = 24). Los escenarios con 10 u 18 h dejan de ser relevantes |
| A8 | **Unir Los Espinos y Santa Rosa** | Es modelación, depende de nosotros. Es **válido**, no dice si es lo correcto; siempre justificando la decisión. | Se implementa como variante, con resultados juntos y separados (ver B9) |
| A9 | **Flota** (reunión anterior) | **Irrestricta.** El `fleet_size = 1200` de `parameters.csv` está obsoleto. | `parametros.py` lo ignora a propósito |
| A10 | **Costo de la energía inicial** (se desprende de A3) | Con ciclo diario, toda la energía que se recarga se paga, incluida la recarga final que restituye el nivel del día siguiente. | La condición cíclica resuelve esta pregunta: no hay energía "gratis" de partida |

**Sobre la presentación [Profesor].** Las entregas son acumulativas: no hay que perder tiempo en lo
que era propio de la introducción del problema de la entrega pasada. Si algún análisis sirvió para
**tomar una decisión de metodología, hay que contarlo como parte de la historia**. Ejemplo del
profesor: "detectamos que todos los terminales están lejos menos estos dos, que están a x distancia, y
eso puede hacer que los juntemos después".

---

## B. Decisiones de modelación nuestras

### B1. La unidad de clusterización es la ruta
- **[Medido]** 94,7% de las 300 rutas con ida y vuelta cierra la ida a menos de 500 m de donde empieza
  la vuelta (mediana 85 m). Archivos: `data-processed/rutas_ida_vuelta.csv`,
  `results/etapa0_preprocesamiento/graficos/ida_vuelta_distancia.png`.
- **[Propio]** Asignar expediciones sueltas rompería ese encadenamiento natural y aumentaría la flota.
- **Limitación:** 15 de las 300 rutas usan más de un paradero como inicio o fin de un sentido.

### B2. Deadhead: distancia euclidiana × 1,3, a 20 km/h, layover de 3 min, radio de interlining 3 km
- **[Propio]** Elegidos por tiempo, sin calibrar. El 1,3 fue una suposición inicial, no un resultado.
- **Qué hay que hacer:** justificarlo con evidencia propia. Propuesta (Bloque B del plan): comparar,
  para los 839 trazados GTFS, el largo real del trazado contra la distancia euclidiana entre sus
  extremos. Es un factor de rodeo empírico, sin internet ni `osmnx`.
- **Salvedad honesta:** una ruta comercial rodea más que un deadhead (va sirviendo paraderos), así que
  ese factor es una **cota superior** del rodeo del deadhead. Si resulta cercano o mayor que 1,3, el
  1,3 es razonable y conservador.
- **Sensibilidad planificada:** factor 1,2 / 1,3 / 1,5; velocidad 15 / 20 / 25 km/h; layover 0 / 3 / 10 min.

### B3. Consumo constante (1,4 kWh/km) y carga lineal (180 kW)
- **[Dato]** Consumo = 350 kWh / 250 km. **[Propio]** Se ignoran topografía, congestión y la curva
  CC-CV de la carga real.

### B4. Buses por ruta estimados por concurrencia máxima
- **[Propio]** Cota inferior (ignora layover y retorno). Suma 7.388 contra 7.456 buses del VSP con
  clustering. Solo se usa para **ponderar** rutas en la Etapa 1, no como cifra de flota.

### B5. La capacidad de C2 es un promedio diario en horas-cargador
- **[Propio]** Simplificación para decidir una asignación antes de tener las jornadas. Los dos lados
  de la restricción están en horas-cargador/día.
- **Límite:** no ve la concentración horaria de la carga. Un electroterminal puede saturarse en horas
  punta aunque su promedio diario sea 70%. Esa saturación aparece como colas en el simulador reactivo.

### B6. Condición cíclica y nivel de carga
**[Profesor]** Debe quedar batería para el día siguiente (condición cíclica: inicio = fin). El rango
80%-90% fue un **ejemplo** mencionado en la reunión; no es una instrucción sobre el nivel.

**[Decisión] El nivel se busca con datos, no se fija por criterio propio.**
- **Punto de partida: 100%**, el máximo de batería que dan los datos del curso (`max_soc = 1.0` en
  `parameters.csv`). Es el único límite superior que viene en los datos.
- **Búsqueda:** barrido de niveles 100%, 90%, 80%, 70%. Para cada uno se mide costo total, buses,
  eventos de carga, jornadas partidas y % de jornadas con recarga intermedia.
- **Criterio de elección, declarado antes de correr:** el nivel que **minimiza el costo total** del
  caso base con ciclo. Si el óptimo es 100%, ese es el resultado y no requiere supuesto adicional.
- **Bajar de 100% solo con una razón externa citada** (por ejemplo, la fase CC-CV de la carga o la vida
  útil de la batería). Hoy no tenemos fuente verificada para ninguna de las dos. Si aparece y el nivel
  óptimo cambia, se reporta como caso alternativo, nunca reemplazando el resultado del barrido.
- **Hipótesis a verificar en el barrido (no afirmada):** con inicio = fin, la energía total cargada no
  depende del nivel. Un nivel más alto debería reducir recargas intermedias, eventos (5 USD cada uno)
  y jornadas partidas. Si el barrido no lo confirma, se reporta tal cual.

**Regla del barrido.** *Declarada el 04/10/2026, antes de correr cualquier nivel distinto de 100%. **Corregida el 04/10/2026,
antes de volver a correr**, por un error de diseño: la versión original comparaba cada nivel contra el 100%, que a su vez
incumplía la condición cíclica (21% de las cargas nocturnas terminaba después de la primera salida del día siguiente), y
trataba los "ciclos no cumplidos" como un indicador y no como una restricción. Lo detectamos antes de presentar.*

**Principio:** la condición cíclica (inicio = fin) es una **restricción** [Profesor]; el nivel se elige **entre las
soluciones que la cumplen**, y entre ellas, la de menor costo. Un bus que no termina de cargar antes de su salida del día
siguiente se reemplaza por un **bus de reserva** ya cargado (250 USD/día): en estado estacionario es una rotación (el
bus atrasado termina de cargar, con atraso < 24 h, y es la reserva del día siguiente). El costo total incluye las
reservas. Se decide el nivel en **E1** (C1b, con interlining, Los Espinos y Santa Rosa unidos: la configuración
propuesta); **E0** (por línea, unidos) se corre como **robustez**. *Por qué no se decide en los escenarios con
terminales separados (E0_sep, E1_sep):* son infactibles por déficit de energía en Los Espinos a cualquier nivel y no
compiten; se muestran como evidencia de la unión.
1. **Grilla obligatoria:** 100, 90, 80, 70, 65, 60, 55 y 50%. 100% es el dato del curso y el punto de partida; 90 y 80%
   son los ejemplos del profesor; los niveles menores permiten ver si el costo sigue bajando o si algún nivel llega a
   cumplir el ciclo sin reservas; **50% es el piso físico** (el menor nivel con que toda expedición se puede hacer
   partiendo y volviendo al electroterminal sin bajar del 10%; la expedición más exigente necesita 41,8% de la batería).
2. **Factibilidad.** Solo compiten las soluciones **factibles**: sin déficit de energía y con todo atraso de carga
   menor a 24 h. Con déficit (la energía no se puede reponer por falta de puestos) las reservas no la arreglan.
3. **Dos familias, reportadas lado a lado:** (a) **cíclica sin reservas** (0 ciclos no cumplidos) y (b) **con reservas**
   (cualquier nivel factible, con el costo de sus reservas). *Por qué:* responde la pregunta "¿existe un nivel que haga
   cíclica la operación sin pagar reservas, y cuánto cuesta frente a 100% + reservas?".
4. **Criterio.** Entre todas las soluciones factibles de (a) y (b), la de **menor costo total** (flota + km vacíos +
   espera + energía + eventos de carga + reservas). *Por qué:* es el objetivo del proyecto.
5. **Empate práctico.** Si dos niveles difieren en menos de **0,5% del costo total**, se elige el **más alto**. *Por qué
   0,5%:* es el orden de magnitud del efecto del parámetro menos seguro del modelo (pasar el factor de desvío del
   deadhead de 1,3 al valor medido de 1,35 cambia el costo de operación en +0,6%, Bloque C); diferencias menores no se
   distinguen del error del modelo. *Por qué el más alto:* es el dato del curso (`max_soc = 1,0`) y no requiere un
   supuesto adicional.
6. **Robustez (no decide, se reporta).** Si el nivel óptimo de E0 coincide con el de E1, la elección no depende de la
   decisión de interlining.
7. **Razón externa para bajar de 100%.** Solo con fuente citada (CC-CV, vida útil); si aparece y cambia el óptimo, se
   reporta como caso alternativo y no reemplaza el resultado del barrido.
8. **Cota de factibilidad (evidencia, no decide).** Para cada nivel se calcula el máximo de energía de las cargas finales
   que cabe dentro de las ventanas de los buses con una carga **perfecta** (LP). Si es menor a 100%, ningún programa de
   carga, ni el MILP, cierra el ciclo con esas jornadas.

Documentada para el informe en `docs/justificaciones/04_nivel_carga_ciclico.md`.

**Resultado del barrido (04/10/2026): el nivel base es 100%, con buses de reserva.** En E1, el menor costo total entre los
niveles factibles es 100% (3.751.250 USD/día con 2.207 reservas); 90% +5,9%, 80% +8,5%, 70% +17,9%, 65% +26,3%,
60% +38,8%, 55% +52,8%; 50% es infactible (déficit de 25 MWh). E0 elige lo mismo: la elección es robusta. Hallazgos:
- **Ningún nivel entre 100% y 55% cumple el ciclo sin reservas** con la política reactiva; el que más se acerca (55%)
  deja 13 reservas pero cuesta 52,8% más. Bajar el nivel no arregla el ciclo: lo paga con flota (cada 10 puntos menos
  agregan ~1.500 buses por jornadas partidas).
- **La cota LP:** al 100% solo cabe el 84% de la energía nocturna (faltan 354 MWh/día); desde 80% hacia abajo cabe el
  100%, es decir, con una carga perfecta el ciclo sí sería posible, pero esa solución costaría ≥ 4,0 M USD/día sin
  reservas, más que 100% con reservas (3,75 M).
- Hipótesis confirmada: más nivel, menos recargas intermedias y menos jornadas partidas. Hipótesis solo aproximada: la
  energía total cargada sube 6% al bajar a 70% por los traslados de las jornadas partidas.

**Por qué exigir la condición cíclica (inicio = fin)** — medido, no depende del nivel:
1. **[Medido]** Bajo SOC 100% sin recuperación, el modelo solo paga la recarga de lo que excede la
   batería durante la jornada: ~150-160 MWh de ~2.150 MWh consumidos. **No paga ~93% de la energía que
   los buses gastan**: cada bus parte con 315 kWh sin costo.
2. **[Medido]** Sin recuperación, los 700 puestos usan ~5% de su capacidad (~830-890 de 16.800
   horas-cargador/día). Con ciclo, ~72%. Un modelo donde la restricción central nunca se activa no
   modela el problema que dijimos resolver.
3. **[Propio]** Un día de operación se repite. Terminar sin recuperar la energía equivale a usarla
   prestada del día siguiente. Es la condición periódica habitual en despacho de baterías. *(Sin cita
   bibliográfica verificada.)*

**Razones que podrían justificar un nivel menor que 100%** — ninguna verificada, todas **[Propio]**:
1. **Modelo de carga.** Se asume carga lineal a 180 kW; la fase final de carga real suele ser más lenta
   (curva CC-CV). Un tope menor dejaría al modelo en la zona donde la aproximación es más fiel. *Falta
   una fuente para el CC-CV.*
2. **Vida útil de la batería.** Práctica habitual evitar el 100% sostenido. *No está en los datos ni
   lo dijo el profesor; sin fuente, no se presenta como hecho.*

**Medido por nivel** (sobre las jornadas de la ronda anterior, caso base; se regenera con el barrido):

| | Nivel 100% (base, datos) | Nivel 90% | Nivel 80% |
|---|---|---|---|
| Energía utilizable entre cargas | 315 kWh | 280 kWh | 245 kWh |
| Jornadas con recarga a mitad del día, caso base (8.654 buses) | 30,1% | 45,2% | 59,1% |
| Ídem, con interlining (7.456 buses) | 38,9% | 57,5% | 76,0% |
| Energía pagada dentro de la jornada (caso base) | 6,9% del consumo | 12,1% | 19,4% |
| Energía a recargar en el día (ciclo) | ~12.000 h-cargador | ~12.000 | ~12.000 |

El nivel **no cambia la energía total a recargar** bajo la condición cíclica; cambia cuántas jornadas
necesitan recargar a mitad de día. Esa es la lectura correcta de cualquier barrido.

**Sobre una idea que se discutió** (partir con la batería que cubra justo la ruta más cara): no sirve como
regla, porque la jornada más cara consume **676 kWh** y la batería completa son 350 kWh. Ningún SOC
inicial evita la recarga intermedia. Lo que sí aporta es el análisis de **cuántas jornadas necesitan 0,
1 o 2+ recargas intermedias según el nivel** (Bloque C).

**Factibilidad [Medido]. La cota anterior de "139% de holgura" queda REFUTADA.** Se calculó sumando las ventanas en
que cada bus está fuera de su jornada, sin mirar a qué hora está cada bus en el patio. Con las jornadas del VSP los
buses vuelven de noche y los puestos no alcanzan en esas horas: el LP con las ventanas reales muestra que al 100% solo cabe
el 84% de la energía nocturna (E1) y el 89,5% (E0). La condición cíclica no es factible con una carga perfecta al
100%; se cumple pagando buses de reserva, o con niveles ≤ 80% (a mayor flota).

### B7. Retorno, puestos y horario de carga
- **[Profesor]** (A5-A7). Se modela: pullout y pullin en el mismo electroterminal; puestos solo para
  carga simultánea; ventana de 24 h.

### B8. Caso base y escalera de escenarios
- **[Profesor]** El caso base es válido. **[Propio]** La escalera E0 → E1 → E3 aísla una decisión por
  escalón (ver `01_metodologia.md` §5). **Todos los escenarios operacionales tratan Los Espinos y Santa Rosa como un
  solo electroterminal** (B11): E0 es "por línea + carga reactiva + terminales unidos", y es **factible** (con buses de
  reserva para el ciclo). Los escenarios con terminales separados (E0_sep, E1_sep) son infactibles por déficit de
  energía y se muestran como evidencia.
- **Expectativas que se verificaron:** (1) E1 mejora a E0 (−1.288 buses en el VSP); (2) unir elimina el déficit de
  energía de Los Espinos (44-48 MWh → 0); (3) el ciclo se puede cumplir: **no** con la política reactiva a ningún nivel
  (se cumple con reservas), y la cota LP muestra que al 100% ni una carga perfecta lo cerraría.

### B9. Unir Los Espinos y Santa Rosa
- **[Medido]** Están a **1,11 km** entre sí; Vespucio Norte y El Conquistador, a 5,86 km; el resto de
  los pares, más lejos. Para la heurística del "más cercano", repartir rutas entre esos dos es casi un
  volado.
- **[Profesor]** Es válido y decisión nuestra, justificando.
- **[Propio]** Se mantienen los dos patios físicos para las distancias, pero se tratan como **un solo
  electroterminal de 270 puestos** (120 + 150): un único grupo de interlining (186 rutas con C1b) y cargadores
  compartidos. Se reportan resultados **juntos y separados** (E1 vs E1_sep) para justificar con números
  si conviene unirlos. **Decisión: se unen en todos los escenarios operacionales (B11).**
- **[Medido] Evidencia de la unión (nivel 100%):** con la carga real, Los Espinos separado necesita
  98,5-104% de su capacidad (déficit de energía de 21-48 MWh en el simulador, infactible) y unido a Santa Rosa
  82,5% (déficit 0, factible). Además el VSP baja 94 buses en E1 (E1_sep → E1: 7.460 → 7.366) y el costo total con carga
  (con reservas) baja de 3.849.470 a 3.751.250 USD/día; en E0 el VSP no cambia, pero E0_sep es infactible y E0 no.
- **Como el terminal unido es uno solo**, un bus puede salir de un patio y volver al otro sin violar
  el retorno al electroterminal [Profesor]; hay que dejarlo explícito.

### B10. Otras simplificaciones heredadas
- Día laboral únicamente. Duración y distancia constantes por patrón GTFS. Sin conductores ni turnos.
  La oferta programada hace de demanda. Capacidad de carga constante durante el día.

---

### B11. Asignación base: C1b con Los Espinos y Santa Rosa unidos; C2 queda como propuesta
**Decisión [Propio]** (04/10/2026). La asignación de rutas a electroterminales de la entrega es **C1b** (en el
relato, "C1"): el electroterminal más cercano a los paraderos terminales reales de cada ruta; y Los Espinos y Santa
Rosa se tratan como un solo electroterminal en **todos** los escenarios operacionales (B9). **C2** (MILP con
capacidad) se formula, se prueba y se valida, pero no entra al caso base. Nomenclatura vigente: E0 (por línea, unidos),
E1 (+ interlining, unidos), LB; E0_sep y E1_sep (separados, evidencia); E1_C2 y E1_C2_sep (variantes con C2).
- **[Medido]** C2 mueve **5 de 417 rutas** (con la carga corregida, C7), el VSP cambia en +2 buses (+0,03%) y el costo
  total con carga mejora 0,3% si además se unen los terminales (E1: 3.751.250 → E1_C2: 3.740.069 USD/día).
- **[Medido]** C2 **no resuelve el problema de capacidad**: sin unir (E1_C2_sep), Los Espinos usa 98,5% de su capacidad
  real y aun así el simulador deja 21 MWh sin reponer (C8). Unir los dos terminales sí lo resuelve (82,5%, déficit 0).
- **[Propio]** C1b es simple y explicable; C2 aporta rigor (GAP con carga que depende del electroterminal) pero su
  parámetro θ no está calibrado. Queda como **metodología propuesta** (el profesor pidió una metodología bien
  propuesta, incluido el modelo de clusterización) y como continuación: calibrar θ con el simulador o delegar la carga
  al MILP (Etapa 4).
- **[Profesor]** Unir los terminales es válido y es decisión nuestra, siempre justificando; la justificación son los
  datos de arriba (`docs/justificaciones/05_unir_terminales.md`).
- **C1a (centroide)** se conserva como control de sensibilidad (cambia 41 rutas y 0,7% del costo de pullout/pullin), sin
  usarse en etapas posteriores. La limpieza (borrarlo y renombrar `c1b` → `c1`) queda para la entrega final.

---

## C. Abierto

| # | Tema | Qué falta | Riesgo |
|---|---|---|---|
| C1 | Factor de desvío 1,3 | Calibración empírica (Bloque B) y feedback de la presentación | La crítica anunciada por el profesor |
| C2 | Cita bibliográfica de la condición cíclica | Buscar y verificar una referencia | Menor: el argumento se sostiene solo, pero conviene citar |
| C3 | Nivel de carga cíclico | **Resuelto: 100% con buses de reserva.** Es el máximo de los datos del curso y el barrido 100-50% (regla de B6, corregida y aplicada por código) lo confirma como el de menor costo total entre las soluciones factibles, en E1 y E0. Ningún nivel entre 100% y 55% cumple el ciclo sin reservas; bajar el nivel lo paga con flota. Cualquier nivel menor exigiría además una fuente externa que hoy no tenemos (CC-CV, vida útil) | Ninguno. Si el grupo prefiriera un nivel menor, debe citarse la razón y se reporta como caso alternativo |
| C4 | E2 idéntico a E1 | **Resuelto:** era un artefacto del estimador de carga de C2 (C7). Con la carga corregida, C2 mueve 5 rutas y el VSP cambia en +2 buses; con la nueva nomenclatura la comparación es E1_C2_sep vs E1_sep | Ninguno |
| C5 | Jornadas partidas bajo política reactiva | **Medido (nivel 100%):** +2.605 buses en E0 (+30%) y +2.955 en E1 (+40%); casi toda jornada sobre la batería se parte porque los huecos son cortos y el electroterminal queda a ~10 km | Es el resultado más fuerte del caso base; hay que presentarlo como precio de la descomposición secuencial, no como error |
| C6 | Unir o no Los Espinos y Santa Rosa | **Resuelto: se unen en todos los escenarios operacionales.** Evidencia (nivel 100%): sin unir la solución es infactible (déficit de energía de 21-48 MWh en Los Espinos) y unidos es factible (82,5% de la capacidad, déficit 0); además el VSP baja 94 buses en E1 | Ninguno: es decisión nuestra con respaldo medido |
| C7 | La Etapa 1 (C2) medía la carga de cada ruta solo con su energía comercial | **Resuelto el 04/10:** $h_{rd}=(\text{kWh}_r+2\,\text{dist}_{rd}\,n_r\,1{,}4)/180$, que depende del electroterminal (GAP). Validado contra la energía real de las jornadas: error de −9 a −14% pasa a −0,5 a −3,1%. Con ella C1b excede Los Espinos (101,6%) y C2 mueve 5 rutas (Los Espinos 97,6%). Ver `docs/justificaciones/08_carga_real_en_clustering.md` | Subestima levemente (traslados entre viajes); se declara como limitación |
| C8 | La capacidad de C2 es un promedio diario: respetar θ = 1 es necesario, no suficiente | Con C2 sin unir (E1_C2_sep) Los Espinos usa 98,5% de su capacidad real y el simulador reactivo deja 21 MWh sin reponer (la carga solo ocurre cuando los buses están en el patio). **Por eso C2 queda como propuesta** (B11). Continuación: calibrar θ < 1 con el simulador o programar la carga (MILP, Etapa 4) | Presentar C2 como "la asignación factible" lo contradice el simulador; se presenta como propuesta con su límite declarado |
| C9 | La condición cíclica no se cumple con la política reactiva a ningún nivel | **Medido:** al 100% el 21% de las cargas nocturnas (2.207 de 10.295 en E1) termina después de la primera salida del día siguiente; la cota LP dice que solo cabe el 84% de la energía nocturna aun con carga perfecta. Se cumple con buses de reserva (551.750 USD/día en E1). Continuación: el MILP de carga (Etapa 4) con reservas o con ventanas de día; o un VSP que "vea" la batería (jornadas con pausas de carga) | Es el resultado más fuerte del caso base: el VSP que ignora la batería produce jornadas que no se pueden recargar a tiempo. Hay que presentarlo como el precio de la descomposición secuencial, no como un error |

---

## D. Sensibilidades planificadas

| Parámetro | Base | Rango | Para qué |
|---|---|---|---|
| `SOC_CICLICO` | 100% (datos del curso, `max_soc`) | 90%, 80%, 70% | Holgura intradía y costo. Barrido completo en B6 |
| Factor de desvío del deadhead | 1,3 | 1,2 / 1,5, y el empírico | Responder la crítica anunciada |
| Velocidad de deadhead | 20 km/h | 15 / 25 | Idem |
| Layover | 3 min | 0 / 10 | Afecta fuertemente la flota |
| Radio de interlining | 3 km | 1 / 5 | Tamaño del problema y ganancia del interlining |
| Holgura de capacidad θ en C2 | 1,0 | 0,9 a 0,6 | Cuándo C2 se separa de C1b (ya medido: desde 0,8) |
| Capacidad de Los Espinos + Santa Rosa | Separadas | Combinada | Decisión B9 |
