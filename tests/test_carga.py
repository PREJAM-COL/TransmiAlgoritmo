import time
import unittest

from motor import Red
from tests.apoyo import DATOS, MINI, requiere, verificar_invariantes


class TestCargaMini(unittest.TestCase):
    """La mini red trae filas desordenadas, repetidas e inválidas a propósito."""

    @classmethod
    def setUpClass(cls):
        cls.red = Red(MINI)

    def test_estaciones_sin_repetidos_ni_vacios(self):
        self.assertEqual(len(self.red._por_id), 9)
        self.assertEqual(self.red.lista_estaciones(),
                         ["ALFA", "BETA", "CALLE 1", "CALLE 10", "CALLE 2", "DELTA", "ECO", "FOXTROT", "GAMA"])

    @requiere('edicion')
    def test_rutas_ordenadas_por_orden_no_por_archivo(self):
        self.assertEqual(self.red.lista_rutas(), ["R1", "R2", "R3", "R4", "R5"])
        self.assertEqual(self.red.recorrido("R1"), ["ALFA", "BETA", "CALLE 1", "CALLE 2"])

    def test_horas_ordenadas_y_mayores_a_24(self):
        self.assertEqual(self.red.info_horas("R1", "ALFA"), [330, 360, 1430])     # 05:30, 06:00, 23:50
        self.assertEqual(self.red.info_horas("R2", "ECO"), [70, 430])             # 25:10 -> 01:10
        self.assertEqual(self.red.info_horas("R1", "BETA"), [365, 365])           # repetidos se cuentan

    def test_buses_dia(self):
        esperado = {"ALFA": 4, "BETA": 3, "CALLE 1": 1, "CALLE 10": 0, "CALLE 2": 3,
                    "DELTA": 2, "ECO": 3, "FOXTROT": 1, "GAMA": 0}
        for nombre, buses in esperado.items():
            self.assertEqual(self.red.info_estacion(nombre)[1], buses, nombre)

    def test_filas_invalidas_se_cuentan(self):
        # 1 en estaciones (ALFA repetida; la línea vacía se salta sin contarse),
        # 2 en rutas, 3 en horarios
        self.assertEqual(self.red.info_advertencias(), 6)

    def test_invariantes(self):
        verificar_invariantes(self.red)


class TestCargaReal(unittest.TestCase):
    def test_red_real(self):
        t = time.perf_counter()
        red = Red(DATOS)
        segundos = time.perf_counter() - t
        self.assertLess(segundos, 3.0)            # criterio: < 1 s en CPython (holgura para equipos lentos)
        self.assertEqual(len(red._por_id), 147)
        self.assertEqual(len(red.lista_rutas()), 181)
        self.assertEqual(len(red._paradas), 1927)
        self.assertEqual(sum(e.buses_dia for e in red._por_id), 140492)
        self.assertEqual(red.info_advertencias(), 0)
        verificar_invariantes(red)

    def test_carpeta_con_barra_final(self):
        self.assertEqual(Red(MINI + "/").info_estacion("ALFA")[1], 4)


if __name__ == "__main__":
    unittest.main()
