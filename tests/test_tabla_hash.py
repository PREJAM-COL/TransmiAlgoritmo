import random
import unittest

from motor.estructuras.tabla_hash import TablaHash, hash_cadena


class TestTablaHash(unittest.TestCase):
    def test_basico(self):
        t = TablaHash()
        self.assertTrue(t.poner("RICAURTE", 1))
        self.assertTrue(t.poner("CALLE 26", 2))
        self.assertEqual(t.obtener("RICAURTE"), 1)
        self.assertEqual(t.obtener("CALLE 26"), 2)
        self.assertIsNone(t.obtener("NO EXISTE"))
        self.assertEqual(t.obtener("NO EXISTE", "x"), "x")
        self.assertTrue(t.contiene("RICAURTE"))
        self.assertFalse(t.contiene("ricaurte"))   # sensible a mayúsculas
        self.assertEqual(len(t), 2)

    def test_reemplazar_valor(self):
        t = TablaHash()
        t.poner("A", 1)
        self.assertFalse(t.poner("A", 2))
        self.assertEqual(t.obtener("A"), 2)
        self.assertEqual(len(t), 1)

    def test_quitar_y_reinsertar(self):
        t = TablaHash()
        t.poner("A", 1)
        self.assertTrue(t.quitar("A"))
        self.assertFalse(t.quitar("A"))
        self.assertFalse(t.contiene("A"))
        self.assertEqual(len(t), 0)
        t.poner("A", 3)
        self.assertEqual(t.obtener("A"), 3)

    def test_lapida_no_corta_la_cadena(self):
        """Tres claves en el mismo grupo: borrar la del medio no debe esconder la última."""
        t = TablaHash(8)
        cap = t.capacidad
        # Buscar tres cadenas cuya casilla inicial coincida (colisión forzada).
        mismas, i = [], 0
        objetivo = hash_cadena("k0") & (cap - 1)
        while len(mismas) < 3:
            k = "k" + str(i)
            if hash_cadena(k) & (cap - 1) == objetivo:
                mismas.append(k)
            i += 1
        for k in mismas:
            t.poner(k, k)
        t.quitar(mismas[1])
        self.assertEqual(t.obtener(mismas[2]), mismas[2])
        self.assertEqual(t.obtener(mismas[0]), mismas[0])

    def test_crece_y_mantiene_carga(self):
        t = TablaHash()
        for i in range(1000):
            t.poner("E" + str(i), i)
            self.assertLessEqual(len(t) * 10, t.capacidad * 7)
        for i in range(1000):
            self.assertEqual(t.obtener("E" + str(i)), i)

    def test_claves_enteras(self):
        t = TablaHash()
        for i in range(500):
            t.poner(i * 7919, i)
        self.assertEqual(t.obtener(7919 * 13), 13)

    def test_clave_invalida(self):
        with self.assertRaises(TypeError):
            TablaHash().poner(("a", "b"), 1)

    def test_recorridos(self):
        t = TablaHash()
        for k in ["A", "B", "C"]:
            t.poner(k, k.lower())
        self.assertEqual(sorted(t.claves()), ["A", "B", "C"])
        self.assertEqual(sorted(t.elementos()), [("A", "a"), ("B", "b"), ("C", "c")])

    def test_aleatorio_contra_dict(self):
        rnd = random.Random(42)
        t, ref = TablaHash(), {}
        for _ in range(100000):
            k = "R" + str(rnd.randrange(3000))
            op = rnd.random()
            if op < 0.5:
                v = rnd.random()
                self.assertEqual(t.poner(k, v), k not in ref)
                ref[k] = v
            elif op < 0.75:
                self.assertEqual(t.quitar(k), k in ref)
                ref.pop(k, None)
            else:
                self.assertEqual(t.obtener(k, "-"), ref.get(k, "-"))
        self.assertEqual(len(t), len(ref))
        self.assertEqual(sorted(t.elementos()), sorted(ref.items()))

    def test_estadisticas_sondeo_corto(self):
        t = TablaHash()
        for i in range(2000):
            t.poner("ESTACION " + str(i), i)
        n, lapidas, cap, mas_largo, promedio = t.estadisticas()
        self.assertEqual(n, 2000)
        self.assertLess(promedio, 3.0)   # con carga <= 0,7 el sondeo promedio es corto


if __name__ == "__main__":
    unittest.main()
