# Justificación: la unidad de agrupamiento es la ruta (y las tres estrategias C1a, C1b, C2)

> Para pegar en el informe. Separa lo que dijo el profesor, lo medido y el razonamiento propio. Datos: `results/etapa0_preprocesamiento/`
> y `results/etapa1_clustering/` (scripts `3-`, `4-`, `5-`, `8-`).

## La decisión

Se agrupan **rutas** (no expediciones sueltas) en electroterminales: cada ruta tiene un electroterminal base, y desde él salen y vuelven sus
buses. La asignación de la entrega es **C1** (internamente `c1b`): el electroterminal más cercano a los paraderos terminales reales de
la ruta, ponderados por uso. **C1a** (centroide) es un control y **C2** (MILP con capacidad de carga) es la propuesta formulada y validada.

## Qué dijo el profesor **[Profesor]**

En el Informe 1 pidió "revisar en profundidad estrategias para clusterizar". Pidió además una metodología bien propuesta, incluido el modelo de clusterización, y probar
el caso base una vez clusterizado para saber qué tan buena es la clusterización. Si un análisis sirvió para decidir la metodología, hay que contarlo.

## Qué medimos **[Medido]**

- **Las rutas cierran su ida y vuelta:** el 94,7% de las 300 rutas con ambos sentidos termina la ida a menos de 500 m de donde empieza la vuelta (mediana 85 m).
  Asignar expediciones sueltas rompería ese encadenamiento natural.
- **El criterio de distancia importa poco:** C1a (centroide) y C1b (paraderos reales) difieren en 41 de 417 rutas (10%), pero el costo aproximado de pullout/pullin mejora solo
  0,7% (83.843 → 83.271 USD/día).
- **La capacidad sí importa, pero no donde se pensaba:** con la carga real (incluye salir y volver al electroterminal), C1b deja a Los Espinos al 101,6% de su capacidad de 24 h; C2 mueve
  5 de 417 rutas para respetarla (97,6%) y cuesta casi nada (83.271 → 83.276 USD/día). Ver `08_carga_real_en_clustering.md`.
- **Efecto sobre la flota:** C2 cambia el VSP en 0 buses (E1) y +2 (sin unir), así que el VSP no ve la capacidad. Ver `05_unir_terminales.md`.

## Cómo lo interpretamos **[Propio]**

1. Agrupar rutas convierte un problema de 5 depósitos en 5 problemas de un depósito, y es lo que permite el flujo exacto del VSP por electroterminal.
2. C1 es simple y explicable ("cada ruta va al electroterminal más cercano a donde sus buses empiezan y terminan"); C2 agrega rigor (asignación generalizada con carga que depende del electroterminal)
   pero su efecto no justifica la complejidad en el caso base, y su capacidad es un **promedio diario** que no ve la concentración nocturna (necesario, no suficiente).
3. La historia que queremos contar: el análisis de distancias ida-vuelta justificó clusterizar por ruta; el análisis de carga mostró que C2 casi no mueve nada; el análisis posterior de
   la carga nocturna (Etapa 3) mostró que lo que realmente resolvía el problema de capacidad era unir los dos terminales cercanos.

## Limitaciones

- 15 de las 300 rutas con ida y vuelta usan más de un paradero como inicio o fin de un mismo sentido; se usa el más frecuente.
- Los buses por ruta se estiman por concurrencia máxima (cota inferior): solo ponderan, no son la flota.
- C2 usa un promedio diario de carga; θ no está calibrado.
- C1a se conserva como control y no lo usa ninguna etapa posterior (limpieza de nombres para la entrega final).
