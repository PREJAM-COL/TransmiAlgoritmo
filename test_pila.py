import unittest

from motor.estructuras.pila import Pila


class TestPila(unittest.TestCase):
    def test_lifo(self):
        p = Pila()
        for x in [1, 2, 3]:
            p.apilar(x)
        self.assertEqual(len(p), 3)
        self.assertEqual(p.cima(), 3)
        self.assertEqual([p.desapilar(), p.desapilar(), p.desapilar()], [3, 2, 1])
        self.assertTrue(p.vacia())

    def test_vacia_lanza_error(self):
        p = Pila()
        with self.assertRaises(IndexError):
            p.desapilar()
        with self.assertRaises(IndexError):
            p.cima()

    def test_vaciar(self):
        p = Pila()
        p.apilar("a")
        p.apilar("b")
        p.vaciar()
        self.assertTrue(p.vacia())
        self.assertEqual(len(p), 0)

    def test_elementos_es_copia(self):
        p = Pila()
        p.apilar(1)
        p.apilar(2)
        e = p.elementos()
        self.assertEqual(e, [1, 2])
        e.append(99)
        self.assertEqual(len(p), 2)

    def test_muchos(self):
        p = Pila()
        for i in range(100000):
            p.apilar(i)
        for i in range(99999, -1, -1):
            self.assertEqual(p.desapilar(), i)


if __name__ == "__main__":
    unittest.main()
