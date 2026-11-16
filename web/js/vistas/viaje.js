/* Vista Viaje: R2 (autocompletar), R5 (viaje) y R4 (próximo bus por tramo). Dueño: Miguel. */

import { colorRuta } from '../mapa.js';
import { autocompletar, avisoConPersonalidad, esc, esperaTexto, h, tiempoMotor } from '../ui.js';
import { abrirVista3D } from '../vista3d.js';

export function crearVistaViaje(ctx) {
  const { motor, mapa } = ctx;
  const panel = h(`<div class="panel-in">
    <section class="seccion">
      <span class="eyebrow">Planear viaje</span>
      <div class="campos">
        <div class="campo"><span class="punto-campo" aria-hidden="true"></span><label for="v-origen">Origen</label><input id="v-origen" placeholder="Escribe una estación" spellcheck="false"></div>
        <button class="intercambiar" id="v-cambiar" type="button" aria-label="Intercambiar origen y destino">⇅</button>
        <div class="campo destino"><span class="punto-campo" aria-hidden="true"></span><label for="v-destino">Destino</label><input id="v-destino" placeholder="Escribe una estación" spellcheck="false"></div>
      </div>
      <p class="pista"><span class="req">R2</span> Sugerencias del motor mientras escribes · <span class="req">R5</span> menos paradas, máximo un transbordo</p>
    </section>
    <div id="v-resultado" aria-live="polite"></div>
  </div>`);
  const origen = panel.querySelector('#v-origen'), destino = panel.querySelector('#v-destino');
  const resultado = panel.querySelector('#v-resultado');
  let ultimo = null;

  autocompletar(origen, motor, { alElegir: () => (destino.value ? calcular() : destino.focus()), alMedir: tiempoMotor });
  autocompletar(destino, motor, { alElegir: calcular, alMedir: tiempoMotor });
  panel.querySelector('#v-cambiar').addEventListener('click', () => { [origen.value, destino.value] = [destino.value, origen.value]; if (origen.value && destino.value) calcular(); });

  resultado.innerHTML = vacio();

  async function calcular() {
    const o = origen.value.trim().toUpperCase(), d = destino.value.trim().toUpperCase();
    if (!o || !d) return;
    const r = await motor.llamar('itinerario', o, d, ctx.horaTexto());
    tiempoMotor(r.ms);
    ultimo = { o, d };
    pintar(o, d, r.datos);
  }

  function pintar(o, d, it) {
    if (it.tramos === null) {
      mapa.limpiar();
      const motivo = !ctx.existe(o) || !ctx.existe(d) ? 'Alguna de las dos estaciones no existe.' : ctx.cerrada(o) || ctx.cerrada(d) ? 'Alguna de las dos estaciones está cerrada.' : 'Estas estaciones no se conectan con un solo transbordo. Prueba con una estación intermedia.';
      resultado.innerHTML = `<div class="sin-viaje"><b>Sin viaje posible</b><p>${motivo}</p></div>`;
      return;
    }
    if (it.tramos.length === 0) {
      mapa.limpiar();
      resultado.innerHTML = `<div class="sin-viaje"><b>Ya estás ahí</b><p>Origen y destino son la misma estación.</p></div>`;
      return;
    }
    const paradas = it.tramos.reduce((s, t) => s + t.n, 0);
    const espera = it.tramos.reduce((s, t) => s + t.espera, 0);
    resultado.innerHTML = `
      <div class="resumen">
        <div><b>${paradas}</b><span>paradas</span></div>
        <div><b>${it.tramos.length - 1}</b><span>${it.tramos.length === 2 ? 'transbordo' : 'transbordos'}</span></div>
        <div><b class="mono">${it.tramos[0].sale}</b><span>sale el bus</span></div>
      </div>
      <div class="botones dos">
        <button class="boton boton-3d" id="v-3d" type="button"><span aria-hidden="true">◢◣</span> Ver en 3D</button>
        <button class="boton boton-rx" id="v-rx" type="button"><span aria-hidden="true">◎</span> Rayos X</button>
      </div>
      <div id="v-rx-panel"></div>
      <div class="seccion">
        <div class="seccion-cab"><span class="eyebrow">Itinerario</span><span class="chip prog">Programado</span></div>
        <ol class="itinerario">${it.tramos.map((t, i) => tramo(t, i)).join('')}
          <li class="parada"><div class="riel"><span class="nodo-it fin"></span></div><div class="cuerpo"><div class="nombre">${esc(d)}</div>
          <div class="meta">Llegada <span class="mono">~${it.llegada}</span> <span class="chip est">Estimado</span></div></div></li>
        </ol>
        ${espera >= 30 ? `<p class="alerta">Ojo: este viaje tiene la menor cantidad de paradas, pero esperas ${esperaTexto(espera)} en total. Así funciona R5: minimiza paradas, no tiempo.</p>` : ''}
        <p class="nota">Horas de salida: <b>Programado</b> (horarios.csv). Llegadas: <b>Estimado</b> con la duración típica de cada tramo; el GTFS no identifica qué bus es cuál.</p>
      </div>`;
    const tramos = it.tramos.map((t) => ({ ruta: t.ruta, paradas: t.paradas }));
    resultado.querySelector('#v-3d').addEventListener('click', () => abrirVista3D({ mapa, tramos }));
    resultado.querySelector('#v-rx').addEventListener('click', () => rayosX(o, d, false));
    mapa.resaltar(tramos, { bus: true });
    mapa.enfocar(it.tramos.flatMap((t) => t.paradas));
    const primero = it.tramos[0];
    if (primero.espera <= 3) avisoConPersonalidad('apura-' + o + primero.sale, `¡Uy, apúrale! El ${primero.ruta} sale en ${esperaTexto(primero.espera)} de ${o}.`);
    const larga = it.tramos.find((t) => t.espera >= 45);
    if (larga) avisoConPersonalidad('larga-' + larga.ruta, `Ojo: el ${larga.ruta} no pasa por ${larga.sube} hasta las ${larga.sale}. Toca paciencia.`);
  }

  function tramo(t, i) {
    const c = colorRuta(t.ruta);
    const inter = t.paradas.slice(1, -1);
    const meta = i === 0
      ? `Sale <span class="mono">${t.sale}</span> · espera ${esperaTexto(t.espera)}`
      : `Transbordo · sale <span class="mono">${t.sale}</span> · espera ${esperaTexto(t.espera)}`;
    return `<li class="parada" style="--tramo:${c}"><div class="riel"><span class="nodo-it ${i ? 'transbordo' : ''}"></span></div>
      <div class="cuerpo"><div class="nombre">${esc(t.sube)}</div><div class="meta">${meta}</div>
        <div class="tramo"><div class="tramo-cab"><span class="ruta" style="--rc:${c}">${esc(t.ruta)}</span><span>${t.n} ${t.n === 1 ? 'parada' : 'paradas'} hasta ${esc(t.baja)} · ~${t.minutos} min</span></div>
        ${inter.length ? `<details><summary>Pasa por ${inter.length} ${inter.length === 1 ? 'estación' : 'estaciones'}</summary><ol>${inter.map((p) => `<li>${esc(p)}${ctx.cerrada(p) ? ' <span class="chip cerr">cerrada</span>' : ''}</li>`).join('')}</ol></details>` : ''}
        </div></div></li>`;
  }

  /* Rayos X: anima la búsqueda real de R5 (la traza la devuelve el motor). */
  async function rayosX(o, d, lento) {
    const caja = resultado.querySelector('#v-rx-panel');
    const traza = await motor.dato('traza_viaje', o, d);
    mapa.enfocar([o, d, ...traza.ida.flatMap((r) => r.visitadas.map((v) => v[0])), ...traza.vuelta.flatMap((r) => r.visitadas.map((v) => v[0]))]);
    caja.innerHTML = `<div class="rx">
      <div class="seccion-cab"><span class="eyebrow">Así busca el motor <span class="req">R5</span></span>
        <span class="botones"><button class="mini" id="rx-repetir">Repetir</button><button class="mini" id="rx-lento" aria-pressed="${lento}">Lento</button></span></div>
      <ol class="rx-pasos">
        <li data-fase="ida"><b>1 · Frente del origen</b><span id="rx-ida"></span>
          <small>Por cada ruta que para en ${esc(o)}, avanza contando paradas y anota la mejor forma de llegar a cada estación.</small></li>
        <li data-fase="vuelta"><b>2 · Frente del destino</b><span id="rx-vuelta"></span>
          <small>Por cada ruta que llega a ${esc(d)}, retrocede. Si una estación ya fue alcanzada desde el origen con otra ruta, ahí se puede transbordar.</small></li>
        <li data-fase="fin"><b>3 · El mejor</b><span id="rx-fin"></span>
          <small>Menos paradas; si empatan, directo antes que transbordo.</small></li>
      </ol>
      <p class="rx-leyenda"><span><i class="l-ida"></i>origen</span><span><i class="l-vuelta"></i>destino</span><span><i class="l-encuentro"></i>se tocan</span><span><i class="l-mejora"></i>nuevo mejor</span></p>
    </div>`;
    const fases = ['ida', 'vuelta', 'fin'];
    mapa.animarTraza(traza, o, d, {
      lento,
      alPaso: (c) => {
        caja.querySelectorAll('.rx-pasos li').forEach((li) => {
          li.classList.toggle('activa', li.dataset.fase === c.fase);
          li.classList.toggle('hecha', fases.indexOf(li.dataset.fase) < fases.indexOf(c.fase));
        });
        caja.querySelector('#rx-ida').textContent = `${c.rutasIda} rutas · ${c.alcanzadas} estaciones alcanzadas`;
        caja.querySelector('#rx-vuelta').textContent = c.fase === 'ida' ? '' : `${c.rutasVuelta} rutas · ${c.revisadas} paradas revisadas · ${c.encuentros} encuentros`;
        const m = c.mejor;
        caja.querySelector('#rx-fin').textContent = !m ? '' : m.directo ? `Directo en ${m.ruta}: ${m.paradas} paradas` : `${m.paradas} paradas: ${m.ruta1} hasta ${m.estacion} y luego ${m.ruta2}`;
      },
    });
    caja.querySelector('#rx-repetir').addEventListener('click', () => rayosX(o, d, lento));
    caja.querySelector('#rx-lento').addEventListener('click', () => rayosX(o, d, !lento));
  }

  function vacio() {
    return `<div class="vacio-viaje"><p>Elige origen y destino. El motor busca el viaje <b>directo o con un transbordo</b> que pase por menos paradas.</p>
      <p class="pista">Prueba: <button class="enlace" data-o="PORTAL AMERICAS" data-d="CALLE 100">Portal Américas → Calle 100</button> · <button class="enlace" data-o="PORTAL NORTE" data-d="PORTAL USME">Portal Norte → Portal Usme</button></p></div>`;
  }
  resultado.addEventListener('click', (e) => {
    const b = e.target.closest('[data-o]');
    if (!b) return;
    origen.value = b.dataset.o;
    destino.value = b.dataset.d;
    calcular();
  });

  return {
    panel,
    titulo: 'Viaje',
    activar() { if (ultimo) calcular(); },
    desactivar() { mapa.limpiar(); },
    alCambiarHora() { if (ultimo) calcular(); },
    alCambiarRed() { if (ultimo) calcular(); },
    alSeleccionarEstacion(n) { if (!origen.value) { origen.value = n; destino.focus(); } else if (!destino.value) { destino.value = n; calcular(); } },
    planear(o, d) { origen.value = o; destino.value = d; return calcular(); },
    async rayos(o, d) { origen.value = o; destino.value = d; await calcular(); return rayosX(o, d, false); },
    async escribir(texto) {
      // escribe letra por letra en Origen para mostrar R2 en vivo
      destino.value = '';
      origen.value = '';
      origen.focus();
      for (const letra of texto) {
        origen.value += letra;
        origen.dispatchEvent(new Event('input'));
        await new Promise((r) => setTimeout(r, 260));
      }
    },
  };
}
