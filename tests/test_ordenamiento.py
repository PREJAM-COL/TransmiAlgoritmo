import bisect
import random
import unittest

from motor.estructuras.ordenamiento import limite_inferior, merge_sort


class TestMergeSort(unittest.TestCase):
    def test_casos_pequenos(self):
        for caso in ([], [1], [2, 1], [3, 1, 2], [1, 1, 1], [5, 4, 3, 2, 1]):
            self.assertEqual(merge_sort(caso), sorted(caso))

    def test_no_modifica_la_entrada(self):
        x = [3, 1, 2]
        merge_sort(x)
        self.assertEqual(x, [3, 1, 2])

    def test_aleatorio_contra_sorted(self):
        rnd = random.Random(11)
        for n in (10, 99, 1000, 4097):
            x = [rnd.randint(-50, 50) for _ in range(n)]
            self.assertEqual(merge_sort(x), sorted(x))

    def test_cadenas(self):
        x = ["CALLE 26", "AV. 68", "RICAURTE", "BANDERAS", "CALLE 100"]
        self.assertEqual(merge_sort(x), sorted(x))

    def test_con_clave_y_estable(self):
        rnd = random.Random(5)
        pares = [(rnd.randint(0, 9), i) for i in range(2000)]
        self.assertEqual(merge_sort(pares, clave=lambda p: p[0]), sorted(pares, key=lambda p: p[0]))

    def test_clave_tupla_ranking(self):
        est = [("B", 10), ("A", 10), ("C", 30)]
        r = merge_sort(est, clave=lambda e: (-e[1], e[0]))
        self.assertEqual([e[0] for e in r], ["C", "A", "B"])


class TestLimiteInferior(unittest.TestCase):
    def test_contra_bisect(self):
        rnd = random.Random(9)
        for n in (0, 1, 2, 10, 500):
            arr = sorted(rnd.randint(0, 1439) for _ in range(n))
            for x in (-1, 0, 720, 1439, 1440) + tuple(rnd.randint(0, 1439) for _ in range(30)):
                self.assertEqual(limite_inferior(arr, x), bisect.bisect_left(arr, x))

    def test_con_repetidos(self):
        arr = [5, 5, 5, 7]
        self.assertEqual(limite_inferior(arr, 5), 0)
        self.assertEqual(limite_inferior(arr, 6), 3)
        self.assertEqual(limite_inferior(arr, 8), 4)

    def test_subrango(self):
        arr = [1, 3, 5, 7, 9]
        self.assertEqual(limite_inferior(arr, 6, 1, 4), 3)
        self.assertEqual(limite_inferior(arr, 100, 1, 4), 4)


if __name__ == "__main__":
    unittest.main()
