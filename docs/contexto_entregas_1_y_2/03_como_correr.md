# Cómo correr la instancia La Reina

Guía para correr el caso base, la Etapa 3, la Etapa 4 y los KPIs en el electroterminal La Reina (depot_id 4) y obtener
`results/instancia_LR/resumen_para_analisis.md`. Cada comando escribe sus CSV al terminar: si uno falla, lo anterior
queda guardado y se retoma desde el que falló.

## 1. Requisitos

- Python 3.11 con `pandas numpy scipy matplotlib tabulate gurobipy psutil` (los de `README.md` más `psutil`).
- Licencia de Gurobi activa (académica). Para comprobarla: `python -c "import gurobipy; gurobipy.Model()"` debe
  imprimir `Academic license`.
- **No hay que volver a correr las Etapas 0-2.** Sus archivos ya existen: `data-processed/expediciones.csv` y
  `data-processed/jornadas_{E0,E1}.csv`.
- **La corrida de la red completa del caso base debe estar en `results/caso_base/`.** El caso base filtrado se compara
  contra ella.
- Todos los comandos se corren desde la raíz del repositorio. `--terminal 4` se puede omitir en 12-, 13- y 14-, porque es
  el valor por defecto (`parametros.TERMINAL_INSTANCIA`).

## 2. Comandos en orden

Los tiempos y la memoria se midieron en pruebas chicas (2 rutas, 20-71 jornadas) y se extrapolaron al terminal completo
(1.333 jornadas Caso base, 1.203 Caso base con interlining, ~1.600-1.700 ventanas de carga). Son órdenes de magnitud.

### Paso 1. Caso base en La Reina
```
python scripts/10-caso_base_carga_reactiva.py --escenario E0 --terminal 4
```
- **Qué hace:** simula la carga reactiva sobre las 1.333 jornadas Caso base del terminal, solo con sus 100 puestos.
- **Tiempo y memoria:** ~10-40 s, ~300 MB.
- **Debe imprimir:**
  - `[OK] Reconstruccion sin cargas calza con el VSP`;
  - `[OK] Cobertura intacta | SOC entre minimo y tope | ...`;
  - `[OK] Igual a la red completa filtrada a La Reina: 1,726 jornadas finales, 319 reservas, ...`;
  - en `=== Resultado ===`: `buses_vsp 1,333`, `buses_final 1,726`, `buses_reserva 319`.
- **Escribe:** `results/instancia_LR/caso_base/`.

### Paso 2. Caso base con interlining en La Reina
```
python scripts/10-caso_base_carga_reactiva.py --escenario E1 --terminal 4
```
- **Qué hace:** lo mismo, sobre las 1.203 jornadas Caso base con interlining (con interlining).
- **Tiempo y memoria:** ~10-40 s, ~300 MB.
- **Debe imprimir:** `[OK] Igual a la red completa filtrada a La Reina: 1,638 jornadas finales, 315 reservas, ...`;
  `buses_vsp 1,203`, `buses_final 1,638`, `buses_reserva 315`.

### Paso 3. Etapa 3 con las tres holguras
```
python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --escenario E1 --holgura 0
python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --escenario E1 --holgura 30
python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --escenario E1 --holgura 60
```
- **Qué hace:** corta cada jornada Caso base con interlining en tramos factibles con la batería y los re-encadena por el patio con un flujo de
  costo mínimo. Deja las ventanas de carga para la Etapa 4.
- **Tiempo y memoria:** ~10-30 s cada una, ~300 MB.
- **Debe imprimir:**
  - `[OK] Reconstruccion sin cargas calza con el VSP`;
  - `[OK] Cobertura exacta de las 10,327 expediciones | todo tramo factible paso a paso ...`;
  - `[OK] Solucion entera | cadenas factibles en tiempo | flota del flujo = cadenas = maximo de intervalos ...`;
  - `[OK] ... ventanas ...: cada una repone su tramo`;
  - el diagnóstico de flota, que empieza con `(i) VSP 1,203`.
- **Qué esperar de la holgura:** con más holgura, más buses en `(iv)`.
- **Escribe:** `results/instancia_LR/etapa3/h0/`, `h30/` y `h60/`.

### Paso 4. Etapa 4: base y sensibilidad
```
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 15
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 30
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 5
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 30 --delta 15
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 60 --delta 15
```
- **Qué hace:** con las ventanas de la Etapa 3 corre Propuesta con carga por orden de llegada (carga por orden de llegada, al minuto) y Propuesta completa (modelo
  agregado: primero el LP como cota, luego el MILP con brecha de 0,5% y límite de 600 s).
- **Requisito:** cada `--holgura h` necesita haber corrido antes el Paso 3 con esa holgura.
- **Tiempo y memoria (el MILP manda; el límite es 600 s):**

  | Δ | Variables (aprox.) | Tiempo | Memoria |
  |---|---|---|---|
  | 30 | ~85 mil | 1-10 min | ~0,5-1 GB |
  | 15 | ~160 mil | 2-12 min | ~1-1,5 GB |
  | 5 | ~480 mil | 5-15 min | ~2-4 GB |

  La realización por minuto agrega entre 10 s y 2 min.
- **Debe imprimir:**
  - `Chequeo previo: energia / capacidad de 24 h = ...%`. Se espera algo cercano al 80%: la energía de los tramos es algo
    mayor que la del VSP por los km extra de los cortes.
  - `[OK] FIFO: ocupacion <= puestos en cada minuto | energia cargada + deficit = consumida.`
  - `[OK] FIFO en la grilla de 15 min: factible para el modelo agregado y mismo costo de energia ...`
  - `LP (cota): ... | MILP: ... USD (+ desempate ...), <estado>, brecha ...%`. El estado es
    `optimo (brecha pedida)` o `limite de tiempo`. En el segundo caso se informa la brecha alcanzada: no es un error.
  - `[OK] E2: energia cargada + deficit = consumida | ocupacion <= puestos en cada bloque | E2 <= E2-FIFO ...`
  - `Realizacion por minuto de E2 ...: minutos sobre 100 puestos: N`. Es informativo y mide el error de los bloques de
    borde.
- **No debe imprimir** `[AVISO] E2 deja ... kWh de deficit`. Si aparece, la energía no cabe en los puestos en 24 h:
  reportarlo, no corregirlo.
- **Escribe:** `results/instancia_LR/etapa4/h0_d15/`, `h0_d30/`, `h0_d5/`, `h30_d15/` y `h60_d15/`.

### Paso 5. KPIs y resumen para el análisis
```
python scripts/14-kpis_instancia.py --terminal 4
```
- **Qué hace:** no corre modelos. Lee todo lo anterior, arma la tabla de KPIs con las mismas definiciones para Caso base, Caso base con interlining,
  Propuesta con carga por orden de llegada y Propuesta completa (más las variantes de holgura de recarga y largo del bloque) y vuelve a verificar las validaciones desde los CSV. Genera las figuras y el
  resumen.
- **Tiempo y memoria:** ~10-30 s, ~300 MB.
- **Debe imprimir:** una línea por validación (`[OK]`, `[NO APLICA]` o `[FALLA]`), la tabla de KPIs y al final
  `TODAS LAS VALIDACIONES OK`.
- **Escribe:** `results/instancia_LR/kpis/tablas/`, las figuras del informe en `results/instancia_LR/informe/` (F0-F6) y **`results/instancia_LR/resumen_para_analisis.md`**.

El orden de los pasos 4 y 5 permite correr el 5 en cualquier momento: el resumen incluye lo que exista y marca como no
corrido lo que falte.

### Paso 6 (P2). Modelo detallado contra el agregado
El detallado se corre **después** del agregado de la misma carpeta (Paso 4), en dos fases dentro de una hora (G11 en
`02_decisiones.md`). No vuelve a resolver ni escribe nada del agregado ni de la carga por orden de llegada; sus salidas van a
`etapa4/h0_d<Δ>/detallado/`.

**Antes de correr**, guardar el estado actual para no perder nada:
```
git add results/instancia_LR
git commit -m "Resultados de la instancia La Reina antes del detallado en dos fases"
```
Luego:
```
python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 15 --detallado
python scripts/14-kpis_instancia.py --terminal 4
```
bloques de 30 es opcional (otra hora): `python scripts/13-etapa4_programacion_carga.py --terminal 4 --holgura 0 --delta 30 --detallado`.
Después, un commit con los resultados.

- **Tiempo y memoria:** ~1 h por largo del bloque (fase 1 hasta 25 min, fase 2 el resto); ~1,5-2 GB con bloques de 15.
- **Debe imprimir:**
  - `[OK] FIFO recalculada = FIFO guardada junto al agregado`. Si falla, la carpeta no tiene el agregado actual: correr antes `13- --delta 15` sin `--detallado`.
  - `--- E2 detallado, fase 1: reservas fijas en las del agregado (218 reservas) ...` y `Fase 1: X USD (...)`. Si dice `[AVISO] La fase 1 no encontro una solucion sin deficit`, la fase 2 parte de la carga por orden de llegada y se informa.
  - `--- E2 detallado, fase 2: modelo completo desde la solucion de la fase 1, limite ... s ---`.
  - `Detallado: X USD (energia + reservas ... + eventos ...)` y `Brecha: ...% (<fuente>)`. La fuente es la menor entre la de Gurobi y la cota válida (G12).
  - `[OK] Detallado: ...` y `[OK] Detallado <= E2-FIFO con eventos (...)`. Si en vez de lo segundo dice `[AVISO] El detallado no supero a la FIFO`, es un resultado y se informa, no un error.
- **En los logs** (`detallado/gurobi_fase1.log` y `gurobi_fase2.log`): la fase 1 debe terminar con `Thread count was 8` y la fase 2 debe empezar con `Loaded user MIP start`.
- **Qué esperar con bloques de 15:** reservas ≈ 218, costo de carga ≈ 109 mil USD, brecha ≤ ~1%.
- **Si se queda sin memoria:** informarlo; también es un resultado sobre el tamaño.
- Los archivos del detallado de corridas anteriores que quedaron en la carpeta principal (`programa_E2_detallado.csv`, `gurobi_detallado.log`) ya no se usan. 14- los ignora, y se pueden borrar después del commit.

## 3. Qué entregar para el análisis

Un solo archivo: `results/instancia_LR/resumen_para_analisis.md`, más las figuras finales del informe en
`results/instancia_LR/informe/` (F0-F6, cada una en PDF para LaTeX, PNG y CSV con sus datos). El resumen contiene:
- la instancia y los parámetros;
- el estado de todas las validaciones;
- los KPIs por escenario (costo total y costo total con espera nocturna). La Propuesta completa es el modelo detallado
  con bloques de 15 min, e incluye el máximo de buses cargando a la vez en la ejecución minuto a minuto;
- el diagnóstico de flota de la Etapa 3;
- las reservas por tipo (diurnas y nocturnas);
- la energía por tramo horario;
- la ocupación por hora;
- las sensibilidades a la holgura de recarga y al largo del bloque (modelo agregado);
- los segundos, el estado y la brecha de cada modelo;
- el modelo detallado frente al modelo agregado;
- las figuras del informe, con un caption propuesto y la cifra principal de cada una;
- las herramientas y el equipo (versiones leídas del entorno).

No hace falta adjuntar los CSV: cada cifra del resumen sale de un CSV de `results/instancia_LR/`.

## 4. Problemas comunes

| Síntoma | Qué hacer |
|---|---|
| `GurobiError: No Gurobi license` o `Model too large for size-limited license` | Activar la licencia académica (`grbgetkey`) y comprobarla con el comando de la sección 1. |
| `MemoryError` o el computador se queda sin memoria en el Paso 4 con bloques de 5 | Correr primero bloques de 30 y 15. Si bloques de 5 no cabe, se informa así (también es un resultado sobre el tamaño). Cerrar otros programas ayuda. |
| El MILP termina por `limite de tiempo` | No es un error: el resumen informa la brecha alcanzada. |
| `AssertionError` en cualquier paso | Copiar el mensaje **completo** (está en español y dice qué falló). No cambiar parámetros para que pase. |
| `No existen las ventanas de la Etapa 3 (...)` | Falta el Paso 3 con esa `--holgura`. |
| `[aviso] No existe la corrida de la red completa` en los Pasos 1-2 | `results/caso_base/tablas/jornadas_E0_soc100.csv` no está: la igualdad no se controla. Recuperar la carpeta antes de seguir. |
| El Paso 5 dice `NO CORRIDO` en alguna validación | Falta correr el paso correspondiente. |

## 5. Pruebas chicas (para revisar el código, no son resultados)

```
python scripts/10-caso_base_carga_reactiva.py --escenario E1 --terminal 4 --rutas C09 C10
python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --rutas C09 C10
python scripts/13-etapa4_programacion_carga.py --prueba --puestos-prueba 3          # con --detallado: ~8 min (congestion forzada)
python scripts/14-kpis_instancia.py --terminal 4 --prueba
```
Escriben en carpetas `*_prueba/` y en `resumen_para_analisis_prueba.md`. `--puestos-prueba` baja los puestos solo para
forzar congestión y ejercitar las reservas; nunca se usa en la instancia. Cada una tarda entre 1 y 4 s.

## 6. Scripts de la red completa (no se vuelven a correr en esta entrega)

- `scripts/10-caso_base_carga_reactiva.py --escenario E1` (sin `--terminal`) y `scripts/11-caso_base_nivel_bateria.py`:
  el caso base y el barrido de niveles de la red completa. Sus resultados ya están en `results/caso_base/`.
- `scripts/16-graficos_informe.py`: los gráficos de datos y del caso base de la red completa (`results/presentacion/`).
