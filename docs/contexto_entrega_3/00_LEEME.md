# Entrega 3: Etapa 4 factible (léeme primero)

Esta carpeta explica qué cambió en la Etapa 4 para la entrega final, cómo correrla y cómo leer los resultados. Está
escrita para el grupo.

| Archivo | Para qué |
|---|---|
| `00_LEEME.md` | Qué se hizo y cómo explicarlo (este archivo) |
| `01_como_correr.md` | Comandos, tiempos, qué revisar y qué devolver |
| `02_decisiones.md` | Cada decisión nueva con su porqué, su evidencia y las alternativas descartadas |
| `03_resultados_y_mensajes.md` | Resultados de la red, mensajes para la presentación, limitaciones y preguntas probables |

## 1. El problema que había

En la entrega 2, la Etapa 4 decidía la carga en bloques de 15 minutos y contaba la capacidad como **energía por
bloque**. Así, dentro de un bloque podían "caber" más buses que puestos. Al revisar minuto a minuto, el plan llegaba
a tener **115 buses cargando a la vez con 100 puestos** (32 minutos al día sobre la capacidad). Eso no se puede hacer
en la realidad, y es lo que pidió corregir el profesor.

## 2. Qué se hizo, en palabras simples

La Etapa 4 ahora entrega un **plan de carga que se puede ejecutar tal cual**: para cada bus dice en qué puesto carga,
a qué hora empieza y a qué hora termina. Nunca hay más buses cargando que puestos.

Se obtiene en dos pasos:

1. **Modelo relajado** (el "agregado" de la entrega 2, rápido). Trabaja en bloques de 15 minutos sin mirar minuto a
   minuto. Sirve para dos cosas:
   - elegir qué buses probablemente necesitan un bus de reserva;
   - dar una **cota inferior**: ningún plan real puede costar menos que eso.
2. **Plan exacto al minuto** (MILP). Parte de la solución relajada y decide cuándo carga cada bus, minuto a minuto,
   contando buses y no energía. Después se asigna un puesto a cada carga.

Un script aparte (`15-`) **valida el plan** sin usar el código del modelo. Revisa que:
- en ningún minuto haya más buses que puestos;
- cada bus cargue solo mientras está en el patio;
- se reponga toda la energía;
- las reservas alcancen al simular 7 días seguidos.

**Para la presentación basta con esto:** "Se resolvió un MILP relajado para elegir las reservas y obtener una cota
inferior; sobre esa solución, un MILP al minuto programa cada carga sin superar los puestos; el plan se validó por
separado y queda a X% del óptimo (distancia a la cota)."

## 3. Otro cambio pequeño: la Etapa 3

La Etapa 3 calculaba la hora en que un bus "queda listo" como si empezara a cargar en el instante exacto de llegada,
por ejemplo a las 10:23,6. En la práctica, la carga parte en el siguiente minuto entero. Esto dejaba 30 ventanas de
carga con menos de 1 minuto de holgura que nunca alcanzaban, y eran **todas** las reservas diurnas de la carga por
orden de llegada. Ahora la Etapa 3 cuenta desde el minuto entero siguiente. Puede subir la flota en unos pocos buses,
y se mide al correr.

## 4. Qué no cambió

- Etapas 0, 1 y 2, y el caso base: igual que en la entrega 2. Todas las cifras de la entrega 3 usan el clustering de
  la entrega 2.
- La escalera de escenarios sigue igual: Caso base → Caso base con interlining → Propuesta con carga por orden de
  llegada → Propuesta completa.
- El "modelo detallado" de la entrega 2 ya no se usa. Tardaba 1 hora y tampoco respetaba los puestos minuto a minuto.

## 5. Qué hay en los resultados

Por cada electroterminal, en `results/instancia_<siglas>/`:
- **`resumen_para_analisis.md`**: todas las cifras. La sección 11 trae el resumen del plan de carga y su distancia al óptimo.
- `etapa4/h0_d15/exacto/`:
  - `buses_cargando_24h.png`: buses cargando durante el día frente a los puestos;
  - `uso_de_cada_puesto.png`: una fila por puesto y una barra por bus cargando;
  - `programa_puestos.csv`: el plan, una fila por carga (bus, puesto, hora de inicio y de fin, kWh);
  - `validacion.csv`: las 6 validaciones.
- `informe/`: las figuras F0-F5 actualizadas.

Para la red completa, en `results/red_completa/`:
- **`resumen_para_analisis.md`**: tabla de KPIs por escenario, costo por terminal y plan de carga por terminal;
- `graficos/`: costo diario de la red, buses necesarios y costo por terminal.

Siglas de las carpetas: `LR` La Reina, `VN` Vespucio Norte, `EC` El Conquistador, `LESR` Los Espinos + Santa Rosa.

## 6. Estado

| Qué | Estado |
|---|---|
| Código: cambio de la Etapa 3, plan exacto (`13- --exacto`), validador (`15-`), KPIs (`14-`) y `correr_terminal.py` | Listo y probado en pruebas chicas y medianas |
| Corrida de La Reina | Lista, todas las validaciones OK |
| Vespucio Norte y El Conquistador | Listas, todas las validaciones OK (brecha 0,0% y 1,6%) |
| Los Espinos + Santa Rosa | Lista, todas las validaciones OK (brecha 1,4%) |
| Tabla de la red completa (suma de los 4 terminales, `17-red_completa.py`) | Lista, en `results/red_completa/` |
| Análisis crítico de los resultados | Hecho: el enfoque sirve; se declaran limitaciones (`03_resultados_y_mensajes.md`) |
| Etapa 1 | Se mantiene la de la entrega 2 |
| Script que corre toda la cadena con un comando (`correr_todo.py`) | Pendiente |
| Gráficos de implementación y resultados para la presentación | Pendiente |

Red completa, contra el caso base con interlining:
- costo de 3,64 a **2,76 millones de USD/día (−24,3%)**;
- buses de 12.502 a **8.995**, de los cuales 1.639 son de reserva;
- plan de carga a **1,5%** de la cota inferior, sumando los cuatro terminales;
- los casos base sumados por terminal son iguales al de la red completa (comprobado por `17-`).

Resultado de La Reina (1.640 ventanas, 100 puestos):
- plan a 2,05% de la cota inferior: 102.674 USD/día en energía y reservas, contra una cota de 100.570;
- 100 buses como máximo a la vez, con 100 puestos;
- 225 reservas, contra 442 de la carga por orden de llegada;
- 2.274 eventos de carga (1,39 por ventana);
- las 6 validaciones OK;
- 4,5 min la corrida completa (3,5 min el plan exacto) y 2,3 GB de memoria.

## 7. Por qué ahora tarda minutos y antes una hora

El modelo detallado de la entrega 2 tenía 160.720 variables binarias, una por bus y bloque ("¿está enchufado en este
bloque?"). Gurobi tiene que probar combinaciones de las binarias, y a la hora se detuvo sin terminar. El plan exacto
tiene más variables (1,2 millones), pero solo 563 binarias: las de reserva de los buses candidatos. Cuando las reservas
están decididas, repartir los minutos de carga es un problema de transporte, y el LP lo resuelve directamente con
valores enteros, sin probar combinaciones.

El precio de esto es que los eventos de carga no están en el objetivo; se mantienen bajos con la prioridad por orden
de llegada. El detallado tenía unos 1.675 eventos y el plan exacto 2.274, unos 3.000 USD/día más. El detallado, en
cambio, superaba los puestos y no se podía aplicar.
