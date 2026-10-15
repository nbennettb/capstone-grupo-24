# Registro de decisiones

Cada decisión de modelación del proyecto, de la Etapa 0 a la 4, en el mismo formato: **qué** se decidió, **por qué**,
qué **alternativa** se descartó, la **evidencia** (medida o razonada) y **dónde** está en el código. Los valores
numéricos viven solo en `scripts/common/parametros.py`. Las conversaciones con el profesor aparecen solo como contexto:
las decisiones son del grupo y se sostienen con datos o razones.

Cómo se lee la evidencia:
- **medido**: sale de un script del repositorio;
- **razonado**: es un argumento;
- **se mide en la corrida**: la cifra la produce la corrida de la instancia y queda en `results/instancia_LR/resumen_para_analisis.md`.

---

## A. Datos y preprocesamiento (Etapa 0)

### A1. Día laboral tipo
- **Qué:** se modela un día laboral (lunes a viernes, `DIA_TIPO = "L"`).
- **Por qué:** es el día de mayor demanda y el que define la flota. Los otros días necesitan menos buses.
- **Alternativa:** modelar sábado y domingo. Se descartó porque no cambia el dimensionamiento.
- **Evidencia:** razonado; las frecuencias del día L son las de mayor servicio.
- **Dónde:** `scripts/2-filtro_tipo_dia.py`.

### A2. Una expedición por salida real
- **Qué:** cada frecuencia (patrón con intervalo) se expande a sus salidas reales. Resultan 64.502 expediciones con origen, destino, horas, km y kWh = km × 1,4.
- **Por qué:** el VSP asigna salidas, no patrones. `trip_id` se repite por frecuencia, así que la clave es `expedicion_id`.
- **Alternativa:** trabajar con patrones agregados. No permite asignar buses.
- **Evidencia:** medido; los chequeos de cobertura de todas las etapas usan `expedicion_id`.
- **Dónde:** `scripts/3-preprocesamiento_expediciones.py`, `scripts/common/tiempo.py`.

### A3. Consumo y batería
- **Qué:** 1,4 kWh/km (350 kWh / 250 km de `vehicles.csv`). Batería útil de 315 kWh entre el 10% y el 100%. Carga lineal a 180 kW.
- **Por qué:** son los datos del curso.
- **Alternativa:** una curva de carga CC-CV. No hay datos para calibrarla; queda declarada como limitación.
- **Evidencia:** datos del curso.
- **Dónde:** `parametros.CONSUMO_KWH_KM`, `data-filtrado/parameters.csv`.

### A4. Flota irrestricta
- **Qué:** se ignora `fleet_size` de `parameters.csv`.
- **Por qué:** el objetivo es dimensionar la flota. Un tope la daría por fijada.
- **Alternativa:** respetar el tope. No responde la pregunta del proyecto.
- **Evidencia:** razonado (confirmado como supuesto válido del curso).
- **Dónde:** `parametros.cargar_costos` (avisa y lo ignora).

### A5. Deadhead euclidiano × 1,3 a 20 km/h, en todas las etapas
- **Qué:** todo traslado sin pasajeros (salida del patio, vuelta y encadenamiento entre viajes) se calcula como distancia en línea recta × 1,3, a 20 km/h, más 3 min de maniobra (layover). Vale para todas las etapas, todos los terminales y el caso base.
- **Por qué:** es simple, auditable y no agrega una caja negra. Así el costo de los km vacíos es comparable entre escenarios.
- **Alternativa:** rutas por la red vial de OpenStreetMap. Es más preciso, pero más lento y difícil de verificar. Queda como mejora.
- **Evidencia (medido):** en los 839 trazados GTFS, el rodeo real (recorrido / línea recta) tiene una mediana de 1,04 a 1 km, 1,22 a 3 km, 1,29 a 5 km y 1,35-1,38 a 10-15 km.
  - Para el interlining (≤ 3 km), 1,3 es conservador.
  - Para la salida y la vuelta al patio (mediana ~12 km) está cerca del valor medido.
  - La sensibilidad 1,2 / 1,3 / 1,5 cambia la flota en ±1%.
  - Los trazados son rutas comerciales, que rodean más que un traslado en vacío, así que el valor medido es una cota superior del rodeo.
- **Dónde:** `parametros.FACTOR_DESVIO`, `VELOCIDAD_KMH`, `LAYOVER_MIN`; calibración en `scripts/9-calibracion_deadhead.py`.

### A6. CSV con `;`
- **Qué:** todos los CSV usan `;` como separador.
- **Por qué:** Excel en configuración regional chilena usa la coma como separador decimal.
- **Dónde:** `scripts/common/rutas.py` (`CSV_SEP`).

## B. Asignación de rutas a electroterminales (Etapa 1)

### B1. La unidad que se asigna es la ruta
- **Qué:** cada ruta tiene un electroterminal base, desde el que salen, al que vuelven y donde cargan sus buses.
- **Por qué:** las rutas cierran su ida y vuelta en el mismo lugar. Asignar rutas convierte un problema de 5 depósitos en problemas independientes de un depósito, que el VSP resuelve de forma exacta.
- **Alternativa:** asignar expediciones sueltas. Rompe el encadenamiento natural ida-vuelta.
- **Evidencia (medido):** el 94,7% de las 300 rutas con ambos sentidos termina la ida a menos de 500 m de donde empieza la vuelta (mediana 85 m).
- **Dónde:** `scripts/3-` y `scripts/4-clustering_c1.py`.

### B2. Electroterminal más cercano a los paraderos reales (C1)
- **Qué:** cada ruta va al electroterminal más cercano a sus paraderos terminales reales, ponderados por uso.
- **Por qué:** es simple y explicable. La métrica de distancia casi no cambia el costo.
- **Alternativas:**
  - C1a (centroide de la ruta): se conserva como control;
  - C2 (MILP de asignación con capacidad de carga): queda como propuesta.
- **Evidencia (medido):**
  - C1a y C1 difieren en 41 de 417 rutas, pero el costo de salida y vuelta cambia solo 0,7%.
  - C2 mueve 5 de 417 rutas, cambia el VSP en 0 buses (E1) y mejora el costo total en 0,3%.
  - Además, C2 respeta un promedio diario y no la concentración nocturna: sin unir terminales sigue dejando 21 MWh sin reponer.
- **Dónde:** `scripts/4-clustering_c1.py`, `scripts/5-clustering_c2.py`, `scripts/8-clustering_comparacion.py`.

### B3. La carga de una ruta incluye salir y volver al patio
- **Qué:** en C2, las horas de carga de una ruta son (kWh comerciales + 2 · distancia al patio · buses · 1,4) / 180.
- **Por qué:** un electroterminal recarga todo lo consumido, no solo los viajes con pasajeros. Con la energía comercial sola, la capacidad parecía no restringir.
- **Alternativa:** solo la energía comercial. Subestima la carga entre 9 y 14%.
- **Evidencia (medido):** con la corrección, el estimador subestima solo entre 0,5 y 3,1%. El script falla si el error supera el 5%.
- **Dónde:** `scripts/5-clustering_c2.py`.

### B4. Los Espinos y Santa Rosa son un solo electroterminal
- **Qué:** se suman sus puestos (120 + 150 = 270) y forman un solo grupo de interlining. Sus patios físicos se mantienen para las distancias.
- **Por qué:** están a 1,11 km (el siguiente par más cercano está a 5,86 km). Separados, Los Espinos no tiene puestos para reponer su energía.
- **Alternativa:** tratarlos por separado. La solución resulta infactible.
- **Evidencia (medido):**
  - Separados, Los Espinos necesita 104,0% (E0) y 102,6% (E1) de su capacidad de 24 h y queda un déficit de 44-48 MWh/día.
  - Unidos, la carga baja a 82,5% de la capacidad combinada y el déficit es 0.
  - En E1 la flota del VSP baja en 94 buses.
- **Dónde:** `parametros.ELECTROTERMINALES_UNIDOS`, `scripts/6-` (`--unir-electroterminales`), `scripts/7-comparar_escenarios.py`.

## C. Asignación de buses (Etapa 2)

### C1. VSP como flujo de costo mínimo en una red espacio-tiempo
- **Qué:** por electroterminal, una unidad de flujo es un bus. El costo es bus (250 USD) + km vacíos (0,5 USD/km) + espera entre viajes (0,03 USD/min). La red no ve la batería.
- **Por qué:** la matriz es de red, así que el LP entrega la solución entera exacta, en segundos para toda la red.
- **Alternativa:** un E-VSP integrado con batería. Es intratable a escala de 64.502 viajes.
- **Evidencia (medido):** solución entera en todas las corridas (el script avisa si hay valores fraccionales).
- **Dónde:** `scripts/6-vsp_asignacion_buses.py`.

### C2. Escenarios E0 (por línea) y E1 (con interlining)
- **Qué:**
  - E0: cada ruta solo con sus propios buses;
  - E1: se permite encadenar viajes de distintas rutas del mismo electroterminal;
  - LB: interlining libre entre terminales; es una cota inferior, no un escenario operacional.
- **Por qué:** E0 representa la operación actual (caso base); E1 aísla el efecto del interlining.
- **Evidencia (medido):** en toda la red, E1 usa 14,9% menos flota que E0 y queda a 4,4% de LB.
- **Dónde:** `scripts/6-` (`--modo ruta | cluster | libre`), `scripts/7-`.

### C3. Radio de interlining de 3 km
- **Qué:** dos viajes de distinta ruta se pueden encadenar si el fin de uno está a ≤ 3 km del inicio del otro, medido ya con el factor de desvío.
- **Por qué:** acota el tamaño del modelo. Sin límite habría miles de millones de arcos.
- **Alternativa:** un radio mayor. Ahorra flota con rendimientos decrecientes y alarga el cómputo.
- **Evidencia (medido), sobre E1:** 1 km da +11,3% de buses, 2 km +2,9%, 4 km −2,2% y 5 km −3,4%. El cómputo pasa de ~20 s a ~120 s. El ahorro del interlining que se reporta es un piso.
- **Dónde:** `parametros.RADIO_INTERLINING_KM`.

### C4. Cada etapa se corre una vez y deja archivos
- **Qué:** las Etapas 0-2 escriben sus resultados en `data-processed/` y `results/`. Las etapas siguientes leen esos archivos y no las vuelven a correr.
- **Por qué:** es reproducible y barato, y cada etapa se valida por separado.
- **Dónde:** README y `docs/context/03_como_correr.md`.

## D. Caso base

### D1. El caso base es E0 + carga reactiva + ciclo diario al 100% con buses de reserva
- **Qué:** sobre las jornadas del VSP, cada bus carga solo cuando lo necesita: sin mirar la tarifa ni el futuro, por orden de llegada a los puestos.
  - Si no puede hacer el siguiente viaje y volver al patio, va a cargar.
  - Si ni así alcanza, la jornada se parte y un bus nuevo cubre el resto.
  - Al final del día carga hasta el 100%.
  - Si no termina antes de su primera salida del día siguiente, esa salida la cubre un bus de reserva (250 USD).
- **Por qué:** representa la operación sin planificación de la carga, con reglas simples de explicar. La reserva convierte lo que la carga no alcanza a reponer en flota, una cota superior honesta.
- **Alternativa:** partir al 100% sin exigir que el bus termine el día cargado. Es miope: esconde el costo de reponer la batería.
- **Evidencia (medido):** en la red completa, E0 cuesta 3.958.063 USD/día y E1 3.751.250 USD/día. Además, ningún programa de carga cierra el ciclo al 100% con esas jornadas: con una carga perfecta solo cabe el 84% de la energía nocturna en E1.
- **Dónde:** `scripts/10-caso_base_carga_reactiva.py`.

### D2. Nivel de carga cíclico 100%
- **Qué:** todo bus parte y termina el día al mismo nivel, y ese nivel es el 100%.
- **Por qué:** es el máximo de los datos (`max_soc = 1,0`). Se eligió por costo total entre todas las soluciones factibles de un barrido de 100% a 50%.
- **Alternativa:** niveles menores. Bajar el nivel no cierra el ciclo; lo paga con flota.
- **Evidencia (medido), E1 en la red completa:**
  - 100% + reservas: 3,75 M USD/día;
  - 90%: +5,9%; 80%: +8,5%; 70%: +17,9%;
  - 55% deja 13 reservas pero cuesta +52,8%;
  - 50% es infactible.
  E0 elige lo mismo. Ante una diferencia < 0,5% se prefiere el nivel más alto, porque 0,5% es el orden del efecto del parámetro menos seguro (el factor de desvío).
- **Dónde:** `scripts/11-caso_base_nivel_bateria.py`, `parametros.SOC_BARRIDO_EXTENDIDO`.

### D3. Carga parcial en el caso base
- **Qué:** en una carga intermedia, el bus carga hasta el 100% o hasta que se acabe el hueco, lo que ocurra primero.
- **Por qué:** un operador no partiría una jornada que puede seguir con una carga parcial.
- **Alternativa:** carga completa obligatoria. Favorecería artificialmente los niveles bajos en el barrido.
- **Dónde:** `scripts/10-` (regla 3 del docstring).

### D4. Los puestos limitan solo la carga simultánea
- **Qué:** estacionar no ocupa un puesto, y se puede cargar las 24 horas.
- **Por qué:** es lo que describen los datos del curso.
- **Dónde:** `scripts/10-`, `scripts/13-`.

## E. Instancia reducida de esta entrega

### E1. Un electroterminal completo: La Reina
- **Qué:** las Etapas 3 y 4 y su caso base se prueban en el terminal La Reina completo: 100 puestos, 10.327 expediciones de 67 rutas, 1.333 jornadas E0 y 1.203 jornadas E1. La red completa queda para la entrega final.
- **Por qué:**
  - Tras la Etapa 1 cada electroterminal es un subproblema independiente: sus rutas solo se encadenan entre sí, sus buses salen, vuelven y cargan ahí y sus puestos no se comparten. Por eso un terminal es un problema completo y real, sin escalar puestos ni muestrear jornadas.
  - La Reina es el terminal congestionado más chico: la energía necesaria es el 80% de la capacidad de 24 h y el caso base E1 necesita 315 reservas. Así las dos etapas tienen algo que decidir.
- **Alternativas:**
  - Vespucio Norte: sin congestión (3 reservas), la Etapa 4 se reduciría a "cargar en la hora más barata";
  - una muestra de jornadas con puestos escalados: no responde una pregunta real.
- **Evidencia (medido):** el caso base filtrado al terminal reproduce exactamente las corridas de la red completa filtradas: E0 1.333 → 1.726 buses y 319 reservas; E1 1.203 → 1.638 buses y 315 reservas. El script lo exige con un assert, y esa igualdad prueba la independencia.
- **Dónde:** `parametros.TERMINAL_INSTANCIA`, `scripts/common/instancia.py`, opción `--terminal` de 10-, 12-, 13- y 14-.

### E2. Escalera de escenarios: cada escalón cambia una sola cosa
- **Qué:** la escalera tiene cuatro escalones.
  1. **E0, caso base:** VSP por línea + carga reactiva.
  2. **E1, segundo caso base:** el VSP permite interlining.
  3. **E2-FIFO, propuesta con carga por orden de llegada:** la Etapa 3 reemplaza a la carga reactiva.
  4. **E2, propuesta completa:** la Etapa 4 reemplaza a la FIFO.
- **Por qué:** así cada diferencia se atribuye a una sola decisión. El caso base va bajo su propio título, separado de los escenarios de evaluación.
- **Dónde:** `scripts/14-kpis_instancia.py`.

## F. Etapa 3: cortes y re-encadenamiento con recarga

### F1. Corte por programación dinámica: mínimos tramos y luego mínimos km extra
- **Qué:** cada jornada del VSP se divide en tramos. Un tramo sale del patio con la batería llena y vuelve a él.
  - Es factible si, al terminar cada expedición, lo consumido más la energía para volver al patio no supera 315 kWh: la misma regla de seguridad del caso base.
  - La DP minimiza primero los tramos y, a igualdad, los km extra (vuelta al patio + nueva salida − conexión que se ahorra).
- **Por qué:** cada tramo extra puede costar un bus (250 USD) y cada km extra 0,5 USD; el orden coincide con el costo del proyecto. Además, la DP ve la jornada completa, a diferencia de la reactiva, que decide viaje a viaje.
- **Alternativa:** cortar lo más tarde o lo más temprano posible (sensibilidad P3).
- **Evidencia:** en la prueba chica, 18 de 20 jornadas se cortan en 38 tramos. Todo tramo se revisa paso a paso: SOC ≥ 10% y siempre puede volver. La cifra del terminal se mide en la corrida.
- **Dónde:** `scripts/12-etapa3_cortes_reencadenamiento.py` (`cortar_jornada`, `validar_tramo`), `parametros.REGLA_CORTE`.

### F2. Recarga completa entre tramos
- **Qué:** tras cada tramo, el bus recarga lo que consumió (a 180 kW) antes de tomar otro.
- **Por qué:** cada tramo parte lleno, así que el re-encadenamiento sigue siendo un flujo exacto. Es una diferencia declarada con el caso base, que usa carga parcial.
- **Alternativa:** carga parcial. Requiere seguir el SOC en el flujo, y el problema deja de ser un flujo. Queda como paso futuro.
- **Dónde:** `datos_tramo` (`listo_min`).

### F3. Re-encadenamiento por flujo de costo mínimo, con solo el costo de flota
- **Qué:** los nodos son los tramos y hay una línea de tiempo del patio.
  - El bus del tramo k llega al patio en a_k y queda listo en ρ_k = a_k + E_k/P + h. Desde ahí puede tomar cualquier tramo que salga en s_l ≥ ρ_k.
  - Costo: 250 USD por bus. Los km de cada tramo no dependen de cómo se encadenen.
- **Por qué:** es la misma red de la Etapa 2 (matriz de red), así que la solución es entera y exacta.
- **Evidencia:** chequeo independiente: la flota del flujo = número de cadenas = máximo de intervalos [s, ρ) superpuestos (Dilworth). El script lo exige.
- **Dónde:** `resolver_flujo`, `flota_por_intervalos`.

### F4. Sale primero el bus que lleva más tiempo en el patio
- **Qué:** al armar las cadenas, cada salida del patio la toma, entre los buses listos, el que llegó primero.
- **Por qué:** le da la mayor ventana de carga y es determinista. No cambia la flota: cualquier bus listo da el mismo número.
- **Dónde:** `armar_cadenas`.

### F5. Holgura h = 0 min como base; sensibilidad 0 / 30 / 60
- **Qué:** después de recargar a plena potencia, el bus espera h minutos más antes de poder tomar otro tramo.
- **Por qué:** la Etapa 3 no ve los puestos. La holgura anticipa las colas a cambio de flota: más holgura da más buses en la Etapa 3 y menos reservas en la Etapa 4. La base es 0 porque no hay un valor medido que justifique otro.
- **Evidencia:** en la prueba chica, h = 0 / 30 / 60 da 26 / 28 / 29 buses y 3 / 3 / 1 reservas nocturnas. La cifra del terminal se mide en la corrida.
- **Dónde:** `parametros.HOLGURAS_RECARGA_MIN`, opción `--holgura`.

### F6. Ventanas de carga
- **Qué:** cada tramo genera una ventana.
  - **Intermedia**, entre dos tramos de una cadena: llegada a_k, límite = la siguiente salida del bus.
  - **Nocturna**, tras el último tramo: límite = la primera salida del bus al día siguiente.
  La energía de cada ventana es la del tramo que la precede.
- **Dónde:** `tablas/ventanas.csv` de la Etapa 3.

### F7. El flujo es de un día, no cíclico; las cadenas de más de 24 h van a reserva
- **Qué:** como el VSP, el re-encadenamiento resuelve un día de servicio (00:00 a ~25:40). Una cadena puede durar más de 24 h (por ejemplo, un servicio que sale a las 00:00 y otro tramo que vuelve a la 01:30 del día siguiente). En ese caso la ventana nocturna termina antes de que el bus llegue y esa salida la cubre un bus de reserva en la Etapa 4: la misma regla del caso base.
- **Por qué:** mantiene la comparabilidad con el VSP y con el caso base, que tampoco son cíclicos.
- **Alternativa:** un flujo cíclico de 24 h (flota contada en una hora de referencia). Es más correcto en estado estacionario, pero cambia el modelo del plan y deja de ser comparable. Queda como mejora para la entrega final.
- **Evidencia (medido):** las propias jornadas E1 de La Reina ya traen 24 jornadas de más de 24 h (máximo 27,3 h), y el caso base les asigna reservas (22 de sus 315). El script informa cuántas cadenas duran más de 24 h y cuántas nocturnas no alcanzan la recarga ni con puesto libre: son reservas que ninguna programación de carga puede evitar.
- **Dónde:** `main` de 12- (columnas `cadenas_mas_24h` y `nocturnas_sin_tiempo_carga` de `resumen.csv`).

### F8. Dónde carga y con qué jornadas
- **Qué:** cada bus carga solo en su electroterminal. La entrada son las jornadas E1 del terminal.
- **Por qué:** se respeta el retorno al electroterminal, se mantiene la comparación con el caso base, y E1 es la configuración propuesta.
- **Alternativa:** las Etapas 3-4 sobre E0 (P3).
- **Dónde:** opción `--escenario` de 12-.

## G. Etapa 4: programación de la carga

### G1. Modelo agregado: capacidad escrita en energía por bloque
- **Qué:** las 24 h de una vez, en bloques de Δ min, módulo 24 h.
  - Variables: la energía que cada ventana carga en cada bloque, con tope P·Δ·fracción del bloque disponible; una reserva binaria por ventana; un déficit con penalización.
  - Capacidad: la energía total por bloque ≤ P·Δ·puestos.
  - Objetivo: energía a la tarifa del bloque + 250 USD por reserva.
- **Por qué:** es exacto por bloque si un bus puede enchufarse y desenchufarse dentro de un bloque, salvo en los bloques de borde. El modelo es chico (una binaria por ventana) y es el candidato para escalar a la red completa.
- **Alternativa:** un modelo detallado con enchufe por bloque y costo por evento (G10). Se corre en el mismo terminal para medir el error del agregado.
- **Evidencia:** en la prueba con 3 puestos, la realización por minuto del agregado supera los puestos en 4 / 15 / 50 minutos con Δ = 5 / 15 / 30. Ese es el error de los bordes y se informa.
- **Dónde:** `scripts/13-etapa4_programacion_carga.py` (`construir_segmentos`, `resolver_agregado`, `realizacion_por_minuto`).

### G2. Dos variables por bloque: dentro de la ventana y en la extensión
- **Qué:** un bloque que contiene la hora límite d_w tiene una parte dentro de [a_w, d_w) y otra en la extensión [d_w, a_w + 24 h). Cada parte tiene su propia variable, y solo la de la extensión exige reserva.
- **Por qué:** si la restricción de la extensión se aplicara al bloque entero, obligaría a pagar una reserva aunque la carga termine antes de d_w. La FIFO dejaría de ser una solución factible del modelo y no se podría garantizar E2 ≤ E2-FIFO.
- **Evidencia:** la FIFO llevada a la grilla es factible y tiene el mismo costo de energía que al minuto. El script lo exige.
- **Dónde:** `construir_segmentos`, `fifo_en_grilla`.

### G3. Reserva en ventanas intermedias
- **Qué:** si la carga de una ventana no termina antes de la siguiente salida del bus, un bus ya cargado cubre la salida. En una ventana intermedia, la reserva toma el resto de la cadena.
- **Por qué:** es la misma regla del caso base, aplicada a toda ventana. Es conservador, porque la reserva podría devolverse antes. Se informa por separado en intermedias y nocturnas.
- **Dónde:** restricción de la extensión en `resolver_agregado`; columna `reserva` de `programa_*.csv`.

### G4. Línea de comparación E2-FIFO
- **Qué:** las mismas ventanas de la Etapa 3, cargadas por orden de llegada, a plena potencia y al minuto, con la lógica de puestos del caso base (`buscar_slot`, `reservar` y `costo_energia` de 10-).
  - La carga debe caber en 24 h desde la llegada, el mismo horizonte del modelo.
  - Si no hay un tramo continuo libre, usa los minutos libres que encuentre.
- **Por qué:** así E1 → E2-FIFO aísla la Etapa 3 y E2-FIFO → E2 aísla la Etapa 4.
- **Dónde:** `correr_fifo`.

### G5. Bloques de Δ = 15 min; sensibilidad 5 / 15 / 30
- **Qué:** la base es Δ = 15 min.
- **Por qué:**
  - las tarifas cambian en horas exactas, y Δ debe dividir la hora (el script lo exige);
  - un bloque de 15 min son 45 kWh, así que una carga completa ocupa ~7 bloques;
  - los bordes se tratan con su fracción exacta;
  - el tamaño del modelo es ∝ 1/Δ.
- **Evidencia:** la sensibilidad Δ = 5 / 15 / 30 mide costo, reservas, minutos sobre los puestos y segundos.
  - En la prueba: objetivo 1.685,8 / 1.685,7 / 1.683,9 USD.
  - Un Δ más grueso relaja la capacidad.
  - La cifra del terminal se mide en la corrida.
- **Dónde:** `parametros.DELTA_MIN`, `DELTAS_SENSIBILIDAD`, opción `--delta`.

### G6. Desempate a igual tarifa
- **Qué:** se suma 10⁻⁶ USD/kWh por bloque transcurrido desde la llegada. A igual tarifa, el bus carga lo antes posible y de corrido.
- **Por qué:** dentro de un periodo tarifario hay muchos programas óptimos y el solver puede repartir la carga en bloques sueltos. Eso multiplica los eventos de carga (5 USD cada uno), que el modelo no ve, y vuelve arbitraria la comparación de costo total.
  - El desempate vale como máximo 96·10⁻⁶ USD/kWh, cien veces menos que la menor diferencia de tarifas (0,01 USD/kWh), así que nunca cambia en qué periodo se carga.
  - El objetivo reportado no incluye el desempate.
- **Alternativa:** sin desempate. Se descartó por la evidencia de abajo.
- **Evidencia (medido, prueba chica sin congestión):** sin desempate, E2 tiene 60 eventos contra 38 de la FIFO; con desempate, 38. La energía (849,81 USD) y las reservas son idénticas. Con congestión extrema (3 puestos) la fragmentación persiste: es real (los buses se reparten la capacidad de un bloque) y es parte del error del agregado que mide el modelo detallado.
- **Dónde:** `parametros.DESEMPATE_USD_KWH_BLOQUE`, función `desempate` de 13-.

### G7. Solver y criterio de parada
- **Qué:** Gurobi.
  - Primero el LP (cota inferior) y luego el MILP, con la FIFO como solución inicial.
  - Brecha 0,5% del objetivo, límite 600 s (detallado: 900 s).
  - El déficit se penaliza con 10.000 USD/kWh.
- **Por qué:** la brecha de 0,5% es menor que cualquier diferencia que se quiera interpretar entre escenarios. Si no se alcanza, se reporta la brecha obtenida. La penalización hace que el déficit solo aparezca si la energía no cabe en los puestos en 24 h; debe salir 0.
- **Dónde:** `parametros.GAP_MIP`, `TIEMPO_LIMITE_S`, `PENALIZACION_DEFICIT_USD_KWH`.

### G8. Eventos de carga contados después de resolver
- **Qué:** un evento es un tramo contiguo de bloques con carga de una misma ventana (5 USD).
- **Por qué:** el agregado no modela eventos. Se cuentan sobre la solución con la misma definición para la FIFO (minutos contiguos) y para E2.
- **Dónde:** `programa_desde_segmentos`.

### G9. Ocupación por minuto de E2: se informa, no se exige
- **Qué:** el agregado se valida por bloque. Además, para cada bloque se calcula el mejor reparto por minuto (un LP chico) y se informan los minutos sobre los puestos y el máximo. La FIFO sí se exige por minuto.
- **Por qué:** el agregado es exacto por bloque salvo en los bordes. Exigirle la ocupación por minuto contradiría su definición; medirla dice cuánto se equivoca.
- **Dónde:** `realizacion_por_minuto`.

### G10. Modelo detallado: el agregado más los eventos de carga
- **Qué:** el detallado agrega al agregado tres cosas, con la misma capacidad en energía, las mismas reservas y el mismo déficit:
  - una binaria y = "el bus de la ventana está enchufado en el bloque";
  - el inicio de cada evento (z, 5 USD) en el objetivo;
  - carga continua a plena potencia en los bloques interiores de cada evento.
  Así la única diferencia con el agregado es la estructura de los eventos. Se corre con Δ = 15 y 30, 900 s, partiendo de la FIFO (factible, 1 evento por ventana) y de la solución del agregado.
- **Por qué:** el error principal del agregado en La Reina es la fragmentación.
  - Con los puestos saturados 17,2 h al día, reparte cada bloque entre muchos buses, porque no ve el costo por evento. Resultan 5.894 eventos contra 1.640 de la FIFO (29.470 contra 8.200 USD/día).
  - La cifra depende de Δ: 8,9, 3,6 y 2,3 eventos por ventana con Δ = 5, 15 y 30, lo que muestra que es un artefacto.
  - El detallado mide cuánto cuesta una programación con eventos reales y cuánto tarda, lo que decide qué modelo llevar a la red completa.
- **Alternativa descartada:** la capacidad como número de buses enchufados (Σ y ≤ puestos, "enchufado todo el bloque"). Cuenta dos veces un puesto que cambia de bus a mitad de bloque, así que mide su propio error de discretización. Evidencia (medido sobre la FIFO, que es factible minuto a minuto):

  | Δ | Máx. buses enchufados por bloque | Puesto-horas perdidas por cambios dentro del bloque |
  |---|---|---|
  | 5 | 113 | 123 h |
  | 15 | 137 | 394 h |
  | 30 | 167 | 804 h |

  La carga necesita 1.907 de las 2.400 puesto-horas, así que con Δ = 30 la energía ni siquiera cabría.
- **Evidencia del tiempo:** en una prueba chica con congestión forzada (38 ventanas, 3 puestos, 3.724 binarias), el detallado bajó los eventos de 126 a 39, con las mismas reservas y +1,2 USD de energía. Tardó 401 s en llegar a una brecha de 0,49%. En la instancia completa (~160 mil binarias con Δ = 15) se espera que llegue al límite de tiempo. Se informa la brecha alcanzada.
- **Dónde:** `resolver_detallado` y opción `--detallado` de 13-; sección 11 de `resumen_para_analisis.md` (`detallado_vs_agregado` de 14-).

## H. KPIs y comparación

### H1. Mismas definiciones para todos los escenarios
- **Qué:**
  - Costo total = flota + reservas + km vacíos + espera + energía + eventos.
  - N de buses = operativos + reservas.
  - % km vacíos = km sin pasajeros / km totales.
  - USD/kWh cargado y % de la energía en valle (P1 y P6).
  - Uso máximo de los puestos y horas con todos los puestos ocupados.
  - Buses extra por batería = N de buses − buses del VSP.
  - Además: reservas intermedias y nocturnas, y segundos y brecha de cada modelo.
- **Por qué:** sin definiciones comunes, la escalera no compara lo mismo.
- **Dónde:** `scripts/14-kpis_instancia.py` (docstring y `completar`).

### H2. Espera comparable
- **Qué:**
  - La espera entre viajes se cuenta como en el VSP.
  - En el patio, de día: d_w − a_w − E_w/P.
  - De noche en el patio no se cobra en la versión comparable, porque es estacionamiento.
  - La versión original la cobra como el caso base: desde la llegada hasta el inicio de la primera carga.
  - Para el caso base, la comparable descuenta la cola de las cargas finales (`espera_cola_min`).
- **Por qué:** E2 espera a propósito la tarifa barata. Cobrarle esa espera lo castigaría por algo que su modelo no ve como costo. Se reportan ambas versiones.
- **Dónde:** `resumen_politica` de 13-, `fila_caso_base` y `fila_propuesta` de 14-.

### H3. En el caso base todas las reservas son nocturnas
- **Qué:** si una carga intermedia del caso base no alcanza, la jornada se parte y el bus nuevo cuenta como operativo, no como reserva.
- **Por qué:** es la regla original del caso base, que no cambia. En la comparación, lo relevante es el N de buses total.
- **Dónde:** `fila_caso_base` de 14-.

### H4. Utilización del bus
- **Qué:** horas con pasajeros / (N de buses × 24 h).
- **Por qué:** mide cuánto del día trabaja la flota. Es igual de calculable en todos los escenarios.
- **Dónde:** `completar` de 14-.
