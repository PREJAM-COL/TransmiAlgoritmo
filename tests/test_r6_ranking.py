import unittest

from motor import Red
from tests.apoyo import nombres, DATOS, MINI, requiere


class TestR6Ranking(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_orden_y_desempate_alfabetico(self):
        # ALFA 4; BETA, CALLE 2, ECO con 3 (alfabético); DELTA 2; CALLE 1 y FOXTROT 1; CALLE 10 y GAMA 0
        self.assertEqual(nombres(self.red.ranking(9)), ["ALFA", "BETA", "CALLE 2", "ECO", "DELTA",
                                               "CALLE 1", "FOXTROT", "CALLE 10", "GAMA"])

    def test_k_borde(self):
        self.assertEqual(nombres(self.red.ranking(0)), [])
        self.assertEqual(self.red.ranking(-1), [])
        self.assertEqual(len(self.red.ranking(100)), 9)

    @requiere("edicion", "comandos")
    def test_quitar_parada_resta_sus_buses(self):
        self.red.quitar_parada("R1", "ALFA")       # ALFA pierde 3 buses: queda con 1
        self.assertEqual(nombres(self.red.ranking(2)), ["BETA", "CALLE 2"])
        self.red.deshacer()
        self.assertEqual(nombres(self.red.ranking(1)), ["ALFA"])

    def test_red_real(self):
        red = Red(DATOS)
        self.assertEqual(nombres(red.ranking(5)), ["RICAURTE", "PORTAL NORTE", "BANDERAS", "AV. JIMENEZ", "PORTAL AMERICAS"])
        todas = sorted(red._por_id, key=lambda e: (-e.buses_dia, e.nombre))
        self.assertEqual(nombres(red.ranking(147)), [e.nombre for e in todas])

    def test_formato_nombre_y_buses(self):
        r = self.red.ranking(2)
        self.assertEqual(r[0], ("ALFA", 4))
        self.assertIsInstance(r[0], tuple)
        self.assertEqual([b for _, b in self.red.ranking(9)], [4, 3, 3, 3, 2, 1, 1, 0, 0])


if __name__ == "__main__":
    unittest.main()
