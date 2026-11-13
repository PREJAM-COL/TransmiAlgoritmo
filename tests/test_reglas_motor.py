"""Validador de las reglas del motor (diapositiva 10).

Recorre el árbol sintáctico (módulo ast) de cada archivo .py dentro de motor/
y falla si encuentra algo prohibido. Es un seguro: un requisito que usa algo
prohibido pierde los puntos de resultados y de rendimiento.

Qué detecta:
  - Nombres prohibidos: dict, set, frozenset, sorted, min, max, vars, globals, locals
  - Literales y comprensiones de diccionario o conjunto: {}, {1, 2}, {k: v ...}, {x ...}
  - Llamadas a .sort(), .index(), .count(), .__dict__
  - Comparaciones con `in` / `not in` (en motor/ buscamos con nuestras estructuras;
    `for x in lista` es otra cosa y sí está permitido)
  - Parámetros **kwargs (crean un dict)
  - Imports que no sean csv, time, random o del propio paquete motor

Si algún día un uso es legítimo (por ejemplo `"x" in cadena`, que el profesor
permite con str), se agrega a EXCEPCIONES con el archivo, la línea y el motivo,
para que la excepción quede revisada y documentada.
"""

import ast
import os
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "motor")

NOMBRES_PROHIBIDOS = {"dict", "set", "frozenset", "sorted", "min", "max", "vars", "globals", "locals"}
ATRIBUTOS_PROHIBIDOS = {"sort", "index", "count", "__dict__"}
MODULOS_PERMITIDOS = {"csv", "time", "random"}

# (ruta relativa a motor/, línea): motivo
EXCEPCIONES = {}


def revisar_codigo(codigo, nombre="<codigo>"):
    """Devuelve una lista de (línea, mensaje) con cada violación encontrada."""
    arbol = ast.parse(codigo, filename=nombre)
    hallazgos = []

    for nodo in ast.walk(arbol):
        linea = getattr(nodo, "lineno", 0)

        if isinstance(nodo, ast.Name) and nodo.id in NOMBRES_PROHIBIDOS:
            hallazgos.append((linea, "nombre prohibido: " + nodo.id))

        elif isinstance(nodo, (ast.Dict, ast.DictComp)):
            hallazgos.append((linea, "diccionario literal o comprensión de diccionario"))

        elif isinstance(nodo, (ast.Set, ast.SetComp)):
            hallazgos.append((linea, "conjunto literal o comprensión de conjunto"))

        elif isinstance(nodo, ast.Attribute) and nodo.attr in ATRIBUTOS_PROHIBIDOS:
            hallazgos.append((linea, "atributo prohibido: ." + nodo.attr))

        elif isinstance(nodo, ast.Compare):
            for op in nodo.ops:
                if isinstance(op, (ast.In, ast.NotIn)):
                    hallazgos.append((linea, "comparación con 'in' (usar las estructuras propias)"))

        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if nodo.args.kwarg is not None:
                hallazgos.append((linea, "parámetro **kwargs (crea un dict)"))

        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                base = alias.name.split(".")[0]
                if base not in MODULOS_PERMITIDOS and base != "motor":
                    hallazgos.append((linea, "import no permitido: " + alias.name))

        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level == 0:
                base = (nodo.module or "").split(".")[0]
                if base not in MODULOS_PERMITIDOS and base != "motor":
                    hallazgos.append((linea, "import no permitido: " + (nodo.module or "")))

    return hallazgos


def archivos_motor():
    for carpeta, _, archivos in os.walk(RAIZ):
        for a in archivos:
            if a.endswith(".py"):
                yield os.path.join(carpeta, a)


class TestReglasMotor(unittest.TestCase):
    def test_motor_sin_construcciones_prohibidas(self):
        errores = []
        for ruta in archivos_motor():
            rel = os.path.relpath(ruta, RAIZ).replace(os.sep, "/")
            with open(ruta, encoding="utf-8") as f:
                codigo = f.read()
            for linea, msg in revisar_codigo(codigo, rel):
                if (rel, linea) not in EXCEPCIONES:
                    errores.append("motor/%s:%d  %s" % (rel, linea, msg))
        self.assertEqual(errores, [], "\n" + "\n".join(errores))

    def test_el_validador_detecta_lo_prohibido(self):
        """Prueba del propio validador: cada línea debe producir un hallazgo."""
        malos = [
            "x = dict()",
            "x = {}",
            "x = {1, 2}",
            "x = {k: 1 for k in y}",
            "x = {k for k in y}",
            "y = sorted(x)",
            "x.sort()",
            "i = x.index(3)",
            "c = x.count(3)",
            "m = max(x)",
            "b = 3 in x",
            "b = 3 not in x",
            "def f(**kw): pass",
            "import heapq",
            "from collections import deque",
            "import functools",
            "import bisect",
        ]
        for codigo in malos:
            with self.subTest(codigo=codigo):
                self.assertNotEqual(revisar_codigo(codigo), [], codigo)

    def test_el_validador_acepta_lo_permitido(self):
        buenos = [
            "for x in lista: pass",
            "y = [x for x in lista]",
            "import csv, time, random",
            "from .estructuras.pila import Pila",
            "from motor.estructuras import avl",
            "t = (1, 'a')",
            "s = 'CALLE'.startswith('CAL')",
            "a = [None] * 8",
        ]
        for codigo in buenos:
            with self.subTest(codigo=codigo):
                self.assertEqual(revisar_codigo(codigo), [], codigo)


if __name__ == "__main__":
    unittest.main()
