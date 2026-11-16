"""Clase Red: fachada del contrato del motor (diapositiva 11). Integración: Daniel.

Cada método público tiene el nombre y la firma EXACTOS que prueba el script
del profesor y delega en el módulo del requisito:

    R1, R2, R3   consultas.py   (Miguel)      R4   horarios.py  (Tomás)
    R5           viaje.py       (Daniel)      R6   ranking.py   (Tomás)
    R7           edicion.py     (Daniel)      R8   cierres.py   (Miguel)
    R9           comandos.py    (Daniel)      R10  fila.py      (Tomás)
    carga        carga.py       (Tomás)

Los métodos que empiezan con "info_" o "lista_" no son del contrato: son de
solo lectura para la interfaz y también respetan las reglas del motor.
"""

from . import carga, comandos, consultas, edicion, horarios, ranking, viaje
from .estructuras.ordenamiento import merge_sort


class Red:
    """Red de TransMilenio cargada desde una carpeta con los tres CSV."""

    def __init__(self, carpeta):
        carga.cargar(self, carpeta)

    @staticmethod
    def clave_parada(ruta, estacion):
        return carga.clave_parada(ruta, estacion)

    # ------------------------------------------------------------ Consultas

    def estado(self, nombre):
        """R1. "abierta", "cerrada" o "no existe"."""
        return consultas.estado(self, nombre)

    def autocompletar(self, prefijo, k):
        """R2. Hasta k estaciones abiertas que empiezan por prefijo, en orden alfabético."""
        return consultas.autocompletar(self, prefijo, k)

    def rango(self, desde, hasta):
        """R3. Estaciones abiertas entre desde y hasta (ambos incluidos), en orden alfabético."""
        return consultas.rango(self, desde, hasta)

    def proximo_bus(self, estacion, ruta, hora):
        """R4. Hora "HH:MM" del siguiente bus de la ruta en la estación, o None."""
        return horarios.proximo_bus(self, estacion, ruta, hora)

    def viaje(self, origen, destino):
        """R5. Lista de tramos (ruta, sube, baja) con a lo sumo un transbordo, [] o None."""
        return viaje.viaje(self, origen, destino)

    def ranking(self, k):
        """R6. Las k estaciones abiertas con más buses al día."""
        return ranking.ranking(self, k)

    # ------------------------------------------------------------ Operación

    def agregar_parada(self, ruta, nueva, despues_de):
        """R7. Inserta nueva después de despues_de en la ruta. True si se pudo."""
        p = edicion.preparar_agregar(self, ruta, nueva, despues_de)
        if p is None:
            return False
        return comandos.ejecutar(self, comandos.ComandoAgregar(p[0], p[1]))

    def quitar_parada(self, ruta, estacion):
        """R7. Quita la estación de la ruta. True si se pudo."""
        p = edicion.preparar_quitar(self, ruta, estacion)
        if p is None:
            return False
        return comandos.ejecutar(self, comandos.ComandoQuitar(p[0], p[1]))

    def recorrido(self, ruta, al_reves=False):
        """R7. Lista de estaciones de la ruta, en su sentido o al revés."""
        return edicion.recorrido(self, ruta, al_reves)

    def cerrar(self, nombre):
        """R8. Cierra una estación abierta. True si cambió algo."""
        e = self._estaciones.obtener(nombre) if isinstance(nombre, str) else None
        if e is None or not e.abierta:
            return False
        return comandos.ejecutar(self, comandos.ComandoCerrar(e))

    def reabrir(self, nombre):
        """R8. Reabre una estación cerrada. True si cambió algo."""
        e = self._estaciones.obtener(nombre) if isinstance(nombre, str) else None
        if e is None or e.abierta:
            return False
        return comandos.ejecutar(self, comandos.ComandoReabrir(e))

    def deshacer(self):
        """R9. Deshace el último cambio. True si había algo para deshacer."""
        return comandos.deshacer(self)

    def rehacer(self):
        """R9. Rehace el último cambio deshecho. True si había algo para rehacer."""
        return comandos.rehacer(self)

    # ------------------------------------------------------------ Solo lectura (interfaz)

    def lista_estaciones(self):
        """Todas las estaciones (abiertas y cerradas), en orden alfabético."""
        res = []
        for e in self._por_id:
            res.append(e.nombre)
        return _ordenados(res)

    def lista_rutas(self):
        """Nombres de todas las rutas, en orden alfabético."""
        return [r for r in self._nombres_rutas]

    def info_estacion(self, nombre):
        """(abierta, buses_dia, [rutas que paran]) o None si no existe."""
        e = self._estaciones.obtener(nombre) if isinstance(nombre, str) else None
        if e is None:
            return None
        rutas = _ordenados([m.parada.ruta.nombre for m in e.membresias.adelante()])
        return (e.abierta, e.buses_dia, rutas)

    def info_horas(self, ruta, estacion):
        """Horas programadas (minutos) de la ruta en la estación, ordenadas."""
        nodo = self._paradas.obtener(carga.clave_parada(ruta, estacion))
        return [] if nodo is None else [m for m in nodo.horas]

    def info_historial(self):
        """(descripciones para deshacer, descripciones para rehacer), del fondo a la cima."""
        return ([c.descripcion() for c in self._deshacer.elementos()],
                [c.descripcion() for c in self._rehacer.elementos()])

    def info_traza_viaje(self, origen, destino):
        """(resultado de R5, pasos de la búsqueda) para la vista "rayos X"."""
        return viaje.traza_viaje(self, origen, destino)

    def info_advertencias(self):
        """Filas de los CSV que se ignoraron al cargar."""
        return self._advertencias


def _ordenados(lista):
    return merge_sort(lista)
