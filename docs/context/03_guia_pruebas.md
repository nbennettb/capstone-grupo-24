# Guía de pruebas — cómo correr y verificar todo el pipeline

> Para cualquiera que clone el repo (equipo, ayudante, profesor) y quiera confirmar que el código corre y reproduce los resultados documentados en [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md). No asume que hayas leído el resto de `docs/context/`, aunque se recomienda.
>
> Última edición: **28/09/2026**.

---

## 1. Prerrequisitos

Python 3 con estas librerías:

```
pandas  numpy  scipy  matplotlib  tabulate  gurobipy
```

Verificación rápida (no debería imprimir nada si todo está instalado):

```
python -c "import pandas, numpy, scipy, matplotlib, tabulate, gurobipy; print('OK')"
```

`gurobipy` además necesita una **licencia Gurobi válida** activada en la máquina (académica o comercial). Si al correr cualquier script aparece un error tipo `GurobiError: No Gurobi license found`, hay que activar una licencia (las licencias académicas son gratuitas en [gurobi.com](https://www.gurobi.com), requieren correo institucional) antes de seguir.

No hace falta `geopandas`, `osmnx` ni `networkx` para nada de este pipeline (solo los usan `data-alumnos/gp.py` y `a.py`, que son exploración suelta, no parte del pipeline).

## 2. Dos puntos de partida posibles

**(a) Repo recién clonado — el camino normal.** `data-filtrado/` ya viene completo en el repo (ver `docs/context/00_contexto_entrega1.md` sobre qué contiene). Se puede saltar directo a la sección 4 (Etapa 0 en adelante).

**(b) Regenerar `data-filtrado/` desde los datos crudos del curso.** Solo hace falta si quieres verificar el filtrado GTFS→buses desde cero, o si cambiaste algo en `scripts/1-...`/`scripts/2-...`. Requiere tener `data-alumnos/gtfs/stop_times.txt` y `shapes.txt` (no están en el repo por tamaño — los entrega el curso, cada integrante del equipo ya los debería tener de haberlos descargado para el Informe 1). Con eso:

```
python scripts/1-filtro_datos_buses.py
python scripts/2-filtro_tipo_dia.py
```

Esto sobrescribe `data-filtrado/*.csv`. Después seguir con la sección 4 igual.

## 3. Orden de ejecución (importante: no es un simple 1→2→…→7)

```
1 (filtro buses) ──► 2 (filtro dia L) ──► 3 (preprocesamiento, Etapa 0)
                                                  │
                     ┌────────────────────────────┼─────────────────────────┐
                     ▼                             ▼                        │
        6 --modo ruta (Etapa 2, caso base)   6 --modo libre (Etapa 2, C0)   │
                     │                                                      │
                     ▼                                                      │
      5 (clustering C2, Etapa 1) ◄── lee jornadas_ruta.csv                  │
                     ▲                                                      │
      4 (clustering C1, Etapa 1) ───────────────────────────────────────────┘
                     │
                     ▼
   6 --modo cluster --asignacion rutas_cluster_c1.csv --etiqueta cluster_c1
   6 --modo cluster --asignacion rutas_cluster_c2.csv --etiqueta cluster_c2
                     │
                     ▼
              7 (comparación final)
```

Los dos puntos no obvios:
- **`6 --modo ruta` debe correrse ANTES que `5-clustering_milp.py`**: C2 lee `data-processed/jornadas_ruta.csv` para saber cuántos buses y cuánta energía diaria demanda cada ruta (ver docstring de `5-clustering_milp.py`).
- **`7-comparar_escenarios.py` necesita los 4 escenarios ya en `results/06_vsp/resumen_escenarios.csv`**, con esas etiquetas exactas: `ruta`, `libre`, `cluster_c1`, `cluster_c2`. Si corres un escenario dos veces, queda una fila duplicada — filtra a la última corrida de cada etiqueta antes de confiar en el archivo, o bórrala a mano.

`4-clustering_nearest.py` (C1) no depende de nada más que `data-processed/expediciones.csv` (Etapa 0).

## 4. Por script: checkpoint chico, corrida completa, y qué esperar

Todos los scripts tienen **chequeos de sanidad automáticos** (`assert` con mensajes en español). Si uno de estos salta, no es "un bug del script en sí" — es una señal real de que algo en los datos, los parámetros o la lógica cambió, y hay que investigarlo antes de confiar en el resultado. Ver la sección 6 para más sobre esto.

### `scripts/3-preprocesamiento_expediciones.py` (Etapa 0)

```
python scripts/3-preprocesamiento_expediciones.py --rutas 101      # checkpoint chico (~5 s)
python scripts/3-preprocesamiento_expediciones.py                  # red completa (~10-20 s)
```

Checkpoint: 171 expediciones, 4 paraderos terminales. Red completa (cifras de referencia, validadas el 28/09): **64.502 expediciones**, **417 rutas**, **641 paraderos terminales**, **concurrencia máxima 6.539 a las 8:00**. El propio script compara contra estas cifras e imprime `[OK]` o un aviso si difieren.

Output: `data-processed/expediciones.csv`, `data-processed/terminales.csv`, `results/03_preprocesamiento/` (reporte + 2 gráficos).

### `scripts/6-vsp_asignacion_buses.py --modo ruta` y `--modo libre` (Etapa 2, caso base y cota inferior)

```
python scripts/6-vsp_asignacion_buses.py --modo ruta  --subset 101 102 301   # checkpoint chico
python scripts/6-vsp_asignacion_buses.py --modo libre --subset 101 102 301   # checkpoint chico

python scripts/6-vsp_asignacion_buses.py --modo ruta     # red completa (~5-10 s)
python scripts/6-vsp_asignacion_buses.py --modo libre    # red completa (~40-90 s)
```

Cifras de referencia (red completa): **`ruta` → 8.654 buses**, costo total ≈ 2.985.009 USD. **`libre` → 7.055 buses**, costo total ≈ 2.546.383 USD. `libre` tarda bastante más porque el interlining libre genera muchos más arcos candidatos — es esperable, no un cuelgue.

Output: `data-processed/jornadas_{ruta,libre}.csv`, `results/06_vsp/graficos_{ruta,libre}.png`, y una fila nueva en `results/06_vsp/resumen_escenarios.csv` por cada corrida.

### `scripts/4-clustering_nearest.py` (Etapa 1, C1)

```
python scripts/4-clustering_nearest.py --muestra 20 --semilla 42   # checkpoint chico, reproducible
python scripts/4-clustering_nearest.py                             # red completa (~1-2 s)
```

Red completa: las 417 rutas quedan repartidas entre los 5 electroterminales (ninguno debería quedar en 0). Referencia del 28/09: entre 59 y 113 rutas por electroterminal.

Output: `data-processed/rutas_cluster_c1.csv`, `results/04_clustering_c1/`.

### `scripts/5-clustering_milp.py` (Etapa 1, C2) — requiere haber corrido `6 --modo ruta` antes

```
# Checkpoint de reactividad: con capacidad muy apretada, el modelo debe reasignar rutas
python scripts/5-clustering_milp.py --rutas 203N 203c 204N 211c 301c 542 546e B08 B32 B35 D11 E13 F06 F11 F16 F25 G05 G37 G43 J06 --theta 0.05

python scripts/5-clustering_milp.py --theta 1.0    # red completa (~2-5 s)
```

En el checkpoint, revisa que la salida "Uso de capacidad por electroterminal" muestre que ningún electroterminal supera su capacidad (el script lo verifica solo) y que la carga se movió lejos del que se apretó. En la red completa (referencia 28/09): **Los Espinos queda al ~99,5%** de su capacidad estimada — es un resultado real, no un error, y vale la pena mostrarlo en la reunión.

Output: `data-processed/rutas_cluster_c2.csv`, `results/05_clustering_c2/`.

### `scripts/6-vsp_asignacion_buses.py --modo cluster` (Etapa 2 por electroterminal)

```
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1.csv --etiqueta cluster_c1
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c2.csv --etiqueta cluster_c2
```

Cifras de referencia: **`cluster_c1` → 7.456 buses**, **`cluster_c2` → 7.454 buses** — ambos deberían quedar entre el resultado de `ruta` (8.654) y `libre` (7.055).

### `scripts/7-comparar_escenarios.py` (comparación final)

```
python scripts/7-comparar_escenarios.py
```

Falla con un mensaje claro si falta algún escenario en `resumen_escenarios.csv`. Si los 4 están, valida solo que `ruta ≥ cluster ≥ libre ≥ 6.539` e imprime la tabla de "precio del clustering". Output: `results/06_vsp/comparacion_escenarios.png` (el gráfico para la reunión) y `precio_del_clustering.csv`.

## 5. Reproducir todo de una vez (copiar y pegar)

Asumiendo el punto de partida (a) de la sección 2 (repo recién clonado, `data-filtrado/` ya viene completo):

```
python scripts/3-preprocesamiento_expediciones.py
python scripts/6-vsp_asignacion_buses.py --modo ruta
python scripts/6-vsp_asignacion_buses.py --modo libre
python scripts/4-clustering_nearest.py
python scripts/5-clustering_milp.py --theta 1.0
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c1.csv --etiqueta cluster_c1
python scripts/6-vsp_asignacion_buses.py --modo cluster --asignacion data-processed/rutas_cluster_c2.csv --etiqueta cluster_c2
python scripts/7-comparar_escenarios.py
```

Tiempo total estimado: 2-3 minutos. Al final, `results/06_vsp/comparacion_escenarios.png` debería verse igual al ya commiteado en el repo.

## 6. Troubleshooting

- **Un `assert` salta con un mensaje en español.** Léelo completo: están escritos para decir exactamente qué se esperaba y qué se encontró (p. ej. cobertura de expediciones, capacidad de electroterminal excedida, orden de escenarios). Antes de reportar "el script está roto", confirma que corriste los pasos previos en el orden de la sección 3 y con las mismas `--etiqueta`.
- **Abrir un CSV de `data-filtrado/` o `data-processed/` y ver todo en una sola columna.** Esos CSV usan `;` como separador (no `,`), por configuración regional Chile/Latam de Excel — ver `docs/decisiones_datos.md` sección 3.5. Con pandas: `pd.read_csv(path, sep=";")`.
- **`GurobiError: No Gurobi license found` (o similar).** Falta activar una licencia Gurobi en esa máquina — ver sección 1.
- **Una ventana de matplotlib no aparece / no hace falta que aparezca.** Todos los scripts fijan `matplotlib.use("Agg")` al principio: generan los PNG directamente a disco, no abren ninguna ventana. Es esperado.
- **`FileNotFoundError` apuntando a `data-processed/jornadas_ruta.csv` al correr `5-clustering_milp.py`.** Te saltaste el orden de la sección 3 — corre primero `6-vsp_asignacion_buses.py --modo ruta`.
- **Los tiempos de corrida son mucho más largos que los de referencia.** Puede ser una máquina más lenta o sin suficiente RAM libre; no es necesariamente un error. Si un script no termina en varios minutos (la referencia más lenta, `--modo libre` en la red completa, es de ~90 s), revisar que Gurobi esté usando una licencia con el tamaño de problema adecuado (las licencias académicas completas no tienen límite de tamaño; una licencia limitada sí podría degradar el rendimiento o rechazar el modelo).

## 7. Referencias

- Metodología completa y resultados ya validados: [`01_metodologia_y_avance.md`](01_metodologia_y_avance.md).
- Decisiones de filtrado de datos (incluye el detalle del separador `;`): [`../decisiones_datos.md`](../decisiones_datos.md).
