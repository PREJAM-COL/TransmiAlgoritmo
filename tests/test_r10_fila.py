import random
import time
import unittest

from motor import simular_fila


def referencia(llegadas, f, cap):
    """Simulación ingenua bus por bus, con sorted y list.pop(0) (aquí sí se permite)."""
    orden = sorted(range(len(llegadas)), key=lambda i: (llegadas[i], i))
    res = [None] * len(llegadas)
    fila, j, t = [], 0, f
    while None in res:
        while j < len(orden) and llegadas[orden[j]] <= t:
            fila.append(orden[j])
            j += 1
        for _ in range(cap):
            if fila:
                res[fila.pop(0)] = t
        t += f
    return res


class TestR10Fila(unittest.TestCase):
    def test_ejemplo_del_profesor(self):
        self.assertEqual(simular_fila([30, 5, 5, 70], 60, 2), [120, 60, 60, 120])

    def test_primer_bus_sale_en_la_frecuencia(self):
        self.assertEqual(simular_fila([0], 60, 1), [60])
        self.assertEqual(simular_fila([0, 0, 0], 10, 2), [10, 10, 20])

    def test_fifo_con_cupo(self):
        self.assertEqual(simular_fila([0, 0, 0, 0, 0], 5, 2), [5, 5, 10, 10, 15])

    def test_desordenadas_y_empates(self):
        # los dos que llegan en el segundo 5 suben en el orden en que aparecen
        self.assertEqual(simular_fila([50, 5, 40, 5], 60, 1), [240, 60, 180, 120])

    def test_llegar_justo_a_la_salida_alcanza(self):
        self.assertEqual(simular_fila([60], 60, 1), [60])
        self.assertEqual(simular_fila([61], 60, 1), [120])

    def test_parametros_invalidos(self):
        self.assertEqual(simular_fila([], 60, 2), [])
        self.assertEqual(simular_fila([1, 2], 0, 2), [])
        self.assertEqual(simular_fila([1, 2], 60, 0), [])
        self.assertEqual(simular_fila([1, 2], -1, 2), [])
        self.assertEqual(simular_fila(None, 60, 2), [])

    def test_no_modifica_la_entrada(self):
        llegadas = [30, 5, 5, 70]
        simular_fila(llegadas, 60, 2)
        self.assertEqual(llegadas, [30, 5, 5, 70])

    def test_aleatorio_contra_referencia(self):
        rnd = random.Random(10)
        for _ in range(400):
            n = rnd.randint(1, 40)
            llegadas = [rnd.randint(0, 300) for _ in range(n)]       # desordenadas
            if rnd.random() < 0.3:
                llegadas.sort()
            f, cap = rnd.randint(1, 70), rnd.randint(1, 5)
            self.assertEqual(simular_fila(llegadas, f, cap), referencia(llegadas, f, cap))

    def test_llegadas_muy_tardias_no_simulan_buses_vacios(self):
        t = time.perf_counter()
        self.assertEqual(simular_fila([1000000, 1000000], 1, 1), [1000000, 1000001])
        self.assertLess(time.perf_counter() - t, 0.1)

    def test_cientos_de_miles_desordenadas(self):
        rnd = random.Random(1)
        llegadas = [rnd.randint(0, 7200) for _ in range(200000)]
        inicio = time.perf_counter()
        res = simular_fila(llegadas, 60, 160)
        self.assertLess(time.perf_counter() - inicio, 8.0)
        self.assertEqual(len(res), 200000)
        orden = sorted(range(len(llegadas)), key=lambda i: (llegadas[i], i))
        for a, b in zip(orden, orden[1:]):
            self.assertLessEqual(res[a], res[b])              # FIFO: nadie se cuela
        for i in range(len(res)):
            self.assertGreaterEqual(res[i], llegadas[i])      # nadie sube antes de llegar
            self.assertEqual(res[i] % 60, 0)                  # solo salen buses en múltiplos de f


if __name__ == "__main__":
    unittest.main()
