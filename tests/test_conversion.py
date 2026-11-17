"""Pruebas del script de conversión GTFS -> CSV con un GTFS pequeño hecho a mano
(tests/fixtures/gtfs_mini). No tenemos el zip real de 54 MB: estas pruebas
verifican las reglas de la diapositiva 9 y que el motor pueda leer el resultado."""

import csv
import os
import shutil
import tempfile
import unittest
import zipfile

from conversion.gtfs_a_csv import convertir, minutos, normalizar
from motor import Red
from tests.apoyo import RAIZ

GTFS = os.path.join(RAIZ, "tests", "fixtures", "gtfs_mini")


def leer(carpeta, nombre):
    with open(os.path.join(carpeta, nombre), newline="", encoding="utf-8") as f:
        return list(csv.reader(f))[1:]


class TestConversion(unittest.TestCase):
    def setUp(self):
        self.salida = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.salida, ignore_errors=True)

    def test_normalizar_nombres(self):
        self.assertEqual(normalizar("Héroes "), "HEROES")
        self.assertEqual(normalizar("Calle  26"), "CALLE 26")
        self.assertEqual(normalizar("Av. Jiménez"), "AV. JIMENEZ")
        self.assertEqual(normalizar("Nariño"), "NARINO")

    def test_horas_mayores_a_24(self):
        self.assertEqual(minutos("25:10:00"), 70)
        self.assertEqual(minutos("06:05:00"), 365)
        self.assertIsNone(minutos(""))

    def test_estaciones_unicas_y_por_estacion_padre(self):
        convertir(GTFS, self.salida)
        nombres = [f[0] for f in leer(self.salida, "estaciones.csv")]
        # los dos vagones de Ricaurte son una sola estación; sin tildes ni repetidos
        self.assertEqual(nombres, ["AV. JIMENEZ", "CALLE 26", "HEROES", "RICAURTE"])

    def test_una_ruta_por_sentido_y_variante(self):
        convertir(GTFS, self.salida)
        rutas = {}
        for ruta, orden, est in leer(self.salida, "rutas.csv"):
            rutas.setdefault(ruta, []).append((int(orden), est))
        recorridos = {r: [e for _, e in sorted(v)] for r, v in rutas.items()}
        self.assertEqual(recorridos, {
            "A51": ["RICAURTE", "AV. JIMENEZ"],                          # un solo recorrido: sin sufijo
            "B10-1": ["HEROES", "CALLE 26", "RICAURTE", "AV. JIMENEZ"],  # sentido 0, el más frecuente
            "B10-2": ["HEROES", "CALLE 26"],                             # sentido 0, viaje corto
            "B10-3": ["AV. JIMENEZ", "RICAURTE", "CALLE 26", "HEROES"],  # sentido 1
        })

    def test_horarios(self):
        convertir(GTFS, self.salida)
        horas = leer(self.salida, "horarios.csv")
        self.assertIn(["B10-1", "RICAURTE", "06:10"], horas)       # primer vagón, no el segundo
        self.assertNotIn(["B10-1", "RICAURTE", "06:11"], horas)
        self.assertIn(["B10-1", "AV. JIMENEZ", "07:20"], horas)     # filas desordenadas se ordenan
        self.assertIn(["A51", "AV. JIMENEZ", "00:05"], horas)       # 24:05 -> 00:05
        self.assertEqual(len(horas), 4 + 4 + 4 + 2 + 2)

    def test_filtrar_por_servicio(self):
        r = convertir(GTFS, self.salida, servicio="HABIL")
        self.assertEqual(r["rutas"], 3)
        self.assertNotIn("A51", {f[0] for f in leer(self.salida, "rutas.csv")})

    def test_desde_zip(self):
        z = os.path.join(self.salida, "gtfs.zip")
        with zipfile.ZipFile(z, "w") as f:
            for nombre in os.listdir(GTFS):
                f.write(os.path.join(GTFS, nombre), "gtfs/" + nombre)
        r = convertir(z, os.path.join(self.salida, "csv"))
        self.assertEqual(r["estaciones"], 4)

    def test_el_motor_lee_el_resultado(self):
        convertir(GTFS, self.salida)
        red = Red(self.salida)
        self.assertEqual(red.info_advertencias(), 0)
        self.assertEqual(red.estado("RICAURTE"), "abierta")
        self.assertEqual(red.proximo_bus("RICAURTE", "B10-1", "06:30"), "07:10")
        self.assertEqual(red.viaje("HEROES", "AV. JIMENEZ"), [("B10-1", "HEROES", "AV. JIMENEZ")])


if __name__ == "__main__":
    unittest.main()
