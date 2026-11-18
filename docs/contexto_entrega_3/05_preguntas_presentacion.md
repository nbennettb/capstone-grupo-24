# Preguntas probables de la presentación y cómo responderlas

Respuestas cortas para lo que no alcanza a explicarse en la presentación. Las cifras son de la red completa, salvo que
se diga otra cosa. Fuente: `03_resultados_y_mensajes.md` y `02_decisiones.md`.

## 1. Calidad de la solución

**¿El 1,5% es la distancia a qué óptimo? ¿Cómo se calculó?**
- El modelo relajado es más flexible que la realidad, así que ningún plan de carga real puede costar menos que él. Su
  costo es una cota inferior: 690.325 USD/día en energía + reservas.
- Nuestro plan cuesta 700.656. Entonces cuesta a lo más (700.656 − 690.325) / 700.656 = 1,5% más que el mejor plan de
  carga posible.
- Por electroterminal: Vespucio Norte 0,0%, El Conquistador 1,6%, Los Espinos + Santa Rosa 1,4%, La Reina 2,0%.

**¿Es el óptimo del problema completo?**
- No. El 1,5% vale para la programación de la carga, dados los buses que deja la Etapa 3.
- Las etapas se resuelven por separado, así que no tenemos una cota del problema completo. Lo declaramos como limitación.

**¿Cómo saben que el plan se puede aplicar?**
- Un validador aparte lee solo el plan (bus, puesto, inicio y fin de cada carga), sin el código del modelo. Revisa:
  1. que nunca haya más buses cargando que puestos ni dos buses en un puesto;
  2. que las cargas sean de minutos enteros, a 180 kW como máximo;
  3. que el bus cargue solo mientras está en el patio;
  4. que se reponga la energía del tramo sin pasar la batería útil;
  5. que, simulando 7 días seguidos, ninguna salida quede sin bus cargado;
  6. que los costos recalculados coincidan.
- Todo da OK en los 4 electroterminales. Y sí detecta errores: sin reservas, encuentra 489 salidas sin bus.

## 2. La Etapa 4

**¿Cómo se hizo, en simple?**
1. Un modelo relajado, en bloques de 15 minutos, decide qué buses probablemente necesitan reserva y entrega la cota
   inferior.
2. Partiendo de esas reservas, un MILP minuto a minuto decide cuándo carga cada bus, contando buses y no energía.
3. A igual costo, carga primero el bus que llegó primero, para que las cargas sean continuas.
4. Cada carga recibe un puesto libre.
5. El validador revisa el plan.

En La Reina toma 4,5 minutos; en el electroterminal más grande, unos 27.

**¿Qué relaja exactamente el modelo relajado?**
- La capacidad se cuenta como energía por bloque de 15 minutos: lo cargado en un bloque no puede superar
  puestos × 180 kW × 15 min. No se cuentan buses minuto a minuto.
- Dentro de un bloque, la energía se reparte libremente entre buses. Dos buses que cargan medio bloque cada uno "caben"
  en un puesto, aunque en la realidad se topen. Por eso el relajado llega a 124 buses cargando con 100 puestos.
- Todo plan real cumple sus restricciones, así que su costo es una cota inferior válida.

**¿Por qué bloques de 15 minutos en el relajado?**
- Las tarifas cambian en horas exactas, así que el bloque debe dividir la hora.
- Un bloque son 45 kWh, así que una carga completa ocupa unos 7 bloques.
- El modelo es 15 veces más chico que al minuto, y solo se usa para elegir reservas y obtener la cota.
- En la entrega 2 se probaron bloques de 5, 15 y 30 minutos: el costo cambió menos de 0,2%.

**¿Por qué al minuto en el plan final?**
- Es la única forma de garantizar que en ningún minuto haya más buses que puestos.
- Es la misma regla de minutos enteros que usan el caso base y la carga por orden de llegada, así que la comparación es
  justa.

**¿Por qué ahora tarda minutos y antes una hora?**
- El modelo de la entrega 2 tenía una decisión de sí o no por bus y bloque: 160.720 en La Reina. No terminó en 1 hora.
- Ahora solo las reservas son de sí o no: 563 en La Reina. Con las reservas fijas, repartir los minutos de carga es un
  problema de transporte, y la relajación lineal ya da una solución entera.

**¿Qué es la carga por orden de llegada?**
- Cada bus carga apenas llega, en el primer puesto libre, como en la operación simple.
- Es el escenario intermedio: tiene la Etapa 3, pero no la Etapa 4. Sirve para separar cuánto ahorra cada etapa.

## 3. Resultados

**¿Contra qué se compara el 24,3%?**
- Contra el caso base: la misma red, el mismo día y los mismos costos, con una operación simple. Cada bus hace su jornada
  y carga cuando ya no le alcanza la batería; si no alcanza a cargar antes de su próxima salida, se agrega un bus.

**¿De dónde sale el ahorro?**
- Dos tercios vienen de la Etapa 3: cortar las jornadas y re-encadenar los tramos baja los buses que operan de 10.295 a
  7.356.
- Un tercio viene de la Etapa 4: con el plan de carga se usan 1.320 buses de reserva menos.

**¿Qué es un bus de reserva y por qué hay tantos (1.639)?**
- Es un bus extra, ya cargado, que sale en lugar de uno que no alcanzó a terminar de cargar. Al día siguiente rotan.
- El 77% (1.254) existe porque los puestos están ocupados: el bus alcanzaría a cargar con un puesto libre. Los otros 385
  no alcanzan ni con un puesto libre.

**¿Por qué la Etapa 4 casi no ahorra en energía?**
- En tres electroterminales los puestos están llenos casi toda la noche, así que no hay espacio para mover carga al
  horario barato.
- Donde sobran puestos sí se ahorra: Vespucio Norte sube su carga en horario barato de 64% a 85% y baja su costo de
  energía 21%.

**¿Por qué cuatro electroterminales y no cinco?**
- Los Espinos y Santa Rosa están a 1,1 km y se modelan como uno solo, de 270 puestos. Por separado, Los Espinos no
  alcanza a reponer su energía.

## 4. Limitaciones

**¿Qué es una carga interrumpida (22%)?**
- El bus no carga de corrido: carga un rato, cede el puesto a otro bus que debe salir antes y vuelve a cargar más tarde,
  a veces en otro puesto.
- Pasa en 2.248 de 10.304 cargas. La mitad de las pausas dura 5 minutos o menos.
- Cada reanudación paga 5 USD de evento de carga en el modelo, pero la maniobra de mover el bus no está modelada.
- Mejora posible: un ajuste posterior que intercambie minutos entre buses de una misma tarifa para que cada uno cargue
  de corrido, sin cambiar el costo ni la capacidad.

**¿Qué pasa si un bus se atrasa?**
- No está modelado: el plan está calzado al minuto, sin holgura. Es la primera extensión: dejar un margen en la Etapa 3
  y medir cuánto cuesta.

**¿Por qué no un solo modelo que integre las Etapas 3 y 4?**
- Sería mucho más grande. Ya el modelo de carga al minuto con todas las decisiones de sí o no no terminaba en una hora.
- La descomposición tiene un costo: la Etapa 3 no mira los puestos y la Etapa 4 compensa con reservas. Un modelo
  integrado podría usar menos reservas, y no sabemos cuántas.

## 5. Supuestos

**¿Por qué los traslados como línea recta × 1,3?**
- No hay distancias por calle para todos los pares. El factor se calibró con recorridos reales (1,04 a 1,38).
- Con factores entre 1,2 y 1,5, la flota cambia apenas ±1%.

**¿Por qué cargar hasta 100%?**
- En el caso base se probaron topes de 100% a 50%. Cargar hasta 100% es lo más barato: con topes menores se parten más
  jornadas y suben los buses.

**¿Por qué la flota no tiene límite?**
- El número de buses es lo que el modelo decide. Además, con los 1.200 buses del archivo de parámetros ni siquiera se
  cubre el peak de 6.539 buses circulando a la vez.
