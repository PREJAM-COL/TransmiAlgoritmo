"""Utilidades compartidas por las pruebas (aquí sí se permite dict, set, sorted…).

- Rutas a la red real (datos/) y a la mini red de prueba (tests/fixtures/mini/).
- verificar_invariantes(red): las seis reglas de docs/fase-2-diseno.md §6.
- foto(red): resumen comparable del estado de la red, para pruebas de R9.
"""

import importlib.util
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, "datos")
MINI = os.path.join(RAIZ, "tests", "fixtures", "mini")


def requiere(*modulos):
    """Salta la prueba si algún módulo del motor todavía no existe.

    El motor se construye por módulos (uno por requisito). Una prueba que
    mezcla requisitos, por ejemplo "cerrar una estación cambia el viaje",
    solo corre cuando ya están todos los módulos que usa.
    """
    faltan = [m for m in modulos if importlib.util.find_spec("motor." + m) is None]
    return unittest.skipIf(faltan, "falta el módulo: motor/" + ", motor/".join(faltan) + ".py")


def nombres(ranking):
    """Solo los nombres de una lista de (nombre, buses) de R6."""
    return [n for n, _ in ranking]


def verificar_invariantes(red):
    estaciones = list(red._por_id)

    # 1. El AVL de abiertas tiene exactamente las abiertas, en orden.
    red._abiertas.verificar()
    abiertas = sorted(e.nombre for e in estaciones if e.abierta)
    assert [c for c, _ in red._abiertas.desde()] == abiertas, "AVL de abiertas desincronizado"

    # 2. El ranking tiene exactamente las abiertas con su clave actual.
    red._ranking.verificar()
    claves = sorted((-e.buses_dia, e.nombre) for e in estaciones if e.abierta)
    assert [c for c, _ in red._ranking.desde()] == claves, "ranking desincronizado"

    # 3. buses_dia = suma de horas de las paradas actuales de la estación.
    for e in estaciones:
        total = 0
        for m in e.membresias.adelante():
            assert m.parada.estacion is e, "membresía en la estación equivocada"
            total += len(m.parada.horas)
        assert e.buses_dia == total, "buses_dia incorrecto en " + e.nombre

    # 4 y 5. Toda parada está en la tabla, su membresía en su estación y los punteros cuadran.
    paradas = 0
    for nombre in red._nombres_rutas:
        r = red._rutas.obtener(nombre)
        vistos = set()
        anterior = r.paradas.centinela
        for n in r.paradas.adelante():
            assert n.ant is anterior and anterior.sig is n, "punteros rotos en " + nombre
            assert n.ruta is r
            assert n.estacion.nombre not in vistos, "estación repetida en " + nombre
            vistos.add(n.estacion.nombre)
            assert red._paradas.obtener(red.clave_parada(nombre, n.estacion.nombre)) is n
            assert any(m is n.membresia for m in n.estacion.membresias.adelante())
            anterior = n
            paradas += 1
        assert len(r.paradas) == len(vistos)
    assert len(red._paradas) == paradas, "la tabla de paradas tiene sobrantes"


def foto(red):
    """Estado observable de la red: estaciones (abierta, buses) y recorrido de cada ruta."""
    return (
        tuple((e.nombre, e.abierta, e.buses_dia) for e in red._por_id),
        tuple((r, tuple(red.recorrido(r))) for r in red.lista_rutas()),
    )
