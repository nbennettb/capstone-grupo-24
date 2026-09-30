# Preguntas para la reunión con el profesor / ayudante

> Para llevar a la próxima reunión. Cada pregunta trae el supuesto que se está usando mientras tanto,
> la evidencia propia que lo respalda (no citada de la propuesta — calculada sobre los datos reales
> del proyecto en esta ronda), y qué cambia en el proyecto según la respuesta. Las tres primeras ya
> se habían enviado el 28/09 sin respuesta; se repiten porque siguen bloqueando decisiones de diseño.
>
> Última edición: **30/09/2026**.

## 1. Alcance real de la Entrega 2 para nuestro proyecto específico

El ayudante pidió explícitamente que esto se discutiera con el profesor antes de seguir. No tenemos
supuesto de respaldo — es la pregunta que condiciona a todas las demás.

## 2. ¿El caso base "operación por línea + carga reactiva" es aceptable?

Cada ruta usa solo sus propios buses (sin interlining), despacho FIFO, electroterminal base = el más
cercano, recarga miope al 100% cuando la batería no alcanza. Es el estándar operacional real y
separa bien el valor de cada etapa (interlining vs. carga inteligente). ¿Es lo que el curso espera
como "política miope, no analítica" de comparación?

## 3. Supuesto de SOC inicial — la pregunta más crítica del proyecto

**¿Los buses parten el día con batería llena (carga nocturna fuera de alcance), o el plan debe
garantizar que terminen el día cargados para el día siguiente (ciclo diario), compitiendo por los
mismos 700 puestos?**

Esta ronda se cuantificó exactamente cuánto cambia la respuesta:

| | SOC inicial 100% (caso base) | Ciclo diario (recargar todo lo consumido) |
|---|---|---|
| Energía a recargar por día | 108 horas-cargador | 10.464 horas-cargador |
| % de la capacidad disponible (H=24h) | **0,6%** | **62%** |
| Uso del electroterminal más cargado | 1,2% (Los Espinos) | 89,9% (Los Espinos) |
| Con solo 10h/día de ventana de carga | 2,8% (sigue holgado) | **infactible** (149% de la capacidad) |

Con SOC 100%, el modelo de asignación de rutas con capacidad (C2) da **exactamente** el mismo
resultado que la heurística sin capacidad — lo comprobamos con un chequeo automático en el código.
La restricción de infraestructura, tal como está modelada hoy, es irrelevante bajo el caso base.

**Por qué importa tanto:** la respuesta decide si "gestionar la capacidad de los electroterminales"
es o no un problema real de este proyecto. Si es SOC 100%, el esfuerzo de las próximas etapas debe
ir a insertar recargas puntuales y optimizar cuándo cargar por tarifa horaria — no a pelear por
espacio. Si es ciclo diario, la capacidad pasa a ser el centro del problema y justifica bastante más
modelo del que tenemos pensado hoy.

## 4. ¿Es aceptable el deadhead euclidiano × factor de desvío calibrado con OSM?

Se usa distancia en línea recta × 1,3 (factor a calibrar/sensibilizar con `osmnx`, ya instalado) en
vez de calcular la ruta real por la red vial para cada par origen-destino. ¿Aceptable como
aproximación para esta entrega?

## 5. ¿Cada bus debe volver a su mismo electroterminal de origen?

Hoy se asume que puede terminar en cualquier electroterminal, no necesariamente el de partida. Afecta
el diseño de los arcos de retorno cuando se retome la Etapa 2, y la interpretación de "electroterminal
base" en el clustering.

## 6. Los 700 puestos no alcanzan para estacionar la flota completa

Con el caso base sin interlining, la flota estimada es del orden de **7.400-8.700 buses** (según se
mida). Los electroterminales solo tienen 700 puestos en total. ¿Se entiende que los electroterminales
son puntos de paso para cargar, no estacionamiento nocturno de toda la flota? ¿Dónde pernocta el
resto de los buses — es parte del alcance del proyecto o queda fuera?

## 7. ¿Cuántas horas al día puede cargar un electroterminal?

No viene en los datos entregados por el curso, y resultó ser el parámetro que decide si el escenario
de ciclo diario es o no factible: con 24h disponibles el sistema aguanta (62% de uso), con 18h queda
al límite (99,3% en Los Espinos), y con 10h (turno nocturno típico) es **matemáticamente infactible**.
¿Hay un valor de referencia que debamos usar, o lo definimos nosotros y lo sensibilizamos?

## 8. Los Espinos y Santa Rosa están a 1,11 km uno del otro

Los otros tres electroterminales están a 5,9 km o más entre sí. Para una heurística geográfica del
"más cercano", repartir rutas entre Los Espinos y Santa Rosa es casi un volado (pequeños cambios en
el punto de referencia de la ruta cambian la asignación). ¿Tiene sentido para el profesor tratarlos
como un solo electroterminal combinado de 270 puestos, o prefiere que se mantengan separados y
dejemos esta sensibilidad como nota?

---

## Versión corta para copiar y pegar (correo / mensaje al ayudante)

```
Hola! Como grupo 24 tenemos 3 preguntas que nos gustaría cerrar antes de seguir avanzando
con la Entrega 2:

1. ¿Cuál es el alcance real esperado para nuestro proyecto específico en esta entrega?
   (nos pidieron discutirlo directamente con el profesor)

2. La más importante: ¿los buses parten el día con batería llena (carga nocturna fuera de
   alcance), o el plan debe garantizar que terminen el día cargados para el día siguiente
   (compitiendo por los mismos 700 puestos de carga)? Ya cuantificamos que esto cambia la
   carga de los electroterminales de ~1% a ~60-90% de su capacidad, así que la respuesta
   define si la infraestructura de carga es o no una restricción real del problema.

3. ¿Cada bus debe volver a su mismo electroterminal de origen al final del día, o puede
   terminar en cualquiera?

Gracias!
```
