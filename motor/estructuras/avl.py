r"""Árbol AVL: árbol binario de búsqueda autobalanceado (docs/fase-2-diseno.md §3.2).

Para qué lo usamos
------------------
- R2 y R3: un AVL con SOLO las estaciones abiertas, ordenadas por nombre.
  Autocompletar y rango son "buscar el primer nombre >= X y avanzar en orden".
- R8: cerrar = eliminar del árbol; reabrir = insertar.
- R6: otro AVL con clave (-buses_dia, nombre); el ranking son los k primeros.

Qué lo hace "AVL"
-----------------
En cada nodo, la altura del subárbol izquierdo y la del derecho difieren a lo
sumo en 1. Si una inserción o eliminación rompe esa regla, se arregla con
rotaciones (cambios locales de 3 punteros). Así la altura siempre es
O(log n) y ninguna operación degenera en una lista como en un árbol de
búsqueda simple al que le llegan nombres ya ordenados.

        z                                  y
       / \        rotación derecha        / \
      y   T4      ─────────────────►     x   z
     / \                                / \ / \
    x   T3                            T1 T2 T3 T4
   / \
  T1  T2

Complejidad (n = nodos):
    insertar, eliminar, buscar, contiene: O(log n)
    desde(clave) para producir m elementos: O(log n + m)
    construir_desde_ordenados: O(n)
    espacio: O(n)

Las claves pueden ser cualquier valor comparable con <: str (nombres) o
tuplas como (-buses, nombre). Se comparan solo con `<`, nunca con min/max.
"""


class _Nodo:
    __slots__ = ("clave", "valor", "izq", "der", "altura")

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izq = None
        self.der = None
        self.altura = 1


def _altura(n):
    return 0 if n is None else n.altura


def _actualizar(n):
    a, b = _altura(n.izq), _altura(n.der)
    n.altura = 1 + (a if a > b else b)


def _rotar_derecha(z):
    y = z.izq
    z.izq = y.der
    y.der = z
    _actualizar(z)
    _actualizar(y)
    return y


def _rotar_izquierda(z):
    y = z.der
    z.der = y.izq
    y.izq = z
    _actualizar(z)
    _actualizar(y)
    return y


def _balancear(n):
    """Recalcula la altura de n y aplica la rotación que haga falta (LL, RR, LR, RL)."""
    _actualizar(n)
    factor = _altura(n.izq) - _altura(n.der)
    if factor > 1:                                   # cargado a la izquierda
        if _altura(n.izq.izq) < _altura(n.izq.der):  # caso LR
            n.izq = _rotar_izquierda(n.izq)
        return _rotar_derecha(n)                     # caso LL
    if factor < -1:                                  # cargado a la derecha
        if _altura(n.der.der) < _altura(n.der.izq):  # caso RL
            n.der = _rotar_derecha(n.der)
        return _rotar_izquierda(n)                   # caso RR
    return n


class AVL:
    __slots__ = ("_raiz", "_n", "_cambio")

    def __init__(self):
        self._raiz = None
        self._n = 0
        self._cambio = False

    def __len__(self):
        return self._n

    def altura(self):
        return _altura(self._raiz)

    # ------------------------------------------------------------ consulta

    def _nodo(self, clave):
        n = self._raiz
        while n is not None:
            if clave < n.clave:
                n = n.izq
            elif n.clave < clave:
                n = n.der
            else:
                return n
        return None

    def contiene(self, clave):
        return self._nodo(clave) is not None

    def buscar(self, clave, defecto=None):
        n = self._nodo(clave)
        return defecto if n is None else n.valor

    def desde(self, clave=None):
        """Recorre (clave, valor) en orden, empezando en el primero >= clave.

        Sin clave, empieza en el menor. Usa una PILA explícita con los
        ancestros pendientes: bajar hasta el punto de partida cuesta O(log n)
        y cada elemento siguiente cuesta O(1) amortizado.

        No se debe modificar el árbol mientras se recorre.
        """
        pila = []
        n = self._raiz
        while n is not None:
            if clave is None or not (n.clave < clave):   # n.clave >= clave
                pila.append(n)
                n = n.izq
            else:
                n = n.der
        while pila:
            n = pila.pop()
            yield n.clave, n.valor
            m = n.der
            while m is not None:
                pila.append(m)
                m = m.izq

    # ------------------------------------------------------------ inserción

    def insertar(self, clave, valor=None):
        """Inserta la clave. Si ya existía, reemplaza el valor y devuelve False."""
        self._cambio = False
        self._raiz = self._insertar(self._raiz, clave, valor)
        if self._cambio:
            self._n += 1
        return self._cambio

    def _insertar(self, n, clave, valor):
        if n is None:
            self._cambio = True
            return _Nodo(clave, valor)
        if clave < n.clave:
            n.izq = self._insertar(n.izq, clave, valor)
        elif n.clave < clave:
            n.der = self._insertar(n.der, clave, valor)
        else:
            n.valor = valor
            return n
        return _balancear(n)

    # ------------------------------------------------------------ eliminación

    def eliminar(self, clave):
        """Elimina la clave. Devuelve True si existía."""
        self._cambio = False
        self._raiz = self._eliminar(self._raiz, clave)
        if self._cambio:
            self._n -= 1
        return self._cambio

    def _eliminar(self, n, clave):
        if n is None:
            return None
        if clave < n.clave:
            n.izq = self._eliminar(n.izq, clave)
        elif n.clave < clave:
            n.der = self._eliminar(n.der, clave)
        else:
            self._cambio = True
            if n.izq is None:
                return n.der
            if n.der is None:
                return n.izq
            # Dos hijos: se reemplaza por el sucesor (el menor del subárbol derecho).
            s = n.der
            while s.izq is not None:
                s = s.izq
            n.clave, n.valor = s.clave, s.valor
            n.der = self._quitar_minimo(n.der)
        return _balancear(n)

    def _quitar_minimo(self, n):
        if n.izq is None:
            return n.der
        n.izq = self._quitar_minimo(n.izq)
        return _balancear(n)

    # ------------------------------------------------------------ construcción

    def construir_desde_ordenados(self, claves, valores=None):
        """Reemplaza el contenido con un árbol perfectamente balanceado. O(n).

        `claves` debe venir ordenada y sin repetidos (por ejemplo, salida de
        merge_sort). Se toma el elemento del medio como raíz y se repite en
        cada mitad.
        """
        n = len(claves)
        for i in range(1, n):
            if not (claves[i - 1] < claves[i]):
                raise ValueError("las claves deben estar ordenadas y sin repetidos")
        self._raiz = self._construir(claves, valores, 0, n - 1)
        self._n = n

    def _construir(self, claves, valores, i, j):
        if i > j:
            return None
        m = (i + j) // 2
        nodo = _Nodo(claves[m], None if valores is None else valores[m])
        nodo.izq = self._construir(claves, valores, i, m - 1)
        nodo.der = self._construir(claves, valores, m + 1, j)
        _actualizar(nodo)
        return nodo

    # ------------------------------------------------------------ verificación

    def verificar(self):
        """Comprueba orden, alturas y balance de todo el árbol (para pruebas). O(n)."""
        cuenta = self._verificar(self._raiz, None, None)
        if cuenta != self._n:
            raise AssertionError("el tamaño guardado no coincide con los nodos")
        return True

    def _verificar(self, n, minimo, maximo):
        if n is None:
            return 0
        if minimo is not None and not (minimo < n.clave):
            raise AssertionError("orden roto en " + repr(n.clave))
        if maximo is not None and not (n.clave < maximo):
            raise AssertionError("orden roto en " + repr(n.clave))
        a, b = _altura(n.izq), _altura(n.der)
        if n.altura != 1 + (a if a > b else b):
            raise AssertionError("altura incorrecta en " + repr(n.clave))
        if a - b > 1 or b - a > 1:
            raise AssertionError("desbalance en " + repr(n.clave))
        return 1 + self._verificar(n.izq, minimo, n.clave) + self._verificar(n.der, n.clave, maximo)
