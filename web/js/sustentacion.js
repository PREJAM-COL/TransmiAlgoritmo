/* Modo sustentación (dueño: Miguel).
 *
 * Un recorrido guiado sobre la app viva, como diapositivas que se manejan con
 * las flechas. Cada paso explica un requisito (estructura, algoritmo,
 * complejidad y quién lo hizo) y lo DEMUESTRA en vivo con el motor real.
 */

import { esc } from './ui.js';

const espera = (ms) => new Promise((r) => setTimeout(r, ms));

function pasos(ctx) {
  const { vistas, irA, seleccionar } = ctx;
  return [
    {
      titulo: 'TransmiAlgoritmo', req: 'Proyecto',
      idea: 'Un planeador sobre la red real de TransMilenio: 147 estaciones, 181 rutas y 140.492 horarios. El motor está escrito en Python, con estructuras propias, y corre aquí mismo en el navegador.',
      ficha: [['Equipo', 'Miguel Preciado · Tomás Gómez · Daniel Bernate'], ['Reglas', 'Sin dict, set, sorted, heapq ni librerías dentro de motor/'], ['Pruebas', '136 pruebas, incluido un validador que revisa el código del motor']],
      demo: async () => { irA('viaje'); ctx.mapa.limpiar(); ctx.mapa.ajustar(); await espera(500); if (!ctx.enPlano()) ctx.alternarPlano(); },
    },
    {
      titulo: '¿Existe y está abierta?', req: 'R1', dueno: 'Miguel',
      idea: 'La consulta más frecuente. Una tabla hash propia lleva cada nombre a su estación sin recorrer las demás y responde "ABIERTA", "CERRADA" o "NO EXISTE".',
      ficha: [['Estructura', 'Tabla hash: direccionamiento abierto, sondeo lineal, lápidas'], ['Complejidad', 'O(1) esperado · n = estaciones'], ['Descartado', 'Buscar en una lista: O(n)']],
      demo: async () => { irA('red'); await espera(400); vistas.red.consultarEstado('RICAURTE'); },
    },
    {
      titulo: 'Autocompletar', req: 'R2', dueno: 'Miguel',
      idea: 'En orden alfabético, los nombres con el mismo prefijo están juntos. Un AVL con solo las estaciones abiertas encuentra el primero en log n y avanza k pasos.',
      ficha: [['Estructura', 'Árbol AVL de estaciones abiertas'], ['Complejidad', 'O(log n + k)'], ['Descartado', 'Arreglo ordenado: con muchas cerradas degenera a O(n)']],
      demo: async () => { irA('viaje'); await espera(400); await vistas.viaje.escribir('CAL'); },
    },
    {
      titulo: 'Estaciones en un rango', req: 'R3', dueno: 'Miguel',
      idea: 'El mismo AVL: bajar hasta "CALLE 26" y avanzar en orden mientras el nombre sea menor o igual a "CALLE 80".',
      ficha: [['Estructura', 'El AVL de R2, reutilizado'], ['Complejidad', 'O(log n + m) · m = tamaño de la respuesta']],
      demo: async () => { irA('red'); await espera(400); vistas.red.rango('CALLE 26', 'CALLE 80'); },
    },
    {
      titulo: 'Próximo bus', req: 'R4', dueno: 'Tomás',
      idea: 'Cada parada guarda sus horas ordenadas (ordenamiento por conteo al cargar). La búsqueda binaria encuentra la siguiente; si ya pasó el último bus del día, devuelve None.',
      ficha: [['Estructura', 'Arreglo ordenado por parada + tabla hash'], ['Complejidad', 'O(log h) · h = horas de esa ruta en esa estación'], ['Carga', 'Conteo con 1.440 cubetas: O(n_H)']],
      demo: async () => { irA('viaje'); await espera(300); seleccionar('RICAURTE'); },
    },
    {
      titulo: 'Planear un viaje', req: 'R5', dueno: 'Daniel',
      idea: 'Búsqueda desde los dos extremos: el frente del origen avanza por sus rutas, el del destino retrocede, y donde se tocan con rutas distintas hay un transbordo. Gana el de menos paradas.',
      ficha: [['Algoritmo', 'Búsqueda bidireccional con marcas por versión'], ['Complejidad', 'O(suma de L de las rutas del origen y del destino)'], ['Verificado', 'Contra fuerza bruta en todos los pares']],
      demo: async () => { irA('viaje'); await espera(400); await vistas.viaje.rayos('PORTAL AMERICAS', 'CALLE 100'); },
    },
    {
      titulo: 'Ranking', req: 'R6', dueno: 'Tomás',
      idea: '"Se consulta mucho y cambia poco": un segundo AVL ordenado por (−buses, nombre). Consultar es leer los primeros k como (nombre, buses por día); un cambio reubica una estación en log n.',
      ficha: [['Estructura', 'AVL con clave (−buses_dia, nombre)'], ['Complejidad', 'Consulta O(log n + k) · cambio O(log n)'], ['Descartado', 'Ordenar en cada consulta: medido, 1.000 veces más lento']],
      demo: async () => { const r = document.querySelector('#ranking'); r && r.scrollIntoView({ behavior: 'smooth', block: 'center' }); r && r.classList.add('foco'); await espera(2400); r && r.classList.remove('foco'); },
    },
    {
      titulo: 'Editar rutas', req: 'R7', dueno: 'Daniel',
      idea: 'Cada ruta es una lista doblemente enlazada. La tabla hash encuentra la parada y se cambian 4 punteros: agregar o quitar no depende del largo de la ruta.',
      ficha: [['Estructura', 'Lista doble con centinela + tabla hash'], ['Complejidad', 'Agregar y quitar O(1) · recorrido O(L)']],
      demo: async () => { irA('operacion'); await espera(400); await vistas.operacion.abrirRuta('1-1'); await espera(900); await vistas.operacion.quitar('1-1', 'RECINTO FERIAL'); },
    },
    {
      titulo: 'Cerrar una estación', req: 'R8', dueno: 'Miguel',
      idea: 'Cerrar es sacar la estación de los dos AVL y marcarla. Para ver el impacto, el motor recalcula R5 entre todos los pares de estaciones.',
      ficha: [['Estructura', 'Bandera + salir de los AVL de abiertas y ranking'], ['Complejidad', 'O(log n)']],
      demo: async () => { irA('operacion'); await espera(400); await vistas.operacion.cerrarConImpacto('RICAURTE'); },
    },
    {
      titulo: 'Deshacer y rehacer', req: 'R9', dueno: 'Daniel',
      idea: 'Cada cambio es un comando que sabe aplicarse y revertirse. Dos pilas: deshacer saca de una y apila en la otra. Un cambio nuevo vacía la de rehacer.',
      ficha: [['Estructura', 'Dos pilas de comandos'], ['Complejidad', 'O(1) + el costo de revertir'], ['Verificado', '10.000 operaciones aleatorias, deshacer todo, red idéntica']],
      demo: async () => { irA('operacion'); await espera(500); await vistas.operacion.deshacer(); await espera(1300); await vistas.operacion.deshacer(); },
    },
    {
      titulo: 'Fila de abordaje', req: 'R10', dueno: 'Tomás',
      idea: 'Las llegadas (en segundos) pueden venir desordenadas: primero se ordenan con merge sort y luego suben en orden de llegada. Los buses salen en f, 2f, 3f… Con una cola circular, encolar y desencolar es O(1); con list.pop(0) sería O(P²).',
      ficha: [['Estructura', 'Merge sort + cola circular sobre un arreglo'], ['Complejidad', 'O(P log P) · O(P) si ya vienen ordenadas · P = pasajeros'], ['Ejemplo del profesor', '[30, 5, 5, 70], 60, 2 → [120, 60, 60, 120]']],
      demo: async () => { irA('horapico'); await espera(400); vistas.horapico.simular(); },
    },
    {
      titulo: 'Panel de rendimiento', req: 'R11', dueno: 'Tomás y Miguel',
      idea: 'Cada operación con redes de 10.000, 20.000, 40.000 y 80.000 estaciones, los mismos tamaños del profesor, contra la complejidad esperada. Y la carrera: la estructura elegida contra la descartada, con tiempos medidos.',
      ficha: [['Resultado', 'Las 11 operaciones evaluadas crecen como se esperaba'], ['Método', 'Duplicar n y medir la razón t(2n)/t(n)'], ['Red más grande', '80.000 estaciones · 1 millón de paradas · 1,9 millones de horarios']],
      demo: async () => { irA('rendimiento'); await espera(500); await vistas.rendimiento.carreraDe('R10', 3); },
    },
    {
      titulo: 'Las pruebas, en vivo', req: 'Calidad', dueno: 'Tomás',
      idea: 'Las mismas pruebas de py -m unittest, corriendo aquí dentro de Python. Cada cuadro es una prueba: estructuras, R1 a R10, invariantes, el contrato y el validador que revisa que el motor no use nada prohibido.',
      ficha: [['Total', '136 pruebas'], ['Las más exigentes', 'R5 contra fuerza bruta · 10.000 operaciones aleatorias de R9'], ['Validador', 'Recorre el código del motor con ast']],
      demo: async () => { irA('rendimiento'); await espera(500); await vistas.rendimiento.correrPruebas(); },
    },
    {
      titulo: 'Gracias', req: 'Preguntas',
      idea: 'Todo lo que viste lo calculó el motor en vivo. Cada decisión, con su alternativa descartada y su O grande, está en el README (R12).',
      ficha: [['En línea', 'transmialgortimomtd.netlify.app'], ['Arranque', 'py app.py'], ['Pruebas', 'py -m unittest'], ['Mediciones', 'py benchmarks/medir.py'], ['Datos', 'py conversion/gtfs_a_csv.py GTFS.zip datos']],
      demo: async () => { irA('viaje'); ctx.mapa.ajustar(); },
    },
  ];
}

export function crearSustentacion(ctx) {
  const lista = pasos(ctx);
  let i = 0, abierta = false;
  const raiz = document.createElement('div');
  raiz.className = 'sustentacion';
  raiz.setAttribute('role', 'region');
  raiz.setAttribute('aria-label', 'Modo sustentación');
  raiz.setAttribute('aria-live', 'polite');
  raiz.tabIndex = -1;
  raiz.hidden = true;
  document.body.appendChild(raiz);

  function pintar() {
    const p = lista[i];
    raiz.innerHTML = `
      <div class="sus-cab"><span class="req">${esc(p.req)}</span>${p.dueno ? `<span class="sus-dueno">Lo hizo: ${esc(p.dueno)}</span>` : ''}<span class="sus-num">${i + 1} / ${lista.length}</span></div>
      <h2>${esc(p.titulo)}</h2>
      <p class="sus-idea">${esc(p.idea)}</p>
      <dl class="sus-ficha">${p.ficha.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>
      <div class="sus-pie">
        <button class="control" data-ir="-1" aria-label="Anterior" ${i === 0 ? 'disabled' : ''}>←</button>
        <ol class="sus-puntos">${lista.map((_, k) => `<li class="${k === i ? 'actual' : k < i ? 'hecho' : ''}"></li>`).join('')}</ol>
        <button class="control" data-accion="demo" title="Repetir la demostración">↻ Demostrar</button>
        <button class="control" data-ir="1" aria-label="Siguiente" ${i === lista.length - 1 ? 'disabled' : ''}>→</button>
        <button class="control" data-accion="salir" aria-label="Salir del modo sustentación">✕</button>
      </div>`;
    raiz.classList.remove('entra');
    void raiz.offsetWidth;
    raiz.classList.add('entra');
  }

  async function ir(k) {
    i = Math.max(0, Math.min(lista.length - 1, k));
    pintar();
    try { await lista[i].demo(); } catch (e) { /* una demo que falla no detiene la presentación */ }
  }

  raiz.addEventListener('click', (e) => {
    const b = e.target.closest('[data-ir]'), a = e.target.closest('[data-accion]');
    if (b) ir(i + Number(b.dataset.ir));
    else if (a && a.dataset.accion === 'demo') lista[i].demo();
    else if (a && a.dataset.accion === 'salir') cerrar();
  });

  function teclas(e) {
    if (!abierta || (e.target.matches && e.target.matches('input, textarea'))) return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); ir(i + 1); }
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); ir(i - 1); }
    else if (e.key === 'Escape') cerrar();
  }
  document.addEventListener('keydown', teclas, true);

  function abrir() { abierta = true; raiz.hidden = false; document.body.classList.add('sustentando'); ir(0); raiz.focus(); }
  function cerrar() { abierta = false; raiz.hidden = true; document.body.classList.remove('sustentando'); document.getElementById('sustentar').focus(); }
  return { abrir, cerrar, get abierta() { return abierta; } };
}
