# Justificación: la instancia reducida del MILP de carga

> Para pegar en el informe. Separa lo que dijo el profesor, lo medido y el razonamiento propio. Datos: `results/etapa4_milp_carga/`
> (script `scripts/11-milp_carga.py`). Decisiones: `docs/context/02_supuestos_y_decisiones.md`, B12, C10 y C11.

## La decisión

El MILP de programación de carga se prueba en **instancias reducidas** del terminal Los Espinos + Santa Rosa (el más exigido) en E1 al 100%, con N = 10, 30, 50, 100, 200 y 400 buses. **No es el resultado de
toda la red**: el MILP sobre los ~10.300 buses (E3) solo se estima.

## Qué dijo el profesor **[Profesor]**

Si se modela un MILP, esperan que se haya testeado en **instancias pequeñas**, no en el modelo completo.

## Los criterios de la instancia **[Propio]**, y qué se midió **[Medido]**

1. **Escala proporcional:** una instancia con 100 buses y los 270 puestos reales no tendría congestión y el MILP no decidiría nada. Se conserva la razón puestos/bus del terminal en la red (270 / 4.622 =
   0,0584): puestos = N × 0,0584 (2, 3, 6, 12 y 23 para N = 30 a 400).
2. **Selección determinista y anidada:** muestra de jornadas del VSP con semilla fija (24), cada N dentro del siguiente; se muestrean jornadas completas, así el simulador las parte igual que en la red (35/35, 69/69, 139/139... iguales).
3. **No trivialidad, con chequeo automático:** los puestos están saturados en 82-96% de los bloques de la política reactiva (umbral exigido: 10%).
4. **Representatividad:** carga/capacidad de 24 h 80-89% (red 86%); 91-95% de las llegadas entre 19:00 y 02:00 (red 90%); USD/kWh 0,137-0,145 (red 0,142); reservas de la reactiva 12-27% (red 26%).
5. **Instancias inválidas se descartan:** N = 20 recibe 1 puesto y su carga supera el 100% de la capacidad (el simulador deja energía sin reponer), así que no conserva la congestión real.
6. **Comparación justa:** mismos buses y puestos para el simulador reactivo (al minuto), la misma regla reactiva en la grilla del MILP (solución inicial y prueba de correctitud: el MILP cuesta menos o igual
   en todas) y el MILP, cuyo programa se ejecuta minuto a minuto y respeta los puestos.

## La holgura que hace el modelo comparable **[Propio]**

Con las ventanas fijas de las jornadas del VSP, la condición cíclica es infactible al 100% (cota LP 77-96% en las instancias). Se agrega la variable binaria "bus con reserva" (250 USD): el bus puede terminar de cargar
hasta 24 h después de su llegada y su salida la cubre otro bus; la energía se carga igual y ocupa puestos. Es la misma regla del simulador, así la comparación es justa. Descartamos multar la energía no repuesta
porque deja energía y puestos gratis.

## Resultados **[Medido]**

| N (buses) | Puestos | Costo de la carga: simulador → MILP | Ganancia | Reservas simulador → MILP (piso) | Brecha |
|---|---|---|---|---|---|
| 9 (N=10) | 1 | 283 → 253 USD/día | ≥ 10,5% | 0 → 0 (0) | 0,26%: **óptimo** |
| 34 (N=30) | 2 | 2.115 → 1.612 | ≥ 23,8% | 4 → 2 (1) | 1,4% |
| 55 (N=50) | 3 | 4.947 → 4.199 | ≥ 15,1% | 12 → 9 (8) | 2,0% |
| 106 (N=100) | 6 | 9.519 → 8.507 | ≥ 10,6% | 23 → 19 (15) | 2,7% |
| 210 (N=200) | 12 | 19.532 → 17.294 | ≥ 11,5% | 48 → 39 (32) | 1,9% |
| 404 (N=400) | 23 | 41.573 → 35.608 | ≥ 14,3% | 107 → 82 (68) | 8,6% |

- **La regla de "resuelta" se declaró antes de correr:** solo se llama así a una instancia con brecha ≤ 1% certificada; solo N = 10 lo cumple. Las demás son soluciones factibles verificadas; el "piso" de reservas es una cota
  (ningún programa de carga puede tener menos reservas con esas ventanas y puestos), así que el potencial total de reducción en N = 400 está entre 107 → 82 (logrado) y 107 → 68.
- **La ganancia viene de las reservas, no de la tarifa:** el costo medio de la energía casi no cambia a escala (0,1445 → 0,1443 USD/kWh en N = 400); el MILP usa los puestos que la reactiva deja ociosos entre las 16:00 y las 19:00.
- **La grilla de 15 min no es inocua:** la misma regla reactiva en bloques deja 21-50% más reservas que el simulador; por eso la referencia es el simulador. La ganancia es una cota inferior.
- **La escala justifica la reducción:** la brecha crece con N (hasta 8,6%); sobre los 4.622 buses del terminal no se certificaría el óptimo.

## Limitaciones

- Muestra de un solo terminal con una semilla; bloques de 15 min; cargas intermedias fijas (0,5% de los buses); las ventanas vienen del VSP, que ignora la batería (el MILP no cambia la flota).
- Los límites de tiempo no son deterministas: las brechas pueden variar algo entre corridas.
- Extrapolar a toda la red es una estimación; no se presenta como resultado de la red.

## Cómo se planificó

(1) Plan aprobado con la holgura de reservas; (2) checkpoint de N = 10 revisado a mano, donde se detectó que el MILP dejaba buses enchufados sin cargar y se exigió evento continuo; (3) resultado inesperado: ni N = 50 certificaba
el 1%, se reforzó la formulación (desigualdades válidas, al menos un evento por bus) y se agregó el piso de reservas; (4) al revisar los gráficos se vio que la reactiva en bloques inflaba la ganancia y se cambió la
referencia al simulador; (5) se declaró la regla de "resuelta" antes de correr la escalera final y se descartó N = 20 por inválida.
