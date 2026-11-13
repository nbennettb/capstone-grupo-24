# Comentarios del profesor --- Informe 2, Grupo 24

Este documento reúne los comentarios insertados en el informe y señala
su ubicación mediante la **sección del informe**, no mediante la
numeración de páginas del archivo PDF.

Se incluyen tanto las notas de texto como las observaciones asociadas a
fragmentos destacados. Los destacados que solo marcan un fragmento, sin
incluir una observación textual adicional, se identifican como tales
para no confundirlos con comentarios independientes.

## 1. Sección 3.1 --- Revisión bibliográfica de la metodología

**Comentario 1**

> Falta agregar otras metodologias y el por qué la que ustedes
> seleccionan hace sentido

**Ubicación específica:** sección 3.1, *Revisión bibliográfica de la
metodología*.

## 2. Sección 3.2 --- Metodología propuesta

**Comentario 2**

> Agregar un diagrama que explique claramente input y putput de cada
> etapa y si es un MILP, reglas, heuristicas, ... Además, argumentar que
> tan cerca o lejos están del óptimo

**Ubicación específica:** sección 3.2, en la presentación general de las
etapas de la metodología.

## 3. Sección 3.2.1 --- Asignación de rutas a electroterminales

Los siguientes comentarios se refieren a la etapa de asignación de rutas
a electroterminales.

**Comentario 3**

> hay revisión bibliografica al respecto?

**Ubicación específica:** sección 3.2.1, en la explicación de la
metodología de asignación de rutas a electroterminales.

**Comentario 4**

> p-mediana

**Ubicación específica:** sección 3.2.1, junto a la explicación de la
asignación de rutas a electroterminales. El comentario menciona el
problema de p-mediana.

**Comentario 5**

> Les queda sobrecargado a nivel espacial? temporal?

**Ubicación específica:** sección 3.2.1, en el análisis de la asignación
de rutas y de la carga que esta genera sobre los electroterminales.

**Comentario 6**

> 1.  Por cada tramo horario del dia: (am, pm), por cada ruta que
>     termina en ese horario, asignar segun un modelo sencillo que haga:
>     min(distancia entre el centro de la ruta y el electroterminal
>     asignado) s.a. no asignar más de C_i viajes por electroterminal
>     por horario por qué centroide o inicio o fin o promedio entre
>     am,bos nomas ...

**Ubicación específica:** sección 3.2.1, en la formulación de la
asignación de rutas a electroterminales.

## 4. Sección 3.2.1 --- Fragmento destacado sobre el criterio de asignación

**Destacado 1**

El profesor destaca el fragmento:

> Cada ruta se asigna al electroterminal con la menor distancia
> ponderada a sus paraderos:

**Ubicación específica:** sección 3.2.1, en el párrafo que describe el
criterio de asignación de cada ruta al electroterminal.

**Nota:** este elemento corresponde a un resaltado del texto y no
contiene una observación escrita adicional. Se registra para dejar
constancia del fragmento señalado por el profesor.

## 5. Sección 3.3.1 --- Propósito y construcción del caso base

**Comentario 7**

> el caso base debiera tener interlining, sino la comparacion capaz que
> sea muy injusta

**Ubicación específica:** sección 3.3.1, *Propósito y construcción*, en
el pasaje donde se describe el caso base sin interlining.

## 6. Sección 4.1.3 --- Presentación de resultados

**Comentario 8**

> Mostrar resultados de forma más visual, aprovechar de hacer tablas
> para facilitar la lectura

**Ubicación específica:** sección 4.1.3, hacia el cierre de la sección y
antes de la sección 4.2.

------------------------------------------------------------------------

## Resumen

  -----------------------------------------------------------------------
  Ubicación en el informe                       Cantidad de observaciones
  ------------------------------ ----------------------------------------
  Sección 3.1 --- Revisión                                              1
  bibliográfica de la            
  metodología                    

  Sección 3.2 --- Metodología                                           1
  propuesta                      

  Sección 3.2.1 --- Asignación      4 comentarios y 1 fragmento destacado
  de rutas a electroterminales   

  Sección 3.3.1 --- Propósito y                                         1
  construcción del caso base     

  Sección 4.1.3 --- Presentación                                        1
  de resultados                  
  -----------------------------------------------------------------------

**Total:** 8 comentarios textuales y 1 fragmento destacado sin
comentario textual adicional.

**Criterio de transcripción:** se conserva la redacción original de los
comentarios, incluidos sus errores tipográficos o expresiones
abreviadas. No se agregan interpretaciones como si fueran parte del
comentario del profesor.


# Cosas que hablamos en reunión

Tuvimos una reunión donde explicó un poco más a detalle los puntos. Ten en cuenta que fue hace una semana entonces no recuerdo con claridad exactamente qué dijo, para que no lo tomes literal. También es MUY IMPORTANTE entender que cuando sugiere algo en los comentarios, como "p-means" no significa que debamos usar eso si o si, solo es una idea que se le ocurrió en el momento, el nunca nos va a decir como es que debemos hacer la solución, solo a veces da ideas generales de como profundizar un poco más en alguna sección, pero la validez de esa idea es tarea nuestra comprobarla y fundamentarla. Mientras esté todo bien explicado es correcto. 

Basicamente sugirió agregarle capacidad al clustering. Lo de centroides lo probamos en la entrega pasada pero ya quedó argumentado por qué es mejor usar inicio y fin de la ruta. 

También sugirió hacer el caso base sin interlining.

Luego hablamos de la metodología y que deber dar una solución factible. Hay que encontrar la manera de que podamos correrlo y que de algo factible y que sirva. Con respecto a la relajación, dijo que no pueden quedar cosas que sean imposibles de aplicar en la realidad. Con respecto al tiempo de ejecución, dijo que podemos correr la última etapa en computadores en pararlelo, ahí hay más flexibilidad de correr cosas más largas para que de factible.