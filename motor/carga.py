"""Carga de la red desde los tres CSV (dueño: Tomás).

El motor solo lee estaciones.csv, rutas.csv y horarios.csv. No se asume que
vengan ordenados ni agrupados: la red del profesor es otra y más grande.
Las filas inválidas (estación o ruta desconocida, orden u hora mal escritos,
estación repetida en una ruta) se ignoran y se cuentan en red._advertencias.

Pasos y complejidad (n_E estaciones, n_P pares ruta-estación, n_H horarios):
  1. estaciones: tabla hash + AVL de abiertas construido desde la lista
     ordenada con merge sort .................................. O(n_E log n_E)
  2. rutas: se agrupan las filas por ruta, cada ruta se ordena por `orden`
     y se enlaza como lista doble ............................. O(n_P log L)
  3. horarios: ORDENAMIENTO POR CONTEO. 1440 cubetas (una por minuto); cada
     fila cae en su cubeta y luego se vacían en orden: todas las listas de
     horas quedan ordenadas sin comparar nada ................. O(n_H + 1440)
  4. ranking: claves (-buses, nombre) ordenadas y AVL balanceado O(n_E log n_E)
"""

import csv

from .estructuras.avl import AVL
from .estructuras.ordenamiento import merge_sort
from .estructuras.pila import Pila
from .estructuras.tabla_hash import TablaHash
from .horarios import MINUTOS_DIA, minutos
from .modelo import Estacion, Membresia, NodoParada, Ruta
from .ranking import clave_ranking

SEPARADOR = "\x1f"   # no aparece en nombres de estaciones ni rutas


def clave_parada(ruta, estacion):
    return ruta + SEPARADOR + estacion


def _ruta_archivo(carpeta, nombre):
    c = str(carpeta)
    while len(c) > 1 and (c.endswith("/") or c.endswith("\\")):
        c = c[:-1]
    return c + "/" + nombre


def _filas(carpeta, nombre, columnas):
    """Recorre las filas del CSV como listas, en el orden de `columnas`.

    Busca cada columna por su nombre en el encabezado (no se usa DictReader
    porque crea un dict por fila).
    """
    with open(_ruta_archivo(carpeta, nombre), newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        encabezado = None
        for fila in lector:
            if encabezado is None:
                encabezado = [c.strip().lower() for c in fila]
                posiciones = []
                for col in columnas:
                    p = -1
                    for i in range(len(encabezado)):
                        if encabezado[i] == col:
                            p = i
                    if p < 0:
                        raise ValueError(nombre + ": falta la columna '" + col + "'")
                    posiciones.append(p)
                continue
            if len(fila) == 0:
                continue
            valores = []
            ok = True
            for p in posiciones:
                if p >= len(fila):
                    ok = False
                    break
                valores.append(fila[p].strip())
            if ok:
                yield valores


def cargar(red, carpeta):
    red._estaciones = TablaHash()
    red._rutas = TablaHash()
    red._paradas = TablaHash()
    red._por_id = []
    red._nombres_rutas = []
    red._advertencias = 0
    red._deshacer = Pila()
    red._rehacer = Pila()

    # 1. Estaciones ---------------------------------------------------------
    nombres = []
    for (nombre,) in _filas(carpeta, "estaciones.csv", ["nombre"]):
        e = Estacion(len(red._por_id), nombre)
        if nombre == "" or not red._estaciones.agregar(nombre, e):   # vacía o repetida
            red._advertencias += 1
            continue
        red._por_id.append(e)
        nombres.append(nombre)
    nombres = merge_sort(nombres)
    red._abiertas = AVL()
    red._abiertas.construir_desde_ordenados(nombres, [red._estaciones.obtener(n) for n in nombres])

    # 2. Rutas --------------------------------------------------------------
    grupos = TablaHash()             # ruta -> lista de (orden, Estacion)
    for ruta, orden, estacion in _filas(carpeta, "rutas.csv", ["ruta", "orden", "estacion"]):
        e = red._estaciones.obtener(estacion)
        if ruta == "" or not orden.lstrip("-").isdigit() or e is None:
            red._advertencias += 1
            continue
        lista = grupos.obtener(ruta)
        if lista is None:
            lista = []
            grupos.poner(ruta, lista)
            red._nombres_rutas.append(ruta)
        lista.append((int(orden), e))

    for nombre_ruta in red._nombres_rutas:
        r = Ruta(nombre_ruta)
        red._rutas.poner(nombre_ruta, r)
        for _, e in merge_sort(grupos.obtener(nombre_ruta), clave=_primero):
            nodo = NodoParada(e, r)
            if not red._paradas.agregar(clave_parada(nombre_ruta, e.nombre), nodo):
                red._advertencias += 1           # estación repetida en la misma ruta
                continue
            nodo.membresia = Membresia(nodo)
            r.paradas.insertar_al_final(nodo)
            e.membresias.insertar_al_final(nodo.membresia)
    red._nombres_rutas = merge_sort(red._nombres_rutas)

    # 3. Horarios: ordenamiento por conteo -----------------------------------
    cubetas = [[] for _ in range(MINUTOS_DIA)]
    for ruta, estacion, hora in _filas(carpeta, "horarios.csv", ["ruta", "estacion", "hora"]):
        nodo = red._paradas.obtener(clave_parada(ruta, estacion))
        m = minutos(hora)
        if nodo is None or m < 0:
            red._advertencias += 1
            continue
        cubetas[m].append(nodo)
        nodo.estacion.buses_dia += 1
    for m in range(MINUTOS_DIA):
        for nodo in cubetas[m]:
            nodo.horas.append(m)

    # 4. Ranking ------------------------------------------------------------
    claves = merge_sort([clave_ranking(e) for e in red._por_id])
    valores = [red._estaciones.obtener(c[1]) for c in claves]
    red._ranking = AVL()
    red._ranking.construir_desde_ordenados(claves, valores)

    # Arreglos reutilizables de la búsqueda de R5 (marcas por versión).
    n = len(red._por_id)
    red._marca = [0] * n
    red._mejor_paradas = [0] * n
    red._mejor_nodo = [None] * n
    red._version = 0


def _primero(par):
    return par[0]
