"""R8 · Cerrar y reabrir estaciones (dueño: Miguel).

Una estación cerrada no aparece en búsquedas, autocompletado, rangos ni
ranking, y nadie sube, baja ni transborda ahí. Con nuestras estructuras eso
se logra así:

  - la bandera `abierta` de la estación (R1, R4, R5 la consultan en O(1));
  - sacarla del AVL de abiertas (R2, R3 ya no la ven): O(log n);
  - sacarla del AVL del ranking (R6 ya no la ve): O(log n).

Reabrir hace lo contrario. Estas funciones solo APLICAN el cambio; el
registro para deshacer/rehacer lo hace R9 (comandos.py).
"""

from .ranking import entrar, salir


def aplicar_cierre(red, e):
    e.abierta = False
    red._abiertas.eliminar(e.nombre)
    salir(red, e)


def aplicar_reapertura(red, e):
    e.abierta = True
    red._abiertas.insertar(e.nombre, e)
    entrar(red, e)
