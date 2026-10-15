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
        ├── jornadas_E0.csv                    (Etapa 2, caso base: por línea, terminales unidos)
        ├── jornadas_E1.csv                    (Etapa 2, con interlining, terminales unidos)
        ├── jornadas_LB.csv                    (Etapa 2, cota inferior; no operacional)
        ├── jornadas_E0_sep.csv                (Etapa 2, E0 con terminales separados: evidencia)
        ├── jornadas_E1_sep.csv                (Etapa 2, E1 con terminales separados: evidencia)
        ├── jornadas_E1_C2.csv                 (Etapa 2, variante con C2, terminales unidos)
        ├── jornadas_E1_C2_sep.csv             (Etapa 2, variante con C2, terminales separados)
        ├── rutas_cluster_c1a.csv              (Etapa 1, C1a: centroide)
        ├── rutas_cluster_c1b.csv              (Etapa 1, C1b: terminales reales)
        ├── rutas_cluster_c2.csv               (Etapa 1, C2: bajo ciclo diario)
        ├── rutas_clustering_completo.csv      (Etapa 1, tabla ancha por ruta)
        ├── rutas_ida_vuelta.csv               (Etapa 0, 300 rutas)
        ├── rutas_resumen.csv                  (Etapa 0, 417 rutas)
        ├── terminales.csv                     (Etapa 0, 641 paraderos)
        ├── terminales_por_ruta.csv            (Etapa 0, 1.356 pares)
    └── 📁docs
        └── 📁context
            ├── 00_contexto_entrega1.md       (foto congelada del Informe 1)
            ├── 01_como_funciona.md           (el problema, el pipeline, caso base vs escenarios; una página)
            ├── 02_decisiones.md              (cada decisión de la Etapa 0 a la 4, con su porqué y evidencia)
            ├── 03_como_correr.md             (guía de ejecución de la instancia La Reina)
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
        ├── Estructura_carpeta_proyecto.md
        ├── feedback_presentacion_2.txt
        ├── Informe 1.docx
        ├── Lineamientos Entrega 1 2026-2.md
        ├── Lineamientos Entrega 2 2026-2.md
        ├── P7 Planificación de la operación de buses eléctricos en la Región Metropolitana-1.md
        ├── plan_etapas_3_4.md                (plan de las Etapas 3-4 en la instancia La Reina)
        ├── Presentacion 1 capstone.pdf
        ├── Presentación 2 Capstone.pdf
        ├── Propuesta_metodologia_reunion.md  (histórico: propuesta con que se rediseñó la metodología)
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
        └── 📁etapa0_calibracion_deadhead
            └── 📁graficos
                ├── ejemplo_trazado.png
                ├── factor_por_escala.png
            └── 📁tablas
                ├── escala_deadhead_pullout_pullin.csv
                ├── factor_por_escala.csv
                ├── factor_por_trazado.csv
            ├── reporte.md
        └── 📁etapa1_clustering
            └── 📁graficos
                ├── barrido_theta.png
                ├── capacidad_ciclo.png
                ├── capacidad_sin_vs_con_recuperacion.png
                ├── distancias.png
                ├── rutas_por_terminal.png
            └── 📁mapas
                ├── mapa_c1a.png
                ├── mapa_c1b.png
                ├── mapa_c2.png
                ├── mapa_diferencias.png
                ├── mapa_paraderos_terminales.png
                ├── mapa_terminal_el_conquistador.png
                ├── mapa_terminal_la_reina.png
                ├── mapa_terminal_los_espinos.png
                ├── mapa_terminal_santa_rosa.png
                ├── mapa_terminal_vespucio_norte.png
            └── 📁tablas
                ├── barrido_theta.csv
                ├── capacidad_por_terminal.csv
                ├── capacidad_sin_vs_con_recuperacion.csv
                ├── comparacion_estrategias.csv
                ├── distancias_ruta_terminal.csv
                ├── resumen_por_terminal.csv
                ├── validacion_carga_c2.csv
                ├── rutas_que_cambian.csv
            ├── reporte.md
        └── 📁etapa2_vsp
            └── 📁graficos
                ├── energia_por_jornada_E0_E1.png
                ├── escalera_buses.png
                ├── escalera_costo.png
                ├── jornadas_<escenario>.png                (histogramas por escenario: E0, E1, LB, E0_sep, E1_sep, E1_C2, E1_C2_sep)
                ├── sensibilidad_deadhead.png
            └── 📁tablas
                ├── escalera_escenarios.csv
                ├── precio_del_clustering.csv
                ├── resumen_escenarios.csv
                ├── resumen_sensibilidad.csv
                ├── variantes_c2.csv
                ├── evidencia_union.csv
                ├── sensibilidad_deadhead.csv
            ├── reporte.md
        └── 📁caso_base                              (caso base de la red completa: no se vuelve a correr)
            └── 📁barrido
                └── 📁graficos
                    ├── barrido_costo_total.png
                    ├── barrido_ciclos_y_cota.png
                    ├── barrido_robustez.png
                └── 📁tablas
                    ├── barrido_niveles.csv
                    ├── decision_barrido.csv
                    ├── evidencia_terminales_separados.csv
                ├── reporte_barrido.md
            └── 📁graficos
                ├── ocupacion_<escenario>_soc100.png        (buses cargando por minuto y electroterminal; x4 escenarios)
                ├── soc_ejemplo_<escenario>_soc100.png      (SOC de jornadas reales; x4)
            └── 📁tablas
                ├── eventos_<escenario>_soc100.csv          (cada carga: tipo, llegada, inicio, fin, espera, kWh, costo)
                ├── jornadas_<escenario>_soc100.csv         (jornadas tras las particiones)
                ├── ocupacion_<escenario>_soc100.csv        (buses cargando por minuto, módulo 24 h)
                ├── ventanas_<escenario>_soc100.csv         (ventanas en que cada bus puede cargar)
                ├── resumen_carga.csv                       (una fila por escenario y nivel)
            ├── reporte_<escenario>_soc100.md
        └── 📁instancia_LR                           (terminal La Reina: caso base, Etapas 3-4 y KPIs)
            └── 📁caso_base                          (E0 y E1 filtrados al terminal; mismas tablas que caso_base/)
            └── 📁etapa3
                └── 📁h<h>                           (h = 0, 30, 60)
                    └── 📁graficos                   (gantt_cadenas, llegadas_patio_por_hora; cada uno con su .csv)
                    └── 📁tablas                     (tramos, cadenas, ventanas, diagnostico_flota, resumen)
                    ├── reporte.md
            └── 📁etapa4
                └── 📁h<h>_d<Δ>                      (h0_d15 base; h0_d5, h0_d30, h30_d15, h60_d15)
                    └── 📁graficos                   (ocupacion_24h, energia_por_tarifa; cada uno con su .csv)
                    └── 📁tablas                     (programa_FIFO, programa_E2, programa_E2_detallado, ocupacion_minutos, ocupacion_bloques,
                                                      energia_por_tarifa, reservas, modelo, resumen)
                    ├── reporte.md
            └── 📁kpis
                └── 📁graficos                       (escalera_buses, costo_apilado, ocupacion_24h, energia_por_tarifa,
                                                      sensibilidad_holgura, sensibilidad_delta; cada uno con su .csv)
                └── 📁tablas                         (kpis_escenarios, validaciones, energia_por_tarifa, ocupacion_por_hora,
                                                      diagnostico_flota_por_holgura, sensibilidad_holgura,
                                                      sensibilidad_delta, tiempos_y_brechas, detallado_vs_agregado)
            ├── resumen_para_analisis.md             (el archivo que se entrega para el análisis)
        └── 📁presentacion                           (gráficos de datos y del caso base de la red completa, script 16-)
    └── 📁scripts
        └── 📁common
            ├── __init__.py
            ├── clustering.py
            ├── geo.py
            ├── graficos.py                         (estilo común de los gráficos de la instancia)
            ├── instancia.py                        (patios, nombre, carpeta y filtros de un electroterminal)
            ├── medicion.py                         (pico de memoria)
            ├── parametros.py
            ├── rutas.py
            ├── tiempo.py
        ├── 1-filtro_datos_buses.py
        ├── 2-filtro_tipo_dia.py
        ├── 3-preprocesamiento_expediciones.py          (Etapa 0)
        ├── 4-clustering_c1.py                          (Etapa 1, C1a + C1b)
        ├── 5-clustering_c2.py                          (Etapa 1, C2)
        ├── 6-vsp_asignacion_buses.py                   (Etapa 2: asignación de buses, un escenario por corrida)
        ├── 7-comparar_escenarios.py                    (Etapa 2: escalera de escenarios y sensibilidad)
        ├── 8-clustering_comparacion.py                 (cierre Etapa 1: comparación y mapas)
        ├── 9-calibracion_deadhead.py                   (calibración del factor de desvío con trazados GTFS)
        ├── 10-caso_base_carga_reactiva.py              (caso base: carga reactiva; red completa o un terminal con --terminal)
        ├── 11-caso_base_nivel_bateria.py               (caso base: barrido de niveles de batería, red completa)
        ├── 12-etapa3_cortes_reencadenamiento.py        (Etapa 3: corte por DP + re-encadenamiento por flujo)
        ├── 13-etapa4_programacion_carga.py             (Etapa 4: E2-FIFO, modelo agregado y detallado)
        ├── 14-kpis_instancia.py                        (KPIs, figuras y resumen_para_analisis.md de la instancia)
        ├── 16-graficos_informe.py                      (gráficos de datos y del caso base de la red completa)
    ├── .gitignore
    ├── README.md
```
