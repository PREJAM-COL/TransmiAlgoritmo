"""Pila LIFO sobre un arreglo (docs/fase-2-diseno.md §3.4).

Se apoya en list.append y list.pop() del final, que son O(1) amortizado
(el arreglo de Python crece por bloques). Es la base de deshacer/rehacer (R9).

Complejidad: apilar, desapilar, cima, vacia, len: O(1) (amortizado al apilar);
vaciar: O(1).
"""


class Pila:
    __slots__ = ("_datos",)

    def __init__(self):
        self._datos = []

    def __len__(self):
        return len(self._datos)

    def vacia(self):
        return len(self._datos) == 0

    def apilar(self, x):
        self._datos.append(x)

    def desapilar(self):
        """Quita y devuelve el elemento de arriba. IndexError si está vacía."""
        if len(self._datos) == 0:
            raise IndexError("desapilar de una pila vacía")
        return self._datos.pop()

    def cima(self):
        """Devuelve el elemento de arriba sin quitarlo. IndexError si está vacía."""
        if len(self._datos) == 0:
            raise IndexError("cima de una pila vacía")
        return self._datos[len(self._datos) - 1]

    def vaciar(self):
        self._datos = []

    def elementos(self):
        """Copia de los elementos, del fondo a la cima (para la interfaz)."""
        copia = []
        for x in self._datos:
            copia.append(x)
        return copia
