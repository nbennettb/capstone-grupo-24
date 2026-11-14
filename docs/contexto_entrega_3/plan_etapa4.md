# Plan: Etapa 4 factible y reproducible en toda la red (Entrega 3)

> **Estado:** implementado en versión simplificada. Para el grupo, leer primero `00_LEEME.md`, `01_como_correr.md`
> y `02_decisiones.md`. Diferencias con este plan:
> - el "agregado" se presenta como "modelo relajado";
> - la sensibilidad de holgura se descartó;
> - Los Espinos + Santa Rosa no separa patios;
> - la tabla de la red completa (`17-red_completa.py`) está hecha y los cuatro terminales están corridos y validados;
> - las sesiones 3 y 4 de la sección 7 están cerradas, salvo la figura de la metodología (9.3), que pasa a la sesión de
>   gráficos. El estado vigente está en `00_LEEME.md` y lo que sigue en `04_prompt_sesion_siguiente.md`;
> - el script por terminal es `scripts/correr_terminal.py`.

Alcance de este plan: la parte asignada a Nicolás. La Etapa 4 tiene que entregar un plan de carga que se pueda ejecutar
tal cual, verificado, y la cadena Etapa 3 → Etapa 4 tiene que correr en los cuatro electroterminales con el mismo código.
Se trabaja sobre las Etapas 1 y 2 actuales. Si el clustering cambia, se vuelve a correr todo con los mismos comandos
(sección 8).

Fuera de alcance: flujo cíclico, sensibilidades nuevas (consumo, velocidad, radio), otros tipos de día, redacción del
informe y comentarios del ayudante. El caso base no cambia de código (ver 1.4).

---

## 1. Diagnóstico: qué de la Etapa 4 actual no se puede aplicar en la realidad

Todas las cifras son de La Reina, holgura 0, salvo que se diga otra cosa. Se midieron sobre los CSV de `results/instancia_LR/`.

### 1.1 Lo que es imposible y se corrige

| Problema | Evidencia | Por qué es imposible |
|---|---|---|
| Capacidad escrita en energía por bloque | Detallado: 32 min sobre 100 puestos, máximo 115 buses. Agregado: 124 min, máximo 125 | En ningún instante pueden cargar más buses que puestos. El bloque cuenta energía y no buses, así que en los bloques de borde (un bus llega o sale a mitad de bloque) la energía cabe pero los buses no |
| Buses fraccionarios | La "ejecución minuto a minuto" es un LP que reparte fracciones de bus por minuto | Un bus está enchufado o no lo está |
| Etapa 3 en tiempo continuo y carga en minutos enteros | 30 ventanas diurnas tienen holgura menor que 1 min (0,00 a 0,82 min). Son exactamente las 30 reservas diurnas de la carga por orden de llegada | El bus llega a las 10:23,6 y "queda listo" a una hora calculada como si cargara desde 10:23,6. La carga real parte en un minuto entero, así que nunca alcanza. El agregado y el detallado lo esconden porque cargan desde la fracción de minuto |

### 1.2 Lo que parece raro pero sí es aplicable (se verifica, no se cambia)

- **Reservas.** Una reserva no es un bus que aparece de la nada. Es una rotación: si el bus A no termina de cargar
  antes de su salida, el bus R (cargado) toma la cadena ese día y A termina de cargar. Al día siguiente A toma la
  cadena y R carga. La carga de la ventana se repite igual cada día y cabe en las 24 h desde la llegada, que es lo
  que exige el modelo. Hasta ahora esto se argumentaba y nunca se comprobó. El validador nuevo (paso E) lo
  comprueba simulando varios días seguidos.
- **54 ventanas nocturnas sin tiempo para cargar** (38 son cadenas de más de 24 h). Necesitan reserva con cualquier
  programa de carga. Son aplicables como rotación y se informan como inevitables.
- **Eventos de carga.** El agregado reparte cada bloque entre muchos buses (3,6 eventos por ventana). Es un costo
  (5 USD por evento) y no una infactibilidad, pero un plan con tantos enchufes no es creíble. El diseño nuevo lo
  reduce con un desempate (paso C).

### 1.3 Supuestos que se mantienen y se declaran

- Estacionar no ocupa un puesto y el patio no tiene límite de estacionamiento (no hay datos).
- Carga lineal a 180 kW.
- Los Espinos y Santa Rosa comparten sus 270 puestos. En la red completa se mide cuántas cargas quedan en el
  otro patio y su traslado de 1,1 km (sección 6.3).

### 1.4 Caso base

El comentario del profesor ("el caso base debiera tener interlining, si no la comparación capaz que sea muy injusta")
ya está cubierto por la escalera, que tiene los dos casos base. No hay cambio de código. Lo que cambia es cómo se
presenta: la comparación justa de la propuesta es contra el **Caso base con interlining**. Esto lo resuelve el grupo en
la presentación. Desde esta parte solo se corre el caso base terminal por terminal para la tabla de la red (Paso 6).

---

## 2. Qué significa "factible": lo que el validador exige

Un plan de carga es factible si cumple todo esto, comprobado por un script que solo lee los CSV de salida:

- **F1. Puestos:** en cada minuto del día hay a lo más κ buses cargando, y cada puesto tiene a lo más un bus a la vez.
- **F2. Enchufe entero:** cada carga es un intervalo de minutos enteros en un puesto identificado, con un bus identificado.
- **F3. El bus está en el patio:** toda carga ocurre entre la llegada del bus y su salida. Si sigue cargando después de
  su salida, esa salida la cubre una reserva.
- **F4. Energía:** cada ventana recibe exactamente la energía de su tramo, a lo más 180 kW, y se recalcula desde
  `tramos.csv` y no desde la tabla de ventanas.
- **F5. Batería:** en toda la cadena de cada bus, la batería queda entre 10% y 100%, y termina el día como lo empezó.
- **F6. Reservas aplicables:** al simular 7 días seguidos del plan periódico, cada salida tiene un bus cargado
  disponible usando solo los buses de la cadena más sus reservas.
- **F7. Costos:** el costo informado se recalcula desde el plan y coincide.

---

## 3. Alternativas analizadas

La pregunta era si la Etapa 4 se relaja, si no se relaja, o si se relaja y después se corrige.

| # | Alternativa | ¿Factible al minuto? | ¿Exacta? | Tamaño y tiempo en La Reina | Decisión |
|---|---|---|---|---|---|
| 1 | Seguir con el agregado o el detallado, capacidad en energía por bloque | No (32 a 146 min sobre los puestos) | Es una relajación | 90 s / 1 h | Descartada. Es lo que el profesor objetó |
| 2 | Detallado con bloques más finos (5 min) o más tiempo | No. El error de borde baja, pero no desaparece | Es una relajación | ~480 mil binarias, más de 1 h | Descartada |
| 3 | Capacidad como buses enchufados el bloque entero (Σ y ≤ puestos) | Sí | No. Es conservadora | Como el detallado | Descartada. Pierde 394 puesto-horas con bloques de 15 (medido, G10). La energía casi no cabe |
| 4 | Agregado y después una reparación heurística (correr cargas que sobran) | Sí, si la reparación converge | No. No hay garantía de calidad | Rápida | Descartada como método principal. Una heurística que mueve cargas a mano es justo lo "relajado y corregido" que no se puede defender |
| 5 | Modelo exacto en tiempo continuo con intervalos elementales (Horn, 1974; McNaughton, 1959) | Sí | Sí | 3.066 cortes de tiempo distintos, ~5 millones de variables, y además un paso para ubicar trozos de menos de un minuto | Descartada por tamaño. Es la misma idea que la 7, pero sin redondear al minuto |
| 6 | Modelo al minuto con binarias de enchufe y de inicio de evento (detallado al minuto) | Sí | Sí, incluidos los eventos | 2 a 5 millones de binarias | Descartada. No se puede resolver |
| **7** | **Dos niveles: el agregado decide qué ventanas pueden llevar reserva y da la cota inferior. Un modelo exacto al minuto, que es un problema de transporte, programa cada carga. Después se asignan los puestos y se valida** | **Sí, por construcción y verificado** | **Sí, al minuto entero** (el error es menor que 1 min y siempre va a favor de la seguridad) | ~0,9 millones de variables continuas y ~300 binarias | **Elegida** |
| 8 | Heurística integrada de las Etapas 3 y 4 (ALNS, Wen et al. 2016) | Depende | No | Rehacer las etapas | Fuera de alcance, queda como extensión |

**Respuesta a la pregunta:** la relajación se usa solo para decidir qué ventanas pueden llevar reserva y para tener
una cota inferior. La solución que se reporta sale de un modelo exacto, no de una corrección heurística, y además se
verifica con un script independiente. Así no queda nada que sea imposible de aplicar, y la distancia al óptimo se mide
contra una cota válida.

Por qué la 7 y no las otras:
- Al contar la capacidad en **buses por minuto** y no en energía por bloque, el error de borde desaparece.
- Con las reservas fijas, el problema es de transporte (ventanas × minutos del reloj, matriz totalmente unimodular).
  El LP entrega directamente una solución entera, así que no hacen falta binarias de enchufe, que eran las que hacían
  lento al detallado.
- Las únicas binarias son las reservas, y solo en las ventanas candidatas.
- La asignación de puestos es un coloreo de intervalos, que se resuelve exacto con un algoritmo goloso.
- Escala a los terminales grandes (sección 6).

---

## 4. Diseño elegido

```
Etapa 3 (listo en minuto entero) ─> ventanas (a_w, d_w, E_w)
   │
   A. Agregado Δ=15 (sin cambios, ~90 s) ─> reservas candidatas + cota inferior LB
   │
   B. Modelo exacto al minuto (transporte + reservas binarias en candidatas)
   │     B1 reparación: reservas del agregado fijas; las ventanas que quedan con déficit pasan a reserva
   │     B2 MILP: reservas libres en las candidatas, partiendo de B1
   │
   C. Pulido: reservas fijas, cara óptima del LP, desempate por orden de llegada ─> 0/1 por (ventana, minuto)
   │
   D. Corridas de minutos ─> puesto de cada carga (coloreo de intervalos) ─> programa_puestos.csv
   │
   E. Validador independiente (F1 a F7, simulación de 7 días) ─> OK / FALLA
```

### 4.0 Convención de minutos enteros y cambio en la Etapa 3

- **Convención:** un bus ocupa un puesto en minutos enteros. Empieza a cargar en el primer minuto entero después de
  llegar, ⌈a⌉. Necesita n_w = ⌈E_w / q⌉ minutos, con q = 180/60 = 3 kWh por minuto, y el último minuto puede ser
  parcial. Es exactamente la regla que ya usan la carga reactiva del caso base y la carga por orden de llegada
  (`buscar_slot`, `correr_fifo`).
- **Cambio en `12-`:** `listo_min = ceil(a) + 60·E/P + h`, en vez de `a + 60·E/P + h`. Es una línea en `datos_tramo`.
  Se agrega un assert: toda ventana diurna tiene al menos el tiempo de carga desde ⌈a⌉.
- **Efecto esperado:** desaparecen las 30 reservas diurnas artificiales de la carga por orden de llegada (7.500 USD/día).
  La flota de la Etapa 3 puede subir unos pocos buses, porque cada tramo queda listo menos de 1 min más tarde. Se mide.
- **Alternativa medida:** dejar la Etapa 3 como está. Esas 30 ventanas pasarían a necesitar reserva también en la
  Etapa 4 exacta (30 × 250 = 7.500 USD/día) por un artefacto de redondeo. Se descarta.
- Las salidas de la Etapa 3 agregan `patio_salida` y `patio_llegada` de cada tramo (para Los Espinos + Santa Rosa, 6.3).

### 4.1 Paso A: agregado (código actual, sin cambios)

- Se corre igual que ahora: `13- --delta 15`.
- Sirve para dos cosas:
  - **Cota inferior LB:** su LP es una relajación del problema real. Todo plan al minuto se convierte en una solución
    factible del agregado, porque la energía por bloque es a lo más P·Δ·κ y la de cada ventana es a lo más P × su
    tiempo disponible en el bloque.
  - **Candidatas a reserva:** C = {r = 1 en el MILP} ∪ {r > 0 en el LP} ∪ {ventanas sin tiempo dentro (|D_w| < n_w)}.
- El agregado ya no es el resultado que se reporta.

### 4.2 Paso B: modelo exacto al minuto

Datos por ventana w: llegada a_w, hora límite d_w y energía E_w.
- n_w = ⌈E_w / q⌉ minutos de puesto.
- resto ρ_w = E_w − (n_w − 1)·q, que es la energía del último minuto.
- t(m) = m mod 1440 es el minuto del reloj.

Minutos posibles de cada ventana (desenrollados, como en `construir_segmentos`):
- **dentro, D_w:** los m enteros con ⌈a_w⌉ ≤ m ≤ ⌊d_w⌋ − 1. Además el minuto ⌊d_w⌋, si ρ_w ≤ q·(d_w − ⌊d_w⌋), es decir,
  si el resto alcanza a cargarse antes de salir. Es la misma regla de la carga por orden de llegada, así que esa carga
  es una solución factible del modelo.
- **extensión, X_w** (solo si w ∈ C): los m con máx D_w < m ≤ ⌊a_w + 1440⌋ − 1.

D_w ∪ X_w cubre menos de 1440 minutos, así que cada minuto del reloj aparece a lo más una vez por ventana.

Variables:
- x_wm ∈ [0, 1]: el bus de w ocupa un puesto en el minuto m.
- r_w ∈ {0, 1}: reserva, solo para w ∈ C. Fuera de C vale 0 y no hay variables de extensión.
- δ_w ≥ 0: minutos de déficit (penalizados con 10.000 USD/kWh × q).

```
min  Σ_wm p_t(m)·q·x_wm  +  250·Σ_w r_w  +  10.000·q·Σ_w δ_w
s.a. Σ_{m ∈ D_w ∪ X_w} x_wm + δ_w = n_w          ∀ w            (toda la energía del tramo se repone)
     Σ_{m ∈ X_w} x_wm ≤ n_w·r_w                  ∀ w ∈ C        (cargar después de la salida exige reserva)
     Σ_{(w,m): t(m) = t} x_wm ≤ κ                ∀ t = 0..1439  (buses cargando por minuto ≤ puestos)
```

Es el mismo agregado, pero con un minuto de bloque y la capacidad contada en buses. El costo del último minuto se
corrige después de resolver (carga ρ_w y no q). El error del objetivo es de menos de 0,66 USD por ventana, y el costo
que se informa es el exacto.

- **B1, reparación:**
  - se fijan las reservas del agregado más las de las ventanas sin tiempo, y se resuelve el LP;
  - si alguna ventana queda con δ > 0, pasa a reserva y se vuelve a resolver;
  - se esperan 0 a 3 vueltas;
  - el resultado es una solución factible, que es la cota superior UB0.
- **B2, MILP:**
  - reservas binarias en C, partiendo de B1;
  - brecha 0,5% y límite `TIEMPO_LIMITE_S["exacto"]` (propuesta: 1.800 s);
  - devuelve UB ≤ UB0;
  - si se acaba el tiempo, se informa la brecha. B1 ya es factible, así que nunca queda sin solución.

### 4.3 Paso C: pulido en la cara óptima

Con las reservas de B2 fijas:
1. Se resuelve el LP por simplex.
2. Se queda en su cara óptima: se fijan las variables con costo reducido distinto de 0 y se dejan como igualdad las
   filas de capacidad con dual positivo.
3. Se minimiza un segundo objetivo de desempate, Σ (m − ⌈a_w⌉)²·x_wm.

Qué se gana:
- **No cambia el costo:** se queda en la cara óptima.
- **Solución entera:** una cara de un poliedro entero es entera. Se exige con un assert.
- **Cargas continuas:** a igual costo, el bus que llegó antes toma los minutos más tempranos. Por intercambio, el costo
  de dos ventanas que se cambian minutos m1 < m2 varía en 2(m2 − m1)(a1 − a2). Así, una carga ya empezada no la
  interrumpe un bus que llegó después, como en la carga por orden de llegada, que hace un evento por ventana.
- **Corrige el defecto del desempate actual:** el desempate lineal de hoy (10⁻⁶ × bloques desde la llegada) es
  constante entre ventanas en un problema de transporte, y por eso no evitaba la fragmentación.

Los eventos se cuentan después: cada evento es una corrida de minutos consecutivos. Si quedan muchos más que uno por
ventana, se agrega una consolidación por tramo tarifario, que no cambia el costo (ver 4.7).

### 4.4 Paso D: puestos y plan operable

- Cada corrida de minutos de una ventana es un intervalo.
- Se ordenan por inicio y se asigna el puesto libre de menor número con un heap.
- En un grafo de intervalos, este algoritmo goloso usa exactamente la máxima superposición, que es ≤ κ por la
  restricción de capacidad. Ningún bus cambia de puesto en medio de una carga.
- Salida `programa_puestos.csv`: ventana, bus, cadena, puesto, patio, inicio, fin, kWh, tramo tarifario, reserva.
- Figura nueva: carta Gantt de los puestos, con una fila por puesto en 24 h. Es la evidencia visual de factibilidad
  para la presentación.

### 4.5 Paso E: validador independiente (`15-validar_plan_carga.py`)

- Lee solo `tramos.csv`, `cadenas.csv`, `ventanas.csv` y `programa_puestos.csv`, y comprueba F1 a F7.
- Para F6, simula 7 días por cadena. Los buses de la cadena son 1 + sus reservas. Cada salida la toma un bus que está
  en el patio con la carga terminada según el plan. Si en algún momento no hay ninguno, informa FALLA con la cadena y
  la hora.
- Imprime una línea `[OK]` o `[FALLA]` por criterio y escribe `validacion.csv`.
- `14-` lo vuelve a leer.

### 4.6 Cotas y qué tan cerca del óptimo

- LB = cota LP del agregado (Paso A). Es válida para el problema al minuto (4.1).
- Con eventos, LB_total = LB + 5 × ventanas (`brechas.mejor_brecha`, G12).
- Brecha reportada = (UB − LB) / UB. Además, la brecha de Gurobi de B2 dentro del modelo con candidatas.
- Referencias de La Reina con las ventanas actuales:
  - LB = 100.129 USD (energía + reservas);
  - agregado: 100.905;
  - detallado: 100.666.
  - Una brecha de 1% o menos sería un resultado sólido.

Para el comentario 2 del profesor, sobre qué tan cerca del óptimo está cada etapa:

| Etapa | Método | Distancia al óptimo de la etapa |
|---|---|---|
| 2 | Flujo de costo mínimo (LP con solución entera) | 0 (exacto) |
| 3 | Programación dinámica por jornada + flujo de costo mínimo | 0 (exacto dado el corte) |
| 4 | Agregado (relajación) + transporte al minuto (exacto) | Brecha medida contra LB |
| Global | Descomposición secuencial | No se garantiza. Se declara |

### 4.7 Riesgos y plan B

| Riesgo | Señal | Plan B |
|---|---|---|
| B2 lento en terminales grandes | No baja la brecha en el límite | Se informa B1 (ya factible) con su brecha contra LB |
| B1 necesita muchas reservas nuevas | Más de ~10 reservas sobre el agregado | Indica que la relajación del agregado era optimista. B2 lo corrige. Se informa como hallazgo |
| El pulido no queda entero | Falla el assert | Se resuelve con `Method=1` (simplex dual) sin barrera, o con un flujo de costo mínimo en networkx/OR-Tools sobre la cara óptima |
| Muchos eventos (> 1,3 por ventana) | Se mide en D | Consolidación por tramo tarifario: los minutos de cada bus dentro de un tramo se reordenan con regla de llegada sin cambiar los totales por minuto. No cambia el costo |
| Memoria en Los Espinos + Santa Rosa (~2,5 millones de variables) | Más de ~6 GB | Correrlo en un computador de 16 GB. Si no alcanza, agrupar minutos con el mismo conjunto de ventanas disponibles (exacto, ~25% menos variables) |

---

## 5. Implementación: archivos

Todo en `scripts/`. `docs/codigos_entrega/` se actualiza después, para el informe final.

| Archivo | Cambio |
|---|---|
| `scripts/12-etapa3_cortes_reencadenamiento.py` | `listo_min` desde ⌈a⌉. Columnas `patio_salida` y `patio_llegada` en `tramos.csv`. Assert de tiempo de carga en las diurnas |
| `scripts/common/parametros.py` | `TIEMPO_LIMITE_S["exacto"]`, `GAP_EXACTO` y `MINUTO_ENTERO = True`, documentados |
| `scripts/13-etapa4_programacion_carga.py` | Modo `--exacto` (como `--detallado`: lee el agregado de la misma carpeta, escribe en `h<h>_d<Δ>/exacto/`). Funciones nuevas: `minutos_ventana`, `candidatas`, `resolver_exacto` (B1 y B2), `pulir_cara_optima` (C), `corridas_y_puestos` (D), `modo_exacto`. Salidas: `programa_puestos.csv`, `programa_E2_exacto.csv`, `ocupacion_minutos.csv` (entera), `modelo.csv` (A, B1, B2 y C), `resumen.csv`, Gantt de puestos, log de Gurobi y `reporte.md`. Se lleva la carga por orden de llegada a la grilla de minutos y se exige que sea factible (asegura Propuesta completa ≤ carga por orden de llegada) |
| `scripts/15-validar_plan_carga.py` (nuevo) | Paso E |
| `scripts/14-kpis_instancia.py` | La Propuesta completa pasa a ser el modelo exacto. El agregado aparece como cota. El detallado deja la tabla principal. Validaciones nuevas (F1 a F7 desde `validacion.csv`). Leyendas y captions con el nombre del terminal, no "La Reina" fijo. Figura F7 (Gantt de puestos) |
| `scripts/17-red_completa.py` (nuevo) | Junta los cuatro `instancia_<siglas>/` y arma la tabla de la red: caso base, caso base con interlining, carga por orden de llegada y Propuesta completa, por terminal y en total. Además figuras de la red |
| `scripts/correr_terminal.py` (nuevo) | Corre toda la cadena de un terminal: 10- E0 y E1, 12- h0, 13- agregado, 13- exacto, 15- y 14-. Se detiene en el primer error y escribe un log |
| `docs/contexto_entrega_3/01_como_funciona.md`, `02_decisiones.md`, `03_como_correr.md` | Versiones nuevas: decisiones G13 y siguientes (convención de minutos, modelo exacto, pulido, puestos, validador, cota); G10 a G12 quedan como descartadas, con su razón |

El código del detallado se mantiene, pero no se corre. Sus resultados viejos dejan de ser comparables cuando cambie la
Etapa 3, y se mueven a `results/instancia_LR/descartado/` (lo hace el usuario).

---

## 6. Red completa

### 6.1 Terminales

| `--terminal` | Electroterminal | Puestos | Jornadas con interlining | Carpeta |
|---|---|---|---|---|
| 1 | Vespucio Norte | 150 | 793 | `results/instancia_VN/` |
| 2 | El Conquistador | 180 | 2.166 | `results/instancia_EC/` |
| 3 (o 5) | Los Espinos + Santa Rosa | 270 | 3.204 | `results/instancia_LESR/` |
| 4 | La Reina | 100 | 1.203 | `results/instancia_LR/` |

### 6.2 Tiempos estimados por terminal

Son estimaciones a partir de La Reina, escaladas por tamaño. Se recalibran después de la primera corrida real (Paso 4).

| Terminal | 10- (E0 + E1) | 12- | 13- agregado | 13- exacto | 15- + 14- | Total | RAM |
|---|---|---|---|---|---|---|---|
| Vespucio Norte | < 1 min | < 1 min | 1 a 3 min | 5 a 15 min | < 1 min | ~15 min | ~2 GB |
| La Reina | < 1 min | < 1 min | ~2 min | 10 a 40 min | < 1 min | ~45 min | ~2 a 3 GB |
| El Conquistador | < 1 min | < 1 min | 5 a 10 min | 20 a 60 min | < 1 min | ~1 h | ~3 a 4 GB |
| Los Espinos + Santa Rosa | ~1 min | ~1 min | ~10 min (límite) | 30 a 90 min | ~1 min | ~1,5 h | ~4 a 6 GB |

El computador de Nicolás tiene 7,7 GB. Los Espinos + Santa Rosa conviene correrlo en un computador de 16 GB.

### 6.3 Los Espinos + Santa Rosa

Comparten 270 puestos, pero son dos patios a 1,1 km. Con las columnas nuevas de patio se mide:
1. cuántas cargas quedan en un puesto del otro patio. En el paso D se asigna primero el patio propio (120 puestos en
   Los Espinos y 150 en Santa Rosa) y después el otro;
2. cuántos encadenamientos de la Etapa 3 llegan a un patio y salen del otro.

Si los traslados (1,44 km y ~4 min cada uno) caben en la holgura de la ventana, se suman como km vacíos y se informan.
Si hay muchos que no caben, se decide con esos datos si separar los patios en la Etapa 4.

---

## 7. Pasos

Leyenda: **[C]** lo hace Claude (código y pruebas chicas), **[N]** lo corre Nicolás, **[G]** lo puede correr cualquier
compañero.

### Sesión 2: implementación del núcleo

| Paso | Quién | Qué | Tiempo |
|---|---|---|---|
| 1.1 | C | Cambio en `12-` (4.0) y parámetros | - |
| 1.2 | C | Modo `--exacto` en `13-` (pasos B, C y D) | - |
| 1.3 | C | `15-validar_plan_carga.py` (paso E) | - |
| 1.4 | C | Pruebas chicas: `12- --terminal 4 --rutas C09 C10`, `13- --prueba --puestos-prueba 3` (agregado y luego exacto), `15- --prueba`. Se fuerza congestión para que haya reservas, déficit en B1 y fragmentación | segundos |
| 1.5 | C | Medir tiempo y memoria de la prueba, y extrapolar a La Reina | - |

**Paso 2 [N]. Antes de correr, guardar el estado actual:**
```
git add results/instancia_LR
git commit -m "Resultados La Reina de la entrega 2"
```

**Paso 3 [N]. La Reina completa con el código nuevo** (~30 a 45 min, ver 6.2). Comandos:
```
python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --escenario E1 --holgura 0
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 15
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 15 --exacto
python scripts/15-validar_plan_carga.py --terminal 4 --holgura 0 --delta 15
```

Qué revisar:
- en 12-, la flota (antes 1.166) y que las reservas diurnas de la carga por orden de llegada queden en ~0;
- en 13- `--exacto`, `minutos sobre los puestos: 0` y `máximo 100`;
- reservas y brecha contra LB;
- eventos por ventana;
- en 15-, todo `[OK]`.

Mandar a Claude la salida de consola completa de los cuatro comandos.

### Sesión 3: revisión y red completa

| Paso | Quién | Qué | Tiempo |
|---|---|---|---|
| 4.1 | C | Revisar la corrida de La Reina, ajustar (plan B de 4.7 si hace falta) y recalibrar los tiempos de 6.2 | - |
| 4.2 | C | Cambios en `14-` (Propuesta completa = exacto, figuras por terminal y F7) | - |
| 4.3 | C | `17-red_completa.py` y `correr_terminal.py`, probados con `--prueba` | - |
| 4.4 | C | Instrucciones para los compañeros (6.2 y sección 8) | - |

**Paso 5 [N]. Cerrar La Reina:** `python scripts/14-kpis_instancia.py --terminal 4` (~30 s). Revisar que diga
`TODAS LAS VALIDACIONES OK`.

**Paso 6 [N/G]. Los otros tres terminales, en paralelo, uno por persona:**
```
python scripts/correr_terminal.py --terminal 1      # Vespucio Norte, ~15 min
python scripts/correr_terminal.py --terminal 2      # El Conquistador, ~1 h
python scripts/correr_terminal.py --terminal 3      # Los Espinos + Santa Rosa, ~1,5 h, idealmente con 16 GB de RAM
```
Cada persona devuelve su carpeta `results/instancia_<siglas>/` comprimida y el log `correr_terminal_<siglas>.log`.

**Paso 7 [N]. Consolidado de la red:** `python scripts/17-red_completa.py` (~1 min) → `results/red_completa/`.

**Paso 8 [G, opcional]. Sensibilidad de la holgura con el modelo exacto, en La Reina** (~45 min cada una). Solo si
la presentación la necesita con el modelo final; si no, se mantiene la del agregado rotulada.
```
python scripts/correr_terminal.py --terminal 4 --holgura 30
python scripts/correr_terminal.py --terminal 4 --holgura 60
```

### Sesión 4: cierre

| Paso | Quién | Qué |
|---|---|---|
| 9.1 | C | Resumen para el análisis de la red (`results/red_completa/resumen_para_analisis.md`) y de La Reina |
| 9.2 | C | `docs/contexto_entrega_3/01_como_funciona.md`, `02_decisiones.md` y `03_como_correr.md` |
| 9.3 | C | Figura de la metodología de la Etapa 4 (entradas, salidas y tipo de método de cada paso, comentario 2 del profesor), si el grupo la quiere para la presentación |
| 9.4 | N | Commit de código y resultados, y envío al grupo (sección 8) |

---

## 8. Qué recibe el grupo y cómo volver a correr

**Entregable:**
- `results/red_completa/` (tabla y figuras de la red);
- `results/instancia_<siglas>/` de cada terminal (KPIs, Gantt de puestos y validación);
- los dos `resumen_para_analisis.md`;
- `docs/contexto_entrega_3/03_como_correr.md`.

**Requisitos para correr:**
- Python 3.11 con `pandas numpy scipy matplotlib tabulate gurobipy psutil`.
- Licencia académica de Gurobi personal (`grbgetkey`, desde la red UC o la VPN). La licencia gratuita de pip no
  sirve, porque se limita a 2.000 variables.
- Comprobarla con `python -c "import gurobipy; gurobipy.Model()"`.
- Todo se corre desde la raíz del repositorio.

**Si cambia el clustering (Etapa 1):**
1. `4-clustering_c1.py` (o el script que deje el compañero);
2. `6-vsp_asignacion_buses.py` para E0 y E1;
3. `10-caso_base_carga_reactiva.py` en la red completa (para la comparación de igualdad);
4. Paso 6 con los cuatro terminales;
5. Paso 7.

Los comandos exactos de 1 a 3 quedan en `03_como_correr.md` cuando se sepa qué cambia el compañero.

---

## 9. Prompt para la sesión 2

```
Contexto: Capstone E-VSP (Grupo 24). Lee primero docs/contexto_entrega_3/plan_etapa4.md completo; es el plan
aprobado y manda sobre cualquier documento anterior. Luego lee scripts/13-etapa4_programacion_carga.py,
scripts/12-etapa3_cortes_reencadenamiento.py (datos_tramo), scripts/common/parametros.py, scripts/common/brechas.py
y docs/contexto_entregas_1_y_2/02_decisiones.md (secciones F y G).

Tarea: implementar la Sesión 2 del plan (pasos 1.1 a 1.5): el cambio de la Etapa 3 (sección 4.0), el modo --exacto de
13- (secciones 4.2 a 4.4) y scripts/15-validar_plan_carga.py (sección 4.5), con las salidas y nombres de la sección 5.
Reglas: tú solo corres pruebas chicas (--prueba, --rutas C09 C10, --puestos-prueba 3); las corridas del terminal
completo las corro yo. Antes de correr algo explica qué hace. Mantén el estilo del código existente (CSV con ';',
asserts en español que dicen qué falló, nombres de common/nombres.py en todo lo que lee una persona, sin rastro de IA
en el código). No hagas commit ni push. Al terminar dame: (1) qué cambiaste y por qué, en pocas líneas;
(2) resultados de las pruebas chicas (reservas, brecha, eventos por ventana, minutos sobre los puestos, tiempos y
memoria); (3) los comandos del Paso 3 del plan con su tiempo estimado recalibrado y qué debe imprimir cada uno.
```
