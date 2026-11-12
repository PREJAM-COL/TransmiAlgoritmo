"""Ordenamiento y búsqueda binaria propios (docs/fase-2-diseno.md §3.6).

Dentro de motor/ no se puede usar sorted, .sort() ni bisect, así que los
implementamos aquí.
"""


def merge_sort(lista, clave=None):
    """Devuelve una lista NUEVA con los elementos ordenados. Estable.

    Versión iterativa ("de abajo hacia arriba"): primero mezcla bloques de 1,
    luego de 2, de 4… hasta cubrir todo. Así no hay recursión ni se crean
    sublistas con cortes en cada nivel.

    clave: función opcional; se evalúa UNA vez por elemento.
    Estable: si dos claves son iguales, conservan su orden original (importa
    para desempates, por ejemplo en el ranking).

    Complejidad: O(n log n) en tiempo, O(n) de espacio extra.
    """
    n = len(lista)
    if clave is None:
        claves = lista
    else:
        claves = [clave(x) for x in lista]

    orden = list(range(n))       # índices; se ordenan comparando claves[i]
    aux = [0] * n
    ancho = 1
    while ancho < n:
        i = 0
        while i < n:
            medio = i + ancho
            if medio > n:
                medio = n
            fin = i + 2 * ancho
            if fin > n:
                fin = n
            a, b, k = i, medio, i
            while a < medio and b < fin:
                # Se toma de la derecha solo si es ESTRICTAMENTE menor: estabilidad.
                if claves[orden[b]] < claves[orden[a]]:
                    aux[k] = orden[b]
                    b += 1
                else:
                    aux[k] = orden[a]
                    a += 1
                k += 1
            while a < medio:
                aux[k] = orden[a]
                a += 1
                k += 1
            while b < fin:
                aux[k] = orden[b]
                b += 1
                k += 1
            i = fin
        orden, aux = aux, orden
        ancho *= 2

    return [lista[i] for i in orden]


def limite_inferior(arreglo, x, inicio=0, fin=None):
    """Índice del primer elemento >= x en arreglo[inicio:fin] (ya ordenado).

    Si todos son menores, devuelve fin (len(arreglo) por defecto).
    Complejidad: O(log n).
    """
    if fin is None:
        fin = len(arreglo)
    izq, der = inicio, fin
    while izq < der:
        medio = (izq + der) // 2
        if arreglo[medio] < x:
            izq = medio + 1
        else:
            der = medio
    return izq
