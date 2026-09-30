```
└── 📁Proyecto Capstone
    └── 📁archivos_analisis_datos
        ├── buses_por_hora_curva.png
        ├── buses_por_hora_dia_laboral.xlsx
        ├── costo_energia_por_periodo.png
        ├── energia_top5_rutas_demandadas.xlsx
        ├── expediciones_por_electroterminal.jpg
        ├── grafico_tipo_dia.png
        ├── mapa_rutas_electroterminales.png
        ├── resumen_por_tipo_dia.xlsx
    └── 📁chapters
        ├── abstract.tex
        ├── acknowledgments.tex
        ├── appendix1.tex
        ├── appendix2.tex
        ├── chapter1.tex
        ├── chapter2.tex
        ├── conclusions.tex
        ├── introduction.tex
        ├── resumen.tex
        ├── use of ai.tex
    └── 📁data-alumnos
        └── 📁gtfs
            ├── agency.txt
            ├── calendar_dates.txt
            ├── calendar.txt
            ├── feed_info.txt
            ├── frequencies.txt
            ├── levels.txt
            ├── pathways.txt
            ├── routes.txt
            ├── shapes.txt          (no viaja en el repo, lo entrega el curso)
            ├── stop_times.txt      (no viaja en el repo, lo entrega el curso)
            ├── stops.txt
            ├── trips.txt
        ├── a.py
        ├── charger_capacity.csv
        ├── charging_activities.csv
        ├── chile.gpkg              (no viaja en el repo por tamaño, 1.3 GB)
        ├── depots.csv
        ├── electricity_prices.csv
        ├── gp.py
        ├── main.py
        ├── mapa_electroterminales_rm.png
        ├── mapa_red.png
        ├── parameters.csv
        ├── parametros_descripcion.csv
        ├── shape_distances.csv
        ├── vehicles.csv
    └── 📁data-filtrado
        ├── charger_capacity.csv
        ├── charging_activities.csv
        ├── depots.csv
        ├── electricity_prices.csv
        ├── frequencies_bus.csv
        ├── frequencies_dia_L.csv
        ├── parameters.csv
        ├── parametros_descripcion.csv
        ├── routes_bus.csv
        ├── shape_distances_bus.csv
        ├── shapes_bus.csv
        ├── stop_times_bus.csv
        ├── stop_times_dia_L.csv
        ├── stops_bus.csv
        ├── trips_bus.csv
        ├── trips_dia_L.csv
        ├── vehicles.csv
    └── 📁data-processed
        ├── expediciones.csv                  (Etapa 0, 64.502 filas)
        ├── rutas_cluster_c1a.csv              (Etapa 1, C1a: centroide)
        ├── rutas_cluster_c1b.csv              (Etapa 1, C1b: terminales reales)
        ├── rutas_cluster_c2.csv               (Etapa 1, C2: caso base SOC 100%)
        ├── rutas_cluster_c2_ciclo.csv         (Etapa 1, C2: escenario ciclico)
        ├── rutas_clustering_completo.csv      (Etapa 1, tabla ancha por ruta)
        ├── rutas_ida_vuelta.csv               (Etapa 0, 300 rutas)
        ├── rutas_resumen.csv                  (Etapa 0, 417 rutas)
        ├── terminales.csv                     (Etapa 0, 641 paraderos)
        ├── terminales_por_ruta.csv            (Etapa 0, 1.356 pares)
    └── 📁docs
        └── 📁context
            ├── 00_contexto_entrega1.md
            ├── 01_metodologia_y_avance.md
            ├── 02_pendientes_profesor.md
            ├── 03_guia_pruebas.md
            ├── 04_preguntas_reunion.md
            ├── 05_cierre_ronda.md
        └── 📁Informe 1
            └── 📁chapters
                ├── anexo1_ia.tex
                ├── anexo2_datos.tex
                ├── chapter1.tex
                ├── chapter2.tex
                ├── conclusions.tex
                ├── introduction.tex
                ├── resumen.tex
            └── 📁figures
                ├── buses_por_hora_curva.png
                ├── costo_energia_por_periodo.png
                ├── expediciones_por_electroterminal.jpg
                ├── grafico_tipo_dia.png
                ├── LogoUC.pdf
                ├── LogoUC.ps
                ├── mapa_rutas_electroterminales.png
            └── 📁firmas
                ├── agustin_irarrazaval.png
                ├── alonso_muelas.png
                ├── antonio_defrutos.png
                ├── claudio_hasbun.png
                ├── joaquin_jimenez.png
                ├── nicolas_bennett.png
                ├── README.md
            ├── apacite.bst
            ├── apacite.sty
            ├── pucthesis.cls
            ├── README.md
            ├── Thesis.bib
            ├── Thesis.tex
        ├── decisiones_datos.md
        ├── Estructura_carpeta_proyecto.md
        ├── Informe 1.docx
        ├── Lineamientos Entrega 1 2026-2.md
        ├── Lineamientos Entrega 2 2026-2.md
        ├── P7 Planificación de la operación de buses eléctricos en la Región Metropolitana-1.md
        ├── PLANIFICACION_DE_LA_OPERACION_DE_LOS_BUSES_ELECTRICOS_EN_LA_RED_METROPOLITANA_DE_MOVILIDAD_DE_SANTIAGO_GRUPO_24.pdf
        ├── Presentacion 1 capstone.pdf
        ├── Presentacion_1_capstone.txt
        ├── Propuesta_metodologia_reunion.md
        ├── Propuesta_metodologia_reunion.pdf
        ├── resumen_exploracion_inicial_incompleta_datos.txt
    └── 📁figures
        ├── LogoUC.pdf
        ├── LogoUC.ps
        ├── selfie_monkey.jpg
    └── 📁firmas
        ├── 1789171072909.jpg
        ├── 1789171072921.jpg
        ├── 1789171072932.jpg
        ├── 1789171072942.jpg
    └── 📁results
        └── 📁etapa0_preprocesamiento
            └── 📁graficos
                ├── buses_por_hora.png
                ├── duracion_y_distancia.png
                ├── energia_por_expedicion.png
                ├── ida_vuelta_distancia.png
            ├── concurrencia_por_minuto.csv
            ├── conteos.csv
            ├── descartes.csv
            ├── distribucion_expediciones.csv
            ├── reporte.md
        └── 📁etapa1_clustering
            └── 📁graficos
                ├── barrido_theta.png
                ├── capacidad.png
                ├── distancias.png
                ├── rutas_por_terminal.png
            └── 📁mapas
                ├── mapa_c1a.png
                ├── mapa_c1b.png
                ├── mapa_c2.png
                ├── mapa_c2_ciclo.png
                ├── mapa_diferencias.png
                ├── mapa_paraderos_terminales.png
                ├── mapa_terminal_el_conquistador.png
                ├── mapa_terminal_la_reina.png
                ├── mapa_terminal_los_espinos.png
                ├── mapa_terminal_santa_rosa.png
                ├── mapa_terminal_vespucio_norte.png
            └── 📁tablas
                ├── barrido_theta.csv
                ├── capacidad_dos_supuestos.csv
                ├── comparacion_estrategias.csv
                ├── distancias_ruta_terminal.csv
                ├── resumen_por_terminal.csv
                ├── rutas_que_cambian.csv
            ├── reporte.md
    └── 📁scripts
        └── 📁common
            ├── __init__.py
            ├── clustering.py
            ├── geo.py
            ├── parametros.py
            ├── rutas.py
            ├── tiempo.py
        ├── 1-filtro_datos_buses.py
        ├── 2-filtro_tipo_dia.py
        ├── 3-preprocesamiento_expediciones.py          (Etapa 0)
        ├── 4-clustering_c1.py                          (Etapa 1, C1a + C1b)
        ├── 5-clustering_c2.py                          (Etapa 1, C2)
        ├── 6-vsp_asignacion_buses.py                   (Etapa 2 — pausada, no correr)
        ├── 7-comparar_escenarios.py                    (Etapa 2 — pausada, no correr)
        ├── 8-clustering_comparacion.py                 (cierre Etapa 1: comparación y mapas)
    ├── .gitignore
    ├── README.md
```

**Nota sobre `_ronda_anterior/`** (no aparece arriba, está en `.gitignore`): guarda los resultados de
la Etapa 2 de la ronda del 28/09 (`jornadas_*.csv`, `rutas_cluster_c1.csv`/`c2.csv` viejos, los
scripts `4-clustering_nearest.py`/`5-clustering_milp.py` que reemplazaron `4-clustering_c1.py` y
`5-clustering_c2.py`, y sus `results/`). Se conserva en disco por si se retoma la Etapa 2, pero no
viaja al repositorio.
