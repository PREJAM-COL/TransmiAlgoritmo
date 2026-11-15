"""Se consulta muy seguido y cambia poco." Por eso el ranking es un AVL que ya
está ordenado por la clave (-buses_dia, nombre):
  - el signo menos pone primero a las de MÁS buses;
  - el nombre desempata alfabéticamente;
  - solo contiene estaciones ABIERTAS (cerrar = sacarla del árbol).

Consultar los k primeros es recorrer el árbol en orden: O(log n + k).
Cada cambio (cerrar, reabrir, quitar o agregar una parada con horarios)
cuesta O(log n): eliminar la clave vieja e insertar la nueva.
"""


def clave_ranking(e):
    return (-e.buses_dia, e.nombre)


def ranking(red, k):
    """Nombres de las k estaciones abiertas con más buses al día."""
    res = []
    if not isinstance(k, int) or k <= 0:
        return res
    for _, e in red._ranking.desde():
        res.append(e.nombre)
        if len(res) == k:
            break
    return res


def entrar(red, e):
    """Pone una estación (abierta) en el ranking. O(log n)."""
    red._ranking.insertar(clave_ranking(e), e)


def salir(red, e):
    """Saca una estación del ranking. O(log n)."""
    red._ranking.eliminar(clave_ranking(e))


def cambiar_buses(red, e, delta):
    """Suma `delta` a los buses diarios de `e` y la reubica en el ranking. O(log n)."""
    if delta == 0:
        return
    if e.abierta:
        salir(red, e)
    e.buses_dia += delta
    if e.abierta:
        entrar(red, e)
