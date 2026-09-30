# Cierre de ronda (29-30/09) — qué se hizo, qué mirar, qué decidir

> Escrito para el resto del grupo, no solo para quien corrió el código. Si no viste ninguna de las
> sesiones de trabajo, este documento más los reportes de cada etapa deberían bastar para que puedas
> explicarle el resultado a otra persona.
>
> Última edición: **30/09/2026**.

---

## 1. Qué se hizo

La ronda del 28/09 había corrido las Etapas 0, 1 y 2 completas en una sola sesión. El resultado
numérico estaba bien, pero nadie del grupo lo había visto construirse paso a paso, así que no era
defendible frente al profesor ni al ayudante. Esta ronda (29-30/09) **rehizo la Etapa 0 y la Etapa 1**,
con revisión y aprobación explícita después de cada una. La Etapa 2 quedó pausada a propósito — su
código existe y funciona (heredado de la ronda anterior), pero tiene supuestos sin validar (ver
sección 4).

- **Etapa 0 (preprocesamiento):** se confirmó que expandir el GTFS por frecuencia a 64.502
  expediciones reales era necesario, no cosmético, y se agregaron tres tablas por ruta que antes no
  existían, para que la Etapa 1 no dependiera de la Etapa 2.
- **Etapa 1 (clustering de rutas a electroterminales):** tres estrategias que aíslan un cambio a la
  vez — C1a (heurística, centroide), C1b (heurística, paraderos reales), C2 (MILP con capacidad) —
  comparadas bajo un criterio común, con mapas geográficos y 22 archivos de evidencia.

Detalle completo, cifras y bitácora fechada: [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md).

## 2. Los tres resultados que hay que poder explicar en la presentación

1. **Por qué se clusteriza por ruta y no por viaje suelto.** El 94,7% de las 300 rutas con ida y
   vuelta cierran su ciclo a menos de 500 m (mediana 85 m) — medido con los datos del proyecto, no
   citado de un paper. Archivo: `data-processed/rutas_ida_vuelta.csv`, gráfico:
   `results/etapa0_preprocesamiento/graficos/ida_vuelta_distancia.png`.

2. **Bajo el caso base aprobado, la capacidad de los electroterminales no restringe.** El modelo con
   capacidad (C2) da exactamente el mismo resultado que la heurística sin capacidad — lo comprobamos
   con un chequeo automático en el propio código, no a ojo. Esto es un resultado real, no una falla
   del modelo: dice que con SOC inicial 100% hay margen de sobra. Bajo el escenario alternativo
   (recargar todo lo consumido cada día) sí aprieta, y ahí es donde vale la pena seguir invirtiendo
   modelo. Archivo: `results/etapa1_clustering/tablas/capacidad_dos_supuestos.csv`, gráfico:
   `results/etapa1_clustering/graficos/capacidad.png`.

3. **El centroide es una simplificación casi inocua.** Medir contra los paraderos reales en vez del
   centroide mueve 41 de 417 rutas (10%), pero el costo total de pullout/pullin solo mejora 0,7%.
   Archivo: `results/etapa1_clustering/tablas/comparacion_estrategias.csv`.

## 3. Traspaso: qué archivo mirar según tu rol

No hace falta que todos lean el código. Con esto alcanza para entender el resultado y poder
discutirlo:

| Si te toca... | Mira esto primero |
|---|---|
| Escribir la sección de datos/metodología del informe | `results/etapa0_preprocesamiento/reporte.md`, `results/etapa1_clustering/reporte.md` |
| Preparar las láminas de resultados de la presentación | Los mapas en `results/etapa1_clustering/mapas/` (especialmente `mapa_c2.png` y `mapa_diferencias.png`) y el gráfico `graficos/capacidad.png` |
| Escribir la discusión de supuestos / limitaciones | `docs/context/04_preguntas_reunion.md` (trae la evidencia numérica de cada supuesto crítico) |
| Revisar o retomar el código | `docs/context/03_guia_pruebas.md` (cómo correr todo desde cero) |
| Escribir la Carta Gantt / pasos futuros | Sección 4 de este documento |

Todos los CSV de `data-processed/` y `results/*/tablas/` usan `;` como separador (ábrelos con Excel
normal, o `pd.read_csv(path, sep=";")` en Python).

## 4. Qué hay que decidir en grupo (antes de seguir con la Etapa 2)

1. **Con qué estrategia de clustering nos quedamos: C1a, C1b o C2.** Dado que C2 = C1b bajo el caso
   base, la decisión real es C1a (más simple, ligeramente peor) vs. C1b/C2 (paraderos reales, 0,7%
   mejor). Recomendación de quien corrió esta ronda: **C1b**, porque además es la que sostiene a C2
   si el profesor pide el escenario cíclico — no hay que rehacer nada si cambia la respuesta a la
   pregunta de SOC.
2. **Si se retoma la Etapa 2 antes o después de la reunión con el profesor.** El código
   (`scripts/6-`, `7-`) existe y funciona: retomarla es rápido una vez estén claros los supuestos de
   SOC inicial, horas de carga disponibles y retorno al electroterminal (preguntas 3, 5 y 7 de
   `04_preguntas_reunion.md`). Correrla antes arriesga rehacer trabajo si la respuesta cambia el
   diseño.
3. **Quién presenta qué el 06/10** (máximo 3 personas, 10 minutos estrictos — ver guión abajo).

## 5. Plan a futuro

### 5.1 Depende de la respuesta a la pregunta de SOC (la que más importa)

| Si el profesor dice... | Entonces |
|---|---|
| **SOC 100% está bien** (carga nocturna fuera de alcance, es el caso base actual) | La capacidad de electroterminales no restringe. C2 queda como el modelo que **demuestra** eso, no como el que decide la asignación (basta C1b). El esfuerzo de las Etapas 3-4 va a insertar recargas puntuales en el ~25-40% de jornadas que superan la batería, y a optimizar **cuándo** cargar por tarifa horaria — no a pelear por espacio de carga. |
| **Hay que dejar los buses cargados para el día siguiente** (escenario cíclico) | La capacidad pasa a ser el centro del problema. C2 se justifica por sí solo como necesario (ya no solo como validación), la pregunta de cuántas horas al día se puede cargar se vuelve crítica (con 10h es infactible, con 24h no), y la Etapa 4 (programación de carga por electroterminal) pasa a ser la contribución más importante del proyecto. |

### 5.2 Carta Gantt hasta el informe (11/10)

*(Responsable: a completar en la reunión del grupo — cada fila necesita un nombre antes de entrar al informe, la rúbrica lo exige explícitamente, 15 pts.)*

| Fecha | Hito | Depende de | Responsable |
|---|---|---|---|
| Antes del 01/10 | Reunión con profesor/ayudante: resolver `04_preguntas_reunion.md` | — | |
| 01/10 | Decidir con el grupo: estrategia de clustering final, y escenario de SOC a modelar | Respuesta del profesor | |
| 01-02/10 | Retomar Etapa 2 (VSP) con los supuestos ya validados, sobre C1b/C2 | Paso anterior | |
| 02-03/10 | Etapa 3: inserción de recargas por jornada | Etapa 2 corrida | |
| 03/10 | Etapa 4: programación de carga por electroterminal (empezar por 1 electroterminal como prueba de concepto, luego los 5) | Etapa 3 | |
| 04/10 | KPIs completos vs. caso base + 1-2 sensibilidades (SOC, layover) | Etapas 2-4 | |
| 04-05/10 | Armar slides + ensayo cronometrado (10 min estrictos) | Resultados completos | |
| **06/10** | **Presentación** | — | |
| 07-10/10 | Informe: formalización matemática completa, resultados, discusión de supuestos, Gantt con responsables actualizado | Presentación | |
| 11/10 | **Entrega del informe** | — | |

## 6. Guión de 2 minutos para la presentación (parte de clustering, dentro de los 10 min totales)

**Lámina 1 — el problema del clustering (20 s):** *"El Informe 1 nos pidió revisar en profundidad
cómo agrupar. Decidimos agrupar por ruta completa, no por viaje suelto, porque el 95% de nuestras
rutas cierran su ida-vuelta a menos de 500 metros — separar la ida de la vuelta rompería algo que se
encadena solo."* → mostrar `ida_vuelta_distancia.png`.

**Lámina 2 — las tres estrategias (40 s):** *"Comparamos tres formas de asignar rutas a los 5
electroterminales: una heurística simple, la misma heurística midiendo contra paraderos reales, y un
modelo de optimización con restricción de capacidad."* → mostrar `mapa_c2.png` (el mapa final, se ve
bien y es autoexplicativo).

**Lámina 3 — el resultado que sorprende (40 s):** *"Bajo nuestro caso base, el modelo con capacidad
da exactamente el mismo resultado que la heurística sin capacidad — lo comprobamos automáticamente en
el código. Eso significa que con batería llena al empezar el día, los 700 puestos de carga sobran.
Pero si en cambio hay que dejar los buses cargados para el día siguiente, un electroterminal llega al
90% de uso y con poca ventana de carga nocturna el problema deja de tener solución."* → mostrar
`capacidad.png`.

**Lámina 4 — qué viene (20 s):** *"Por eso esta es justo la pregunta que le llevamos al profesor: si
el caso base es con batería llena o si hay que modelar el ciclo completo. La respuesta decide cuánto
esfuerzo del proyecto va a infraestructura de carga versus a optimizar cuándo cargar."*

**Qué NO decir** (para no gastar tiempo): no entrar en la formulación matemática completa del MILP
(va en el informe, no en la presentación), no mostrar los 5 mapas por electroterminal (uno solo
alcanza), no explicar el barrido de θ en detalle (queda como pregunta si alguien pregunta "¿y si
apretamos la capacidad?").

---

## 7. Referencias

- Bitácora completa y cifras: [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md)
- Preguntas para la reunión: [`04_preguntas_reunion.md`](04_preguntas_reunion.md)
- Cómo reproducir todo: [`03_guia_pruebas.md`](03_guia_pruebas.md)
