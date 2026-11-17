"""Genera redes de tamaño creciente a partir de la red real. Dueño: Tomás.

El profesor mide en redes de 10.000, 20.000, 40.000 y 80.000 estaciones. La red
real tiene 147, así que esas redes son 68, 136, 272 y 544 copias de ella.

Como el script del profesor, duplicamos la red y medimos. Una red ×f tiene f
copias de cada estación, ruta y horario. Las copias se nombran con un sufijo
de letras para respetar el formato (MAYÚSCULAS, sin tildes, sin repetidos):

    copia 0: RICAURTE        copia 1: RICAURTE B        copia 2: RICAURTE C …

Cada copia se une con la siguiente con una ruta puente, para que la red siga
conectada. Así crecen a la vez estaciones, rutas, paradas y horarios (todo n
se multiplica por f) y el tamaño de cada ruta (L) y las horas por parada (h)
se mantienen: justo lo que permite ver si una operación depende de n o no.

Horarios livianos: copiar los 140.000 horarios 544 veces daría 76 millones de
filas. Por eso cada copia se queda con 1 de cada PASO_HORARIOS filas (las
horas de cada parada siguen ordenadas y repartidas en el día). Así los
horarios también crecen proporcionalmente a n, que es lo que importa medir.

Uso:  py benchmarks/generar_red.py 68         (crea benchmarks/redes/x68/, ~10.000 estaciones)
"""

import csv
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, "datos")
REDES = os.path.join(RAIZ, "benchmarks", "redes")
PASO_HORARIOS = 40

# Copias de la red real para llegar a los tamaños que mide el profesor.
FACTORES_PROFESOR = [68, 136, 272, 544]      # ≈ 10.000, 20.000, 40.000 y 80.000 estaciones


def sufijo(i):
    """0 -> '', 1 -> ' B', 2 -> ' C', …, 25 -> ' Z', 26 -> ' AA'…"""
    if i == 0:
        return ""
    letras = ""
    n = i
    while n >= 0:
        letras = chr(ord("A") + n % 26) + letras
        n = n // 26 - 1
    return " " + letras


def _leer(nombre):
    with open(os.path.join(DATOS, nombre), newline="", encoding="utf-8") as f:
        filas = list(csv.reader(f))
    return filas[0], filas[1:]


def generar(factor, destino=None):
    """Escribe los tres CSV de la red ×factor y devuelve la carpeta."""
    destino = destino or os.path.join(REDES, "x%d" % factor)
    os.makedirs(destino, exist_ok=True)
    _, estaciones = _leer("estaciones.csv")
    _, rutas = _leer("rutas.csv")
    _, horarios = _leer("horarios.csv")
    estaciones = [f[0] for f in estaciones if f]
    primera, ultima = estaciones[0], estaciones[-1]

    with open(os.path.join(destino, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre"])
        for c in range(factor):
            for e in estaciones:
                w.writerow([e + sufijo(c)])

    with open(os.path.join(destino, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "orden", "estacion"])
        for c in range(factor):
            s = sufijo(c)
            for ruta, orden, est in rutas:
                w.writerow([ruta + s, orden, est + s])
            if c + 1 < factor:
                w.writerow(["PUENTE" + s, 1, ultima + s])
                w.writerow(["PUENTE" + s, 2, primera + sufijo(c + 1)])

    with open(os.path.join(destino, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "estacion", "hora"])
        for c in range(factor):
            s = sufijo(c)
            for i in range(0, len(horarios), PASO_HORARIOS):
                ruta, est, hora = horarios[i]
                w.writerow([ruta + s, est + s, hora])
            if c + 1 < factor:
                for hora in ("06:00", "12:00", "18:00"):
                    w.writerow(["PUENTE" + s, ultima + s, hora])
                    w.writerow(["PUENTE" + s, primera + sufijo(c + 1), hora])
    return destino


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["2"]:
        print(generar(int(arg)))
