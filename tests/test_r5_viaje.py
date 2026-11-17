import random
import unittest

from motor import Red
from tests.apoyo import DATOS, MINI


def referencia(red, o, d):
    """Fuerza bruta con dict/set (permitidos en pruebas) y el mismo criterio de desempate."""
    if red.estado(o) != "abierta" or red.estado(d) != "abierta":
        return None
    if o == d:
        return []
    rutas = {r: red.recorrido(r) for r in red.lista_rutas()}
    pos = {r: {s: i for i, s in enumerate(seq)} for r, seq in rutas.items()}
    mejor = None

    def candidato(clave, res):
        nonlocal mejor
        if mejor is None or clave < mejor[0]:
            mejor = (clave, res)

    for r1, seq in rutas.items():
        if o not in pos[r1]:
            continue
        i = pos[r1][o]
        if d in pos[r1] and pos[r1][d] > i:
            candidato((pos[r1][d] - i, 0, r1, "", ""), [(r1, o, d)])
        for j in range(i + 1, len(seq)):
            t = seq[j]
            if t == d:
                break
            if red.estado(t) != "abierta":
                continue
            for r2 in rutas:
                if r2 != r1 and t in pos[r2] and d in pos[r2] and pos[r2][d] > pos[r2][t]:
                    candidato((j - i + pos[r2][d] - pos[r2][t], 1, r1, r2, t), [(r1, o, t), (r2, t, d)])
    return None if mejor is None else mejor[1]


class TestR5Mini(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    def test_directo_con_menos_paradas(self):
        self.assertEqual(self.red.viaje("ALFA", "CALLE 2"), [("R5", "ALFA", "CALLE 2")])   # 1 parada, no 3 por R1
        self.assertEqual(self.red.viaje("BETA", "DELTA"), [("R3", "BETA", "DELTA")])

    def test_transbordo(self):
        self.assertEqual(self.red.viaje("ALFA", "ECO"), [("R5", "ALFA", "CALLE 2"), ("R2", "CALLE 2", "ECO")])
        self.assertEqual(self.red.viaje("BETA", "ECO"), [("R3", "BETA", "DELTA"), ("R2", "DELTA", "ECO")])

    def test_sin_viaje_con_un_transbordo(self):
        self.assertIsNone(self.red.viaje("ALFA", "FOXTROT"))   # necesitaría dos transbordos
        self.assertIsNone(self.red.viaje("GAMA", "ALFA"))      # GAMA no tiene rutas
        self.assertIsNone(self.red.viaje("ECO", "ALFA"))       # las rutas van en un solo sentido

    def test_bordes(self):
        self.assertEqual(self.red.viaje("ALFA", "ALFA"), [])
        self.assertIsNone(self.red.viaje("ZETA", "ALFA"))
        self.assertIsNone(self.red.viaje("ALFA", "ZETA"))

    def test_edicion_cambia_el_viaje(self):
        self.red.agregar_parada("R3", "ECO", "DELTA")
        self.assertEqual(self.red.viaje("BETA", "ECO"), [("R3", "BETA", "ECO")])
        self.red.deshacer()
        self.assertEqual(self.red.viaje("BETA", "ECO"), [("R3", "BETA", "DELTA"), ("R2", "DELTA", "ECO")])

    def test_coincide_con_referencia_en_todos_los_pares(self):
        nombres = self.red.lista_estaciones()
        for o in nombres:
            for d in nombres:
                self.assertEqual(self.red.viaje(o, d), referencia(self.red, o, d), (o, d))


class TestR5Real(unittest.TestCase):
    def test_ejemplos_conocidos(self):
        red = Red(DATOS)
        self.assertEqual(red.viaje("PORTAL AMERICAS", "CALLE 100"),
                         [("E32", "PORTAL AMERICAS", "SIMON BOLIVAR"), ("B44-1", "SIMON BOLIVAR", "CALLE 100")])
        self.assertIsNone(red.viaje("POLICARPA", "AGUAS"))

    def test_aleatorio_contra_referencia_con_cierres(self):
        red = Red(DATOS)
        rnd = random.Random(21)
        nombres = red.lista_estaciones()
        for nombre in rnd.sample(nombres, 12):
            red.cerrar(nombre)
        for _ in range(300):
            o, d = rnd.choice(nombres), rnd.choice(nombres)
            self.assertEqual(red.viaje(o, d), referencia(red, o, d), (o, d))

    def test_traza_da_el_mismo_resultado(self):
        """La vista "rayos X" anima la MISMA búsqueda: su resultado debe coincidir con viaje()."""
        red = Red(DATOS)
        rnd = random.Random(8)
        nombres = red.lista_estaciones()
        for _ in range(200):
            o, d = rnd.choice(nombres), rnd.choice(nombres)
            res, traza = red.info_traza_viaje(o, d)
            self.assertEqual(res, red.viaje(o, d))
        res, traza = red.info_traza_viaje("PORTAL AMERICAS", "CALLE 100")
        tipos = {e[0] for e in traza}
        self.assertTrue({"ida", "vuelta", "encuentro"} <= tipos)
        mejoras = [e for e in traza if e[0] == "encuentro" and e[5]]
        self.assertEqual(mejoras[-1][1], "SIMON BOLIVAR")

    def test_cuantos_pares_no_tienen_viaje(self):
        """Hallazgo de la Fase 1: 518 pares ordenados sin viaje con <= 1 transbordo."""
        red = Red(DATOS)
        nombres = red.lista_estaciones()
        sin = sum(1 for o in nombres for d in nombres if o != d and red.viaje(o, d) is None)
        self.assertEqual(sin, 518)


if __name__ == "__main__":
    unittest.main()
