# Prompts para cerrar el Informe 2 (no commitear este archivo)

Orden de uso: el **A** va a la sesión de código, que ya existe. El **B** abre una sesión nueva de redacción. El **C** abre una sesión nueva de revisión final. Plan general: `docs/plan_redaccion_informe2.md`.

---

## Prompt A: sesión de código (nombres y figuras finales)

```
Siguiente tarea: preparar las salidas para el informe. El código de los modelos está cerrado y las corridas son
finales. Lee docs/plan_redaccion_informe2.md, secciones 0a, 1 y 4. No recalcules ningún modelo: esto es solo
presentación.

0. MODELO DE LA PROPUESTA COMPLETA. En la tabla de KPIs (sección 3 del resumen) y en las figuras principales, la
   columna de la Propuesta completa pasa a ser el modelo detallado con bloques de 15 min (corrida
   etapa4/h0_d15/detallado). Calcula para él TODOS los KPIs: costo total y desglose (incluido el costo con espera
   nocturna), buses, reservas diurnas y nocturnas, % km vacíos, costo medio de la energía y % en valle, uso máximo de
   los puestos, horas con todos los puestos ocupados, minutos sobre los puestos, utilización del bus, eventos y
   segundos de cómputo. El agregado se mantiene en la tabla de validación (detallado frente a agregado) y en las
   sensibilidades de holgura y largo del bloque, rotulado "(modelo agregado)". El detallado con 30 min no se reporta:
   quita o mueve a una carpeta "descartado" sus restos en etapa4/h0_d30/ (gurobi_detallado.log de la corrida
   anterior), para que nada lo lea.

1. NOMBRES. Aplica la tabla de nombres de la sección 1 del plan en todo lo que lee una persona: ejes, leyendas y
   títulos de los gráficos; encabezados y valores de los CSV de resultados; resumen_para_analisis.md; los reporte.md;
   y docs/context/01-03. Las siglas internas (E0, E1, E2-FIFO, E2, LB, C1b, h, Delta, LR) pueden quedar solo en las
   variables, las opciones de línea de comandos y los nombres de archivo. Agrega en docs/context/01_como_funciona.md
   una tabla de equivalencias entre sigla interna y nombre. Antes y después del cambio compara todas las cifras de
   resumen_para_analisis.md y de los CSV de kpis/: deben quedar idénticas. Muéstrame esa comprobación.

2. FIGURAS FINALES del informe en results/instancia_LR/informe/, en PDF (vectorial, para LaTeX) y PNG, cada una
   con su CSV.
   Estilo:
   - mismo color por escenario en todas;
   - textos en español con coma decimal y unidades en los ejes;
   - leyenda dentro de la figura;
   - sin título en la imagen, porque el título va en el caption de LaTeX;
   - pensadas para 0.8\textwidth con letra de al menos 9 pt.
   Figuras:
   - F0 (caso base en toda la red): buses de las jornadas sin batería, después de la carga reactiva y con reservas,
     para el Caso base y el Caso base con interlining. Sale de results/caso_base/ y results/etapa2_vsp/.
   - F1: diagrama de la metodología. Etapas 0 a 4 en secuencia, y el caso base aparte, no como etapa.
   - F2: un mismo grupo de viajes en el caso base (jornada partida, bus parado) frente a la Etapa 3 (tramo, recarga
     en el patio, otro tramo), tipo Gantt. Elige un ejemplo real y representativo de La Reina.
   - F3: escalera de buses (operativos + reservas diurnas + reservas nocturnas) para los cuatro escenarios.
   - F4: costo total apilado por componente para los cuatro escenarios, con el costo con espera nocturna marcado.
   - F5: buses cargando en 24 h para el Caso base con interlining, la Propuesta con carga por orden de llegada y la
     Propuesta completa, con la línea de los 100 puestos y los tramos de tarifa punta sombreados.
   - F6: un panel con las dos sensibilidades: holgura de recarga (buses y reservas) y largo del bloque (costo y
     segundos de cómputo).
   La Propuesta completa en F3, F4 y F5 es el modelo detallado con bloques de 15 min. F6 usa el modelo agregado y
   lo dice en la leyenda.

3. Regenera resumen_para_analisis.md con los nombres nuevos y con la Propuesta completa = detallado. Agrega:
   - una sección "Figuras del informe" con, para cada figura, el archivo, un caption propuesto que diga su mensaje
     y la cifra principal que respalda;
   - para el modelo detallado, el máximo de buses sobre los puestos en la ejecución minuto a minuto;
   - una sección "Herramientas y equipo" con las versiones de Python, Gurobi, scipy, pandas y numpy y el procesador
     (las del plan, sección 0a; verifícalas).

Pruébalo en chico si cambias código de figuras o de KPIs. Al final dame el comando para regenerar todo (sin correr
modelos) y cuánto tarda, y recuérdame hacer commit de scripts/ y results/. No hagas commits tú.
```

---

## Prompt B: sesión nueva de redacción (capítulos 2, 3 y 4)

```
Vamos a terminar parte del Informe 2 del Capstone ICS2122, Grupo 24 (planificación de buses eléctricos de RED,
Santiago). Es LaTeX, con un máximo de 30 páginas sin portada, índice, resumen, anexos ni bibliografía. El informe
está en docs/Informe 2/ (archivo principal Informe2.tex; capítulos en chapters/informe2/).

Lee primero:
- docs/plan_redaccion_informe2.md (plan, nombres y reglas: obligatorio);
- docs/Lineamientos Entrega 2 2026-2.md (pauta y puntajes) y docs/feedback_presentacion_2.txt (feedback del ayudante);
- docs/plan_etapas_3_4.md (la metodología de las Etapas 3 y 4);
- docs/context/01_como_funciona.md y 02_decisiones.md (todas las decisiones con su porqué);
- results/instancia_LR/resumen_para_analisis.md (todas las cifras de la instancia);
- los reportes del caso base en toda la red (results/caso_base/ y results/etapa2_vsp/reporte.md).
No leas CSV grandes ni código, salvo para resolver una duda puntual.

Tu alcance son solo estas partes, en este orden:
(1) capítulo 3, Discusión metodológica, completo;
(2) supuestos del capítulo 2;
(3) KPIs del capítulo 2;
(4) capítulo 4, Trabajo desarrollado y resultados, completo.
El resumen, la introducción, las conclusiones, los pasos futuros y la bibliografía los escribe el resto del equipo.
No los edites.

FASE A (empieza ya)
A1. Auditoría. Compara los capítulos 2, 3 y 4 actuales con la implementación y las decisiones. Entrégame una lista
    breve por sección de:
    - contradicciones;
    - cifras desactualizadas;
    - nombres antiguos de escenarios;
    - numeración escrita a mano;
    - lo que falta según la pauta;
    - violaciones de estilo.
    Incluye una estimación de páginas actual por capítulo. NO edites nada hasta que yo apruebe la lista.
A2. Capítulo 3.
    - Revisa la revisión bibliográfica y la sección de las Etapas 1 y 2. Corrige solo lo necesario.
    - Escribe la Etapa 3 (cortes por programación dinámica y reencadenamiento como flujo de costo mínimo) y la
      Etapa 4 (programación de la carga) con formulación completa: conjuntos, parámetros, variables, función
      objetivo y cada restricción con una frase sobre qué hace y por qué está. En la Etapa 4, el modelo detallado
      es la formulación y el agregado es su relajación con la capacidad en energía. Explica qué supone cada uno y
      para qué se usa cada uno.
    - Deja claro que el caso base NO es una etapa de la metodología.
    - Actualiza la sección Caso base con los nombres nuevos y el alcance (caso base en toda la red; comparación
      con la propuesta en La Reina).
A3. Supuestos. Revisa los que existen (corrige que el valor medido del factor de desvío es 1,35 y las escalas del
    texto) y pásalos a \subsection. Agrega los que faltan, cada uno con justificación, límite y sensibilidad
    realizada o planificada. Como mínimo:
    - recarga completa y lineal a 180 kW entre tramos;
    - la Etapa 3 no ve los puestos (la holgura de recarga lo compensa);
    - capacidad escrita en energía por bloque;
    - largo del bloque de 15 min;
    - bus de reserva a 250 USD;
    - la espera nocturna en el patio no se cobra en el costo total principal;
    - flujo de un día, no cíclico;
    - un terminal como instancia;
    - consumo constante;
    - un día tipo.
A4. KPIs. Propónme qué agregar a los 4 actuales, cada uno con su definición y la decisión que evalúa. Como base:
    - buses adicionales por batería;
    - buses de reserva (diurnas y nocturnas);
    - uso de los puestos de carga;
    - utilización del bus;
    - tiempo de cómputo y brecha (KPI metodológico).
    Ajusta la definición del costo total con su versión con espera nocturna. Escríbelos solo cuando apruebe.

FASE B (cuando te avise que las figuras finales y el resumen regenerado están listos en results/instancia_LR/;
las cifras ya son finales y están resumidas en la sección 0a del plan)
Decisiones fijas (plan, sección 4):
- en la tabla principal, la Propuesta completa es el modelo detallado con bloques de 15 min;
- el agregado aparece en la validación (mismas reservas y energía en 89 s frente a 1 h, candidato para la red
  completa, con su error de bordes) y en las sensibilidades, rotulado;
- el arranque del detallado se cuenta en una frase (primero con las reservas del agregado fijas, luego libre);
- herramientas: Python 3.11.9, Gurobi 13.0.2, scipy 1.15.3 (HiGHS), pandas 2.2.3, numpy 2.1.1, Intel i5-1035G4.
Capítulo 4 completo. Estructura sugerida (ajústala si el contenido lo pide):
- Implementación y herramientas: pipeline de scripts (cada etapa se corre una vez y deja archivos que lee la
  siguiente), lenguajes y solvers con versión, validaciones automáticas, tabla de tiempos, cómo reproducir y
  enlace al repositorio ([ENLACE]).
- Prueba de concepto: la instancia La Reina (por qué ese terminal, por qué un terminal completo y no una muestra,
  cómo se verificó que reproduce el caso base).
- Resultados del caso base en toda la red: actualiza el párrafo existente con los nombres nuevos, usa F0.
- Resultados de la propuesta en La Reina: tabla de KPIs de los cuatro escenarios; de dónde viene la mejora
  (diagnóstico de flota de la Etapa 3: cuánto es reuso del patio y cuánto es batería; reservas diurnas y nocturnas;
  ocupación de los puestos; energía por tarifa). Figuras F2 a F5.
- Validación del modelo de carga y tiempos: agregado frente a detallado, con brecha y segundos.
- Sensibilidad: holgura de recarga y largo del bloque (F6). Qué se concluye de cada una.
- Discusión: qué se aprendió, límites (con cifras, por ejemplo las reservas que ninguna programación puede evitar)
  y cómo orienta la entrega final.
Cada afirmación lleva su cifra. Compara siempre con el caso base y con lo esperado; si algo no salió como se
esperaba, explícalo.

FASE C
Escribe docs/notas_para_equipo.md (corto) con:
- el mensaje principal y las 5 cifras clave para el resumen y las conclusiones;
- los límites a declarar;
- los pasos futuros que se desprenden de los resultados;
- la lista de citas faltantes marcadas [CITA: tema].

REGLAS
- Nombres de escenarios y términos: los de la sección 1 del plan, sin siglas como E0, E1 o FIFO en el texto.
- Estilo: en mitad de un párrafo de texto libre no uses rayas ni guiones dobles ("—", "--") ni dos puntos.
  Frases directas y concisas. Coma decimal y punto de miles.
- Numeración solo con \section, \subsection, \label y \ref.
- Toda figura y tabla citada en el texto, con un caption que diga su mensaje.
- Cifras solo desde resumen_para_analisis.md y los reportes indicados. No inventes números.
- Citas solo de Thesis.bib; si falta una, márcala [CITA: tema].
- Páginas: no escribas de forma insuficiente las partes críticas (metodología, resultados y análisis, implementación,
  caso base, KPIs, supuestos) para ahorrar espacio. Escríbelas bien y concisas. Al final de cada fase dime cuántas
  páginas estimas por capítulo y qué partes menos importantes se podrían recortar.
- Cada decisión importante se justifica en pocas líneas (qué, por qué, alternativa, evidencia), usando
  docs/context/02_decisiones.md.
- Si compilas, usa pdflatex y bibtex desde docs/Informe 2/. No hagas commits.
```

---

## Prompt C: sesión nueva de revisión final (cuando todo esté escrito)

```
Revisa el Informe 2 completo en docs/Informe 2/ (LaTeX) antes de la entrega. Lee docs/plan_redaccion_informe2.md
(reglas y nombres), docs/Lineamientos Entrega 2 2026-2.md (pauta y descuentos), docs/feedback_presentacion_2.txt y
results/instancia_LR/resumen_para_analisis.md.

Entrégame, sin editar todavía:
1. Incoherencias entre capítulos: cifras, nombres de escenarios, supuestos, definiciones de KPIs, alcance (La Reina
   o toda la red), y afirmaciones de la introducción y las conclusiones que no estén respaldadas por los resultados.
2. Cifras del texto que no coincidan con el resumen de resultados o con los reportes del caso base. Verifica
   que la Propuesta completa de la tabla principal sea el modelo detallado con bloques de 15 min y que las
   sensibilidades digan que usan el modelo agregado.
3. Evaluación ítem por ítem con la pauta (135 puntos), con lo que falta en cada uno y si se responde el feedback del
   ayudante.
4. Páginas: compila y cuenta las páginas del cuerpo (máximo 30, sin portada, índice, resumen, anexos ni
   bibliografía). Si sobran, propone recortes empezando por las partes de menor puntaje, sin dejar insuficientes la
   metodología, los resultados, la implementación ni el caso base.
5. Formato: figuras legibles y citadas, captions con mensaje, tablas con unidades, índice, referencias y citas bien
   hechas, anexos solo complementarios.
6. Estilo: párrafos con rayas, guiones dobles ("—", "--") o dos puntos en mitad del texto libre; listas de cambios
   para corregirlos.
Después de que apruebe, aplica los cambios y vuelve a compilar.
```
