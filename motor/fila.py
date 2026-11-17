"""R10 · Fila de abordaje en hora pico (dueño: Tomás). Función suelta, fuera de Red.

Modelo (enunciado del profesor):
  - `llegadas`: segundo en que llega cada persona. Pueden venir DESORDENADAS.
  - Los buses salen en t = f, 2f, 3f, ... (f = `frecuencia`, en segundos).
  - Cada bus se lleva hasta `capacidad` personas de la fila, en orden de
    llegada (FIFO). Quien llega justo cuando sale un bus alcanza a subir.
  - Se devuelve, en el MISMO orden de `llegadas`, el segundo en que salió el
    bus de cada persona.

Ejemplo: simular_fila([30, 5, 5, 70], 60, 2) -> [120, 60, 60, 120].

Pasos:
  1. Orden de llegada. Si `llegadas` ya viene ordenada (se revisa en O(P)),
     se usa tal cual. Si no, se ordenan los pares (segundo, posición) con
     nuestro merge sort: O(P log P). La posición desempata, así dos personas
     que llegan en el mismo segundo suben en el orden en que aparecen.
  2. Simulación con una ColaCircular: encolar y desencolar son O(1). Con
     list.pop(0) cada desencolar costaría O(P) y el total sería O(P^2).
  3. Salto de buses vacíos: si la fila está vacía y la siguiente persona llega
     más tarde, se salta directo al primer bus que sale en o después de su
     llegada. Así cada bus que se procesa sube al menos a una persona.

Complejidad: O(P) si las llegadas vienen ordenadas y O(P log P) si no;
O(P) de espacio. P = número de personas. No depende de la hora de llegada
(una llegada en el segundo 1.000.000 no simula un millón de buses vacíos).
"""

from .estructuras.cola_circular import ColaCircular
from .estructuras.ordenamiento import merge_sort


def _es_numero(x):
    return (isinstance(x, int) or isinstance(x, float)) and not isinstance(x, bool)


def simular_fila(llegadas, frecuencia, capacidad):
    """R10. Segundo en que salió el bus de cada persona, en el orden de `llegadas`.

    llegadas: segundos de llegada (en cualquier orden).
    frecuencia: segundos entre buses (> 0); el primero sale en `frecuencia`.
    capacidad: cupo por bus (entero > 0).
    Devuelve [] si no hay personas o los parámetros no son válidos.
    """
    if llegadas is None or not _es_numero(frecuencia) or not isinstance(capacidad, int):
        return []
    p = len(llegadas)
    if p == 0 or not frecuencia > 0 or not capacidad > 0:
        return []
    for x in llegadas:
        if not _es_numero(x):
            return []

    # 1. Orden de llegada (índices de las personas, de la primera a la última).
    ordenada = True
    for i in range(1, p):
        if llegadas[i] < llegadas[i - 1]:
            ordenada = False
            break
    if ordenada:
        orden = list(range(p))
    else:
        pares = merge_sort([(llegadas[i], i) for i in range(p)])
        orden = [par[1] for par in pares]

    # 2 y 3. Simulación bus por bus.
    res = [0] * p
    cola = ColaCircular()
    j = 0              # siguiente persona (en orden de llegada) que aún no está en la fila
    k = 1              # número del bus actual: sale en k * frecuencia
    abordaron = 0
    while abordaron < p:
        salida = k * frecuencia
        if cola.vacia() and salida < llegadas[orden[j]]:
            # nadie esperando: saltar al primer bus que sale en o después de esa llegada
            a = llegadas[orden[j]]
            k = int(a // frecuencia)
            if k * frecuencia < a:
                k += 1
            if k < 1:
                k = 1
            salida = k * frecuencia
        while j < p and llegadas[orden[j]] <= salida:
            cola.encolar(orden[j])
            j += 1
        suben = 0
        while suben < capacidad and not cola.vacia():
            res[cola.desencolar()] = salida
            suben += 1
            abordaron += 1
        k += 1
    return res
