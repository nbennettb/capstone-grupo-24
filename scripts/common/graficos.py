"""Estilo comun de los graficos de la instancia (Etapas 3-4 y KPIs): colores fijos por escenario y por componente,
para que un mismo escenario tenga el mismo color en todas las figuras del informe."""

import time

import matplotlib.pyplot as plt

TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
GRILLA = "#e5e4e0"
FONDO = "#fcfcfb"
PUESTOS = "#e34948"          # linea de capacidad
PUNTA = "#52514e"            # sombreado de la tarifa punta (neutro, con transparencia)

# Orden categorico fijo (se asigna por entidad, nunca por rango)
CATEGORICOS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ESCENARIO = {"E0": CATEGORICOS[0], "E1": CATEGORICOS[1], "E2-FIFO": CATEGORICOS[2], "E2": CATEGORICOS[3]}
NOMBRE_ESCENARIO = {"E0": "Caso base", "E1": "Caso base con interlining",
                    "E2-FIFO": "Propuesta con carga por orden de llegada", "E2": "Propuesta completa"}


def estilo(ax):
    """Ejes sobrios: sin borde superior ni derecho, grilla horizontal tenue, texto en tinta de texto."""
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TEXTO_SECUNDARIO)
    ax.tick_params(colors=TEXTO_SECUNDARIO, labelsize=8)
    ax.yaxis.label.set_color(TEXTO)
    ax.xaxis.label.set_color(TEXTO)
    ax.grid(axis="y", color=GRILLA, linewidth=0.7)
    ax.set_axisbelow(True)


def _escribir(funcion, path, intentos=6):
    """Escribe con reintentos: dentro de una carpeta sincronizada (OneDrive) Windows puede rechazar por un momento la
    escritura de un archivo recien sobrescrito (OSError 22 o 13) mientras lo sincroniza o lo tiene abierto un visor."""
    for k in range(intentos):
        try:
            funcion(path)
            return
        except OSError as error:
            if k == intentos - 1:
                raise OSError(f"No se pudo escribir {path} tras {intentos} intentos ({error}). Cerrar el archivo si "
                              "esta abierto en un visor, o pausar la sincronizacion de OneDrive, y volver a correr.") from error
            time.sleep(1.0 + k)


def guardar(fig, path_png, datos):
    """Guarda el grafico y, al lado, el CSV con los datos que muestra."""
    fig.patch.set_facecolor(FONDO)
    fig.tight_layout()
    _escribir(lambda p: fig.savefig(p, dpi=150, facecolor=FONDO), path_png)
    plt.close(fig)
    _escribir(lambda p: datos.to_csv(p, index=False, sep=";"), path_png.with_suffix(".csv"))
