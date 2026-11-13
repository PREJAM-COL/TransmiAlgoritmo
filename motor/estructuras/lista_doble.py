"""Lista doblemente enlazada con nodo centinela (docs/fase-2-diseno.md §3.3).

El centinela es un nodo falso que siempre existe: el primero real es
centinela.sig y el último es centinela.ant. Con él, insertar o quitar al
inicio, al final o en una lista vacía son el mismo código, sin casos
especiales.

La lista no define el tipo de nodo: cualquier objeto con atributos `ant` y
`sig` sirve (NodoParada, Membresia o el NodoLista genérico de abajo).

Complejidad (n = elementos):
    insertar_despues, insertar_al_inicio, insertar_al_final, quitar: O(1)
    adelante, atras (recorrer todo): O(n)
    len: O(1)
"""


class NodoLista:
    """Nodo genérico con un dato (útil en pruebas y en usos simples)."""

    __slots__ = ("dato", "ant", "sig")

    def __init__(self, dato=None):
        self.dato = dato
        self.ant = None
        self.sig = None


class ListaDoble:
    __slots__ = ("_centinela", "_n")

    def __init__(self):
        c = NodoLista()
        c.ant = c
        c.sig = c
        self._centinela = c
        self._n = 0

    def __len__(self):
        return self._n

    def vacia(self):
        return self._n == 0

    @property
    def centinela(self):
        """Nodo falso. insertar_despues(lista.centinela, x) inserta al inicio."""
        return self._centinela

    def es_centinela(self, nodo):
        return nodo is self._centinela

    def primero(self):
        """Primer nodo real, o None si la lista está vacía."""
        n = self._centinela.sig
        return None if n is self._centinela else n

    def ultimo(self):
        """Último nodo real, o None si la lista está vacía."""
        n = self._centinela.ant
        return None if n is self._centinela else n

    def siguiente(self, nodo):
        """Nodo después de `nodo`, o None si `nodo` es el último."""
        n = nodo.sig
        return None if n is self._centinela else n

    def anterior(self, nodo):
        """Nodo antes de `nodo`, o None si `nodo` es el primero."""
        n = nodo.ant
        return None if n is self._centinela else n

    def insertar_despues(self, nodo, nuevo):
        """Enlaza `nuevo` justo después de `nodo` (que puede ser el centinela). O(1)."""
        nuevo.ant = nodo
        nuevo.sig = nodo.sig
        nodo.sig.ant = nuevo
        nodo.sig = nuevo
        self._n += 1

    def insertar_al_inicio(self, nuevo):
        self.insertar_despues(self._centinela, nuevo)

    def insertar_al_final(self, nuevo):
        self.insertar_despues(self._centinela.ant, nuevo)

    def quitar(self, nodo):
        """Desenlaza `nodo` de la lista. O(1).

        Se limpian sus punteros para que un nodo quitado no se pueda recorrer
        por error. Quien necesite volver a insertarlo en el mismo sitio (R9)
        debe guardar antes su anterior (nodo.ant).
        """
        nodo.ant.sig = nodo.sig
        nodo.sig.ant = nodo.ant
        nodo.ant = None
        nodo.sig = None
        self._n -= 1

    def adelante(self):
        """Recorre los nodos del primero al último."""
        c = self._centinela
        n = c.sig
        while n is not c:
            sig = n.sig            # se guarda antes por si quien recorre quita el nodo
            yield n
            n = sig

    def atras(self):
        """Recorre los nodos del último al primero."""
        c = self._centinela
        n = c.ant
        while n is not c:
            ant = n.ant
            yield n
            n = ant
