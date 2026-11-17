/* Vista Rendimiento (R11): cada operación con redes de 10.000 a 80.000 estaciones, la curva medida
 * contra la esperada, el veredicto y la explicación ahí mismo. Dueño: Miguel.
 * Los datos de referencia los genera benchmarks/medir.py (Tomás). */

import { esc, h, toast } from '../ui.js';

const EXPLICACION = {
  carga: 'Crece un poco más de ×2 al duplicar la red: domina leer las filas (lineal) y Python se pone más lento con más de un millón de objetos en memoria. El ordenamiento por conteo deja los horarios ordenados sin comparar (O(n_H + 1440)).',
  estado: 'La tabla hash no depende de cuántas estaciones haya. La leve subida viene de la memoria caché del procesador, no del algoritmo.',
  autocompletar: 'Bajar por el AVL cuesta log n: de 10 mil a 80 mil estaciones son solo 3 niveles más. Después se avanza k = 5 pasos.',
  rango: 'Igual que autocompletar: log n para encontrar el inicio y m ≈ 10 pasos para la respuesta.',
  proximo_bus: 'Depende de h, las horas de ese par ruta-estación, que no cambia al duplicar la red. Por eso es plano.',
  ranking: 'Los k primeros de un AVL que ya está ordenado: log n para bajar y k pasos. No se reordena nada al consultar.',
  editar: 'Enlazar el nodo en la lista doble es O(1). Lo que crece un poco es reubicar la estación en el ranking: O(log n).',
  recorrido: 'Recorre una ruta (L paradas). L no cambia al duplicar la red.',
  cerrar: 'Sacar la estación de dos AVL (abiertas y ranking) y volver a meterla al deshacer: O(log n).',
  deshacer: 'Desapilar y revertir un cierre: lo mismo que cerrar, O(log n). Las pilas son O(1).',
  fila: 'Las llegadas vienen desordenadas: ordenarlas con merge sort es P log P y domina; después cada pasajero entra y sale de la cola circular una sola vez (O(P)). P = 2 pasajeros por estación, así que se duplica con la red: un poco más de ×2.',
  viaje: 'R5 no se evalúa en rendimiento. Depende de las rutas del origen y del destino, no del tamaño de la red: casi plano.',
};
const EXPLICACION_COMP = {
  R1: 'Buscar en una lista se duplica cada vez que se duplica la red; la tabla hash no cambia. Con 80.000 estaciones la lista es unas 200 veces más lenta (con la red real de 147 estaciones la lista ganaba, porque `in` corre en C).',
  R2: 'Resultado honesto: bisect corre en C y con la mitad cerradas al azar el arreglo sigue siendo un poco más rápido. El AVL se eligió porque cerrar y reabrir en un arreglo ordenado cuesta O(n) (correr los elementos) y en el AVL O(log n), y porque el arreglo degenera si se cierran muchas estaciones con el mismo prefijo.',
  R4: 'En estas redes cada parada tiene pocas horas (se dejó 1 de cada 40 horarios), así que binaria y lineal empatan. Con la red real (h ≈ 70) la binaria tarda la mitad, y la diferencia crece con troncales más frecuentes: O(log h) contra O(h).',
  R6: 'Recalcular y ordenar en cada consulta crece con n log n (unos 660 ms con 80.000 estaciones); el AVL ya está ordenado y responde en unos 5 µs.',
  R7: 'Insertar en medio de un arreglo corre todos los elementos siguientes (crece ×2); la lista doble solo cambia 4 punteros.',
  R10: 'Con la fila llena, cada pop(0) corre toda la fila: O(P²) (crece ×4). La cola circular solo mueve un índice: con 160.000 personas, 0,17 s contra 1,2 s.',
};

const fmtMil = (n) => (n >= 1000 ? Math.round(n / 1000) + ' mil' : String(n));
const fmtT = (us) => (us >= 1e6 ? (us / 1e6).toFixed(2) + ' s' : us >= 1000 ? (us / 1000).toFixed(1) + ' ms' : us >= 10 ? us.toFixed(0) + ' µs' : us.toFixed(2) + ' µs');

export function crearVistaRendimiento(ctx) {
  const panel = h(`<div class="panel-in">
    <section class="seccion">
      <span class="eyebrow">Panel de rendimiento <span class="req">R11</span></span>
      <p>Cada operación se corre con redes de <b>10.000, 20.000, 40.000 y 80.000 estaciones</b>, los mismos tamaños con que mide el profesor (copias de la red real unidas entre sí). Si el tiempo crece como la complejidad esperada, el veredicto es ✓.</p>
      <p class="pista">Duplicar n: O(1) y O(log n) se quedan cerca de ×1; O(n) cerca de ×2; O(n²) cerca de ×4.</p>
      <div id="p-fuente" class="pista"></div>
      <button class="boton primario" id="p-vivo" type="button">Medir en este dispositivo</button>
      <p class="pista" id="p-vivo-txt">Corre el mismo código en tu navegador con redes más pequeñas (unas 600, 1.200 y 2.400 estaciones), que también se duplican. Tarda alrededor de un minuto.</p>
    </section>
    <section class="seccion">
      <span class="eyebrow">Pruebas en vivo</span>
      <p>Las mismas pruebas de <code>py -m unittest</code>, corriendo aquí dentro de Python: estructuras, R1–R10, invariantes, el validador de reglas y el contrato.</p>
      <button class="boton" id="p-pruebas" type="button">✓ Correr todas las pruebas aquí</button>
    </section>
  </div>`);
  const centro = h(`<div class="rendimiento">
    <section class="pruebas" id="p-pruebas-caja" aria-label="Pruebas en vivo" hidden>
      <div class="pruebas-cab"><h2 class="sub">Pruebas en vivo</h2><span class="pruebas-cuenta" id="pr-cuenta" aria-live="polite"></span></div>
      <div class="pruebas-grilla" id="pr-grilla"></div>
      <p class="pista" id="pr-ultima"></p>
    </section>
    <section class="carrera" aria-label="Carrera de algoritmos">
      <div class="carrera-cab"><h2 class="sub">La carrera</h2>
        <p class="pista">Las dos hacen el mismo trabajo. La velocidad de cada bus es el tiempo <b>medido</b> por operación. Duplica la red y mira quién se queda atrás.</p></div>
      <div class="carrera-ctrl">
        <div class="interruptor" id="c-req" role="group" aria-label="Comparación"></div>
        <div class="interruptor" id="c-fac" role="group" aria-label="Tamaño de la red"></div>
        <button class="boton primario" id="c-correr" type="button">▶ Correr</button>
        <button class="boton" id="c-duplicar" type="button">Duplicar la red</button>
      </div>
      <div class="carriles" id="c-carriles"></div>
      <p class="explica" id="c-texto"></p>
    </section>
    <h2 class="sub">Cada operación, de 10 mil a 80 mil estaciones</h2>
    <div class="tarjetas" id="p-tarjetas"></div>
    <h2 class="sub">La estructura elegida contra la descartada</h2><div class="tarjetas" id="p-comp"></div></div>`);
  let datos = null, vivo = null;

  async function cargar() {
    try {
      const r = await fetch(new URL('../benchmarks/resultados/cpython.json', location.href));
      datos = await r.json();
      panel.querySelector('#p-fuente').innerHTML = `Referencia: <b>${esc(datos.fuente)}</b> · ${esc(datos.fecha)} · red más grande: ${datos.tamanos.at(-1).estaciones.toLocaleString('es-CO')} estaciones, ${datos.tamanos.at(-1).paradas.toLocaleString('es-CO')} paradas y ${datos.tamanos.at(-1).horarios.toLocaleString('es-CO')} horarios.`;
      pintar();
      prepararCarrera();
      correr();
    } catch (e) {
      centro.querySelector('#p-tarjetas').innerHTML = '<p class="pista">No se encontraron resultados. Corre <code>py benchmarks/medir.py</code>.</p>';
    }
  }

  function pintar() {
    centro.querySelector('#p-tarjetas').innerHTML = datos.operaciones.map((op) => {
      const v = vivo && vivo.operaciones.find((x) => x.id === op.id);
      const clase = op.veredicto === 'ok' ? 'ok' : op.veredicto === 'revisar' ? 'mal' : 'neutro';
      return `<article class="tarjeta">
        <header><span class="req">${esc(op.requisito)}</span><span class="veredicto ${clase}">${op.veredicto === 'ok' ? '✓ crece como se esperaba' : op.veredicto === 'revisar' ? '⚠ revisar' : 'no se evalúa'}</span></header>
        <h3>${esc(op.nombre)}</h3>
        <p class="esperado">Esperado <b>${esc(op.esperado)}</b> · n = ${esc(op.n_es)}</p>
        ${grafica(datos.factores, op.tiempos_us, op.esperado, v && v.tiempos_us, etiquetas())}
        <p class="razon">Al duplicar: <b>×${op.razon_media}</b>${op.banda ? ` <span class="pista">(banda ${op.banda[0]}–${op.banda[1]})</span>` : ''}${v ? ` · este dispositivo ×${v.razon_media}` : ''}</p>
        <p class="explica">${EXPLICACION[op.id] || ''}</p>
      </article>`;
    }).join('');
    centro.querySelector('#p-comp').innerHTML = datos.comparaciones.map((c) => `
      <article class="tarjeta">
        <header><span class="req">${esc(c.requisito)}</span></header>
        <h3>${esc(c.elegida)}</h3><p class="esperado">contra ${esc(c.alternativa)}</p>
        ${graficaComp(datos.factores, c.elegida_us, c.alternativa_us, etiquetas())}
        <p class="razon">${fmtMil(datos.tamanos.at(-1).estaciones)} estaciones: <b>${fmtT(c.elegida_us.at(-1))}</b> contra <b>${fmtT(c.alternativa_us.at(-1))}</b></p>
        <p class="explica">${EXPLICACION_COMP[c.requisito] || ''}</p>
      </article>`).join('');
  }

  function etiquetas() { return datos.tamanos.map((t) => fmtMil(t.estaciones)); }

  // Gráfica log-log: x = tamaño de la red (cada punto duplica al anterior), y = tiempo.
  // La banda es la pendiente esperada.
  function grafica(fs0, ts, esperado, tsVivo, etq) {
    const fs = fs0.map((f) => f / fs0[0]);
    const W = 260, H = 120, m = { l: 8, r: 8, t: 10, b: 18 };
    const pend = /O\((n|P)( log (n|P))?\)/.test(esperado) ? 1 : /n\^2/.test(esperado) ? 2 : 0;
    const todos = [...ts, ...(tsVivo || [])];
    const ymin = Math.log2(Math.min(...todos)) - 0.5, ymax = Math.max(Math.log2(Math.max(...todos)), Math.log2(ts[0]) + pend * Math.log2(fs.at(-1))) + 0.5;
    const X = (f) => m.l + ((W - m.l - m.r) * Math.log2(f)) / Math.log2(fs.at(-1));
    const Y = (t) => H - m.b - ((H - m.t - m.b) * (Math.log2(t) - ymin)) / (ymax - ymin);
    const linea = (xs) => xs.map((t, i) => `${i ? 'L' : 'M'}${X(fs[i]).toFixed(1)},${Y(t).toFixed(1)}`).join('');
    const e0 = ts[0], e1 = ts[0] * Math.pow(fs.at(-1), pend);
    const banda = `M${X(1)},${Y(e0 / 1.4)}L${X(fs.at(-1))},${Y(e1 / 1.4)}L${X(fs.at(-1))},${Y(e1 * 1.4)}L${X(1)},${Y(e0 * 1.4)}Z`;
    return `<svg viewBox="0 0 ${W} ${H}" class="grafica" role="img" aria-label="Tiempo medido contra esperado">
      <path d="${banda}" class="banda"/>
      <path d="M${X(1)},${Y(e0)}L${X(fs.at(-1))},${Y(e1)}" class="esperada"/>
      <path d="${linea(ts)}" class="medida"/>
      ${ts.map((t, i) => `<circle cx="${X(fs[i])}" cy="${Y(t)}" r="3" class="punto-medido"><title>${etq[i]} estaciones: ${fmtT(t)}</title></circle>`).join('')}
      ${tsVivo ? `<path d="${linea(tsVivo)}" class="vivo"/>` : ''}
      ${fs.map((f, i) => `<text x="${X(f)}" y="${H - 4}" class="eje">${etq[i]}</text>`).join('')}
    </svg>`;
  }

  function graficaComp(fs0, a, b, etq) {
    const fs = fs0.map((f) => f / fs0[0]);
    const W = 260, H = 110, m = { l: 8, r: 8, t: 10, b: 18 };
    const ymin = Math.log2(Math.min(...a, ...b)) - 0.4, ymax = Math.log2(Math.max(...a, ...b)) + 0.4;
    const X = (f) => m.l + ((W - m.l - m.r) * Math.log2(f)) / Math.log2(fs.at(-1));
    const Y = (t) => H - m.b - ((H - m.t - m.b) * (Math.log2(t) - ymin)) / (ymax - ymin);
    const linea = (xs) => xs.map((t, i) => `${i ? 'L' : 'M'}${X(fs[i]).toFixed(1)},${Y(t).toFixed(1)}`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" class="grafica" role="img" aria-label="Elegida contra alternativa">
      <path d="${linea(b)}" class="alternativa"/><path d="${linea(a)}" class="medida"/>
      ${fs.map((f, i) => `<text x="${X(f)}" y="${H - 4}" class="eje">${etq[i]}</text>`).join('')}
      <text x="${W - m.r}" y="${Y(b.at(-1)) - 6}" class="rotulo alt">descartada</text>
      <text x="${W - m.r}" y="${Y(a.at(-1)) + 14}" class="rotulo">elegida</text>
    </svg>`;
  }

  /* ------------------------------------------------------------ la carrera */
  let carrera = { req: 'R10', f: 0, raf: 0 };
  const DURACION_GANADOR = 2600, TOPE = 14000;

  function prepararCarrera() {
    const reqs = datos.comparaciones.map((c) => c.requisito);
    centro.querySelector('#c-req').innerHTML = reqs.map((r) => `<button type="button" data-r="${r}" class="${r === carrera.req ? 'activo' : ''}">${r}</button>`).join('');
    centro.querySelector('#c-fac').innerHTML = datos.factores.map((f, i) => `<button type="button" data-f="${i}" class="${i === carrera.f ? 'activo' : ''}">${fmtMil(datos.tamanos[i].estaciones)}</button>`).join('');
    pintarCarriles(0, 0);
  }

  function comparacion() { return datos.comparaciones.find((c) => c.requisito === carrera.req); }

  function pintarCarriles(pa, pb, final) {
    const c = comparacion(), i = carrera.f;
    const a = c.elegida_us[i], b = c.alternativa_us[i];
    const carril = (clase, nombre, t, p, gana) => `
      <div class="carril ${clase} ${final && gana ? 'gana' : ''}">
        <div class="carril-nombre"><b>${esc(nombre)}</b><span>${fmtT(t)} por operación</span></div>
        <div class="pista-carril"><div class="meta-carril"></div><div class="bus-mini" style="--p:${p}"><i></i><i></i><i></i></div></div>
        <div class="carril-res">${final && gana ? '🏁 gana' : Math.round(p * 100) + ' %'}</div>
      </div>`;
    centro.querySelector('#c-carriles').innerHTML =
      carril('elegida', c.elegida, a, pa, a <= b) + carril('alternativa', c.alternativa, b, pb, b < a);
    const razon = a <= b ? b / a : a / b;
    const ganador = a <= b ? 'la estructura elegida' : 'la alternativa descartada';
    let texto = `Red de ${datos.tamanos[i].estaciones.toLocaleString('es-CO')} estaciones: gana ${ganador}, ${razon.toFixed(1)} veces más rápida. `;
    if (i > 0) {
      const a0 = c.elegida_us[i - 1], b0 = c.alternativa_us[i - 1];
      texto += `Al duplicar, la elegida tardó ×${(a / a0).toFixed(2)} y la alternativa ×${(b / b0).toFixed(2)}. `;
    }
    centro.querySelector('#c-texto').textContent = texto + (EXPLICACION_COMP[c.requisito] || '');
  }

  function correr() {
    cancelAnimationFrame(carrera.raf);
    const c = comparacion(), i = carrera.f;
    const a = c.elegida_us[i], b = c.alternativa_us[i];
    const rapido = Math.min(a, b);
    const da = Math.min(TOPE, DURACION_GANADOR * a / rapido), db = Math.min(TOPE, DURACION_GANADOR * b / rapido);
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { pintarCarriles(Math.min(1, db / da), Math.min(1, da / db), true); return; }
    const t0 = performance.now();
    const paso = (t) => {
      const e = t - t0;
      const pa = Math.min(1, e / da), pb = Math.min(1, e / db);
      const terminado = e >= Math.min(da, db) + 600 || (pa >= 1 && pb >= 1);
      pintarCarriles(pa, pb, terminado);
      if (!terminado) carrera.raf = requestAnimationFrame(paso);
    };
    carrera.raf = requestAnimationFrame(paso);
  }

  centro.addEventListener('click', (e) => {
    const r = e.target.closest('[data-r]'), f = e.target.closest('[data-f]');
    if (r) { carrera.req = r.dataset.r; prepararCarrera(); correr(); }
    else if (f) { carrera.f = +f.dataset.f; prepararCarrera(); correr(); }
    else if (e.target.closest('#c-correr')) correr();
    else if (e.target.closest('#c-duplicar')) { carrera.f = (carrera.f + 1) % datos.factores.length; prepararCarrera(); correr(); }
  });

  /* ------------------------------------------------------------ pruebas en vivo */
  const NOMBRES_ARCHIVO = {
    test_avl: 'AVL', test_tabla_hash: 'Tabla hash', test_lista_doble: 'Lista doble', test_pila: 'Pila',
    test_cola_circular: 'Cola circular', test_ordenamiento: 'Ordenamiento', test_carga: 'Carga',
    test_r1_r2_r3_consultas: 'R1 · R2 · R3', test_r4_proximo_bus: 'R4', test_r5_viaje: 'R5', test_r6_ranking: 'R6',
    test_r7_edicion: 'R7', test_r8_cierres: 'R8', test_r9_deshacer: 'R9', test_r10_fila: 'R10',
    test_reglas_motor: 'Reglas del motor', test_contrato: 'Contrato', test_web: 'App', test_conversion: 'Conversión GTFS',
  };
  let corriendoPruebas = false;

  async function correrPruebas() {
    if (corriendoPruebas) return;
    corriendoPruebas = true;
    const caja = centro.querySelector('#p-pruebas-caja');
    const grilla = centro.querySelector('#pr-grilla');
    const cuenta = centro.querySelector('#pr-cuenta');
    const ultima = centro.querySelector('#pr-ultima');
    const boton = panel.querySelector('#p-pruebas');
    boton.disabled = true;
    caja.hidden = false;
    grilla.textContent = '';
    caja.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const c = { ok: 0, mal: 0, salta: 0 };
    const filas = new Map();
    cuenta.textContent = 'Preparando Python…';
    try {
      const resumen = await ctx.motor.correrPruebas((p) => {
        let fila = filas.get(p.archivo);
        if (!fila) {
          fila = h(`<div class="pruebas-fila"><span>${esc(NOMBRES_ARCHIVO[p.archivo] || p.archivo)}</span><div></div></div>`);
          grilla.appendChild(fila);
          filas.set(p.archivo, fila);
        }
        const estado = p.estado === 'ok' ? 'ok' : p.estado === 'salta' ? 'salta' : 'mal';
        c[estado]++;
        const cuadro = document.createElement('i');
        cuadro.className = estado;
        cuadro.title = `${p.prueba} · ${p.ms} ms${p.detalle ? '\n' + p.detalle : ''}`;
        fila.lastElementChild.appendChild(cuadro);
        cuenta.innerHTML = `<b class="ok">${c.ok} ✓</b>${c.mal ? ` <b class="mal">${c.mal} ✗</b>` : ''}${c.salta ? ` <b>${c.salta} saltadas</b>` : ''}`;
        ultima.textContent = `${p.prueba.replace(/^test_/, '').replace(/_/g, ' ')} · ${p.ms} ms`;
      });
      ultima.innerHTML = resumen.fallas + resumen.errores === 0
        ? `<b class="ok">Las ${resumen.total} pruebas pasaron</b> en ${(resumen.ms / 1000).toFixed(1)} s, dentro del navegador.`
        : `<b class="mal">${resumen.fallas + resumen.errores} pruebas fallaron</b> de ${resumen.total}. Pasa el mouse sobre los cuadros rojos para ver el detalle.`;
      toast(resumen.fallas + resumen.errores === 0 ? `✓ ${resumen.total} pruebas en verde` : 'Hay pruebas que fallaron', resumen.fallas + resumen.errores ? 'error' : '');
    } catch (err) {
      ultima.textContent = 'No se pudieron correr las pruebas: ' + err.message;
    }
    // test_web reinicia la red del puente: la interfaz vuelve a leer su estado
    await ctx.redCambio();
    boton.disabled = false;
    corriendoPruebas = false;
  }
  panel.querySelector('#p-pruebas').addEventListener('click', correrPruebas);

  panel.querySelector('#p-vivo').addEventListener('click', async (e) => {
    const b = e.currentTarget;
    b.disabled = true;
    panel.querySelector('#p-vivo-txt').textContent = 'Midiendo en tu navegador con Pyodide… la interfaz sigue funcionando.';
    try {
      vivo = await ctx.motor.dato('medir_en_vivo', [4, 8, 16]);
      const fs = datos.factores;
      vivo.operaciones.forEach((o) => { while (o.tiempos_us.length < fs.length) o.tiempos_us.push(null); o.tiempos_us = o.tiempos_us.filter((x) => x !== null); });
      panel.querySelector('#p-vivo-txt').innerHTML = 'Línea punteada: <b>este dispositivo</b>, con redes de unas 600, 1.200 y 2.400 estaciones (cada una el doble de la anterior). El valor absoluto cambia; la forma de la curva no.';
      pintar();
      toast('Medición en este dispositivo terminada.');
    } catch (err) {
      panel.querySelector('#p-vivo-txt').textContent = 'No se pudo medir: ' + err.message;
    }
    b.disabled = false;
  });

  return {
    panel, centro, titulo: 'Rendimiento',
    activar() { if (!datos) cargar(); else correr(); },
    desactivar() { cancelAnimationFrame(carrera.raf); },
    async carreraDe(req, f = 0) { if (!datos) await cargar(); carrera.req = req; carrera.f = f; prepararCarrera(); correr(); },
    correrPruebas,
  };
}
