# Rondas de commits

El proyecto se sube a GitHub en **rondas**, una rama y un *pull request* por entrega, para que el historial muestre el trabajo de los tres a lo largo del tiempo. Los archivos de cada ronda están en la carpeta local `rondas/` (no se sube: está en `.gitignore`), organizada en una carpeta por día (`dia-1` a `dia-4`). Las rondas de Tomás y Daniel vienen en `.zip`, listas para enviárselas; las de Miguel, como carpeta.

Cada ronda se verificó con las pruebas sobre el estado acumulado del repositorio: si se respetan el orden y los archivos, `py -m unittest` pasa en todas.

Son 12 rondas en **4 días**: cada día, **cada uno hace un push**.

| Día | # | Quién | Rama | Qué entra | Revisa |
|---|---|---|---|---|---|
| — | 01 | Los tres | (ya en `main`) | E0 + E1: estructura, contrato y estructuras genéricas | — |
| 1 | 02 | Tomás | `e2-carga-r4-r6` | Carga de los CSV, R4, R6, mini red de prueba | Daniel |
| 1 | 03 | Miguel | `e2-r1-r2-r3-r8` | R1, R2, R3 y R8 | Tomás |
| 1 | 04 | Daniel | `e3-r7-r9` | R7, R9 (y cerrar/reabrir pasan a usar comandos) | Tomás |
| 2 | 05 | Tomás | `e3-r10-fila` | R10 | Daniel |
| 2 | 06 | Daniel | `e4-r5-viaje` | R5 y su traza (rayos X) | Miguel |
| 2 | 07 | Miguel | `e4-interfaz-base` | Estilos, mapa con plano de metro, intro, `app.py`, `netlify.toml` | Daniel |
| 3 | 08 | Tomás | `e5-benchmarks` | Generador de redes y medición (R11) | Daniel |
| 3 | 09 | Daniel | `e5-puente` | Puente motor–interfaz: itinerario, flota, impacto de cierres, medición en vivo | Miguel |
| 3 | 10 | Miguel | `e6-vistas` | Las cinco vistas, vista 3D y modo sustentación | Tomás |
| 4 | 11 | Daniel | `e6-worker` | Worker con Pyodide, pruebas en vivo y pruebas del puente | Miguel |
| 4 | 12 | Tomás | `e7-conversion` | Script de conversión del GTFS y su GTFS de prueba | Daniel |
| 4 | 13 | Miguel | `e8-readme` | README con R12, `integrantes.md` | Daniel y Tomás |

## Calendario: 4 días, un push por persona al día

| Día | Orden del día |
|---|---|
| 1 | 02 Tomás → 03 Miguel → 04 Daniel |
| 2 | 05 Tomás → 06 Daniel → 07 Miguel |
| 3 | 08 Tomás → 09 Daniel → 10 Miguel |
| 4 | 11 Daniel → 12 Tomás → 13 Miguel |

Las tres rondas de un día van una detrás de otra, en el orden de la tabla: cada una se sube cuando la anterior ya tiene su *pull request* aprobado y unido a `main`. Por eso conviene coordinarse por chat («ya uní la mía, sigue tú»). Si un día se pierde, simplemente se corre todo un día; nunca se salta una ronda.

## Cómo se sube una ronda

1. Actualizar `main` y crear la rama:

```bash
git switch main
```

```bash
git pull
```

```bash
git switch -c NOMBRE-DE-LA-RAMA
```

2. Si la ronda viene en `.zip`, descomprimirlo (clic derecho → *Extraer todo*). Copiar el contenido de la carpeta de la ronda **encima** del repositorio, respetando las rutas. Algunos archivos, como `motor/red.py`, reemplazan una versión anterior. El archivo `LEEME.md` de la ronda no se copia.
3. Correr las pruebas; deben terminar en `OK`:

```bash
py -m unittest
```

4. Hacer el commit, con el mensaje que indica el `LEEME.md` de la ronda, y subir la rama:

```bash
git add -A
```

```bash
git commit -m "MENSAJE DE LA RONDA"
```

```bash
git push -u origin NOMBRE-DE-LA-RAMA
```

5. Abrir el *pull request* en GitHub y asignar al revisor. El revisor lee el código y debe poder explicarlo; después aprueba y hace *merge*.
6. Recién entonces se sube la siguiente ronda.

Respetar los 4 días hace que el historial muestre un avance real y no todo en una tarde. Antes de cada ronda, su dueño debe leer los archivos y saber explicarlos: en la sustentación cada uno responde por un requisito que no hizo, y el día del cambio sorpresa hay que modificar este código en vivo.
