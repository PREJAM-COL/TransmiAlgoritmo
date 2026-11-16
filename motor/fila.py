"""Modelo: los buses salen en t = 0, f, 2f, ...; cada uno se lleva hasta
`capacidad` personas que ya estén en la fila, en orden de llegada (FIFO).

La fila es una ColaCircular: encolar y desencolar son O(1). Con list.pop(0)
cada desencolar costaría O(P) y con cientos de miles de pasajeros el total
sería O(P^2).

Salto de buses vacíos: si la fila está vacía y el siguiente pasajero llega
más tarde, se salta directo al primer bus que sale después de su llegada.
Así cada bus que se procesa sube al menos a una persona y el total es O(P),
aunque las llegadas empiecen en el minuto 1.000.000.

Complejidad: O(P) en tiempo y espacio, P = número de pasajeros.
"""

from .estructuras.cola_circular import ColaCircular


def simular_fila(llegadas, frecuencia, capacidad):
    """Minuto en que aborda cada pasajero, en el mismo orden de `llegadas`.

    llegadas: minutos de llegada en orden no decreciente.
    frecuencia: minutos entre buses (> 0).
    capacidad: pasajeros máximos por bus (> 0).
    Devuelve [] si no hay pasajeros o los parámetros no son válidos.
    """
    if llegadas is None or frecuencia is None or capacidad is None:
        return []
    p = len(llegadas)
    if p == 0 or not frecuencia > 0 or not capacidad > 0:
        return []

    res = [0] * p
    cola = ColaCircular()
    i = 0          # siguiente pasajero que todavía no llega a la fila
    t = 0          # hora del bus actual
    abordaron = 0
    while abordaron < p:
        if cola.vacia() and t < llegadas[i]:
            q = llegadas[i] // frecuencia
            t = q * frecuencia
            if t < llegadas[i]:
                t = (q + 1) * frecuencia
        while i < p and llegadas[i] <= t:
            cola.encolar(i)
            i += 1
        suben = 0
        while suben < capacidad and not cola.vacia():
            res[cola.desencolar()] = t
            suben += 1
            abordaron += 1
        t += frecuencia
    return res
