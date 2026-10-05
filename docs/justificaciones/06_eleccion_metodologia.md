# Justificación: por qué descomposición jerárquica, flujo exacto en el VSP y MILP solo en la carga

> Para pegar en el informe. Separa lo que dijo el profesor, lo medido y el razonamiento propio. La metodología completa está en
> `docs/context/01_metodologia.md`; el diagnóstico del enfoque anterior, en `docs/Propuesta_metodologia_reunion.md`.

## La decisión

El problema (planificar 64.502 viajes con buses eléctricos y decidir cuándo y dónde carga cada uno) se resuelve **por tipo de decisión**, en etapas: (1) agrupar rutas en
electroterminales, (2) asignar viajes a buses con un **flujo de costo mínimo exacto** (VSP), (3) insertar recargas con una política reactiva, (4) programar la carga con un **MILP** en instancias
pequeñas. Reemplaza la descomposición temporal por horizonte rodante del Informe 1.

## Qué dijo el profesor **[Profesor]**

La propuesta del Informe 1 resultó demasiado compleja. Debemos tener una metodología bien propuesta y justificada (qué se hace y por qué), probar el modelo de clusterización y probar el MILP en
instancias pequeñas, no el modelo completo. En la reunión del 28/09 la metodología jerárquica de 4 etapas se aprobó sin cambios.

## Qué medimos **[Medido]**

- **El VSP es exacto y rápido:** la matriz del flujo en red espacio-tiempo es totalmente unimodular, así que la relajación LP da solución entera: ~40 s sobre toda la red, y 5-55 s por escenario. No hace falta
  un MILP para decidir quién cubre qué viaje.
- **El clustering captura casi todo el beneficio del interlining:** E1 queda a +4,4% de buses sobre la cota inferior LB (7.366 vs 7.055); el interlining explica el 81% de lo que separa a E0 de LB.
- **La carga es donde hay una decisión que la política miope toma mal:** el MILP, en instancias reducidas, baja el costo de la carga al menos 10-24% frente al simulador reactivo (casi todo por menos reservas), y solo
  N = 10 se certifica al óptimo: la brecha crece con el tamaño (1,4-8,6%), lo que justifica no correrlo sobre los 4.622 buses de un terminal.
- **El precio de descomponer es grande en un punto:** el VSP ignora la batería, y de 7.366 buses del VSP se pasa a 12.502 en E1 con partición de jornadas y reservas (+70%), mientras que el efecto del retorno al
  electroterminal y del clustering es +4,4%.

## Cómo lo interpretamos **[Propio]**

1. **Descomposición jerárquica:** primero lo que define el costo dominante (la flota), después lo que define energía e infraestructura. Cada etapa es explicable, verificable por separado y tiene una cota (LB, cota LP, piso de reservas)
   que mide cuánto se pierde por descomponer. Es lo que responde "propuesta demasiado compleja": cada pieza es resoluble y se valida con su propia comprobación.
2. **Flujo exacto en el VSP, no heurística ni MILP genérico:** da el óptimo del subproblema en segundos; así cualquier pérdida de optimalidad viene de la descomposición, no de la resolución.
3. **MILP solo en la carga:** es el único lugar donde conviven tiempo (cuándo), tarifa (hora) y capacidad (puestos). Se prueba en instancias pequeñas, como pidió el profesor, y se compara contra la política
   reactiva sobre los mismos buses.
4. **Alternativa descartada:** el problema integrado (VSP + carga en un solo MILP) es la forma estándar de evitar el precio de la descomposición, pero es intratable a esta escala (64.502 viajes); se deja
   como referencia teórica.

## Fortalezas, debilidades y mejoras

- *Fortalezas:* cada etapa es exacta o tiene cota; resultados reproducibles; el caso base y el valor de cada decisión se miden por separado.
- *Debilidades:* el VSP ignora la batería (C9), la condición cíclica se cumple con reservas en lugar de resolverse en el modelo, la carga a escala completa solo se estima, y supuestos sin calibrar (layover, factor 1,3).
- *Mejoras para la entrega final:* un VSP que vea la batería (jornadas con pausas de carga de día), mejor manejo de la condición cíclica, calibrar layover, MILP de carga con descomposición por terminal
  o con estrategias para romper la simetría.

*Referencia a verificar antes de citarla: Kliewer, Mellouli y Suhl (2006), "A time-space network based exact optimization model for multi-depot bus scheduling", European Journal of Operational Research 175(3). No se afirma
nada de ella en este texto más allá del tipo de modelo.*
