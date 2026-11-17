"""R5 · Planear un viaje: directo o con un transbordo, con menos paradas (dueño: Daniel).

Algoritmo: búsqueda desde los dos extremos que se encuentra en el medio.

  1. FRENTE DEL ORIGEN. Por cada ruta que para en el origen, se avanza por su
     lista doble contando paradas. Si aparece el destino, es un viaje directo.
     En cada estación abierta t se anota la mejor forma de llegar:
     mejor_paradas[t] y el nodo (y por tanto la ruta) con que se llegó.
  2. FRENTE DEL DESTINO. Por cada ruta r2 que para en el destino, se
     retrocede contando paradas d2. Si t fue alcanzada desde el origen por
     una ruta distinta de r2, "bajarse en t y tomar r2" es un viaje con un
     transbordo de mejor_paradas[t] + d2 paradas.
  3. Se queda el mejor candidato según: menos paradas, luego directo antes
     que transbordo, luego nombre de la primera ruta, de la segunda y de t.

¿Por qué basta con guardar UNA ruta (la mejor) por estación t? Si la mejor
ruta hasta t es justo r2, entonces r2 pasa por origen, luego por t y luego
por destino: ese viaje ya es DIRECTO y tiene igual o menos paradas que
cualquier transbordo en t, así que no se pierde ninguna solución mejor.

Marcas por versión: en vez de limpiar los arreglos (O(n_E)) en cada consulta,
se incrementa `red._version`; una casilla solo vale si marca[id] == versión.

Paradas cerradas: el bus pasa por ellas y cuentan como parada, pero no se
puede subir, bajar ni transbordar ahí.

Complejidad: O(suma de longitudes de las rutas del origen y del destino).
No recorre el resto de la red. (R5 no se mide en rendimiento.)
"""


def viaje(red, origen, destino):
    """R5. Lista de tramos (ruta, sube, baja), [] si origen == destino, o None."""
    return buscar(red, origen, destino, None)


def traza_viaje(red, origen, destino):
    """La misma búsqueda de R5, pero anotando cada paso (para la vista "rayos X").

    Devuelve (resultado, traza). La traza es una lista de eventos:
        ("ida", ruta, [(estacion, paradas), ...])     ruta explorada desde el origen
        ("vuelta", ruta, [(estacion, paradas), ...])  ruta explorada hacia el destino
        ("directo", ruta, paradas)                    viaje directo encontrado
        ("encuentro", estacion, ruta1, ruta2, paradas, mejora)  los frentes se tocan
    No es parte del contrato del profesor; no cambia el costo de viaje().
    """
    traza = []
    return buscar(red, origen, destino, traza), traza


def buscar(red, origen, destino, traza):
    if not isinstance(origen, str) or not isinstance(destino, str):
        return None
    o = red._estaciones.obtener(origen)
    d = red._estaciones.obtener(destino)
    if o is None or d is None or not o.abierta or not d.abierta:
        return None
    if o is d:
        return []

    red._version += 1
    version = red._version
    marca, mejor_paradas, mejor_nodo = red._marca, red._mejor_paradas, red._mejor_nodo

    mejor_clave = None
    mejor_res = None

    # 1. Frente del origen --------------------------------------------------
    for memb in o.membresias.adelante():
        inicio = memb.parada
        r = inicio.ruta
        paradas = r.paradas
        cuenta = 0
        visitadas = None if traza is None else []
        n = paradas.siguiente(inicio)
        while n is not None:
            cuenta += 1
            t = n.estacion
            if visitadas is not None:
                visitadas.append((t.nombre, cuenta))
            if t is d:
                clave = (cuenta, 0, r.nombre, "", "")
                if traza is not None:
                    traza.append(("directo", r.nombre, cuenta))
                if mejor_clave is None or clave < mejor_clave:
                    mejor_clave = clave
                    mejor_res = [(r.nombre, o.nombre, d.nombre)]
                break
            if t.abierta:
                i = t.id
                if (marca[i] != version or cuenta < mejor_paradas[i]
                        or (cuenta == mejor_paradas[i] and r.nombre < mejor_nodo[i].ruta.nombre)):
                    marca[i] = version
                    mejor_paradas[i] = cuenta
                    mejor_nodo[i] = n
            n = paradas.siguiente(n)
        if traza is not None:
            traza.append(("ida", r.nombre, visitadas))

    # 2. Frente del destino -------------------------------------------------
    for memb in d.membresias.adelante():
        fin = memb.parada
        r2 = fin.ruta
        paradas = r2.paradas
        cuenta = 0
        visitadas = None if traza is None else []
        encuentros = None if traza is None else []
        n = paradas.anterior(fin)
        while n is not None:
            cuenta += 1
            t = n.estacion
            i = t.id
            if visitadas is not None:
                visitadas.append((t.nombre, cuenta))
            if marca[i] == version:
                r1 = mejor_nodo[i].ruta
                if r1 is not r2:
                    total = mejor_paradas[i] + cuenta
                    mejora = False
                    if mejor_clave is None or total <= mejor_clave[0]:
                        clave = (total, 1, r1.nombre, r2.nombre, t.nombre)
                        if mejor_clave is None or clave < mejor_clave:
                            mejor_clave = clave
                            mejor_res = [(r1.nombre, o.nombre, t.nombre), (r2.nombre, t.nombre, d.nombre)]
                            mejora = True
                    if encuentros is not None:
                        encuentros.append(("encuentro", t.nombre, r1.nombre, r2.nombre, total, mejora))
            n = paradas.anterior(n)
        if traza is not None:
            traza.append(("vuelta", r2.nombre, visitadas))
            for e in encuentros:
                traza.append(e)

    return mejor_res
