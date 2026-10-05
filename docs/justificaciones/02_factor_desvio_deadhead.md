# Justificación: factor de desvío del deadhead (1,3)

> Para pegar en el informe. Separa lo que dijo el profesor, lo que medimos y lo que es razonamiento
> nuestro. Datos y gráficos: `results/etapa0_calibracion_deadhead/` (script
> `scripts/9-calibracion_deadhead.py`).

## La decisión

Todo desplazamiento sin pasajeros (salida del electroterminal, regreso y encadenamiento entre
viajes) se calcula como **distancia en línea recta × 1,3**, a 20 km/h. No usamos la red vial de
OpenStreetMap.

## Qué dijo el profesor **[Profesor]**

La distancia euclidiana es una decisión de modelación nuestra, pero "si es euclidiana probablemente
nos la critiquen". Por eso la respaldamos con datos propios.

## Qué medimos **[Medido]**

Los 839 trazados GTFS son el camino real que recorre un bus por las calles. En cada trazado tomamos
pares de puntos separados por *s* km **de recorrido** y calculamos `s / distancia en línea recta`: es
cuánto más largo que la recta es el camino real, a la escala de un deadhead (33.000 ventanas de 1 km
y 11.600 de 15 km, cada 0,5 km de recorrido).

| Escala *s* | Mediana | p25 – p75 | p90 | Ventanas con factor ≤ 1,3 |
|---|---|---|---|---|
| 1 km | 1,04 | 1,00 – 1,27 | 1,47 | 77% |
| 3 km | 1,22 | 1,04 – 1,45 | 1,83 | 60% |
| 5 km | 1,29 | 1,09 – 1,55 | 2,03 | 52% |
| 10 km | 1,35 | 1,17 – 1,68 | 2,51 | 45% |
| 15 km | 1,38 | 1,20 – 1,75 | 3,70 | 41% |

¿Qué escala le toca a cada deadhead? El **interlining** se permite hasta 3 km, así que corresponde a
1-3 km. El **pullout/pullin** de cada ruta tiene mediana de ~12 km (p10-p90: 6-16 km, ponderado por
buses estimados), así que corresponde a 5-15 km.

- **Interlining:** el 1,3 queda sobre la mediana medida (1,04-1,22). Es conservador.
- **Pullout/pullin:** la mediana medida (1,29-1,38) es cercana a 1,3 y algo mayor a escalas largas.

## Cómo lo interpretamos **[Propio]**

1. Los trazados son rutas comerciales: sirven paraderos y hacen lazos, así que rodean **más** que un
   traslado en vacío por el camino directo. El valor medido es una **cota superior** del rodeo de un
   deadhead, no un valor central. Con eso, el 1,3 queda entre un trayecto directo (factor ≥ 1) y el
   rodeo de una ruta con pasajeros.
2. A la escala de pullout/pullin no podemos afirmar que 1,3 sea conservador: podría subestimar algo
   el costo de salir y volver al electroterminal. Por eso lo tratamos como un parámetro con
   sensibilidad (1,2 / 1,3 / 1,5 y el valor medido) y miramos cuánto cambia la flota y el costo
   (Etapa 2).
3. El factor afecta sobre todo al **costo** de los kilómetros vacíos (pullout/pullin), no a la
   factibilidad del interlining, que ocurre a distancias cortas donde el 1,3 es holgado.
4. No usamos OSM por ahora: agregaría una caja negra y no cambia la conclusión de orden de magnitud.

## Sobre el radio de interlining (3 km)

- **[Propio]** El radio máximo para encadenar viajes de rutas distintas (3 km) se eligió para acotar el tamaño del problema: sin un límite habría que considerar casi todos los pares de viajes (miles de millones de arcos).
  No es una medición. Se compara contra la distancia ya multiplicada por 1,3, así que equivale a ~2,3 km en línea recta (~9 min a 20 km/h).
- **[Medido]** Sensibilidad sobre E1: 1 km → 8.198 buses (+11,3%), 2 km → 7.577 (+2,9%), **3 km → 7.366**, 4 km → 7.201 (−2,2%), 5 km → 7.118 (−3,4%); el tiempo de cómputo pasa de ~20 s a ~120 s.
  Los retornos son decrecientes: cada km extra ahorra menos buses que el anterior.
- **Cómo lo interpretamos [Propio]:** el radio **no es inocuo**; es una decisión de tamaño del modelo y su efecto es del mismo orden que el del layover. Lo mantenemos porque ampliarlo exigiría rehacer la carga con jornadas más largas, y lo
  declaramos como limitación y mejora para la entrega final. Sirve en una dirección: el ahorro del interlining que reportamos es un piso (con 5 km, E1 usaría 17,7% menos flota que E0, contra 14,9% con 3 km).
  LB usa el mismo radio, así que el +4,4% de E1 sobre LB es a igual radio.

## Limitaciones

- Los buses circulan por avenidas principales: el factor podría subestimar el de un par
  origen-destino cualquiera por calles menores.
- Los trazados cubren la red de buses, no todo par de puntos de la ciudad.
- Sin topografía, congestión ni sentidos de calles.
- Mejora para el informe final: validar contra la red vial de `chile.gpkg`.

*Referencia a verificar antes de citarla: factores de rodeo en redes urbanas (por ejemplo Ballou,
Rahardja & Sakai, 2002, Transportation Research Part A). No se afirma nada de ella en este texto.*
