# Plan para cerrar el Informe 2: secciones a cargo de Nicolás

Los prompts para las sesiones de IA están en `docs/prompts_redaccion_informe2.md`. No commitear ese archivo.

## 0a. Código cerrado: resultados finales de la instancia La Reina

Fuente: `results/instancia_LR/resumen_para_analisis.md`. Todas las validaciones dan OK.

| | Caso base | Caso base con interlining | Propuesta con carga por orden de llegada | Propuesta completa (modelo detallado, Δ = 15) |
|---|---|---|---|---|
| Costo total (USD/día) | 594.602 | 567.807 | 488.464 | 424.300 |
| N° de buses (operativos + reservas) | 2.045 | 1.953 | 1.638 | 1.383 |
| Reservas | 319 | 315 | 472 | 217 |

**Modelo detallado (Δ = 15)**, comparado con el agregado:

| | Detallado | Agregado |
|---|---|---|
| Reservas | 217 | 218 |
| Eventos | 1.675 | 5.866 |
| Costo de carga | 109.041 USD | 130.235 USD con sus eventos |
| Minutos sobre los puestos (al minuto) | 32 | 124 |
| Tiempo | 1 h, arranque en dos fases | 89 s |
| Brecha | 0,66% | 0,32% |

**Sensibilidades** (modelo agregado):
- Holgura 0 / 30 / 60 min: costo total 445.495 / 448.862 / 452.702.
- Largo del bloque 5 / 15 / 30 min: objetivo 101.148 / 100.905 / 100.681, en 94 / 89 / 13 s.

**Herramientas:** Python 3.11.9, Gurobi 13.0.2 (gurobipy), scipy 1.15.3 (HiGHS), pandas 2.2.3 y numpy 2.1.1. Equipo con Intel i5-1035G4 (4 núcleos, 8 hilos).

## 0. Estado del informe (revisado en `docs/Informe 2/`)

| Capítulo (numeración actual) | Archivo | Estado | Responsable |
|---|---|---|---|
| 1 Introducción | `introduccion.tex` | Escrita | Compañeros |
| 2 Problema, datos y modelo: descripción, datos, análisis de datos, **supuestos**, **KPIs** | `problema_modelo.tex` | Descripción y datos escritos. Supuestos incompletos: 3 de unos 10, numerados a mano ("2.4.1.", que ya no calza con la numeración). KPIs: 4 en la tabla | **Esta sesión: supuestos y KPIs** |
| 3 Discusión metodológica: revisión bibliográfica, **metodología**, **caso base** | `metodologia.tex` | Revisión escrita, al día con la nueva metodología. Metodología con las Etapas 1 y 2 nada más (**faltan las Etapas 3 y 4**). Caso base escrito con E0/E1, "red completa" e "instancias reducidas" | **Esta sesión: completo** |
| 4 Trabajo y resultados: **implementación**, **prueba de concepto**, **resultados**, **discusión** | `trabajo_resultados.tex` | Plantilla, más un párrafo de resultados del caso base en la red completa | **Esta sesión: completo** |
| 5 Conclusiones | `conclusiones.tex` | Plantilla | Compañeros |
| 6 Pasos futuros | `pasos_futuros.tex` | Plan parcial con supuestos antiguos (ventanas reactivas, instancias de Los Espinos y Santa Rosa) | Compañeros, con las notas de esta sesión |
| Resumen y bibliografía | `resumen.tex`, `Thesis.bib` | Plantilla. Bibliografía con 7 entradas | Compañeros |

Problemas detectados que la redacción debe corregir:
- **Numeración escrita a mano.** Hay que usar `\subsection` y `\ref`, nunca números escritos.
- **Supuesto del factor de desvío** (`problema_modelo.tex`, 2.4.1):
  - dice "valor medido (1,3)", pero el valor medido es 1,35;
  - las escalas del texto ([1-3] y [3-5] km) no calzan con las de la tabla (1-3 y 5-15 km).
- **Nombres antiguos de escenarios:** E0, E1 y "red completa vs instancias reducidas" aparecen en el capítulo 2, en el caso base y en el capítulo 4.
- **Revisión bibliográfica desactualizada.** Dice que el modelo detallado "no alcanza a resolverse en un tiempo razonable", y hoy llega a una brecha de 0,66% en 1 h.
- **Estilo:** varios párrafos usan dos puntos en mitad del texto.

## 1. Nombres de los escenarios y términos (se aplican en el código, las figuras, las tablas y el informe)

| Antes | Nombre en el informe y en las figuras | Etiqueta corta (gráficos) | Qué es |
|---|---|---|---|
| E0 | **Caso base** | Caso base | VSP por línea + carga reactiva |
| E1 | **Caso base con interlining** | Caso base + interlining | Extensión del caso base que aísla el efecto del interlining |
| E2-FIFO | **Propuesta con carga por orden de llegada** | Propuesta, carga por llegada | Etapa 3 + carga en orden de llegada. Aísla el aporte de la Etapa 3 |
| E2 | **Propuesta completa** | Propuesta completa | Etapa 3 + Etapa 4. Si hace falta, se indica el modelo: (modelo agregado) o (modelo detallado) |
| LB | Cota inferior de flota | Cota inferior | VSP sin retorno al terminal. No es operacional |
| E0_sep, E1_sep | … con terminales separados | — | Evidencia para unir Los Espinos y Santa Rosa |
| C1 / C1b, C2 | Asignación por cercanía; asignación con capacidad | — | Etapa 1 |
| VSP (en etiquetas) | Jornadas sin batería (Etapa 2) | Sin batería | Salida de la Etapa 2 |
| FIFO | orden de llegada | por llegada | — |
| reservas intermedias / nocturnas | **reservas diurnas / reservas nocturnas** | — | Ventana entre tramos / ventana nocturna |
| h | holgura de recarga (min) | — | Parámetro de la Etapa 3 |
| Δ | largo del bloque (min) | — | Parámetro de la Etapa 4 |
| P1…P6 | tramo horario con sus horas, por ejemplo "00-08 h" | — | Tarifa |
| Costo total comparable / original | **Costo total** / **costo total con espera nocturna** | — | El primero es la métrica principal |
| LR | La Reina | — | — |

Las siglas internas solo pueden quedar en el código y en los nombres de archivo. Todo lo que lee una persona usa los nombres de la tabla: ejes, leyendas, encabezados de tablas, resúmenes y texto del informe.

## 2. Pasos en orden

**Paso 0. Corridas de la Etapa 4. HECHO.** Las cifras de la sección 0a son finales. No se recalcula ningún modelo.

**Paso 0b. Commit de respaldo (ahora, antes de tocar nada más).** Sacar del repo los prompts, que no se entregan:
```
git rm --cached docs/prompt_sesion_implementacion.md
echo "docs/prompt*.md" >> .gitignore
git add .gitignore scripts results docs/context docs/plan_redaccion_informe2.md "docs/Informe 2"
git commit -m "Resultados finales instancia La Reina (detallado en dos fases)"
```

**Paso 1. Sesión de código (la misma de la implementación): solo presentación, sin recalcular.** Prompt A.
- **1a.** Cambiar los nombres en todas las salidas y comprobar que las cifras quedan idénticas.
- **1b.** La Propuesta completa de la tabla de KPIs y de las figuras principales pasa a ser el modelo detallado. Hay que calcular todos sus KPIs. Las sensibilidades quedan con el agregado.
- **1c.** Generar las figuras finales del informe (F0-F6) en PDF y PNG, más un índice con el mensaje de cada una.
- **1d.** Regenerar `resumen_para_analisis.md` y hacer commit.

**Paso 2. Sesión nueva de redacción.** Prompt B. Puede empezar en paralelo con el Paso 1.
- **Fase A (ya, sin esperar las figuras finales):**
  1. Auditoría de coherencia de los capítulos 2 a 4. **Espera la aprobación de Nicolás antes de escribir.**
  2. Capítulo 3 completo:
     - revisar lo existente;
     - escribir las Etapas 3 y 4 formalmente;
     - actualizar el caso base.
  3. Supuestos: revisar y agregar los que faltan.
  4. Proponer KPIs adicionales. **Espera aprobación antes de escribirlos.**
- **Fase B (cuando el Paso 1 esté listo):** el capítulo 4 completo:
  - implementación y herramientas;
  - prueba de concepto en La Reina;
  - resultados del caso base;
  - resultados de la propuesta;
  - validación y tiempos;
  - sensibilidad;
  - discusión.
- **Fase C:** `docs/notas_para_equipo.md`, con los mensajes y cifras clave para resumen, conclusiones y pasos futuros, y las citas faltantes. Así el resto del informe queda coherente con lo escrito.

**Paso 3. Revisión final** (sesión nueva, cuando todo esté escrito). Prompt C.
- Coherencia entre capítulos, cifras contra el resumen y nombres.
- Cumplimiento de la pauta ítem por ítem, páginas (≤ 30) y estilo.
- Propone recortes **en las partes menos importantes primero**.

**Paso 4. Cierre.** Compilar, revisar el PDF a mano, hacer commit y push (sin los archivos de prompts) y poner el enlace al repositorio en el informe.

## 3. Reglas de redacción (van en los prompts B y C)

- **Prioridad.** Las partes críticas no se escriben de forma insuficiente por las páginas. Primero se escriben bien y concisas, y después se recorta lo menos importante. Las partes críticas son:
  - metodología y su formalización (20 puntos);
  - resultados y análisis (20);
  - implementación (10);
  - caso base (10);
  - KPIs (10);
  - supuestos (5).
- **Estilo.**
  - En mitad de un párrafo de texto libre **no se usan rayas ni guiones dobles ("—", "--") ni dos puntos**.
  - Frases directas. Coma decimal y punto de miles (64.502).
  - Toda figura y tabla se cita en el texto y tiene un caption que dice el mensaje.
- **Numeración.** Siempre `\section`, `\subsection`, `\label` y `\ref`. Nunca números escritos a mano.
- **Cifras.** Todas salen de `results/instancia_LR/resumen_para_analisis.md`. Las del caso base en toda la red salen de sus reportes en `results/caso_base/` y de `results/etapa2_vsp/`.
- **Citas.** Solo las de `Thesis.bib`. Si falta una, se marca `[CITA: tema]` para que el equipo la agregue.
- **Justificación.** Cada decisión importante dice qué se decidió, por qué, la alternativa y la evidencia, en pocas líneas. La fuente es `docs/context/02_decisiones.md`.
- **Alcance explícito.**
  - La metodología se probó en el terminal La Reina completo: subproblema independiente, sin escalar puestos, y el terminal congestionado más chico.
  - El caso base se corrió en toda la red.
  - La red completa con la metodología queda para la entrega final.

## 4. Decisiones tomadas

1. **La Propuesta completa de la tabla principal y de las figuras principales es el modelo detallado con Δ = 15.**
   - Es la formulación que se presenta en el capítulo 3.
   - Sus eventos de carga son realistas.
   - Casi no supera los puestos: 32 minutos al día, contra 124 del agregado y su pico de 125 buses a las 7:00.
   - Su brecha es de 0,66%.
2. **El modelo agregado aparece en dos lugares:**
   - en la validación, donde logra las mismas reservas y la misma energía en 89 s en vez de 1 h, y por eso es el candidato para la red completa (con su error de bordes declarado);
   - en las sensibilidades de holgura y largo del bloque, donde todas las variantes se comparan con el mismo modelo, y así se rotula.
3. **El modelo detallado con Δ = 30 no se reporta,** porque no se corrió con el código final.
4. **El arranque en dos fases del detallado se cuenta en una sola frase en Implementación:** se resuelve primero con las reservas del agregado fijas y luego se libera. La historia de las corridas queda solo en `docs/context/02_decisiones.md`.
5. **Herramientas y equipo:** los de la sección 0a.
