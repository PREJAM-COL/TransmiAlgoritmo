"""R4 · Próximo bus, y utilidades de horas (dueño: Tomás).

Las horas se guardan como minutos desde la medianoche (0..1439): comparar y
ordenar enteros es más barato que comparar textos "HH:MM".

Decisión sobre horas >= 24 (el GTFS trae cosas como "25:10" para viajes que
pasan de medianoche): se toman módulo 24 h, así "25:10" es 01:10 del mismo
día de servicio. Los CSV del profesor ya vienen así (71 filas con "00:xx").
"""

from .estructuras.ordenamiento import limite_inferior

MINUTOS_DIA = 1440


def minutos(texto):
    """"HH:MM" -> minutos 0..1439 (horas >= 24 dan la vuelta). -1 si el texto no es válido."""
    if not isinstance(texto, str):
        return -1
    partes = texto.strip().split(":")
    if len(partes) != 2:
        return -1
    hh, mm = partes[0], partes[1]
    if not hh.isdigit() or not mm.isdigit() or len(mm) != 2:
        return -1
    h, m = int(hh), int(mm)
    if m > 59:
        return -1
    return (h * 60 + m) % MINUTOS_DIA


def formato(m):
    """Minutos -> "HH:MM"."""
    h = m // 60
    mi = m % 60
    return ("0" if h < 10 else "") + str(h) + ":" + ("0" if mi < 10 else "") + str(mi)


def proximo_bus(red, estacion, ruta, hora):
    """Primer bus de `ruta` en `estacion` a la hora `hora` o después.

    None si ya no hay más buses ese día, si la estación no existe, está cerrada, la ruta no para ahí, no tiene
    horarios o la hora no es válida.

    Complejidad: O(1) esperado para encontrar el nodo (tabla hash) +
    O(log h) de búsqueda binaria, con h = horas de ese par (ruta, estación).
    """
    e = red._estaciones.obtener(estacion)
    if e is None or not e.abierta:
        return None
    nodo = red._paradas.obtener(red.clave_parada(ruta, estacion))
    if nodo is None or len(nodo.horas) == 0:
        return None
    m = minutos(hora)
    if m < 0:
        return None
    i = limite_inferior(nodo.horas, m)
    if i == len(nodo.horas):
        return None          # ya pasó el último bus del día
    return formato(nodo.horas[i])
