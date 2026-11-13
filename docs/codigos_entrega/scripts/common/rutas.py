"""Carpetas del proyecto, relativas a la carpeta scripts/ (no al directorio desde donde se ejecuta cada script).

datos/       entrada: archivos del curso (ver la Seccion 4.1.2 del informe)
resultados/  salida: todo lo que escriben los scripts
"""

from pathlib import Path

# scripts/common/rutas.py -> common -> scripts (raiz)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATOS = PROJECT_ROOT / "datos"
GTFS = DATOS / "gtfs"
RESULTS_DIR = PROJECT_ROOT / "resultados"
DATA_FILTRADO = RESULTS_DIR / "datos_filtrados"
DATA_PROCESSED = RESULTS_DIR / "datos_procesados"

for _dir in (RESULTS_DIR, DATA_FILTRADO, DATA_PROCESSED):
    _dir.mkdir(parents=True, exist_ok=True)

# Separador de los CSV que escriben los scripts (Excel con configuracion regional de Chile espera ';').
CSV_SEP = ";"


def carpeta_resultados(nombre_etapa: str) -> Path:
    """Crea (si no existe) y devuelve resultados/<nombre_etapa>/."""
    carpeta = RESULTS_DIR / nombre_etapa
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta
