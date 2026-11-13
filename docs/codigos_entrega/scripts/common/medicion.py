"""Memoria maxima de la corrida."""

import psutil


def pico_memoria_mb() -> float:
    """Pico de memoria del proceso en MB (peak working set en Windows; RSS actual en otros sistemas)."""
    info = psutil.Process().memory_info()
    return getattr(info, "peak_wset", info.rss) / 2**20
