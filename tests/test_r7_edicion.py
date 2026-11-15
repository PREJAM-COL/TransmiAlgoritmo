import unittest

from motor import Red
from tests.apoyo import MINI, verificar_invariantes


class TestR7Edicion(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_recorrido_en_ambos_sentidos(self):
        self.assertEqual(self.red.recorrido("R1"), ["ALFA", "BETA", "CALLE 1", "CALLE 2"])
        self.assertEqual(self.red.recorrido("R1", al_reves=True), ["CALLE 2", "CALLE 1", "BETA", "ALFA"])
        self.assertEqual(self.red.recorrido("NO EXISTE"), [])

    def test_agregar_en_medio_y_al_final(self):
        self.assertTrue(self.red.agregar_parada("R1", "GAMA", "BETA"))
        self.assertEqual(self.red.recorrido("R1"), ["ALFA", "BETA", "GAMA", "CALLE 1", "CALLE 2"])
        self.assertTrue(self.red.agregar_parada("R1", "ECO", "CALLE 2"))
        self.assertEqual(self.red.recorrido("R1")[-1], "ECO")
        self.assertIn("R1", self.red.info_estacion("GAMA")[2])
        verificar_invariantes(self.red)

    def test_agregar_invalido(self):
        self.assertFalse(self.red.agregar_parada("R1", "BETA", "ALFA"))     # ya está en la ruta
        self.assertFalse(self.red.agregar_parada("R1", "GAMA", "ECO"))      # despues_de no está en la ruta
        self.assertFalse(self.red.agregar_parada("NO", "GAMA", "ALFA"))     # ruta no existe
        self.assertFalse(self.red.agregar_parada("R1", "ZETA", "ALFA"))     # estación no existe
        self.assertEqual(self.red.recorrido("R1"), ["ALFA", "BETA", "CALLE 1", "CALLE 2"])

    def test_quitar_primero_medio_ultimo(self):
        self.assertTrue(self.red.quitar_parada("R1", "ALFA"))
        self.assertTrue(self.red.quitar_parada("R1", "CALLE 1"))
        self.assertTrue(self.red.quitar_parada("R1", "CALLE 2"))
        self.assertEqual(self.red.recorrido("R1"), ["BETA"])
        self.assertNotIn("R1", self.red.info_estacion("ALFA")[2])
        verificar_invariantes(self.red)

    def test_quitar_invalido(self):
        self.assertFalse(self.red.quitar_parada("R1", "ECO"))
        self.assertFalse(self.red.quitar_parada("NO", "ALFA"))

    def test_estacion_cerrada_se_puede_agregar(self):
        self.red.cerrar("GAMA")
        self.assertTrue(self.red.agregar_parada("R2", "GAMA", "DELTA"))
        verificar_invariantes(self.red)


if __name__ == "__main__":
    unittest.main()
