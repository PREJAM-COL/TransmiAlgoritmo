"""Tabla hash propia con direccionamiento abierto (docs/fase-2-diseno.md §3.1).

Es nuestro reemplazo de dict dentro de motor/. Se usa para R1 (estado de una
estación), para encontrar rutas y paradas en O(1) (R4, R7) y como índice
general.

Cómo funciona
-------------
1. La función hash convierte la clave en un entero: h = h*31 + código de cada
   carácter, y luego se "mezclan" los bits para que claves parecidas
   ("CALLE 26", "CALLE 72") no caigan en casillas vecinas.
2. La casilla inicial es h & (capacidad - 1). Como la capacidad es potencia
   de 2, eso equivale a h % capacidad pero es más barato.
3. Si la casilla está ocupada por otra clave (colisión), se prueba la
   siguiente (sondeo lineal) hasta encontrar la clave o una casilla vacía.
4. Al borrar se deja una LÁPIDA en vez de vaciar la casilla: si se vaciara,
   se cortaría la cadena de sondeo y otras claves dejarían de encontrarse.
5. Cuando (ocupadas + lápidas) supera el 70 % de la capacidad, se reconstruye
   la tabla (más grande si hace falta) y desaparecen las lápidas.

Tres arreglos paralelos (claves, valores, estado) en vez de una lista de
tuplas: menos objetos en memoria.

Complejidad (n = elementos):
    obtener, contiene, quitar: O(1) esperado; O(n) en el peor caso (todas
        las claves colisionan, muy improbable con la mezcla de bits)
    poner: O(1) amortizado (cada redimensionamiento cuesta O(n), pero ocurre
        cada vez que la tabla duplica su tamaño)
    espacio: O(n)
"""

_VACIA = 0
_OCUPADA = 1
_LAPIDA = 2

_MASCARA32 = 0xFFFFFFFF
_CARGA_MAX_NUM = 7      # se reconstruye si (ocupadas + lápidas) / capacidad > 7/10
_CARGA_MAX_DEN = 10


def hash_cadena(texto):
    """Hash polinomial de 32 bits con mezcla final (fmix32 de MurmurHash3)."""
    h = 0
    for c in texto:
        h = (h * 31 + ord(c)) & _MASCARA32
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & _MASCARA32
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & _MASCARA32
    h ^= h >> 16
    return h


def hash_entero(x):
    h = x & _MASCARA32
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & _MASCARA32
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & _MASCARA32
    h ^= h >> 16
    return h


def _hash(clave):
    if isinstance(clave, str):
        return hash_cadena(clave)
    if isinstance(clave, int):
        return hash_entero(clave)
    raise TypeError("TablaHash solo acepta claves str o int")


class TablaHash:
    __slots__ = ("_claves", "_valores", "_estado", "_ocupadas", "_lapidas")

    def __init__(self, capacidad=8):
        cap = 8
        while cap < capacidad:
            cap *= 2
        self._reiniciar(cap)

    def _reiniciar(self, cap):
        self._claves = [None] * cap
        self._valores = [None] * cap
        self._estado = [_VACIA] * cap
        self._ocupadas = 0
        self._lapidas = 0

    def __len__(self):
        return self._ocupadas

    @property
    def capacidad(self):
        return len(self._estado)

    # ------------------------------------------------------------ búsqueda

    def _posicion(self, clave):
        """Índice de la casilla que guarda `clave`, o -1 si no está."""
        mascara = len(self._estado) - 1
        i = _hash(clave) & mascara
        estado, claves = self._estado, self._claves
        # Termina porque la carga nunca llega a 100 %: siempre hay una casilla vacía.
        while estado[i] != _VACIA:
            if estado[i] == _OCUPADA and claves[i] == clave:
                return i
            i = (i + 1) & mascara
        return -1

    def obtener(self, clave, defecto=None):
        i = self._posicion(clave)
        return defecto if i < 0 else self._valores[i]

    def contiene(self, clave):
        return self._posicion(clave) >= 0

    # ------------------------------------------------------------ cambios

    def poner(self, clave, valor):
        """Inserta o reemplaza. Devuelve True si la clave era nueva."""
        mascara = len(self._estado) - 1
        i = _hash(clave) & mascara
        estado, claves = self._estado, self._claves
        primera_lapida = -1
        while estado[i] != _VACIA:
            if estado[i] == _OCUPADA:
                if claves[i] == clave:
                    self._valores[i] = valor
                    return False
            elif primera_lapida < 0:
                primera_lapida = i
            i = (i + 1) & mascara

        # La clave no está: se reutiliza la primera lápida del camino, si hubo.
        if primera_lapida >= 0:
            i = primera_lapida
            self._lapidas -= 1
        claves[i] = clave
        self._valores[i] = valor
        estado[i] = _OCUPADA
        self._ocupadas += 1

        if (self._ocupadas + self._lapidas) * _CARGA_MAX_DEN > len(estado) * _CARGA_MAX_NUM:
            self._redimensionar()
        return True

    def quitar(self, clave):
        """Elimina la clave. Devuelve True si existía."""
        i = self._posicion(clave)
        if i < 0:
            return False
        self._claves[i] = None
        self._valores[i] = None
        self._estado[i] = _LAPIDA
        self._ocupadas -= 1
        self._lapidas += 1
        return True

    def _redimensionar(self):
        """Reconstruye sin lápidas, con capacidad tal que la carga quede <= 50 %."""
        cap = 8
        while self._ocupadas * 2 > cap:
            cap *= 2
        claves, valores, estado = self._claves, self._valores, self._estado
        self._reiniciar(cap)
        for i in range(len(estado)):
            if estado[i] == _OCUPADA:
                self.poner(claves[i], valores[i])

    # ------------------------------------------------------------ recorridos

    def claves(self):
        """Recorre las claves (sin orden definido). O(capacidad)."""
        for i in range(len(self._estado)):
            if self._estado[i] == _OCUPADA:
                yield self._claves[i]

    def elementos(self):
        """Recorre los pares (clave, valor) (sin orden definido). O(capacidad)."""
        for i in range(len(self._estado)):
            if self._estado[i] == _OCUPADA:
                yield self._claves[i], self._valores[i]

    # ------------------------------------------------------------ métricas

    def estadisticas(self):
        """Datos para el panel de rendimiento y el inspector de la interfaz.

        Devuelve (elementos, lápidas, capacidad, sondeo más largo, sondeo promedio).
        """
        mascara = len(self._estado) - 1
        mas_largo = 0
        total = 0
        for i in range(len(self._estado)):
            if self._estado[i] == _OCUPADA:
                ideal = _hash(self._claves[i]) & mascara
                d = (i - ideal) & mascara
                total += d + 1
                if d + 1 > mas_largo:
                    mas_largo = d + 1
        promedio = total / self._ocupadas if self._ocupadas else 0.0
        return self._ocupadas, self._lapidas, len(self._estado), mas_largo, promedio
