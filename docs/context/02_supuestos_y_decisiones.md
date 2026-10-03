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
| A3 | **SOC 100%** | **No es una opción.** Hay que dejar batería para el día siguiente (ciclo diario). Se pueden incluir restricciones del tipo "al terminar el día los buses deben terminar con 80%-90% de carga (y comenzar con eso)". Con SOC 100% "nos estaríamos comiendo un montón de costos y la solución sería miope". | `SOC_INICIAL = 1.0` queda obsoleto. Se adopta SOC cíclico (ver B6) |
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

### B6. SOC cíclico: 90% base, 80% sensibilidad, con tope
**Decisión [Propio, dentro del rango del Profesor]:** todo bus empieza y termina el día con
`SOC_CICLICO` = 90%; la sensibilidad usa 80%. `SOC_CICLICO` es además el tope de carga.

**Por qué exigir la condición cíclica (inicio = fin):**
1. **[Medido]** Bajo SOC 100% el modelo solo paga la recarga de lo que excede la batería durante la
   jornada: ~150-160 MWh de ~2.150 MWh consumidos. **No paga ~93% de la energía que los buses gastan**:
   cada bus parte con 315 kWh regalados. Es lo que el profesor llamó "comernos un montón de costos".
2. **[Medido]** Con SOC 100% los 700 puestos usan ~5% de su capacidad (~830-890 de 16.800
   horas-cargador/día). La infraestructura de carga, que el Informe 1 presentó como el cuello de
   botella, sería irrelevante: un modelo donde la restricción central nunca se activa no modela el
   problema que dijimos resolver.
3. **[Propio]** Un día de operación es un ciclo que se repite. Terminar con 20% sin pagar la
   recuperación equivale a pedir prestada energía al día siguiente. `SOC_fin ≥ SOC_inicio` es la
   condición terminal/periódica habitual en despacho de baterías. *(No hay cita bibliográfica
   verificada; si se quiere en el informe, hay que buscarla.)*

**Por qué un nivel fijo de 80-90% y no 100%:** el profesor dio el rango sin explicar el motivo. Las
razones que el grupo puede defender, todas **[Propio]**:
1. **Validez del modelo de carga (la más fuerte).** El modelo asume carga lineal a 180 kW; en la
   realidad la fase final (~90-100%) es lenta (curva CC-CV). Un tope en 90% deja al modelo en la
   zona donde la aproximación lineal es más fiel.
2. **Vida útil de la batería.** Es práctica habitual evitar el 100% sostenido. **No está en los datos
   ni lo dijo el profesor**: presentarlo como práctica común, no como hecho del proyecto.
3. **Fijo y no variable de decisión.** Una variable más no aporta a lo que se quiere mostrar, y fijarlo
   deja la sensibilidad limpia (un solo parámetro).

**Qué mide la sensibilidad 90% → 80% [Medido]:**

| | SOC 100% (rechazado) | Ciclo 90% | Ciclo 80% |
|---|---|---|---|
| Energía utilizable entre cargas | 315 kWh | 280 kWh | 245 kWh |
| Jornadas con recarga a mitad del día, caso base (8.654 buses) | 30,1% | 45,2% | 59,1% |
| Ídem, con interlining (7.456 buses) | 38,9% | 57,5% | 76,0% |
| Energía pagada dentro de la jornada (caso base) | 6,9% del consumo | 12,1% | 19,4% |
| Energía a recargar en el día | ~830-890 h-cargador | ~12.000 h-cargador | ~12.000 h-cargador |
| Uso global de los 700 puestos | ~5% | ~72% | ~72% |

Con inicio = fin se recarga **todo lo consumido** en ambos niveles, así que 80% **no implica más
energía total**. Cambia la **holgura intradía**: cuántas jornadas necesitan recargar a mitad del día.
Esa es la lectura correcta de la sensibilidad.

**Sobre una idea que se discutió** (partir con la batería que cubra justo la ruta más cara): no sirve
como regla, porque la jornada más cara consume **676 kWh** y la batería completa son 350 kWh. Ningún
SOC inicial evita la recarga intermedia. El análisis que sí justifica el 90% con datos propios es
**cuántas jornadas necesitan 0, 1 o 2+ recargas intermedias según el SOC** (a producir, Bloque C).

**Factibilidad [Medido, cota optimista]:** considerando solo las ventanas en que cada bus está fuera
de su jornada, caben ~16.500 horas-cargador contra ~11.900 necesarias (139%). No está descartado que
el ciclo diario sea factible, pero con ~28% de holgura y suponiendo reparto perfecto. Con holgura tan
justa, la forma de programar la carga importa.

### B7. Retorno, puestos y horario de carga
- **[Profesor]** (A5-A7). Se modela: pullout y pullin en el mismo electroterminal; puestos solo para
  carga simultánea; ventana de 24 h.

### B8. Caso base y escalera de escenarios
- **[Profesor]** El caso base es válido. **[Propio]** La escalera E0 → E3 aísla una decisión por
  escalón (ver `01_metodologia.md` §5).
- **Expectativa a verificar:** E2 podría ser idéntico a E1 si la capacidad agregada no se activa.
  Sería un resultado, no un error.

### B9. Unir Los Espinos y Santa Rosa
- **[Medido]** Están a **1,11 km** entre sí; Vespucio Norte y El Conquistador, a 5,86 km; el resto de
  los pares, más lejos. Para la heurística del "más cercano", repartir rutas entre esos dos es casi un
  volado.
- **[Profesor]** Es válido y decisión nuestra, justificando.
- **[Propio]** Se mantienen los dos patios físicos para las distancias, pero se tratan como **un solo
  electroterminal de 270 puestos** (120 + 150): un único grupo de interlining (186 rutas) y cargadores
  compartidos. Se reportan resultados **juntos y separados** (E2b vs E2) para justificar con números
  si conviene unirlos.
- **[Medido] Combinar solo la capacidad no sirve como prueba:** la asignación de C2 no cambia (separados
  ya no aprietan: Los Espinos 89,9%, Santa Rosa 58,6%; juntos 72,5%). El efecto de unir está en el
  interlining (Etapa 2) y en las colas de carga (Etapas 3-4), no en la asignación de la Etapa 1.
- **Como el terminal unido es uno solo**, un bus puede salir de un patio y volver al otro sin violar
  el retorno al electroterminal [Profesor]; hay que dejarlo explícito.

### B10. Otras simplificaciones heredadas
- Día laboral únicamente. Duración y distancia constantes por patrón GTFS. Sin conductores ni turnos.
  La oferta programada hace de demanda. Capacidad de carga constante durante el día.

---

## C. Abierto

| # | Tema | Qué falta | Riesgo |
|---|---|---|---|
| C1 | Factor de desvío 1,3 | Calibración empírica (Bloque B) y feedback de la presentación | La crítica anunciada por el profesor |
| C2 | Cita bibliográfica de la condición cíclica | Buscar y verificar una referencia | Menor: el argumento se sostiene solo, pero conviene citar |
| C3 | Tope de carga en `SOC_CICLICO` | Decisión nuestra, sin respaldo del profesor ni de los datos más que la razón de la curva CC-CV | Si se cuestiona, la alternativa es topar en 100% y partir/terminar en 90% (cambia la energía utilizable) |
| C4 | E2 idéntico a E1 | Confirmar al correr | Que "no cambia nada" requiera explicación en la presentación |
| C5 | Jornadas partidas bajo política reactiva | Cuantificar cuántos buses extra exige el ciclo diario | Puede encarecer fuertemente E0 y E1; es resultado, pero hay que anticiparlo |
| C6 | Unir o no Los Espinos y Santa Rosa | Resultados juntos y separados | Ninguno: es decisión nuestra, falta la evidencia |

---

## D. Sensibilidades planificadas

| Parámetro | Base | Rango | Para qué |
|---|---|---|---|
| `SOC_CICLICO` | 90% | 80% | Holgura intradía (ver B6) |
| Factor de desvío del deadhead | 1,3 | 1,2 / 1,5, y el empírico | Responder la crítica anunciada |
| Velocidad de deadhead | 20 km/h | 15 / 25 | Idem |
| Layover | 3 min | 0 / 10 | Afecta fuertemente la flota |
| Radio de interlining | 3 km | 1 / 5 | Tamaño del problema y ganancia del interlining |
| Holgura de capacidad θ en C2 | 1,0 | 0,9 a 0,6 | Cuándo C2 se separa de C1b (ya medido: desde 0,8) |
| Capacidad de Los Espinos + Santa Rosa | Separadas | Combinada | Decisión B9 |
