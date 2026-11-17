import bisect
import random
import unittest

from motor import Red
from motor.horarios import formato, minutos
from tests.apoyo import DATOS, MINI, requiere


class TestHoras(unittest.TestCase):
    def test_minutos(self):
        self.assertEqual(minutos("00:00"), 0)
        self.assertEqual(minutos("07:05"), 425)
        self.assertEqual(minutos("7:05"), 425)
        self.assertEqual(minutos("23:59"), 1439)
        self.assertEqual(minutos("25:10"), 70)
        for malo in ["", "7", "07:5", "07:60", "aa:bb", "07:05:00", None, 705]:
            self.assertEqual(minutos(malo), -1, malo)

    def test_formato(self):
        self.assertEqual(formato(0), "00:00")
        self.assertEqual(formato(425), "07:05")
        self.assertEqual(formato(1439), "23:59")


class TestR4ProximoBus(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)          # R1 en ALFA: 05:30, 06:00, 23:50

    def test_siguiente_e_igual(self):
        self.assertEqual(self.red.proximo_bus("ALFA", "R1", "05:00"), "05:30")
        self.assertEqual(self.red.proximo_bus("ALFA", "R1", "06:00"), "06:00")   # a la misma hora sí alcanza
        self.assertEqual(self.red.proximo_bus("ALFA", "R1", "06:01"), "23:50")

    def test_sin_mas_buses_ese_dia(self):
        self.assertIsNone(self.red.proximo_bus("ALFA", "R1", "23:51"))   # ya pasó el último
        self.assertIsNone(self.red.proximo_bus("ECO", "R2", "08:00"))
        self.assertEqual(self.red.proximo_bus("ECO", "R2", "00:00"), "01:10")

    def test_casos_none(self):
        self.assertIsNone(self.red.proximo_bus("ZETA", "R1", "06:00"))   # estación no existe
        self.assertIsNone(self.red.proximo_bus("ALFA", "R2", "06:00"))   # la ruta no para ahí
        self.assertIsNone(self.red.proximo_bus("ALFA", "NO", "06:00"))   # ruta no existe
        self.assertIsNone(self.red.proximo_bus("ALFA", "R1", "6 am"))    # hora inválida

    @requiere("cierres")
    def test_cerrada_no_da_bus(self):
        self.red.cerrar("ALFA")
        self.assertIsNone(self.red.proximo_bus("ALFA", "R1", "06:00"))

    @requiere("edicion", "comandos")
    def test_parada_nueva_sin_horarios(self):
        self.red.agregar_parada("R3", "ECO", "DELTA")
        self.assertIsNone(self.red.proximo_bus("ECO", "R3", "06:00"))

    @requiere("edicion")
    def test_red_real_contra_bisect(self):
        red = Red(DATOS)
        rnd = random.Random(4)
        rutas = red.lista_rutas()
        for _ in range(500):
            ruta = rnd.choice(rutas)
            est = rnd.choice(red.recorrido(ruta))
            m = rnd.randrange(1440)
            horas = red.info_horas(ruta, est)
            i = bisect.bisect_left(horas, m)
            esperado = formato(horas[i]) if i < len(horas) else None
            self.assertEqual(red.proximo_bus(est, ruta, formato(m)), esperado)


if __name__ == "__main__":
    unittest.main()
