/* Vista Operación: R7 (agregar/quitar parada), R8 (cerrar/reabrir) y R9 (deshacer/rehacer).
 * Las dos pilas de R9 se dibujan tal como las guarda el motor. Dueño: Miguel. */

import { colorRuta } from '../mapa.js';
import { autocompletar, avisoConPersonalidad, esc, h, tiempoMotor, toast } from '../ui.js';

export function crearVistaOperacion(ctx) {
  const { motor, mapa } = ctx;
  const panel = h(`<div class="panel-in">
    <section class="seccion">
      <span class="eyebrow">Cerrar o reabrir una estación <span class="req">R8</span></span>
      <form class="fila-form" id="o-form-est">
        <div class="campo simple"><label for="o-est" class="oculto">Estación</label><input id="o-est" placeholder="Estación" spellcheck="false"></div>
      </form>
      <div class="botones"><button class="boton peligro" id="o-cerrar" type="button">Cerrar</button><button class="boton" id="o-reabrir" type="button">Reabrir</button></div>
      <p class="pista">Una estación cerrada sale de búsquedas, rangos y ranking, y nadie sube, baja ni transborda ahí. Al cerrar se calcula el impacto en todos los viajes.</p>
      <div id="o-impacto" aria-live="polite"></div>
    </section>
    <section class="seccion">
      <span class="eyebrow">Editar una ruta <span class="req">R7</span></span>
      <form class="fila-form" id="o-form-ruta">
        <div class="campo simple"><label for="o-ruta" class="oculto">Ruta</label><input id="o-ruta" list="lista-rutas" placeholder="Ruta, p. ej. 1-1" spellcheck="false"></div>
        <button class="boton">Abrir</button>
      </form>
      <div id="o-editor"></div>
    </section>
    <section class="seccion">
      <div class="seccion-cab"><span class="eyebrow">Historial <span class="req">R9</span></span>
        <div class="botones"><button class="boton" id="o-deshacer" type="button" title="Ctrl+Z">↶ Deshacer</button><button class="boton" id="o-rehacer" type="button" title="Ctrl+Y">↷ Rehacer</button></div></div>
      <div class="pilas">
        <div><span class="pila-titulo">Pila deshacer</span><ol class="pila" id="o-pila-d"></ol></div>
        <div><span class="pila-titulo">Pila rehacer</span><ol class="pila" id="o-pila-r"></ol></div>
      </div>
      <p class="pista">Un cambio nuevo vacía la pila de rehacer.</p>
    </section>
  </div>`);
  const $ = (s) => panel.querySelector(s);
  let ruta = null;

  autocompletar($('#o-est'), motor, { alMedir: tiempoMotor, alElegir: (n) => ctx.seleccionar(n) });

  async function cambio(op, ...args) {
    const r = await motor.llamar(op, ...args);
    tiempoMotor(r.ms);
    if (r.datos) await ctx.redCambio();
    await pintarHistorial(op);
    return r.datos;
  }

  $('#o-cerrar').addEventListener('click', () => cerrarConImpacto($('#o-est').value.trim().toUpperCase()));

  /* Cerrar (R8) y medir qué viajes se pierden: el motor recalcula R5 para todos los pares. */
  async function cerrarConImpacto(n) {
    if (!n) return;
    $('#o-est').value = n;
    const caja = $('#o-impacto');
    caja.innerHTML = `<div class="impacto calculando"><span class="eyebrow">Calculando el impacto</span>
      <p>El motor está recalculando el viaje (R5) entre <b>todos</b> los pares de estaciones, antes y después del cierre…</p><div class="barra-cargando"><i></i></div></div>`;
    const r = await motor.llamar('impacto_cierre', n);
    tiempoMotor(r.ms);
    const d = r.datos;
    if (!d.cerrada) { caja.innerHTML = ''; toast(`No se pudo cerrar ${n}: no existe o ya estaba cerrada.`, 'error'); return; }
    await ctx.redCambio();
    await pintarHistorial();
    mapa.ondaCierre(n, d.rutas, d.mas_afectadas);
    ctx.seleccionar(n);
    const fmt = (x) => x.toLocaleString('es-CO');
    caja.innerHTML = `<div class="impacto">
      <span class="eyebrow">Impacto del cierre <span class="req">R8 + R5</span></span>
      <p class="impacto-cifra"><b id="o-contador">0</b> pares de estaciones se quedan sin viaje</p>
      <p class="pista">Pares que antes tenían viaje directo o con un transbordo y ahora no, sin contar los ${fmt(d.pares_propios)} que salen o llegan a ${esc(n)}.</p>
      ${d.mas_afectadas.length ? `<div><span class="pila-titulo">Más afectadas</span><ol class="afectadas">${d.mas_afectadas.map(([e, c]) => `<li><span>${esc(e)}</span><b>−${c}</b></li>`).join('')}</ol></div>` : '<p class="pista">Ningún otro viaje depende de esta estación: siempre hay otra forma de llegar.</p>'}
      <div class="ranking-cambio"><span class="pila-titulo">Ranking R6</span><span>${d.ranking_antes.slice(0, 3).map(esc).join(' · ')}</span><span>→ ${d.ranking_despues.slice(0, 3).map(esc).join(' · ')}</span></div>
      <p class="tiempo">R5 ejecutado ${fmt(d.viajes_calculados)} veces en ${fmt(d.ms)} ms · ${d.rutas.length} rutas pasan por ${esc(n)}</p>
      <button class="boton" id="o-deshacer-cierre" type="button">↶ Deshacer el cierre</button>
    </div>`;
    contar($('#o-contador'), d.nuevos);
    $('#o-deshacer-cierre').addEventListener('click', async () => { await deshacer(); caja.innerHTML = ''; mapa.limpiar(); });
    if (d.nuevos > 100) avisoConPersonalidad('cierre-' + n, `Cerrar ${n} deja a ${fmt(d.nuevos)} viajes sin opción. Mejor que no sea en hora pico.`);
  }

  function contar(elem, hasta) {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { elem.textContent = hasta.toLocaleString('es-CO'); return; }
    const t0 = performance.now();
    const paso = (t) => { const p = Math.min(1, (t - t0) / 1400); elem.textContent = Math.round(hasta * (1 - Math.pow(1 - p, 3))).toLocaleString('es-CO'); if (p < 1) requestAnimationFrame(paso); };
    requestAnimationFrame(paso);
    setTimeout(() => { elem.textContent = hasta.toLocaleString('es-CO'); }, 1600);   // por si la pestaña está en segundo plano
  }
  $('#o-reabrir').addEventListener('click', async () => {
    const n = $('#o-est').value.trim().toUpperCase();
    if (!n) return;
    const ok = await cambio('reabrir', n);
    toast(ok ? `${n} reabierta.` : `No se pudo reabrir ${n}: no existe o ya estaba abierta.`, ok ? '' : 'error');
    if (ok) ctx.seleccionar(n);
  });

  async function abrirRuta() {
    ruta = $('#o-ruta').value.trim().toUpperCase();
    if (!ruta) return;
    const paradas = await motor.dato('recorrido', ruta, false);
    const ed = $('#o-editor');
    if (!paradas.length) { ed.innerHTML = '<p class="pista">Esa ruta no existe.</p>'; return; }
    const c = colorRuta(ruta);
    ed.innerHTML = `<ol class="editor-ruta" style="--tramo:${c}">${paradas.map((p) => `
      <li><span class="nombre-parada">${esc(p)}</span>
        <button class="mini" data-quitar="${esc(p)}" aria-label="Quitar ${esc(p)} de ${esc(ruta)}">Quitar</button>
        <button class="mini" data-despues="${esc(p)}" aria-label="Agregar una parada después de ${esc(p)}">+ después</button></li>`).join('')}</ol>
      <form class="agregar" id="o-agregar" hidden><p class="pista" id="o-agregar-txt"></p>
        <div class="fila-form"><div class="campo simple"><label for="o-nueva" class="oculto">Estación nueva</label><input id="o-nueva" placeholder="Estación a agregar" spellcheck="false"></div><button class="boton">Agregar</button></div></form>`;
    mapa.resaltar([{ ruta, paradas }], { color: c });
    autocompletar($('#o-nueva'), motor, { alMedir: tiempoMotor });
  }
  $('#o-form-ruta').addEventListener('submit', (e) => { e.preventDefault(); abrirRuta(); });

  let despuesDe = null;
  $('#o-editor').addEventListener('click', async (e) => {
    const q = e.target.closest('[data-quitar]'), a = e.target.closest('[data-despues]');
    if (q) {
      const ok = await cambio('quitar_parada', ruta, q.dataset.quitar);
      toast(ok ? `${q.dataset.quitar} ya no es parada de ${ruta}.` : 'No se pudo quitar.', ok ? '' : 'error');
      abrirRuta();
    } else if (a) {
      despuesDe = a.dataset.despues;
      $('#o-agregar').hidden = false;
      $('#o-agregar-txt').textContent = `Nueva parada de ${ruta} después de ${despuesDe}:`;
      $('#o-nueva').focus();
    }
  });
  $('#o-editor').addEventListener('submit', async (e) => {
    e.preventDefault();
    const nueva = $('#o-nueva').value.trim().toUpperCase();
    if (!nueva || !despuesDe) return;
    const ok = await cambio('agregar_parada', ruta, nueva, despuesDe);
    toast(ok ? `${nueva} agregada a ${ruta}.` : `No se pudo: la estación no existe o ya está en ${ruta}.`, ok ? '' : 'error');
    if (ok) abrirRuta();
  });

  async function pintarHistorial(animar) {
    const { deshacer, rehacer } = await motor.dato('historial');
    const lista = (xs, vacia) => (xs.length ? xs.map((x) => `<li>${esc(x)}</li>`).join('') : `<li class="vacia">${vacia}</li>`);
    $('#o-pila-d').innerHTML = lista(deshacer, 'vacía');
    $('#o-pila-r').innerHTML = lista(rehacer, 'vacía');
    $('#o-deshacer').disabled = !deshacer.length;
    $('#o-rehacer').disabled = !rehacer.length;
    if (animar === 'deshacer' || animar === 'rehacer') {
      document.body.classList.remove('rebobinar');
      void document.body.offsetWidth;
      document.body.classList.add('rebobinar');
    }
  }
  const deshacer = async () => { const ok = await cambio('deshacer'); toast(ok ? 'Cambio deshecho.' : 'No hay nada para deshacer.'); if (ruta) abrirRuta(); };
  const rehacer = async () => { const ok = await cambio('rehacer'); toast(ok ? 'Cambio rehecho.' : 'No hay nada para rehacer.'); if (ruta) abrirRuta(); };
  $('#o-deshacer').addEventListener('click', deshacer);
  $('#o-rehacer').addEventListener('click', rehacer);

  return {
    panel,
    titulo: 'Operación',
    activar() { pintarHistorial(); if (ruta) abrirRuta(); },
    desactivar() { mapa.limpiar(); },
    alSeleccionarEstacion(n) { $('#o-est').value = n; },
    deshacer,
    rehacer,
    cerrarConImpacto,
    abrirRuta(r) { $('#o-ruta').value = r; return abrirRuta(); },
    async quitar(r, e) { const ok = await cambio('quitar_parada', r, e); $('#o-ruta').value = r; await abrirRuta(); return ok; },
  };
}
