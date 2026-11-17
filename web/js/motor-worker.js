/* Web Worker: carga Python (Pyodide), copia el motor y los datos a su disco
 * virtual y atiende las llamadas de la interfaz. Corre en un hilo aparte para
 * que las animaciones no se congelen mientras Python carga o calcula.
 * Dueño: Daniel. */

const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';
importScripts(PYODIDE + 'pyodide.js');

const BASE = new URL('../../', self.location.href);

// Archivos que se copian al disco virtual (la vista 3D no necesita nada extra del motor). tests/test_web.py verifica que la
// lista de motor/ esté completa.
const ARCHIVOS = [
  'motor/__init__.py', 'motor/red.py', 'motor/carga.py', 'motor/modelo.py',
  'motor/consultas.py', 'motor/cierres.py', 'motor/horarios.py', 'motor/ranking.py',
  'motor/viaje.py', 'motor/edicion.py', 'motor/comandos.py', 'motor/fila.py',
  'motor/estructuras/__init__.py', 'motor/estructuras/tabla_hash.py', 'motor/estructuras/avl.py',
  'motor/estructuras/lista_doble.py', 'motor/estructuras/pila.py',
  'motor/estructuras/cola_circular.py', 'motor/estructuras/ordenamiento.py',
  'api/__init__.py', 'api/puente.py',
  'benchmarks/__init__.py', 'benchmarks/generar_red.py', 'benchmarks/medir.py',
  'datos/estaciones.csv', 'datos/rutas.csv', 'datos/horarios.csv',
];

// Las pruebas solo se descargan si alguien pide correrlas (no retrasan el arranque).
// tests/test_web.py verifica que esta lista esté completa.
const ARCHIVOS_PRUEBAS = [
  'tests/__init__.py', 'tests/apoyo.py', 'web/js/motor-worker.js',
  'tests/fixtures/mini/estaciones.csv', 'tests/fixtures/mini/rutas.csv', 'tests/fixtures/mini/horarios.csv',
  'tests/test_avl.py', 'tests/test_carga.py', 'tests/test_cola_circular.py', 'tests/test_contrato.py',
  'tests/test_lista_doble.py', 'tests/test_ordenamiento.py', 'tests/test_pila.py',
  'tests/test_r1_r2_r3_consultas.py', 'tests/test_r4_proximo_bus.py', 'tests/test_r5_viaje.py',
  'tests/test_r6_ranking.py', 'tests/test_r7_edicion.py', 'tests/test_r8_cierres.py',
  'tests/test_r9_deshacer.py', 'tests/test_r10_fila.py', 'tests/test_reglas_motor.py',
  'tests/test_tabla_hash.py', 'tests/test_web.py',
  'tests/test_conversion.py', 'conversion/__init__.py', 'conversion/gtfs_a_csv.py',
  'tests/fixtures/gtfs_mini/stops.txt', 'tests/fixtures/gtfs_mini/routes.txt',
  'tests/fixtures/gtfs_mini/trips.txt', 'tests/fixtures/gtfs_mini/stop_times.txt',
];

let llamarPython = null;
let py = null;

async function copiar(rutas) {
  const contenidos = await Promise.all(rutas.map(async (ruta) => {
    const r = await fetch(new URL(ruta, BASE));
    if (!r.ok) throw new Error('No se pudo leer ' + ruta + ' (' + r.status + ')');
    return [ruta, await r.text()];
  }));
  for (const [ruta, texto] of contenidos) {
    py.FS.mkdirTree('/proyecto/' + ruta.split('/').slice(0, -1).join('/'));
    py.FS.writeFile('/proyecto/' + ruta, texto);
  }
}

async function correrPruebas(id) {
  await copiar(ARCHIVOS_PRUEBAS);
  const correr = py.runPython('from api.puente import correr_pruebas\ncorrer_pruebas');
  const avisar = (texto) => self.postMessage({ tipo: 'prueba', id, datos: JSON.parse(texto) });
  const resumen = correr(avisar).toJs({ dict_converter: Object.fromEntries });
  self.postMessage({ tipo: 'respuesta', id, ok: true, datos: resumen, ms: resumen.ms });
}

function progreso(etapa, texto, pct) {
  self.postMessage({ tipo: 'progreso', etapa, texto, pct });
}

async function iniciar() {
  const t0 = performance.now();
  progreso('python', 'Descargando Python', 0.05);
  py = await loadPyodide({ indexURL: PYODIDE });
  const tPython = performance.now() - t0;

  progreso('motor', 'Copiando el motor y los datos', 0.55);
  await copiar(ARCHIVOS);

  progreso('red', 'Construyendo las estructuras', 0.8);
  py.runPython("import sys, os\nsys.path.insert(0, '/proyecto')\nos.chdir('/proyecto')");
  llamarPython = py.runPython('from api.puente import llamar\nllamar');
  const r = JSON.parse(llamarPython('iniciar', JSON.stringify(['/proyecto/datos'])));
  if (!r.ok) throw new Error(r.error);
  progreso('listo', 'Listo', 1);
  return { ...r.datos, ms_python: Math.round(tPython), ms_total: Math.round(performance.now() - t0) };
}

const listo = iniciar();
listo.then(
  (info) => self.postMessage({ tipo: 'listo', info }),
  (err) => self.postMessage({ tipo: 'fallo', error: String(err && err.message || err) }),
);

self.onmessage = async (e) => {
  const { id, op, args } = e.data;
  try {
    await listo;
    if (op === 'correr_pruebas') { await correrPruebas(id); return; }
    const r = JSON.parse(llamarPython(op, JSON.stringify(args || [])));
    self.postMessage({ tipo: 'respuesta', id, ...r });
  } catch (err) {
    self.postMessage({ tipo: 'respuesta', id, ok: false, error: String(err && err.message || err) });
  }
};
