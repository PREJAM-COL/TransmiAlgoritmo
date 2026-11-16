import bisect
import math
import random
import unittest

from motor.estructuras.avl import AVL


def todo(arbol, desde=None):
    return [c for c, _ in arbol.desde(desde)]


class TestAVL(unittest.TestCase):
    def test_vacio(self):
        a = AVL()
        self.assertEqual(len(a), 0)
        self.assertEqual(todo(a), [])
        self.assertFalse(a.eliminar("X"))
        self.assertTrue(a.verificar())

    def test_insertar_ordenado_no_degenera(self):
        """Nombres que llegan ya ordenados: un BST simple quedaría como lista."""
        a = AVL()
        n = 1023
        for i in range(n):
            a.insertar("%05d" % i)
            a.verificar()
        self.assertLessEqual(a.altura(), int(1.45 * math.log2(n + 2)))

    def test_insertar_repetido_reemplaza_valor(self):
        a = AVL()
        self.assertTrue(a.insertar("A", 1))
        self.assertFalse(a.insertar("A", 2))
        self.assertEqual(a.buscar("A"), 2)
        self.assertEqual(len(a), 1)

    def test_eliminar_todos_los_casos(self):
        a = AVL()
        for k in [50, 30, 70, 20, 40, 60, 80, 35, 45, 65]:
            a.insertar(k)
        for k in [20, 30, 50, 70, 35]:     # hoja, un hijo, dos hijos, raíz…
            self.assertTrue(a.eliminar(k))
            a.verificar()
        self.assertEqual(todo(a), [40, 45, 60, 65, 80])

    def test_desde_es_limite_inferior(self):
        nombres = ["AV. 68", "BANDERAS", "CALLE 100", "CALLE 26", "CALLE 72", "CAN", "RICAURTE"]
        a = AVL()
        for n in nombres:
            a.insertar(n)
        self.assertEqual(todo(a, "CAL"), ["CALLE 100", "CALLE 26", "CALLE 72", "CAN", "RICAURTE"])
        self.assertEqual(todo(a, "CALLE 26"), ["CALLE 26", "CALLE 72", "CAN", "RICAURTE"])
        self.assertEqual(todo(a, "ZZZ"), [])
        self.assertEqual(todo(a, ""), nombres)

    def test_claves_tupla_para_ranking(self):
        a = AVL()
        for nombre, buses in [("RICAURTE", 4446), ("BANDERAS", 3038), ("PORTAL NORTE", 3282), ("AAA", 3038)]:
            a.insertar((-buses, nombre), nombre)
        self.assertEqual([v for _, v in a.desde()], ["RICAURTE", "PORTAL NORTE", "AAA", "BANDERAS"])

    def test_construir_desde_ordenados(self):
        claves = ["%04d" % i for i in range(1000)]
        a = AVL()
        a.construir_desde_ordenados(claves, list(range(1000)))
        a.verificar()
        self.assertEqual(len(a), 1000)
        self.assertEqual(a.buscar("0500"), 500)
        self.assertEqual(todo(a), claves)
        with self.assertRaises(ValueError):
            AVL().construir_desde_ordenados(["B", "A"])

    def test_aleatorio_contra_lista_ordenada(self):
        rnd = random.Random(2021)
        a, ref = AVL(), []
        for paso in range(10000):
            k = rnd.randrange(2000)
            if rnd.random() < 0.6:
                nueva = k not in ref
                self.assertEqual(a.insertar(k), nueva)
                if nueva:
                    bisect.insort(ref, k)
            else:
                existe = k in ref
                self.assertEqual(a.eliminar(k), existe)
                if existe:
                    ref.remove(k)
            if paso % 250 == 0:
                a.verificar()
                d = rnd.randrange(2000)
                self.assertEqual(todo(a, d), ref[bisect.bisect_left(ref, d):])
        a.verificar()
        self.assertEqual(todo(a), ref)
        self.assertEqual(len(a), len(ref))


if __name__ == "__main__":
    unittest.main()
