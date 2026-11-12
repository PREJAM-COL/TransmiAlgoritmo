# Planeador TransMilenio — Fase 1: Análisis y propuesta

> Estado: **propuesta para aprobación**. Nada de lo que aquí se recomienda está implementado.
> Fuentes: `Proyecto final · Planeador TransMilenio.pptx` (17 diapositivas + notas del orador) y los tres CSV de la carpeta.
> Todas las cifras de datos de este documento se midieron con scripts sobre los CSV reales (12-nov-2026).

---

## 0. Resumen ejecutivo: lo que cambia todo

Antes de los detalles, siete hallazgos que redefinen el proyecto respecto a la visión inicial:

1. **Dentro de `motor/` están prohibidos `dict`, `set`, `sorted`, `.sort()`, `min`/`max` sobre colecciones, `x in lista`, `.index()`, `.count()`, `bisect`, `heapq`, `collections`, `functools` y toda librería externa.** Solo se permiten `list` como arreglo, `str`, recorridos `for`, y los módulos `csv`, `time` y `random`. Consecuencia: **tenemos que implementar nosotros mismos** la tabla hash, el árbol balanceado, el ordenamiento, la búsqueda binaria, las listas enlazadas, la pila y la cola. Un requisito que use algo prohibido **pierde los puntos de resultados y de rendimiento aunque funcione**.
2. **El contrato es fijo**: `from motor import Red, simular_fila` y 14 llamadas con nombre y firma exactos. Lo que devuelve cada una "está en el enunciado", **un documento que no está en la carpeta**. Es el bloqueo principal (ver §13).
3. **El profesor califica con un script y con otra red, "mucho más grande"**. Nada puede depender de nuestros datos (nombres, tamaños, horas). Además duplica la red y mide: cada operación (menos R5) debe crecer como "la mejor opción vista en el curso".
4. **La rúbrica oficial no asigna puntos al diseño visual.** 75 puntos grupales van a motor, rendimiento, decisiones (R11/R12), cambio sorpresa, app/datos y Git; 25 a la sustentación individual. El bono de diseño es una oferta verbal aparte. Por eso propongo que la ambición visual se concentre donde **también** suma nota: el **panel de rendimiento (R11)** y visualizaciones que muestren las estructuras reales del motor.
5. **La sustentación es sobre un requisito que *no* hiciste según `integrantes.md`, con un cambio en vivo.** Cada integrante debe entender todo el motor. La distribución "Miguel = UI, Tomás = datos, Daniel = algoritmos" deja a dos personas sin requisitos R1–R10 propios; propongo repartirlos (§10).
6. **Los CSV no traen coordenadas, ni identificadores de viaje, ni día de la semana.** Un mapa geográfico, la reconstrucción exacta de buses y un selector de fecha **no se pueden justificar solo con estos archivos**. Las coordenadas sí existen en el GTFS original (que tenemos que convertir nosotros, es entregable).
7. **Entorno local**: Python 3.14 está instalado pero solo responde como `py` (no `python`); **Node/npm no están instalados**; Git sí. Esto favorece un frontend **sin paso de compilación**.

---

## 1. Análisis de requisitos

### 1.1 Resumen de la presentación

| Diap. | Contenido |
|---|---|
| 1 | Proyecto de último corte, grupos de 3 o 4. "Con la red real. Ustedes deciden cómo." |
| 2 | Tres piezas: **la app** (web o escritorio, libre, *solo llama al motor*), **el motor** (Python, "aquí vive toda la lógica y casi toda la nota"), **los datos** (red real en tres CSV). |
| 3 | Regla central: el profesor dice *qué*, nunca *cómo*. La elección de estructura y algoritmo "es lo que más pesa en la nota". |
| 4 | R1 buscar estación · R2 autocompletar · R3 listar rango. |
| 5 | R4 próximo bus · R5 planear viaje · R6 ranking. |
| 6 | R7 editar rutas · R8 cerrar/reabrir · R9 deshacer/rehacer · R10 fila de abordaje. |
| 7 | **Vacía** (sin texto ni imagen). Conviene preguntar si falta contenido. |
| 8 | R11 panel de rendimiento · R12 README de decisiones. |
| 9 | Datos: GTFS jul-2021 (~54 MB) → script de conversión propio → tres CSV con formato fijo. |
| 10 | Reglas del motor: lo permitido y lo prohibido dentro de `motor/`. |
| 11 | Contrato exacto de llamadas. |
| 12 | Rendimiento: el script mide con red n y 2n. |
| 13 | IA permitida; se evalúa que cada decisión sea defendible. |
| 14 | Entregables: un link al repositorio. |
| 15 | Día de entrega: 45 min de cambio sorpresa + 10 min de sustentación individual. |
| 16 | Rúbrica (100 pts). |
| 17 | Fechas: **aún como `[fecha]`**. |

Notas del orador relevantes (no visibles en las diapositivas):
- R1 es la consulta más frecuente; **R2 y R3 piden orden**.
- R5 "es el más difícil: no hay un algoritmo del curso que lo resuelva tal cual, tienen que combinar lo que saben". Por eso no se mide en rendimiento.
- R8 y R9 "tocan todo lo anterior".
- R11: "Insistir en que digan qué es *n* en cada operación".
- Conversión: "pueden usar IA y pandas"; "las pruebas corren con una red distinta y más grande".
- `simular_fila` es una **función suelta, fuera de la clase `Red`**.
- Repositorio en GitLab o GitHub con acceso para el profesor; de `integrantes.md` sale sobre qué requisito sustenta cada persona.

### 1.2 Matriz de requisitos

**Obligatorios — funcionales del motor**

| ID | Llamada | Qué exige | Pista de la presentación |
|---|---|---|---|
| R1 | `red.estado(nombre)` | Nombre exacto → si existe y si está abierta | "La consulta que más se usa" |
| R2 | `red.autocompletar(prefijo, k)` | Hasta *k* estaciones **abiertas** que empiezan por el prefijo, **orden alfabético** | Pide orden |
| R3 | `red.rango(desde, hasta)` | Todas las abiertas entre dos nombres, orden alfabético | Pide orden |
| R4 | `red.proximo_bus(estacion, ruta, hora)` | Hora del siguiente bus de esa ruta en esa estación | "Las troncales pasan cientos de veces al día" |
| R5 | `red.viaje(origen, destino)` | Directo o **un solo transbordo**, el que pase por **menos paradas**: ruta, dónde bajar, dónde cambiar | No se mide rendimiento |
| R6 | `red.ranking(k)` | *k* estaciones abiertas con más buses al día | "Se consulta muy seguido y cambia poco" |
| R7 | `agregar_parada(ruta, nueva, despues_de)`, `quitar_parada(ruta, estacion)`, `recorrido(ruta, al_reves=False)` | Insertar/quitar paradas; ver recorrido en ambos sentidos | "Todo el tiempo" |
| R8 | `cerrar(nombre)`, `reabrir(nombre)` | Cerrada: fuera de búsquedas, autocompletado, rangos, ranking; nadie sube, baja ni transborda | Afecta R1–R6 |
| R9 | `deshacer()`, `rehacer()` | Deshace/rehace cierres, reaperturas y ediciones en orden; un cambio nuevo borra el "rehacer" | Afecta todo |
| R10 | `simular_fila(llegadas, frecuencia, capacidad)` | Hora pico: buses cada cierto tiempo, cupo limitado, FIFO | "Cientos de miles de pasajeros" |
| Carga | `Red(carpeta)` | Lee **solo** los tres CSV | Otra red, más grande |

**Obligatorios — técnicos (reglas del motor)**

| Regla | Detalle |
|---|---|
| T1 | Toda regla del sistema vive en el paquete `motor/`. "Una regla del sistema escrita en el front no cuenta". |
| T2 | Prohibido en `motor/`: `dict`, `set`, `sorted`, `.sort()`, `min`/`max` sobre colecciones, `x in lista`, `.index()`, `.count()`, `bisect`, `heapq`, `collections`, `functools`, librerías externas. |
| T3 | Permitido en `motor/`: `list` como arreglo, `str` y sus métodos, `for x in lista`, módulos `csv`, `time`, `random`. |
| T4 | Fuera del motor (front, conversión): cualquier librería. |
| T5 | Nombres y firmas exactos; uno distinto = requisito no hecho. |
| T6 | Rendimiento: al duplicar la red, cada operación (menos R5) crece como la mejor opción vista en el curso. |
| T7 | Formato de datos: nombres en MAYÚSCULAS, sin tildes, sin repetidos; cada ruta en un solo sentido; horas `HH:MM`; decidir qué hacer con horas tipo `25:10` y explicarlo. |

**Obligatorios — entregables y presentación**

| ID | Entregable |
|---|---|
| E1 | Paquete `motor/` con el contrato completo |
| E2 | Front (web o escritorio) que **solo llama al motor** |
| E3 | Script de conversión GTFS → CSV **y** los CSV generados |
| E4 | `README.md` con las decisiones (R12) y **el comando único para arrancar la app** |
| E5 | `integrantes.md`: nombres y qué requisitos hizo cada uno |
| E6 | Git desde la primera semana, commits de **todos** a lo largo del proyecto |
| R11 | Vista de la app que corre cada operación con redes crecientes, grafica tiempo vs complejidad esperada y explica discrepancias **ahí mismo** |
| R12 | Para R1–R10: estructura, algoritmo, alternativa descartada y por qué, O grande de cada operación **diciendo qué es n** |
| D1 | Día de entrega: cambio sorpresa (45 min, todos a la vez, IA permitida) y sustentación individual (10 min) |

**Criterios de evaluación (100 pts)**

| Criterio | Cómo se mide | Pts |
|---|---|---|
| Resultados del motor | R1–R10 correctos con red desconocida, **bordes incluidos** | 20 |
| Rendimiento | Duplicar la red: cada operación menos R5 crece como debe | 10 |
| Decisiones y panel | R11 y R12 justificados y coherentes | 20 |
| Cambio sorpresa | Verificado por script | 15 |
| App y datos | Arranca con un comando; la conversión funciona | 5 |
| Historial de Git | Commits de todos a lo largo del proyecto | 5 |
| Sustentación | Individual, sobre un requisito que no hizo | 25 |

Penalización transversal: **usar algo prohibido en `motor/` anula resultados y rendimiento de ese requisito**.

**Oportunidades de puntos adicionales**

| Oportunidad | Cómo la aprovechamos |
|---|---|
| Bono "programa más optimizado" | Estructuras propias bien elegidas + mediciones reales + comparación de implementaciones en R11 |
| Bono "mejor diseño visual" | Interfaz de centro de control, red animada, R11 cinematográfico |
| R11/R12 (20 pts) | Un panel que *demuestra* las complejidades es a la vez nota y espectáculo |
| Cambio sorpresa (15 pts) | Arquitectura modular con estructuras genéricas reutilizables: agregar un requisito nuevo es componer piezas ya probadas |
| Sustentación (25 pts) | Documentación de aprendizaje y visualizaciones "rayos X" que ayudan a explicar cada estructura |

---

## 2. Análisis de los CSV

### 2.1 `estaciones.csv` (1,8 KB)

| Columna | Tipo | Observaciones |
|---|---|---|
| `nombre` | texto | 147 filas, **todas únicas**, MAYÚSCULAS, solo `A–Z 0–9 . -` y espacio, sin espacios sobrantes, longitud 3–25 |

- Viene **ya ordenado alfabéticamente** (no podemos depender de eso: la red del profesor podría no estarlo).
- Usa fin de línea **CRLF**; los otros dos usan LF. El módulo `csv` lo maneja si abrimos con `newline=''`.
- 19 nombres contienen guion (`EL TIEMPO - MALOKA`, `CAMPIN-UAN`…): no afecta al CSV, pero **no podemos usar `-` como separador de claves compuestas**.
- No trae coordenadas, troncal, ni estado abierto/cerrado (todas empiezan abiertas, presumiblemente).

### 2.2 `rutas.csv` (38 KB)

| Columna | Tipo | Observaciones |
|---|---|---|
| `ruta` | texto | 181 rutas distintas (`1-1`, `B10-2`, `F23-1`, `A51`…) |
| `orden` | entero | 1..L consecutivo en todas las rutas, sin huecos |
| `estacion` | texto | Todas existen en `estaciones.csv` |

- 1.927 filas = 1.927 pares (ruta, estación).
- Ninguna ruta repite estación. Paradas por ruta: mín 3, media 10,6, máx 33.
- Todas las estaciones aparecen en al menos 2 rutas (RICAURTE en 45, PORTAL NORTE en 41).
- Sufijos: 74 rutas `-1`, 74 `-2`, 10 `-3`, 8 `-4`, 15 sin sufijo. **De los 74 pares `X-1`/`X-2`, solo 7 son exactamente el recorrido inverso.** Confirma la regla "cada ruta va en un solo sentido": `recorrido(ruta, al_reves=True)` debe invertir *esa* ruta, no buscar la "ruta hermana".
- Grafo inducido: 973 aristas dirigidas (paradas consecutivas), 518 pares de estaciones adyacentes, grado entre 2 y 25. Hay rutas expresas: "consecutivas" en la ruta no significa vecinas físicas.

### 2.3 `horarios.csv` (3,3 MB)

| Columna | Tipo | Observaciones |
|---|---|---|
| `ruta` | texto | Coincide con `rutas.csv` |
| `estacion` | texto | Coincide con `rutas.csv` |
| `hora` | `HH:MM` | 100 % con formato válido, rango 00:01–23:59, **ninguna ≥ 24** |

- 140.492 filas. Cada uno de los 1.927 pares (ruta, estación) tiene horarios y viceversa: integridad referencial perfecta.
- Buses por par: mín 4, media 72,9, máx 188 (F23-1).
- Hora pico 07:00–07:59 (16.154 filas); valle nocturno 23:00 (758).
- Estaciones con más paso de buses: RICAURTE 4.446, PORTAL NORTE 3.282, BANDERAS 3.038, AV. JIMENEZ 2.684, PORTAL AMERICAS 2.500. Menos: POLICARPA 90.

**Problemas e inconsistencias detectadas**

| # | Hallazgo | Evidencia | Impacto | Propuesta |
|---|---|---|---|---|
| H1 | **Filas idénticas repetidas** | 1.529 combinaciones (ruta, estación, hora) repetidas, 1.580 filas sobrantes; concentradas en B44-1 (195), K43-1 (135), B28-1 (117) | Infla el conteo de R6; R4 no se afecta | Hipótesis (no verificable sin GTFS): se mezclaron calendarios (hábil/sábado/domingo) o viajes solapados. Decidir en la conversión y documentar |
| H2 | **Horas que cruzaron medianoche ya vienen "envueltas"** | 71 filas `00:xx`, todas continuaciones de viajes iniciados antes de medianoche (p. ej. 3-1: SANTA LUCIA 23:59 → MOLINOS 00:04) | R4 a las 23:58 debe "dar la vuelta" | Si generamos los CSV nosotros: `hora mod 24` y documentarlo; R4 con búsqueda circular |
| H3 | **Horarios desordenados** | En 447 de 1.927 pares las horas no vienen en orden ascendente | R4 necesita orden; no podemos usar `sorted` | Ordenar al cargar con algoritmo propio (§4) |
| H4 | **Sin identificador de viaje** | Las filas parecen agrupadas por viaje (13.206 bloques inferidos, 12.747 completos) pero es una heurística del orden del archivo | No se puede reconstruir con certeza "qué bus" es cuál | No basar ninguna regla del motor en el orden del archivo; animaciones = interpolación declarada |
| H5 | **Viajes parciales** | 41 rutas tienen distinto número de buses en distintas paradas | R6 cuenta distinto por parada, es correcto | Ninguna, solo saberlo |
| H6 | **Sin día de la semana** | No hay columna de calendario | **Selector de fecha no justificable** | Solo selector de hora |
| H7 | **Sin coordenadas** | `estaciones.csv` solo trae `nombre` | Mapa geográfico imposible con estos datos | Extraer lat/lon del GTFS a un archivo **solo para el front** |
| H8 | **Pares no conectables** | De 21.462 pares ordenados: 7.204 directos, 13.740 con un transbordo, **518 imposibles con ≤ 1 transbordo** (90 desde POLICARPA) | R5 debe manejar "no hay viaje" | Definir retorno según el enunciado |

### 2.4 Relaciones

```
estaciones.nombre  1 ──< rutas.estacion        (una estación está en muchas rutas)
rutas.ruta         1 ──< rutas (orden)          (una ruta es una secuencia ordenada)
(rutas.ruta, rutas.estacion) 1 ──< horarios     (un par tiene muchas horas)
```

### 2.5 Pregunta abierta sobre el origen de los CSV

La diapositiva 9 dice que el script de conversión **es nuestro y es entregable**. Los CSV de la carpeta tienen exactamente el formato pedido y ya resolvieron las horas `25:10`. O los entregó el profesor como ejemplo, o alguien del grupo ya los generó. En cualquier caso **necesitamos el zip GTFS** para escribir y demostrar la conversión (y para las coordenadas).

### 2.6 Medición inicial de carga (CPython 3.14, esta máquina)

| Operación | Tiempo |
|---|---|
| Leer `horarios.csv` con `csv` + convertir horas a minutos (140.492 filas) | 0,08 s |
| Calcular un hash polinomial propio de cada clave `ruta|estacion` | 0,17 s |

El hash escrito en Python puro cuesta el doble que leer el archivo. Es la primera optimización a vigilar (en el navegador con Pyodide todo será más lento; estimación a verificar: 2–3×).

---

## 3. Comprensión del problema

### 3.1 Qué estamos resolviendo

Dos problemas distintos que comparten datos:

1. **Un índice de consultas** sobre estaciones, rutas y horarios que cambia con operaciones de los operadores (editar, cerrar, deshacer). Es un problema de **estructuras de datos dinámicas**: cada consulta y cada actualización debe tener el costo mínimo posible.
2. **Un planificador de viajes** restringido (≤ 1 transbordo, mínimo de paradas). Es un problema de **grafos**.

Más una **simulación de colas** (R10) independiente de la red.

### 3.2 Modelo matemático

- **E**: conjunto de estaciones, |E| = n_E (147 aquí).
- **R**: conjunto de rutas; cada ruta r es una **secuencia** (s₁, s₂, …, s_L) de estaciones distintas, recorrida en un solo sentido.
- **H(r, s)**: multiconjunto de horas (minutos 0–1439) en que pasa un bus de r por s.
- **abierta: E → {sí, no}**.

**R5 formalizado.** Para origen o y destino d, un viaje es:
- Directo: una ruta r con o = sᵢ y d = sⱼ, i < j. Costo = j − i paradas.
- Con un transbordo: rutas r₁ ≠ r₂ y estación t abierta, con o antes de t en r₁ y t antes de d en r₂. Costo = (pos₁(t) − pos₁(o)) + (pos₂(d) − pos₂(t)).
- Buscamos el de **menor costo**, con o y d abiertas.

Esto **no** es un camino mínimo general: es un grafo de dos niveles (estaciones y rutas) con un límite de un transbordo. Por eso la nota del profesor dice que hay que *combinar* lo que sabemos.

### 3.3 Modelo computacional

Un **grafo bipartito implícito estación ↔ ruta**: cada estación conoce las rutas que pasan por ella; cada ruta conoce su secuencia. Desde la estación origen se "sube" a cada ruta y se avanza; desde el destino se "retrocede" por cada ruta que llega. El punto donde ambos frentes se encuentran es el transbordo. Esta representación es la que debe dibujar la interfaz.

### 3.4 ¿Qué es *n*? (exigido por R12)

| Símbolo | Significado | Valor actual |
|---|---|---|
| n_E | estaciones | 147 |
| n_R | rutas | 181 |
| n_P | pares (ruta, estación) = Σ longitudes | 1.927 |
| n_H | filas de horarios | 140.492 |
| h | horas de un par (ruta, estación) | 4–188 |
| L | paradas de una ruta | 3–33 |
| k, m | tamaño pedido / tamaño de la salida | — |
| P, B | pasajeros y buses en R10 | — |

---

## 4. Propuesta de estructuras de datos

Todas implementadas por nosotros sobre `list` y objetos (con `__slots__`, que además reduce memoria y evita discusiones sobre el `__dict__` interno de los objetos).

### 4.1 Tabla hash propia (R1, R4, R7, R8 y como índice general)

| Aspecto | Detalle |
|---|---|
| Guarda | nombre → objeto `Estacion`; ruta → objeto `Ruta`; `ruta + "\x1f" + estacion` → nodo de parada (separador que no aparece en los nombres) |
| Por qué | R1 es "la consulta que más se usa": necesitamos O(1) esperado |
| Diseño | Direccionamiento abierto con sondeo lineal, capacidad potencia de 2, factor de carga ≤ 0,7, redimensionamiento ×2, hash polinomial propio (base 31), lápidas para borrados |
| Operaciones | buscar, insertar, eliminar: **O(1) esperado**, O(n) peor caso; redimensionar O(n), amortizado O(1) |
| Espacio | O(n) |
| Alternativas | Arreglo ordenado + búsqueda binaria (O(log n)); AVL (O(log n)); encadenamiento separado |
| Decisión | Sondeo lineal: mejor localidad de memoria y código más corto que encadenamiento; el AVL se reserva para lo que pide orden |

### 4.2 Árbol AVL de estaciones abiertas (R2, R3, R8)

| Aspecto | Detalle |
|---|---|
| Guarda | Solo las estaciones **abiertas**, ordenadas por nombre |
| Por qué | R2 y R3 piden orden alfabético y R8 exige que las cerradas no aparezcan. Si el árbol solo contiene abiertas, nunca recorremos cerradas |
| Operaciones | cerrar = eliminar O(log n); reabrir = insertar O(log n); `autocompletar` = descender hasta el primer nombre ≥ prefijo y avanzar en orden mientras empiece por el prefijo: **O(log n + k)**; `rango` = **O(log n + m)** |
| Espacio | O(n_E) |
| Alternativas | (a) Arreglo ordenado + búsqueda binaria: consultas O(log n + k + c) donde c = cerradas que hay que saltar → si cierran muchas, degenera a O(n). (b) Trie: excelente para prefijos (O(|p| + k)) pero incómodo para rangos y para excluir cerradas. (c) Árbol rojinegro / treap / skip list: equivalentes en O, más difíciles de defender o aleatorios |
| Decisión | AVL: garantiza O(log n) **en el peor caso**, es clásico y fácil de visualizar. *Depende de qué árboles vieron en el curso (pregunta §13)* |

### 4.3 Segundo AVL con la misma implementación (R6)

| Aspecto | Detalle |
|---|---|
| Guarda | Estaciones abiertas con clave `(−buses_al_dia, nombre)` |
| Por qué | "Se consulta muy seguido y cambia poco": la consulta debe costar casi nada y las actualizaciones pueden costar log n |
| Operaciones | `ranking(k)`: recorrido en orden de los k primeros **O(log n + k)**; cerrar/reabrir/editar ruta: eliminar + insertar **O(log n)** por estación afectada |
| Alternativas | (a) Montículo máximo propio: `ranking(k)` costaría O(k log n) cada vez y la eliminación arbitraria es incómoda. (b) Lista ordenada en caché con bandera "sucia": consulta O(k), pero cada cambio O(n log n). (c) Recalcular siempre: O(n log n) por consulta, inaceptable |
| Decisión | Reutilizar el mismo AVL con otra clave: una sola estructura probada, dos requisitos |

### 4.4 Lista doblemente enlazada por ruta (R7, R5)

| Aspecto | Detalle |
|---|---|
| Guarda | Los nodos de parada de cada ruta, en orden; cada nodo guarda su estación y su arreglo de horarios |
| Por qué | "Los operadores agregan o quitan paradas todo el tiempo". Con la tabla hash (§4.1) encontramos el nodo `despues_de` en O(1) y enlazamos en O(1) |
| Operaciones | `agregar_parada` **O(1)**; `quitar_parada` **O(1)**; `recorrido` **O(L)** en ambos sentidos (por eso doble) |
| Alternativa | Arreglo: inserción y borrado O(L) por desplazamiento; posiciones gratis |
| Decisión | Lista doble. R5 no necesita posiciones: avanza o retrocede contando paradas |

### 4.5 Índice estación → rutas que la atraviesan (R5, R6, R7)

Cada estación tiene una lista doblemente enlazada de "membresías"; el nodo de parada guarda un puntero a su membresía, así quitar una parada la desvincula de la estación en O(1). Alternativa: tabla hash de rutas por estación (más memoria por estación).

### 4.6 Arreglos ordenados de horarios + búsqueda binaria (R4)

| Aspecto | Detalle |
|---|---|
| Guarda | Por cada nodo de parada, sus horas en minutos (enteros), ordenadas |
| Carga | **Ordenamiento por conteo** global: 1.440 cubetas (una por minuto), se reparten las 140.492 filas y se vacían en orden → todos los arreglos quedan ordenados en **O(n_H + 1440)**, sin comparar. Más rápido que un merge sort O(n_H log h) y sin `sorted` |
| Consulta | Tabla hash O(1) para el nodo + búsqueda binaria propia del primer minuto ≥ hora: **O(log h)**; si no hay, vuelta al primero (servicio nocturno, H2) |
| Alternativa | Tabla de 1.440 posiciones por par con la respuesta precalculada: O(1) por consulta pero 1.440 × n_P enteros (~2,8 M aquí, mucho más en la red del profesor) |
| Decisión | Búsqueda binaria: O(log h) con memoria O(n_H). Lo comparamos en R11 contra la tabla directa |

### 4.7 Pilas de comandos (R9)

Dos pilas (`deshacer`, `rehacer`) sobre `list.append`/`list.pop()` (O(1) amortizado). Cada cambio es un **objeto comando** con `aplicar()` y `revertir()` que guarda lo necesario (p. ej. `quitar_parada` guarda el nodo anterior para reinsertarlo en el mismo sitio). Un cambio nuevo vacía la pila de rehacer. Costo: O(1) + el costo de la operación revertida.

### 4.8 Cola circular (R10)

Arreglo circular con índices de cabeza y cola, crecimiento ×2: encolar/desencolar **O(1) amortizado**. Alternativa ingenua `list.pop(0)`: O(P) por desencolar → **O(P²)** con cientos de miles de pasajeros. Ambas se compararán en R11.

### 4.9 Resumen de memoria (red actual)

| Estructura | Elementos |
|---|---|
| Tabla hash principal | ~2.300 claves (147 + 181 + 1.927), capacidad 4.096 |
| AVL abiertas / ranking | 147 nodos cada uno |
| Nodos de parada | 1.927 |
| Horarios | 140.492 enteros (≈ el costo dominante) |

Todo crece **linealmente** con el tamaño de la red: O(n_E + n_R + n_P + n_H).

---

## 5. Propuesta de algoritmos

### 5.1 R5 — Búsqueda bidireccional por rutas (recomendado)

```
1. Si origen o destino no existen o están cerrados → sin viaje.
2. FRENTE ORIGEN: para cada ruta r que pasa por el origen,
   avanzar desde el nodo del origen hacia adelante contando paradas:
     - si encuentro el destino → candidato directo (r, paradas)
     - en cada estación abierta t: mejor_ida[t] = mínimo (paradas, r)
3. FRENTE DESTINO: para cada ruta r2 que pasa por el destino,
   retroceder desde el nodo del destino contando paradas d2:
     - en cada estación abierta t con mejor_ida[t] definida y ruta ≠ r2:
       candidato = mejor_ida[t] + d2  (transbordo en t)
4. Devolver el candidato con menos paradas (desempates según el enunciado).
```

- **Tiempo**: O(Σ L de las rutas del origen + Σ L de las rutas del destino). No recorre el resto de la red.
- **Espacio**: `mejor_ida` indexado por id de estación. Para no pagar O(n_E) en limpiarlo en cada consulta usamos **marcas con versión** (un contador que invalida todo el arreglo en O(1)).
- Es, en esencia, un **BFS de dos niveles desde ambos extremos** que se encuentra en el medio.

**Alternativas comparadas**

| Algoritmo | Idea | Por qué no |
|---|---|---|
| BFS sobre estaciones | Mínimo de saltos | No controla transbordos: puede cambiar de ruta en cada estación |
| BFS/0-1 BFS sobre estados (estación, ruta) | Grafo expandido | Correcto y general, pero construye un grafo de O(n_P) estados y explora mucho más de lo necesario |
| Dijkstra con costo lexicográfico | Montículo propio | Sobredimensionado: con ≤ 1 transbordo el espacio de soluciones es pequeño y estructurado |
| A* | Heurística | No hay coordenadas para una heurística admisible |
| Fuerza bruta (todas las parejas de rutas) | O(n_R² · L) | No escala a la red del profesor |
| DFS | — | No encuentra mínimos |

### 5.2 Resumen de complejidades propuestas

| Req. | Operación | Estructura | Tiempo | n es… |
|---|---|---|---|---|
| Carga | `Red(carpeta)` | todas | O(n_E log n_E + n_P + n_H) | tamaño de los CSV |
| R1 | `estado` | tabla hash | O(1) esperado | n_E |
| R2 | `autocompletar` | AVL abiertas | O(log n_E + k) | n_E |
| R3 | `rango` | AVL abiertas | O(log n_E + m) | n_E, m = salida |
| R4 | `proximo_bus` | hash + búsqueda binaria | O(log h) | h = horas del par |
| R5 | `viaje` | bidireccional | O(Σ L rutas de o y d) | — (no medido) |
| R6 | `ranking` | AVL ranking | O(log n_E + k) | n_E |
| R7 | `agregar_parada`, `quitar_parada` | hash + lista doble | O(1) esperado (+ O(log n_E) si cambia el ranking) | — |
| R7 | `recorrido` | lista doble | O(L) | L |
| R8 | `cerrar`, `reabrir` | hash + 2 AVL | O(log n_E) | n_E |
| R9 | `deshacer`, `rehacer` | 2 pilas | O(1) + costo de la operación | — |
| R10 | `simular_fila` | cola circular | O(P + B) | P pasajeros |

> Nota: si `agregar_parada` debe actualizar el conteo de buses de R6, cambia la clave de una estación en el AVL de ranking → O(log n_E). Depende de qué diga el enunciado sobre los horarios de una parada nueva.

### 5.3 Ordenamiento (prohibido `sorted`)

- Horarios: ordenamiento por conteo (§4.6).
- Construcción de los AVL: insertar n veces O(n log n); alternativa O(n) si primero ordenamos con **merge sort propio** y construimos el árbol balanceado desde el arreglo. Se mide y se decide.

### 5.4 Cómo verificaremos el rendimiento (R11 y criterio de 10 pts)

- Un **generador de redes** que replica la red ×2, ×4, ×8 (copias con sufijo y conexiones entre copias) produciendo CSV con el mismo formato.
- Para cada operación: mediana de muchas repeticiones con `time.perf_counter`, razón t(2n)/t(n) y comparación con la razón esperada (≈1 para O(1) y O(log n), ≈2 para O(n), ≈4 para O(n²)).
- Pruebas automáticas que **fallan si la razón se sale de la banda esperada**, para detectar regresiones antes que el profesor.

---

## 6. Propuesta de arquitectura

```
┌───────────────────────── Navegador ─────────────────────────┐
│  UI (HTML/CSS/JS, sin compilación)                          │
│   ├─ Vistas: Viaje · Red · Operación · Hora pico · Rendim.  │
│   ├─ Render: SVG (red) + Canvas (flota de buses)            │
│   └─ EngineClient  ── postMessage ──┐                       │
│                                     ▼                       │
│                     Web Worker + Pyodide (Python en WASM)   │
│                       └─ import motor  (MISMO código)       │
│                       └─ api.py: traduce objetos → JSON     │
└─────────────────────────────────────────────────────────────┘
         ▲ archivos estáticos (Netlify o servidor local)
         │
  datos/*.csv   motor/*.py   web/*
```

- **`motor/`**: la única fuente de verdad, Python puro, cumple las reglas. Lo prueba el script del profesor con CPython.
- **`api.py` (fuera de `motor/`)**: adaptador delgado que llama al motor y convierte resultados a JSON para la UI. Aquí sí se puede usar `dict`, pero **no contiene reglas del sistema**, solo traducción.
- **Web Worker**: Pyodide corre en un hilo aparte, así la animación nunca se congela mientras el motor calcula o carga.
- **UI**: no calcula rutas, ni rankings, ni horarios. Solo dibuja lo que el motor devuelve. La posición en pantalla de las estaciones es un cálculo de presentación, no una regla.

---

## 7. Estrategia de despliegue

| Criterio | A. Pyodide en el navegador | B. Backend Python externo + Netlify | C. Híbrido: A en Netlify + servidor local CPython |
|---|---|---|---|
| Compatibilidad Netlify | Total (sitio estático) | Front sí; backend en Render/Railway/Fly | Total |
| Rendimiento | Carga inicial ~5–10 MB de Pyodide (en caché luego); Python 2–3× más lento (estimado) | Rápido, pero latencia de red por consulta y "arranque en frío" de los planes gratuitos (decenas de segundos) | Local: CPython nativo; web: como A |
| Facilidad de despliegue | Arrastrar carpeta a Netlify | Dos servicios, CORS, variables, cuenta adicional | Como A |
| Complejidad | Baja-media (worker + puente) | Media-alta | Media (dos adaptadores con la misma interfaz) |
| Dependencias | Pyodide (CDN) | Framework web (Flask/FastAPI), hosting | Pyodide + `http.server` de la librería estándar |
| Dispositivos | Cualquier navegador moderno; móviles de gama baja cargan más lento | Cualquiera | Cualquiera |
| Mantenimiento | Ninguno (sin servidor) | Servidor que puede dormirse o caducar | Bajo |
| Fidelidad académica | **Excelente**: corre literalmente el `motor/` evaluado | Buena | Excelente |
| Funciona sin internet | No (Pyodide desde CDN) salvo que lo descarguemos | No | **Sí** en modo local |

**Recomendación: A**, con la opción de evolucionar a **C** solo si queremos garantizar que la demo funcione sin internet en el salón. Motivos: es la única que hace que el mismo código evaluado sea el que ve el usuario, no hay servidor que se caiga ni que dependa de tu computador, y Netlify lo sirve como sitio estático.

**Comando único** (exigido): `py app.py` (Windows) / `python3 app.py`: levanta un servidor estático con la librería estándar y abre el navegador. Sin `pip install`.

Precauciones:
- Escribir el motor compatible con la versión de Python de Pyodide (3.12/3.13): evitar sintaxis exclusiva de 3.14.
- Cargar los CSV en el worker con `fetch` y escribirlos al sistema de archivos virtual de Pyodide, para que `Red(carpeta)` funcione igual que en CPython.
- `netlify.toml` con cabeceras de caché largas para Pyodide y los CSV.

---

## 8. Dirección visual

### 8.1 Concepto: "Centro de Operaciones"

Una sala de control nocturna donde **la red es el protagonista** y los paneles flotan sobre ella como instrumentos. Oscuro, preciso, con luz que solo aparece donde hay información.

### 8.2 Paleta (tokens)

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#060A13` | Fondo base (azul casi negro, no negro puro) |
| `--bg-grid` | `#0C1424` | Retícula sutil de fondo |
| `--panel` | `rgba(14, 23, 40, 0.72)` + desenfoque 16 px | Paneles de cristal |
| `--line` | `rgba(120, 170, 255, 0.12)` | Bordes y divisores |
| `--text` | `#E6EEF8` | Texto principal |
| `--text-dim` | `#8A9BB4` | Texto secundario |
| `--cyan` | `#22D3EE` | Acento principal: selección, trayecto activo |
| `--blue` | `#3B82F6` | Acento secundario: interacción |
| `--bus-red` | `#D7262E` | **Exclusivo de los buses** (rojo de articulado); nada más en la interfaz es rojo, así el bus siempre resalta |
| `--ok` / `--warn` / `--closed` | `#34D399` / `#FBBF24` / `#64748B` | Abierta / advertencia / cerrada (gris apagado, no rojo, para no competir con los buses) |

Colores de ruta: una familia por **letra de prefijo** del código de ruta (A, B, C… y numéricas), con tonos de luminancia similar para que ninguna domine. No afirmaremos que coinciden con los colores oficiales de troncales salvo que lo verifiquemos en una fuente.

Modo claro opcional (para proyectar en salón con mucha luz) con los mismos tokens invertidos.

### 8.3 Tipografía

- **Space Grotesk**: títulos y cifras grandes (técnica, geométrica).
- **Inter**: texto de interfaz (legible a tamaños pequeños).
- **JetBrains Mono** con cifras tabulares: reloj, horas, métricas de rendimiento (los números no "bailan" al cambiar).

### 8.4 Composición (escritorio)

```
┌──────────────────────────────────────────────────────────────┐
│ ◉ TransmiAlgoritmo   Viaje · Red · Operación · Hora pico · ⚡ │  ← barra superior
├────────────┬───────────────────────────────────┬─────────────┤
│ PLANEAR    │                                   │ ESTACIÓN    │
│ Origen  ▾  │        RED ESQUEMÁTICA            │ Ricaurte    │
│ Destino ▾  │   (nodos, rutas, buses en vivo)   │ ● abierta   │
│ ─────────  │                                   │ Próximos:   │
│ Itinerario │                                   │ F23 07:42   │
│ animado    │                                   │ ...         │
├────────────┴───────────────────────────────────┴─────────────┤
│ 05:00 ━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━ 23:59   ▶ ×60   07:41:12 │  ← línea de tiempo
└──────────────────────────────────────────────────────────────┘
```

Móvil: la red ocupa la pantalla; los paneles se vuelven una **hoja inferior** deslizable; la línea de tiempo se compacta.

### 8.5 Red esquemática

- Sin coordenadas en los CSV. Recomiendo: **posiciones iniciales desde lat/lon del GTFS** (si lo tenemos) y luego **esquematizar** (acercar ángulos a múltiplos de 45°, separar nodos que se solapan) estilo plano de metro. Sin GTFS: layout de fuerzas, que con 147 nodos y 518 aristas tiende a parecer una madeja; habría que trabajarlo mucho más.
- Aristas = pares consecutivos de rutas reales (las 973 del grafo); rutas paralelas en el mismo tramo se dibujan como haces desplazados.
- Estaciones de transbordo (≥ N rutas) con anillo doble; cerradas en gris con trama.
- El trayecto elegido se ilumina; el resto baja a 15 % de opacidad.

### 8.6 Tecnología de render (evaluada)

| Opción | Pros | Contras | Uso |
|---|---|---|---|
| SVG | Nítido, estilable con CSS, clic y accesibilidad nativos | Cientos de elementos animados a la vez lo ponen lento | **Red estática** y bus seleccionado |
| Canvas 2D | Miles de objetos a 60 fps | Hay que hacer el clic a mano | **Flota de buses** |
| WebGL / Three.js | 3D real | Dependencia pesada, poco valor para un plano esquemático | Descartado (salvo un detalle decorativo) |
| CSS animations | Microinteracciones baratas | No sirve para movimiento sobre trayectorias | Paneles, botones |

**Bus articulado**: vista cenital de tres secciones rojas con dos fuelles. Truco técnico: cada sección se coloca en un punto distinto de la trayectoria y se orienta según la tangente local, así **el bus se dobla de verdad en las curvas** como un articulado real.

### 8.7 Animación

- Duraciones 150–250 ms en microinteracciones; 600–900 ms en transiciones de vista; curvas `cubic-bezier(.2,.8,.2,1)`.
- Movimiento con `requestAnimationFrame`, interpolación por tiempo real (no por fotograma).
- `prefers-reduced-motion`: desactiva la flota animada y deja posiciones estáticas.

### 8.8 Honestidad de los datos (regla de diseño)

Cada dato en pantalla lleva una de tres etiquetas visuales:

| Etiqueta | Significado | Ejemplo |
|---|---|---|
| **Programado** | Sale tal cual de `horarios.csv` (GTFS jul-2021) | "Próximo F23-1: 07:42" |
| **Estimado** | Calculado a partir de datos programados | Hora de llegada tras un transbordo |
| **Simulado** | Modelo, no dato | Posición de un bus entre dos estaciones; fila de R10 |

Nunca se usará la palabra "en vivo" ni "tiempo real".

---

## 9. Ideas creativas

| # | Idea | Cómo se ve / cómo funciona | Tecnología | Dificultad | Valor |
|---|---|---|---|---|---|
| 1 | **Rayos X de R5** | Al buscar un viaje, se ve el frente del origen avanzando en cian por sus rutas y el del destino retrocediendo en azul; donde se encuentran destella el transbordo. El motor devuelve opcionalmente la traza de la búsqueda | Motor (método extra) + SVG | Media | **Muy alto**: explica el algoritmo en la sustentación y es espectacular |
| 2 | **Articulado que se dobla** | Bus de 3 secciones que se flexiona en las curvas (§8.6) | SVG/Canvas, geometría de trayectorias | Media | Alto: identidad TransMilenio inmediata |
| 3 | **Máquina del tiempo** | Arrastras la línea de tiempo y la flota se redistribuye; ×1, ×60, ×600. Posiciones interpoladas entre horas programadas, etiquetadas "Simulado" | Canvas + R4 | Media-alta | Alto, si se etiqueta con honestidad |
| 4 | **Pulso de la red** | Grosor y brillo de cada tramo según buses/hora a la hora elegida; la ciudad "respira" de madrugada a hora pico | SVG + conteos del motor | Baja-media | Alto: datos reales hechos visibles |
| 5 | **Itinerario con horas** | Resultado de R5 como tarjeta tipo boarding pass: sube 07:42 en F23-1, transbordo en Ricaurte (espera estimada 4 min), llega ~08:10 | Combina R4 + R5 en el motor | Baja | Alto: convierte un resultado técnico en utilidad real |
| 6 | **Inspector de tabla hash** | Al buscar una estación (R1) se ve el cálculo del hash, la cubeta y los sondeos | DOM/SVG + estadísticas del motor | Baja-media | Alto para la defensa de R1 |
| 7 | **Árbol AVL vivo** | Al cerrar/reabrir, el árbol de estaciones abiertas anima sus rotaciones | SVG | Media | Alto para R2/R3/R8 |
| 8 | **Historial deshacer/rehacer** | Dos pilas dibujadas lado a lado; cada cambio es una ficha que salta de una a otra | DOM + CSS | Baja | Medio-alto: R9 visible |
| 9 | **Simulador de hora pico** | Andén con pasajeros en fila, buses que llegan cada f minutos con cupo; gráfica de longitud de fila y espera; comparar dos frecuencias lado a lado | Canvas + R10 | Media | Alto: R10 deja de ser una función invisible |
| 10 | **Panel de rendimiento cinematográfico** | Por operación: curva medida vs. banda teórica en escala log-log, animación "n → 2n", veredicto ✓/⚠ con la explicación escrita | Canvas/SVG propio o uPlot | Media | **Muy alto**: R11 vale nota |
| 11 | **Paleta de comandos (Ctrl+K)** | Buscador universal con autocompletado de R2: "ir a Calle 26", "cerrar Ricaurte", "deshacer" | DOM | Baja | Medio: sensación de producto profesional |
| 12 | **Impacto de un cierre** | Al cerrar una estación: rutas afectadas, pares que pierden conexión (p. ej. "518 → 560 pares sin viaje"), cambios en el ranking | Motor + worker | Alta (cálculo masivo) | Medio-alto; candidato a fase posterior |
| 13 | **Comparador de horarios** | El mismo viaje a 06:00, 14:00 y 22:00 con esperas lado a lado | R4 | Baja | Medio |
| 14 | **Accesibilidad de primera** | Vista alternativa en lista navegable con teclado, narración del itinerario para lector de pantalla, rutas distinguibles por patrón además de color, alto contraste | ARIA, CSS | Baja-media | Alto y suele ser lo que separa un proyecto "bonito" de uno profesional |
| 15 | **Modo presentación** | Recorrido guiado para la sustentación: cada requisito con su visualización y su O grande | DOM | Baja | Medio-alto el día de la entrega |

Mi priorización: 1, 2, 4, 5, 9, 10, 14 primero; 3, 6, 7, 8, 11 después; 12, 13, 15 si sobra tiempo.

---

## 10. Organización del equipo

### 10.1 Crítica a la distribución propuesta

La presentación evalúa por **requisitos**: `integrantes.md` dice "qué requisitos hizo cada uno" y la sustentación es sobre uno que **no** hiciste. Si Miguel solo hace UI y Tomás solo datos, `integrantes.md` mostraría a Daniel como autor de los diez requisitos. Además, el historial de Git debe reflejar trabajo **real** de cada uno: que Miguel desarrolle y luego "comparta entregables" para que otros los suban sería atribuir trabajo que no hicieron, y eso es justo lo que el profesor quiere detectar. Recomiendo que cada integrante haga sus partes desde su propia cuenta (con Claude Code en su máquina si quiere) y que Miguel coordine, revise e integre.

### 10.2 Propuesta (equilibra roles preferidos y requisitos)

| Integrante | Rol transversal | Requisitos del motor | Otros entregables |
|---|---|---|---|
| **Miguel Preciado** | Coordinación, UI/UX, dirección visual | **R1** (tabla hash), **R2–R3** (AVL), **R8** (cerrar/reabrir) | Front completo, vista R11, README general, demo |
| **Tomás Gómez** | Datos, validación, pruebas | **R4** (horarios + búsqueda binaria), **R6** (ranking), **R10** (cola) | Script de conversión GTFS, generador de redes para R11, suite de pruebas, validador de reglas prohibidas |
| **Daniel Bernate** | Arquitectura, algoritmos, integración | **R5** (viaje), **R7** (lista doble), **R9** (comandos) | Esqueleto de `Red` y contrato, `api.py` y worker, benchmarks |

Reglas de equipo:
- Cada cambio entra por *pull request* revisado **por otro integrante**, que debe poder explicarlo (prepara la sustentación cruzada).
- Cada quien escribe la sección de R12 de sus requisitos.
- Commits pequeños y frecuentes desde la primera semana, cada uno desde su cuenta.

---

## 11. Estructura de carpetas recomendada

```
TransmiAlgoritmo/
├── app.py                    # Comando único: servidor estático + abre el navegador
├── README.md                 # R12 + cómo arrancar
├── integrantes.md            # Quién hizo qué requisito
├── netlify.toml              # Publicación
├── .gitignore
│
├── motor/                    # ← lo que evalúa el script. Reglas estrictas
│   ├── __init__.py           # exporta Red, simular_fila
│   ├── red.py                # Fachada: implementa el contrato llamando a los módulos
│   ├── carga.py              # Lectura de los 3 CSV (módulo csv)
│   ├── modelo.py             # Estacion, Ruta, NodoParada (__slots__)
│   ├── viaje.py              # R5
│   ├── comandos.py           # R9: comandos con aplicar/revertir
│   ├── fila.py               # R10: simular_fila
│   └── estructuras/          # Estructuras genéricas, reutilizables en el cambio sorpresa
│       ├── tabla_hash.py
│       ├── avl.py
│       ├── lista_doble.py
│       ├── pila.py
│       ├── cola_circular.py
│       └── ordenamiento.py   # conteo, merge sort, búsqueda binaria
│
├── api/                      # Adaptador motor → JSON (fuera de motor/, sin reglas)
│   └── puente.py
│
├── datos/                    # Los 3 CSV generados (+ coordenadas.csv solo para el front)
├── conversion/               # Script GTFS → CSV + su documentación
│   └── gtfs_a_csv.py
│
├── web/                      # Front estático (lo que se publica en Netlify)
│   ├── index.html
│   ├── css/                  # tokens.css, layout.css, componentes.css
│   ├── js/
│   │   ├── motor-worker.js   # Pyodide en Web Worker
│   │   ├── cliente-motor.js  # Interfaz única hacia el motor
│   │   ├── red/              # Render SVG de la red + Canvas de la flota
│   │   ├── vistas/           # viaje, red, operacion, hora-pico, rendimiento
│   │   └── ui/               # componentes: autocompletar, reloj, paneles
│   └── assets/               # Iconos, fuentes, el SVG del articulado
│
├── benchmarks/               # R11: generador de redes n, 2n, 4n… y mediciones
│   ├── generar_red.py
│   ├── medir.py
│   └── resultados/           # JSON que también lee el panel
│
├── tests/                    # unittest (librería estándar, cero dependencias)
│   ├── test_r01_estado.py … test_r10_fila.py
│   ├── test_rendimiento.py   # razones t(2n)/t(n)
│   └── test_reglas_motor.py  # analiza el código de motor/ (ast) y falla si hay algo prohibido
│
└── docs/
    ├── fase-1-analisis.md    # este documento
    └── decisiones/           # una ficha por decisión importante (problema, alternativas, decisión…)
```

El **validador de reglas** (`test_reglas_motor.py`) recorre el árbol sintáctico de cada archivo de `motor/` y detecta `dict`, `set`, `{}`, comprensiones de diccionario, `sorted`, `.sort`, `min`, `max`, `.index`, `.count`, imports prohibidos y usos de `in` que no estén en un `for` (estos últimos para revisión manual, porque `"x" in cadena` sí está permitido). Es nuestro seguro contra perder puntos por descuido.

---

## 12. Plan de desarrollo

### 12.1 Fases y prioridades

| Fase | Contenido | Prioridad | Depende de |
|---|---|---|---|
| 0 | Repositorio Git, README mínimo, `integrantes.md`, enunciado completo, decisiones de §13 | P0 | — |
| 1 | Estructuras genéricas + pruebas unitarias + validador de reglas | P0 | 0 |
| 2 | `Red(carpeta)` + R1, R2, R3, R4, R8 | P0 | 1 |
| 3 | R6, R7, R9, R10 | P0 | 2 |
| 4 | R5 | P0 | 2, 3 (R7 define los nodos) |
| 5 | Conversión GTFS + generador de redes + benchmarks (R11 datos) | P0 | 2 |
| 6 | Puente Pyodide + esqueleto de la UI + red esquemática | P1 | 2 (en paralelo con 3–5) |
| 7 | Vistas: viaje, operación, hora pico, rendimiento | P1 | 3, 4, 5, 6 |
| 8 | Ideas creativas priorizadas, accesibilidad, responsive | P2 | 7 |
| 9 | Optimización medida, README R12 final, Netlify, ensayo de sustentación y de "cambio sorpresa" simulado | P0 | todo |

El motor (fases 1–5) va primero porque concentra ~70 de los 100 puntos; la UI arranca en paralelo en cuanto el contrato existe.

### 12.2 Riesgos

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| No tener el enunciado (retornos exactos) | Alta | Muy alto | Conseguirlo antes de programar |
| Usar sin querer algo prohibido | Media | Muy alto | Validador automático + revisión cruzada |
| Que la red del profesor rompa supuestos | Media | Alto | Generador de redes grandes y casos borde en pruebas |
| Que la ambición visual consuma el tiempo del motor | Alta | Alto | Prioridades de §12.1; la UI nunca bloquea al motor |
| Pyodide lento en móviles | Media | Medio | Worker, indicador de carga elegante, medir pronto |
| Sustentación individual débil | Media | Muy alto | PR revisados por otro integrante, modo presentación, ensayos |
| Cambio sorpresa difícil de integrar | Media | Alto | Estructuras genéricas, fachada `Red` delgada, ensayo con un requisito inventado |
| Commits desbalanceados | Media | Medio | Cada uno trabaja en su cuenta desde la semana 1 |

### 12.3 Criterios de aceptación

| Área | Criterio |
|---|---|
| Contrato | `from motor import Red, simular_fila` funciona; las 14 llamadas existen con la firma exacta |
| Reglas | El validador no reporta nada en `motor/` |
| Correctitud | Pruebas de R1–R10 con casos normales y borde (estación inexistente, cerrada, prefijo vacío, k = 0, rango invertido, hora después del último bus, origen = destino, sin viaje posible, deshacer sin historial…) |
| Rendimiento | Razón t(2n)/t(n) dentro de la banda esperada en todas las operaciones menos R5, en redes de hasta 8× la actual |
| Carga | `Red("datos")` < 1 s en CPython con la red actual (medido) |
| App | `py app.py` abre la aplicación; publicada en Netlify funciona en Chrome, Firefox, Safari y móvil |
| Fluidez | ≥ 50 fps con la flota animada en un portátil promedio |
| Accesibilidad | Navegable con teclado, contraste AA, `prefers-reduced-motion` respetado |
| Documentación | README R12 completo con "qué es n" por operación; una ficha por decisión |

---

## 13. Preguntas pendientes

1. **Enunciado completo**: ¿tienen el documento que define qué devuelve cada llamada y sus reglas exactas (formato de `estado`, de `viaje`, desempates, qué pasa con `proximo_bus` después del último bus, si `agregar_parada` puede crear estaciones nuevas, si los buses cuentan paradas en estaciones cerradas, formato de `llegadas` en R10)? Sin él no se puede cerrar el diseño de retornos.
2. **Temario del curso**: ¿qué estructuras vieron? (tabla hash con direccionamiento abierto o encadenamiento, AVL, rojinegro, treap, skip list, trie, montículos, merge sort, counting sort). La regla es "crecer como la mejor opción vista en el curso".
3. **Origen de los CSV y GTFS**: ¿los CSV los entregó el profesor o alguien del grupo los generó? ¿Tienen el zip GTFS de julio de 2021? Lo necesitamos para el script de conversión (entregable) y para las coordenadas de la red.
4. **Despliegue**: ¿aprueban la alternativa A (Pyodide, sitio estático)? ¿O prefieren C para garantizar la demo sin internet?
5. **Equipo**: ¿aceptan repartir R1–R10 como en §10.2, con cada integrante haciendo commits desde su propia cuenta?
6. **Fechas**: ¿cuándo se entrega el link del repositorio y cuándo es la sustentación?
7. **Frontend sin compilación**: ¿están de acuerdo con HTML/CSS/JS sin React ni TypeScript (Node no está instalado y no lo necesitamos)?
8. **Diapositiva 7**: está vacía. ¿Falta algún requisito ahí?

---

## 14. Respuestas del equipo y decisiones (12-nov-2026)

| # | Pregunta | Respuesta | Consecuencia |
|---|---|---|---|
| 1 | Temario | Pilas, colas (FIFO/LIFO), grafos, árboles "y demás" | Se mantienen las estructuras de §4; el AVL entra como "árbol" |
| 2 | Origen de los CSV / enunciado | Los CSV son recurso del profesor; trabajamos solo con ellos y la presentación | **No hay enunciado ni GTFS**: los formatos de retorno los definimos nosotros (§15) y los documentamos en el README. Sin coordenadas: red esquemática sin geografía |
| 3 | Despliegue | **Opción A aprobada** (Pyodide en el navegador, sitio estático en Netlify) | Motor compatible con Python 3.12/3.13; Web Worker; `py app.py` = servidor estático local |
| 4 | Reparto de requisitos (§10.2) | **Aprobado** | — |
| 5 | Fechas | No aplica | — |
| 6 | Frontend sin React/TypeScript | **Aprobado** | HTML/CSS/JS sin compilación |
| 7 | Diapositiva 7 | Sin contenido faltante | — |

Riesgo que queda abierto: la rúbrica dice "la conversión del GTFS funciona" (dentro de los 5 pts de App y datos). Sin el zip GTFS no podemos escribir ni probar ese script. Conviene confirmar con el profesor si sigue siendo exigible.

## 15. Contrato (retornos) — **aprobado el 12-nov-2026**

Como no tenemos el enunciado, proponemos estos retornos. Fijarlos en pruebas y README desde el inicio.

| Llamada | Devuelve | Reglas de borde propuestas |
|---|---|---|
| `Red(carpeta)` | objeto `Red` | Horas `HH:MM` → minutos; no se eliminan duplicados (cada fila = un paso de bus) |
| `estado(nombre)` | `"abierta"`, `"cerrada"` o `"no existe"` | Coincidencia exacta, sensible a mayúsculas |
| `autocompletar(prefijo, k)` | `list[str]` (≤ k, alfabético) | k ≤ 0 → `[]`; prefijo vacío → las k primeras abiertas |
| `rango(desde, hasta)` | `list[str]` alfabético, **ambos extremos incluidos** | `desde > hasta` → `[]`; los extremos no tienen que existir |
| `proximo_bus(estacion, ruta, hora)` | `"HH:MM"` o `None` | Primer bus con hora ≥ `hora`; si no hay más ese día, el primero del día siguiente; `None` si la estación no existe, está cerrada o la ruta no para ahí |
| `viaje(origen, destino)` | lista de tramos `[(ruta, sube, baja)]` (1 o 2 tramos) o `None` | `None` si no existe/cerrada o no hay viaje con ≤ 1 transbordo; origen = destino → `[]`; empate en paradas → preferir directo, luego orden alfabético de ruta. Los buses **sí pasan** por estaciones cerradas (cuentan como parada) pero nadie sube, baja ni transborda ahí |
| `ranking(k)` | `list[str]` | Empate en buses → orden alfabético |
| `agregar_parada(ruta, nueva, despues_de)` | `True` / `False` | `nueva` debe existir en la red y no estar ya en la ruta; `despues_de` debe estar en la ruta. La parada nueva no tiene horarios (no suma al ranking) |
| `quitar_parada(ruta, estacion)` | `True` / `False` | Se conservan sus horarios para poder deshacer |
| `recorrido(ruta, al_reves=False)` | `list[str]` | Ruta inexistente → `[]` |
| `cerrar(nombre)` / `reabrir(nombre)` | `True` / `False` | `False` si no existe o ya está en ese estado (y no entra al historial) |
| `deshacer()` / `rehacer()` | `True` / `False` | `False` si no hay nada |
| `simular_fila(llegadas, frecuencia, capacidad)` | `list[int]`: minuto en que aborda cada pasajero, en el orden de `llegadas` | `llegadas` = minutos de llegada en orden no decreciente; buses en t = 0, f, 2f, …; cada uno sube hasta `capacidad` personas que hayan llegado a esa hora o antes, en orden FIFO |
