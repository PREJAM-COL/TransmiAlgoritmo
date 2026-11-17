/* Vista Hora pico: R10 (simular_fila). Las llegadas son de ejemplo (Simulado);
 * la fila FIFO y el abordaje los calcula el motor. Dueño: Miguel. */

import { fmtN, h, hhmm, tiempoMotor } from '../ui.js';

export function crearVistaHoraPico(ctx) {
  const { motor } = ctx;
  const panel = h(`<div class="panel-in">
    <section class="seccion">
      <span class="eyebrow">Fila de abordaje <span class="req">R10</span></span>
      <form id="h-form" class="grilla-form">
        <label>Pasajeros<input id="h-p" type="number" min="1" max="1000000" value="12000"></label>
        <label>Duración del pico (min)<input id="h-d" type="number" min="1" max="600" value="120"></label>
        <label>Un bus cada (min)<input id="h-f" type="number" min="1" max="60" value="1"></label>
        <label>Cupo por bus<input id="h-c" type="number" min="1" max="500" value="160"></label>
        <button class="boton primario">Simular</button>
      </form>
      <p class="pista">Las llegadas son <span class="chip sim">Simulado</span>: más gente en el centro del pico. La fila es FIFO: sube primero quien llegó primero.</p>
    </section>
    <div id="h-res" aria-live="polite"></div>
  </div>`);
  const centro = h(`<div class="lienzo-pico"><canvas id="h-canvas" aria-label="Personas en la fila y espera a lo largo del pico"></canvas>
    <div class="leyenda-pico"><span><i class="l-fila"></i>Personas en la fila</span><span><i class="l-espera"></i>Espera de quien llega (min)</span></div></div>`);
  const $ = (s) => panel.querySelector(s);
  let serie = null, animacion = 0;

  $('#h-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const P = +$('#h-p').value, D = +$('#h-d').value, f = +$('#h-f').value, c = +$('#h-c').value;
    $('#h-res').innerHTML = '<p class="pista">Simulando…</p>';
    const llegadasSeg = await motor.dato('generar_llegadas', P, D);         // R10 trabaja en segundos
    const r = await motor.llamar('fila', llegadasSeg, f * 60, c);
    tiempoMotor(r.ms);
    const llegadas = llegadasSeg.map((s) => s / 60);                         // y la gráfica, en minutos
    const ab = r.datos.abordaje.map((s) => s / 60);
    let suma = 0, max = 0;
    for (let i = 0; i < ab.length; i++) { const w = ab[i] - llegadas[i]; suma += w; if (w > max) max = w; }
    const buses = new Set(ab).size;
    const fin = ab[ab.length - 1];
    serie = construirSerie(llegadas, ab, fin);
    $('#h-res').innerHTML = `<div class="resumen">
        <div><b>${(suma / ab.length).toFixed(1)}</b><span>min de espera promedio</span></div>
        <div><b>${max.toFixed(1)}</b><span>min de espera máxima</span></div>
        <div><b>${fmtN(buses)}</b><span>buses con gente</span></div></div>
      <p class="pista">El último bus sale en el minuto ${fmtN(Math.round(fin))} del pico (segundo ${fmtN(Math.round(fin * 60))}; el primero sale en el segundo ${fmtN(f * 60)}). El motor procesó ${fmtN(ab.length)} pasajeros en <b>${r.datos.ms} ms</b> con una cola circular: O(P) si llegan en orden, O(P log P) si hay que ordenarlas.</p>
      ${max > 30 ? `<p class="alerta">No cabe ni un alfiler: con un bus cada ${f} min y ${c} de cupo, la fila crece más rápido de lo que se vacía. Prueba otra frecuencia.</p>` : ''}`;
    dibujar(1);
    animar();
  });

  function construirSerie(llegadas, ab, fin) {
    const T = Math.ceil(Math.max(fin, llegadas[llegadas.length - 1])) + 1;
    const fila = new Array(T).fill(0), espera = new Array(T).fill(null);
    let i = 0, j = 0;
    const subidos = [...ab].sort((a, b) => a - b);
    for (let t = 0; t < T; t++) {
      let suma = 0, n = 0;
      while (i < llegadas.length && llegadas[i] <= t) { suma += ab[i] - llegadas[i]; n++; i++; }
      while (j < subidos.length && subidos[j] <= t) j++;
      fila[t] = i - j;
      if (n) espera[t] = suma / n;
    }
    return { T, fila, espera, maxFila: Math.max(1, ...fila), maxEspera: Math.max(1, ...espera.filter((x) => x !== null)) };
  }

  function dibujar(progreso) {
    const cv = centro.querySelector('canvas');
    const r = cv.getBoundingClientRect();
    if (!r.width) return;
    const dpr = Math.min(2, devicePixelRatio || 1);
    cv.width = r.width * dpr; cv.height = r.height * dpr;
    const g = cv.getContext('2d');
    g.scale(dpr, dpr);
    const css = getComputedStyle(document.documentElement);
    const color = (v) => css.getPropertyValue(v).trim();
    const M = { l: 56, r: 56, t: 24, b: 36 }, W = r.width - M.l - M.r, H = r.height - M.t - M.b;
    g.font = '11px JetBrains Mono, monospace';
    g.fillStyle = color('--tenue');
    g.strokeStyle = color('--linea');
    for (let k = 0; k <= 4; k++) {
      const y = M.t + H - (H * k) / 4;
      g.beginPath(); g.moveTo(M.l, y); g.lineTo(M.l + W, y); g.stroke();
      g.textAlign = 'right'; g.fillText(fmtN(Math.round((serie.maxFila * k) / 4)), M.l - 8, y + 4);
      g.textAlign = 'left'; g.fillText(Math.round((serie.maxEspera * k) / 4) + ' min', M.l + W + 8, y + 4);
    }
    g.textAlign = 'center';
    for (let k = 0; k <= 4; k++) g.fillText('min ' + Math.round((serie.T * k) / 4), M.l + (W * k) / 4, M.t + H + 22);
    const hasta = Math.max(1, Math.floor(serie.T * progreso));
    const x = (t) => M.l + (W * t) / serie.T;
    g.beginPath();
    g.moveTo(x(0), M.t + H);
    for (let t = 0; t < hasta; t++) g.lineTo(x(t), M.t + H - (H * serie.fila[t]) / serie.maxFila);
    g.lineTo(x(hasta - 1), M.t + H);
    g.closePath();
    const grad = g.createLinearGradient(0, M.t, 0, M.t + H);
    grad.addColorStop(0, 'rgba(215,38,46,.55)'); grad.addColorStop(1, 'rgba(215,38,46,.05)');
    g.fillStyle = grad; g.fill();
    g.beginPath();
    let empezado = false;
    for (let t = 0; t < hasta; t++) {
      if (serie.espera[t] === null) continue;
      const y = M.t + H - (H * serie.espera[t]) / serie.maxEspera;
      empezado ? g.lineTo(x(t), y) : g.moveTo(x(t), y);
      empezado = true;
    }
    g.strokeStyle = color('--cian'); g.lineWidth = 2; g.stroke(); g.lineWidth = 1;
  }

  function animar() {
    cancelAnimationFrame(animacion);
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { dibujar(1); return; }
    const t0 = performance.now();
    const paso = (now) => { const p = Math.min(1, (now - t0) / 1600); dibujar(p); if (p < 1) animacion = requestAnimationFrame(paso); };
    animacion = requestAnimationFrame(paso);
  }
  new ResizeObserver(() => serie && dibujar(1)).observe(centro);

  return {
    panel,
    centro,
    titulo: 'Hora pico',
    activar() { if (!serie) $('#h-form').requestSubmit(); else dibujar(1); },
    simular() { $('#h-form').requestSubmit(); },
    desactivar() {},
  };
}
