import random
import unittest

from motor.estructuras.cola_circular import ColaCircular


class TestColaCircular(unittest.TestCase):
    def test_fifo(self):
        c = ColaCircular()
        for x in "ABC":
            c.encolar(x)
        self.assertEqual(c.frente(), "A")
        self.assertEqual([c.desencolar() for _ in range(3)], ["A", "B", "C"])
        self.assertTrue(c.vacia())

    def test_vacia_lanza_error(self):
        c = ColaCircular()
        with self.assertRaises(IndexError):
            c.desencolar()
        with self.assertRaises(IndexError):
            c.frente()

    def test_da_la_vuelta_y_crece(self):
        c = ColaCircular(4)
        for x in range(3):
            c.encolar(x)
        c.desencolar()
        c.desencolar()          # cabeza avanzó; lo siguiente da la vuelta al arreglo
        for x in range(3, 10):  # obliga a crecer con la cabeza en medio
            c.encolar(x)
        self.assertEqual([c.desencolar() for _ in range(len(c))], list(range(2, 10)))

    def test_aleatorio_contra_lista(self):
        rnd = random.Random(3)
        c, ref = ColaCircular(2), []
        for i in range(20000):
            if ref and rnd.random() < 0.45:
                self.assertEqual(c.desencolar(), ref.pop(0))
            else:
                c.encolar(i)
                ref.append(i)
            self.assertEqual(len(c), len(ref))

    def test_un_millon(self):
        c = ColaCircular()
        n = 1000000
        for i in range(n):
            c.encolar(i)
        total = 0
        while not c.vacia():
            total += c.desencolar()
        self.assertEqual(total, n * (n - 1) // 2)


if __name__ == "__main__":
    unittest.main()
