# Justificación: el nivel de carga de la condición cíclica y la regla para elegirlo

> Para pegar en el informe. Separa lo que dijo el profesor, lo medido y el razonamiento propio. La regla se declaró el
> **04/10/2026 antes de correr cualquier nivel distinto de 100%** y se **corrigió el mismo día, antes de volver a
> correr**, al detectar un error de diseño (ver "Qué cambió y por qué"). Texto de referencia:
> `docs/context/02_supuestos_y_decisiones.md`, B6.

## La decisión

Todo bus empieza y termina el día con el mismo nivel de batería `L` (condición cíclica), y `L` es también el tope de
carga. **El nivel no se fija por criterio propio:** se busca con datos, partiendo del máximo que traen los datos del
curso (100%), y se elige **entre las soluciones que cumplen la condición cíclica**, la de menor costo total. El
resultado es **100%, con buses de reserva para cumplir el ciclo**.

## Qué dijo el profesor **[Profesor]**

Debe quedar batería para el día siguiente: la condición cíclica (inicio = fin). Es una **restricción**, no un
indicador. El rango 80-90% fue un **ejemplo**, no una instrucción sobre el nivel. Partir con 100% sin recuperar la
batería es "miope" y nos "come un montón de costos".

## Qué medimos **[Medido]**

- **El dato del curso:** `max_soc = 1,0` en `parameters.csv`: el único límite superior que viene en los datos, y por eso
  el punto de partida.
- **El nivel no cambia la energía a recargar** (con inicio = fin se recarga todo lo consumido), pero sí cuántas
  jornadas necesitan recargar a mitad del día: 30% de las jornadas del caso base superan la batería útil al 100%
  (315 kWh), 45% al 90%, 59% al 80% y 68% al 70%. La jornada más cara consume 676 kWh contra 350 kWh de batería.
- **La política reactiva casi no recarga a mitad del día, parte la jornada:** los huecos entre expediciones son cortos
  (mediana 12,7 min) y ir al electroterminal y volver cuesta ~63 min. Por eso el nivel afecta sobre todo la flota.
- **La carga nocturna no cabe en las ventanas de los buses (hallazgo central).** Casi todos los buses vuelven al patio
  entre las 19:00 y las 02:00. Con las jornadas de E1 al 100%, el **21% de las cargas finales (2.207 de 10.295) termina
  después de la primera salida del día siguiente**, con un atraso mediano de 3,2 h. No es el orden de la cola (cargar
  primero al que sale antes baja el incumplimiento solo de 2.199 a 2.160): es **capacidad en las horas en que los buses
  están en el patio**. Con un LP que reparte la carga de la **mejor forma posible** dentro de la ventana de cada bus,
  **solo cabe el 84% de la energía nocturna** (faltan 354 MWh/día; en E0, el 89,5%). El promedio diario de uso de los
  puestos (73%) lo ocultaba.

## Cómo se cumple la condición cíclica: buses de reserva **[Propio]**

Un bus que no termina de cargar antes de su salida del día siguiente se reemplaza por un **bus de reserva** ya cargado.
En estado estacionario es una rotación: el bus atrasado termina de cargar (atraso < 24 h) y es la reserva del día
siguiente. Se necesitan tantas reservas como ciclos no cumplidos, a 250 USD/día cada una, y el costo total las incluye.
Es una cota superior simple de explicar: *lo que la carga no alcanza a reponer a tiempo se paga con flota.* Una solución
es **factible** si no tiene déficit de energía y todo atraso es menor a 24 h; con déficit (falta de puestos para reponer
la energía) las reservas no la arreglan.

## La regla **[Propio]** y por qué cada parte

Se decide el nivel en **E1** (C1b, con interlining, Los Espinos y Santa Rosa unidos: la configuración propuesta); E0
(por línea, unidos) es robustez. Los escenarios con terminales separados no compiten: son infactibles por déficit de
energía y se muestran como evidencia de la unión.

1. **Grilla 100 / 90 / 80 / 70 / 65 / 60 / 55 / 50%, siempre los ocho.** 100% es el dato; 90 y 80% son los ejemplos del
   profesor; los niveles menores permiten ver si el costo sigue bajando o si alguno llega a cumplir el ciclo sin
   reservas; 50% es el **piso físico** (la expedición más exigente necesita 41,8% de la batería entre ir, hacerla y
   volver).
2. **Solo compiten las soluciones factibles** (sin déficit de energía, atraso < 24 h): la condición cíclica es una
   restricción.
3. **Dos familias, lado a lado:** (a) cíclica **sin** reservas y (b) **con** reservas. Responde "¿existe un nivel que
   haga cíclica la operación sin pagar reservas, y cuánto cuesta frente a 100% + reservas?".
4. **Criterio: menor costo total** (flota + km vacíos + espera + energía + eventos de carga + reservas), el objetivo del
   proyecto.
5. **Empate: si dos niveles difieren en menos de 0,5% del costo total, se elige el más alto.** 0,5% es el orden de
   magnitud del efecto del parámetro menos seguro del modelo (el factor de desvío de 1,3 al valor medido de 1,35 cambia
   el costo de operación en +0,6%). Se prefiere el más alto porque es el dato del curso y no requiere un supuesto
   adicional.
6. **Robustez (no decide):** si el óptimo de E0 coincide con el de E1, no depende de la decisión de interlining.
7. **Razón externa para bajar de 100%** (por ejemplo la fase CC-CV de la carga real o la vida útil de la batería): solo
   con fuente citada. Hoy no hay fuente verificada; si aparece y cambia el óptimo, se reporta como caso alternativo.
8. **Cota LP (evidencia, no decide):** el máximo de energía nocturna que cabe en las ventanas con carga perfecta.

## Resultado del barrido **[Medido]**

**El nivel base es 100%, con buses de reserva.** E1, política reactiva, USD por día:

| Nivel | Buses tras la carga | Reservas (ciclos no cumplidos) | Cota LP | Costo total | vs. 100% | Factible |
|---|---|---|---|---|---|---|
| **100%** | 10.295 | 2.207 | 84,0% | **3.751.250** | | sí |
| 90% | 11.791 | 1.417 | 95,5% | 3.973.783 | +5,9% | sí |
| 80% | 13.267 | 246 | 100% | 4.069.352 | +8,5% | sí |
| 70% | 14.747 | 73 | 100% | 4.424.005 | +17,9% | sí |
| 65% | 15.936 | 50 | 100% | 4.737.923 | +26,3% | sí |
| 60% | 17.717 | 20 | n.c. | 5.206.564 | +38,8% | sí |
| 55% | 19.671 | 13 | n.c. | 5.732.581 | +52,8% | sí |
| 50% | 22.549 | 274 (déficit 25,3 MWh) | n.c. | 6.573.732 | | **no** |

*(n.c.: cota LP no calculada; ya alcanza 100% desde 80% hacia abajo. La grilla llegó hasta el piso físico.)*

- **Robustez:** E0 también elige 100% (3.958.063 USD/día; 90% = 4.136.249; el costo sube con cada nivel menor).
- **Hallazgo 1, la comparación que se pidió:** **ningún nivel entre 100% y 55% cumple el ciclo sin reservas** con la
  política reactiva. El que más se acerca (55%) deja 13 reservas pero cuesta **52,8% más** que 100% con reservas. No
  existe una solución cíclica sin reservas más barata.
- **Hallazgo 2, la cota LP:** al 100% **ningún programa de carga**, ni siquiera el óptimo, cierra el ciclo (solo cabe el
  84%). Desde 80% hacia abajo una carga perfecta sí lo cerraría, pero esa solución costaría ≥ 4,0 M USD/día sin reservas
  (a 80%: 4.007.852), más que 100% con reservas (3,75 M). Es decir, incluso con un MILP perfecto, 100% + reservas sigue
  siendo la solución factible más barata.
- **Hallazgo 3:** bajar el nivel **no arregla** el ciclo, lo paga con flota: cada 10 puntos menos agregan ~1.500 buses,
  porque la batería útil baja de 315 a 210 kWh y casi toda jornada que la supera se parte.
- **El 50% (piso físico) ya es infactible** por déficit de energía: con tantos buses el patio no alcanza a reponerlos.

**Hipótesis de B6, verificadas:** *"un nivel más alto reduce recargas intermedias, eventos y jornadas partidas"*:
confirmada (jornadas partidas 15.183 → 2.929 entre 50% y 100%). *"La energía total cargada no depende del nivel"*: solo
aproximadamente: sube 6% al bajar a 70% (2.221 → 2.353 MWh) por los traslados de las jornadas partidas.

## Qué cambió y por qué (cómo se planificó)

1. El profesor pidió la condición cíclica y dio 80-90% como ejemplo; se decidió buscar el nivel con datos.
2. Se declaró el criterio (mínimo costo total) y se construyó el simulador. **Se escribió una primera regla** con
   admisibilidad "no empeorar los ciclos no cumplidos respecto de 100%". Corrió y eligió 100%.
3. **Se detectó el error antes de presentar:** la regla comparaba contra una referencia que **también incumplía** la
   condición cíclica (21% de ciclos no cumplidos al 100%), y trataba el ciclo como un indicador y no como una
   restricción. La lectura "100% es mejor" no era válida: el modelo no terminaba el día con todos los buses al nivel, o
   sea, esa solución no era factible.
4. Se diagnosticó la causa (capacidad nocturna, no la cola) con el LP, y se corrigió la regla: **solo compiten
   soluciones factibles; el ciclo se cumple con buses de reserva y su costo se paga; se agregan niveles hasta el piso
   físico y las dos familias (con y sin reservas)**. La corrección se escribió **antes** de volver a correr.
5. Se volvió a correr y se aplicó la regla por código (`scripts/13-barrido_niveles.py`), que escribe la tabla con
   la factibilidad, las reservas, la cota y el nivel elegido.

## Limitaciones

- Los buses de reserva son una cota superior simple (no comparten reservas entre atrasos cortos); un modelo de
  rotación más fino podría reducirlas.
- Política reactiva y miope: con carga programada (Etapa 4) bajaría el costo de la energía y las reservas, pero la cota LP
  muestra que al 100% no alcanza para cerrar el ciclo.
- El resultado depende de las jornadas del VSP, que ignora la batería. Un VSP que la vea (jornadas con pausas de carga
  de día) es una mejora para la entrega final.
- Carga lineal a 180 kW (sin curva CC-CV); un solo día laboral; el ciclo supone que el día siguiente es igual.
