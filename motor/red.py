"""Clase Red: fachada del contrato del motor (diapositiva 11).

Cada método público tiene el nombre y la firma EXACTOS que prueba el script
del profesor. Por ahora es un esqueleto: devuelve valores neutros con el mismo
tipo que el contrato aprobado (docs/fase-1-analisis.md §15). Cada dueño
reemplaza el cuerpo de sus métodos en las etapas E2 y E3.

Dueños por requisito (docs/fase-3-plan.md §1):
    Miguel: R1 estado, R2 autocompletar, R3 rango, R8 cerrar/reabrir
    Tomás:  R4 proximo_bus, R6 ranking  (R10 está en fila.py)
    Daniel: R5 viaje, R7 agregar/quitar/recorrido, R9 deshacer/rehacer
"""


class Red:
    """Red de TransMilenio cargada desde una carpeta con los tres CSV."""

    def __init__(self, carpeta):
        # E2 (Tomás): carga real en motor/carga.py.
        self._carpeta = carpeta

    # ------------------------------------------------------------ Consultas

    def estado(self, nombre):
        """R1. Devuelve "abierta", "cerrada" o "no existe"."""
        return "no existe"

    def autocompletar(self, prefijo, k):
        """R2. Hasta k estaciones abiertas que empiezan por prefijo, en orden alfabético."""
        return []

    def rango(self, desde, hasta):
        """R3. Estaciones abiertas entre desde y hasta (ambos incluidos), en orden alfabético."""
        return []

    def proximo_bus(self, estacion, ruta, hora):
        """R4. Hora "HH:MM" del siguiente bus de la ruta en la estación, o None."""
        return None

    def viaje(self, origen, destino):
        """R5. Lista de tramos (ruta, sube, baja) con a lo sumo un transbordo, [] o None."""
        return None

    def ranking(self, k):
        """R6. Las k estaciones abiertas con más buses al día."""
        return []

    # ------------------------------------------------------------ Operación

    def agregar_parada(self, ruta, nueva, despues_de):
        """R7. Inserta nueva después de despues_de en la ruta. True si se pudo."""
        return False

    def quitar_parada(self, ruta, estacion):
        """R7. Quita la estación de la ruta. True si se pudo."""
        return False

    def recorrido(self, ruta, al_reves=False):
        """R7. Lista de estaciones de la ruta, en su sentido o al revés."""
        return []

    def cerrar(self, nombre):
        """R8. Cierra una estación abierta. True si cambió algo."""
        return False

    def reabrir(self, nombre):
        """R8. Reabre una estación cerrada. True si cambió algo."""
        return False

    def deshacer(self):
        """R9. Deshace el último cambio. True si había algo para deshacer."""
        return False

    def rehacer(self):
        """R9. Rehace el último cambio deshecho. True si había algo para rehacer."""
        return False
