import random
import unittest

from motor import Red
from tests.apoyo import DATOS, MINI, foto, verificar_invariantes


class TestR9Mini(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_sin_historial(self):
        self.assertFalse(self.red.deshacer())
        self.assertFalse(self.red.rehacer())

    def test_orden_correcto(self):
        self.red.cerrar("ALFA")
        self.red.quitar_parada("R1", "BETA")
        self.red.agregar_parada("R1", "GAMA", "CALLE 1")
        self.assertTrue(self.red.deshacer())   # agregar
        self.assertEqual(self.red.recorrido("R1"), ["ALFA", "CALLE 1", "CALLE 2"])
        self.assertTrue(self.red.deshacer())   # quitar
        self.assertEqual(self.red.recorrido("R1"), ["ALFA", "BETA", "CALLE 1", "CALLE 2"])
        self.assertTrue(self.red.deshacer())   # cerrar
        self.assertEqual(self.red.estado("ALFA"), "ABIERTA")
        self.assertFalse(self.red.deshacer())
        self.assertTrue(self.red.rehacer())
        self.assertEqual(self.red.estado("ALFA"), "CERRADA")
        verificar_invariantes(self.red)

    def test_cambio_nuevo_borra_rehacer(self):
        self.red.cerrar("ALFA")
        self.red.deshacer()
        self.red.cerrar("BETA")
        self.assertFalse(self.red.rehacer())
        self.assertEqual(self.red.estado("ALFA"), "ABIERTA")

    def test_operacion_fallida_no_entra_al_historial(self):
        self.red.cerrar("ALFA")
        self.assertFalse(self.red.cerrar("ALFA"))
        self.assertFalse(self.red.quitar_parada("R1", "ECO"))
        self.assertTrue(self.red.deshacer())
        self.assertFalse(self.red.deshacer())

    def test_historial_para_la_interfaz(self):
        self.red.cerrar("ALFA")
        self.red.quitar_parada("R1", "BETA")
        self.red.deshacer()
        self.assertEqual(self.red.info_historial(), (["Cerrar ALFA"], ["Quitar BETA de R1"]))


class TestR9Aleatorio(unittest.TestCase):
    def test_10000_operaciones_y_deshacer_todo(self):
        """Invariante 6: tras cualquier secuencia y deshacer todo, la red es la original."""
        red = Red(DATOS)
        original = foto(red)
        rnd = random.Random(99)
        estaciones = red.lista_estaciones()
        rutas = red.lista_rutas()
        cambios = 0
        for paso in range(10000):
            op = rnd.random()
            if op < 0.2:
                ok = red.cerrar(rnd.choice(estaciones))
            elif op < 0.35:
                ok = red.reabrir(rnd.choice(estaciones))
            elif op < 0.55:
                ruta = rnd.choice(rutas)
                rec = red.recorrido(ruta)
                ok = bool(rec) and red.agregar_parada(ruta, rnd.choice(estaciones), rnd.choice(rec))
            elif op < 0.75:
                ruta = rnd.choice(rutas)
                rec = red.recorrido(ruta)
                ok = bool(rec) and red.quitar_parada(ruta, rnd.choice(rec))
            elif op < 0.9:
                ok = red.deshacer()
                if ok:
                    cambios -= 1
                continue
            else:
                ok = red.rehacer()
                if ok:
                    cambios += 1
                continue
            if ok:
                cambios += 1
            if paso % 1000 == 0:
                verificar_invariantes(red)
        verificar_invariantes(red)
        while red.deshacer():
            cambios -= 1
        self.assertEqual(cambios, 0)
        self.assertEqual(foto(red), original)
        verificar_invariantes(red)


if __name__ == "__main__":
    unittest.main()
