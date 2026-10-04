# Justificación: la carga que se usa para asignar rutas a electroterminales (C2)

> Para pegar en el informe. Separa lo medido, lo que viene del profesor y el razonamiento propio. Datos:
> `results/etapa1_clustering/tablas/{validacion_carga_c2,capacidad_por_terminal}.csv` (script
> `scripts/5-clustering_c2.py`).

## El problema que encontramos

C2 asigna cada ruta a un electroterminal sin pasarse de su capacidad de carga. En la primera versión, la
carga de una ruta era solo la energía de sus viajes con pasajeros. Con esa medida C2 coincidía con la
asignación más cercana (C1b) y Los Espinos usaba 89,9% de su capacidad: parecía que la capacidad "no
restringía". Al construir el simulador de carga (Etapa 3) apareció que Los Espinos no podía reponer toda su
energía. La causa: **un electroterminal no recarga solo los viajes con pasajeros, sino todo lo que el bus
consumió, incluido salir del electroterminal y volver**.

## Qué medimos **[Medido]**

Comparamos, por electroterminal, la energía real de las jornadas del VSP (asignación C1b; escenarios E0 y E1)
con lo que estimaba C2:

| Electroterminal | Solo energía comercial | Estimador corregido | Uso de capacidad real (E0 / E1) |
|---|---|---|---|
| Vespucio Norte | −9,3% / −8,7% | −1,2% / −0,5% | 34,1% / 33,9% |
| El Conquistador | −14,2% / −12,6% | −2,7% / −1,0% | 81,3% / 79,9% |
| Los Espinos | −13,6% / −12,3% | −2,4% / −1,0% | **104,0% / 102,6%** |
| La Reina | −13,1% / −12,4% | −2,9% / −2,0% | 78,5% / 77,8% |
| Santa Rosa | −13,9% / −12,7% | −3,1% / −1,7% | 68,0% / 67,1% |

(Error de cada estimación respecto de la energía real.) Con la energía real, Los Espinos necesitaba más
del 100% de su capacidad de 24 h: la asignación más cercana era **infactible**, no solo apretada.

## La corrección **[Propio]**

La energía de salir y volver ya estaba en el modelo como **costo**: C2 calcula `c_rd = 2 · dist_rd · n_r ·
costo_km`. La misma distancia y el mismo número de buses dan su **energía**:

  `h_rd = ( kWh_r + 2 · dist_rd · n_r · 1,4 ) / 180`   (horas-cargador por día)

Dos propiedades la hacen coherente con el resto del modelo: (1) no usa datos nuevos, y (2) hace que la
carga **dependa del electroterminal**: mandar una ruta a uno lejano no solo cuesta más km, también exige más
carga ahí. El problema pasa a ser una asignación generalizada (GAP) en su forma estándar.

Con la corrección, el estimador subestima solo 0,5 a 3,1%. El resto son los traslados entre viajes
(interlining) y la diferencia entre los buses estimados por ruta (cota inferior) y los reales. Se declara
como limitación y el script falla si el error pasa de 5%.

## Qué cambia en el resultado **[Medido]**

- La asignación más cercana deja a Los Espinos al 101,6% y **C2 mueve 5 rutas** (4 a Santa Rosa, a 1,1 km;
  1 a El Conquistador); Los Espinos baja a 97,6%. El costo de pullout/pullin casi no cambia (83.271 →
  83.276 USD/día).
- El resultado anterior "C2 = C1b" (y "E2 = E1", con la nomenclatura antigua) era un **artefacto del estimador**, no una conclusión
  sobre la capacidad. Se corrige y se declara.
- **Límite que se mantiene:** C2 respeta un promedio diario. Con C2 sin unir (variante E1_C2_sep), Los Espinos usa 98,5% de su capacidad real
  y aun así el simulador reactivo deja 21 MWh sin reponer (la carga solo puede ocurrir cuando los buses están
  en el patio). Respetar el 100% diario es necesario, no suficiente (`02_supuestos_y_decisiones.md`, C8).
- Unir Los Espinos y Santa Rosa (E1) lleva la carga al 82,5% de la capacidad combinada y elimina el
  déficit: es la evidencia numérica de la decisión B9.

## Qué dijo el profesor **[Profesor]**

Los puestos limitan solo la carga simultánea y se puede cargar las 24 horas; de ahí el 24 h × puestos de la
capacidad. El profesor sugirió probar el caso base una vez clusterizado y mirar los costos, que es lo que
dejó al descubierto el problema.

## Cómo se planificó

La decisión se tomó en este orden, y cada paso quedó documentado antes del siguiente: (1) el simulador de
carga mostró el déficit de Los Espinos; (2) se midió la energía real por electroterminal y se vio que la
Etapa 1 la subestimaba 9-14%; (3) se propuso la fórmula con la distancia y el `n_r` que ya definían el costo;
(4) se validó contra la energía real **antes** de regenerar las variantes con C2; (5) se regeneró la cadena
completa (Etapa 1, VSP y simulador); (6) se decidió dejar C2 como propuesta y usar C1b con los terminales unidos
como configuración base (`02_supuestos_y_decisiones.md`, B11).
