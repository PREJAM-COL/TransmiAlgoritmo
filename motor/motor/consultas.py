"""R1, R2, R3 · Consultas de estaciones (dueño: Miguel).

R1 usa la tabla hash (nombre -> Estacion): O(1) esperado.
R2 y R3 usan el AVL que contiene SOLO estaciones abiertas, ordenado por
nombre. Como las cerradas no están en el árbol, nunca hay que saltarlas.

Idea clave de R2: en orden alfabético, todos los nombres que empiezan por un
prefijo están JUNTOS, y el primero de ellos es el primer nombre >= prefijo.
Basta con bajar una vez por el árbol (O(log n)) y avanzar mientras el nombre
empiece por el prefijo.
"""


def estado(red, nombre):
    """R1. "abierta", "cerrada" o "no existe". O(1) esperado (n = estaciones)."""
    if not isinstance(nombre, str):
        return "no existe"
    e = red._estaciones.obtener(nombre)
    if e is None:
        return "no existe"
    return "abierta" if e.abierta else "cerrada"


def autocompletar(red, prefijo, k):
    """R2. Hasta k estaciones abiertas que empiezan por `prefijo`, alfabéticas.

    O(log n + k), n = estaciones abiertas.
    """
    res = []
    if not isinstance(prefijo, str) or not isinstance(k, int) or k <= 0:
        return res
    for nombre, _ in red._abiertas.desde(prefijo):
        if not nombre.startswith(prefijo):
            break
        res.append(nombre)
        if len(res) == k:
            break
    return res


def rango(red, desde, hasta):
    """R3. Estaciones abiertas con desde <= nombre <= hasta, alfabéticas.

    O(log n + m), n = estaciones abiertas, m = tamaño de la respuesta.
    """
    res = []
    if not isinstance(desde, str) or not isinstance(hasta, str) or hasta < desde:
        return res
    for nombre, _ in red._abiertas.desde(desde):
        if hasta < nombre:
            break
        res.append(nombre)
    return res
