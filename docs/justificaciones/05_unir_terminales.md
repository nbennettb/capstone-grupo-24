# Justificación: unir Los Espinos y Santa Rosa, y por qué C2 queda como propuesta

> Para pegar en el informe. Separa lo medido, lo que dijo el profesor y el razonamiento propio. Datos:
> `results/etapa1_clustering/`, `results/etapa2_vsp/`, `results/etapa3_carga_reactiva/`. Escenarios: E0 (por línea) y E1
> (con interlining), ambos con terminales unidos; E0_sep y E1_sep (los mismos, separados); E1_C2 y E1_C2_sep (variantes
> con la asignación C2, unidos y separados).

## La decisión

La asignación de rutas a electroterminales de la entrega es **C1** (el electroterminal más cercano a los paraderos
terminales reales de cada ruta; internamente `c1b`), y **Los Espinos y Santa Rosa se tratan como un solo
electroterminal** de 270 puestos (120 + 150) **en todos los escenarios operacionales**, manteniendo sus dos patios
físicos para las distancias. La asignación con restricción de capacidad (**C2**) se formula y se prueba, pero queda
como **propuesta**, no como caso base.

## Qué dijo el profesor **[Profesor]**

Unir los dos electroterminales es una decisión de modelación nuestra y es válida, siempre que se justifique. El
profesor también pidió probar el caso base una vez clusterizado y mirar los costos para saber qué tan buena es la
clusterización, y una metodología bien propuesta, incluido el modelo de clusterización.

## Por qué unirlos **[Medido]**

1. **Están a 1,11 km entre sí;** el siguiente par más cercano está a 5,86 km. Un bus que sale de un patio y vuelve al
   otro sigue volviendo "al mismo electroterminal" y no viola el retorno.
2. **Sin unir, la solución es infactible.** Con la energía **real** de las jornadas (incluye pullout, pullin e
   interlining), Los Espinos necesita **104,0% (E0_sep) y 102,6% (E1_sep)** de su capacidad de 24 h (puestos × 24 h ×
   180 kW): no hay puestos para reponer su energía aunque la carga se programe a la perfección. En el simulador queda
   con un déficit de **44 a 48 MWh/día** sin reponer, y los buses de reserva no lo arreglan (son para el ciclo, no para
   la energía).
3. **Unidos, la solución es factible:** la carga necesaria baja a **82,5%** de la capacidad combinada y el déficit es 0
   (E0 y E1).
4. **En el VSP, unir baja la flota 94 buses en E1** (E1_sep 7.460 → E1 7.366; −1,3% del costo de operación): las 186
   rutas de ambos pasan a poder encadenarse entre sí. En E0 (por línea) el VSP no cambia, pero el escenario pasa de
   infactible a factible. En E1, 1.068 jornadas salen de un patio y vuelven al otro.
5. **Costo total con carga y reservas (nivel 100%):** E1_sep 3.849.470 (infactible) contra E1 3.751.250 USD/día
   (factible, −2,6%); E0_sep 4.036.222 (infactible) contra E0 3.958.063 (factible). Los ciclos no cumplidos de E1 bajan de
   2.518 a 2.207.

## Por qué C2 queda como propuesta y no como base **[Medido]** y **[Propio]**

- **Su aporte es marginal.** Con la carga corregida (la que incluye pullout y pullin, ver
  `08_carga_real_en_clustering.md`), C2 mueve **5 de 417 rutas**, el VSP cambia en +0 buses en E1 y +2 sin unir, y el
  costo de pullout/pullin en +5 USD/día. Combinado con la unión, mejora el costo total solo 0,3% (E1 3.751.250 → E1_C2
  3.740.069 USD/día).
- **No resuelve el problema que motivó la capacidad.** Sin unir, con C2 Los Espinos usa 98,5% de su capacidad real y aun
  así el simulador deja **21 MWh** sin reponer (E1_C2_sep, infactible): respetar el 100% diario es necesario, no
  suficiente, porque la carga solo puede ocurrir cuando los buses están en el patio. La unión sí lo resuelve.
- **Su parámetro de holgura θ no está calibrado.** Calibrarlo exige el simulador y más corridas; con la presentación en
  pocos días es una mejora honesta para la entrega final, no un resultado cerrado.
- **C1 es simple y explicable.** "Cada ruta va al electroterminal más cercano a donde sus buses empiezan y terminan" se
  entiende sin matemática; C2 agrega rigor (asignación generalizada con carga que depende del electroterminal) pero su
  efecto no justifica la complejidad para el caso base.

**C2 se presenta como metodología propuesta**, con su formulación, su validación contra la energía real y su límite
declarado, y con su continuación: calibrar θ con el simulador o delegar la programación de la carga al MILP (Etapa 4).

## Sobre C1a (centroide)

Se conserva como control de sensibilidad: cambia 41 de 417 rutas pero solo 0,7% del costo de pullout/pullin
(83.843 → 83.271 USD/día). Su lectura: la métrica de distancia importa poco; lo que importa es la capacidad de carga. No
la usa ninguna etapa posterior. En el relato se llama **C1** al criterio de paraderos reales.

## Limitaciones

- La unión supone que un bus puede cargar en cualquiera de los dos patios y operar desde ambos, lo que el profesor
  declaró válido pero depende de que la infraestructura lo permita en la práctica.
- Aun unidos, la capacidad nocturna no alcanza para cerrar el ciclo con las jornadas actuales (cota LP: 84% de la
  energía nocturna cabe en E1); el ciclo se cumple con buses de reserva (ver `04_nivel_carga_ciclico.md`).
- Las cifras son del nivel de batería 100%, que el barrido de la Etapa 3 confirma como base.

## Cómo se planificó

(1) El simulador de carga mostró el déficit de Los Espinos; (2) se midió la energía real por electroterminal; (3) se
corrigió el estimador de carga de C2 y se vio que movía solo 5 rutas y no eliminaba el déficit; (4) se comparó con la
unión, que sí lo elimina; (5) se decidió usar C1 con la unión como configuración base en **todos** los escenarios, para
que el caso base sea factible, y dejar C2 como propuesta; (6) se regeneró la escalera (E0, E1, LB) con las evidencias de
terminales separados y las variantes con C2 aparte.
