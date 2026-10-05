# Guía de pruebas — cómo correr y verificar el pipeline vigente

> Para cualquiera que clone el repo (equipo, ayudante, profesor) y quiera confirmar que el código
> corre y reproduce los resultados documentados en [`01_metodologia.md`](01_metodologia.md).
> No asume que hayas leído el resto de `docs/context/`, aunque se recomienda.
>
> Cubre el pipeline **vigente**: Etapa 0 (preprocesamiento), Etapa 1 (clustering de rutas a
> electroterminales, bajo condición cíclica), calibración del deadhead y Etapa 2 (asignación de buses,
> escalera de escenarios). La Etapa 3 (carga reactiva y barrido de niveles) y la Etapa 4 (MILP en instancia reducida) están hechas. Ver `01_metodologia.md` y
> `05_plan_entrega2.md`.
>
> Última edición: **04/10/2026**.
>

---

## 1. Prerrequisitos

Python 3 con estas librerías:

```
pandas  numpy  scipy  matplotlib  tabulate  gurobipy  geopandas  shapely
```

Verificación rápida (no debería imprimir nada si todo está instalado):

```
python -c "import pandas, numpy, scipy, matplotlib, tabulate, gurobipy, geopandas, shapely; print('OK')"
```

`gurobipy` además necesita una **licencia Gurobi válida** activada en la máquina (académica o
comercial; las académicas son gratuitas en [gurobi.com](https://www.gurobi.com), requieren correo
institucional). Si al correr `5-clustering_c2.py` aparece `GurobiError: No Gurobi license found`, hay
que activar una licencia antes de seguir.

`geopandas`/`shapely` son necesarios desde esta ronda: los usa `scripts/8-clustering_comparacion.py`
para dibujar los mapas de rutas y electroterminales sobre el fondo geográfico de `chile.gpkg`. No hace
falta `osmnx`, `contextily`, `folium` ni `networkx` para nada del pipeline actual.

## 2. Dos puntos de partida posibles

**(a) Repo recién clonado — el camino normal.** `data-filtrado/` ya viene completo en el repo (ver
`docs/context/00_contexto_entrega1.md` sobre qué contiene). Se puede saltar directo a la sección 4.

**(b) Regenerar `data-filtrado/` desde los datos crudos del curso.** Solo hace falta si quieres
verificar el filtrado GTFS→buses desde cero, o si cambiaste algo en `scripts/1-`/`scripts/2-`.
Requiere tener `data-alumnos/gtfs/stop_times.txt` y `shapes.txt` (no están en el repo por tamaño —
los entrega el curso). Con eso:

```
python scripts/1-filtro_datos_buses.py
python scripts/2-filtro_tipo_dia.py
```

Esto sobrescribe `data-filtrado/*.csv`. Después seguir con la sección 4 igual.

También hace falta `data-alumnos/chile.gpkg` (1,3 GB, no está en el repo por tamaño — lo entrega el
curso) para los mapas del script 8. Sin ese archivo, todo lo demás del pipeline corre igual; solo
falla la parte de mapas.

## 3. Orden de ejecución

Mucho más simple que en la ronda anterior: la Etapa 1 ya no depende de la Etapa 2.

```
1 (filtro buses) ──► 2 (filtro dia L) ──► 3 (preprocesamiento, Etapa 0)
                                                  │
                                                  ▼
                                    4 (clustering C1a + C1b, Etapa 1)
                                                  │
                                                  ▼
                                    5 (clustering C2, Etapa 1)
                                                  │
                                                  ▼
                            8 (comparación, tabla ancha, mapas — cierre Etapa 1)
```

`4-clustering_c1.py` y `5-clustering_c2.py` dependen solo de `data-processed/rutas_resumen.csv`,
`terminales_por_ruta.csv` y `terminales.csv` (Etapa 0) — **ninguno de los dos necesita que se haya
corrido la Etapa 2** (a diferencia de la ronda anterior, donde `5-clustering_milp.py` leía
`jornadas_ruta.csv`). `8-clustering_comparacion.py` sí necesita que 4 y 5 ya hayan corrido sobre la
red completa (417 rutas): lee las tres asignaciones que generan (C1a, C1b, C2).

## 4. Por script: checkpoint chico, corrida completa, y qué esperar

Todos los scripts tienen **chequeos de sanidad automáticos** (`assert` con mensajes en español). Si
uno de estos salta, no es "un bug del script en sí" — es una señal real de que algo en los datos, los
parámetros o la lógica cambió, y hay que investigarlo antes de confiar en el resultado.

### `scripts/3-preprocesamiento_expediciones.py` (Etapa 0)

```
python scripts/3-preprocesamiento_expediciones.py --rutas 101      # checkpoint chico (~5 s)
python scripts/3-preprocesamiento_expediciones.py                  # red completa (~10-20 s)
```

Checkpoint: 171 expediciones, 4 paraderos terminales. Red completa (cifras de referencia, validadas
el 29/09): **64.502 expediciones**, **417 rutas**, **641 paraderos terminales**, concurrencia máxima
**6.539 a las 8:00**, **1.883,6 MWh/día**. El script compara contra estas cifras e imprime `[OK]` o un
aviso si difieren.

Output: `data-processed/{expediciones,terminales,rutas_resumen,rutas_ida_vuelta,terminales_por_ruta}.csv`,
`results/etapa0_preprocesamiento/` (reporte + 4 tablas + 4 gráficos).

### `scripts/4-clustering_c1.py` (Etapa 1, C1a y C1b)

```
python scripts/4-clustering_c1.py --rutas 101 102 301   # checkpoint chico
python scripts/4-clustering_c1.py                       # red completa (~1-2 s)
```

C1a = electroterminal más cercano al centroide de la ruta. C1b = más cercano a sus paraderos
terminales reales (ponderado por uso). Red completa (referencia 30/09): C1a reparte 59-111 rutas por
electroterminal, C1b reparte 56-108; **41 de 417 rutas cambian entre ambas**.

Output: `data-processed/rutas_cluster_c1a.csv`, `rutas_cluster_c1b.csv`,
`results/etapa1_clustering/{tablas/distancias_ruta_terminal.csv, graficos/distancias.png}`.

### `scripts/5-clustering_c2.py` (Etapa 1, C2) — no requiere haber corrido la Etapa 2

```
# Checkpoint de reactividad: capacidad muy apretada a proposito
python scripts/5-clustering_c2.py --rutas 203N 203c 204N 211c 301c 542 546e B08 B32 B35 D11 E13 F06 F11 F16 F25 G05 G37 G43 J06 --theta 0.05

python scripts/5-clustering_c2.py    # red completa (~30-40 s: asignación, evidencia y barrido de theta)
```

Resuelve bajo la **condición cíclica** (se recarga todo lo consumido, sin importar el nivel de batería; H = 24 h). En el checkpoint, revisa que
ningún electroterminal supere el 100% y que se reasignen rutas (4 de 20). En la red completa
(referencia, regenerada el 04/10; ~2 min por el barrido de θ):

- La carga de cada ruta incluye su pullout y pullin y depende del electroterminal (C7). Con ella, la
  asignación C1b deja a Los Espinos al 101,6% y **C2 mueve 5 rutas** (4 a Santa Rosa, 1 a El Conquistador).
  Uso de C2: Vespucio Norte 33,7% · El Conquistador 80,8% · **Los Espinos 97,6%** · La Reina 76,2% · Santa
  Rosa 67,1%. Carga total 11.760 h-cargador/día (2.117 MWh) de 16.800. Costo pullout/pullin 83.271 → 83.276 USD/día.
- **Validación del estimador** (`validacion_carga_c2.csv`): error contra la energía real de las jornadas
  −9 a −14% con solo energía comercial y −0,5 a −3,1% con el estimador de C2. El script falla si pasa de 5%.
- **Barrido de θ** (capacidad separada): 0 rutas movidas con θ = 1 (referencia), 8 con 0,9, 14 con 0,8,
  infactible con 0,7. Con Los Espinos + Santa Rosa combinados: 5 con 1 y 0,9, 8 con 0,8, infactible con 0,7.
- **Evidencia "sin recuperación" vs "con recuperación"** (proxy por ruta, sin deadhead; mismo nivel de
  batería en ambos lados). Con recuperación (ciclo): 11.760 horas-cargador (70,0% de la capacidad),
  igual para todo nivel. Sin recuperación: 375 h (2,2%) al 100%, 1.054 h (6,3%) al 90%, 2.106 h (12,5%) al
  80% y 3.352 h (20,0%) al 70%. No genera ninguna asignación.

Output: `data-processed/rutas_cluster_c2.csv`,
`results/etapa1_clustering/tablas/{capacidad_por_terminal,capacidad_sin_vs_con_recuperacion,barrido_theta}.csv`,
`results/etapa1_clustering/graficos/{capacidad_ciclo,capacidad_sin_vs_con_recuperacion,barrido_theta}.png`.

### `scripts/6-vsp_asignacion_buses.py` y `7-comparar_escenarios.py` (Etapa 2) — requiere 3, 4 y 5 corridos en la red completa

Un escenario por corrida de `6-`; `7-` compara. Gurobi con licencia (flujo de costo mínimo; ~5-55 s por
escenario). Checkpoint chico (3 rutas, revisar a mano una jornada: orden temporal, traslados y kWh):

```
python scripts/6-vsp_asignacion_buses.py --modo ruta --asignacion data-processed/rutas_cluster_c1b.csv --subset 101 102 301 --etiqueta E0
python scripts/6-vsp_asignacion_buses.py --modo libre --subset 101 102 301 --etiqueta LB
```

Las corridas con `--subset` guardan sus archivos con sufijo `_subset`; borrarlos antes de la red completa
(`data-processed/jornadas_*_subset.csv` y su fila en `resumen_escenarios.csv`). Red completa. **Todos los escenarios
operacionales usan C1b y los electroterminales 3 y 5 (Los Espinos y Santa Rosa) unidos:**

```
python scripts/6-vsp_asignacion_buses.py --modo ruta    --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --etiqueta E0
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --etiqueta E1
python scripts/6-vsp_asignacion_buses.py --modo libre --etiqueta LB

# Evidencia de por que se unen (mismos escenarios con terminales separados; infactibles en la carga):
python scripts/6-vsp_asignacion_buses.py --modo ruta    --asignacion data-processed/rutas_cluster_c1b.csv --etiqueta E0_sep
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --etiqueta E1_sep

# Variantes con C2 (propuesta, fuera de la escalera):
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c2.csv --unir-electroterminales --etiqueta E1_C2
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c2.csv --etiqueta E1_C2_sep

# Sensibilidad sobre E1 (no escribe jornadas):
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --sin-jornadas --factor-desvio 1.2  --etiqueta E1_f1.2
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --sin-jornadas --factor-desvio 1.35 --etiqueta E1_f1.35
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --sin-jornadas --factor-desvio 1.5  --etiqueta E1_f1.5
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --sin-jornadas --layover 0  --etiqueta E1_l0
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1b.csv --unir-electroterminales --sin-jornadas --layover 10 --etiqueta E1_l10

python scripts/7-comparar_escenarios.py
```

Cifras de referencia (04/10): **E0 8.654 · E1 7.366 · LB 7.055** buses; costo de operación 2,31 / 1,97 / 1,87 millones de
USD/día. Separados: E0_sep 8.654 · E1_sep 7.460. Variantes C2: E1_C2 7.366 · E1_C2_sep 7.462. Sensibilidad de E1: factor
1,2 / 1,35 / 1,5 → 7.294 / 7.401 / 7.441; layover 0 / 10 min → 7.161 / 7.810. Cada corrida verifica cobertura exacta
(cada `expedicion_id` en una sola jornada) y retorno al electroterminal (en LB solo lo cuenta: 4.192 de 7.055 jornadas
no vuelven, por eso es cota inferior). `7-` falla si no se cumple `E0 >= E1 >= LB >= 6.539`, si E0 y E1 no se corrieron
con C1b y los electroterminales 3 y 5 unidos, o si unir cambia E0 (en modo `ruta` no debe cambiar el VSP).

Output: `data-processed/jornadas_{E0,E1,LB,E0_sep,E1_sep,E1_C2,E1_C2_sep}.csv` y
`results/etapa2_vsp/{reporte.md, tablas/, graficos/}` (el `reporte.md` termina con un índice de archivos).

### `scripts/10-carga_reactiva.py` (Etapa 3, carga reactiva) — requiere las jornadas de la Etapa 2

```
python scripts/10-carga_reactiva.py --escenario E0 --jornadas data-processed/jornadas_E0_subset.csv --soc 0.7 --traza 1   # checkpoint chico
python scripts/10-carga_reactiva.py --escenario E0 --cota-lp      # red completa, nivel 100% (~10 s; con la cota LP ~40 s)
python scripts/10-carga_reactiva.py --escenario E1 --cota-lp
python scripts/10-carga_reactiva.py --escenario E0_sep            # y E1_sep, E1_C2, E1_C2_sep
python scripts/10-carga_reactiva.py --escenario E1 --soc 0.9      # otro nivel
```

No usa Gurobi (la cota LP usa scipy/HiGHS). El terminal unido se lee de la columna `unir` del resumen del VSP. El
checkpoint chico necesita antes `python scripts/6-vsp_asignacion_buses.py --modo ruta --asignacion
data-processed/rutas_cluster_c1b.csv --subset 101 102 301 --etiqueta E0`; con `--traza <jornada>` imprime el SOC paso a
paso para revisarlo a mano (borrar después los archivos `*_subset*`). Antes de simular, el script reconstruye cada
jornada sin cargas y exige que calce con el VSP (kWh y espera total); después verifica cobertura, SOC entre el mínimo y
el tope, ocupación ≤ puestos y balance de energía por jornada. Los ciclos no cumplidos se cubren con **buses de reserva**
(250 USD/día) incluidos en `costo_total_usd`; una solución es **factible** si no tiene déficit de energía y todo atraso
es < 24 h. `--cota-lp` calcula el máximo de energía nocturna que cabe en las ventanas de los buses con carga perfecta.

Cifras de referencia (nivel 100%, 04/10):

| | E0 | E1 | E0_sep | E1_sep | E1_C2 | E1_C2_sep |
|---|---|---|---|---|---|---|
| Buses tras la carga | 11.259 | 10.295 | 11.259 | 10.415 | 10.258 | 10.343 |
| Ciclos no cumplidos = reservas | 1.988 | 2.207 | 2.357 | 2.518 | 2.204 | 2.363 |
| Déficit de energía (MWh) | 0 | 0 | 48,2 | 44,1 | 0 | 21,3 |
| Cota LP | 89,5% | 84,0% | 89,4% | 84,4% | 84,0% | 84,3% |
| Costo total con reservas (USD/día) | 3.958.063 | 3.751.250 | 4.036.222 | 3.849.470 | 3.740.069 | 3.799.556 |
| Factible | sí | sí | no | no | sí | no |

Ver `01_metodologia.md` (Etapa 3) para la lectura. Output: `results/etapa3_carga_reactiva/{tablas/,graficos/,
reporte_<esc>_soc<nivel>.md}`. Los nombres llevan el nivel (`_soc100`) para que el barrido no pise archivos;
`tablas/resumen_carga.csv` tiene una fila por escenario y nivel. `--solo-resumen` escribe solo esa fila.

### `scripts/13-barrido_niveles.py` (barrido de niveles de batería) — requiere las jornadas de E0 y E1

```
python scripts/13-barrido_niveles.py     # ~2 min si las filas ya estan simuladas; ~35 min desde cero (la cota LP crece al bajar el nivel)
```

Aplica por código la regla corregida de `02`, B6 (la condición cíclica como restricción): grilla 100/90/80/70/65/60/55/50%
(piso físico 50%), solo soluciones factibles, buses de reserva, dos familias (con y sin reservas), mínimo costo total,
empate de 0,5% a favor del nivel más alto, robustez en E0, y la cota LP (solo hasta 65%: a menor nivel ya alcanza
100%). Cada nivel se simula con `10-carga_reactiva.py --solo-resumen` (reutiliza las filas ya simuladas); al final se
corre completo el nivel elegido. Referencia (04/10): E1 elige **100%** (3.751.250 USD/día con 2.207 reservas; 90%
+5,9%, 80% +8,5%, 70% +17,9%, 65% +26,3%, 60% +38,8%, 55% +52,8%; 50% infactible); E0 también. Ningún nivel cumple el
ciclo sin reservas.

Output: `results/etapa3_carga_reactiva/barrido/{reporte_barrido.md, tablas/{barrido_niveles,decision_barrido,
evidencia_terminales_separados}.csv, graficos/{barrido_costo_total,barrido_ciclos_y_cota,barrido_robustez}.png}`.

### `scripts/11-milp_carga.py` (Etapa 4, MILP de carga en instancia reducida) — requiere las jornadas de E1 y los resultados de la Etapa 3

```
python scripts/11-milp_carga.py --n 10 --detalle --sin-salidas   # checkpoint chico (~10 s): imprime bus por bus la ventana, la energía y los bloques de la reactiva y del MILP
python scripts/11-milp_carga.py                                  # escalera N = 10 / 30 / 50 / 100 / 200 / 400 (cada una hasta 600 s: ~50 min en total)
python scripts/11-milp_carga.py --n 200 --semilla 7              # otra semilla (variabilidad)
python scripts/11-milp_carga.py --regenerar                      # gráficos y reporte desde los CSV, sin resolver
```

Gurobi con licencia (13.0). Importa el simulador de `10-carga_reactiva.py` sin modificarlo. En cada instancia verifica con `assert`: la
reconstrucción de las jornadas contra el VSP, la solución del MILP (energía exacta por bus, ≤ 45 kWh por bloque, puestos, fuera de ventana solo con
reserva, costo recalculado coherente con Gurobi) y **MILP ≤ reactiva en bloques**; marca la instancia como no trivial si los puestos están saturados en
≥ 10% de los bloques. También verifica que el programa del MILP se ejecuta al minuto sin exceder puestos y que la cota de reservas ≤ reservas del MILP. Los límites de tiempo no son deterministas: las brechas y los costos del MILP pueden variar algo entre corridas.
Cifras de referencia (05/10, semilla 24): costo de la carga simulador → MILP (USD/día en la instancia) 283 → 253 (N=10, óptimo en 2,6 s), 2.115 → 1.612 (30), 4.947 → 4.199 (50),
9.519 → 8.507 (100), 19.532 → 17.294 (200), 41.573 → 35.608 (400); reservas 4→2, 12→9, 23→19, 48→39, 107→82 (cota de reservas 1 / 8 / 15 / 32 / 68); brecha 1,4 / 2,0 / 2,7 / 1,9 / 8,6%
(solo N=10 certifica el 1%). N=20 se descarta por inválida (1 puesto, carga > 100%). 

Output: `results/etapa4_milp_carga/{reporte.md, tablas/{instancias,comparacion_reactiva_milp,tiempos_resolucion,representatividad,energia_por_tarifa,
ocupacion_N<n>,programa_reactiva_N<n>,programa_milp_N<n>}.csv, graficos/{ocupacion_reactiva_vs_milp_N<n>,energia_por_tarifa,costo_reactiva_vs_milp,brecha_vs_N}.png}`.

### `scripts/9-calibracion_deadhead.py` (calibración del factor de desvío) — independiente de las etapas

```
python scripts/9-calibracion_deadhead.py --shapes 101I 101R 210I   # checkpoint chico (imprime una ventana para revisar a mano)
python scripts/9-calibracion_deadhead.py                           # los 839 trazados (~5 s)
```

Mide, en cada trazado GTFS, el cociente `recorrido / línea recta` entre pares de puntos separados por
1, 3, 5, 10 y 15 km de recorrido. Requiere `data-filtrado/{shapes_bus,shape_distances_bus}.csv` y
`data-processed/rutas_cluster_c2.csv` (para la escala del pullout/pullin). Referencia (03/10): medianas
**1,04 / 1,22 / 1,29 / 1,35 / 1,38** para 1 / 3 / 5 / 10 / 15 km; pullout/pullin de C2 con mediana de
~12 km ponderada por buses; largo calculado vs `shape_distances_bus.csv` con error máximo 0,29%.

Output: `results/etapa0_calibracion_deadhead/{reporte.md, tablas/{factor_por_escala,factor_por_trazado,
escala_deadhead_pullout_pullin}.csv, graficos/{factor_por_escala,ejemplo_trazado}.png}`. Justificación
para el informe: `docs/justificaciones/02_factor_desvio_deadhead.md`.

### `scripts/8-clustering_comparacion.py` (cierre de la Etapa 1) — requiere 4 y 5 ya corridos en la red completa

```
python scripts/8-clustering_comparacion.py     # ~35-40 s (la mayor parte es leer chile.gpkg y dibujar mapas)
```

Falla con un mensaje claro si falta alguna de las 3 asignaciones (`rutas_cluster_{c1a,c1b,c2}.csv`) o
alguna tabla del script 5. Valida que C2 respete la capacidad y que el mapa de diferencias C1b → C2 calce
con la tabla de comparación. Genera la tabla ancha por
ruta y **10 mapas** (uno por estrategia ×3, uno por electroterminal ×5, paraderos, diferencias). Referencia:
C1a vs C1b cambia 41 de 417 rutas (83.843 → 83.271 USD/día de pullout/pullin); C1b vs C2 cambia 5.

Output: `data-processed/rutas_clustering_completo.csv`, `results/etapa1_clustering/{reporte.md,
tablas/{resumen_por_terminal,comparacion_estrategias,rutas_que_cambian}.csv,
graficos/rutas_por_terminal.png, mapas/*.png}`. El `reporte.md` termina con un índice de todos los
archivos de la carpeta.

## 5. Reproducir todo de una vez (copiar y pegar)

Asumiendo el punto de partida (a) de la sección 2 (repo recién clonado, `data-filtrado/` completo):

```
python scripts/3-preprocesamiento_expediciones.py
python scripts/4-clustering_c1.py
python scripts/5-clustering_c2.py
python scripts/8-clustering_comparacion.py
python scripts/9-calibracion_deadhead.py
```

Tiempo total estimado: ~1,5 minutos. La Etapa 2 (cinco escenarios y cinco sensibilidades, ~10 minutos) se corre
aparte con los comandos de la sección de `6-` y `7-`.

## 6. Troubleshooting

- **Un `assert` salta con un mensaje en español.** Léelo completo: dice exactamente qué se esperaba y
  qué se encontró. Antes de reportar "el script está roto", confirma que corriste los pasos previos
  en el orden de la sección 3.
- **Abrir un CSV de `data-filtrado/` o `data-processed/` y ver todo en una sola columna.** Esos CSV
  usan `;` como separador (no `,`), por configuración regional Chile/Latam de Excel — ver
  `docs/decisiones_datos.md` sección 3.5. Con pandas: `pd.read_csv(path, sep=";")`.
- **`GurobiError: No Gurobi license found`.** Falta activar una licencia Gurobi en esa máquina — ver
  sección 1. Solo lo usa `5-clustering_c2.py`.
- **`8-clustering_comparacion.py` falla al leer `chile.gpkg` o los mapas salen sin fondo de comunas.**
  Falta `data-alumnos/chile.gpkg` (no viaja en el repo por tamaño, ver sección 2b) o falta
  `geopandas`/`shapely`. El resto del script corre igual si solo falla la parte de mapas.
- **Nombres de comuna con caracteres raros si los llegas a imprimir.** La capa `gis_osm_adminareas_a_free`
  de `chile.gpkg` viene con encoding latin-1 ("Peñaflor" sale mal). Los mapas del script 8 no
  imprimen nombres de comuna (solo bordes), así que no afecta a los outputs actuales.
- **Una ventana de matplotlib no aparece / no hace falta que aparezca.** Todos los scripts fijan
  `matplotlib.use("Agg")` al principio: generan los PNG directamente a disco. Es esperado.
- **`FileNotFoundError` apuntando a `data-processed/rutas_resumen.csv`.** Falta correr
  `3-preprocesamiento_expediciones.py` primero (genera esa tabla junto con `expediciones.csv`).
- **`SystemExit` en `8-clustering_comparacion.py` pidiendo correr 4 y 5 antes.** Exactamente eso —
  y sobre la red completa (417 rutas), no un checkpoint chico con `--rutas`.

## 7. Referencias

- Metodología completa: [`01_metodologia.md`](01_metodologia.md). Plan de lo que falta: [`05_plan_entrega2.md`](05_plan_entrega2.md).
- Decisiones de filtrado de datos (incluye el detalle del separador `;`): [`../decisiones_datos.md`](../decisiones_datos.md).
- Supuestos y decisiones (incluye las respuestas del profesor): [`02_supuestos_y_decisiones.md`](02_supuestos_y_decisiones.md).
