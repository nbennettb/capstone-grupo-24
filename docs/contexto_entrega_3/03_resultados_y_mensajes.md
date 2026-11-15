# Resultados de la red y cómo presentarlos

Cifras de la corrida de la entrega 3: clustering de la entrega 2 y los cuatro terminales. Son las cifras de la
presentación. La fuente de todas es `results/red_completa/resumen_para_analisis.md`.

## 1. Los cinco mensajes de la presentación

1. **El plan de carga se puede aplicar tal cual.**
   - En ningún minuto hay más buses cargando que puestos, en los cuatro terminales.
   - Un validador independiente revisa 6 criterios y simula 7 días seguidos para comprobar que las reservas alcanzan.
   - Esto responde la crítica principal de la entrega 2: el plan anterior llegaba a 115 buses en 100 puestos.
2. **Es casi óptimo.** El plan queda a **1,5%** de una cota inferior válida.
   - Alcance, que siempre hay que decir: es la distancia al óptimo de la programación de carga, dados los buses de la
     Etapa 3, en energía + reservas.
3. **Ahorra 24,3% frente al caso base con interlining.**
   - Costo: 3,64 → 2,76 millones de USD/día.
   - Buses: 12.502 → 8.995 (3.507 menos).
4. **Hallazgo: el cuello de botella son los puestos de carga, no la tarifa.**
   - El 77% de las reservas (1.254 de 1.639) existe por falta de puestos. Las otras 385 son inevitables: el bus no
     alcanza a cargar ni con un puesto libre.
   - En tres terminales la energía del día ocupa 80–86% de la capacidad de 24 h, así que hay poco espacio para mover
     carga al horario valle.
   - Contraste: Vespucio Norte, con 35% de carga, lleva el valle de 64% a 85% y baja su energía 21%.
5. **Es reproducible.** Un comando por terminal, en minutos (antes, una hora sin terminar).

## 2. De dónde viene el ahorro (red completa, USD/día)

| Paso | Ahorro | Parte | Qué lo explica |
|---|---|---|---|
| Caso base con interlining → Propuesta con carga por orden de llegada | 556.705 | 63% | Etapa 3: cortes y re-encadenamiento (flota −734.750; reservas +188.000) |
| → Propuesta completa | 327.340 | 37% | Etapa 4: 1.320 reservas menos (−330.000) y energía −13.474; eventos +16.135 |
| **Total** | **884.045** | **100%** | **−24,3%** |

## 3. Cifras por terminal

| Terminal | Puestos | Energía / capacidad 24 h | Reservas | Reservas inevitables | Distancia a la cota | Ahorro vs interlining |
|---|---|---|---|---|---|---|
| Vespucio Norte | 150 | 34% | 29 | 29 | 0,0% | 20,8% |
| El Conquistador | 180 | 82% | 505 | 108 | 1,6% | 24,3% |
| Los Espinos + Santa Rosa | 270 | 85% | 880 | 194 | 1,4% | 24,8% |
| La Reina | 100 | 80% | 225 | 54 | 2,0% | 24,4% |
| **Red** | **700** | – | **1.639** | **385** | **1,5%** | **24,3%** |

## 4. Limitaciones que se declaran (no se corrigen antes de la presentación)

Se decidió esperar el feedback de la presentación antes de corregirlas (decisión J9).

- **Sin margen para atrasos:** holgura 0. El plan es determinista y está calzado al minuto.
- **Cargas cortadas:** el 22% de las ventanas (2.248 de 10.304) carga en dos o más tramos, y entre tramos el bus cambia
  de puesto.
  - Hay 1.608 pausas de 5 min o menos.
  - El costo de cada evento (5 USD) está en el modelo; la maniobra del bus no.
- **Descomposición:** la Etapa 3 arma las cadenas sin mirar los puestos y la Etapa 4 corrige con reservas. Un modelo
  integrado podría usar menos reservas; no se sabe cuántas.
- **Otros supuestos:**
  - Los Espinos y Santa Rosa comparten sus 270 puestos;
  - carga lineal a 180 kW;
  - un solo tipo de día (laboral).

## 5. Preguntas probables y respuesta

| Pregunta | Respuesta |
|---|---|
| ¿El plan es factible de verdad? | Sí. Lo revisa un validador que no usa el código del modelo, minuto a minuto, por puesto, por bus y simulando 7 días. Sin reservas, ese mismo validador encuentra 489 salidas sin bus, así que sí detecta un plan malo. |
| ¿1,5% del óptimo de qué? | De la programación de la carga dados los buses de la Etapa 3, en energía + reservas. Ningún plan de carga para esos buses puede costar más de 1,5% menos. |
| ¿Por qué la Etapa 4 ahorra poco en energía? | Porque los puestos están casi llenos todo el día. El ahorro de la Etapa 4 está en usar menos reservas. Donde sobran puestos (Vespucio Norte), la energía baja 21%. |
| ¿Por qué hay tantas reservas? | Tres de cada cuatro son por falta de puestos. Es una señal para la planificación de la infraestructura. |
| ¿Y si un bus se atrasa? | No está modelado (holgura 0). Es la primera extensión: dejar margen en la Etapa 3 y medir cuánto cuesta. |
| ¿Por qué hay buses que cargan en dos tramos? | Lo obligan las horas de salida con los puestos llenos. Cada tramo tiene su costo en el modelo. Reducir los cambios de puesto queda como mejora. |
