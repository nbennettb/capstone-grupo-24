"""Nombres de los escenarios y terminos en todo lo que lee una persona (graficos, tablas, CSV de resultados y
reportes). Las siglas internas (E0, E1, E2-FIFO, E2, LB, C1b, h, Delta, LR) quedan solo en el codigo, las opciones de
linea de comandos y los nombres de archivo. Equivalencias en docs/context/01_como_funciona.md."""

import re

ESCENARIO = {"E0": "Caso base", "E1": "Caso base con interlining",
             "E2-FIFO": "Propuesta con carga por orden de llegada", "E2": "Propuesta completa"}
CORTO = {"E0": "Caso base", "E1": "Caso base + interlining", "E2-FIFO": "Propuesta, carga por llegada",
         "E2": "Propuesta completa"}

# Encabezados de los CSV de resultados
COLUMNAS = {
    "holgura_min": "holgura_de_recarga_min", "delta_min": "largo_del_bloque_min",
    "reservas_intermedias": "reservas_diurnas", "costo_reservas_intermedias": "costo_reservas_diurnas",
    "ventanas_intermedias": "ventanas_diurnas",
    "costo_total_comparable": "costo_total", "costo_total_original": "costo_total_con_espera_nocturna",
    "costo_espera_comparable": "costo_espera", "costo_espera_original": "costo_espera_con_espera_nocturna",
    "buses_vsp": "buses_jornadas_sin_bateria", "jornadas_vsp": "jornadas_sin_bateria",
    "reservas_FIFO": "reservas_carga_por_llegada", "reservas_E2": "reservas_propuesta_completa",
    "buses_totales_FIFO": "buses_totales_carga_por_llegada", "buses_totales_E2": "buses_totales_propuesta_completa",
    "costo_total_comparable_E2": "costo_total_propuesta_completa", "costo_energia_E2": "costo_energia_propuesta_completa",
    "politica": "escenario",
}

# Reemplazos de texto, en orden (los especificos antes que los generales)
_REGLAS = [
    (r"E2 agregado - LP \(cota\)", "Modelo agregado, LP (cota)"),
    (r"E2 agregado - MILP", "Modelo agregado (MILP)"),
    (r"E2 detallado - fase 1 \(reservas fijas\)", "Modelo detallado, fase 1 (reservas fijas)"),
    (r"E2 detallado - MILP", "Modelo detallado (MILP)"),
    (r"\bE2-detallado\b", "Propuesta completa (modelo detallado)"),
    (r"\bE2-FIFO\b", "Propuesta con carga por orden de llegada"),
    (r"\bE2\b", "Propuesta completa"),
    (r"\bE1_sep\b", "Caso base con interlining con terminales separados"),
    (r"\bE0_sep\b", "Caso base con terminales separados"),
    (r"\bE1\b", "Caso base con interlining"),
    (r"\bE0\b", "Caso base"),
    (r"\bFIFO\b", "orden de llegada"),
    (r"\bLB\b", "cota inferior de flota"),
    (r"\bC1b\b", "asignacion por cercania"),
    (r"(?<![\w/])LR\b", "La Reina"),
    (r"\bDelta ?= ?(\d+)( min)?", r"largo del bloque \1 min"),
    (r"\bDelta\b", "largo del bloque"),
    (r"(?<![\w.])h=(\d+(?:\.\d+)?)\b", r"holgura de recarga \1 min"),
    (r"holgura h\b", "holgura de recarga"),
    (r"\bbuses del VSP\b", "buses de las jornadas sin bateria"),
    (r"\bjornadas del VSP\b", "jornadas sin bateria"),
    (r"\(i\) VSP\b", "(i) Jornadas sin bateria"),
    (r"intermedias\b", "diurnas"),
    (r"intermedia\b", "diurna"),
    (r"[Cc]osto total comparable", "Costo total"),
    (r"[Cc]osto total original", "Costo total con espera nocturna"),
    (r"total original", "total con espera nocturna"),
]


def renombrar_texto(texto):
    """Aplica los nombres a un texto libre (markdown o celdas). No toca lo que va entre comillas invertidas
    (rutas y nombres de archivo)."""
    partes = texto.split("`")
    for i in range(0, len(partes), 2):                 # solo fuera de `...`
        for patron, nuevo in _REGLAS:
            partes[i] = re.sub(patron, nuevo, partes[i])
    return "`".join(partes)


def renombrar_reporte_etapa4(texto):
    """En los reportes por corrida de la Etapa 4, "E2" sin sufijo es el modelo agregado."""
    partes = texto.split("`")
    for i in range(0, len(partes), 2):
        partes[i] = re.sub(r"\bE2\b(?!-)", "Propuesta completa (modelo agregado)", partes[i])
    return renombrar_texto("`".join(partes))


def presentar(df):
    """Copia de una tabla lista para una persona: encabezados con los nombres y celdas de texto renombradas."""
    out = df.rename(columns=COLUMNAS).copy()
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].map(lambda x: renombrar_texto(x) if isinstance(x, str) else x)
    return out


def tramo_horario(inicio, fin):
    """Tramo tarifario con sus horas, por ejemplo '00-08 h'."""
    return f"{int(inicio):02d}-{int(fin):02d} h"
