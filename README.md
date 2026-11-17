# TransmiAlgoritmo · Planeador TransMilenio

**Ver la app en línea: https://transmialgortimomtd.netlify.app**

Proyecto final de Estructuras de Datos y Algoritmos. Una app para buscar estaciones, planear viajes y saber a qué hora pasa el bus, sobre la red real de TransMilenio (GTFS de julio de 2021, convertida a tres CSV por el profesor).

- **Motor** (`motor/`): Python puro. Todas las estructuras (tabla hash, AVL, listas dobles, pila, cola, ordenamiento) están implementadas por el equipo, sin `dict`, `set`, `sorted`, `heapq`, `bisect` ni librerías.
- **App** (`web/`): HTML, CSS y JavaScript sin compilación. El motor corre **dentro del navegador** con [Pyodide](https://pyodide.org): es el mismo código que evalúa el profesor.

## Cómo arrancar

```
py app.py
```

En macOS o Linux: `python3 app.py`. Abre el navegador en `http://localhost:8000/web/`. No hay que instalar nada; la primera vez se necesita internet para descargar Pyodide.

## Publicar en Netlify

Se publica la **raíz del repositorio** como sitio estático: no hay servidor ni comando de compilación. La app (`web/`) lee con `fetch` el motor, los datos y las pruebas. `netlify.toml` y `_redirects` envían `/` a `/web/`, y `index.html` en la raíz hace lo mismo por si el servidor no aplica esas reglas.

- **Desde GitHub:** "Add new site → Import an existing project", sin comando de build y con la carpeta de publicación `.`.
- **A mano:** arrastrar la carpeta del proyecto (o el zip) a Netlify Drop.

## Pruebas y mediciones

```
py -m unittest                 # 132 pruebas: estructuras, R1–R10, invariantes, reglas del motor, contrato, app, conversión
py benchmarks/medir.py         # redes ×1, ×2, ×4, ×8 → benchmarks/resultados/cpython.json (lo lee el panel R11)
```

`tests/test_reglas_motor.py` revisa el árbol sintáctico de todo `motor/` y falla si aparece algo prohibido.

## Estructura

| Carpeta | Contenido |
|---|---|
| `motor/` | `Red` y `simular_fila`. `red.py` es una fachada que delega cada requisito en su módulo |
| `motor/estructuras/` | Tabla hash, AVL, lista doble, pila, cola circular, merge sort y búsqueda binaria |
| `api/puente.py` | Traduce llamadas JSON de la interfaz a métodos de `Red`. Sin reglas del sistema |
| `web/` | Interfaz: vistas Viaje, Red, Operación, Hora pico y Rendimiento |
| `benchmarks/` | Generador de redes ×f y medición de R11 |
| `tests/` | `unittest`, mini red de prueba en `tests/fixtures/mini/` |
| `datos/` | Los tres CSV |
| `docs/` | Análisis, diseño, plan y guías del proyecto |

## Conversión del GTFS

```
py conversion/gtfs_a_csv.py GTFS.zip datos            # también acepta una carpeta con los .txt
py conversion/gtfs_a_csv.py GTFS.zip datos --servicio ID   # solo un calendario (service_id)
```

Lee `stops.txt`, `routes.txt`, `trips.txt` y `stop_times.txt` y escribe los tres CSV con las reglas de la diapositiva 9:
- **Nombres:** MAYÚSCULAS y sin tildes. Los vagones de una misma estación (`parent_station`) se unen en una sola estación.
- **Rutas:** una por sentido. Cada recorrido distinto de una ruta se numera (`B10-1`, `B10-2`…); si hay uno solo, conserva el nombre (`A51`).
- **Horas:** ≥ 24 pasan a módulo 24 h.

Se prueba con un GTFS pequeño hecho a mano (`tests/fixtures/gtfs_mini`), y el motor lee el resultado sin advertencias. Como no tenemos el zip original de 54 MB, no comprobamos que reproduzca exactamente los CSV del profesor; por ejemplo, su forma de numerar las rutas.

## Decisiones sobre los datos

- **Horas ≥ 24** (el GTFS trae cosas como `25:10`): se toman módulo 24 h, así `25:10` es `01:10`. Los CSV del profesor ya vienen así (71 filas `00:xx` que continúan viajes de la noche). `proximo_bus` "da la vuelta": después del último bus devuelve el primero del día siguiente.
- **Filas repetidas** en `horarios.csv` (1.580): se cuentan, porque cada fila es un paso de bus programado.
- **Archivos desordenados**: no se asume ningún orden. Las rutas se ordenan por la columna `orden` y las horas por conteo.
- **Filas inválidas** (estación o ruta inexistente, hora mal escrita): se ignoran y se cuentan.
- **Sin coordenadas** en los CSV: el mapa se dibuja a partir del grafo (disposición por fuerzas).

## Decisiones por requisito (R12)

Notación: n_E = estaciones, n_P = pares (ruta, estación), n_H = filas de horarios, L = paradas de una ruta, h = horas de un par (ruta, estación), k = tamaño pedido, m = tamaño de la respuesta, P = pasajeros.

### Carga · `Red(carpeta)` — Tomás
- **Estructuras**: tablas hash para estaciones, rutas y paradas; listas dobles para las rutas; AVL para abiertas y ranking.
- **Algoritmo**: las horas se ordenan por **conteo**. Hay 1.440 cubetas, una por minuto: cada fila cae en la suya y luego se vacían en orden. Así todas las listas de horas quedan ordenadas sin comparar nada. Los AVL se construyen balanceados desde una lista ordenada con merge sort.
- **Descartado**: ordenar cada lista de horas con merge sort (O(n_H log h)) y llenar los AVL insertando uno por uno (O(n log n)).
- **Complejidad**: O(n_E log n_E + n_P log L + n_H). Medido: ×2,06 al duplicar la red; entre 0,37 y 0,47 s con la red real en CPython, según el equipo.

### R1 · `estado(nombre)` — Miguel
- **Estructura**: tabla hash propia con direccionamiento abierto y sondeo lineal. La capacidad es potencia de 2, se usan lápidas al borrar y crece cuando la carga pasa de 0,7. El hash es polinomial (base 31) con mezcla de bits.
- **Descartado**: búsqueda lineal (O(n)); arreglo ordenado con búsqueda binaria o AVL (O(log n)). Es la consulta más frecuente, así que conviene O(1).
- **Complejidad**: O(1) esperado; n = n_E. Medido: ×1,04.
- **Hallazgo honesto**: con la red real (147 estaciones), `x in lista` es más rápido, porque corre en C. Pero se duplica con n y la tabla no: empatan cerca de la red ×4 (unas 590 estaciones) y en la red ×8 la tabla hash ya es el doble de rápida.

### R2 · `autocompletar(prefijo, k)` — Miguel
- **Estructura**: AVL que contiene **solo las estaciones abiertas**, ordenado por nombre.
- **Algoritmo**: en orden alfabético, los nombres con un mismo prefijo están juntos y el primero es el menor nombre ≥ prefijo. Se baja una vez por el árbol con una pila explícita y se avanza en orden mientras el nombre empiece por el prefijo.
- **Descartado**:
  - Un arreglo ordenado: tiene que saltar las cerradas, y con muchas cerradas degenera a O(n).
  - Un trie: excelente para prefijos, pero incómodo para R3 y para excluir cerradas.
- **Complejidad**: O(log n + k); n = estaciones abiertas. Medido: ×1,17.

### R3 · `rango(desde, hasta)` — Miguel
- **Estructura y algoritmo**: el mismo AVL. Se busca el primer nombre ≥ `desde` y se avanza mientras sea ≤ `hasta`. Ambos extremos están incluidos y no tienen que existir.
- **Descartado**: recorrer todas las estaciones y filtrar (O(n)).
- **Complejidad**: O(log n + m); m = tamaño de la respuesta. Medido con m ≈ 10: ×1,00.

### R4 · `proximo_bus(estacion, ruta, hora)` — Tomás
- **Estructura**: cada parada (nodo de la ruta) guarda su lista de horas en minutos, ordenada; la tabla hash encuentra la parada en O(1).
- **Algoritmo**: búsqueda binaria propia del primer minuto ≥ la hora pedida. Si no hay más ese día, se toma el primero (vuelta al día siguiente).
- **Descartado**:
  - Recorrido lineal (O(h)), que medido es 2 veces más lento.
  - Una tabla de 1.440 respuestas por par: O(1), pero gasta 1.440 × n_P de memoria.
- **Complejidad**: O(log h); h no depende del tamaño de la red. Medido: ×1,01.

### R5 · `viaje(origen, destino)` — Daniel
- **Algoritmo**: búsqueda desde los dos extremos que se encuentra en el medio, sobre un grafo estación ↔ ruta.
  1. Desde el origen se avanza por cada ruta que para ahí contando paradas, y se anota la mejor forma de llegar a cada estación abierta.
  2. Desde el destino se retrocede por cada ruta que llega a él.
  3. Donde ambos frentes se tocan con rutas distintas hay un transbordo.
  4. Desempate: menos paradas; luego directo antes que transbordo; luego orden alfabético de las rutas y de la estación.
- **Por qué basta guardar una ruta por estación**: si la mejor ruta hasta t es la misma r2 que sigue hasta el destino, entonces r2 pasa por origen, t y destino. Ese viaje ya es directo y es igual o mejor. Se verificó contra fuerza bruta en todos los pares de la mini red y en 300 pares reales con estaciones cerradas.
- **Marcas por versión**: en vez de limpiar los arreglos en cada consulta (O(n_E)), se incrementa un contador.
- **Descartado**:
  - BFS sobre estaciones: no controla los transbordos.
  - BFS o Dijkstra sobre estados (estación, ruta): son correctos, pero exploran mucho más de lo necesario para un solo transbordo.
  - A*: no hay coordenadas para la heurística.
  - Fuerza bruta: O(n_R² · L).
- **Complejidad**: O(suma de L de las rutas del origen y del destino). R5 no se evalúa en rendimiento.
- **Hallazgos**: 518 de 21.462 pares no tienen viaje con un transbordo o menos. "Menos paradas" no significa "llegar antes": por eso la app muestra la espera de cada tramo.

### R6 · `ranking(k)` — Tomás
- **Estructura**: un segundo AVL (la misma clase) con clave `(-buses_dia, nombre)`. Solo contiene abiertas.
- **Algoritmo**: los k primeros en orden. Cerrar, reabrir, quitar o agregar una parada con horarios reubica una estación en O(log n).
- **Descartado**:
  - Recalcular y ordenar en cada consulta: medido, unos 1.460 µs contra ~1,5 µs en la red ×8.
  - Un montículo: costaría O(k log n) por consulta y la eliminación arbitraria es incómoda.
- **Complejidad**: consulta O(log n + k); cambio O(log n); n = estaciones abiertas. Medido: ×1,02.

### R7 · `agregar_parada`, `quitar_parada`, `recorrido` — Daniel
- **Estructura**: lista doblemente enlazada con nodo centinela por ruta. Cada estación tiene además una lista de "membresías" (las rutas que paran ahí).
- **Algoritmo**: la tabla hash encuentra el nodo `despues_de` y se enlazan 4 punteros. `recorrido` avanza o retrocede por la lista.
- **Descartado**: un arreglo por ruta, que tiene inserción y borrado en O(L). Medido en una ruta larga, el arreglo crece al doble y la lista se mantiene constante. Además R5 y R9 necesitan referencias estables a los nodos.
- **Complejidad**: agregar y quitar O(1) esperado + O(log n_E) para reubicar el ranking; recorrido O(L). Medido: ×1,05 y ×1,07.

### R8 · `cerrar`, `reabrir` — Miguel
- **Estructura**: una bandera en la estación (R1, R4 y R5 la consultan en O(1)) y la salida o entrada de los dos AVL (abiertas y ranking).
- **Descartado**: dejar las cerradas en las estructuras y filtrarlas en cada consulta. Eso degrada R2, R3 y R6 a O(n) en el peor caso.
- **Complejidad**: O(log n_E). Medido: ×1,11.

### R9 · `deshacer`, `rehacer` — Daniel
- **Estructura**: dos pilas de **comandos** (patrón Comando). Cada cambio sabe `aplicar` y `revertir`; `quitar_parada` guarda el nodo anterior para reinsertarlo en el mismo sitio. Un cambio nuevo vacía la pila de rehacer, y las operaciones que fallan no entran al historial.
- **Verificación**: 10.000 operaciones aleatorias en la red real; al deshacerlas todas, la red queda idéntica a la original.
- **Descartado**: guardar copias completas de la red por cada cambio (O(n) de tiempo y memoria por operación).
- **Complejidad**: O(1) de las pilas más el costo de la operación que se revierte. Medido: ×1,11.

### R10 · `simular_fila(llegadas, frecuencia, capacidad)` — Tomás
- **Estructura**: cola circular sobre un arreglo, que encola y desencola en O(1).
- **Algoritmo**: los buses salen en t = 0, f, 2f, …; cada uno sube hasta `capacidad` personas en orden FIFO. Si la fila está vacía, se salta al primer bus después de la siguiente llegada, así nunca se simulan buses vacíos. Devuelve el minuto en que aborda cada pasajero.
- **Descartado**: `list.pop(0)`, que cuesta O(P) por pasajero. En hora pico saturada, la cola circular crece ×2 al duplicar P y `pop(0)` crece ×4, hasta unos 880 ms con 160.000 pasajeros.
- **Complejidad**: O(P); P = pasajeros. Medido: ×2,01.

## Panel de rendimiento (R11)
La vista **Rendimiento** muestra cada operación con la red ×1…×8, la curva medida contra la esperada (banda), el veredicto y la explicación. Todas las operaciones evaluadas quedan dentro de su banda. Además tiene:
- **La carrera**: la estructura elegida contra la descartada, con la velocidad de cada una sacada del tiempo medido.
- **Medir en este dispositivo**: repite la medición con Pyodide en el navegador de quien la abre.
- **Pruebas en vivo**: corre las 132 pruebas dentro del navegador, mostrándolas una por una.

## Otras funciones de la app
- **Rayos X de R5** (vista Viaje): anima la búsqueda real del motor. Los dos frentes, los encuentros y el mejor viaje salen de `traza_viaje`, la misma búsqueda de `viaje()` con anotaciones.
- **Vista 3D**: recorre el viaje desde una cámara detrás del articulado. Three.js se descarga solo al abrirla; el suelo es la red esquemática, no la geografía de Bogotá.
- **Impacto de un cierre** (vista Operación): al cerrar una estación, se recalcula R5 para todos los pares y se muestra cuántos viajes se pierden.
- **Plano de metro**: cambia la disposición de la red a conexiones de 0°, 45° y 90°.
- **Modo sustentación** (botón ▶ Sustentar): un recorrido guiado por R1–R11 con demostraciones en vivo.

## Datos en pantalla
- **Programado**: sale tal cual de `horarios.csv`.
- **Estimado**: horas de llegada, calculadas con la duración típica de cada tramo.
- **Simulado**: la posición de los buses entre estaciones y las llegadas de ejemplo de Hora pico.

La app nunca dice "en tiempo real".

## Equipo
Ver [integrantes.md](integrantes.md).
