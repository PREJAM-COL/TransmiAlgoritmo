"""Mide cada operación del motor con redes ×1, ×2, ×4, ×8 (R11). Dueño: Tomás.

Método (el mismo del Taller 1): duplicar n y mirar cuánto crece el tiempo.
    O(1) o O(log n)  -> la razón t(2n)/t(n) se queda cerca de 1
    O(n)             -> cerca de 2
    O(n log n)       -> un poco más de 2
    O(n^2)           -> cerca de 4

Para cada operación se corren muchas consultas aleatorias (semilla fija), se
repite el lote varias veces y se toma la MEDIANA del tiempo por consulta.
Las operaciones que cambian la red se miden en pares (cambio + deshacer)
para que la red quede igual para la siguiente medición.

También se comparan las estructuras elegidas contra la alternativa descartada
(las alternativas viven aquí, fuera de motor/, porque usan lo prohibido).

Uso:
    py benchmarks/medir.py                 (×1, ×2, ×4, ×8)
    py benchmarks/medir.py 1 2 4 8 16      (factores a elección)
Escribe benchmarks/resultados/cpython.json, que lee el panel de rendimiento.
"""

import bisect
import json
import os
import platform
import random
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from benchmarks.generar_red import generar  # noqa: E402
from motor import Red, simular_fila  # noqa: E402
from motor.estructuras.lista_doble import ListaDoble, NodoLista  # noqa: E402
from motor.estructuras.ordenamiento import limite_inferior, merge_sort  # noqa: E402

RESULTADOS = os.path.join(RAIZ, "benchmarks", "resultados")

# id, requisito, nombre visible, complejidad esperada, qué es n
OPERACIONES = [
    ("carga", "Carga", "Red(carpeta)", "O(n)", "filas de los tres CSV (domina n_H, el conteo es lineal)"),
    ("estado", "R1", "estado(nombre)", "O(1)", "estaciones"),
    ("autocompletar", "R2", "autocompletar(prefijo, 5)", "O(log n + k)", "estaciones abiertas"),
    ("rango", "R3", "rango(desde, hasta) con ~10 resultados", "O(log n + m)", "estaciones abiertas"),
    ("proximo_bus", "R4", "proximo_bus(estacion, ruta, hora)", "O(log h)", "h = horas del par; no depende del tamaño de la red"),
    ("ranking", "R6", "ranking(10)", "O(log n + k)", "estaciones abiertas"),
    ("editar", "R7", "agregar_parada + deshacer", "O(log n)", "estaciones (el ranking se reubica); el enlace es O(1)"),
    ("recorrido", "R7", "recorrido(ruta)", "O(L)", "L = paradas de la ruta; no depende del tamaño de la red"),
    ("cerrar", "R8", "cerrar + deshacer", "O(log n)", "estaciones"),
    ("deshacer", "R9", "deshacer + rehacer de un cierre", "O(log n)", "estaciones"),
    ("fila", "R10", "simular_fila con P = 20.000 × factor", "O(P)", "P = pasajeros"),
    ("viaje", "R5", "viaje(origen, destino)", "No se evalúa", "suma de longitudes de las rutas del origen y destino"),
]

BANDAS = {
    "O(1)": (0.7, 1.4), "O(log n + k)": (0.7, 1.5), "O(log n + m)": (0.7, 1.5),
    "O(log h)": (0.7, 1.4), "O(log n)": (0.7, 1.5), "O(L)": (0.7, 1.4),
    "O(n)": (1.6, 2.6), "O(P)": (1.6, 2.6), "O(n^2)": (3.2, 5.0),
}


def mediana(xs):
    xs = sorted(xs)
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def cronometrar(funcion, repeticiones=5):
    """Mediana de `repeticiones` corridas de funcion(); devuelve segundos."""
    tiempos = []
    for _ in range(repeticiones):
        t = time.perf_counter_ns()
        funcion()
        tiempos.append((time.perf_counter_ns() - t) / 1e9)
    return mediana(tiempos)


def por_consulta(red_fn, consultas, repeticiones=5):
    """Microsegundos por consulta (mediana de lotes)."""
    def lote():
        for c in consultas:
            red_fn(*c)
    return cronometrar(lote, repeticiones) / len(consultas) * 1e6


# ---------------------------------------------------------------- alternativas descartadas

def fila_ingenua(llegadas, f, cap):
    res = [0] * len(llegadas)
    fila, i, t, hechos = [], 0, 0, 0
    while hechos < len(llegadas):
        if not fila and t < llegadas[i]:
            t = -(-llegadas[i] // f) * f
        while i < len(llegadas) and llegadas[i] <= t:
            fila.append(i)
            i += 1
        for _ in range(cap):
            if not fila:
                break
            res[fila.pop(0)] = t          # O(P) cada vez
            hechos += 1
        t += f
    return res


def medir_factor(factor, rnd):
    carpeta = generar(factor)
    tiempo_carga = cronometrar(lambda: Red(carpeta), 3) * 1e6
    red = Red(carpeta)
    nombres = red.lista_estaciones()
    rutas = red.lista_rutas()
    Q = 2000

    est = [(rnd.choice(nombres),) for _ in range(Q)]
    pref = [(rnd.choice(nombres)[:3], 5) for _ in range(Q)]
    rangos = []
    for _ in range(Q):
        i = rnd.randrange(len(nombres) - 11)
        rangos.append((nombres[i], nombres[i + 10]))
    pares = []
    for _ in range(Q):
        r = rnd.choice(rutas)
        pares.append((rnd.choice(red.recorrido(r)), r, "%02d:%02d" % (rnd.randrange(24), rnd.randrange(60))))
    rutas_q = [(rnd.choice(rutas),) for _ in range(Q)]
    viajes = [(rnd.choice(nombres), rnd.choice(nombres)) for _ in range(300)]

    def editar(ruta):
        rec = red.recorrido(ruta)
        nueva = nombres[rnd.randrange(len(nombres))]
        if red.agregar_parada(ruta, nueva, rec[0]):
            red.deshacer()

    def cerrar(nombre):
        if red.cerrar(nombre):
            red.deshacer()

    red.cerrar(nombres[0])

    def deshacer_rehacer():
        red.deshacer()
        red.rehacer()

    P = 20000 * factor
    llegadas, t = [], 0
    for _ in range(P):
        t += rnd.randint(0, 1)
        llegadas.append(t)

    tiempos = {
        "carga": tiempo_carga,
        "estado": por_consulta(red.estado, est),
        "autocompletar": por_consulta(red.autocompletar, pref),
        "rango": por_consulta(red.rango, rangos),
        "proximo_bus": por_consulta(red.proximo_bus, pares),
        "ranking": por_consulta(red.ranking, [(10,)] * Q),
        "editar": por_consulta(editar, rutas_q[:500]),
        "recorrido": por_consulta(red.recorrido, rutas_q),
        "cerrar": por_consulta(cerrar, est[:1000]),
        "deshacer": por_consulta(deshacer_rehacer, [()] * 1000),
        "fila": cronometrar(lambda: simular_fila(llegadas, 4, 160), 3) * 1e6,
        "viaje": por_consulta(red.viaje, viajes, 3),
    }

    # Comparaciones contra la alternativa descartada --------------------------
    lista_nombres = list(nombres)
    horas = [(red.info_horas(r, e), int(h[:2]) * 60 + int(h[3:])) for e, r, h in pares[:500]]
    abiertas_con_cerradas = list(nombres)            # arreglo ordenado; la mitad cerradas
    cerradas = set(nombres[::2])

    def r2_arreglo(p, k):
        i = bisect.bisect_left(abiertas_con_cerradas, p)
        res = []
        while i < len(abiertas_con_cerradas) and len(res) < k and abiertas_con_cerradas[i].startswith(p):
            if abiertas_con_cerradas[i] not in cerradas:
                res.append(abiertas_con_cerradas[i])
            i += 1
        return res

    def r6_recalcular(k):
        return [e.nombre for e in merge_sort([e for e in red._por_id if e.abierta], clave=lambda e: (-e.buses_dia, e.nombre))[:k]]

    def r4_lineal(h, m):
        for i in range(len(h)):
            if h[i] >= m:
                return i
        return len(h)

    # R7: una ruta larga de L = 2000 × factor paradas, insertar y quitar en el medio.
    L = 2000 * factor
    lista = ListaDoble()
    nodos = []
    for i in range(L):
        n = NodoLista(i)
        lista.insertar_al_final(n)
        nodos.append(n)
    medio = nodos[L // 2]
    arreglo = list(range(L))

    def r7_lista():
        nuevo = NodoLista(-1)
        lista.insertar_despues(medio, nuevo)
        lista.quitar(nuevo)

    def r7_arreglo():
        arreglo.insert(L // 2, -1)
        arreglo.pop(L // 2)

    # R10: hora pico saturada (llegan más personas de las que caben): la fila crece.
    saturada = [i // 400 for i in range(P)]          # 400 personas por minuto, buses de 160 cada 4 min

    comparaciones = {
        "R1": (por_consulta(red.estado, est), por_consulta(lambda n: n in lista_nombres, est[:300])),
        "R4": (por_consulta(limite_inferior, horas), por_consulta(r4_lineal, horas)),
        "R6": (por_consulta(red.ranking, [(10,)] * 500), por_consulta(r6_recalcular, [(10,)] * 50, 3)),
        "R10": (cronometrar(lambda: simular_fila(saturada, 4, 160), 3) * 1e6,
                cronometrar(lambda: fila_ingenua(saturada, 4, 160), 1) * 1e6),
        "R2": (por_consulta(red.autocompletar, pref), por_consulta(r2_arreglo, pref)),
        "R7": (por_consulta(r7_lista, [()] * 2000), por_consulta(r7_arreglo, [()] * 2000)),
    }
    tamano = {"estaciones": len(nombres), "rutas": len(rutas), "paradas": len(red._paradas),
              "horarios": sum(e.buses_dia for e in red._por_id), "pasajeros_R10": P}
    return tamano, tiempos, comparaciones


COMPARACIONES = [
    ("R1", "Tabla hash", "Búsqueda lineal en la lista"),
    ("R2", "AVL solo de abiertas", "Arreglo ordenado saltando cerradas (50 % cerradas)"),
    ("R4", "Búsqueda binaria propia", "Recorrido lineal de las horas"),
    ("R6", "AVL de ranking", "Recalcular y ordenar en cada consulta"),
    ("R7", "Lista doble: insertar y quitar en medio (L = 2.000 × factor)", "Arreglo: list.insert y list.pop en medio"),
    ("R10", "Cola circular (hora pico saturada)", "list.pop(0) (hora pico saturada)"),
]


def razon_media(valores):
    razones = [b / a for a, b in zip(valores, valores[1:]) if a > 0]
    if not razones:
        return None
    p = 1.0
    for r in razones:
        p *= r
    return p ** (1 / len(razones))


def main(factores):
    rnd = random.Random(2021)
    tamanos, tiempos, comps = [], {op[0]: [] for op in OPERACIONES}, {c[0]: ([], []) for c in COMPARACIONES}
    for f in factores:
        print("Midiendo red x%d…" % f, flush=True)
        tam, t, c = medir_factor(f, rnd)
        tamanos.append(tam)
        for k, v in t.items():
            tiempos[k].append(round(v, 3))
        for k, (a, b) in c.items():
            comps[k][0].append(round(a, 3))
            comps[k][1].append(round(b, 3))

    salida = {
        "fuente": "CPython %s · %s" % (platform.python_version(), platform.system()),
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "factores": factores,
        "tamanos": tamanos,
        "operaciones": [],
        "comparaciones": [],
    }
    for oid, req, nombre, esperado, n_es in OPERACIONES:
        r = razon_media(tiempos[oid])
        banda = BANDAS.get(esperado)
        veredicto = "no se evalúa" if banda is None else ("ok" if banda[0] <= r <= banda[1] else "revisar")
        salida["operaciones"].append({
            "id": oid, "requisito": req, "nombre": nombre, "esperado": esperado, "n_es": n_es,
            "tiempos_us": tiempos[oid], "razon_media": round(r, 2) if r else None,
            "banda": banda, "veredicto": veredicto,
        })
        print("  %-4s %-40s %-14s razón %.2f  %s" % (req, nombre, esperado, r or 0, veredicto))
    for req, elegida, alternativa in COMPARACIONES:
        a, b = comps[req]
        salida["comparaciones"].append({"requisito": req, "elegida": elegida, "alternativa": alternativa,
                                        "elegida_us": a, "alternativa_us": b})
    os.makedirs(RESULTADOS, exist_ok=True)
    ruta = os.path.join(RESULTADOS, "cpython.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print("Resultados en", ruta)


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [1, 2, 4, 8])
