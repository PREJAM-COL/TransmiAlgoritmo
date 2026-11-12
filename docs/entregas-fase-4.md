# Entregas de la Fase 4 · E0 y E1

> Todos los archivos ya están creados en esta carpeta y probados: `py -m unittest` → **53 pruebas en verde** y el validador sin hallazgos en `motor/`.
> Miguel entrega a cada integrante sus archivos; **cada uno los lee, los entiende y los sube desde su cuenta**, en su rama, con un *pull request*.
> Los pasos de Git (crear repositorio, clonar, ramas) están en [guia-fase-4-arranque.md](guia-fase-4-arranque.md).

## Orden obligatorio

Las pruebas importan el paquete `motor`, y `motor/__init__.py` importa `red.py` y `fila.py`. Por eso el contrato de Daniel debe entrar a `main` **antes** que cualquier otra rama de E1.

```
1. Miguel  · e0-estructura     ─► main
2. Tomás, Daniel · e0-nombre   ─► main   (confirman su rol)
3. Daniel  · e1-contrato       ─► main   ← desbloquea todo lo demás
4. En paralelo: el resto de ramas de E1 (cualquier orden)
```

---

## 1. Miguel · rama `e0-estructura` (primer commit del repositorio)

| Archivo | Qué es |
|---|---|
| `.gitignore` | Ignora `__pycache__`, `.pptx`, redes generadas |
| `README.md` | Versión mínima; R12 se completa después |
| `integrantes.md` | Reparto de roles y requisitos |
| `datos/estaciones.csv`, `datos/rutas.csv`, `datos/horarios.csv` | Los CSV del profesor (ya movidos a `datos/`) |
| `docs/` completa | Fases 1–3, esta guía y la carpeta `decisiones/` |
| `prototipos/maqueta-viaje.html` | Maqueta aprobada |
| `motor/estructuras/__init__.py` | Vacío (convierte la carpeta en paquete) |
| `api/__init__.py`, `tests/__init__.py` | Vacíos |
| `tests/fixtures/.gitkeep`, `benchmarks/.gitkeep`, `web/.gitkeep`, `conversion/.gitkeep` | Mantienen las carpetas vacías en Git |

Mensaje: `chore: estructura inicial, documentación de fases 1-3 y datos`

> Como es el primer commit, este va directo a `main` (todavía no hay nada que proteger). Después de este, activar la protección de `main`.

---

## 2. Daniel

### `e1-contrato` (va primero)

| Archivo | Qué es |
|---|---|
| `motor/__init__.py` | Exporta `Red` y `simular_fila` |
| `motor/red.py` | Clase `Red` con los 13 métodos y el constructor con la firma exacta; por ahora devuelven valores neutros |
| `motor/fila.py` | `simular_fila` con su firma; devuelve `[]` (Tomás la implementa en E3) |

Mensaje: `motor: esqueleto del contrato (Red y simular_fila)` · Revisa: **Miguel**

### `e1-lista-doble`

| Archivo | Qué es |
|---|---|
| `motor/estructuras/lista_doble.py` | Lista doble con centinela: insertar/quitar en O(1) |
| `motor/modelo.py` | `Estacion`, `Ruta`, `NodoParada`, `Membresia` (usa la lista doble) |
| `tests/test_lista_doble.py` | 7 pruebas, incluida una aleatoria de 5.000 operaciones contra `list` |

Mensaje: `motor: lista doblemente enlazada y modelo de objetos` · Revisa: **Miguel**

### `e1-pila`

| Archivo | Qué es |
|---|---|
| `motor/estructuras/pila.py` | Pila LIFO (base de R9) |
| `tests/test_pila.py` | 5 pruebas |

Mensaje: `motor: pila para deshacer/rehacer` · Revisa: **Tomás**

**Lo que Daniel debe poder explicar:**
- Por qué el centinela elimina los casos especiales.
- Por qué `quitar` limpia los punteros y cómo se reinserta en el mismo sitio guardando `nodo.ant` (clave para R9).
- Por qué `modelo.py` usa `__slots__`.

---

## 3. Tomás

### `e1-validador`

| Archivo | Qué es |
|---|---|
| `tests/test_reglas_motor.py` | Recorre con `ast` todo `motor/` y falla ante cualquier construcción prohibida; incluye pruebas del propio validador |

Mensaje: `tests: validador de reglas del motor` · Revisa: **Daniel**

### `e1-contrato-pruebas`

| Archivo | Qué es |
|---|---|
| `tests/test_contrato.py` | Verifica con `inspect` los nombres y parámetros exactos del contrato |

Mensaje: `tests: verificación de firmas del contrato` · Revisa: **Daniel**

### `e1-cola`

| Archivo | Qué es |
|---|---|
| `motor/estructuras/cola_circular.py` | Cola FIFO circular con crecimiento ×2 (base de R10) |
| `tests/test_cola_circular.py` | 5 pruebas, incluida una de 1.000.000 de elementos |

Mensaje: `motor: cola circular` · Revisa: **Daniel**

### `e1-ordenamiento`

| Archivo | Qué es |
|---|---|
| `motor/estructuras/ordenamiento.py` | `merge_sort` iterativo y estable; `limite_inferior` (búsqueda binaria) |
| `tests/test_ordenamiento.py` | 9 pruebas comparando contra `sorted` y `bisect` |

Mensaje: `motor: merge sort y búsqueda binaria` · Revisa: **Miguel**

**Lo que Tomás debe poder explicar:**
- Por qué la cola circular es O(1) y `list.pop(0)` no.
- Qué significa que el merge sort sea estable y por qué importa en el ranking.
- Por qué el validador prohíbe todo `in` en comparaciones aunque `"x" in cadena` esté permitido. Es una decisión conservadora con excepciones documentadas.

---

## 4. Miguel · E1

### `e1-tabla-hash`

| Archivo | Qué es |
|---|---|
| `motor/estructuras/tabla_hash.py` | Sondeo lineal, potencia de 2, lápidas, crecimiento con carga > 0,7, hash polinomial con mezcla de bits; `estadisticas()` para el panel |
| `tests/test_tabla_hash.py` | 10 pruebas: colisiones forzadas, lápidas, crecimiento, 100.000 operaciones contra `dict` |

Mensaje: `motor: tabla hash con direccionamiento abierto` · Revisa: **Daniel**

### `e1-avl`

| Archivo | Qué es |
|---|---|
| `motor/estructuras/avl.py` | AVL con rotaciones, `desde(clave)` con pila explícita, construcción O(n) desde ordenados, `verificar()` |
| `tests/test_avl.py` | 8 pruebas: inserción ordenada sin degenerar, todos los casos de eliminación, claves tupla del ranking, 10.000 operaciones contra una lista ordenada |

Mensaje: `motor: árbol AVL con recorrido desde una clave` · Revisa: **Tomás**

**Lo que Miguel debe poder explicar:**
- Por qué una lápida y no vaciar la casilla (lo demuestra `test_lapida_no_corta_la_cadena`).
- Por qué la capacidad es potencia de 2.
- Las cuatro rotaciones del AVL.
- Por qué `desde` cuesta O(log n + k).

---

## Criterio de salida de E1

En `main`, con todas las ramas integradas:

```bash
py -m unittest
```

Debe decir `OK` con 53 pruebas. Después sigue **E2**: carga de los CSV (Tomás) y R1, R2, R3, R8 (Miguel), R4, R6 (Tomás).
