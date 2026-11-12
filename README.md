# TransmiAlgoritmo · Planeador TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. Planeador de viajes sobre la red
real de TransMilenio (GTFS de julio de 2021, convertida a tres CSV).

- **Motor** (`motor/`): Python puro, con estructuras de datos implementadas por el equipo.
- **App** (`web/`): HTML, CSS y JavaScript; el motor corre en el navegador con Pyodide.

## Cómo arrancar
_Pendiente: `py app.py` (Windows) o `python3 app.py`._

## Pruebas

```
py -m unittest
```

En macOS o Linux: `python3 -m unittest`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `motor/` | Lo que evalúa el profesor: `Red` y `simular_fila`. Sin `dict`, `set`, `sorted`, etc. |
| `motor/estructuras/` | Estructuras genéricas propias: tabla hash, AVL, lista doble, pila, cola, ordenamiento |
| `api/` | Puente entre el motor y la interfaz (sin reglas del sistema) |
| `datos/` | Los tres CSV de la red |
| `web/` | Interfaz |
| `benchmarks/` | Generador de redes y mediciones (R11) |
| `tests/` | Pruebas con `unittest` (incluye el validador de reglas del motor) |
| `docs/` | Análisis, diseño, plan y decisiones |

## Documentación
- [Fase 1 · Análisis](docs/fase-1-analisis.md)
- [Fase 2 · Diseño](docs/fase-2-diseno.md)
- [Fase 3 · Plan](docs/fase-3-plan.md)

## Decisiones por requisito (R12)
_Se completa a medida que se implementa cada requisito._
