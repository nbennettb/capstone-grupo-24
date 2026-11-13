# Entrega 3: Etapa 4 factible (léeme primero)

Esta carpeta explica qué cambió en la Etapa 4 para la entrega final, cómo correrla y cómo leer los resultados. Está
escrita para el grupo. El detalle técnico y las alternativas que se descartaron están en `plan_etapa4.md`.

| Archivo | Para qué |
|---|---|
| `00_LEEME.md` | Qué se hizo y cómo explicarlo (este archivo) |
| `01_como_correr.md` | Comandos, tiempos, qué revisar y qué devolver |
| `02_decisiones.md` | Cada decisión nueva con su porqué y su evidencia |
| `plan_etapa4.md` | Plan técnico completo (alternativas analizadas y formulación) |

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

- Etapas 0, 1 y 2, y el caso base: igual que en la entrega 2. Si el compañero cambia el clustering (Etapa 1), se
  vuelve a correr todo con los mismos comandos (`01_como_correr.md`).
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

Siglas de las carpetas: `LR` La Reina, `VN` Vespucio Norte, `EC` El Conquistador, `LESR` Los Espinos + Santa Rosa.

## 6. Estado

| Qué | Estado |
|---|---|
| Código: cambio de la Etapa 3, plan exacto (`13- --exacto`), validador (`15-`), KPIs (`14-`) y `correr_terminal.py` | Listo y probado en pruebas chicas y medianas |
| Corrida de La Reina | Pendiente (Nicolás) |
| Corrida de los otros 3 electroterminales | Pendiente (en paralelo, ver `01_como_correr.md`) |
| Tabla de la red completa (suma de los 4 terminales) | Pendiente, después de las corridas |

Prueba mediana de referencia (17 rutas de La Reina, 1.025 ventanas, 60 puestos, más congestionada que La Reina):
- plan a 2,0% de la cota inferior;
- 60 buses como máximo a la vez, con 60 puestos;
- 1,5 eventos de carga por ventana;
- las 6 validaciones OK;
- 3 a 5 min de cómputo.
