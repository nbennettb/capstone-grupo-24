# Lo que sigue y prompt para la próxima sesión

## 1. Pasos

| # | Quién | Qué | Cuándo |
|---|---|---|---|
| 1 | Nicolás | Commit y push de lo actual: resultados de los cuatro terminales, red completa y docs | Ya |
| 2 | Compañero | Termina la Etapa 1 (clustering) en paralelo y la sube al repositorio | En curso |
| 3 | Nicolás | Abre una sesión nueva con el prompt de la sección 2, cuando el compañero avise | Al recibir la Etapa 1 |
| 4 | Claude | Revisa los cambios del compañero y arma `scripts/correr_todo.py`, que corre toda la cadena con un comando, con sus instrucciones y tiempos | Sesión nueva |
| 5 | Nicolás | Corre `correr_todo.py` (~1 h; Los Espinos + Santa Rosa usa 3,6 GB) y manda el log | Sesión nueva |
| 6 | Claude | Revisa los resultados, compara con la corrida actual y actualiza las cifras de `03_resultados_y_mensajes.md` | Sesión nueva |
| 7 | Claude | Gráficos para la presentación (sección 3) | Sesión nueva |
| 8 | Grupo | Elige los gráficos y arma la presentación | Después |

Si el compañero no cambia la asignación de rutas, igual se hace el paso 4: así queda un archivo que corre todo. El
paso 5 es opcional en ese caso, porque las cifras de hoy siguen valiendo.

## 2. Prompt para la sesión nueva

```
Contexto: capstone E-VSP, Grupo 24 (buses eléctricos de RED). Estamos preparando la presentación de la entrega 3.
La Etapa 4 ya está resuelta, corrida en los 4 electroterminales y validada. Lee primero, en este orden:
docs/contexto_entrega_3/00_LEEME.md, 03_resultados_y_mensajes.md, 01_como_correr.md, 02_decisiones.md y este archivo
(04_prompt_sesion_siguiente.md). plan_etapa4.md es la referencia técnica; léelo solo si lo necesitas.

Mi compañero terminó la Etapa 1 (clustering). Sus cambios están en: <COMPLETAR: archivos/commit/descripción>.

Tareas, en orden:
1. Revisa los cambios del compañero. Antes de tocar código, dime qué cambia aguas abajo: la asignación de rutas a
   terminales, los archivos de data-processed/ y qué scripts hay que volver a correr.
2. Crea scripts/correr_todo.py, en el estilo de scripts/correr_terminal.py:
   - corre la cadena completa: Etapa 1, Etapa 2 (E0 y E1), caso base de la red, los 4 terminales (reutilizando
     correr_terminal.py) y 17-red_completa.py;
   - log único, se detiene en el primer error y admite --desde para retomar;
   - actualiza 01_como_correr.md con el comando, los tiempos y la memoria.
   Pruébalo solo con casos chicos; la corrida completa la hago yo. Dame el comando y el tiempo estimado.
3. Cuando te mande el log: revisa todas las validaciones, compara las cifras con las de 03_resultados_y_mensajes.md
   (dime qué cambió y por qué) y actualiza ese archivo con las cifras nuevas.
4. Gráficos para la presentación, según la sección 3 de 04_prompt_sesion_siguiente.md: un script nuevo,
   scripts/18-graficos_presentacion.py, que escribe en results/presentacion/entrega3/. Prefiero que sobren gráficos y
   nosotros descartamos. Antes de escribir código de gráficos, carga el skill de visualización.

Reglas:
- Simple, sin sobre-complicar.
- Nada de siglas ni letras en lo que ve el público ("Propuesta completa", no "E2").
- Docs concisos, sin fechas.
- Yo corro lo pesado; tú pruebas solo con casos chicos.
- No hagas commit ni push.
- Español.
```

## 3. Gráficos para la presentación (para la tarea 4 del prompt)

**Requisitos para todos:**
- Pensados para proyectar: formato 16:9, letra grande y un mensaje por gráfico, dicho en el título.
- Mismos colores por escenario en todos (`scripts/common/graficos.py`).
- Números con formato chileno (12.502; 24,3%). Sin siglas.
- Cada gráfico en PNG (200 dpi) y PDF, con su CSV de datos al lado.
- Un catálogo `results/presentacion/entrega3/catalogo.md` con una línea por gráfico: qué muestra y qué mensaje apoya
  (sección 1 de `03_resultados_y_mensajes.md`).

**Candidatos** (el mensaje que apoya, entre paréntesis):

1. **Antes y después de la factibilidad (1):** buses cargando por minuto en La Reina, comparando el modelo relajado
   (llega a 124 con 100 puestos, `etapa4/h0_d15/tablas/ocupacion_minutos.csv`, columna `e2`) con el plan final (nunca
   más de 100, `exacto/ocupacion_minutos.csv`), con la línea de puestos.
2. **Cómo se resuelve la Etapa 4 (1, 2):** diagrama de pasos: modelo relajado → plan exacto al minuto → ordenar cargas →
   asignar puestos → validación independiente. Para cada paso, qué entra y qué sale. Es el pendiente 9.3 del plan.
3. **Cómo se valida (1):** los 6 criterios como lista de chequeo con OK por terminal.
4. **Distancia al óptimo (2):** por terminal y para la red, el costo del plan contra la cota inferior.
5. **Escalera de costos de la red (3):** costo diario por escenario (`red_completa/graficos/costo_diario_red.png`,
   mejorado).
6. **De dónde viene el ahorro (3):** cascada desde el caso base con interlining hasta la Propuesta completa, separando
   la Etapa 3 y la Etapa 4 por componente (flota, reservas, energía, eventos).
7. **Buses necesarios (3):** buses que operan y buses de reserva por escenario (`buses_red.png`, mejorado).
8. **Ahorro por terminal (3):** porcentaje de ahorro de cada terminal y de la red.
9. **Reservas inevitables y reservas por falta de puestos (4):** por terminal.
10. **Puestos llenos y tarifa (4):** buses cargando durante el día en un terminal congestionado (Los Espinos + Santa
    Rosa) y en uno holgado (Vespucio Norte), con las horas de tarifa cara sombreadas.
11. **Energía en horario valle según la carga del terminal (4):** carga del terminal contra el ahorro de energía y el %
    en valle de la Etapa 4.
12. **Plan de carga legible (1):** Gantt de unos 15 puestos durante unas 4 horas. El de 270 puestos no se lee.
13. **Un bus de reserva en acción (1):** línea de tiempo de una ventana con reserva: el bus llega, carga, la reserva
    sale en su lugar y el bus queda listo para la siguiente salida.
14. **Tiempo de cómputo (5):** entrega 2 (1 h sin terminar) contra ahora (minutos por terminal).
15. **Tabla resumen de KPIs de la red** como imagen limpia (sección 3 de `red_completa/resumen_para_analisis.md`).
