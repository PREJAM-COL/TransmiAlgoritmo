# TransmiAlgoritmo · Planeador TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos: un motor que responde las consultas R1 a R10 sobre la red de TransMilenio (los tres CSV del profesor) y una app web que lo usa.

- **Motor** (`motor/`): Python puro. Toda la lógica de los requisitos vive aquí. Las estructuras (tabla hash, AVL, listas dobles, pila, cola circular, merge sort, ordenamiento por conteo, búsqueda binaria) las implementamos nosotros: no se usan `dict`, `set`, `sorted`, `.sort()`, `min`/`max` sobre colecciones, búsquedas con `in`, `index` o `count`, ni librerías externas (solo `csv` de la librería estándar para leer los archivos).
- **Front** (`web/`): HTML, CSS y JavaScript, sin compilación. Solo llama al motor: el motor corre **dentro del navegador** con [Pyodide](https://pyodide.org) y es el mismo código que se evalúa.

## App desplegada

**https://transmialgortimomtd.netlify.app**

## Cómo arrancar

```
py app.py
```

En macOS o Linux: `python3 app.py`. Abre el navegador en `http://localhost:8000/web/`. No hay que instalar nada; la primera vez se necesita internet para descargar Pyodide.

Usar el motor directamente desde Python:

```python
from motor import Red, simular_fila

red = Red("datos")
red.estado("RICAURTE")                       # "ABIERTA"
red.viaje("PORTAL AMERICAS", "CALLE 100")    # [("E32", "PORTAL AMERICAS", "SIMON BOLIVAR"), ("B44-1", "SIMON BOLIVAR", "CALLE 100")]
simular_fila([30, 5, 5, 70], 60, 2)          # [120, 60, 60, 120]
```

Pruebas y mediciones:

```
py -m unittest            # 136 pruebas: estructuras, R1–R10, casos borde, invariantes, reglas del motor, contrato, app
py benchmarks/medir.py    # redes de 10.000, 20.000, 40.000 y 80.000 estaciones → benchmarks/resultados/cpython.json
```

`tests/test_reglas_motor.py` recorre el árbol sintáctico de todo `motor/` y falla si aparece algo prohibido.

## Contrato

| Método | Req. | Devuelve |
|---|---|---|
| `Red(carpeta)` | carga | La red cargada desde los tres CSV, todas las estaciones abiertas |
| `estado(nombre)` | R1 | `"ABIERTA"`, `"CERRADA"` o `"NO EXISTE"` |
| `autocompletar(prefijo, k)` | R2 | Hasta k estaciones abiertas que empiezan por el prefijo, en orden alfabético |
| `rango(desde, hasta)` | R3 | Estaciones abiertas entre los dos nombres (inclusive), en orden alfabético |
| `proximo_bus(estacion, ruta, hora)` | R4 | `"HH:MM"` del siguiente bus, o `None` si no hay más ese día |
| `viaje(origen, destino)` | R5 | Lista de tramos `(ruta, sube_en, baja_en)`: 1 si es directo, 2 con transbordo; `None` si no hay viaje |
| `ranking(k)` | R6 | Lista de `(nombre, buses_por_dia)` de las k abiertas con más buses, de mayor a menor |
| `agregar_parada(ruta, nueva, despues_de)` / `quitar_parada(ruta, estacion)` | R7 | `True` o `False` |
| `recorrido(ruta, al_reves=False)` | R7 | Lista de nombres en orden (`[]` si la ruta no existe) |
| `cerrar(nombre)` / `reabrir(nombre)` | R8 | `True` si cambió el estado |
| `deshacer()` / `rehacer()` | R9 | `True` si deshizo o rehizo algo |
| `simular_fila(llegadas, frecuencia, capacidad)` | R10 | Segundo en que salió el bus de cada persona, en el orden de `llegadas` |

Nunca se devuelven diccionarios ni conjuntos. Casos borde cubiertos por las pruebas: estación inexistente o cerrada, ruta inexistente, hora inválida, viaje imposible, deshacer o rehacer sin nada pendiente, parámetros inválidos de R10. Con origen igual a destino, `viaje` devuelve `[]` (no hay que tomar ningún bus).

## Decisiones por requisito (R12)

Notación usada en las O grandes:

| Símbolo | Qué es |
|---|---|
| n | Número de estaciones (n_A: solo las abiertas) |
| n_P | Pares (ruta, estación), es decir, paradas |
| n_H | Filas de `horarios.csv` |
| L | Paradas de una ruta |
| h | Horas de un par (ruta, estación) |
| k | Tamaño pedido (R2, R6) |
| m | Tamaño de la respuesta (R3) |
| P | Personas en la fila (R10) |

"Medido" es la razón promedio del tiempo cada vez que la red se duplica (10.000 → 20.000 → 40.000 → 80.000 estaciones, ver R11). Cerca de 1 significa que no depende de n; cerca de 2, lineal.

### Carga · `Red(carpeta)` — Tomás
- **Estructuras**: tablas hash para estaciones, rutas y paradas; una lista doble por ruta; dos AVL (abiertas y ranking).
- **Algoritmo**: las horas se ordenan por **conteo**: hay 1.440 cubetas, una por minuto; cada fila cae en la suya y luego se vacían en orden, así todas las listas de horas quedan ordenadas sin comparar. Las paradas de cada ruta se ordenan por la columna `orden` con merge sort. Los AVL se construyen balanceados desde una lista ordenada, en O(n).
- **Descartado**: ordenar cada lista de horas con merge sort (O(n_H log h)); llenar los AVL insertando uno por uno (O(n log n)).
- **O grande**: O(n log n + n_P log L + n_H). En la práctica domina la lectura de las filas, que es lineal; la razón medida queda un poco por encima de 2 por el manejo de memoria de Python con más de un millón de objetos.
- **Medido**: ×2,35 al duplicar; 43,6 s con 80.000 estaciones, 1,05 millones de paradas y 1,9 millones de horarios.

### R1 · `estado(nombre)` — Miguel
- **Estructura**: tabla hash propia con direccionamiento abierto y sondeo lineal. La capacidad es potencia de 2, se usan lápidas al borrar y crece cuando la carga pasa de 0,7. El hash es un polinomio sobre los bytes del nombre, módulo el primo 2^61 − 1, con una mezcla final de bits; cada casilla guarda el hash de su clave para no recalcularlo.
- **Algoritmo**: se busca el nombre en la tabla; si no está, `"NO EXISTE"`; si está, la bandera de la estación dice `"ABIERTA"` o `"CERRADA"`.
- **Descartado**: búsqueda lineal (O(n)); arreglo ordenado con búsqueda binaria o AVL (O(log n)). Es la consulta más frecuente, así que conviene O(1).
- **O grande**: O(1) esperado; n = estaciones.
- **Medido**: ×1,04. La búsqueda lineal (`x in lista`) es 210 veces más lenta con 80.000 estaciones y se duplica con n.

### R2 · `autocompletar(prefijo, k)` — Miguel
- **Estructura**: AVL que contiene **solo las estaciones abiertas**, ordenado por nombre.
- **Algoritmo**: en orden alfabético, los nombres con un mismo prefijo están juntos y el primero es el menor nombre ≥ prefijo. Se baja una vez por el árbol con una pila explícita y se avanza en orden mientras el nombre empiece por el prefijo.
- **Descartado**: un arreglo ordenado, que tendría que saltar las cerradas una por una (con muchas cerradas degenera a O(n)); un trie, cómodo para prefijos pero no para R3 ni para excluir cerradas.
- **O grande**: O(log n_A + k); n_A = estaciones abiertas.
- **Medido**: ×1,02. Resultado honesto: contra un arreglo ordenado con `bisect` (que corre en C) y la mitad de las estaciones cerradas al azar, el arreglo responde un poco más rápido (3,1 µs contra 4,1 µs con 80.000 estaciones). El AVL se mantiene porque cerrar y reabrir (R8) en un arreglo ordenado cuesta O(n) y en el AVL O(log n).

### R3 · `rango(desde, hasta)` — Miguel
- **Estructura y algoritmo**: el mismo AVL. Se busca el primer nombre ≥ `desde` y se avanza mientras sea ≤ `hasta`. Los extremos se incluyen y no tienen que existir.
- **Descartado**: recorrer todas las estaciones y filtrar (O(n)).
- **O grande**: O(log n_A + m); m = estaciones en la respuesta.
- **Medido** con m ≈ 10: ×1,21.

### R4 · `proximo_bus(estacion, ruta, hora)` — Tomás
- **Estructura**: cada parada (nodo de la ruta) guarda su arreglo de horas en minutos, ya ordenado por la carga; la tabla hash encuentra la parada en O(1).
- **Algoritmo**: búsqueda binaria propia del primer minuto ≥ la hora pedida. Si ya pasó el último bus del día, devuelve `None`. También `None` si la estación no existe o está cerrada, la ruta no para ahí o la hora no es válida.
- **Descartado**: recorrer las horas una por una (O(h)); una tabla de 1.440 respuestas por parada (O(1), pero 1.440 × n_P de memoria).
- **O grande**: O(log h); h = horas de esa ruta en esa estación. No depende de n.
- **Medido**: ×1,06.

### R5 · `viaje(origen, destino)` — Daniel
- **Algoritmo**: búsqueda desde los dos extremos, que se encuentra en el medio, sobre el grafo estación ↔ ruta.
  1. Desde el origen se avanza por cada ruta que para ahí, contando paradas, y se anota la mejor forma de llegar a cada estación abierta.
  2. Desde el destino se retrocede por cada ruta que llega a él.
  3. Donde los dos frentes se tocan con rutas distintas hay un transbordo.
  4. Gana el viaje con **menos paradas**; en empate, el directo, y luego el orden alfabético de las rutas y de la estación.
- **Por qué basta guardar una ruta por estación**: si la mejor ruta hasta t es la misma r2 que sigue hasta el destino, r2 pasa por el origen, por t y por el destino; ese viaje ya es directo y es igual o mejor.
- **Marcas por versión**: en vez de limpiar los arreglos en cada consulta (O(n)), se incrementa un contador.
- **Descartado**: BFS sobre estaciones (no controla los transbordos); BFS o Dijkstra sobre estados (estación, ruta), correctos pero exploran mucho más de lo necesario para un solo transbordo; fuerza bruta.
- **O grande**: O(suma de L de las rutas que pasan por el origen y por el destino). R5 no se evalúa en rendimiento.
- **Verificado** contra fuerza bruta en todos los pares de la mini red y en 300 pares de la red real con estaciones cerradas.

### R6 · `ranking(k)` — Tomás
- **Estructura**: un segundo AVL (la misma clase) con clave `(-buses_por_dia, nombre)`, solo con estaciones abiertas.
- **Algoritmo**: se leen los k primeros en orden y se devuelven como `(nombre, buses_por_dia)`. Cerrar, reabrir, quitar o agregar una parada con horarios reubica la estación en O(log n).
- **Descartado**: recalcular y ordenar en cada consulta (O(n log n)): con 80.000 estaciones tarda 660 ms contra 5 µs del AVL. Un montículo: O(k log n) por consulta y la eliminación de una estación cualquiera es incómoda.
- **O grande**: consulta O(log n_A + k); cada cambio O(log n).
- **Medido**: ×1,02.

### R7 · `agregar_parada`, `quitar_parada`, `recorrido` — Daniel
- **Estructura**: lista doblemente enlazada con nodo centinela por ruta. Cada estación tiene además la lista de las rutas que paran en ella.
- **Algoritmo**: la tabla hash encuentra el nodo `despues_de` (o la parada a quitar) y se cambian 4 punteros. `recorrido` avanza o retrocede por la lista.
- **Descartado**: un arreglo por ruta, que inserta y borra en O(L). Medido en una ruta de 80.000 paradas, el arreglo tarda 28,6 µs por operación y la lista 0,5 µs. Además R5 y R9 necesitan referencias estables a los nodos.
- **O grande**: agregar y quitar O(1) esperado + O(log n) para reubicar la estación en el ranking; recorrido O(L).
- **Medido**: agregar + deshacer ×1,21; recorrido ×1,12.

### R8 · `cerrar`, `reabrir` — Miguel
- **Estructura**: una bandera en la estación (R1, R4 y R5 la consultan en O(1)) y la salida o entrada de los dos AVL (abiertas y ranking).
- **Descartado**: dejar las cerradas en las estructuras y filtrarlas en cada consulta, que degrada R2, R3 y R6 a O(n) en el peor caso.
- **O grande**: O(log n).
- **Medido**: ×1,08.

### R9 · `deshacer`, `rehacer` — Daniel
- **Estructura**: dos pilas de **comandos**. Cada cambio sabe aplicarse y revertirse; `quitar_parada` guarda el nodo anterior para reinsertarlo en el mismo sitio. Un cambio nuevo vacía la pila de rehacer, y las operaciones que fallan no entran al historial.
- **Descartado**: guardar una copia completa de la red por cada cambio (O(n) de tiempo y memoria por operación).
- **O grande**: O(1) de las pilas más el costo de revertir la operación (O(log n) para R7 y R8).
- **Medido**: ×1,10. Verificado con 10.000 operaciones aleatorias: al deshacerlas todas, la red queda idéntica.

### R10 · `simular_fila(llegadas, frecuencia, capacidad)` — Tomás
- **Modelo**: las llegadas están en segundos y pueden venir desordenadas. Los buses salen en `frecuencia`, `2·frecuencia`, …; cada uno se lleva hasta `capacidad` personas en orden de llegada (quien llega justo cuando sale el bus alcanza a subir). Se devuelve, en el mismo orden de `llegadas`, el segundo en que salió el bus de cada persona. Ejemplo: `simular_fila([30, 5, 5, 70], 60, 2)` → `[120, 60, 60, 120]`.
- **Estructuras**: merge sort propio para el orden de llegada y una cola circular sobre un arreglo (encolar y desencolar en O(1)).
- **Algoritmo**:
  1. Si las llegadas ya vienen ordenadas (se revisa en O(P)), se usan tal cual; si no, se ordenan los pares (segundo, posición) con merge sort. La posición desempata: dos personas que llegan en el mismo segundo suben en el orden en que aparecen.
  2. Bus por bus, se encolan las personas que ya llegaron y suben hasta `capacidad`.
  3. Si la fila está vacía, se salta directo al primer bus que sale después de la siguiente llegada, así nunca se simulan buses vacíos.
- **Descartado**: `list.pop(0)` como fila, que cuesta O(P) por persona. En hora pico saturada (160.000 personas) tarda 1,23 s contra 0,17 s de la cola circular, y crece ×4 al duplicar P.
- **O grande**: O(P log P) si hay que ordenar y O(P) si ya vienen ordenadas; P = personas.
- **Medido** con llegadas desordenadas: ×2,52 (un poco más que ×2 por el log P).

## Panel de rendimiento (R11)

La vista **Rendimiento** de la app muestra cada operación medida con redes de **10.000, 20.000, 40.000 y 80.000 estaciones**, los mismos tamaños con que mide el profesor. Esas redes son 68, 136, 272 y 544 copias de la red real unidas entre sí con rutas puente (`benchmarks/generar_red.py`); cada copia se queda con 1 de cada 40 horarios para que la red de 80.000 quepa en memoria (aun así tiene 1,9 millones). Para cada operación se dibuja la curva medida contra la esperada (una banda), la razón al duplicar y el veredicto. Las 11 operaciones evaluadas quedan dentro de su banda, de forma coherente con las O grandes de arriba:

| Req. | Operación | O grande | Razón medida al duplicar |
|---|---|---|---|
| Carga | `Red(carpeta)` | O(n log n + n_P log L + n_H) | ×2,35 |
| R1 | `estado` | O(1) | ×1,04 |
| R2 | `autocompletar(prefijo, 5)` | O(log n_A + k) | ×1,02 |
| R3 | `rango` con ~10 resultados | O(log n_A + m) | ×1,21 |
| R4 | `proximo_bus` | O(log h) | ×1,06 |
| R6 | `ranking(10)` | O(log n_A + k) | ×1,02 |
| R7 | `agregar_parada` + deshacer | O(log n) | ×1,21 |
| R7 | `recorrido` | O(L) | ×1,12 |
| R8 | `cerrar` + deshacer | O(log n) | ×1,08 |
| R9 | `deshacer` + `rehacer` | O(log n) | ×1,10 |
| R10 | `simular_fila`, P = 2 por estación, desordenadas | O(P log P) | ×2,52 |
| R5 | `viaje` | no se evalúa | ×1,24 |

Además:
- **La carrera**: la estructura elegida contra la descartada, con la velocidad de cada una sacada del tiempo medido.
- **Medir en este dispositivo**: repite la medición con Pyodide en el navegador de quien la abre, con redes más pequeñas.
- **Pruebas en vivo**: corre las 136 pruebas dentro del navegador.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `motor/` | El motor: `Red` y `simular_fila`. `red.py` es la fachada del contrato y delega cada requisito en su módulo |
| `motor/estructuras/` | Tabla hash, AVL, lista doble, pila, cola circular, merge sort y búsqueda binaria |
| `web/` | El front: vistas Viaje, Red, Operación, Hora pico y Rendimiento. `web/python/puente.py` traduce las llamadas de la interfaz a métodos de `Red` |
| `datos/` | Los tres CSV |
| `tests/` | Pruebas con `unittest` y la mini red de prueba (`tests/fixtures/mini/`) |
| `benchmarks/` | Generador de redes grandes y medición de R11 |
| `conversion/` | Script que convierte un GTFS a los tres CSV |
| `docs/` | Análisis, diseño y plan del proyecto |

## Decisiones sobre los datos

- **Archivos desordenados**: no se asume ningún orden. Las rutas se ordenan por la columna `orden` y las horas por conteo.
- **Filas inválidas** (estación o ruta inexistente, orden u hora mal escritos, estación repetida en una ruta): se ignoran y se cuentan.
- **Horas ≥ 24** (el GTFS trae cosas como `25:10`): se toman módulo 24 h, así `25:10` es `01:10`.
- **Filas repetidas** en `horarios.csv`: se cuentan, porque cada fila es un paso de bus programado.
- **Sin coordenadas** en los CSV: el mapa se dibuja a partir del grafo.

Para convertir un GTFS a los tres CSV: `py conversion/gtfs_a_csv.py GTFS.zip datos`.

## Otras funciones de la app

- **Rayos X de R5**: anima la búsqueda real del motor (los dos frentes, los encuentros y el mejor viaje).
- **Vista 3D**: recorre el viaje desde una cámara detrás del articulado.
- **Impacto de un cierre**: al cerrar una estación se recalcula R5 para todos los pares y se muestra cuántos viajes se pierden.
- **Plano de metro**: dibuja la red con conexiones de 0°, 45° y 90°.
- **Modo sustentación** (botón ▶ Sustentar): recorrido guiado por R1–R11 con demostraciones en vivo.

Los datos en pantalla se marcan como **Programado** (sale de `horarios.csv`), **Estimado** (horas de llegada) o **Simulado** (posición de los buses y llegadas de ejemplo de Hora pico).

## Equipo

Ver [integrantes.md](integrantes.md).
