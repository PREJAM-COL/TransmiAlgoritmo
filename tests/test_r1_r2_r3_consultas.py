import unittest

from motor import Red
from tests.apoyo import DATOS, MINI, requiere


class TestR1Estado(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_existe_y_abierta(self):
        self.assertEqual(self.red.estado("ALFA"), "ABIERTA")

    def test_no_existe(self):
        self.assertEqual(self.red.estado("ZETA"), "NO EXISTE")
        self.assertEqual(self.red.estado(""), "NO EXISTE")
        self.assertEqual(self.red.estado("alfa"), "NO EXISTE")      # nombre exacto
        self.assertEqual(self.red.estado(None), "NO EXISTE")

    @requiere("cierres")
    def test_cerrada(self):
        self.red.cerrar("ALFA")
        self.assertEqual(self.red.estado("ALFA"), "CERRADA")


class TestR2Autocompletar(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_prefijo_y_orden(self):
        self.assertEqual(self.red.autocompletar("CALLE", 10), ["CALLE 1", "CALLE 10", "CALLE 2"])
        self.assertEqual(self.red.autocompletar("CALLE 1", 5), ["CALLE 1", "CALLE 10"])

    def test_limite_k(self):
        self.assertEqual(self.red.autocompletar("CALLE", 2), ["CALLE 1", "CALLE 10"])
        self.assertEqual(self.red.autocompletar("CALLE", 0), [])
        self.assertEqual(self.red.autocompletar("CALLE", -3), [])

    def test_prefijo_vacio_da_las_primeras(self):
        self.assertEqual(self.red.autocompletar("", 3), ["ALFA", "BETA", "CALLE 1"])

    def test_sin_resultados(self):
        self.assertEqual(self.red.autocompletar("Z", 5), [])
        self.assertEqual(self.red.autocompletar("cal", 5), [])
        self.assertEqual(self.red.autocompletar("CALLE 3", 5), [])

    @requiere("cierres")
    def test_no_muestra_cerradas(self):
        self.red.cerrar("CALLE 10")
        self.assertEqual(self.red.autocompletar("CALLE", 5), ["CALLE 1", "CALLE 2"])

    def test_red_real(self):
        red = Red(DATOS)
        self.assertEqual(red.autocompletar("CAL", 3), ["CALLE 100", "CALLE 106", "CALLE 127"])
        todas = red.lista_estaciones()
        for p in ["P", "PORTAL", "SAN", "AV.", "X"]:
            esperado = [n for n in todas if n.startswith(p)][:4]
            self.assertEqual(red.autocompletar(p, 4), esperado, p)


class TestR3Rango(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_ambos_extremos_incluidos(self):
        self.assertEqual(self.red.rango("BETA", "CALLE 2"), ["BETA", "CALLE 1", "CALLE 10", "CALLE 2"])
        self.assertEqual(self.red.rango("ECO", "ECO"), ["ECO"])

    def test_extremos_que_no_existen(self):
        self.assertEqual(self.red.rango("B", "D"), ["BETA", "CALLE 1", "CALLE 10", "CALLE 2"])

    def test_rango_invertido(self):
        self.assertEqual(self.red.rango("ECO", "ALFA"), [])

    @requiere("cierres")
    def test_no_muestra_cerradas(self):
        self.red.cerrar("CALLE 1")
        self.assertEqual(self.red.rango("C", "D"), ["CALLE 10", "CALLE 2"])

    def test_red_real_ejemplo_presentacion(self):
        red = Red(DATOS)
        r = red.rango("CALLE 26", "CALLE 80")
        self.assertEqual(r[0], "CALLE 26")
        self.assertEqual(r[-1], "CALLE 76")
        self.assertEqual(r, [n for n in red.lista_estaciones() if "CALLE 26" <= n <= "CALLE 80"])


if __name__ == "__main__":
    unittest.main()
