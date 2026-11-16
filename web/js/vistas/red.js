/* Vista Red: R1 (estado), R3 (rango) y R7 (recorrido en ambos sentidos). Dueño: Miguel. */

import { colorRuta } from '../mapa.js';
import { autocompletar, esc, h, textoMs, tiempoMotor } from '../ui.js';
import { abrirVista3D } from '../vista3d.js';

export function crearVistaRed(ctx) {
  const { motor, mapa } = ctx;
  const panel = h(`<div class="panel-in">
    <section class="seccion">
      <span class="eyebrow">¿Existe y está abierta? <span class="req">R1</span></span>
      <form class="fila-form" id="r-form-estado">
        <div class="campo simple"><label for="r-estado" class="oculto">Nombre exacto</label><input id="r-estado" placeholder="Nombre exacto, p. ej. RICAURTE" spellcheck="false"></div>
        <button class="boton">Consultar</button>
      </form>
      <div id="r-res-estado" aria-live="polite"></div>
    </section>
    <section class="seccion">
      <span class="eyebrow">Estaciones abiertas en un rango <span class="req">R3</span></span>
      <form class="fila-form" id="r-form-rango">
        <div class="campo simple"><label for="r-desde" class="oculto">Desde</label><input id="r-desde" value="CALLE 26" spellcheck="false"></div>
        <div class="campo simple"><label for="r-hasta" class="oculto">Hasta</label><input id="r-hasta" value="CALLE 80" spellcheck="false"></div>
        <button class="boton">Listar</button>
      </form>
      <div id="r-res-rango" aria-live="polite"></div>
    </section>
    <section class="seccion">
      <span class="eyebrow">Recorrido de una ruta <span class="req">R7</span></span>
      <form class="fila-form" id="r-form-ruta">
        <div class="campo simple"><label for="r-ruta" class="oculto">Ruta</label><input id="r-ruta" list="lista-rutas" placeholder="Ruta, p. ej. F23-1" spellcheck="false"></div>
        <button class="boton">Ver</button>
      </form>
      <div class="interruptor" role="group" aria-label="Sentido"><button type="button" class="activo" data-rev="0">En su sentido</button><button type="button" data-rev="1">Al revés</button></div>
      <div id="r-res-ruta"></div>
    </section>
  </div>`);

  const $ = (s) => panel.querySelector(s);
  let alReves = false, rutaActual = null;

  $('#r-form-estado').addEventListener('submit', async (e) => {
    e.preventDefault();
    const n = $('#r-estado').value.trim().toUpperCase();
    if (!n) return;
    const r = await motor.llamar('estado', n);
    tiempoMotor(r.ms);
    const clase = { abierta: 'ok', cerrada: 'cerr', 'no existe': 'no' }[r.datos];
    $('#r-res-estado').innerHTML = `<p class="respuesta"><span class="chip ${clase}">${r.datos}</span> ${esc(n)} <span class="tiempo">${textoMs(r.ms)} · tabla hash</span></p>`;
    if (r.datos !== 'no existe') ctx.seleccionar(n);
  });

  $('#r-form-rango').addEventListener('submit', async (e) => {
    e.preventDefault();
    const a = $('#r-desde').value.trim().toUpperCase(), b = $('#r-hasta').value.trim().toUpperCase();
    const r = await motor.llamar('rango', a, b);
    tiempoMotor(r.ms);
    $('#r-res-rango').innerHTML = r.datos.length
      ? `<p class="pista">${r.datos.length} estaciones abiertas, en orden alfabético</p><div class="pildoras">${r.datos.map((n) => `<button class="pildora" data-n="${esc(n)}">${esc(n)}</button>`).join('')}</div>`
      : '<p class="pista">Ninguna estación abierta en ese rango.</p>';
  });
  $('#r-res-rango').addEventListener('click', (e) => { const b = e.target.closest('[data-n]'); if (b) ctx.seleccionar(b.dataset.n); });

  async function verRuta() {
    const ruta = $('#r-ruta').value.trim().toUpperCase();
    if (!ruta) return;
    const r = await motor.llamar('recorrido', ruta, alReves);
    tiempoMotor(r.ms);
    rutaActual = ruta;
    if (!r.datos.length) { $('#r-res-ruta').innerHTML = '<p class="pista">Esa ruta no existe.</p>'; mapa.limpiar(); return; }
    const c = colorRuta(ruta);
    $('#r-res-ruta').innerHTML = `<p class="pista"><span class="ruta" style="--rc:${c}">${esc(ruta)}</span> ${r.datos.length} paradas ${alReves ? '(al revés)' : ''}</p>
      ${r.datos.length > 1 ? '<button class="boton boton-3d" id="r-3d" type="button"><span aria-hidden="true">◢◣</span> Recorrer en 3D</button>' : ''}
      <ol class="lista-ruta" style="--tramo:${c}">${r.datos.map((n) => `<li><button class="enlace" data-n="${esc(n)}">${esc(n)}</button>${ctx.cerrada(n) ? ' <span class="chip cerr">cerrada</span>' : ''}</li>`).join('')}</ol>`;
    const b3 = $('#r-3d');
    if (b3) b3.addEventListener('click', () => abrirVista3D({ mapa, tramos: [{ ruta, paradas: r.datos }] }));
    mapa.resaltar([{ ruta, paradas: r.datos }], { bus: true, color: c });
    mapa.enfocar(r.datos);
  }
  $('#r-form-ruta').addEventListener('submit', (e) => { e.preventDefault(); verRuta(); });
  panel.querySelectorAll('.interruptor button').forEach((b) => b.addEventListener('click', () => {
    alReves = b.dataset.rev === '1';
    panel.querySelectorAll('.interruptor button').forEach((x) => x.classList.toggle('activo', x === b));
    if (rutaActual) verRuta();
  }));
  $('#r-res-ruta').addEventListener('click', (e) => { const b = e.target.closest('[data-n]'); if (b) ctx.seleccionar(b.dataset.n); });
  autocompletar($('#r-estado'), motor, { alMedir: tiempoMotor });

  return {
    panel,
    titulo: 'Red',
    activar() { if (rutaActual) verRuta(); },
    desactivar() { mapa.limpiar(); },
    alCambiarRed() { if (rutaActual) verRuta(); },
    verRuta(r) { $('#r-ruta').value = r; verRuta(); },
    consultarEstado(n) { $('#r-estado').value = n; $('#r-form-estado').requestSubmit(); },
    rango(a, b) { $('#r-desde').value = a; $('#r-hasta').value = b; $('#r-form-rango').requestSubmit(); },
  };
}
