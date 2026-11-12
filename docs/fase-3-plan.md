# Planeador TransMilenio — Fase 3: Planificación

> Estado: **propuesta para aprobación**. Viene de lo aprobado en la [Fase 1](fase-1-analisis.md) y la [Fase 2](fase-2-diseno.md), y de la maqueta de la vista Viaje (`prototipos/maqueta-viaje.html`).
> El equipo pidió no usar fechas, así que las etapas se ordenan por dependencia y criterio de salida, no por calendario.

Índice: 1 Quién hace qué · 2 Árbol de carpetas · 3 Dependencias · 4 Etapas · 5 Backlog priorizado · 6 Criterios de aceptación · 7 Flujo de Git · 8 Animaciones y efectos · 9 Vista 3D "cámara de cabina" · 10 Riesgos nuevos · 11 Primer paso de la Fase 4

---

## 1. Quién hace qué

La regla que protege la nota: **cada archivo tiene un dueño que lo escribe y lo sube desde su propia cuenta.** Otro integrante lo revisa y debe poder explicarlo (la sustentación es sobre un requisito ajeno).

### 1.1 Motor

| Archivo | Dueño | Revisa | Por qué ese dueño |
|---|---|---|---|
| `motor/estructuras/tabla_hash.py` | Miguel | Daniel | Base de R1 |
| `motor/estructuras/avl.py` | Miguel | Tomás | Base de R2, R3 y R8 (y R6 la reutiliza) |
| `motor/estructuras/lista_doble.py` | Daniel | Miguel | Base de R7 y R5 |
| `motor/estructuras/pila.py` | Daniel | Tomás | Base de R9 |
| `motor/estructuras/cola_circular.py` | Tomás | Daniel | Base de R10 |
| `motor/estructuras/ordenamiento.py` | Tomás | Miguel | Merge sort y búsqueda binaria de R4 |
| `motor/modelo.py`, `motor/red.py` (esqueleto y contrato) | Daniel | Miguel | Arquitectura e integración |
| `motor/carga.py` | Tomás | Daniel | Datos (incluye el ordenamiento por conteo de horarios) |
| R1, R2, R3, R8 dentro de `red.py` | Miguel | Tomás | Reparto aprobado |
| R4, R6 dentro de `red.py` | Tomás | Miguel | Reparto aprobado |
| `motor/fila.py` (R10) | Tomás | Daniel | Reparto aprobado |
| `motor/viaje.py` (R5) | Daniel | Miguel | Reparto aprobado |
| R7 en `red.py`, `motor/comandos.py` (R9) | Daniel | Tomás | Reparto aprobado |

### 1.2 Fuera del motor

| Área | Dueño | Apoyo |
|---|---|---|
| Repositorio, README general, `integrantes.md`, coordinación | Miguel | todos |
| `api/puente.py`, `web/js/motor-worker.js`, `cliente-motor.js` | Daniel | Miguel |
| `api/flota.py` (posiciones simuladas) | Daniel | Tomás |
| Toda la interfaz `web/` (vistas, componentes, efectos, 3D) | Miguel | — |
| `benchmarks/` (generador de redes y medición) | Tomás | Daniel |
| Vista de rendimiento R11 en `web/` | Miguel | Tomás aporta los datos |
| `tests/` de reglas, contrato e invariantes | Tomás | todos escriben las pruebas de sus requisitos |
| `conversion/` | Tomás | Solo si el profesor confirma que es exigible sin GTFS |
| Secciones del README R12 | Cada dueño escribe la de sus requisitos | Miguel unifica el estilo |
| `app.py`, `netlify.toml` | Miguel | Daniel |

Claude Code puede ayudar a cada integrante en su propia máquina. Lo que se genere en la sesión de Miguel se sube como trabajo de Miguel y debe corresponder a archivos de Miguel.

---

## 2. Árbol de carpetas

Es el de la Fase 1 (§11), con lo nuevo de las fases 2 y 3:

```
TransmiAlgoritmo/
├── app.py · README.md · integrantes.md · netlify.toml · .gitignore
├── motor/            (§1.1)
├── api/              puente.py · flota.py
├── datos/            estaciones.csv · rutas.csv · horarios.csv
├── web/
│   ├── index.html
│   ├── css/          tokens.css · base.css · componentes.css · efectos.css
│   ├── js/
│   │   ├── motor-worker.js · cliente-motor.js · app.js (enrutador de vistas)
│   │   ├── red/      disposicion.js · esquematizar.js · render-red.js · flota.js · articulado.js
│   │   ├── vistas/   viaje.js · red.js · operacion.js · hora-pico.js · rendimiento.js
│   │   ├── ui/       autocompletar.js · reloj.js · linea-tiempo.js · paneles.js · toast.js
│   │   ├── efectos/  intro.js · ambiente.js · avisos.js · transiciones.js · sonido.js
│   │   └── vista3d/  escena.js · camara.js · modelo-bus.js   ← carga diferida (§9)
│   └── assets/
├── benchmarks/       generar_red.py · medir.py · resultados/
├── tests/            fixtures/ · test_*.py
├── prototipos/       maqueta-viaje.html (no se publica en la app)
└── docs/             fase-1… fase-3 · decisiones/
```

---

## 3. Dependencias entre módulos

```
estructuras ──► modelo ──► carga ──► red (contrato) ──► puente ──► worker ──► cliente ──► vistas
     │                                  ▲    ▲                                    │
     │                     viaje (R5) ──┘    └── comandos (R9)                    ├─► efectos
     └──────────────► benchmarks ──► resultados JSON ─────────────────────────────┴─► vista R11
```

| Para empezar… | …tiene que existir |
|---|---|
| `carga.py` | tabla hash, lista doble, ordenamiento, modelo |
| R2/R3/R8 | AVL + carga |
| R5 | lista doble + carga (y R8 para las cerradas) |
| R9 | R7 y R8 funcionando |
| Puente y worker | Esqueleto de `Red` con el contrato completo, aunque devuelva valores vacíos |
| Interfaz real | Puente funcionando. Mientras tanto, la UI avanza con **datos falsos marcados** que tienen el mismo formato que el contrato |
| R11 | Generador de redes + todas las operaciones medibles |

Lo que desbloquea a todos: **el esqueleto del contrato** (Daniel) y **las estructuras genéricas** (cada dueño). Por eso van primero.

---

## 4. Etapas

Cada etapa termina con un **criterio de salida** comprobable, no con una fecha.

| Etapa | Contenido | Quién | Criterio de salida |
|---|---|---|---|
| **E0 · Arranque** | Repo en GitHub con el profesor invitado; carpetas; README mínimo; `integrantes.md`; `.gitignore`; CSV en `datos/` | Miguel | Los tres integrantes clonan y hacen un commit cada uno (aunque sea su línea en `integrantes.md`) |
| **E1 · Cimientos** | Esqueleto del contrato · validador de reglas · prueba de firmas · estructuras genéricas con sus pruebas | Daniel (contrato), Tomás (validador, cola, ordenamiento), Miguel (hash, AVL), Daniel (lista, pila) | `py -m unittest` pasa; el validador no encuentra nada prohibido |
| **E2 · Carga y consultas** | `carga.py`; R1, R2, R3, R4, R6, R8 | Tomás, Miguel | Pruebas de esos requisitos con casos borde; `Red("datos")` < 1 s |
| **E3 · Operación y viaje** | R7, R9, R5, R10; invariantes; prueba aleatoria de deshacer | Daniel, Tomás | Las seis invariantes se cumplen tras 10.000 operaciones aleatorias |
| **E4 · Puente y app base** | Worker con Pyodide; cliente; vista Viaje funcional sobre el motor real; intro de carga | Daniel, Miguel | `py app.py` abre la app y planea un viaje real |
| **E5 · Rendimiento** | Generador; mediciones ×1…×16; comparaciones; vista R11 | Tomás, Miguel | Todas las operaciones (menos R5) dentro de banda; panel con explicaciones |
| **E6 · Vistas completas** | Red, Operación, Hora pico; accesibilidad; responsive | Miguel (con apoyo) | Todos los requisitos usables desde la app |
| **E7 · Efectos y 3D** | §8 y §9, según prioridad | Miguel | Dentro del presupuesto de rendimiento (§8.3) |
| **E8 · Cierre** | README R12 final; Netlify; ensayo de cambio sorpresa; ensayo de sustentación cruzada | Todos | Lista de §6 completa |

E4 puede empezar en paralelo con E3, en cuanto el esqueleto del contrato existe. E7 nunca bloquea a E5.

---

## 5. Backlog priorizado

**Imprescindible** (sin esto se pierden puntos):
1. Contrato completo R1–R10 con casos borde.
2. Cero construcciones prohibidas en `motor/`.
3. Rendimiento dentro de banda al duplicar.
4. Vista R11 con mediciones y explicaciones.
5. README R12 completo, con "qué es n" en cada operación.
6. `integrantes.md` y commits de los tres a lo largo del proyecto.
7. `py app.py` arranca la app.

**Importante** (para el bono de diseño y una buena sustentación):

8. Vista Viaje completa (maqueta aprobada + motor real + espera visible por tramo).
9. Intro de bienvenida que es también la pantalla de carga (§8, n.º 1).
10. Vistas Red, Operación (pilas visibles) y Hora pico.
11. Rayos X de R5 (idea creativa n.º 1 de la Fase 1).
12. Accesibilidad y responsive.
13. Publicación en Netlify.

**Deseable**:

14. Vista 3D "cámara de cabina" (§9).
15. Avisos con personalidad (§8, n.º 3).
16. Ambiente según la hora (§8, n.º 6).
17. Carrera de algoritmos en R11 (§8, n.º 9).
18. El resto de §8.

**Fuera de alcance**:
- Mapa geográfico.
- Selector de fecha.
- "Tiempo real".
- Conversión del GTFS, salvo que el profesor la confirme.

---

## 6. Criterios de aceptación ("terminado" significa…)

Para **cada requisito del motor**:
- [ ] Implementado por su dueño, en su cuenta, con PR revisado por otro integrante.
- [ ] Pruebas de casos normales y de todos los bordes de §15 de la Fase 1.
- [ ] Sin construcciones prohibidas (validador en verde).
- [ ] Complejidad medida dentro de banda (menos R5).
- [ ] Sección en el README: estructura, algoritmo, alternativa descartada y por qué, O grande con n definido.
- [ ] El revisor lo explicó en voz alta a quien lo escribió.

Para **cada vista**:
- [ ] Solo llama al motor; ninguna regla del sistema en JavaScript.
- [ ] Estados de carga, vacío, error y borde diseñados.
- [ ] Usable con teclado; contraste AA; `prefers-reduced-motion` respetado.
- [ ] Funciona a 375 px y a 1440 px.
- [ ] Cada dato lleva su etiqueta: Programado, Estimado o Simulado.

Para **cada efecto o animación**:
- [ ] Se puede saltar o desactivar.
- [ ] No bloquea la interacción ni oculta datos.
- [ ] Respeta el presupuesto de §8.3.

---

## 7. Flujo de Git

- **Repositorio**: GitHub, creado por Miguel. Tomás y Daniel entran como colaboradores y el profesor con acceso de lectura.
- **Ramas**: `main` siempre funciona. Cada tarea va en su propia rama (`r4-proximo-bus`, `ui-vista-viaje`) y entra por *pull request*.
- **Revisión**: un PR solo se aprueba si el revisor puede explicar el cambio. Así se prepara la sustentación cruzada.
- **Commits**: pequeños, en español, con prefijo de área: `motor(R4): búsqueda binaria de la próxima hora`, `ui: autocompletar con teclado`, `docs(R12): decisión de R6`.
- **Issues**: uno por requisito y por vista, asignado a su dueño, con la lista de §6 como casillas.
- **Historial**: commits de los tres desde E0 y a lo largo de todas las etapas, nunca un bloque al final.

---

## 8. Animaciones y efectos: propuesta

**Respuesta corta a la pregunta: sí, el pulido visual va al final (E7).** Pero algunas ideas tocan la arquitectura y hay que dejarlas previstas desde ya:
- La intro depende de los eventos de progreso del worker.
- El ambiente por hora depende de los tokens de color.
- La vista 3D depende de que el motor entregue la secuencia de paradas.

Las dejo planificadas aquí.

### 8.1 Propuestas

| # | Idea | Cómo se ve | Por qué no es solo adorno | Dificultad |
|---|---|---|---|---|
| 1 | **Bienvenida en articulado** (idea de Miguel, ampliada) | Pantalla oscura con la retícula. Un articulado rojo cruza de izquierda a derecha y, a su paso, va **dibujando la red real** detrás de él. En las ventanas pasa el texto "BIENVENIDO" como en un letrero LED. Cuando sale de la pantalla, la red ya está completa y la interfaz aparece | **Es la pantalla de carga de Pyodide**: el bus avanza según el progreso real (descargar Python → cargar motor → leer CSV). La espera se vuelve espectáculo en vez de un spinner. Solo una vez por sesión y con botón "Saltar" | Media |
| 2 | **Tablero LED de estación** | Los próximos buses (R4) se muestran como en las pantallas de las estaciones: matriz de puntos ámbar. Al cambiar la hora, los caracteres "voltean" uno por uno | Es la información de R4, presentada con el lenguaje visual de un andén | Baja-media |
| 3 | **Avisos con personalidad** (idea de Miguel, con reglas) | Notificaciones breves con voz bogotana, **disparadas por datos reales**: "¡Uy, apúrale! El E32 sale en 2 minutos" (R4 respecto al reloj); "Hora pico: 16.154 pasos de bus programados entre 7 y 8"; "Ojo: el H72-1 no vuelve a pasar hasta las 10:11" (la espera larga de R5) | Convierte los hallazgos de datos en avisos útiles. Máximo uno cada cierto tiempo, nunca tapa el itinerario, y existe un **"modo serio"** para la sustentación | Baja |
| 4 | **Puertas de vagón** | Al cambiar de vista, dos paneles se cierran y se abren desde el centro como las puertas de las estaciones, con un "ding" opcional | Da identidad a la navegación. Dura menos de 400 ms y no se repite si se cambia rápido | Baja |
| 5 | **Abordaje** | Al confirmar un viaje, el itinerario sale "impreso" como un tiquete que se desliza hacia abajo; un torniquete gira | Marca el momento en que el resultado de R5 está listo | Baja |
| 6 | **Ambiente según la hora** | Al mover la línea de tiempo cambia la atmósfera: amanecer azul-violeta a las 5:00, luz plena al mediodía, noche con los buses encendiendo los faros después de las 18:30. La flota se vuelve más densa en hora pico, según los conteos reales | El reloj deja de ser un control y se vuelve una experiencia | Media |
| 7 | **"No cabe ni un alfiler"** | En Hora pico (R10), los pasajeros son puntos que se apretujan al subir, el bus se hunde un poco al llenarse y un contador dice "cupo: 160/160" | Hace visible la simulación FIFO | Media |
| 8 | **Rebobinar** | Al deshacer (R9), la red hace un breve efecto de rebobinado (líneas de barrido, desplazamiento de color) y la ficha salta de una pila a la otra | R9 se ve, no solo se ejecuta | Baja-media |
| 9 | **Carrera de algoritmos** | En R11, dos buses compiten por el mismo carril: "tabla hash" contra "búsqueda lineal", "cola circular" contra `pop(0)`. La velocidad de cada uno es el tiempo **medido**. Al duplicar n, el lento se queda atrás | La comparación de complejidades se entiende de un vistazo: rendimiento y diseño en la misma pieza | Media |
| 10 | **Cierre con talanquera** | Al cerrar una estación, baja una barrera, el nodo se apaga y las rutas que pasaban por ella pierden brillo en ese punto | R8 visible | Baja |
| 11 | **"Próxima estación…"** | En la vista 3D (§9) una voz sintética anuncia "Próxima estación: Ricaurte", con la API de voz del navegador. Desactivada por defecto | Sorpresa y también accesibilidad | Baja |
| 12 | **Huevos de Pascua** | Escribir "HORA PICO" en la paleta de comandos llena la red de buses durante 5 segundos; hacer clic 5 veces en el logo hace pasar un desfile de articulados | Lo inesperado que la gente comenta | Baja |
| 13 | **Postal del viaje** | Botón que genera una imagen vertical del trayecto (red, ruta iluminada, paradas, horas) para compartir | Producto que se comparte | Media |

Mi orden recomendado: 1 → 3 → 6 → 9 → 2 → 8 → 10 → 4 → 7 → 11 → 5 → 12 → 13.

### 8.2 Una crítica honesta a los avisos tipo pop-up

Si aparecen sin motivo, cansan en la segunda visita y restan profesionalismo. Si **dependen de datos reales y son breves**, se convierten en una funcionalidad. Por eso propongo tres reglas:
- Cada aviso tiene un disparador con datos.
- Hay un límite de frecuencia.
- Existe un interruptor "modo serio". En la sustentación, que el profesor vea primero el modo serio y después la sorpresa.

### 8.3 Presupuesto de rendimiento para todo efecto

| Regla | Valor |
|---|---|
| Fotogramas | ≥ 50 fps en un portátil promedio con la flota activa |
| Trabajo por fotograma en JavaScript | ≤ 6 ms |
| Intro | ≤ 3 s si la carga ya terminó; nunca retrasa la app lista |
| Librerías | Ninguna nueva para §8 (CSS, SVG, Canvas y Web Audio) |
| Movimiento reducido | Todo efecto tiene una versión sin movimiento |

---

## 9. Vista 3D "cámara de cabina"

No estaba en el plan: en la Fase 1 descarté el 3D "salvo que aporte valor". La idea de Miguel sí aporta, porque muestra el viaje **en el orden en que se vive**: parada por parada, transbordo incluido.

### 9.1 Qué se vería

- El articulado está **fijo** en el centro inferior de la pantalla, visto desde atrás y un poco desde arriba, en diagonal.
- El **mundo se desplaza**: la cinta de la ruta (en el color de la ruta) corre bajo el bus y las estaciones se acercan como plataformas iluminadas con su nombre flotando.
- En las curvas de la ruta, el mundo gira y el bus se dobla en sus fuelles.
- Al llegar al transbordo, el bus se detiene y se abren las puertas. Aparece un segundo bus con el color de la nueva ruta, la cámara pasa a él y sigue.
- Arriba, una barra de progreso con las paradas restantes; opcionalmente, la voz "Próxima estación…".
- Es honesto con los datos: el suelo es la red esquemática (no Bogotá real), las distancias salen de la disposición y no de kilómetros, y el tiempo lleva la etiqueta *Simulado*.

### 9.2 Cómo hacerlo: tres alternativas

| Opción | Cómo | A favor | En contra |
|---|---|---|---|
| A. CSS 3D | Inclinar el plano 2D de la red con `perspective` + `rotateX` y moverlo bajo un bus fijo | Sin dependencias, rápido de hacer | El bus y las estaciones se ven planos, como calcomanías: no da la sensación de cámara |
| **B. Three.js** | Escena 3D real: suelo con la red, cinta de la ruta, estaciones como plataformas, articulado de 3 secciones con fuelles, cámara de persecución | Es exactamente la idea; luces, sombras suaves y niebla de distancia; 60 fps sin problema con unos cientos de objetos | Una dependencia (~600 KB). Se carga **solo cuando el usuario abre la vista 3D**, así no afecta el arranque |
| C. Canvas 2D con proyección propia | Calcular la perspectiva a mano | Sin dependencias y muy defendible | Mucho trabajo para un resultado peor que B |

**Recomendación: B (Three.js) con carga diferida**, como botón "Ver en 3D" en la tarjeta del itinerario, y prioridad *deseable* (E7). Si el tiempo se acaba, A sirve como versión reducida.

### 9.3 Qué necesita del motor

Nada nuevo. Usa la respuesta de R5 (tramos), `recorrido` (R7) para la secuencia de paradas y la misma disposición de la red que la vista 2D. **Cero reglas en el front.**

---

## 10. Riesgos nuevos de esta fase

| Riesgo | Mitigación |
|---|---|
| Los efectos se comen el tiempo del motor | Los efectos van en E7 y solo después de que E5 (rendimiento) cumpla su criterio de salida |
| Que Miguel termine haciendo el trabajo de otros por coordinar | Tabla de dueños (§1) e issues asignados; si alguien se atrasa, se redistribuye **y se refleja en `integrantes.md`** |
| La vista 3D no funciona en celulares viejos | Detectar WebGL; si no hay, mostrar la versión 2D con un mensaje |
| Avisos molestos | Reglas de §8.2 |

---

## 11. Primer paso de la Fase 4 (al aprobar este plan)

E0 lo hace Miguel:
1. Crear el repositorio en GitHub (privado) e invitar a Tomás, Daniel y al profesor.
2. Hacer `git init` en esta carpeta.
3. Primer commit con:
   - `docs/`
   - los CSV en `datos/`
   - `.gitignore`
   - README mínimo
   - `integrantes.md` con el reparto
   - la estructura de carpetas vacía con su `__init__.py`
4. Tomás y Daniel clonan y cada uno hace su primer commit.

Después, cada uno toma su parte de E1. Desde esta sesión puedo ayudar con las partes de Miguel (tabla hash y AVL) y preparar las instrucciones para que Tomás y Daniel arranquen las suyas con Claude Code en sus máquinas.
