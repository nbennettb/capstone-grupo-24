# Guía de pruebas — cómo correr y verificar el pipeline vigente

> Para cualquiera que clone el repo (equipo, ayudante, profesor) y quiera confirmar que el código
> corre y reproduce los resultados documentados en [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md).
> No asume que hayas leído el resto de `docs/context/`, aunque se recomienda.
>
> Cubre el pipeline **vigente**: Etapa 0 (preprocesamiento) y Etapa 1 (clustering de rutas a
> electroterminales). La Etapa 2 (`scripts/6-vsp_asignacion_buses.py`, `7-comparar_escenarios.py`)
> existe y funciona, pero está pausada hasta validar supuestos con el profesor — no forma parte de
> esta guía. Ver `01_metodologia_y_avance.md` sección 1.
>
> Última edición: **30/09/2026**.

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
red completa (417 rutas): lee las cuatro asignaciones que generan.

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
python scripts/5-clustering_c2.py --rutas 203N 203c 204N 211c 301c 542 546e B08 B32 B35 D11 E13 F06 F11 F16 F25 G05 G37 G43 J06 --carga ciclo --theta 0.05

python scripts/5-clustering_c2.py    # red completa (~40-45 s: corre 2 supuestos + grilla + barrido de theta)
```

En el checkpoint, revisa que "Uso de capacidad por electroterminal" no supere el 100% en ningún
electroterminal y que se reasignen rutas. En la red completa (referencia 30/09):

- **Caso base (SOC inicial 100%):** el MILP con capacidad coincide **exactamente** con C1b (0 rutas
  distintas) — la capacidad no está activa. Uso máximo: 1,2% (Los Espinos).
- **Escenario cíclico** (recargar todo lo consumido): uso máximo 89,9% (Los Espinos). Infactible con
  menos de ~18h/día de ventana de carga.
- **Barrido de θ** (cíclico, H=24h): empieza a mover rutas en θ≈0,8, infactible en θ=0,6.

Output: `data-processed/rutas_cluster_c2.csv`, `rutas_cluster_c2_ciclo.csv`,
`results/etapa1_clustering/tablas/{capacidad_dos_supuestos,barrido_theta}.csv`,
`results/etapa1_clustering/graficos/{capacidad,barrido_theta}.png`.

### `scripts/8-clustering_comparacion.py` (cierre de la Etapa 1) — requiere 4 y 5 ya corridos en la red completa

```
python scripts/8-clustering_comparacion.py     # ~35-40 s (la mayor parte es leer chile.gpkg y dibujar mapas)
```

Falla con un mensaje claro si falta alguna de las 4 asignaciones (`rutas_cluster_{c1a,c1b,c2,c2_ciclo}.csv`).
Valida que C2 caso base coincida exactamente con C1b (si no, hay un error real que investigar antes de
confiar en el resultado). Genera la tabla ancha por ruta y **11 mapas** (uno por estrategia ×4, uno por
electroterminal ×5, paraderos, diferencias).

Output: `data-processed/rutas_clustering_completo.csv`, `results/etapa1_clustering/{reporte.md,
tablas/{resumen_por_terminal,comparacion_estrategias,rutas_que_cambian}.csv,
graficos/rutas_por_terminal.png, mapas/*.png}`.

## 5. Reproducir todo de una vez (copiar y pegar)

Asumiendo el punto de partida (a) de la sección 2 (repo recién clonado, `data-filtrado/` completo):

```
python scripts/3-preprocesamiento_expediciones.py
python scripts/4-clustering_c1.py
python scripts/5-clustering_c2.py
python scripts/8-clustering_comparacion.py
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

- Metodología completa y resultados ya validados: [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md).
- Decisiones de filtrado de datos (incluye el detalle del separador `;`): [`../decisiones_datos.md`](../decisiones_datos.md).
- Preguntas y supuestos pendientes de validar con el profesor/ayudante: [`02_pendientes_profesor.md`](02_pendientes_profesor.md).
