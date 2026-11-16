/* Mapa esquemático de la red (dueño: Miguel).
 *
 * Los CSV no traen coordenadas: la posición de cada estación se calcula del
 * propio grafo con un algoritmo de fuerzas (d3-force): las conexiones atraen,
 * las estaciones se repelen. Lo que se dibuja ES la estructura del motor:
 * nodos = estaciones, aristas = paradas consecutivas de alguna ruta.
 *
 * Capas: SVG para la red (nítida, accesible, clic) y Canvas para la flota
 * (cientos de buses a 60 fps). El bus articulado del viaje va en SVG.
 */

const NS = 'http://www.w3.org/2000/svg';
const COLORES = { A: '#60a5fa', B: '#34d399', C: '#f472b6', D: '#a78bfa', E: '#fb923c', F: '#facc15', G: '#2dd4bf', H: '#f87171', J: '#c084fc', K: '#4ade80', L: '#38bdf8', M: '#fda4af' };
export const colorRuta = (r) => COLORES[r && /^[A-Z]/.test(r) ? r[0] : ''] || '#93c5fd';
const el = (tag, attrs = {}, padre) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (padre) padre.appendChild(e); return e; };
const REDUCIDO = matchMedia('(prefers-reduced-motion: reduce)').matches;

export class Mapa {
  constructor(escenario, { alSeleccionar } = {}) {
    this.escenario = escenario;
    this.alSeleccionar = alSeleccionar;
    this.svg = el('svg', { role: 'img', 'aria-label': 'Red esquemática de TransMilenio. Para recorrer las estaciones con teclado, usa el botón Ver como lista.' });
    this.svg.innerHTML = `<defs>
      <filter id="brillo" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      <filter id="brillo-bus" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      <pattern id="trama-cerrada" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="4" height="4" fill="#0b1322"/><line x1="0" y1="0" x2="0" y2="4" stroke="#64748b" stroke-width="1.6"/></pattern>
    </defs>`;
    this.mundo = el('g', {}, this.svg);
    this.gAristas = el('g', {}, this.mundo);
    this.gTraza = el('g', { class: 'traza' }, this.mundo);
    this.gResalte = el('g', {}, this.mundo);
    this.gNodos = el('g', {}, this.mundo);
    this.gEtiquetas = el('g', { class: 'etiquetas' }, this.mundo);
    this.gBus = el('g', { filter: 'url(#brillo-bus)' }, this.mundo);
    this.canvas = document.createElement('canvas');
    this.canvas.setAttribute('aria-hidden', 'true');
    this.tip = document.createElement('div');
    this.tip.className = 'tip';
    this.tip.hidden = true;
    escenario.append(this.svg, this.canvas, this.tip);
    this.ctx = this.canvas.getContext('2d');
    this.zt = d3.zoomIdentity;
    this.flota = [];
    this.pulsoMax = 1;
    this.camino = null;
    new ResizeObserver(() => this._medir()).observe(escenario);
  }

  /* ------------------------------------------------------------ disposición */

  cargar(red) {
    const r = this.escenario.getBoundingClientRect();
    this.W = 1000;
    this.H = r.width > 0 ? Math.round(Math.max(560, Math.min(1100, 1000 * r.height / r.width))) : 700;
    this.svg.setAttribute('viewBox', `0 0 ${this.W} ${this.H}`);
    this.nodos = red.estaciones.map((e) => ({ id: e.n, ...e }));
    this.porNombre = new Map(this.nodos.map((n) => [n.id, n]));
    const aristas = this._aristas(red.rutas);
    const sim = d3.forceSimulation(this.nodos)
      .force('link', d3.forceLink(aristas).id((d) => d.id).distance((l) => 16 + 10 / Math.sqrt(l.rutas)).strength(0.8))
      .force('charge', d3.forceManyBody().strength(-95).distanceMax(320))
      .force('collide', d3.forceCollide((d) => 5 + Math.sqrt(d.rutas) * 1.3))
      .force('x', d3.forceX().strength(0.04))
      .force('y', d3.forceY().strength(0.06))
      .stop();
    for (let i = 0; i < 600; i++) sim.tick();
    const xs = this.nodos.map((n) => n.x), ys = this.nodos.map((n) => n.y);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const m = 40, k = Math.min((this.W - 2 * m) / (x1 - x0 || 1), (this.H - 2 * m) / (y1 - y0 || 1));
    const ox = (this.W - k * (x1 - x0)) / 2, oy = (this.H - k * (y1 - y0)) / 2;
    this.nodos.forEach((n) => { n.x = ox + (n.x - x0) * k; n.y = oy + (n.y - y0) * k; });
    this.posFuerza = this.nodos.map((n) => ({ x: n.x, y: n.y }));
    this.posPlano = null;
    this.modoPlano = false;
    this._dibujar(red);
    this._zoom();
    this._medir();
  }

  _aristas(rutas) {
    const mapa = new Map();
    for (const { r, p } of rutas) {
      for (let i = 1; i < p.length; i++) {
        const a = p[i - 1], b = p[i];
        const clave = a < b ? a + '|' + b : b + '|' + a;
        if (!mapa.has(clave)) mapa.set(clave, { source: a < b ? a : b, target: a < b ? b : a, rutas: 0, lista: [] });
        const e = mapa.get(clave);
        e.rutas++;
        e.lista.push(r);
      }
    }
    return [...mapa.values()];
  }

  /** Redibuja aristas y estados (tras editar rutas o cerrar estaciones) sin mover estaciones. */
  actualizar(red) {
    red.estaciones.forEach((e) => Object.assign(this.porNombre.get(e.n), e));
    this._dibujar(red);
    if (this.resalte) this.resaltar(this.resalte.tramos, this.resalte.opciones);
  }

  _dibujar(red) {
    this.aristas = this._aristas(red.rutas).map((a) => ({ ...a, s: this.porNombre.get(a.source), t: this.porNombre.get(a.target) }));
    this.porArista = new Map(this.aristas.map((a) => [a.source + '|' + a.target, a]));
    this.gAristas.textContent = '';
    for (const a of this.aristas) {
      a.linea = el('path', { d: this._d([a.s, a.t]), fill: 'none', 'stroke-linejoin': 'round', 'stroke-width': (0.6 + Math.sqrt(a.rutas) * 0.55).toFixed(2), 'stroke-linecap': 'round', class: 'arista' }, this.gAristas);
    }
    this.aplicarPulso(this.ultimoPulso || []);
    this.gNodos.textContent = '';
    this.gEtiquetas.textContent = '';
    for (const n of this.nodos) {
      const rad = 2.2 + Math.sqrt(n.rutas) * 0.7;
      n.rad = rad;
      // Sin tabindex: 147 paradas de tabulador harían imposible navegar con teclado.
      // Quien usa teclado o lector de pantalla tiene la vista en lista (botón ☰).
      const g = el('g', { class: 'nodo' + (n.abierta ? '' : ' cerrada') }, this.gNodos);
      n.anillo = n.rutas >= 20 ? el('circle', { cx: n.x, cy: n.y, r: rad + 2.6, class: 'anillo' }, g) : null;
      n.circulo = el('circle', { cx: n.x, cy: n.y, r: rad, class: 'punto' }, g);
      g.addEventListener('mouseenter', () => this._mostrarTip(n));
      g.addEventListener('mouseleave', () => { this.tip.hidden = true; });
      g.addEventListener('focus', () => this._mostrarTip(n));
      g.addEventListener('blur', () => { this.tip.hidden = true; });
      g.addEventListener('click', () => { this._mostrarTip(n); this.alSeleccionar && this.alSeleccionar(n.id); });
      n.grupo = g;
      n.etiqueta = el('text', { x: n.x + rad + 3.5, y: n.y + 3, class: 'etiqueta' + (n.rutas >= 20 ? ' mayor' : '') }, this.gEtiquetas);
      n.etiqueta.textContent = n.id;
    }
  }

  _mostrarTip(n) {
    const ctm = this.svg.getScreenCTM();
    if (!ctm) return;
    const r = this.escenario.getBoundingClientRect();
    const p = new DOMPoint(this.zt.applyX(n.x), this.zt.applyY(n.y)).matrixTransform(ctm);
    this.tip.innerHTML = `<b>${n.id}</b> <span>${n.abierta ? '' : 'CERRADA · '}${n.buses.toLocaleString('es-CO')} buses/día · ${n.rutas} rutas</span>`;
    this.tip.style.left = p.x - r.left + 'px';
    this.tip.style.top = p.y - r.top + 'px';
    this.tip.hidden = false;
  }

  /* ------------------------------------------------------------ plano de metro */

  /** Disposición "plano de metro": cada conexión se acerca a 0°, 45° o 90° y todas
   * tienden al mismo largo, como en los planos de metro. Es una relajación
   * iterativa sobre la disposición por fuerzas (solo presentación). */
  _calcularPlano() {
    const n = this.nodos.length;
    const P0 = this.posFuerza, P = P0.map((p) => ({ x: p.x, y: p.y }));
    const idx = new Map(this.nodos.map((nd, i) => [nd.id, i]));
    const E = this.aristas.map((a) => [idx.get(a.source), idx.get(a.target)]);
    const grado = new Array(n).fill(0);
    E.forEach(([i, j]) => { grado[i]++; grado[j]++; });
    const largos = E.map(([i, j]) => Math.hypot(P[j].x - P[i].x, P[j].y - P[i].y)).sort((a, b) => a - b);
    const L = largos[Math.floor(largos.length / 2)];
    const PASO = Math.PI / 4, MIN = L * 0.55, TOPE = L * 0.25, ITER = 500;
    for (let it = 0; it < ITER; it++) {
      const k = it < ITER * 0.6 ? 0.5 : 0.9;
      const F = P.map(() => ({ x: 0, y: 0 }));
      // cada conexión empuja hacia el múltiplo de 45° más cercano y hacia un largo parejo;
      // se divide por el grado para que las estaciones con muchas conexiones no "exploten"
      for (const [i, j] of E) {
        const dx = P[j].x - P[i].x, dy = P[j].y - P[i].y, len = Math.hypot(dx, dy) || 0.01;
        const ang = Math.round(Math.atan2(dy, dx) / PASO) * PASO, l2 = len * 0.7 + L * 0.3;
        const ex = (Math.cos(ang) * l2 - dx) * 0.5, ey = (Math.sin(ang) * l2 - dy) * 0.5;
        F[i].x -= ex / grado[i]; F[i].y -= ey / grado[i]; F[j].x += ex / grado[j]; F[j].y += ey / grado[j];
      }
      for (let i = 0; i < n; i++) {
        F[i].x = F[i].x * k + (P0[i].x - P[i].x) * 0.01;   // ancla: conserva la forma general
        F[i].y = F[i].y * k + (P0[i].y - P[i].y) * 0.01;
      }
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        const dx = P[j].x - P[i].x, dy = P[j].y - P[i].y, d = Math.hypot(dx, dy) || 0.01;
        if (d < MIN) { const f = ((MIN - d) / d) * 0.2; F[i].x -= dx * f; F[i].y -= dy * f; F[j].x += dx * f; F[j].y += dy * f; }
      }
      for (let i = 0; i < n; i++) {
        const m = Math.hypot(F[i].x, F[i].y), s = m > TOPE ? TOPE / m : 1;
        P[i].x += F[i].x * s; P[i].y += F[i].y * s;
      }
    }
    // rejilla: alinea estaciones vecinas en filas y columnas
    const R = L / 4;
    P.forEach((p) => { p.x = Math.round(p.x / R) * R; p.y = Math.round(p.y / R) * R; });
    // encajar en el mismo marco que la disposición original
    const xs = P.map((p) => p.x), ys = P.map((p) => p.y);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const m = 40, k = Math.min((this.W - 2 * m) / (x1 - x0 || 1), (this.H - 2 * m) / (y1 - y0 || 1));
    const ox = (this.W - k * (x1 - x0)) / 2, oy = (this.H - k * (y1 - y0)) / 2;
    return P.map((p) => ({ x: ox + (p.x - x0) * k, y: oy + (p.y - y0) * k }));
  }

  /** Cambia entre la disposición por fuerzas y el plano de metro, con una transición animada. */
  alternarPlano() {
    if (!this.posPlano) this.posPlano = this._calcularPlano();
    this.modoPlano = !this.modoPlano;
    const desde = this.nodos.map((nd) => ({ x: nd.x, y: nd.y }));
    const codoDesde = this.codo || 0, codoHacia = this.modoPlano ? 1 : 0;
    const hacia = this.modoPlano ? this.posPlano : this.posFuerza;
    const resalte = this.resalte;
    this.gResalte.style.opacity = 0;
    this.gBus.style.opacity = 0;
    this.svg.classList.toggle('plano', this.modoPlano);
    const fin = () => {
      this.gResalte.style.opacity = '';
      this.gBus.style.opacity = '';
      if (resalte) this.resaltar(resalte.tramos, resalte.opciones);
    };
    // sin animación si el usuario pidió menos movimiento o la pestaña está en segundo plano
    if (REDUCIDO || document.hidden) { this.nodos.forEach((nd, i) => { nd.x = hacia[i].x; nd.y = hacia[i].y; }); this.codo = codoHacia; this._reposicionar(); fin(); return this.modoPlano; }
    const t0 = performance.now(), DUR = 1400, yo = (this._transicion = (this._transicion || 0) + 1);
    let terminada = false;
    const aplicar = (e) => {
      this.nodos.forEach((nd, i) => { nd.x = desde[i].x + (hacia[i].x - desde[i].x) * e; nd.y = desde[i].y + (hacia[i].y - desde[i].y) * e; });
      this.codo = codoDesde + (codoHacia - codoDesde) * e;
      this._reposicionar();
    };
    const terminar = () => { if (terminada || yo !== this._transicion) return; terminada = true; aplicar(1); fin(); };
    const paso = (t) => {
      if (terminada || yo !== this._transicion) return;
      const u = Math.min(1, (t - t0) / DUR), e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
      if (u < 1) { aplicar(e); requestAnimationFrame(paso); } else terminar();
    };
    requestAnimationFrame(paso);
    setTimeout(terminar, DUR + 300);   // respaldo: si el navegador no dibuja cuadros, igual llega al final
    return this.modoPlano;
  }

  _reposicionar() {
    for (const a of this.aristas) {
      a.linea.setAttribute('d', this._d([a.s, a.t]));
    }
    for (const nd of this.nodos) {
      nd.circulo.setAttribute('cx', nd.x); nd.circulo.setAttribute('cy', nd.y);
      if (nd.anillo) { nd.anillo.setAttribute('cx', nd.x); nd.anillo.setAttribute('cy', nd.y); }
      nd.etiqueta.setAttribute('x', nd.x + nd.rad + 3.5); nd.etiqueta.setAttribute('y', nd.y + 3);
    }
  }

  /* ------------------------------------------------------------ geometría de las conexiones */

  /** Punto de quiebre de una conexión en el plano de metro: un tramo diagonal (45°) y
   * uno recto (0° o 90°). Con codo = 0 queda en la mitad de la recta (sin quiebre). */
  _quiebre(a, b) {
    const e = this.codo || 0;
    if (e <= 0) return null;
    const dx = b.x - a.x, dy = b.y - a.y, m = Math.min(Math.abs(dx), Math.abs(dy));
    if (m < 0.5 || Math.abs(Math.abs(dx) - Math.abs(dy)) < 0.5) return null;   // ya es recta o diagonal
    const cx = a.x + Math.sign(dx) * m, cy = a.y + Math.sign(dy) * m;
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    return { x: mx + (cx - mx) * e, y: my + (cy - my) * e };
  }

  /** Puntos (estaciones + quiebres) para recorrer una secuencia de estaciones. */
  _expandir(ps) {
    const out = [];
    ps.forEach((p, i) => {
      if (i) { const q = this._quiebre(ps[i - 1], p); if (q) out.push(q); }
      out.push(p);
    });
    return out;
  }

  _d(ps) {
    return 'M' + this._expandir(ps).map((p) => p.x.toFixed(1) + ',' + p.y.toFixed(1)).join('L');
  }

  /* ------------------------------------------------------------ zoom */

  _zoom() {
    const svg = d3.select(this.svg);
    this.zoom = d3.zoom().scaleExtent([0.7, 10]).on('zoom', (e) => {
      this.zt = e.transform;
      this.mundo.setAttribute('transform', this.zt);
      this.svg.dataset.cerca = this.zt.k > 2.2 ? 'si' : 'no';
      this.tip.hidden = true;
    });
    svg.call(this.zoom).on('dblclick.zoom', null);
  }

  acercar(f) { d3.select(this.svg).transition().duration(250).call(this.zoom.scaleBy, f); }
  ajustar() { d3.select(this.svg).transition().duration(350).call(this.zoom.transform, d3.zoomIdentity); }

  enfocar(nombres) {
    const ps = nombres.map((n) => this.porNombre.get(n)).filter(Boolean);
    if (!ps.length) return;
    const xs = ps.map((p) => p.x), ys = ps.map((p) => p.y);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const k = Math.max(1, Math.min(4, 0.75 * Math.min(this.W / (x1 - x0 + 60), this.H / (y1 - y0 + 60))));
    const t = d3.zoomIdentity.translate(this.W / 2, this.H / 2).scale(k).translate(-(x0 + x1) / 2, -(y0 + y1) / 2);
    d3.select(this.svg).transition().duration(REDUCIDO ? 0 : 700).call(this.zoom.transform, t);
  }

  /* ------------------------------------------------------------ pulso y flota */

  /** Brillo de cada tramo según buses programados en una hora (dato Programado). */
  aplicarPulso(pulso) {
    this.ultimoPulso = pulso;
    const conteo = new Map(pulso.map(([a, b, c]) => [a + '|' + b, c]));
    const max = Math.max(1, ...conteo.values());
    for (const a of this.aristas || []) {
      const c = conteo.get(a.source + '|' + a.target) || 0;
      a.linea.style.strokeOpacity = (0.14 + 0.62 * Math.sqrt(c / max)).toFixed(3);
    }
  }

  ponerFlota(flota, minuto) {
    this.flota = flota;
    this.minutoFlota = minuto;
  }

  _medir() {
    const r = this.escenario.getBoundingClientRect();
    const dpr = Math.min(2, devicePixelRatio || 1);
    this.canvas.width = Math.round(r.width * dpr);
    this.canvas.height = Math.round(r.height * dpr);
    const k = Math.min(r.width / (this.W || 1000), r.height / (this.H || 700));
    this.vista = { k, ox: (r.width - k * (this.W || 1000)) / 2, oy: (r.height - k * (this.H || 700)) / 2, dpr };
  }

  /** Se llama en cada fotograma con el minuto simulado (con decimales). */
  dibujarFlota(minuto) {
    const { k, ox, oy, dpr } = this.vista || { k: 1, ox: 0, oy: 0, dpr: 1 };
    const ctx = this.ctx;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!this.flota.length || !this.porNombre) return;
    ctx.setTransform(dpr * k * this.zt.k, 0, 0, dpr * k * this.zt.k, dpr * (ox + k * this.zt.x), dpr * (oy + k * this.zt.y));
    const avance = REDUCIDO ? 0 : minuto - this.minutoFlota;
    ctx.fillStyle = '#d7262e';
    ctx.globalAlpha = this.camino ? 0.35 : 0.85;
    for (const [a, b, f, d] of this.flota) {
      const s = this.porNombre.get(a), t = this.porNombre.get(b);
      if (!s || !t) continue;
      const u = Math.min(1, f + avance / d);
      let a = s, b = t, v = u;
      const q = this._quiebre(s, t);
      if (q) {
        const l1 = Math.hypot(q.x - s.x, q.y - s.y), l2 = Math.hypot(t.x - q.x, t.y - q.y), r = u * (l1 + l2);
        if (r <= l1) { b = q; v = l1 ? r / l1 : 0; } else { a = q; v = l2 ? (r - l1) / l2 : 0; }
      }
      const x = a.x + (b.x - a.x) * v, y = a.y + (b.y - a.y) * v;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(Math.atan2(b.y - a.y, b.x - a.x));
      ctx.fillRect(-2.6, -1, 5.2, 2);
      ctx.restore();
    }
    ctx.globalAlpha = 1;
  }

  /* ------------------------------------------------------------ resaltes */

  /** tramos: [{ruta, paradas:[...]}]; opciones: {bus: true} anima un articulado. */
  resaltar(tramos, opciones = {}) {
    this.resalte = { tramos, opciones };
    this.gResalte.textContent = '';
    this.gBus.textContent = '';
    this.svg.classList.add('atenuado');
    const marcados = new Set();
    const puntos = [];
    tramos.forEach((t, i) => {
      const ps = t.paradas.map((p) => this.porNombre.get(p)).filter(Boolean);
      t.paradas.forEach((p) => marcados.add(p));
      if (ps.length < 2) return;
      const d = this._d(ps);
      const color = opciones.color || (tramos.length > 1 ? colorRuta(t.ruta) : '#22d3ee');
      el('path', { d, class: 'resalte-halo', stroke: color }, this.gResalte);
      const linea = el('path', { d, class: 'resalte-linea', stroke: color, filter: 'url(#brillo)' }, this.gResalte);
      if (!REDUCIDO) {
        const L = linea.getTotalLength();
        linea.animate([{ strokeDasharray: L, strokeDashoffset: L }, { strokeDasharray: L, strokeDashoffset: 0 }], { duration: 800, delay: i * 500, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'backwards' });
      }
      (i === 0 ? ps : ps.slice(1)).forEach((p) => puntos.push(p));
    });
    for (const n of this.nodos) {
      const on = marcados.has(n.id);
      n.grupo.classList.toggle('marcado', on);
      n.etiqueta.classList.toggle('marcada', on);
    }
    if (tramos.length) {
      const primero = tramos[0].paradas[0], ultimo = tramos[tramos.length - 1].paradas.at(-1);
      this._marca(primero, 'origen');
      this._marca(ultimo, 'destino');
      for (let i = 1; i < tramos.length; i++) this._marca(tramos[i].paradas[0], 'transbordo');
    }
    this.camino = opciones.bus && puntos.length > 1 ? this._prepararBus(puntos, tramos) : null;
  }

  _marca(nombre, tipo) {
    const n = this.porNombre.get(nombre);
    if (!n) return;
    el('circle', { cx: n.x, cy: n.y, r: n.rad + 3.2, class: 'marca ' + tipo }, this.gResalte);
  }

  limpiar() {
    if (this.trazaActiva) { this.trazaActiva.cancelar(); this.trazaActiva = null; }
    this.resalte = null;
    this.camino = null;
    this.gResalte.textContent = '';
    this.gBus.textContent = '';
    this.svg.classList.remove('atenuado');
    for (const n of this.nodos || []) { n.grupo.classList.remove('marcado'); n.etiqueta.classList.remove('marcada'); }
  }

  /* ------------------------------------------------------------ impacto de un cierre */

  /** Onda que sale de la estación cerrada, las rutas que pasaban por ella y las estaciones más afectadas. */
  ondaCierre(nombre, rutas, afectadas) {
    this.limpiar();
    this.svg.classList.add('atenuado');
    const n = this.porNombre.get(nombre);
    if (!n) return;
    rutas.forEach((r, i) => {
      const ps = r.paradas.map((p) => this.porNombre.get(p)).filter(Boolean);
      if (ps.length < 2) return;
      const linea = el('path', { d: this._d(ps), class: 'onda-ruta' }, this.gResalte);
      linea.style.animationDelay = (i * 25) + 'ms';
    });
    for (let i = 0; i < 4; i++) {
      const c = el('circle', { cx: n.x, cy: n.y, r: 8, class: 'onda' }, this.gResalte);
      c.style.animationDelay = (i * 0.45) + 's';
    }
    afectadas.forEach(([nom, cuantos], i) => {
      const p = this.porNombre.get(nom);
      if (!p) return;
      const c = el('circle', { cx: p.x, cy: p.y, r: 4 + Math.sqrt(cuantos), class: 'afectada' }, this.gResalte);
      c.style.animationDelay = (0.8 + i * 0.15) + 's';
      const t = el('text', { x: p.x + 8, y: p.y - 6, class: 'afectada-txt' }, this.gResalte);
      t.textContent = `${nom} · −${cuantos}`;
      t.style.animationDelay = (0.8 + i * 0.15) + 's';
    });
    el('circle', { cx: n.x, cy: n.y, r: n.rad + 3, class: 'cerrada-x' }, this.gResalte);
    const x = el('path', { d: `M${n.x - 4},${n.y - 4}L${n.x + 4},${n.y + 4}M${n.x + 4},${n.y - 4}L${n.x - 4},${n.y + 4}`, class: 'cerrada-x' }, this.gResalte);
    x.style.strokeWidth = 2;
    this.enfocar([nombre, ...afectadas.map((a) => a[0])]);
  }

  /* ------------------------------------------------------------ rayos X de R5 */

  /** Anima la búsqueda real de R5: el frente del origen avanza por sus rutas,
   * el del destino retrocede, y donde se tocan hay un candidato a transbordo.
   * alPaso recibe contadores para el panel. Devuelve una promesa y un cancelar. */
  animarTraza(traza, origen, destino, { alPaso, lento = false } = {}) {
    this.limpiar();
    this.gTraza.textContent = '';
    this.svg.classList.add('atenuado', 'rayos-x');
    const paso = (REDUCIDO ? 0 : lento ? 180 : 85);
    let cancelado = false;
    const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
    const pos = (n) => this.porNombre.get(n);
    const marcadas = new Set();
    const punto = (n, clase, r = 2.6) => { const p = pos(n); if (p) el('circle', { cx: p.x, cy: p.y, r, class: clase }, this.gTraza); };
    const segmento = (a, b, clase) => { const p = pos(a), q = pos(b); if (p && q) el('path', { d: this._d([p, q]), fill: 'none', class: clase }, this.gTraza); };
    const contadores = { fase: 'ida', rutasIda: 0, alcanzadas: 0, rutasVuelta: 0, revisadas: 0, encuentros: 0, mejor: null };
    const avisar = () => alPaso && alPaso({ ...contadores });
    // Mismo criterio que el motor: menos paradas, directo antes que transbordo, luego nombres.
    const clave = (m) => [m.paradas, m.directo ? 0 : 1, m.directo ? m.ruta : m.ruta1, m.directo ? '' : m.ruta2, m.directo ? '' : m.estacion];
    const menor = (a, b) => { for (let i = 0; i < a.length; i++) { if (a[i] < b[i]) return true; if (a[i] > b[i]) return false; } return false; };
    const proponer = (m) => { if (!contadores.mejor || menor(clave(m), clave(contadores.mejor))) { contadores.mejor = m; return true; } return false; };

    // encuentros indexados por (ruta2, estación) para dispararlos al pasar por ahí
    const porEncuentro = new Map();
    traza.encuentros.forEach((e) => porEncuentro.set(e.ruta2 + '|' + e.estacion, e));

    const correr = async () => {
      punto(origen, 'tx-origen', 5);
      punto(destino, 'tx-destino', 5);
      // Fase 1: todas las rutas del origen avanzan a la vez, parada por parada
      contadores.rutasIda = traza.ida.length;
      avisar();
      const largoIda = Math.max(0, ...traza.ida.map((r) => r.visitadas.length));
      for (let k = 0; k < largoIda && !cancelado; k++) {
        for (const r of traza.ida) {
          const v = r.visitadas[k];
          if (!v) continue;
          segmento(k ? r.visitadas[k - 1][0] : origen, v[0], 'tx-ida');
          if (!marcadas.has(v[0])) { marcadas.add(v[0]); punto(v[0], 'tx-alcanzada'); contadores.alcanzadas++; }
          if (v[0] === destino && proponer({ paradas: v[1], directo: true, ruta: r.ruta })) punto(destino, 'tx-directo', 9);
        }
        avisar();
        await dormir(paso);
      }
      if (cancelado) return;
      await dormir(paso * 3);
      // Fase 2: las rutas del destino retroceden; cada estación marcada es un encuentro
      contadores.fase = 'vuelta';
      contadores.rutasVuelta = traza.vuelta.length;
      avisar();
      const largoVuelta = Math.max(0, ...traza.vuelta.map((r) => r.visitadas.length));
      for (let k = 0; k < largoVuelta && !cancelado; k++) {
        for (const r of traza.vuelta) {
          const v = r.visitadas[k];
          if (!v) continue;
          segmento(k ? r.visitadas[k - 1][0] : destino, v[0], 'tx-vuelta');
          contadores.revisadas++;
          const e = porEncuentro.get(r.ruta + '|' + v[0]);
          if (e) {
            contadores.encuentros++;
            const mejora = proponer({ paradas: e.paradas, directo: false, estacion: e.estacion, ruta1: e.ruta1, ruta2: e.ruta2 });
            punto(v[0], mejora ? 'tx-mejora' : 'tx-encuentro', mejora ? 7 : 4);
          }
        }
        avisar();
        await dormir(paso);
      }
      if (cancelado) return;
      contadores.fase = 'fin';
      avisar();
      await dormir(paso * 4);
      if (cancelado) return;
      this.svg.classList.remove('rayos-x');
      this.gTraza.classList.add('apagandose');
      if (traza.resultado) this.resaltar(traza.resultado, { bus: true });
      setTimeout(() => { this.gTraza.textContent = ''; this.gTraza.classList.remove('apagandose'); }, 1200);
    };
    const promesa = correr();
    this.trazaActiva = { promesa, cancelar: () => { cancelado = true; this.gTraza.textContent = ''; this.svg.classList.remove('rayos-x'); } };
    return this.trazaActiva;
  }

  /* ------------------------------------------------------------ articulado */

  _prepararBus(estaciones, tramos) {
    const pts = this._expandir(estaciones);
    const segs = [];
    let total = 0;
    const enEstacion = new Map();          // estación -> distancia recorrida al llegar
    enEstacion.set(pts[0], 0);
    for (let i = 1; i < pts.length; i++) {
      const d = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
      segs.push(d);
      total += d;
      enEstacion.set(pts[i], total);
    }
    const pausas = [];
    for (let i = 1; i < tramos.length; i++) {
      const n = this.porNombre.get(tramos[i].paradas[0]);
      if (enEstacion.has(n)) pausas.push(enEstacion.get(n));
    }
    const SEC = 8.5, GAP = 1.3, ANCHO = 4.2;
    const secciones = [0, 1, 2].map((i) => {
      const g = el('g', {}, this.gBus);
      el('rect', { x: -SEC / 2, y: -ANCHO / 2, width: SEC, height: ANCHO, rx: 1.4, class: 'bus-cuerpo' }, g);
      el('rect', { x: -SEC / 2 + 1.2, y: -0.55, width: SEC - 2.4, height: 1.1, rx: 0.5, class: 'bus-techo' }, g);
      if (i === 0) el('rect', { x: SEC / 2 - 1.3, y: -ANCHO / 2 + 0.5, width: 0.9, height: ANCHO - 1, rx: 0.4, class: 'bus-vidrio' }, g);
      return g;
    });
    const fuelles = [0, 1].map(() => el('circle', { r: 1.25, class: 'bus-fuelle' }, this.gBus));
    const camino = { pts, segs, total, pausas, SEC, GAP, secciones, fuelles, d: 3 * SEC + 2 * GAP, espera: 0, siguientePausa: 0 };
    this._ubicarBus(camino);
    return camino;
  }

  _punto(c, d) {
    d = Math.max(0, Math.min(c.total, d));
    for (let i = 0; i < c.segs.length; i++) {
      if (d <= c.segs[i] || i === c.segs.length - 1) { const u = c.segs[i] ? d / c.segs[i] : 0; const a = c.pts[i], b = c.pts[i + 1]; return { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u }; }
      d -= c.segs[i];
    }
    return c.pts[0];
  }

  _ubicarBus(c) {
    let d = c.d;
    c.secciones.forEach((g) => {
      const f = this._punto(c, d), b = this._punto(c, d - c.SEC);
      const ang = Math.atan2(f.y - b.y, f.x - b.x) * 180 / Math.PI;
      g.setAttribute('transform', `translate(${((f.x + b.x) / 2).toFixed(2)},${((f.y + b.y) / 2).toFixed(2)}) rotate(${ang.toFixed(1)})`);
      d -= c.SEC + c.GAP;
    });
    c.fuelles.forEach((j, i) => { const p = this._punto(c, c.d - (i + 1) * c.SEC - (i + 0.5) * c.GAP); j.setAttribute('cx', p.x); j.setAttribute('cy', p.y); });
  }

  /** Avanza el articulado; se llama en cada fotograma con dt en ms. */
  animarBus(dt, ahora) {
    const c = this.camino;
    if (!c || REDUCIDO) return;
    if (ahora < c.espera) return;
    c.d += dt * 0.05;
    if (c.siguientePausa < c.pausas.length && c.d >= c.pausas[c.siguientePausa]) {
      c.d = c.pausas[c.siguientePausa];
      c.siguientePausa++;
      c.espera = ahora + 900;
    }
    if (c.d >= c.total) {
      c.d = c.total;
      this._ubicarBus(c);
      c.d = 3 * c.SEC + 2 * c.GAP;
      c.siguientePausa = 0;
      c.espera = ahora + 1500;
      return;
    }
    this._ubicarBus(c);
  }
}
