# Decisiones de la entrega 3

Continúa el registro de la entrega 2 (`docs/contexto_entregas_1_y_2/02_decisiones.md`). Ahí siguen valiendo las
decisiones A a F y G1 a G9. G10 a G12, sobre el modelo detallado, quedan reemplazadas por las de este archivo.
Cada decisión tiene qué se decidió, por qué y su evidencia (medida o razonada).

## J1. La Etapa 4 tiene que entregar un plan ejecutable

- **Qué:** la Propuesta completa es un plan de carga en el que cada bus carga en minutos enteros, en un puesto
  identificado, y en ningún minuto cargan más buses que puestos.
- **Por qué:** el modelo agregado y el detallado contaban la capacidad como energía por bloque de 15 min. En los
  bloques donde un bus llega o sale a mitad de bloque, la energía cabía pero los buses no. En la realidad un puesto
  atiende a un bus a la vez.
- **Evidencia (medido, La Reina, entrega 2):**
  - detallado: 32 min al día sobre 100 puestos, con un máximo de 115 buses;
  - agregado: 124 min, con un máximo de 125.

## J2. Cómo se obtiene: modelo relajado y luego MILP al minuto

- **Qué:**
  1. El modelo agregado de la entrega 2, que en todo lo que lee una persona se llama ahora **modelo relajado**, se
     resuelve primero. Sus reservas son el punto de partida y su resultado es la **cota inferior**.
  2. Un MILP con una variable por (ventana de carga, minuto) decide cuándo carga cada bus, contando buses por minuto.
     Las reservas son binarias solo en las ventanas candidatas: las que tienen reserva en el modelo relajado o en la
     carga por orden de llegada, y las que no tienen tiempo de cargar dentro de su ventana.
  3. Si con las reservas del relajado alguna ventana no cabe, pasa a reserva antes del MILP.
- **Por qué:**
  - Con las reservas fijas, el problema es de transporte (buses × minutos), así que el LP ya da una solución entera.
    No hacen falta binarias de enchufe, que eran las que hacían lento al detallado (1 h).
  - El relajado es una relajación del plan al minuto: todo plan al minuto es factible para él. Por eso su costo es
    una cota inferior válida y permite decir a cuánto del óptimo queda el plan.
- **Alternativas descartadas:**
  - detallado con bloques más finos: sigue superando los puestos;
  - contar buses enchufados el bloque entero: pierde 394 puesto-horas, medido en la entrega 2;
  - corregir el relajado con una heurística: sin garantía de calidad;
  - un modelo al minuto con binarias de enchufe: millones de binarias.
- **Evidencia (prueba mediana: 17 rutas de La Reina, 1.025 ventanas, 60 puestos, energía 84,5% de la capacidad):**
  - el plan queda a 2,0% de la cota inferior, y el MILP a 0,2% dentro de su propio modelo;
  - máximo 60 buses a la vez;
  - 163 reservas, contra 158 del relajado, que no es factible;
  - 4 min y 1,7 GB.
- **Evidencia (La Reina completa: 1.640 ventanas, 100 puestos):**
  - el plan queda a 2,05% de la cota inferior (102.674 contra 100.570 USD/día);
  - máximo 100 buses a la vez;
  - 225 reservas, contra 218 del relajado, que no es factible;
  - 208 s y 2,3 GB, con 563 binarias. El detallado tenía 160.720 binarias y llegó al límite de 1 h.
- **Dónde:** `scripts/13-etapa4_programacion_carga.py` (`--exacto`: `minutos_ventana`, `resolver_exacto`,
  `modo_exacto`), `parametros.TIEMPO_LIMITE_S["exacto"]` (1.800 s) y `parametros.GAP_EXACTO` (0,5%).

## J3. Misma regla de minutos que la carga por orden de llegada

- **Qué:**
  - la carga parte en el primer minuto entero después de llegar;
  - el bus ocupa el puesto minutos completos;
  - el último minuto carga solo lo que falta, y vale aunque cruce la hora de salida, si alcanza a terminar antes.
- **Por qué:** es la regla que ya usaban el caso base y la carga por orden de llegada (`buscar_slot` de 10-), así que
  las comparaciones son justas. La diferencia con un tiempo continuo es de menos de 1 minuto por carga, y siempre a
  favor de la seguridad.
- **Dónde:** `minutos_ventana` en 13-.

## J4. Etapa 3: el bus queda listo contando desde el minuto entero siguiente a su llegada

- **Qué:** `listo = ceil(llegada) + energía / potencia + holgura`, en vez de partir de la llegada exacta.
- **Por qué:** con la regla J3, una ventana diurna con menos de 1 minuto de holgura nunca alcanzaba a cargar a tiempo
  y necesitaba un bus de reserva (250 USD) por un redondeo.
- **Evidencia (medido, La Reina, entrega 2):** 30 ventanas diurnas tenían holgura entre 0,00 y 0,82 min, y eran
  exactamente las 30 reservas diurnas de la carga por orden de llegada (7.500 USD/día).
- **Costo:** cada tramo queda listo menos de 1 min más tarde, así que la flota puede subir unos pocos buses. Se mide
  al correr.
- **Dónde:** `datos_tramo` en 12-, con un assert que exige que toda ventana diurna alcance a cargar desde ese minuto.

## J5. Desempate: cargas continuas por orden de llegada

- **Qué:** entre los planes de igual costo, se elige el que da los minutos más tempranos al bus que llegó primero,
  con una prioridad estricta por orden de llegada.
- **Por qué:** sin desempate, el solver reparte la carga en trozos sueltos. Cada trozo es un evento de carga
  (5 USD) y un movimiento del bus. Con la prioridad, una carga empezada no la interrumpe un bus que llegó después.
- **Cómo:** se resuelve el LP con las reservas fijas, se queda en su cara óptima (mismo costo, se exige) y se
  minimiza el desempate.
- **Evidencia (prueba chica, 3 puestos):**
  - eventos de 92 a 66;
  - el desempate cuadrático que se probó primero empataba cuando dos buses llegaban casi juntos;
  - de los cortes que quedan, la mayoría los obligan las horas de salida, no el desempate;
  - en La Reina, 2.274 eventos contra unos 1.675 del detallado, que tenía los eventos en el objetivo pero superaba los
    puestos. Son unos 3.000 USD/día. Se acepta, porque meter los eventos en el objetivo exige binarias por bus y
    minuto, y eso es lo que hacía lento al detallado.
- **Dónde:** `resolver_exacto`, paso de pulido.

## J6. Asignación de puestos

- **Qué:** cada carga continua recibe el puesto libre de menor número, recorriendo el día desde el minuto con menos
  buses cargando.
- **Por qué:** es el algoritmo clásico de coloreo de intervalos. Usa a lo más el máximo de buses a la vez, que ya es
  ≤ puestos, así que siempre alcanza. Ningún bus cambia de puesto en medio de una carga, salvo que la carga cruce el
  minuto de corte.
- **Dónde:** `corridas_y_puestos` en 13-; salida `programa_puestos.csv` y gráfico `uso_de_cada_puesto.png`.

## J7. Validación independiente del plan

- **Qué:** `15-validar_plan_carga.py` lee solo los CSV y revisa 6 criterios:
  1. puestos por minuto y por puesto;
  2. minutos enteros y 180 kW;
  3. el bus está en el patio, y si termina después de su salida hay reserva;
  4. energía igual a la del tramo y batería útil;
  5. reservas suficientes al simular 7 días;
  6. costos recalculados.
- **Por qué:** muestra que el plan es aplicable sin confiar en el modelo que lo generó. En particular, comprueba por
  primera vez que las reservas funcionan como rotación: mientras un bus termina de cargar, el otro sale. Hasta ahora
  eso solo se argumentaba.
- **Evidencia:** en la prueba mediana, los 6 criterios dan OK. Sin las reservas, la simulación encuentra 489 salidas
  sin bus, así que el chequeo sí detecta un plan malo.

## J8. Lo que no se hace en esta entrega

- **Sensibilidad a la holgura y al largo del bloque:** no aportan a la pregunta principal. Las de la entrega 2 quedan
  en `results/instancia_LR/descartado/entrega2/`.
- **Separar los patios de Los Espinos y Santa Rosa en la Etapa 4:** comparten 270 puestos, como en la entrega 2. Se
  declara como supuesto (están a 1,1 km).
- **Flujo cíclico, otros tipos de día, sensibilidad del consumo:** quedan para el informe final, según el feedback de
  la presentación.

## J9. Robustez y cargas cortadas: se declaran y se espera el feedback

- **Qué:** no se corre la sensibilidad a la holgura con el plan exacto, ni un post-proceso para juntar los tramos cortos
  de carga. Las dos cosas se declaran como limitaciones, con sus números (`03_resultados_y_mensajes.md`, sección 4).
- **Por qué:**
  - el análisis crítico de los resultados concluyó que el enfoque sirve y que ninguna de las dos invalida los
    resultados;
  - agregarlas antes de la presentación suma casos que pueden confundir;
  - el feedback del profesor dirá cuál priorizar para el informe final.
- **Evidencia (medido, red completa):**
  - 2.248 de 10.304 ventanas cargan en dos o más tramos, y casi todas cambian de puesto;
  - 1.608 pausas son de 5 min o menos;
  - el costo de los eventos (5 USD cada uno) sí está en el modelo.
- **Si se retoma:**
  - holgura: `--holgura 15` en 12-, 13- y 15- para La Reina (~5 min);
  - tramos cortos: post-proceso que intercambia minutos entre buses dentro de un mismo período de tarifa y mantiene el
    puesto del bus, sin cambiar costos ni capacidad.
