"""R9 · Deshacer y rehacer con el patrón Comando y dos pilas (dueño: Daniel).

Cada cambio de la red es un objeto con dos métodos:
    aplicar(red)   hace el cambio
    revertir(red)  lo deshace exactamente

    operación nueva:  aplicar; apilar en DESHACER; vaciar REHACER
    deshacer:         sacar de DESHACER; revertir; apilar en REHACER
    rehacer:          sacar de REHACER;  aplicar;  apilar en DESHACER

Como las pilas son LIFO, los cambios se deshacen en el orden inverso exacto
en que se hicieron. Eso garantiza que, al deshacer un "quitar parada", el
nodo anterior que guardamos sigue en la ruta y la parada vuelve a su sitio.

Complejidad: apilar/desapilar O(1); cada deshacer/rehacer cuesta lo mismo
que la operación que revierte (O(1) en paradas, O(log n) en cierres).
"""

from .cierres import aplicar_cierre, aplicar_reapertura
from .edicion import desenlazar, enlazar


class ComandoCerrar:
    __slots__ = ("estacion",)

    def __init__(self, estacion):
        self.estacion = estacion

    def aplicar(self, red):
        aplicar_cierre(red, self.estacion)

    def revertir(self, red):
        aplicar_reapertura(red, self.estacion)

    def descripcion(self):
        return "Cerrar " + self.estacion.nombre


class ComandoReabrir:
    __slots__ = ("estacion",)

    def __init__(self, estacion):
        self.estacion = estacion

    def aplicar(self, red):
        aplicar_reapertura(red, self.estacion)

    def revertir(self, red):
        aplicar_cierre(red, self.estacion)

    def descripcion(self):
        return "Reabrir " + self.estacion.nombre


class ComandoAgregar:
    __slots__ = ("nodo", "anterior")

    def __init__(self, nodo, anterior):
        self.nodo = nodo
        self.anterior = anterior

    def aplicar(self, red):
        enlazar(red, self.nodo, self.anterior)

    def revertir(self, red):
        desenlazar(red, self.nodo)

    def descripcion(self):
        return "Agregar " + self.nodo.estacion.nombre + " a " + self.nodo.ruta.nombre


class ComandoQuitar:
    __slots__ = ("nodo", "anterior")

    def __init__(self, nodo, anterior):
        self.nodo = nodo
        self.anterior = anterior

    def aplicar(self, red):
        desenlazar(red, self.nodo)

    def revertir(self, red):
        enlazar(red, self.nodo, self.anterior)

    def descripcion(self):
        return "Quitar " + self.nodo.estacion.nombre + " de " + self.nodo.ruta.nombre


def ejecutar(red, comando):
    comando.aplicar(red)
    red._deshacer.apilar(comando)
    red._rehacer.vaciar()
    return True


def deshacer(red):
    if red._deshacer.vacia():
        return False
    c = red._deshacer.desapilar()
    c.revertir(red)
    red._rehacer.apilar(c)
    return True


def rehacer(red):
    if red._rehacer.vacia():
        return False
    c = red._rehacer.desapilar()
    c.aplicar(red)
    red._deshacer.apilar(c)
    return True
