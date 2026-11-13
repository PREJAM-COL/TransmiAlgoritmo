"""Objetos del dominio (docs/fase-2-diseno.md §2).

Todas las clases usan __slots__: cada objeto guarda sus atributos en un
arreglo fijo en vez de un diccionario interno. Gasta menos memoria y deja
claro que no usamos dict en ningún lado.

Relaciones:
    Ruta.paradas      -> ListaDoble de NodoParada (recorrido en un solo sentido)
    Estacion.membresias -> ListaDoble de Membresia (rutas que paran ahí)
    NodoParada.membresia <-> Membresia.parada (para quitar una parada en O(1))
"""

from .estructuras.lista_doble import ListaDoble


class Estacion:
    __slots__ = ("id", "nombre", "abierta", "buses_dia", "membresias")

    def __init__(self, id_, nombre):
        self.id = id_                  # índice en los arreglos internos de Red
        self.nombre = nombre
        self.abierta = True
        self.buses_dia = 0             # suma de len(horas) de sus paradas actuales (R6)
        self.membresias = ListaDoble()

    def __repr__(self):
        return "Estacion(" + self.nombre + ")"


class Ruta:
    __slots__ = ("nombre", "paradas")

    def __init__(self, nombre):
        self.nombre = nombre
        self.paradas = ListaDoble()

    def __repr__(self):
        return "Ruta(" + self.nombre + ")"


class NodoParada:
    """Nodo de la lista doble de una ruta."""

    __slots__ = ("estacion", "ruta", "ant", "sig", "horas", "membresia")

    def __init__(self, estacion, ruta):
        self.estacion = estacion
        self.ruta = ruta
        self.ant = None
        self.sig = None
        self.horas = []                # minutos 0..1439, ordenados (R4)
        self.membresia = None


class Membresia:
    """Nodo de la lista doble de rutas de una estación."""

    __slots__ = ("parada", "ant", "sig")

    def __init__(self, parada):
        self.parada = parada
        self.ant = None
        self.sig = None
