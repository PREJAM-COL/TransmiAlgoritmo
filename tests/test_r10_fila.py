import random
import time
import unittest

from motor import simular_fila


def referencia(llegadas, f, cap):
    """Simulación ingenua bus por bus, con list.pop(0) (aquí sí se permite)."""
    res = [None] * len(llegadas)
    fila, i, t = [], 0, 0
    while None in res:
        while i < len(llegadas) and llegadas[i] <= t:
            fila.append(i)
            i += 1
        for _ in range(cap):
            if fila:
                res[fila.pop(0)] = t
        t += f
    return res


class TestR10Fila(unittest.TestCase):
    def test_ejemplo(self):
        self.assertEqual(simular_fila([0, 0, 1, 2, 5, 100], 3, 2), [0, 0, 3, 3, 6, 102])

    def test_fifo_con_cupo(self):
        self.assertEqual(simular_fila([0, 0, 0, 0, 0], 5, 2), [0, 0, 5, 5, 10])

    def test_llegar_justo_a_la_salida_alcanza(self):
        self.assertEqual(simular_fila([3], 3, 1), [3])

    def test_parametros_invalidos(self):
        self.assertEqual(simular_fila([], 3, 2), [])
        self.assertEqual(simular_fila([1, 2], 0, 2), [])
        self.assertEqual(simular_fila([1, 2], 3, 0), [])
        self.assertEqual(simular_fila([1, 2], -1, 2), [])

    def test_aleatorio_contra_referencia(self):
        rnd = random.Random(10)
        for _ in range(300):
            n = rnd.randint(1, 40)
            llegadas = sorted(rnd.randint(0, 60) for _ in range(n))
            f, cap = rnd.randint(1, 7), rnd.randint(1, 5)
            self.assertEqual(simular_fila(llegadas, f, cap), referencia(llegadas, f, cap))

    def test_llegadas_muy_tardias_no_simulan_buses_vacios(self):
        t = time.perf_counter()
        self.assertEqual(simular_fila([1000000, 1000000], 1, 1), [1000000, 1000001])
        self.assertLess(time.perf_counter() - t, 0.1)

    def test_cientos_de_miles(self):
        rnd = random.Random(1)
        llegadas, t = [], 0
        for _ in range(300000):
            t += rnd.randint(0, 1)
            llegadas.append(t)
        inicio = time.perf_counter()
        res = simular_fila(llegadas, 4, 160)
        self.assertLess(time.perf_counter() - inicio, 5.0)
        self.assertEqual(len(res), 300000)
        for i in range(1, len(res)):
            self.assertLessEqual(res[i - 1], res[i])           # FIFO: nadie se cuela
            self.assertGreaterEqual(res[i], llegadas[i])       # nadie sube antes de llegar


if __name__ == "__main__":
    unittest.main()
