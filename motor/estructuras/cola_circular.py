"""Cola FIFO sobre un arreglo circular (docs/fase-2-diseno.md §3.5).

Idea: un arreglo de tamaño fijo donde la "cabeza" avanza en círculo. Sacar el
primero solo mueve un índice; no hay que correr los demás elementos como hace
list.pop(0), que cuesta O(n) por llamada.

    datos:   [ _, _, C, D, E, _ ]      cabeza = 2, n = 3
                     ^cabeza
    encolar(F) escribe en (cabeza + n) % capacidad

La capacidad siempre es potencia de 2, así "módulo capacidad" se calcula con
`& (capacidad - 1)`, que es más barato que %.

Complejidad: encolar O(1) amortizado (al llenarse se duplica: O(n) de vez en
cuando); desencolar, frente, vacia, len: O(1). Espacio O(n).
"""


class ColaCircular:
    __slots__ = ("_datos", "_cabeza", "_n")

    def __init__(self, capacidad=16):
        cap = 1
        while cap < capacidad:
            cap *= 2
        self._datos = [None] * cap
        self._cabeza = 0
        self._n = 0

    def __len__(self):
        return self._n

    def vacia(self):
        return self._n == 0

    def encolar(self, x):
        cap = len(self._datos)
        if self._n == cap:
            self._crecer()
            cap = len(self._datos)
        self._datos[(self._cabeza + self._n) & (cap - 1)] = x
        self._n += 1

    def desencolar(self):
        """Quita y devuelve el primero. IndexError si está vacía."""
        if self._n == 0:
            raise IndexError("desencolar de una cola vacía")
        x = self._datos[self._cabeza]
        self._datos[self._cabeza] = None          # no retener referencias
        self._cabeza = (self._cabeza + 1) & (len(self._datos) - 1)
        self._n -= 1
        return x

    def frente(self):
        """Devuelve el primero sin quitarlo. IndexError si está vacía."""
        if self._n == 0:
            raise IndexError("frente de una cola vacía")
        return self._datos[self._cabeza]

    def _crecer(self):
        """Duplica la capacidad copiando en orden lógico (cabeza queda en 0). O(n)."""
        viejo = self._datos
        cap = len(viejo)
        nuevo = [None] * (cap * 2)
        for i in range(self._n):
            nuevo[i] = viejo[(self._cabeza + i) & (cap - 1)]
        self._datos = nuevo
        self._cabeza = 0


