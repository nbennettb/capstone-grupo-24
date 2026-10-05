# Justificación: el caso base y la escalera de escenarios

> Para pegar en el informe. Separa lo que dijo el profesor, lo medido y el razonamiento propio. Datos: `results/etapa2_vsp/`,
> `results/etapa3_carga_reactiva/`, `results/etapa5_kpis_comparacion/`.

## La decisión

El **caso base (E0)** es la operación intuitiva: cada ruta usa solo sus propios buses (sin interlining), con su electroterminal más cercano (C1), los terminales Los Espinos + Santa
Rosa unidos, y una política de carga reactiva (el bus carga solo cuando lo necesita, sin mirar la tarifa), con la condición cíclica cumplida mediante buses de reserva. **E1** agrega el
interlining dentro del electroterminal y es la configuración propuesta. **LB** (interlining libre, sin retorno al electroterminal) es una cota inferior y **no es un escenario operacional**.
Cada escalón cambia **una sola decisión**, para medir su efecto marginal.

## Qué dijo el profesor **[Profesor]**

El caso base de "operación por línea + carga reactiva" **es válido**; hay que ser conscientes de qué se espera que pase y verificar si el caso base lo refleja. Si no es difícil, conviene
un segundo caso base con interlining para ver el efecto aislado de esa decisión. Al prohibir el interlining, toda la ganancia aparece al habilitarlo. Además, la solución debe ser
**factible**: debe quedar batería para el día siguiente (condición cíclica).

## Qué esperábamos y qué medimos **[Medido]**

| Expectativa | Resultado |
|---|---|
| (i) El interlining baja fuertemente la flota | E0 8.654 → E1 7.366 buses en el VSP (−14,9%); costo total con carga 3.958.063 → 3.751.250 USD/día (−5,2%). Concentra el 81% de lo que separa a E0 de LB |
| (ii) Unir los dos terminales cercanos elimina el déficit de carga | Déficit de energía 44-48 MWh → 0; el VSP baja 94 buses en E1 (`05_unir_terminales.md`) |
| (iii) El ciclo diario se puede cumplir | No con la política reactiva a ningún nivel de batería; sí pagando buses de reserva (E1: 2.207; E0: 1.988). Con las jornadas actuales, ni una carga perfecta lo cerraría al 100% (cota LP 84% en E1, 89,5% en E0) |
| (iv) Programar la carga mejora a la reactiva | A escala de instancia, el MILP baja el costo de la carga al menos 10-24% frente al simulador, casi todo por menos reservas (`07_instancia_chica_milp.md`) |

Resultados con los cuatro escenarios factibles al nivel 100% (USD/día): E0 3.958.063 (11.259 buses tras la carga + 1.988 reservas); E1 3.751.250 (10.295 + 2.207). La flota es el 69-71% del costo.
El **hallazgo inesperado (C9)** es la distancia entre el VSP y la operación real: de 7.366 buses del VSP a 12.502 con la batería (+70%), mientras el clustering agrega solo 311 sobre la cota LB (+4,4%).

## Cómo lo interpretamos **[Propio]**

1. E0 es un caso base sólido porque es lo que haría un operador sin optimizar, es simple de explicar y separa el valor de cada decisión (interlining, carga).
2. La condición cíclica es una **restricción** y no un indicador: un caso base que no la cumpliera no sería una solución factible. Se cumple con buses de reserva (250 USD/día cada uno),
   que es una cota superior simple: lo que la carga no alcanza a reponer a tiempo se paga con flota.
3. Los terminales se unen en **todos** los escenarios operacionales: sin unirlos el caso base es infactible (déficit de energía en Los Espinos), y un caso base infactible no sirve de referencia.
   E0_sep y E1_sep se conservan como evidencia.
4. El nivel de batería (100%) sale de un barrido 100-50% por costo total, no de un supuesto (`04_nivel_carga_ciclico.md`).

## Limitaciones

- El caso base es una política miope por diseño: el valor del MILP se mide contra ella, pero una política reactiva más inteligente reduciría esa brecha.
- Deadhead euclidiano × 1,3 y layover de 3 min (−2,8% a +6,0% de flota con 0 a 10 min) y radio de interlining de 3 km (+11,3% a −3,4% con 1 a 5 km): los dos supuestos más sensibles; ver `02_factor_desvio_deadhead.md`.
- Un día laboral; consumo constante; carga lineal a 180 kW.
- La espera por puesto en el patio (~100.000 USD/día) se cobra en el total; sin ella, E1 = 3.644.536 y E0 = 3.857.135 y ninguna conclusión cambia.
