"""Rutas de carpetas del proyecto, resueltas de forma relativa al repo
(no al directorio desde donde se ejecuta el script), igual que en
scripts/1-filtro_datos_buses.py.
"""

from pathlib import Path

# scripts/common/rutas.py -> parent (common) -> parent (scripts) -> parent (raiz del repo)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_ALUMNOS = PROJECT_ROOT / "data-alumnos"
DATA_FILTRADO = PROJECT_ROOT / "data-filtrado"

# Nuevas carpetas de esta ronda de trabajo (Etapas 0-2, ver plan del 28/09).
# Se crean automaticamente si no existen para que los scripts no fallen en
# una maquina nueva del equipo.
DATA_PROCESSED = PROJECT_ROOT / "data-processed"
RESULTS_DIR = PROJECT_ROOT / "results"

for _dir in (DATA_PROCESSED, RESULTS_DIR):
    _dir.mkdir(exist_ok=True)

# Separador usado para leer/escribir CSV en data-filtrado/ y data-processed/.
# Ver docs/decisiones_datos.md seccion 3.5: Excel en configuracion regional
# Chile/Latam usa ',' como separador decimal, por lo que espera ';' como
# separador de columnas.
CSV_SEP = ";"


def carpeta_resultados(nombre_etapa: str) -> Path:
    """Crea (si no existe) y devuelve results/<nombre_etapa>/."""
    carpeta = RESULTS_DIR / nombre_etapa
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta
