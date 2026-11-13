"""Motor del planeador TransMilenio.

El script del profesor hace exactamente:

    from motor import Red, simular_fila

Todo lo que resuelve un requisito vive dentro de este paquete y respeta las
reglas del curso: sin dict, set, sorted, heapq, collections, etc.
"""

from .red import Red
from .fila import simular_fila

__all__ = ["Red", "simular_fila"]
