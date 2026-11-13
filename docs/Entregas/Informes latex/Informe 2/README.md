# Informe 2 — ICS2122

Este proyecto contiene la base LaTeX del segundo informe del grupo 24. El archivo principal es `Informe2.tex`; sus secciones editables están en `chapters/informe2/`.

## Compilación

Desde la carpeta del proyecto:

1. Ejecutar `pdflatex Informe2.tex`.
2. Cuando el informe ya tenga citas, ejecutar `bibtex Informe2`.
3. Ejecutar `pdflatex Informe2.tex` dos veces más para actualizar citas e índice.

Las referencias se agregan en `Thesis.bib`. La plantilla usa la clase `pucthesis.cls` y los estilos bibliográficos `apacite.sty` y `apacite.bst`.

## Firmas

Las imágenes de firmas se guardan en `firmas/`. El anexo de declaración de uso de IA busca archivos PNG, JPG o JPEG con los nombres definidos en `chapters/informe2/declaracion_ia.tex`.
