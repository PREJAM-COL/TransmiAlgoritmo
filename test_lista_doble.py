import random
import unittest

from motor.estructuras.lista_doble import ListaDoble, NodoLista


def datos(it):
    return [n.dato for n in it]


class TestListaDoble(unittest.TestCase):
    def test_vacia(self):
        l = ListaDoble()
        self.assertEqual(len(l), 0)
        self.assertTrue(l.vacia())
        self.assertIsNone(l.primero())
        self.assertIsNone(l.ultimo())
        self.assertEqual(datos(l.adelante()), [])
        self.assertEqual(datos(l.atras()), [])

    def test_insertar_en_los_extremos(self):
        l = ListaDoble()
        l.insertar_al_final(NodoLista("B"))
        l.insertar_al_inicio(NodoLista("A"))
        l.insertar_al_final(NodoLista("C"))
        self.assertEqual(datos(l.adelante()), ["A", "B", "C"])
        self.assertEqual(datos(l.atras()), ["C", "B", "A"])
        self.assertEqual(l.primero().dato, "A")
        self.assertEqual(l.ultimo().dato, "C")
        self.assertEqual(len(l), 3)

    def test_insertar_despues_y_quitar_en_medio(self):
        l = ListaDoble()
        a, c = NodoLista("A"), NodoLista("C")
        l.insertar_al_final(a)
        l.insertar_al_final(c)
        b = NodoLista("B")
        l.insertar_despues(a, b)
        self.assertEqual(datos(l.adelante()), ["A", "B", "C"])
        anterior = b.ant
        l.quitar(b)
        self.assertIsNone(b.ant)
        self.assertIsNone(b.sig)
        self.assertEqual(datos(l.adelante()), ["A", "C"])
        # deshacer: volver a enlazar después del anterior guardado
        l.insertar_despues(anterior, b)
        self.assertEqual(datos(l.adelante()), ["A", "B", "C"])

    def test_quitar_primero_y_reinsertar_con_centinela(self):
        l = ListaDoble()
        for x in "ABC":
            l.insertar_al_final(NodoLista(x))
        a = l.primero()
        anterior = a.ant
        self.assertTrue(l.es_centinela(anterior))
        l.quitar(a)
        self.assertEqual(datos(l.adelante()), ["B", "C"])
        l.insertar_despues(anterior, a)
        self.assertEqual(datos(l.adelante()), ["A", "B", "C"])

    def test_vecinos(self):
        l = ListaDoble()
        for x in "AB":
            l.insertar_al_final(NodoLista(x))
        a, b = l.primero(), l.ultimo()
        self.assertIs(l.siguiente(a), b)
        self.assertIsNone(l.siguiente(b))
        self.assertIs(l.anterior(b), a)
        self.assertIsNone(l.anterior(a))

    def test_quitar_mientras_se_recorre(self):
        l = ListaDoble()
        for x in range(10):
            l.insertar_al_final(NodoLista(x))
        for n in l.adelante():
            if n.dato % 2 == 0:
                l.quitar(n)
        self.assertEqual(datos(l.adelante()), [1, 3, 5, 7, 9])

    def test_aleatorio_contra_list(self):
        rnd = random.Random(7)
        l, ref, nodos = ListaDoble(), [], []
        for paso in range(5000):
            if not nodos or rnd.random() < 0.6:
                nuevo = NodoLista(paso)
                if not nodos:
                    l.insertar_al_inicio(nuevo)
                    ref.insert(0, paso)
                else:
                    i = rnd.randrange(len(nodos))
                    l.insertar_despues(nodos[i], nuevo)
                    ref.insert(ref.index(nodos[i].dato) + 1, paso)
                nodos.append(nuevo)
            else:
                i = rnd.randrange(len(nodos))
                n = nodos.pop(i)
                l.quitar(n)
                ref.remove(n.dato)
            self.assertEqual(len(l), len(ref))
        self.assertEqual(datos(l.adelante()), ref)
        self.assertEqual(datos(l.atras()), ref[::-1])


if __name__ == "__main__":
    unittest.main()
