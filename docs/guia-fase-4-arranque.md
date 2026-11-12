# Guía de arranque — Fase 4 (etapas E0 y E1)

> Esta guía dice **qué hace cada integrante**. Claude no ejecuta Git: cada uno corre sus comandos y hace sus commits desde su propia cuenta.
>
> **Actualización:** los archivos de E0 y E1 (pasos 2 a 5 y todas las tareas de E1) ya están creados en la carpeta. Qué sube cada uno, en qué rama y en qué orden está en [entregas-fase-4.md](entregas-fase-4.md). De esta guía siguen valiendo los pasos de Git.
> Referencias: [plan](fase-3-plan.md) · [diseño](fase-2-diseno.md) · [contrato §15](fase-1-analisis.md)

---

## Antes de empezar: dos avisos

1. **Sacar el proyecto de OneDrive.** La carpeta actual está dentro de OneDrive. OneDrive sincroniza los archivos internos de `.git` mientras Git los escribe, y eso suele corromper el repositorio o crear copias "-PREJAM-COL" en conflicto. Recomiendo mover la carpeta a algo como `C:\dev\TransmiAlgoritmo` **antes** de `git init`. Los documentos no se pierden: quedan respaldados en GitHub.
2. **Identidad de Git.** En el computador de Miguel, `user.name` es `PREJAM-COL`. El profesor revisará los nombres de los commits. Cada uno debe configurar su **nombre real** y el **correo de su cuenta de GitHub**; si no, GitHub no asocia los commits a su perfil.

```bash
git config --global user.name "Miguel Preciado"
```

```bash
git config --global user.email "el-correo-de-tu-cuenta-de-github"
```

---

## E0 · Miguel

### Paso 1. Crear el repositorio en GitHub (desde la web)
1. github.com → **New repository** → nombre `TransmiAlgoritmo` → **Private** → *sin* README, *sin* .gitignore y *sin* licencia, porque los crearemos localmente.
2. **Settings → Collaborators** → invitar a Tomás y a Daniel.
3. Invitar también al profesor. En un repositorio personal, todo colaborador puede escribir. Si se quiere que el profesor solo lea, hay que crear una **organización** gratuita y darle el rol *Read*. Para una revisión, basta con invitarlo como colaborador.

### Paso 2. Ordenar la carpeta
- Crear `datos/` y mover allí `estaciones.csv`, `rutas.csv` y `horarios.csv`.
- La presentación del profesor (`.pptx`) **no se sube**: queda ignorada por `.gitignore`.
- Crear estas carpetas y archivos vacíos (Python necesita `__init__.py` para tratar una carpeta como paquete):

```
motor/estructuras/__init__.py
api/__init__.py
tests/__init__.py
tests/fixtures/.gitkeep
benchmarks/.gitkeep
web/.gitkeep
conversion/.gitkeep
docs/decisiones/.gitkeep
```

### Paso 3. Crear `.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/

# Material del curso que no se publica
*.pptx

# Redes generadas por los benchmarks (se regeneran con un comando)
benchmarks/redes/

# Sistema operativo y editores
.DS_Store
Thumbs.db
desktop.ini
.vscode/
.idea/

# Configuración local de Claude Code
.claude/settings.local.json
```

### Paso 4. Crear `README.md` (versión mínima; R12 se completa después)

````markdown
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

## Documentación
- [Fase 1 · Análisis](docs/fase-1-analisis.md)
- [Fase 2 · Diseño](docs/fase-2-diseno.md)
- [Fase 3 · Plan](docs/fase-3-plan.md)

## Decisiones por requisito (R12)
_Se completa a medida que se implementa cada requisito._
````

### Paso 5. Crear `integrantes.md`

```markdown
# Integrantes

| Integrante | Rol transversal | Requisitos del motor |
|---|---|---|
| Miguel Preciado | Coordinación, interfaz y experiencia de usuario | R1, R2, R3, R8 |
| Tomás Gómez | Datos, validación y pruebas | R4, R6, R10 |
| Daniel Bernate | Arquitectura, algoritmos e integración | R5, R7, R9 |

Detalle de archivos por integrante: ver `docs/fase-3-plan.md` §1.
```

### Paso 6. Primer commit y subida

```bash
git init -b main
```

```bash
git add .
```

```bash
git commit -m "chore: estructura inicial, documentación de fases 1-3 y datos"
```

```bash
git remote add origin https://github.com/USUARIO/TransmiAlgoritmo.git
```

```bash
git push -u origin main
```

Antes del `git add .`, revisar con `git status` que **no** aparezca el `.pptx`.

### Paso 7. Proteger `main` (recomendado)
GitHub → **Settings → Branches → Add rule** para `main` → *Require a pull request before merging*. Así nadie, ni Miguel, sube directo a `main`, y cada cambio deja un PR revisado en el historial.

---

## E0 · Tomás y Daniel (cada uno)

1. Aceptar la invitación al repositorio (llega al correo de GitHub).
2. Instalar Git y Python 3.12 o superior. En Windows, comprobar con `py --version`.
3. Configurar nombre y correo (ver los avisos al inicio de esta guía).
4. Clonar y crear su rama:

```bash
git clone https://github.com/USUARIO/TransmiAlgoritmo.git
```

```bash
git switch -c e0-nombre
```

5. En `integrantes.md`, agregar debajo de la tabla una línea propia, por ejemplo `- Tomás: confirmo mi rol y mis requisitos.`
6. Commit, push y abrir el *pull request* en GitHub:

```bash
git commit -am "docs: confirmo rol en integrantes.md"
```

```bash
git push -u origin e0-nombre
```

7. Miguel revisa y aprueba los dos PR. **Criterio de salida de E0:** los tres aparecen en el historial de `main`.

---

## E1 · Cimientos

Todos leen antes: [diseño §3](fase-2-diseno.md) (interfaces de cada estructura) y las **reglas del motor**.

> **Dentro de `motor/` está prohibido:** `dict`, `set`, `{}`, `sorted`, `.sort()`, `min`/`max` sobre colecciones, `x in lista`, `.index()`, `.count()`, `bisect`, `heapq`, `collections`, `functools` y cualquier librería externa.
> **Permitido:** `list` como arreglo, `str` y sus métodos, `for x in lista`, tuplas, clases, y los módulos `csv`, `time` y `random`.
> Las pruebas (`tests/`) **sí** pueden usar todo eso para verificar.

Cada tarea va en su propia rama (`e1-tabla-hash`, `e1-avl`…), con sus pruebas en `tests/`, y entra por PR revisado por quien indica la tabla.

### Tareas de Daniel (primero el esqueleto, porque desbloquea a todos)

| Rama | Entregable | Revisa |
|---|---|---|
| `e1-contrato` | `motor/__init__.py` exporta `Red` y `simular_fila`. `motor/red.py` con la clase `Red` y los **14 métodos con la firma exacta** de la diapositiva 11, devolviendo por ahora un valor neutro (`[]`, `None`, `False`, `"no existe"`). `motor/fila.py` con `simular_fila` que devuelve `[]` | Miguel |
| `e1-lista-doble` | `motor/estructuras/lista_doble.py` con centinela circular: `insertar_despues`, `insertar_al_final`, `quitar`, `adelante`, `atras`, `__len__` + `tests/test_lista_doble.py` | Miguel |
| `e1-pila` | `motor/estructuras/pila.py`: `apilar`, `desapilar`, `cima`, `vacia`, `vaciar`, `__len__` + prueba | Tomás |

**Criterio de salida:** `from motor import Red, simular_fila` funciona y `Red("datos")` se puede crear sin error.

### Tareas de Tomás

| Rama | Entregable | Revisa |
|---|---|---|
| `e1-validador` | `tests/test_reglas_motor.py`: recorre con `ast` cada `.py` de `motor/` y falla si encuentra nombres o imports prohibidos, literales `{}` o comprensiones de diccionario/conjunto. Los `in` fuera de un `for` se reportan como advertencia para revisión manual | Daniel |
| `e1-contrato-pruebas` | `tests/test_contrato.py`: con `inspect.signature`, verifica que existan los 14 métodos con sus parámetros exactos | Daniel |
| `e1-cola` | `motor/estructuras/cola_circular.py`: `encolar`, `desencolar`, `frente`, `vacia`, `__len__`, con crecimiento ×2 + prueba con 1.000.000 de elementos | Daniel |
| `e1-ordenamiento` | `motor/estructuras/ordenamiento.py`: `merge_sort(lista, clave=None)` estable y `limite_inferior(arreglo, x)` + pruebas comparando contra `sorted` y `bisect` **dentro de la prueba** | Miguel |

**Criterio de salida:** `py -m unittest` en verde y el validador sin hallazgos.

### Tareas de Miguel

| Rama | Entregable | Revisa |
|---|---|---|
| `e1-tabla-hash` | `motor/estructuras/tabla_hash.py`: sondeo lineal, capacidad potencia de 2, lápidas, crecimiento con carga > 0,7, hash polinomial propio. Métodos `obtener`, `poner`, `quitar`, `contiene`, `__len__`, `claves` + `tests/test_tabla_hash.py` (colisiones forzadas, borrar y volver a insertar, crecer, 100.000 claves comparadas contra un `dict` en la prueba) | Daniel |
| `e1-avl` | `motor/estructuras/avl.py`: `insertar`, `eliminar`, `buscar`, `desde(clave)` (iterador con pila explícita), `construir_desde_ordenados`, `__len__` + `tests/test_avl.py` (verificar altura y balance después de **cada** operación; 10.000 operaciones aleatorias contra una lista ordenada) | Tomás |

### Cómo usar Claude Code cada uno en su máquina

Abrir Claude Code dentro de la carpeta del repositorio y empezar con un mensaje como:

> Lee `docs/fase-2-diseno.md` §3 y `docs/guia-fase-4-arranque.md`. Voy a implementar `<archivo>` (mi tarea de E1). Respeta las reglas del motor. Explícame cada decisión para poder defenderla. No hagas commits; los hago yo.

Lo que Claude genere en la máquina de cada uno lo sube **esa persona**, después de entenderlo. En la sustentación cada uno responde por un requisito ajeno, así que el revisor de cada PR debe poder explicarlo también.

---

## Orden recomendado

```
Miguel E0 ─► Tomás E0, Daniel E0 ─► Daniel e1-contrato ─┬─► Tomás e1-contrato-pruebas
                                                        ├─► (en paralelo) todas las demás de E1
                                                        └─► E2 empieza cuando E1 cumple su criterio
```
