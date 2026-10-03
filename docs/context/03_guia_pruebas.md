# Guía de pruebas — cómo correr y verificar el pipeline vigente

> Para cualquiera que clone el repo (equipo, ayudante, profesor) y quiera confirmar que el código
> corre y reproduce los resultados documentados en [`01_metodologia.md`](01_metodologia.md).
> No asume que hayas leído el resto de `docs/context/`, aunque se recomienda.
>
> Cubre el pipeline **vigente**: Etapa 0 (preprocesamiento) y Etapa 1 (clustering de rutas a
> electroterminales, bajo ciclo diario). La Etapa 2 (`scripts/6-vsp_asignacion_buses.py`,
> `7-comparar_escenarios.py`) existe y funciona, pero se ajusta y corre en el Bloque C del plan: no
> forma parte de esta guía todavía. Ver `01_metodologia.md` (Etapa 2) y `05_plan_entrega2.md`.
>
> Última edición: **03/10/2026** (corrección: el nivel cíclico base pasa a 100%, dato del curso; ver `04_bitacora.md`).
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
ningún electroterminal supere el 100% y que se reasignen rutas (3 de 20). En la red completa
(referencia, regenerada el 03/10):

- **C2 coincide exactamente con C1b** (0 rutas distintas): con θ = 1 la restricción agregada diaria
  no está activa. Uso: Vespucio Norte 30,9% · El Conquistador 69,8% · **Los Espinos 89,9%** · La Reina
  68,1% · Santa Rosa 58,6%. `h_r` total = 10.464 horas-cargador/día (1.884 MWh) de 16.800 disponibles.
- **Barrido de θ** (capacidad separada): 0 rutas movidas con θ = 1 y 0,9; 11 con 0,8; 21 con 0,7;
  infactible con 0,6. Con Los Espinos + Santa Rosa combinados: 0 rutas movidas hasta θ = 0,8; 9 con 0,7;
  infactible con 0,6.
- **Evidencia "sin recuperación" vs "con recuperación"** (proxy por ruta, sin deadhead; mismo nivel de
  batería en ambos lados). Con recuperación (ciclo): 10.464 horas-cargador (62,3% de la capacidad),
  igual para todo nivel. Sin recuperación: 108 h (0,6%) al 100%, 380 h (2,3%) al 90%, 1.086 h (6,5%) al
  80% y 2.201 h (13,1%) al 70%. No genera ninguna asignación.

Output: `data-processed/rutas_cluster_c2.csv`,
`results/etapa1_clustering/tablas/{capacidad_por_terminal,capacidad_sin_vs_con_recuperacion,barrido_theta}.csv`,
`results/etapa1_clustering/graficos/{capacidad_ciclo,capacidad_sin_vs_con_recuperacion,barrido_theta}.png`.

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
alguna tabla del script 5. Valida que C2 coincida exactamente con C1b (si no, la restricción de
capacidad se activó y hay que explicarlo antes de confiar en el resultado). Genera la tabla ancha por
ruta y **10 mapas** (uno por estrategia ×3, uno por electroterminal ×5, paraderos, diferencias). Referencia:
C1a vs C1b cambia 41 de 417 rutas; costo aproximado de pullout/pullin 83.843 → 83.271 USD/día.

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

Tiempo total estimado: ~1,5 minutos.

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
