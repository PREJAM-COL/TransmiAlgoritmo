"""Verifica el contrato exacto del motor (diapositiva 11).

Un nombre o una firma distinta cuenta como requisito no hecho, así que esta
prueba compara los parámetros de cada método con los de la presentación.
"""

import inspect
import os
import unittest

import motor
from motor import Red, simular_fila

DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")

CONTRATO = [
    ("estado", ["nombre"]),
    ("autocompletar", ["prefijo", "k"]),
    ("rango", ["desde", "hasta"]),
    ("proximo_bus", ["estacion", "ruta", "hora"]),
    ("viaje", ["origen", "destino"]),
    ("ranking", ["k"]),
    ("agregar_parada", ["ruta", "nueva", "despues_de"]),
    ("quitar_parada", ["ruta", "estacion"]),
    ("recorrido", ["ruta", "al_reves"]),
    ("cerrar", ["nombre"]),
    ("reabrir", ["nombre"]),
    ("deshacer", []),
    ("rehacer", []),
]


class TestContrato(unittest.TestCase):
    def test_exporta_red_y_simular_fila(self):
        self.assertTrue(inspect.isclass(Red))
        self.assertTrue(inspect.isfunction(simular_fila))
        self.assertIs(motor.Red, Red)

    def test_constructor(self):
        params = list(inspect.signature(Red.__init__).parameters)
        self.assertEqual(params, ["self", "carpeta"])

    def test_firmas_de_red(self):
        for nombre, esperados in CONTRATO:
            with self.subTest(metodo=nombre):
                self.assertTrue(hasattr(Red, nombre), "falta Red." + nombre)
                params = list(inspect.signature(getattr(Red, nombre)).parameters)
                self.assertEqual(params, ["self"] + esperados)

    def test_recorrido_al_reves_por_defecto_false(self):
        p = inspect.signature(Red.recorrido).parameters["al_reves"]
        self.assertIs(p.default, False)

    def test_firma_simular_fila(self):
        params = list(inspect.signature(simular_fila).parameters)
        self.assertEqual(params, ["llegadas", "frecuencia", "capacidad"])

    def test_se_puede_crear_con_los_datos(self):
        red = Red(DATOS)
        self.assertIsNotNone(red)


if __name__ == "__main__":
    unittest.main()
