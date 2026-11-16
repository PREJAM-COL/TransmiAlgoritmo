import unittest

from motor import Red
from tests.apoyo import MINI, requiere, verificar_invariantes


class TestR8Cierres(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_cerrar_y_reabrir(self):
        self.assertTrue(self.red.cerrar("ALFA"))
        self.assertEqual(self.red.estado("ALFA"), "cerrada")
        verificar_invariantes(self.red)
        self.assertTrue(self.red.reabrir("ALFA"))
        self.assertEqual(self.red.estado("ALFA"), "abierta")
        verificar_invariantes(self.red)

    def test_cambios_sin_efecto_devuelven_false(self):
        self.assertFalse(self.red.reabrir("ALFA"))       # ya está abierta
        self.assertFalse(self.red.cerrar("ZETA"))        # no existe
        self.assertFalse(self.red.reabrir("ZETA"))
        self.red.cerrar("ALFA")
        self.assertFalse(self.red.cerrar("ALFA"))        # ya está cerrada

    def test_no_aparece_en_ninguna_consulta(self):
        self.red.cerrar("ALFA")
        self.assertEqual(self.red.autocompletar("A", 5), [])
        self.assertNotIn("ALFA", self.red.rango("A", "Z"))
        self.assertNotIn("ALFA", self.red.ranking(20))
        self.assertIsNone(self.red.proximo_bus("ALFA", "R1", "06:00"))

    @requiere("viaje")
    def test_nadie_sube_baja_ni_transborda(self):
        self.red.cerrar("ALFA")
        self.assertIsNone(self.red.viaje("ALFA", "BETA"))
        self.assertIsNone(self.red.viaje("BETA", "ALFA"))
        self.red.reabrir("ALFA")
        self.red.cerrar("DELTA")
        # BETA -> ECO transbordaba en DELTA; ahora debe ir por CALLE 2 (DELTA cuenta como parada)
        self.assertEqual(self.red.viaje("BETA", "ECO"),
                         [("R1", "BETA", "CALLE 2"), ("R2", "CALLE 2", "ECO")])

    def test_ranking_se_actualiza(self):
        self.assertEqual(self.red.ranking(1), ["ALFA"])
        self.red.cerrar("ALFA")
        self.assertEqual(self.red.ranking(1), ["BETA"])
        self.red.reabrir("ALFA")
        self.assertEqual(self.red.ranking(1), ["ALFA"])


if __name__ == "__main__":
    unittest.main()
