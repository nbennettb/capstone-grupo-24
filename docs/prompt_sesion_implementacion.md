Trabajas en el repo del Capstone ICS2122, Grupo 24 (E-VSP de buses eléctricos de RED, Santiago). Tu tarea es rehacer
la implementación de las Etapas 3 y 4 y probarla, junto al caso base, en la instancia reducida del terminal La Reina,
según docs/plan_etapas_3_4.md (EL PLAN: síguelo; si ves un error, avísame antes de desviarte). La red completa NO se
corre en esta entrega.

Antes de nada lee: el plan, docs/feedback_presentacion_2.txt, docs/Lineamientos Entrega 2 2026-2.md (sección
Evaluación) y docs/Propuesta_metodologia_reunion.md §5. Para el código existente lee scripts/6-vsp_asignacion_buses.py,
scripts/10-carga_reactiva.py y scripts/common/. NO leas CSV grandes, imágenes ni el PDF de la Presentación 2, y no
busques versiones antiguas en git: lo anterior se descartó a propósito.

Reglas:
- El caso base (E0 + carga reactiva + reservas, ciclo al 100%) NO cambia. Solo se renombra y se le agrega --terminal.
  En La Reina debe reproducir exactamente las corridas existentes filtradas (plan §3).
- La Etapa 3 (cortes + re-encadenamiento) y la Etapa 4 (programación de la carga) son modelos NUESTROS, distintos del
  caso base. La lógica reactiva solo se reutiliza para la línea FIFO, importando sus funciones.
- Antes de escribir cada script, explícame en 5-10 líneas qué hará. Pruébalo SOLO en chico (2-3 rutas de La Reina),
  midiendo tiempo y memoria. Yo corro la instancia completa.
- Entregables: los scripts, docs/context/03_como_correr.md (guía: comandos en orden, tiempo y memoria estimados, qué
  debe imprimir cada uno, qué hacer si falla) y que el script de KPIs genere results/instancia_LR/resumen_para_analisis.md
  con todo lo del plan §7, que es lo que yo le pasaré a una IA para el análisis.
- Toda decisión queda en docs/context/02_decisiones.md (qué, por qué, alternativa, evidencia, dónde en el código),
  escrita para alguien ajeno al proyecto: concisa, sin fechas ni historia. Lo que se conversó con el profesor fueron
  ideas, no instrucciones; las decisiones son nuestras y se justifican con datos o razones.
- Si un resultado sale distinto a lo esperado, explícalo antes de seguir. Nunca ajustes el modelo para que calce.
- Convenciones: CSV con ';', matplotlib Agg, parámetros solo en scripts/common/parametros.py, asserts en español, CSV
  debajo de cada gráfico. Sin rastro de IA en el código. No hagas commits ni push.
- Termina P1 (plan §6) antes de tocar P2.

Los KPIs y los nombres de los escenarios ya están definidos en el plan, §9b: úsalos sin preguntar. Si el informe cambia
algún nombre, se ajusta después en una revisión de consistencia.
