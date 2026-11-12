# Planeador TransMilenio — Fase 2: Diseño y arquitectura

> Estado: **propuesta para aprobación**. Todavía no hay código.
> Parte de lo aprobado en la Fase 1 ([fase-1-analisis.md](fase-1-analisis.md)): despliegue A (Pyodide), contrato de retornos (§15), reparto de requisitos (§10.2), frontend sin compilación.
> Al final (§12) están las pocas decisiones que siguen abiertas.

Índice: 1 Arquitectura · 2 Modelo de objetos · 3 Estructuras · 4 Carga · 5 Algoritmos R1–R10 · 6 Invariantes R8/R9 · 7 Puente y worker · 8 Rendimiento R11 · 9 Pruebas · 10 Experiencia de usuario · 11 Registro de decisiones · 12 Decisiones abiertas

---

## 1. Arquitectura en capas

```
 ┌──────────────── web/ (JavaScript, hilo principal) ────────────────┐
 │  Vistas ── Componentes ── Render (SVG red + Canvas flota)         │
 │                    │                                              │
 │             cliente-motor.js   ← única puerta hacia Python        │
 └────────────────────┼──────────────────────────────────────────────┘
          postMessage │ {id, op, args}        {id, ok, datos, ms}
 ┌────────────────────▼──── Web Worker ───────────────────────────────┐
 │  motor-worker.js: carga Pyodide, copia motor/ y datos/ al disco    │
 │                   virtual, ejecuta puente.py                       │
 │  api/puente.py : traduce llamadas JSON ⇄ métodos de Red            │
 │                  (sin reglas del sistema; puede usar dict)         │
 │  motor/        : Red y simular_fila (reglas estrictas)             │
 └────────────────────────────────────────────────────────────────────┘
```

Reglas de dependencia (se verifican en pruebas):

| Capa | Puede importar | No puede |
|---|---|---|
| `motor/estructuras/` | nada del proyecto | `motor/red.py`, `api/`, prohibidos |
| `motor/` (resto) | `motor/estructuras/`, `csv`, `time`, `random` | `api/`, prohibidos |
| `api/` | `motor` y la librería estándar | — |
| `web/` | solo `cliente-motor.js` habla con el worker | lógica de requisitos |

Así el **cambio sorpresa** casi siempre consiste en: una estructura genérica ya existente + un método nuevo en `Red` + una prueba.

---

## 2. Modelo de objetos (`motor/modelo.py`)

Todas las clases usan `__slots__` (menos memoria y sin `__dict__` por objeto).

```
Estacion
  id            int      índice en los arreglos internos (0..n_E-1)
  nombre        str
  abierta       bool
  buses_dia     int      Σ len(horas) de sus paradas actuales (para R6)
  membresias    ListaDoble[Membresia]   rutas que paran aquí

Ruta
  nombre        str
  paradas       ListaDoble[NodoParada]  recorrido en un solo sentido
  
NodoParada   (nodo de la lista doble de la ruta)
  estacion      Estacion
  ruta          Ruta
  ant, sig      NodoParada
  horas         list[int]   minutos 0..1439, ordenados
  membresia     Membresia   su nodo en estacion.membresias (para quitarlo en O(1))

Membresia    (nodo de la lista doble de la estación)
  parada        NodoParada
  ant, sig      Membresia
```

Diagrama de punteros de una estación de transbordo:

```
           Ruta F23-1:  … ⇄ [AV. JIMENEZ] ⇄ [RICAURTE] ⇄ [BANDERAS] ⇄ …
                                                ▲
 Estacion RICAURTE.membresias:  [m1] ⇄ [m2] ⇄ … ⇄ [m45]
                                  │
                                  └─► NodoParada (RICAURTE en F23-1)
```

La clase `Red` (`motor/red.py`) es una **fachada**: guarda las estructuras y cada método del contrato delega en una función pequeña.

```
Red
  _estaciones    TablaHash  nombre → Estacion
  _rutas         TablaHash  nombre → Ruta
  _paradas       TablaHash  "ruta\x1festacion" → NodoParada
  _por_id        list[Estacion]          id → Estacion (arreglo)
  _abiertas      AVL  clave nombre               (R2, R3)
  _ranking       AVL  clave (-buses_dia, nombre) (R6)
  _deshacer      Pila[Comando]
  _rehacer       Pila[Comando]
  _busqueda      EstadoBusqueda          arreglos reutilizables de R5
```

---

## 3. Estructuras genéricas (`motor/estructuras/`)

Cada archivo es independiente, con su propia prueba unitaria.

### 3.1 `tabla_hash.py` — `TablaHash`

| Método | Complejidad |
|---|---|
| `obtener(clave, defecto=None)` | O(1) esperado |
| `poner(clave, valor)` | O(1) amortizado |
| `quitar(clave) -> bool` | O(1) esperado |
| `contiene(clave) -> bool` | O(1) esperado |
| `__len__`, `claves()` | O(1), O(capacidad) |

Diseño interno:
- Tres arreglos paralelos `_claves`, `_valores`, `_estado` (vacío / ocupado / lápida). Tres listas planas en vez de una lista de tuplas: menos objetos, mejor caché.
- Capacidad potencia de 2 → la posición es `h & (cap - 1)` (más barato que `%`).
- Sondeo lineal; crecer ×2 cuando `(ocupados + lápidas) / cap > 0,7`; reconstruir sin lápidas.
- Función hash propia: polinomial `h = (h * 31 + ord(c)) & 0xFFFFFFFF`, seguida de una mezcla de bits para que claves parecidas ("CALLE 26", "CALLE 72") no caigan juntas.
- En la Fase 5 se mide contra la función `hash()` de Python, que **no está prohibida**. Ver §12.

### 3.2 `avl.py` — `AVL`

| Método | Complejidad |
|---|---|
| `insertar(clave, valor)` | O(log n) |
| `eliminar(clave) -> bool` | O(log n) |
| `buscar(clave)` | O(log n) |
| `desde(clave)` → iterador en orden a partir del primer elemento ≥ clave | O(log n) para empezar, O(1) amortizado por elemento |
| `construir_desde_ordenados(claves, valores)` | O(n) |
| `__len__` | O(1) |

- Nodo: `clave, valor, izq, der, altura`.
- Inserción y eliminación recursivas con las cuatro rotaciones (LL, RR, LR, RL).
- El iterador `desde` usa una **pila explícita** de ancestros. No hace falta guardar el puntero al padre y el costo total de producir k elementos es O(log n + k).
- La clave puede ser `str` (R2/R3) o una tupla `(-buses, nombre)` (R6). Python compara tuplas elemento por elemento y eso no está prohibido.

### 3.3 `lista_doble.py` — `ListaDoble`

- Con **nodo centinela** circular: nunca hay casos especiales para cabeza, cola ni lista vacía.
- `insertar_despues(nodo, nuevo)`, `insertar_al_final(nuevo)`, `quitar(nodo)`: O(1).
- `adelante()` y `atras()`: iteradores O(n).
- Los nodos los define quien usa la lista (`NodoParada`, `Membresia`). La lista solo exige atributos `ant` y `sig`.

### 3.4 `pila.py` — `Pila`

Envoltura de `list` con `apilar`, `desapilar`, `cima`, `vacia`, `vaciar`: O(1) amortizado. Se crea como clase para que R9 se lea como "dos pilas" y se pueda dibujar en la interfaz.

### 3.5 `cola_circular.py` — `ColaCircular`

- Arreglo de capacidad fija con `cabeza` y `tamano`. `encolar` crece ×2 cuando está llena, copiando en orden.
- `encolar`, `desencolar`, `frente`, `vacia`: O(1) amortizado.

### 3.6 `ordenamiento.py`

| Función | Uso | Complejidad |
|---|---|---|
| `merge_sort(lista, clave=None)` | Nombres de estaciones, filas de `rutas.csv` por `orden`, claves de ranking | O(n log n), estable |
| `limite_inferior(arreglo, x)` | Búsqueda binaria del primer elemento ≥ x (R4) | O(log n) |

El ordenamiento por conteo de horarios se hace dentro de la carga (§4), porque está acoplado a los nodos.

---

## 4. Carga: `Red(carpeta)`

```
1. estaciones.csv
   por cada nombre (saltando vacíos y repetidos):
       crear Estacion(id = len(_por_id)), poner en _estaciones, agregar a _por_id
   nombres = merge_sort(nombres)            → O(n_E log n_E)
   _abiertas.construir_desde_ordenados(…)   → O(n_E)

2. rutas.csv
   agrupar filas por ruta (TablaHash ruta → lista de (orden, estacion))
   por cada ruta: merge_sort por orden; enlazar NodoParada en la ListaDoble;
                  crear su Membresia; poner en _paradas
   (no se asume que el archivo venga agrupado ni ordenado)

3. horarios.csv — ordenamiento por conteo
   cubetas = 1440 listas vacías
   por cada fila (ruta, estacion, "HH:MM"):
       m = (HH*60 + MM) % 1440                ← soporta horas ≥ 24 (25:10 → 01:10)
       nodo = _paradas.obtener(clave)          ← si no existe, la fila se ignora
       cubetas[m].append(nodo)
       nodo.estacion.buses_dia += 1
   para m en 0..1439: para nodo en cubetas[m]: nodo.horas.append(m)
   → todas las listas de horas quedan ordenadas en O(n_H + 1440)

4. ranking: claves (-buses_dia, nombre) → merge_sort → construir AVL en O(n_E)
```

**Complejidad total:** O(n_E log n_E + n_P log L + n_H). El término dominante es n_H, que es lineal.

Optimización sin depender del formato: en los CSV actuales las filas vienen agrupadas por ruta. Guardamos la última ruta vista, pero el algoritmo sigue siendo correcto si llegan desordenadas.

**Robustez:** las filas con estación o ruta desconocida, o con hora mal formada, se ignoran. Se cuentan en `red._advertencias_carga` para mostrarlas en la interfaz.

---

## 5. Algoritmos por requisito

### R1 · `estado(nombre)`
`e = _estaciones.obtener(nombre)` → `"no existe"` / `"abierta"` / `"cerrada"`. **O(1) esperado**, n = n_E.

### R2 · `autocompletar(prefijo, k)`
```
si k <= 0: devolver []
res = []
para (nombre, _) en _abiertas.desde(prefijo):
    si no nombre.startswith(prefijo) o len(res) == k: parar
    res.append(nombre)
```
Funciona porque, en orden alfabético, todos los nombres que empiezan por el prefijo están **contiguos** y el primero es ≥ prefijo. **O(log n_E + k)**.

### R3 · `rango(desde, hasta)`
Igual, desde `desde`, mientras `nombre <= hasta`. Si `desde > hasta` → `[]`. **O(log n_E + m)**, m = tamaño de la respuesta.

### R4 · `proximo_bus(estacion, ruta, hora)`
```
e = _estaciones.obtener(estacion); si no existe o cerrada → None
nodo = _paradas.obtener(ruta + SEP + estacion); si no existe o sin horas → None
m = minutos(hora)
i = limite_inferior(nodo.horas, m)
si i == len(nodo.horas): i = 0                    ← vuelta al día siguiente
devolver formato(nodo.horas[i])
```
**O(log h)**, h = horas de ese par.

### R5 · `viaje(origen, destino)` — búsqueda bidireccional

`EstadoBusqueda` guarda tres arreglos del tamaño de n_E (`marca`, `mejor_paradas`, `mejor_parada_nodo`) y un contador `version`. Para "limpiar" los arreglos basta con `version += 1`: una casilla solo es válida si `marca[id] == version`. Así no se paga O(n_E) en cada consulta.

```
validar: ambos existen y están abiertos; si origen == destino → []
version += 1
mejor = None                                      # (paradas, tramos, desempate, resultado)

# Frente del origen
para cada membresia m de origen:
    nodo = m.parada; r = nodo.ruta; d1 = 0
    avanzar con nodo = nodo.sig hasta el final de r:
        d1 += 1; t = nodo.estacion
        si t es destino: candidato directo (r, origen, destino, d1); parar esta ruta
        si t.abierta y (marca[t.id] != version o d1 < mejor_paradas[t.id]):
            marca[t.id] = version; mejor_paradas[t.id] = d1; mejor_parada_nodo[t.id] = nodo

# Frente del destino
para cada membresia m de destino:
    nodo = m.parada; r2 = nodo.ruta; d2 = 0
    retroceder con nodo = nodo.ant hasta el inicio de r2:
        d2 += 1; t = nodo.estacion
        si marca[t.id] == version y mejor_parada_nodo[t.id].ruta no es r2:
            candidato con transbordo:
              [(ruta1, origen, t), (r2, t, destino)], paradas = mejor_paradas[t.id] + d2

devolver el mejor candidato según: menos paradas → directo antes que transbordo
         → nombre de la primera ruta → nombre de la segunda → nombre de t
```

**¿Por qué basta con guardar la mejor ruta hacia cada t?** Si la mejor ruta para llegar a t es la misma r2 que sale de t hacia el destino, entonces r2 pasa por el origen, luego por t y luego por el destino. Ese viaje ya existe como **directo**, con menos o igual paradas que cualquier transbordo en t. No perdemos ninguna solución mejor. Este argumento va al README de R12.

**Paradas cerradas:** el bus pasa y la parada cuenta (regla aprobada en §15), pero t solo puede ser transbordo si está abierta.

**Complejidad:** O(Σ L de las rutas del origen + Σ L de las rutas del destino). R5 no se mide en rendimiento, pero lo documentamos igual.

### R6 · `ranking(k)`
Los k primeros de `_ranking` en orden. **O(log n_E + k)**.

`buses_dia` cambia en tres casos:

| Evento | Efecto en `_ranking` |
|---|---|
| `cerrar` | eliminar la clave |
| `reabrir` | insertar la clave |
| `quitar_parada` / deshacer `agregar` | si la estación está abierta: eliminar la clave vieja, `buses_dia -= len(horas)`, insertar la nueva → O(log n_E) |
| `agregar_parada` / deshacer `quitar` | lo inverso (`+= len(horas)`; una parada nueva tiene 0 horas, así que no cambia) |

### R7 · Editar rutas
```
agregar_parada(ruta, nueva, despues_de):
    validar: ruta existe; nueva existe; despues_de está en la ruta; nueva NO está en la ruta
    nodo = NodoParada(nueva, ruta, horas=[]) ; insertar_despues(nodo_de(despues_de), nodo)
    crear Membresia y agregarla a nueva.membresias ; _paradas.poner(clave, nodo)
    registrar ComandoAgregar(nodo)                          → O(1) esperado

quitar_parada(ruta, estacion):
    nodo = _paradas.obtener(clave) ; si no existe → False
    anterior = nodo.ant ; desenlazar de la ruta y de la estación ; _paradas.quitar(clave)
    actualizar ranking (§R6)
    registrar ComandoQuitar(nodo, anterior)                 → O(1) + O(log n_E)

recorrido(ruta, al_reves): recorrer la ListaDoble adelante o atrás → O(L)
```

### R8 · `cerrar(nombre)` / `reabrir(nombre)`
Cambiar la bandera y actualizar `_abiertas` y `_ranking`. **O(log n_E)**.

### R9 · `deshacer()` / `rehacer()`
Patrón **Comando**: cada cambio es un objeto con `aplicar(red)` y `revertir(red)`.

| Comando | Guarda | `revertir` |
|---|---|---|
| `ComandoCerrar(e)` | la estación | reabrir |
| `ComandoReabrir(e)` | la estación | cerrar |
| `ComandoAgregar(nodo)` | el nodo insertado | desenlazarlo |
| `ComandoQuitar(nodo, anterior)` | el nodo y su antecesor | volver a enlazarlo después de `anterior` |

```
operación pública exitosa:  aplicar; _deshacer.apilar(cmd); _rehacer.vaciar()
deshacer:  cmd = _deshacer.desapilar(); cmd.revertir(); _rehacer.apilar(cmd)
rehacer:   cmd = _rehacer.desapilar();  cmd.aplicar();  _deshacer.apilar(cmd)
```
Una operación que devuelve `False` no entra al historial. `deshacer` y `rehacer` cuestan O(1) más el costo de la operación.

### R10 · `simular_fila(llegadas, frecuencia, capacidad)`
```
si frecuencia <= 0 o capacidad <= 0 o llegadas vacía: devolver []
cola = ColaCircular(); res = [0]*P; i = 0 (siguiente llegada); t = 0
mientras queden pasajeros por abordar:
    si cola vacía y t < llegadas[i]:
        t = siguiente múltiplo de frecuencia ≥ llegadas[i]     ← salta buses vacíos
    mientras i < P y llegadas[i] <= t: cola.encolar(i); i += 1
    repetir hasta capacidad veces mientras la cola no esté vacía:
        res[cola.desencolar()] = t
    t += frecuencia
devolver res
```
Cada pasajero entra y sale de la cola una sola vez, y cada bus procesado sube al menos a uno (gracias al salto). Por eso la simulación cuesta **O(P)**, n = P.

Sin el salto, unas llegadas que empiezan en el minuto 1.000.000 con frecuencia 1 obligarían a simular un millón de buses vacíos.

---

## 6. Invariantes que conectan R8 y R9 con todo lo demás

Se verifican con una función `red._verificar()` que solo usan las pruebas:

1. `_abiertas` contiene exactamente las estaciones con `abierta == True`.
2. `_ranking` contiene exactamente las abiertas, con clave `(-buses_dia, nombre)` actualizada.
3. `buses_dia(e) == Σ len(n.horas)` para las paradas actuales de e.
4. Para toda parada de toda ruta: `_paradas` la encuentra, y su membresía está en la estación.
5. `ant`/`sig` son consistentes en todas las listas.
6. Después de cualquier secuencia de operaciones y de sus `deshacer` completos, la red es idéntica a la recién cargada.

La prueba 6 es aleatoria (módulo `random` con semilla fija): 10.000 operaciones mezcladas, deshacer todo y comparar. Es la mejor protección contra errores sutiles de R9.

---

## 7. Puente y protocolo del worker

### 7.1 Métodos extra de `Red` (de solo lectura, para la interfaz)

| Método | Devuelve | Para |
|---|---|---|
| `estaciones()` | `list[str]` en orden alfabético (todas) | Dibujar nodos |
| `rutas()` | `list[str]` | Dibujar rutas |
| `info_estacion(nombre)` | `(abierta, buses_dia, [rutas])` | Panel lateral |
| `horas(ruta, estacion)` | `list[int]` | Pulso de la red y animación |

Son métodos del motor, así que también cumplen las reglas. No forman parte del contrato del profesor.

### 7.2 Mensajes

```
UI → worker   { id: 17, op: "viaje", args: ["PORTAL NORTE", "PORTAL SUR"] }
worker → UI   { id: 17, ok: true, datos: [...], ms: 0.42 }
worker → UI   { id: 17, ok: false, error: "..." }
worker → UI   { tipo: "progreso", etapa: "Cargando Python", pct: 40 }
```

- `ms` lo mide el worker con `performance.now()` alrededor de la llamada a Python. La UI lo muestra discretamente ("0,42 ms") en cada resultado. Es una forma barata de recordar en todo momento que el motor es rápido.
- `cliente-motor.js` expone promesas: `await motor.viaje(o, d)`.
- Arranque: barra de progreso real por etapas (descargar Pyodide → cargar motor → leer CSV → construir estructuras), cada una con su tiempo medido.

### 7.3 Animación de buses: honesta y fuera del motor

La posición de un bus entre dos paradas **no es un requisito**, así que no va en `motor/`. La calcula `api/flota.py`, marcada como *Simulado*:

```
para cada tramo (a → b) de cada ruta:
    duración estimada = mediana de (primera hora en b ≥ t_a) − t_a, sobre las horas t_a de a
    a la hora T, hay un bus en el tramo por cada salida t_a con t_a ≤ T < t_a + duración
    posición = (T − t_a) / duración
```

Se precalcula una vez al cargar: O(n_H log h). Luego se consulta por minuto y el Canvas interpola entre minutos con `requestAnimationFrame`.

---

## 8. Panel de rendimiento (R11)

### 8.1 Generador de redes (`benchmarks/generar_red.py`)
- Factor f ∈ {1, 2, 4, 8, 16}: copia la red f veces. Las estaciones van con sufijo de letras (`RICAURTE B`, `RICAURTE C`…), para respetar MAYÚSCULAS y sin tildes.
- Cada copia se conecta con la siguiente mediante rutas puente, para que el grafo siga conectado.
- Escribe los tres CSV con el mismo formato en `benchmarks/redes/xf/`.
- Así todo n crece ×f a la vez (n_E, n_R, n_P, n_H). En R12 decimos explícitamente qué n afecta a cada operación.

### 8.2 Medición
- `time.perf_counter_ns`; para cada operación, 200–2000 consultas aleatorias (con `random.seed` fija) y se reporta la **mediana**.
- Las operaciones que modifican la red se miden en pares (cerrar + deshacer) para no alterar el siguiente punto.
- Se calcula la razón `t(2n)/t(n)` y se compara con la esperada:

| Clase esperada | Razón esperada al duplicar | Banda aceptada |
|---|---|---|
| O(1) | 1,0 | 0,7 – 1,4 |
| O(log n) | ≈ 1,1 | 0,8 – 1,5 |
| O(n) | 2,0 | 1,6 – 2,6 |
| O(n log n) | ≈ 2,2 | 1,8 – 2,8 |
| O(n²) | 4,0 | 3,2 – 5,0 |

### 8.3 Comparaciones (evidencia de las decisiones)

| Requisito | Elegida | Contra |
|---|---|---|
| R1 | Tabla hash | Recorrido lineal de la lista |
| R2/R3 | AVL de abiertas | Arreglo ordenado saltando cerradas (con 50 % cerradas) |
| R4 | Búsqueda binaria | Recorrido lineal de las horas |
| R6 | AVL de ranking | Recalcular y ordenar en cada consulta |
| R7 | Lista doble | Inserción en arreglo (`list.insert`) |
| R10 | Cola circular | `list.pop(0)` |
| Carga | Conteo | Merge sort por par |

### 8.4 Dos fuentes de datos en el panel
1. **Resultados de referencia** medidos con CPython (`benchmarks/resultados/*.json`, versionados en Git).
2. **Medición en vivo** con el botón "Medir en este dispositivo", que corre el mismo código en Pyodide con factores 1–4. Así se ve que la forma de la curva se mantiene aunque el valor absoluto cambie.

Si una medición no coincide con lo esperado, la tarjeta muestra la explicación escrita (exigido por R11), por ejemplo: "Para n pequeño domina el costo fijo de la llamada; la pendiente se estabiliza desde ×4".

---

## 9. Estrategia de pruebas

| Tipo | Herramienta | Contenido |
|---|---|---|
| Unitarias de estructuras | `unittest` | Hash (colisiones, lápidas, crecimiento), AVL (balance tras cada operación, comparado con una lista ordenada a mano), lista doble, pila, cola |
| Por requisito | `unittest` + mini redes en `tests/fixtures/` | Casos normales y borde de §15 para R1–R10 |
| Invariantes | `red._verificar()` | Tras cada operación de las pruebas de R7–R9 |
| Aleatoria de R9 | `random` con semilla | 10.000 operaciones, deshacer todo, comparar |
| Rendimiento | `tests/test_rendimiento.py` | Razones dentro de banda (§8.2) |
| Reglas | `tests/test_reglas_motor.py` (módulo `ast`) | Ningún constructor prohibido en `motor/` |
| Contrato | `tests/test_contrato.py` | Firmas exactas con `inspect` |

Comando único: `py -m unittest` (sin instalar nada).

---

## 10. Experiencia de usuario

### 10.1 Arquitectura de la información

| Vista | Pregunta que responde | Requisitos |
|---|---|---|
| **Viaje** (inicio) | ¿Cómo voy de A a B y a qué hora pasa mi bus? | R2, R5, R4 |
| **Red** | ¿Cómo es el sistema? ¿Qué pasa en esta estación? | R1, R3, R6, R7 (`recorrido`) |
| **Operación** | Soy operador: cierro, edito, deshago | R7, R8, R9 |
| **Hora pico** | ¿Cuánto espera la gente con esta frecuencia? | R10 |
| **Rendimiento** | ¿El motor es tan eficiente como dicen? | R11 |

La red esquemática es **persistente**: vive detrás de todas las vistas y cada vista la "ilumina" de forma distinta.

### 10.2 Flujo principal: planear un viaje

```
1. Escribe "PORT" en Origen → lista R2 (≤ 8) con flechas/Enter
2. Elige destino igual → se dispara R5 automáticamente
3. La red se atenúa; el trayecto se dibuja en cian (600 ms)
   con el transbordo marcado por un anillo pulsante
4. Tarjeta de itinerario:
     ● PORTAL NORTE ── F23-1 · 12 paradas ──► ◎ RICAURTE (transbordo)
     ◎ RICAURTE ────── G43-1 ·  5 paradas ──► ● PORTAL SUR
   Total 17 paradas · Próximo F23-1 a las 07:42 (Programado)
5. Un articulado recorre el trayecto (botón ▶ repetir)
6. Arrastrar la línea de tiempo recalcula los próximos buses (R4)
```

### 10.3 Estados que se diseñan explícitamente

| Estado | Tratamiento |
|---|---|
| Cargando Pyodide (1ª visita) | Pantalla de arranque con la red dibujándose línea por línea y la barra por etapas: convierte la espera en presentación |
| Estación cerrada | Gris con trama diagonal y el aviso "Cerrada · nadie sube, baja ni transborda" |
| Sin viaje (≤ 1 transbordo) | Mensaje claro y las rutas del origen y del destino resaltadas, para que se vea por qué no se tocan |
| Origen = destino | "Ya estás ahí" |
| Error del motor | Mensaje humano + detalle técnico plegable |
| Sin conexión tras la 1ª visita | Pyodide y los datos quedan en caché del navegador |

### 10.4 Disposición responsive

| Ancho | Disposición |
|---|---|
| ≥ 1200 px | Panel izquierdo (360 px) + red + panel derecho contextual (320 px) + línea de tiempo abajo |
| 768–1199 px | Panel izquierdo plegable; panel derecho como cajón |
| < 768 px | Red a pantalla completa; **hoja inferior** con tres alturas (resumen / media / completa); navegación inferior con 5 iconos |

### 10.5 Diseño de la red sin coordenadas

Los CSV no traen posiciones, así que la disposición se **calcula del grafo**. Esto además garantiza que la interfaz represente la estructura real del motor.

1. **Disposición por fuerzas** (atracción en aristas, repulsión entre nodos) calculada **una vez** y guardada en `localStorage` con una huella de la red. Si la red cambia, se recalcula.
2. **Esquematización:** las aristas se acercan a ángulos de 0°/45°/90°, como en un plano de metro, y se separan los nodos que se solapan.
3. **Haces de rutas:** varias rutas en el mismo tramo se dibujan como líneas paralelas desplazadas, coloreadas por letra de prefijo.
4. **Nivel de detalle con el zoom:** lejos, solo estaciones de transbordo y troncales; cerca, todos los nombres.

Opción de calidad: para la red real se puede guardar una disposición **ajustada a mano** en `web/datos/disposicion.json`, que tiene prioridad sobre la calculada. Es presentación, no regla, así que está permitido.

### 10.6 Inventario de componentes

`BarraSuperior`, `Autocompletar` (R2), `TarjetaItinerario`, `PanelEstacion`, `Reloj` y `LineaTiempo`, `ListaRanking`, `EditorRuta` (lista arrastrable de paradas), `HistorialPilas` (R9), `SimuladorAnden` (R10), `GraficaRendimiento`, `Toast`, `HojaInferior`, `PaletaComandos` (Ctrl+K).

Cada componente es un módulo ES con `crear(raiz, props)` y `actualizar(props)`. No hace falta framework.

### 10.7 Accesibilidad (desde el diseño, no al final)
- Toda la funcionalidad se puede usar sin la red gráfica: la red es una mejora visual y existe una vista en lista equivalente.
- `Autocompletar` sigue el patrón ARIA *combobox*.
- Contraste AA en texto, foco visible en cian, y las rutas se distinguen por patrón y no solo por color.
- `prefers-reduced-motion` detiene la flota y sustituye animaciones por fundidos.

---

## 11. Registro de decisiones (ADR)

Cada fila tendrá su ficha en `docs/decisiones/` con problema, alternativas, decisión, justificación, ventajas/desventajas y complejidad.

| # | Decisión | Estado |
|---|---|---|
| 001 | Despliegue con Pyodide en Web Worker (A) | Aprobada |
| 002 | Frontend HTML/CSS/JS sin compilación | Aprobada |
| 003 | Contrato de retornos §15 | Aprobada |
| 004 | Tabla hash con sondeo lineal | Propuesta |
| 005 | AVL de estaciones abiertas para R2/R3/R8 | Propuesta |
| 006 | AVL con clave (−buses, nombre) para R6 | Propuesta |
| 007 | Listas dobles con centinela para rutas y membresías | Propuesta |
| 008 | Ordenamiento por conteo de horarios + búsqueda binaria | Propuesta |
| 009 | R5 bidireccional con marcas por versión | Propuesta |
| 010 | Patrón Comando con dos pilas para R9 | Propuesta |
| 011 | Cola circular con salto de buses vacíos para R10 | Propuesta |
| 012 | Horas ≥ 24 → módulo 1440; duplicados se cuentan | Propuesta |
| 013 | Animación de flota fuera del motor, etiquetada "Simulado" | Propuesta |
| 014 | Disposición de la red por fuerzas + esquematización | Propuesta |

---

## 12. Decisiones abiertas

1. **Función hash.** ¿La implementamos nosotros (polinomial) o usamos `hash()` de Python dentro de nuestra tabla? Está permitido y probablemente es mucho más rápido, porque está escrito en C (hay que medirlo; en la Fase 1 el hash propio costó 0,17 s para las 140.492 claves). Recomendación: **empezar con la propia** (es lo defendible ante el profesor), medir ambas en la Fase 5 y decidir con datos.
2. **Disposición de la red.** ¿Escribimos nuestro propio algoritmo de fuerzas (~150 líneas de JS, cero dependencias, defendible) o usamos `d3-force` desde CDN (probado, más rápido de integrar)? Recomendación: **d3-force** para la versión inicial y la capa de esquematización propia. La esquematización es lo que da la apariencia de plano de metro.
3. **Prototipo visual.** Antes de la Fase 3 puedo hacer **una maqueta estática** (solo HTML/CSS, sin motor) de la vista Viaje con la paleta, la tipografía y un articulado animado. Sirve para aprobar la dirección visual antes de construirla. Recomendación: **sí**, es barata y evita rehacer la interfaz después.

### 12.1 Resolución (12-nov-2026)

Las tres recomendaciones fueron **aceptadas**: (1) hash propio y comparación medida contra `hash()` en la Fase 5; (2) `d3-force` + capa de esquematización propia; (3) maqueta estática de la vista Viaje antes de la Fase 3.

### 12.2 Hallazgos al preparar la maqueta (datos reales)

1. **"Menos paradas" no es "llegar antes".** Con el criterio de R5, PORTAL NORTE → PORTAL USME consultado a las 07:40 da 8-3 hasta TOBERIN y luego H72-1: 5 paradas, pero el siguiente H72-1 en TOBERIN es a las **10:11**. Las rutas con pocas paradas suelen ser expresas que no circulan a toda hora. El contrato no cambia (R5 es así). La interfaz debe **mostrar la espera** de cada tramo para que el usuario no se lleve una sorpresa. Más adelante podríamos ofrecer un método extra, fuera del contrato, de "llegar antes".
2. **No se puede estimar la llegada encadenando R4.** Preguntar "primer bus de la ruta en el destino después de abordar" a veces devuelve un bus que salió *antes* que el nuestro (no hay id de viaje). Ejemplo engañoso: PORTAL TUNAL → HEROES "en 9 minutos". Las horas de llegada deben estimarse con las **duraciones de tramo** de §7.3 y etiquetarse *Estimado*. Se corrige la idea creativa n.º 5 de la Fase 1 en ese sentido.
3. Maqueta: `prototipos/maqueta-viaje.html` (ejemplo fijo: PORTAL AMERICAS → CALLE 100, E32 hasta SIMON BOLIVAR + B44-1, 4 paradas, sale 07:45).
