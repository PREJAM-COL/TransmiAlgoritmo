"""Conversión del GTFS de TransMilenio a los tres CSV que lee el motor (dueño: Tomás).

Uso:
    py conversion/gtfs_a_csv.py RUTA_AL_GTFS(.zip o carpeta) CARPETA_DE_SALIDA [--servicio ID]

Lee los archivos estándar de GTFS (https://gtfs.org/schedule/reference/):
    stops.txt       stop_id, stop_name, parent_station
    routes.txt      route_id, route_short_name
    trips.txt       route_id, service_id, trip_id, direction_id
    stop_times.txt  trip_id, departure_time (o arrival_time), stop_id, stop_sequence

y escribe, con las reglas de la diapositiva 9:
    estaciones.csv  nombre
    rutas.csv       ruta, orden, estacion
    horarios.csv    ruta, estacion, hora

Decisiones (documentadas en el README):
  1. NOMBRES: MAYÚSCULAS, sin tildes, espacios normalizados. Si una parada tiene
     estación padre (parent_station), se usa el nombre del padre: los vagones y
     plataformas de una misma estación se vuelven una sola estación.
  2. UNA RUTA POR SENTIDO: cada secuencia distinta de estaciones de un mismo
     route_short_name es una ruta. Si hay una sola, se llama igual que la ruta
     ("A51"); si hay varias, se numeran "B10-1", "B10-2"… ordenadas por sentido
     (direction_id) y luego por cantidad de viajes.
  3. ESTACIONES REPETIDAS: dos paradas seguidas de la misma estación (dos
     vagones) cuentan una vez; si un recorrido vuelve a pasar por una estación,
     se conserva solo la primera vez (el formato no permite repetidos en una ruta).
  4. HORAS: "HH:MM:SS" → "HH:MM". El GTFS trae horas ≥ 24 para viajes que pasan
     de medianoche ("25:10:00"): se toman módulo 24 h ("01:10"), la misma regla
     que usa el motor.
  5. CALENDARIOS: por defecto se incluyen los viajes de todos los service_id;
     con --servicio se puede quedar con uno solo (por ejemplo, días hábiles).

Fuera de motor/ se permite cualquier librería; aquí basta la estándar.
"""

import csv
import io
import os
import sys
import unicodedata
import zipfile


def normalizar(nombre):
    """'Héroes  ' -> 'HEROES'; 'Calle 26 - Av. El Dorado' -> 'CALLE 26 - AV. EL DORADO'."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.upper().split())


def minutos(hora):
    """'25:10:00' -> 70 (01:10). Devuelve None si no es una hora válida."""
    partes = (hora or "").strip().split(":")
    if len(partes) < 2 or not partes[0].isdigit() or not partes[1].isdigit():
        return None
    return (int(partes[0]) * 60 + int(partes[1])) % 1440


def hhmm(m):
    return "%02d:%02d" % (m // 60, m % 60)


class FuenteGTFS:
    """Lee archivos de un .zip o de una carpeta, con o sin BOM."""

    def __init__(self, ruta):
        self.ruta = ruta
        self.zip = zipfile.ZipFile(ruta) if zipfile.is_zipfile(ruta) else None

    def filas(self, nombre):
        if self.zip:
            candidatos = [n for n in self.zip.namelist() if n.split("/")[-1] == nombre]
            if not candidatos:
                raise FileNotFoundError(nombre + " no está en el GTFS")
            texto = io.TextIOWrapper(self.zip.open(candidatos[0]), encoding="utf-8-sig", newline="")
        else:
            texto = open(os.path.join(self.ruta, nombre), encoding="utf-8-sig", newline="")
        with texto:
            for fila in csv.DictReader(texto):
                yield {k.strip(): (v or "").strip() for k, v in fila.items() if k}


def convertir(origen, destino, servicio=None):
    """Convierte el GTFS de `origen` y escribe los tres CSV en `destino`. Devuelve un resumen."""
    g = FuenteGTFS(origen)

    # 1. Estaciones: cada parada se lleva al nombre de su estación padre
    paradas = {fila["stop_id"]: fila for fila in g.filas("stops.txt")}

    def estacion_de(stop_id):
        p = paradas.get(stop_id)
        if p is None:
            return None
        padre = p.get("parent_station")
        if padre and padre in paradas:
            p = paradas[padre]
        nombre = normalizar(p.get("stop_name", ""))
        return nombre or None

    # 2. Rutas y viajes
    nombre_ruta = {f["route_id"]: (f.get("route_short_name") or f.get("route_long_name") or f["route_id"]).strip()
                   for f in g.filas("routes.txt")}
    viajes = {}
    for f in g.filas("trips.txt"):
        if servicio and f.get("service_id") != servicio:
            continue
        sentido = f.get("direction_id") or "0"
        viajes[f["trip_id"]] = (nombre_ruta.get(f["route_id"], f["route_id"]), sentido)

    # 3. Paradas de cada viaje, en orden
    por_viaje = {}
    for f in g.filas("stop_times.txt"):
        if f["trip_id"] not in viajes:
            continue
        hora = f.get("departure_time") or f.get("arrival_time")
        por_viaje.setdefault(f["trip_id"], []).append((int(f.get("stop_sequence") or 0), f["stop_id"], hora))

    # 4. Cada viaje se reduce a su secuencia de estaciones (sin repetidos) con sus horas
    patrones = {}   # (ruta, sentido, secuencia) -> lista de viajes [(estacion, minutos), ...]
    descartadas = 0
    for trip_id, filas in por_viaje.items():
        filas.sort()
        secuencia, horas, vistas = [], [], set()
        for _, stop_id, hora in filas:
            est, m = estacion_de(stop_id), minutos(hora)
            if est is None or m is None:
                descartadas += 1
                continue
            if est in vistas:          # vagón repetido o recorrido que vuelve: solo la primera vez
                continue
            vistas.add(est)
            secuencia.append(est)
            horas.append(m)
        if len(secuencia) < 2:
            continue
        ruta, sentido = viajes[trip_id]
        patrones.setdefault((ruta, sentido, tuple(secuencia)), []).append(horas)

    # 5. Nombres de ruta: "A51" si hay un solo recorrido; "B10-1", "B10-2"… si hay varios
    por_ruta = {}
    for (ruta, sentido, sec), lista in patrones.items():
        por_ruta.setdefault(ruta, []).append((sentido, -len(lista), sec, lista))
    salida_rutas, salida_horarios, usadas = [], [], set()
    for ruta in sorted(por_ruta):
        variantes = sorted(por_ruta[ruta])
        for k, (_, _, sec, lista) in enumerate(variantes, start=1):
            nombre = ruta if len(variantes) == 1 else "%s-%d" % (ruta, k)
            for orden, est in enumerate(sec, start=1):
                salida_rutas.append((nombre, orden, est))
                usadas.add(est)
            for horas in lista:
                for est, m in zip(sec, horas):
                    salida_horarios.append((nombre, est, hhmm(m)))

    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(destino, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre"])
        for est in sorted(usadas):
            w.writerow([est])
    with open(os.path.join(destino, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "orden", "estacion"])
        w.writerows(salida_rutas)
    with open(os.path.join(destino, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "estacion", "hora"])
        w.writerows(salida_horarios)
    return {"estaciones": len(usadas), "rutas": len({r for r, _, _ in salida_rutas}),
            "paradas": len(salida_rutas), "horarios": len(salida_horarios), "filas_descartadas": descartadas}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    servicio = None
    if "--servicio" in argv:
        i = argv.index("--servicio")
        servicio = argv[i + 1] if i + 1 < len(argv) else None
        args = [a for a in args if a != servicio]
    if len(args) != 2:
        print(__doc__.split("\n\n")[1])
        return 1
    r = convertir(args[0], args[1], servicio)
    print("Listo: %(estaciones)d estaciones, %(rutas)d rutas, %(paradas)d paradas, %(horarios)d horarios "
          "(%(filas_descartadas)d filas descartadas)." % r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
