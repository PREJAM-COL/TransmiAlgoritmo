"""La app web carga el motor en Pyodide copiando una lista fija de archivos.
Si alguien agrega un módulo a motor/ y olvida agregarlo a la lista, la app
fallaría solo en el navegador. Esta prueba lo detecta antes. También prueba
el puente con la red real."""

import json
import os
import re
import unittest

import sys

from tests.apoyo import DATOS, RAIZ

sys.path.insert(0, os.path.join(RAIZ, "web", "python"))
import puente  # noqa: E402  (el lado Python del front, en web/python/)


class TestWeb(unittest.TestCase):
    def test_worker_copia_todo_el_motor(self):
        with open(os.path.join(RAIZ, "web", "js", "motor-worker.js"), encoding="utf-8") as f:
            listados = set(re.findall(r"'([\w/]+\.(?:py|csv))'", f.read()))
        necesarios = set()
        for carpeta in ("motor", os.path.join("web", "python")):
            for base, _, archivos in os.walk(os.path.join(RAIZ, carpeta)):
                for a in archivos:
                    if a.endswith(".py"):
                        necesarios.add(os.path.relpath(os.path.join(base, a), RAIZ).replace(os.sep, "/"))
        self.assertEqual(sorted(necesarios - listados), [])

    def test_worker_copia_todas_las_pruebas(self):
        with open(os.path.join(RAIZ, "web", "js", "motor-worker.js"), encoding="utf-8") as f:
            listados = set(re.findall(r"'([\w/.-]+\.(?:py|csv|js|txt))'", f.read()))
        necesarios = set()
        for base, _, archivos in os.walk(os.path.join(RAIZ, "tests")):
            for a in archivos:
                if a.endswith((".py", ".csv", ".txt")):
                    necesarios.add(os.path.relpath(os.path.join(base, a), RAIZ).replace(os.sep, "/"))
        self.assertEqual(sorted(necesarios - listados), [])

    def test_puente(self):
        r = json.loads(puente.llamar("iniciar", json.dumps([DATOS])))
        self.assertTrue(r["ok"])
        self.assertEqual(r["datos"]["estaciones"], 147)
        it = json.loads(puente.llamar("itinerario", json.dumps(["PORTAL AMERICAS", "CALLE 100", "07:40"])))["datos"]
        self.assertEqual([t["ruta"] for t in it["tramos"]], ["E32", "B44-1"])
        self.assertEqual(it["tramos"][0]["sale"], "07:45")
        self.assertGreater(len(json.loads(puente.llamar("flota", "[460]"))["datos"]), 0)
        error = json.loads(puente.llamar("no_existe", "[]"))
        self.assertFalse(error["ok"])


if __name__ == "__main__":
    unittest.main()
