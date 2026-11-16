"""Puente entre el motor y la interfaz web (dueño: Daniel).

Corre dentro de Pyodide (en el Web Worker) y también en CPython para las
pruebas. Traduce llamadas JSON a métodos de Red y devuelve JSON.

Aquí NO hay reglas del sistema: todo requisito lo resuelve `motor/`. Lo que
este archivo calcula por su cuenta es solo para presentación y va marcado:
  - duraciones de tramo y horas de llegada ............ ESTIMADO
  - posiciones de la flota entre estaciones ............ SIMULADO
Fuera de motor/ sí se permite dict, sorted, bisect, etc.
"""

import bisect
import json
import time

from motor import Red, simular_fila
from motor.horarios import formato, minutos

_red = None
_duraciones = {}          # (ruta, a, b) -> minutos estimados del tramo a -> b
_tramos_por_ruta = {}     # ruta -> [(a, b, horas_en_a, duracion)]


def _mediana(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def _estimar_duracion(ha, hb):
    """Minutos estimados entre dos paradas consecutivas de una ruta.

    Sin identificador de viaje no sabemos qué bus es cuál. Si las dos paradas
    tienen el mismo número de pasos, se emparejan por orden (el k-ésimo bus en
    a es el k-ésimo en b: los buses de una ruta no se adelantan). Si no, se
    usa "el primer bus en b después de cada salida de a". Se toma la mediana.
    """
    difs = []
    if len(ha) == len(hb):
        for x, y in zip(ha, hb):
            d = (y - x) % 1440
            if d < 240:
                difs.append(d)
    if not difs:
        for x in ha:
            j = bisect.bisect_left(hb, x)
            y = hb[j] if j < len(hb) else hb[0] + 1440
            difs.append(y - x)
    m = _mediana(difs)
    return 2 if m is None else max(1, round(m))


def _preparar_estimaciones():
    _duraciones.clear()
    _tramos_por_ruta.clear()
    for ruta in _red.lista_rutas():
        rec = _red.recorrido(ruta)
        tramos = []
        for a, b in zip(rec, rec[1:]):
            ha, hb = _red.info_horas(ruta, a), _red.info_horas(ruta, b)
            d = _estimar_duracion(ha, hb) if ha and hb else 2
            _duraciones[(ruta, a, b)] = d
            tramos.append((a, b, ha, d))
        _tramos_por_ruta[ruta] = tramos


# ---------------------------------------------------------------- operaciones

def iniciar(carpeta):
    global _red
    t = time.perf_counter()
    _red = Red(carpeta)
    ms = (time.perf_counter() - t) * 1000
    _preparar_estimaciones()
    return {"ms_carga": round(ms, 1), "estaciones": len(_red.lista_estaciones()),
            "rutas": len(_red.lista_rutas()), "advertencias": _red.info_advertencias()}


def red_completa():
    """Estaciones y rutas para dibujar la red (refleja ediciones y cierres)."""
    estaciones = []
    for n in _red.lista_estaciones():
        abierta, buses, rutas = _red.info_estacion(n)
        estaciones.append({"n": n, "abierta": abierta, "buses": buses, "rutas": len(rutas)})
    rutas = [{"r": r, "p": _red.recorrido(r)} for r in _red.lista_rutas()]
    return {"estaciones": estaciones, "rutas": rutas}


def detalle_estacion(nombre, hora):
    info = _red.info_estacion(nombre)
    if info is None:
        return None
    abierta, buses, rutas = info
    proximos = []
    for r in rutas:
        p = _red.proximo_bus(nombre, r, hora)
        if p is not None:
            espera = (minutos(p) - minutos(hora)) % 1440
            proximos.append({"ruta": r, "hora": p, "espera": espera})
    proximos.sort(key=lambda x: (x["espera"], x["ruta"]))
    return {"nombre": nombre, "estado": _red.estado(nombre), "buses": buses,
            "rutas": rutas, "proximos": proximos}


def itinerario(origen, destino, hora):
    """R5 + R4 por tramo, con espera y llegada ESTIMADA."""
    tramos = _red.viaje(origen, destino)
    if tramos is None:
        return {"tramos": None}
    t = minutos(hora)
    res = []
    for ruta, sube, baja in tramos:
        rec = _red.recorrido(ruta)
        i, j = rec.index(sube), rec.index(baja)
        paradas = rec[i:j + 1]
        sale_txt = _red.proximo_bus(sube, ruta, formato(t % 1440))
        sale = minutos(sale_txt) if sale_txt else t
        if sale < t % 1440:
            sale += 1440 * (t // 1440 + 1)
        else:
            sale += 1440 * (t // 1440)
        viaje_min = sum(_duraciones.get((ruta, a, b), 2) for a, b in zip(paradas, paradas[1:]))
        llega = sale + viaje_min
        res.append({"ruta": ruta, "sube": sube, "baja": baja, "paradas": paradas,
                    "n": len(paradas) - 1, "sale": formato(sale % 1440), "espera": sale - t,
                    "llega": formato(llega % 1440), "minutos": viaje_min})
        t = llega
    return {"tramos": res, "llegada": formato(t % 1440), "total_min": t - minutos(hora)}


def flota(hora_min):
    """Posiciones SIMULADAS de los buses a una hora: [[a, b, fracción, duración], ...]."""
    T = hora_min % 1440
    out = []
    for ruta, tramos in _tramos_por_ruta.items():
        for a, b, ha, d in tramos:
            if not ha:
                continue
            j = bisect.bisect_right(ha, T)
            k = j - 1
            while k >= 0 and T - ha[k] < d:
                out.append([a, b, round((T - ha[k]) / d, 3), d])
                k -= 1
    return out


def pulso(hora):
    """Buses programados por tramo en la hora [h, h+1): [[a, b, cantidad], ...]."""
    inicio = (hora % 24) * 60
    conteo = {}
    for ruta, tramos in _tramos_por_ruta.items():
        for a, b, ha, d in tramos:
            c = bisect.bisect_left(ha, inicio + 60) - bisect.bisect_left(ha, inicio)
            if c:
                clave = (a, b) if a < b else (b, a)
                conteo[clave] = conteo.get(clave, 0) + c
    return [[a, b, c] for (a, b), c in conteo.items()]


def traza_viaje(origen, destino):
    """Pasos de la búsqueda de R5, listos para animar."""
    res, traza = _red.info_traza_viaje(origen, destino)
    ida, vuelta, encuentros, directos = [], [], [], []
    for e in traza:
        if e[0] == "ida":
            ida.append({"ruta": e[1], "visitadas": [list(v) for v in e[2]]})
        elif e[0] == "vuelta":
            vuelta.append({"ruta": e[1], "visitadas": [list(v) for v in e[2]]})
        elif e[0] == "directo":
            directos.append({"ruta": e[1], "paradas": e[2]})
        else:
            encuentros.append({"estacion": e[1], "ruta1": e[2], "ruta2": e[3], "paradas": e[4], "mejora": e[5]})
    tramos = None if res is None else [{"ruta": r, "paradas": _tramo(r, a, b)} for r, a, b in res]
    return {"resultado": tramos, "ida": ida, "vuelta": vuelta, "directos": directos, "encuentros": encuentros}


def _tramo(ruta, a, b):
    rec = _red.recorrido(ruta)
    return rec[rec.index(a):rec.index(b) + 1]


def _pares_sin_viaje():
    """Todos los pares (origen, destino) abiertos y distintos sin viaje con <= 1 transbordo.

    Llama a R5 (motor) una vez por par: n_E² viajes. Es un análisis para la
    interfaz, no un requisito; la regla de qué es un viaje la sigue poniendo R5.
    """
    abiertas = [n for n in _red.lista_estaciones() if _red.estado(n) == "abierta"]
    sin = set()
    for o in abiertas:
        for d in abiertas:
            if o != d and _red.viaje(o, d) is None:
                sin.add((o, d))
    return abiertas, sin


def impacto_cierre(nombre):
    """Cierra la estación (R8, queda en el historial de R9) y mide qué viajes se pierden."""
    if _red.estado(nombre) != "abierta":
        return {"cerrada": False}
    t = time.perf_counter()
    antes_abiertas, antes = _pares_sin_viaje()
    top_antes = _red.ranking(5)
    _red.cerrar(nombre)
    despues_abiertas, despues = _pares_sin_viaje()
    ms = (time.perf_counter() - t) * 1000
    nuevos = sorted(despues - antes)
    # destinos y orígenes más golpeados (cuántos pares nuevos sin viaje toca cada uno)
    golpe = {}
    for o, d in nuevos:
        golpe[o] = golpe.get(o, 0) + 1
        golpe[d] = golpe.get(d, 0) + 1
    mas_afectadas = sorted(golpe.items(), key=lambda x: (-x[1], x[0]))[:6]
    viajes = len(antes_abiertas) * (len(antes_abiertas) - 1) + len(despues_abiertas) * (len(despues_abiertas) - 1)
    pares_propios = 2 * (len(antes_abiertas) - 1)
    return {
        "cerrada": True, "estacion": nombre, "ms": round(ms), "viajes_calculados": viajes,
        "sin_antes": len(antes), "sin_despues": len(despues), "nuevos": len(nuevos),
        "pares_propios": pares_propios, "ejemplos": [list(p) for p in nuevos[:8]],
        "mas_afectadas": [list(x) for x in mas_afectadas],
        "rutas": [{"ruta": r, "paradas": _red.recorrido(r)} for r in _red.info_estacion(nombre)[2]],
        "ranking_antes": top_antes, "ranking_despues": _red.ranking(5),
    }


def correr_pruebas(avisar=None):
    """Corre toda la suite de unittest (la misma de `py -m unittest`) y avisa prueba por prueba.

    `avisar` es una función (en el navegador, una función de JavaScript) que
    recibe un JSON por cada prueba terminada. Ojo: test_web reinicia la red
    del puente, así que la interfaz debe recargar su estado al terminar.
    """
    import unittest

    class Resultado(unittest.TestResult):
        def startTest(self, prueba):
            self._t = time.perf_counter()
            super().startTest(prueba)

        def _aviso(self, prueba, estado, detalle=""):
            if avisar is None:
                return
            ident = prueba.id().split(".")
            avisar(json.dumps({"archivo": ident[1] if len(ident) > 2 else ident[0], "prueba": ident[-1],
                               "estado": estado, "ms": round((time.perf_counter() - self._t) * 1000, 1),
                               "detalle": detalle[-400:]}, ensure_ascii=False))

        def addSuccess(self, prueba):
            super().addSuccess(prueba)
            self._aviso(prueba, "ok")

        def addFailure(self, prueba, err):
            super().addFailure(prueba, err)
            self._aviso(prueba, "falla", self.failures[-1][1])

        def addError(self, prueba, err):
            super().addError(prueba, err)
            self._aviso(prueba, "error", self.errors[-1][1])

        def addSkip(self, prueba, razon):
            super().addSkip(prueba, razon)
            self._aviso(prueba, "salta", razon)

    suite = unittest.TestLoader().discover("tests", top_level_dir=".")
    resultado = Resultado()
    t = time.perf_counter()
    suite.run(resultado)
    return {"total": resultado.testsRun, "fallas": len(resultado.failures), "errores": len(resultado.errors),
            "saltadas": len(resultado.skipped), "ms": round((time.perf_counter() - t) * 1000)}


def historial():
    d, r = _red.info_historial()
    return {"deshacer": d, "rehacer": r}


def fila(llegadas, frecuencia, capacidad):
    t = time.perf_counter()
    res = simular_fila(llegadas, frecuencia, capacidad)
    return {"abordaje": res, "ms": round((time.perf_counter() - t) * 1000, 2)}


def generar_llegadas(pasajeros, minutos_pico, semilla=7):
    """Llegadas de ejemplo para R10 (presentación): más gente en el centro del pico."""
    import random
    rnd = random.Random(semilla)
    xs = []
    for _ in range(pasajeros):
        x = (rnd.random() + rnd.random() + rnd.random()) / 3     # campana suave
        xs.append(int(x * minutos_pico))
    xs.sort()
    return xs


def medir_en_vivo(factores):
    """Corre la medición de R11 en este dispositivo (Pyodide) y devuelve el JSON."""
    import random as _random
    from benchmarks import medir
    rnd = _random.Random(2021)
    tamanos, tiempos = [], {op[0]: [] for op in medir.OPERACIONES}
    for f in factores:
        tam, t, _ = medir.medir_factor(f, rnd)
        tamanos.append(tam)
        for k, v in t.items():
            tiempos[k].append(round(v, 3))
    ops = []
    for oid, req, nombre, esperado, n_es in medir.OPERACIONES:
        r = medir.razon_media(tiempos[oid])
        banda = medir.BANDAS.get(esperado)
        ver = "no se evalúa" if banda is None else ("ok" if banda[0] <= r <= banda[1] else "revisar")
        ops.append({"id": oid, "tiempos_us": tiempos[oid], "razon_media": round(r, 2) if r else None,
                    "veredicto": ver})
    return {"factores": factores, "tamanos": tamanos, "operaciones": ops}


OPERACIONES = {
    "iniciar": iniciar,
    "estado": lambda n: _red.estado(n),
    "autocompletar": lambda p, k: _red.autocompletar(p, k),
    "rango": lambda a, b: _red.rango(a, b),
    "proximo_bus": lambda e, r, h: _red.proximo_bus(e, r, h),
    "viaje": lambda o, d: _red.viaje(o, d),
    "ranking": lambda k: _red.ranking(k),
    "agregar_parada": lambda r, n, d: _red.agregar_parada(r, n, d),
    "quitar_parada": lambda r, e: _red.quitar_parada(r, e),
    "recorrido": lambda r, rev=False: _red.recorrido(r, rev),
    "cerrar": lambda n: _red.cerrar(n),
    "reabrir": lambda n: _red.reabrir(n),
    "deshacer": lambda: _red.deshacer(),
    "rehacer": lambda: _red.rehacer(),
    "rutas": lambda: _red.lista_rutas(),
    "red_completa": red_completa,
    "detalle_estacion": detalle_estacion,
    "itinerario": itinerario,
    "flota": flota,
    "pulso": pulso,
    "historial": historial,
    "traza_viaje": traza_viaje,
    "impacto_cierre": impacto_cierre,
    "fila": fila,
    "generar_llegadas": generar_llegadas,
    "medir_en_vivo": medir_en_vivo,
}


def llamar(op, args_json):
    """Punto de entrada desde JavaScript: devuelve JSON con datos y tiempo en ms."""
    try:
        args = json.loads(args_json) if args_json else []
        t = time.perf_counter()
        datos = OPERACIONES[op](*args)
        ms = (time.perf_counter() - t) * 1000
        return json.dumps({"ok": True, "datos": datos, "ms": round(ms, 3)}, ensure_ascii=False)
    except Exception as e:  # el error se muestra en la interfaz, no tumba el worker
        return json.dumps({"ok": False, "error": type(e).__name__ + ": " + str(e)}, ensure_ascii=False)
