"""R7 · Editar rutas (dueño: Daniel).

Cada ruta es una lista doblemente enlazada de NodoParada, y la tabla hash
_paradas encuentra el nodo de (ruta, estación) en O(1). Con eso:

  agregar_parada: buscar `despues_de` (O(1)) y enlazar el nodo nuevo (O(1))
  quitar_parada:  buscar el nodo (O(1)) y desenlazarlo (O(1))
  recorrido:      recorrer la lista hacia adelante o hacia atrás (O(L))

Además, cada estación tiene su lista de "membresías" (rutas que paran ahí)
y el nodo conoce su membresía, así que también se actualiza en O(1).

Si la parada tenía horarios, sus buses dejan de pasar (o vuelven a pasar)
por esa estación: se ajusta el ranking de R6 en O(log n).

Estas funciones validan y APLICAN; el registro para deshacer lo hace R9.
"""

from .modelo import Membresia, NodoParada
from .ranking import cambiar_buses


def preparar_agregar(red, ruta, nueva, despues_de):
    """Valida y devuelve (nodo_nuevo, anterior) o None si no se puede.

    Reglas aprobadas (docs/fase-1-analisis.md §15): la ruta existe, `nueva`
    existe en la red y no está ya en la ruta, y `despues_de` está en la ruta.
    """
    if not isinstance(ruta, str) or not isinstance(nueva, str) or not isinstance(despues_de, str):
        return None
    r = red._rutas.obtener(ruta)
    e = red._estaciones.obtener(nueva)
    if r is None or e is None:
        return None
    anterior = red._paradas.obtener(red.clave_parada(ruta, despues_de))
    if anterior is None or red._paradas.contiene(red.clave_parada(ruta, nueva)):
        return None
    nodo = NodoParada(e, r)
    nodo.membresia = Membresia(nodo)
    return nodo, anterior


def preparar_quitar(red, ruta, estacion):
    """Devuelve (nodo, anterior) de la parada a quitar, o None si no existe."""
    if not isinstance(ruta, str) or not isinstance(estacion, str):
        return None
    nodo = red._paradas.obtener(red.clave_parada(ruta, estacion))
    if nodo is None:
        return None
    return nodo, nodo.ant


def enlazar(red, nodo, anterior):
    """Pone `nodo` en su ruta justo después de `anterior`. O(1) + O(log n) del ranking."""
    nodo.ruta.paradas.insertar_despues(anterior, nodo)
    nodo.estacion.membresias.insertar_al_final(nodo.membresia)
    red._paradas.poner(red.clave_parada(nodo.ruta.nombre, nodo.estacion.nombre), nodo)
    cambiar_buses(red, nodo.estacion, len(nodo.horas))


def desenlazar(red, nodo):
    """Saca `nodo` de su ruta y de su estación. O(1) + O(log n) del ranking."""
    nodo.ruta.paradas.quitar(nodo)
    nodo.estacion.membresias.quitar(nodo.membresia)
    red._paradas.quitar(red.clave_parada(nodo.ruta.nombre, nodo.estacion.nombre))
    cambiar_buses(red, nodo.estacion, -len(nodo.horas))


def recorrido(red, ruta, al_reves=False):
    """Nombres de las estaciones de la ruta, en su sentido o al revés. O(L)."""
    if not isinstance(ruta, str):
        return []
    r = red._rutas.obtener(ruta)
    if r is None:
        return []
    nodos = r.paradas.atras() if al_reves else r.paradas.adelante()
    return [n.estacion.nombre for n in nodos]
