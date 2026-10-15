# Plan: rehacer la implementación de las Etapas 3 y 4 (Entrega 2), instancia reducida en La Reina

> Prompt para la sesión que implementa este plan: `docs/prompt_sesion_implementacion.md`.

## 0. Contexto
- **Problema:** E-VSP de un día laboral. 64.502 viajes, 4 electroterminales (Los Espinos + Santa Rosa unidos) y 700 puestos de carga.
- **Etapas 0-2, sanas y corridas en la red completa:** preproceso, asignación de rutas a electroterminales (C1) y VSP en red espacio-tiempo (E0 por línea, E1 con interlining).
- **Caso base:** se mantiene igual que en la presentación. E0 + carga reactiva + ciclo diario al 100% cumplido con buses de reserva. Su código es `10-carga_reactiva.py`.
- **Qué falló antes:**
  - La "Etapa 3" de la metodología *era* el caso base.
  - El MILP reprogramaba la carga dentro de las ventanas del caso base, en muestras de 10 a 400 buses con puestos escalados.
  - No se entendió qué se comparaba.
- **Objetivo de esta entrega:**
  - Las Etapas 3 y 4 como modelos propios, distintos del caso base.
  - Probados con su caso base en **una instancia reducida bien justificada: el terminal La Reina completo**.
  - Una comparación en la que cada escalón cambie una sola cosa, con tiempos de cómputo y una justificación de cada decisión.
  - **La red completa queda para la entrega final** y se dice explícitamente (el ayudante criticó que antes no se dijo).

## 1. La instancia reducida: el terminal La Reina

**Por qué un terminal completo y no una muestra:**
- Después de la Etapa 1, cada electroterminal es un **subproblema independiente**:
  - sus rutas solo se encadenan entre sí (en E1 el interlining es dentro del terminal);
  - sus buses salen, vuelven y cargan solo ahí;
  - sus puestos no se comparten.
- Por eso un terminal es un problema completo y real: sus viajes, sus buses, sus 100 puestos. **No se escalan los puestos ni se muestrean jornadas.** Eso elimina lo que confundió en la presentación.

**Por qué La Reina.** Las cifras son medidas, del caso base vigente (E1 con carga reactiva):

| Terminal | Puestos | Buses VSP | Energía / capacidad 24 h | Uso promedio de los puestos | Horas de espera por puesto | Buses de reserva |
|---|---|---|---|---|---|---|
| Vespucio Norte | 150 | 793 | 34% | 34,8% | 1.182 | **3** |
| **La Reina** | **100** | **1.203** | **80%** | **80,9%** | **8.852** | **315** |
| El Conquistador | 180 | 2.166 | ~83% | 83,5% | 17.960 | 684 |
| Los Espinos + Santa Rosa | 270 | 3.204 | ~87% | 86,8% | 31.292 | 1.205 |

- **Es el terminal congestionado más chico.** Los puestos sí restringen, así que las dos etapas tienen algo que decidir:
  - la Etapa 3: las jornadas partidas;
  - la Etapa 4: tarifa **y** reservas.
- **Vespucio Norte se descarta.** Sin congestión (3 reservas), la Etapa 4 se reduce a "cargar en la hora más barata" y no prueba el modelo.
- **Los dos terminales grandes quedan para la entrega final** con la red completa.

**Prototipo exploratorio en La Reina** (orden de magnitud; se recalcula con el código final):
- Con una carga perfecta cabe ~81% de la energía en las ventanas.
- Con FIFO, ~622 cargas de 1.640 se atrasan.
- Cargar en las horas baratas ahorraría hasta ~20% de la energía.
- La Etapa 3 tiene un potencial grande de flota (en toda E1: 10.295 + 2.207 reservas → ~7.450 buses).

## 2. La metodología corregida (para 2.3; quien la escribe hoy puede usar esto ya)

```
Etapa 0 Preproceso → Etapa 1 Rutas→electroterminal → Etapa 2 VSP sin batería (jornadas)
  → Etapa 3 Cortes y re-encadenamiento con recarga  (qué bus hace qué tramo y cuándo vuelve al patio a recargar)
  → Etapa 4 Programación de la carga en el patio     (cuándo carga cada bus, con puestos y tarifa)
Caso base (aparte, NO es una etapa): jornadas de la Etapa 2 + política reactiva
```

### Etapa 3: cortes y re-encadenamiento con recarga
**Pregunta:** ¿cómo reorganizar las jornadas del VSP para que todo bus las cumpla con su batería, con la menor flota?

**3a. Corte (programación dinámica por jornada).**
- Cada jornada se divide en **tramos** que un bus hace partiendo del patio con batería llena y volviendo a él.
- Un tramo es factible si, en todo momento, lo consumido más la energía para volver al patio no supera 315 kWh. Es la misma regla de seguridad del caso base.
- La DP minimiza, en ese orden:
  1. el número de tramos;
  2. los km extra del corte (vuelta al patio + nueva salida − conexión que se ahorra).

**3b. Re-encadenamiento (flujo de costo mínimo, la misma red que la Etapa 2).**
- Nodos: los tramos. Línea de tiempo: la del patio.
- El bus que termina el tramo $k$ llega al patio en $a_k$ y queda listo en $\rho_k=a_k+E_k/P+h$: recarga lo consumido a 180 kW, más una holgura $h$.
- Después puede tomar cualquier tramo del terminal que salga del patio en $s_l\ge\rho_k$.

$$\min\ 250\sum_k x_{o,k}\quad\text{s.a.}\quad \textstyle\sum_{\delta^-(k)}x=\sum_{\delta^+(k)}x=1\ \ \forall k,\qquad\text{conservación en la línea de tiempo del patio},\qquad x\ge 0$$

- Es una matriz de red: el LP entrega la solución entera exacta.
- **Salida:**
  - Cadenas, una por bus.
  - **Ventanas de carga** $w$, cada una con llegada $a_w$, hora límite $d_w$ (la siguiente salida del bus; en la nocturna, su primera salida del día siguiente) y energía $E_w$.
- **Qué NO ve:** los puestos. Eso lo resuelve la Etapa 4. La holgura $h$ anticipa colas.
- **Diferencia con el caso base:**

  | | Caso base (reactiva) | Etapa 3 |
  |---|---|---|
  | Cuándo decide | Viaje a viaje | Con la jornada completa a la vista |
  | Si la batería no alcanza | Parte la jornada y el bus queda parado el resto del día | Corta donde menos cuesta |
  | Después de cargar | El bus queda parado | El bus vuelve a servicio con otro tramo |

- **Honestidad:** parte de la mejora viene de permitir que un bus vuelva al patio y salga de nuevo, algo que ni la Etapa 2 ni el caso base permiten. Se mide por separado (§3).

### Etapa 4: programación de la carga en el electroterminal
**Pregunta:** dadas las ventanas de la Etapa 3, ¿cuándo carga cada bus para minimizar energía y buses de reserva sin superar los puestos?

**Modelo agregado** (24 h de una vez, en bloques de Δ = 15 min, módulo 24 h):

$$\min \sum_{w,t}p_t\,e_{wt}+250\sum_w r_w+M\sum_w \delta_w$$

$$\text{s.a.}\quad \sum_t e_{wt}+\delta_w=E_w\ \ \forall w,\qquad 0\le e_{wt}\le P\Delta(\alpha_{wt}+\beta_{wt}),\qquad \sum_{t\in ext(w)}e_{wt}\le E_w r_w,\qquad \sum_w e_{wt}\le P\Delta\,\kappa\ \ \forall t,\qquad r_w\in\{0,1\},\ \delta_w\ge0$$

| Símbolo | Significado |
|---|---|
| $\alpha_{wt}$ | Fracción del bloque $t$ dentro de $[a_w,d_w)$ (el borde se trata sin redondear) |
| $\beta_{wt}$ | Fracción del bloque $t$ dentro de la extensión $[d_w,\ a_w+24\text{ h})$ |
| $r_w$ | **Bus de reserva**, la misma regla del caso base: si la carga no termina a tiempo, un bus ya cargado cubre la salida (250 USD). En una ventana intermedia, la reserva toma el resto de la cadena (supuesto conservador y declarado). Se reporta separada en intermedias y nocturnas |
| $\delta_w$ | Déficit con penalización alta $M$. Debe salir 0 |

- **Por qué la capacidad se escribe en energía y no con binarias de enchufe:** es exacta si un bus puede enchufarse y desenchufarse dentro de un bloque, salvo en los bloques de borde. El modelo resulta chico y es el candidato para escalar a la red completa.
- **Modelo detallado** ($y_{wt}$ binaria "enchufado el bloque", $z_{wt}$ inicio de evento con 5 USD, carga continua dentro del evento). Se escribe en 2.3 y se corre **en el mismo terminal**, con límite de tiempo:
  - mide cuánto se equivoca el agregado;
  - mide cuánto tarda, lo que justifica cuál de los dos llevar a la red completa.
- **Línea de comparación (E2-FIFO):** las mismas ventanas cargadas por orden de llegada, a plena potencia y al minuto, con la lógica de puestos del caso base (funciones de `10-`).

## 3. Escenarios en La Reina (cada escalón cambia una sola cosa)
En el informe, el **caso base** va bajo su propio título, separado de los **escenarios de evaluación** (lo pidió el ayudante).

| Código | Nombre en el informe | Qué cambia respecto del anterior | Qué aísla |
|---|---|---|---|
| E0 | **Caso base** | VSP por línea + carga reactiva | Línea base |
| E1 | Caso base + interlining | El VSP permite interlining | El interlining |
| E2-FIFO | Propuesta con carga por orden de llegada | Etapa 3 en lugar de la reactiva | **La Etapa 3** |
| E2 | **Propuesta completa** | Etapa 4 en lugar de FIFO | **La Etapa 4** |

**Diagnóstico de flota de la Etapa 3** (sin carga; sale del mismo script):

| Paso | Qué mide |
|---|---|
| (i) VSP E1 | Punto de partida |
| (ii) Reuso del patio sin batería | Efecto del reuso |
| (iii) Solo cortes (cada tramo un bus) | Efecto de cortar |
| (iv) Cortes + re-encadenamiento | La Etapa 3 completa |

E0 y E1 en La Reina se vuelven a correr con el simulador del caso base filtrado al terminal. Deben dar **exactamente** lo que ya dicen las corridas de la red completa filtradas a La Reina:

| Escenario | Buses VSP | Tras carga | Reservas |
|---|---|---|---|
| E0 | 1.333 | 1.726 | 319 |
| E1 | 1.203 | 1.638 | 315 |

Esa igualdad es la prueba de que los terminales son independientes.

## 4. Decisiones de implementación (todas van a `docs/context/02_decisiones.md`)

| Decisión | Valor | Por qué | Cómo se prueba |
|---|---|---|---|
| Instancia | Terminal La Reina completo | §1 | Igualdad con la red completa filtrada |
| Regla de corte | Mínimos tramos, luego mínimos km extra | Coincide con el costo del proyecto (km a 0,5 USD); en el prototipo da la menor flota | Tarde / temprano (P3) |
| Recarga completa entre tramos | Sí | Cada tramo parte lleno y el re-encadenamiento sigue siendo un flujo exacto. Diferencia declarada con el caso base (carga parcial) | Paso futuro |
| Holgura $h$ | 0 min base | La Etapa 3 no ve los puestos | **0 / 30 / 60 (P1):** más holgura da más buses y menos reservas |
| Asignación en el patio | Sale primero el que lleva más tiempo en el patio | Mayor ventana de carga; determinista | — |
| Dónde carga | Solo en su electroterminal | Retorno a su electroterminal; comparable con el caso base | — |
| Entrada | Jornadas E1 de La Reina | Configuración propuesta (con interlining) | Etapas 3-4 sobre E0 (P3) |
| Bloques Δ | 15 min | Las tarifas cambian en horas exactas; 45 kWh por bloque (una carga completa ≈ 7 bloques); borde con fracciones; tamaño ∝ 1/Δ | **Δ = 5 / 15 / 30 (P1, barato):** costo, reservas y segundos (responde al ayudante) |
| Solver | Gurobi. Agregado: brecha 0,5% del objetivo de la Etapa 4, 600 s. Detallado: 900 s | Si no se alcanza la brecha, se reporta la alcanzada | — |
| **Espera comparable** | Entre viajes: como en el VSP. En el patio de día: $d_w-a_w-E_w/P$. **De noche en el patio: no se cobra** (es estacionamiento) | E2 no se castiga por esperar la tarifa barata, algo que su modelo no ve | El caso base se reporta con su total original y con el comparable (descontando `espera_cola_min` de las cargas finales) |
| Eventos | Tramos contiguos de bloques con carga × 5 USD, contados después de resolver | El agregado puede repartir la carga | — |
| Deadhead | Euclidiana × 1,3 a 20 km/h en **todos** los traslados y etapas | Respuesta al ayudante. Ya está medido: rodeo real 1,04-1,38 y flota ±1% con factor 1,2-1,5 | Ya existe |

## 5. Archivos

**Parámetro nuevo:** `TERMINAL_INSTANCIA = "4"` (La Reina) en `parametros.py`. Todo se puede cambiar con `--terminal`, de modo que la entrega final repite lo mismo terminal por terminal.

**Todas las salidas de la instancia van a `results/instancia_LR/`**, con subcarpetas `caso_base/`, `etapa3/`, `etapa4/` y `kpis/`, más `resumen_para_analisis.md`.

**Scripts:**

**`10-caso_base_carga_reactiva.py`** (renombrado desde `10-carga_reactiva.py`)
- Se agrega `--terminal`, que filtra las jornadas y los puestos.
- Docstring: "caso base", sin "Etapa 3" ni "insumo del MILP".
- Las corridas de la red completa existentes se mueven a `results/caso_base/` y no se vuelven a correr.

**`11-caso_base_nivel_bateria.py`** (renombrado desde `13-barrido_niveles.py`)
- Solo se actualizan rutas. No se corre.

**`12-etapa3_cortes_reencadenamiento.py`** (nuevo)
- **Qué hace:** DP de corte + flujo (Gurobi, API matricial como `6-`) + diagnóstico (i)-(iv). Opciones `--terminal --escenario E1 --holgura`.
- **Asserts:**
  - cobertura exacta de cada `expedicion_id` del terminal;
  - cada tramo factible al revisarlo paso a paso (SOC ≥ 10% y puede volver);
  - cadenas factibles en tiempo;
  - solución entera;
  - flota = máximo de intervalos $[s_k,\rho_k)$ superpuestos (chequeo independiente);
  - balance de energía;
  - la reconstrucción calza con el VSP (reutilizar `validar_reconstruccion`).
- **Salidas:**
  - tramos, cadenas y ventanas (CSV);
  - gráficos: cadenas de ejemplo tipo Gantt y llegadas al patio por hora;
  - `reporte.md` con tiempos.

**`13-etapa4_programacion_carga.py`** (nuevo)
- **Qué hace:**
  - (a) E2-FIFO al minuto, importando `buscar_slot`, `reservar` y `costo_energia` de `10-`.
  - (b) Agregado: LP (cota) y luego MILP, con `addMVar`, cotas como límite superior de la variable y el FIFO en la grilla como solución inicial.
  - (c) `--delta`.
  - (d) `--detallado`, con límite de tiempo.
  - Un chequeo previo que imprime energía / capacidad de 24 h.
- **Asserts:**
  - energía cargada + déficit = consumida;
  - ocupación ≤ 100 puestos por bloque y por minuto;
  - E2 ≤ E2-FIFO en la grilla.
- **Salidas:**
  - programa por ventana;
  - ocupación por bloque;
  - energía por periodo tarifario;
  - reservas intermedias y nocturnas;
  - estado, brecha y segundos.

**`14-kpis_instancia.py`** (nuevo)
- **Qué hace:** tabla única con las mismas definiciones para E0, E1, E2-FIFO, E2 y las variantes de $h$ y Δ.
- **KPIs:**
  - costo total desglosado (flota, reservas intermedias y nocturnas, km vacíos, espera, energía, eventos), original y comparable;
  - buses: VSP → Etapa 3 → + reservas;
  - % km vacíos;
  - USD/kWh y % en valle;
  - uso máximo y horas saturadas;
  - utilización del bus;
  - segundos por etapa.
- **Gráficos:**
  - escalera de buses;
  - costo apilado;
  - ocupación de puestos en 24 h (E1 vs E2-FIFO vs E2);
  - energía por tarifa;
  - sensibilidades $h$ y Δ.
- **Genera `results/instancia_LR/resumen_para_analisis.md`** (ver §7).

**`16-graficos_informe.py`** (renombrado desde `14-graficos_presentacion.py`)
- Se quitan G4 y G7 y se actualizan las rutas.

**Corregir:**
- `parametros.py`: quitar el bloque del MILP antiguo y agregar `TERMINAL_INSTANCIA`, `REGLA_CORTE`, `HOLGURAS_RECARGA_MIN`, `DELTA_MIN`, `DELTAS_SENSIBILIDAD`, `TIEMPO_LIMITE_S` y `GAP_MIP`.
- Los docstrings de los scripts 1-9 que apuntan a documentos borrados.
- `README.md` y `docs/Estructura_carpeta_proyecto.md`.
- Los encabezados de `docs/Propuesta_metodologia_reunion.md` y `docs/context/00_contexto_entrega1.md`.

**Documentación** (concisa, sin fechas, entendible por alguien ajeno al proyecto):
- **`docs/context/01_como_funciona.md`:** una página. El problema, el pipeline con un diagrama, el caso base vs los escenarios, qué archivo produce cada etapa (cada una se corre una vez: responde al ayudante) y por qué la instancia es La Reina.
- **`docs/context/02_decisiones.md`:** registro de todas las decisiones de la Etapa 0 a la 4.
  - Formato: qué · por qué · alternativa descartada · evidencia · dónde en el código.
  - Absorbe lo esencial de `docs/justificaciones/` (01, 02, 04, 05, 08), que después se borra.
  - Las reuniones con el profesor aparecen solo como contexto.
- **`docs/context/03_como_correr.md`:** la **guía de ejecución** (§7).

## 6. Prioridades
- **P1:**
  1. Etapa 3 en La Reina con el diagnóstico;
  2. caso base E0/E1 filtrado a La Reina;
  3. E2-FIFO y E2 agregado;
  4. holgura 0 / 30 / 60;
  5. Δ = 5 / 15 / 30;
  6. KPIs, gráficos y `resumen_para_analisis.md`;
  7. los 3 documentos;
  8. renombrar.
- **P2:** el modelo detallado en La Reina (Δ = 30 y 15, 900 s) contra el agregado.
- **P3:**
  - regla de corte tarde / temprano;
  - Etapas 3-4 sobre E0;
  - diagrama de la metodología.

## 7. Guía de ejecución y qué reportar (contenido de `docs/context/03_como_correr.md`)
1. **Requisitos:**
   - Python con los paquetes de `README.md` y licencia de Gurobi;
   - no hace falta volver a correr las Etapas 0-2 (sus archivos ya existen).
2. **Comandos en orden**, cada uno con:
   - qué hace en una línea;
   - tiempo y memoria esperados (medidos por la IA en chico y extrapolados);
   - qué debe imprimir si salió bien: los `[OK]` de cada assert y las cifras de control, por ejemplo E1 en La Reina = 1.203 → 1.638 buses y 315 reservas.
   Cada comando escribe sus CSV, así que si uno falla, lo anterior queda guardado.
3. **Qué reportar para el análisis asistido por IA:** un solo archivo generado automáticamente, `results/instancia_LR/resumen_para_analisis.md` (corto, sin CSV pesados), con:
   - descripción de la instancia y parámetros usados;
   - estado de todas las validaciones;
   - la tabla de KPIs por escenario (costo original y comparable);
   - el diagnóstico de flota de la Etapa 3;
   - reservas por tipo;
   - energía por periodo tarifario;
   - ocupación por hora (24 filas por escenario);
   - las sensibilidades $h$ y Δ;
   - segundos, estado y brecha de cada modelo;
   - detallado vs agregado (P2);
   - la lista de figuras con su mensaje en una línea.
   Eso más las figuras es lo que se entrega para escribir 2.7, 2.8 y Conclusiones.
4. **Problemas comunes:**
   - licencia de Gurobi;
   - falta de memoria: bajar Δ a 30;
   - un assert que falla: copiar el mensaje completo.

## 8. Qué queda listo para el informe
- **2.3:** la sección 2 de este plan.
- **2.7 Implementación:**
  - pipeline (cada etapa se corre una vez y deja archivos);
  - herramientas: Python, Gurobi (versión y licencia académica), HiGHS;
  - validaciones automáticas y tiempos;
  - **alcance:** instancia La Reina y por qué; red completa en la entrega final.
- **2.8 Resultados:**
  1. escalera E0 → E1 → E2-FIFO → E2 en La Reina, con el costo total siempre desglosado;
  2. de dónde viene la mejora (diagnóstico de la flota y reservas por tipo);
  3. ocupación en 24 h y energía por tarifa;
  4. sensibilidades ($h$, Δ);
  5. tiempos, y detallado vs agregado;
  6. limitaciones: un solo terminal; la Etapa 3 no ve los puestos; recarga completa; deadhead euclidiano; un día tipo.
- **3 / 4:**
  - escalar a los 4 terminales (red completa);
  - retroalimentar la capacidad a la Etapa 3;
  - carga parcial;
  - cargar en otro electroterminal;
  - reuso del patio en la Etapa 2.

## 9. Verificación de punta a punta
- E0 y E1 en La Reina = red completa filtrada (1.333 → 1.726 / 319 y 1.203 → 1.638 / 315).
- Etapa 3: cobertura exacta; todo tramo factible; flota = máximo de intervalos superpuestos.
- Etapa 4:
  - energía + déficit = consumida;
  - déficit = 0;
  - ocupación ≤ 100;
  - E2 ≤ E2-FIFO.
- Los KPIs usan las mismas definiciones en todos los escenarios.
- Toda cifra del informe sale de `resumen_para_analisis.md` o de un CSV producido por un script.

## 9b. Respuestas a las preguntas del prompt (para que la sesión no tenga que preguntar)

**KPIs.** Se usan los de la presentación, con definiciones que sirven igual para el caso base y para la propuesta, más
tres KPIs propios de la metodología. Si el informe cambia algún nombre, se arregla después en la revisión de
consistencia.

| # | KPI | Definición común a E0, E1, E2-FIFO y E2 |
|---|---|---|
| 1 | Costo total (USD/día) | Flota + reservas + km vacíos + espera + energía + eventos. Se reporta en dos versiones: original (como el caso base) y comparable (sin la espera nocturna en el patio) |
| 2 | N° de buses | Flota operativa + buses de reserva |
| 3 | % km de deadheading | km sin pasajeros / km totales |
| 4 | Costo medio de la energía | USD/kWh cargado (+ % de la energía cargada en valle) |
| 5 | N° de buses extra por batería insuficiente | N° de buses − buses del VSP del mismo escenario (ver nota) |

Nota sobre el KPI 5:
- En el caso base son las jornadas partidas + las reservas.
- En E2 son los buses de la Etapa 3 − los buses del VSP + las reservas.
- Puede salir negativo por el reuso del patio. Si pasa, se explica con el diagnóstico (ii)-(iv).

KPIs propios de la metodología:
- **6.** Buses de reserva separados en intermedias y nocturnas.
- **7.** Uso de los puestos: horas saturadas y uso máximo.
- **8.** Tiempo de cómputo y brecha de cada modelo.

**Nombres de los escenarios.** E1 se presenta como "**segundo caso base** (con interlining)". Los escenarios de
evaluación son E2-FIFO y E2.
