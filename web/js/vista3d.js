/* Vista 3D "cámara de cabina" (dueño: Miguel).
 *
 * El articulado queda en primer plano, visto desde atrás y un poco desde
 * arriba, y el mundo pasa a su alrededor: la cinta de la ruta, las estaciones
 * como plataformas iluminadas y la red completa en el suelo.
 *
 * Es honesta con los datos: el suelo es la RED ESQUEMÁTICA (la misma
 * disposición del mapa 2D, no la geografía de Bogotá), y el movimiento es
 * SIMULADO. El viaje en sí (rutas, paradas, transbordo) es la respuesta de R5.
 *
 * Three.js se descarga solo cuando alguien abre esta vista.
 */

import { colorRuta } from './mapa.js';
import { esc, toast } from './ui.js';

const URL_THREE = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
const ESCALA = 4;            // 1 unidad del mapa 2D = 4 unidades 3D
const ENTRADA = 40;          // tramo extra antes del origen y después del destino
const SEC = 7, HUECO = 0.9;  // largo de cada vagón y del fuelle
const REDUCIDO = matchMedia('(prefers-reduced-motion: reduce)').matches;
let THREE = null;

export function webglDisponible() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch (e) { return false; }
}

export async function abrirVista3D({ mapa, tramos }) {
  if (!webglDisponible()) { toast('Este dispositivo no permite gráficos 3D (WebGL). Sigue disponible el mapa 2D.', 'error'); return; }
  const capa = document.createElement('div');
  capa.className = 'vista3d';
  capa.setAttribute('role', 'dialog');
  capa.setAttribute('aria-label', 'Recorrido en 3D');
  capa.innerHTML = '<div class="v3-cargando">Preparando la vista 3D…</div>';
  document.body.appendChild(capa);
  try {
    THREE = THREE || await import(URL_THREE);
  } catch (e) {
    capa.remove();
    toast('No se pudo descargar el motor 3D. Revisa la conexión.', 'error');
    return;
  }
  capa.textContent = '';
  new Viaje3D(capa, mapa, tramos);
}

/* ------------------------------------------------------------------ utilidades */

function textura(ancho, alto, dibujar) {
  const c = document.createElement('canvas');
  c.width = ancho; c.height = alto;
  dibujar(c.getContext('2d'), ancho, alto);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

function etiqueta(texto, { tamano = 1, color = '#e6eef8', fondo = 'rgba(6,10,19,.78)', borde = null } = {}) {
  const px = 44, pad = 26;
  const medir = document.createElement('canvas').getContext('2d');
  medir.font = `600 ${px}px "Space Grotesk", sans-serif`;
  const w = Math.ceil(medir.measureText(texto).width) + pad * 2, h = px + pad * 1.4;
  const tex = textura(w, h, (g) => {
    g.fillStyle = fondo;
    const r = 18;
    g.beginPath(); g.roundRect(2, 2, w - 4, h - 4, r); g.fill();
    if (borde) { g.strokeStyle = borde; g.lineWidth = 4; g.stroke(); }
    g.font = `600 ${px}px "Space Grotesk", sans-serif`;
    g.fillStyle = color; g.textBaseline = 'middle';
    g.fillText(texto, pad, h / 2 + 2);
  });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, fog: true }));
  s.scale.set((w / h) * 3.2 * tamano, 3.2 * tamano, 1);
  return s;
}

function halo(color, tamano) {
  const tex = textura(128, 128, (g) => {
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, color); gr.addColorStop(0.35, color + '88'); gr.addColorStop(1, color + '00');
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  s.scale.set(tamano, tamano, 1);
  return s;
}

/* ------------------------------------------------------------------ la vista */

class Viaje3D {
  constructor(capa, mapa, tramos) {
    this.capa = capa;
    this.mapa = mapa;
    this.tramos = tramos;
    this.velocidad = 1;
    this.pausa = false;
    this.voz = false;
    this.cerrado = false;
    this._prepararCamino();
    this._crearEscena();
    this._crearHud();
    this._reiniciar();
    this._alTeclear = (e) => { if (e.key === 'Escape') this.cerrar(); if (e.key === ' ') { e.preventDefault(); this._alternarPausa(); } };
    document.addEventListener('keydown', this._alTeclear);
    this.ultimo = performance.now();
    this.raf = requestAnimationFrame((t) => this._cuadro(t));
  }

  /* ---------------- camino: polilínea de estaciones del viaje */
  _prepararCamino() {
    const nombres = [], tramoDe = [];
    this.tramos.forEach((t, i) => t.paradas.forEach((p, j) => { if (i === 0 || j > 0) { nombres.push(p); tramoDe.push(i); } }));
    const ps = nombres.map((n) => this.mapa.porNombre.get(n));
    const cx = ps.reduce((s, p) => s + p.x, 0) / ps.length, cy = ps.reduce((s, p) => s + p.y, 0) / ps.length;
    this.centro = { cx, cy };
    this.a3d = (n) => new THREE.Vector3((n.x - cx) * ESCALA, 0, (n.y - cy) * ESCALA);
    const v = ps.map((p) => this.a3d(p));
    // tramo de entrada antes del origen y de salida después del destino
    const d0 = v[1].clone().sub(v[0]).normalize(), d1 = v.at(-1).clone().sub(v.at(-2)).normalize();
    this.puntos = [v[0].clone().addScaledVector(d0, -ENTRADA), ...v, v.at(-1).clone().addScaledVector(d1, ENTRADA)];
    this.largos = [];
    this.acum = [0];
    for (let i = 1; i < this.puntos.length; i++) {
      const l = this.puntos[i].distanceTo(this.puntos[i - 1]);
      this.largos.push(l);
      this.acum.push(this.acum[i - 1] + l);
    }
    this.total = this.acum.at(-1);
    this.paradas = nombres.map((n, i) => {
      const esTransbordo = i > 0 && tramoDe[i] !== tramoDe[i - 1];
      return {
        nombre: n, d: this.acum[i + 1], tramo: tramoDe[i] - (esTransbordo ? 1 : 0),
        tipo: i === 0 ? 'origen' : i === nombres.length - 1 ? 'destino' : esTransbordo ? 'transbordo' : 'parada',
        siguienteTramo: tramoDe[i],
        cerrada: this.mapa.porNombre.get(n).abierta === false,
      };
    });
  }

  _en(d) {
    d = Math.max(0, Math.min(this.total, d));
    let i = 0;
    while (i < this.largos.length - 1 && this.acum[i + 1] < d) i++;
    const u = this.largos[i] ? (d - this.acum[i]) / this.largos[i] : 0;
    return this.puntos[i].clone().lerp(this.puntos[i + 1], u);
  }

  /* ---------------- escena */
  _crearEscena() {
    const r = this.capa.getBoundingClientRect();
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1));
    this.renderer.setSize(r.width, r.height);
    this.renderer.setClearColor(0x060a13);
    this.capa.appendChild(this.renderer.domElement);
    this.escena = new THREE.Scene();
    this.escena.fog = new THREE.Fog(0x060a13, 70, 520);
    this.camara = new THREE.PerspectiveCamera(55, r.width / r.height, 0.5, 2000);

    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;
    this.escena.add(new THREE.HemisphereLight(0xb8d4ff, 0x1a2436, 2.2));
    const sol = new THREE.DirectionalLight(0xffffff, 2.4);
    sol.position.set(60, 120, 40);
    this.escena.add(sol);
    // luz de relleno que acompaña a la cámara: el bus nunca queda a contraluz
    this.relleno = new THREE.PointLight(0xfff1e6, 900, 120, 1.6);
    this.escena.add(this.relleno);

    // Suelo con retícula
    const suelo = new THREE.Mesh(new THREE.PlaneGeometry(6000, 6000), new THREE.MeshStandardMaterial({ color: 0x0a1222, roughness: 1 }));
    suelo.rotation.x = -Math.PI / 2;
    suelo.position.y = -0.05;
    this.escena.add(suelo);
    const reticula = new THREE.GridHelper(6000, 300, 0x1b3a5c, 0x12243d);
    reticula.material.transparent = true;
    reticula.material.opacity = 0.55;
    this.escena.add(reticula);

    // La red completa, tenue, en el suelo (misma disposición que el mapa 2D)
    const pos = [];
    for (const a of this.mapa.aristas) {
      const p = this.a3d(a.s), q = this.a3d(a.t);
      pos.push(p.x, 0.02, p.z, q.x, 0.02, q.z);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    this.escena.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x3d6aa8, transparent: true, opacity: 0.45 })));
    const enViaje = new Set(this.paradas.map((p) => p.nombre));
    const geoPoste = new THREE.CylinderGeometry(0.9, 0.9, 2.2, 10);
    const matPoste = new THREE.MeshStandardMaterial({ color: 0x5b7aa6, emissive: 0x1d3557, emissiveIntensity: 0.6 });
    for (const n of this.mapa.nodos) {
      if (enViaje.has(n.id)) continue;
      const m = new THREE.Mesh(geoPoste, matPoste);
      const p = this.a3d(n);
      m.position.set(p.x, 1.1, p.z);
      this.escena.add(m);
    }

    // Cinta de la ruta, con el color de cada tramo
    let inicio = 0;   // índice (en this.paradas) de la primera estación del tramo
    this.tramos.forEach((t, i) => {
      const fin = inicio + t.paradas.length - 1;
      const desde = i === 0 ? 0 : this.acum[inicio + 1];
      const hasta = i === this.tramos.length - 1 ? this.total : this.acum[fin + 1];
      this._cinta(desde, hasta, new THREE.Color(colorRuta(t.ruta)));
      inicio = fin;
    });

    // Estaciones del viaje: plataforma, poste luminoso y nombre
    this.objetosParada = this.paradas.map((p, i) => {
      const pos3 = this._en(p.d);
      const dir = this._en(p.d + 1).sub(this._en(p.d - 1)).normalize();
      const lado = new THREE.Vector3(dir.z, 0, -dir.x);
      const grupo = new THREE.Group();
      const color = p.tipo === 'transbordo' ? '#fbbf24' : p.tipo === 'destino' ? '#e6eef8' : p.cerrada ? '#64748b' : '#22d3ee';
      const plataforma = new THREE.Mesh(new THREE.BoxGeometry(5, 1.1, 22),
        new THREE.MeshStandardMaterial({ color: 0x1a2840, emissive: new THREE.Color(color), emissiveIntensity: 0.18, roughness: 0.6 }));
      plataforma.position.copy(pos3).addScaledVector(lado, 5);
      plataforma.position.y = 0.55;
      plataforma.lookAt(plataforma.position.clone().add(dir));
      grupo.add(plataforma);
      const borde = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.15, 22), new THREE.MeshBasicMaterial({ color: new THREE.Color(color) }));
      borde.position.copy(plataforma.position).addScaledVector(lado, -2.6);
      borde.position.y = 1.15;
      borde.quaternion.copy(plataforma.quaternion);
      grupo.add(borde);
      const poste = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 9, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(color) }));
      poste.position.copy(plataforma.position).addScaledVector(lado, 1.6);
      poste.position.y = 4.5;
      grupo.add(poste);
      const brillo = halo(color, p.tipo === 'parada' ? 9 : 16);
      brillo.position.copy(poste.position); brillo.position.y = 9.2;
      grupo.add(brillo);
      const nombre = etiqueta(p.nombre + (p.cerrada ? ' · cerrada' : ''), { tamano: p.tipo === 'parada' ? 1.1 : 1.5, borde: color });
      nombre.position.copy(poste.position); nombre.position.y = 12.5;
      grupo.add(nombre);
      this.escena.add(grupo);
      return { grupo, brillo, nombre };
    });

    this._crearBus();
    this._alRedimensionar = new ResizeObserver(() => {
      const b = this.capa.getBoundingClientRect();
      this.renderer.setSize(b.width, b.height);
      this.camara.aspect = b.width / b.height;
      this.camara.updateProjectionMatrix();
    });
    this._alRedimensionar.observe(this.capa);
  }

  _cinta(desde, hasta, color) {
    const ancho = 3.4, pasos = [];
    for (let i = 0; i < this.acum.length; i++) if (this.acum[i] > desde && this.acum[i] < hasta) pasos.push(this.acum[i]);
    const ds = [desde, ...pasos, hasta];
    const pos = [], idx = [];
    ds.forEach((d, k) => {
      const p = this._en(d);
      const dir = this._en(Math.min(this.total, d + 0.5)).sub(this._en(Math.max(0, d - 0.5))).normalize();
      const lado = new THREE.Vector3(dir.z, 0, -dir.x).multiplyScalar(ancho / 2);
      pos.push(p.x + lado.x, 0.06, p.z + lado.z, p.x - lado.x, 0.06, p.z - lado.z);
      if (k) { const b = (k - 1) * 2; idx.push(b, b + 1, b + 2, b + 1, b + 3, b + 2); }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.85, side: THREE.DoubleSide }));
    this.escena.add(m);
    // línea central brillante
    const linea = new THREE.Mesh(g.clone(), new THREE.MeshBasicMaterial({ color: color.clone().lerp(new THREE.Color(0xffffff), 0.5), transparent: true, opacity: 0.25, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }));
    linea.scale.set(1, 1, 1);
    linea.position.y = 0.02;
    this.escena.add(linea);
  }

  /* ---------------- el articulado */
  _crearBus() {
    const rojo = new THREE.MeshStandardMaterial({ color: 0xd7262e, emissive: 0x3a0306, roughness: 0.4, metalness: 0.1 });
    const vidrio = new THREE.MeshStandardMaterial({ color: 0x0b1a2b, emissive: 0x6fc3ff, emissiveIntensity: 0.35, roughness: 0.2 });
    const techo = new THREE.MeshStandardMaterial({ color: 0xe9eef5, roughness: 0.6 });
    const oscuro = new THREE.MeshStandardMaterial({ color: 0x1b0507, roughness: 0.9 });
    const llanta = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 1 });
    this.secciones = [0, 1, 2].map((i) => {
      const g = new THREE.Group();
      const cuerpo = new THREE.Mesh(new THREE.BoxGeometry(2.6, 2.4, SEC), rojo);
      cuerpo.position.y = 1.75;
      g.add(cuerpo);
      for (const lado of [-1, 1]) {
        const v = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.9, SEC - 0.8), vidrio);
        v.position.set(lado * 1.31, 2.25, 0);
        g.add(v);
      }
      const t = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.2, SEC - 0.4), techo);
      t.position.y = 3.05;
      g.add(t);
      for (const z of [-SEC / 2 + 1.2, SEC / 2 - 1.2]) for (const lado of [-1, 1]) {
        const w = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.35, 14), llanta);
        w.rotation.z = Math.PI / 2;
        w.position.set(lado * 1.2, 0.5, z);
        g.add(w);
      }
      if (i === 0) {
        const frente = new THREE.Mesh(new THREE.BoxGeometry(2.5, 1.1, 0.05), vidrio);
        frente.position.set(0, 2.2, SEC / 2 + 0.01);
        g.add(frente);
        for (const lado of [-1, 1]) {
          const faro = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.25, 0.05), new THREE.MeshBasicMaterial({ color: 0xfff4d6 }));
          faro.position.set(lado * 0.85, 1.0, SEC / 2 + 0.03);
          g.add(faro);
          const luz = halo('#fff4d6', 2.2);
          luz.position.set(lado * 0.85, 1.0, SEC / 2 + 0.3);
          g.add(luz);
        }
        this.letrero = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.45), new THREE.MeshBasicMaterial({ transparent: true }));
        this.letrero.position.set(0, 2.85, SEC / 2 + 0.03);
        g.add(this.letrero);
      }
      if (i === 1) {
        // puertas del lado izquierdo (el de las plataformas)
        this.puertas = [-1, 1].map((s) => {
          const p = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.9, 0.95), new THREE.MeshStandardMaterial({ color: 0x9aa7b8, emissive: 0x22d3ee, emissiveIntensity: 0 }));
          p.position.set(1.33, 1.55, s * 0.48);
          p.userData.base = s * 0.48;
          p.userData.lado = s;
          g.add(p);
          return p;
        });
      }
      this.escena.add(g);
      return g;
    });
    this.fuelles = [0, 1].map(() => {
      const f = new THREE.Mesh(new THREE.BoxGeometry(2.3, 2.1, HUECO + 0.3), oscuro);
      this.escena.add(f);
      return f;
    });
    this.direccionCamara = new THREE.Vector3(0, 0, 1);
  }

  _ponerLetrero(ruta) {
    const c = colorRuta(ruta);
    this.letrero.material.map && this.letrero.material.map.dispose();
    this.letrero.material.map = textura(512, 104, (g) => {
      g.fillStyle = '#05070c'; g.fillRect(0, 0, 512, 104);
      g.fillStyle = c; g.fillRect(0, 0, 18, 104);
      g.font = '600 64px "JetBrains Mono", monospace';
      g.fillStyle = '#ffb020'; g.textBaseline = 'middle';
      g.fillText(ruta, 40, 56);
    });
    this.letrero.material.needsUpdate = true;
  }

  _ubicarBus(dFrente) {
    let d = dFrente;
    const extremos = [];
    this.secciones.forEach((g) => {
      const f = this._en(d), b = this._en(d - SEC);
      g.position.copy(f).add(b).multiplyScalar(0.5);
      g.lookAt(f.x, 0, f.z);
      extremos.push(b);
      d -= SEC + HUECO;
    });
    this.fuelles.forEach((f, i) => {
      const a = extremos[i], b = this._en(dFrente - (i + 1) * SEC - (i + 1) * HUECO);
      f.position.copy(a).add(b).multiplyScalar(0.5);
      f.position.y = 1.65;
      f.lookAt(a.x, 1.65, a.z);
    });
  }

  /* ---------------- HUD */
  _crearHud() {
    const hud = document.createElement('div');
    hud.className = 'v3-hud';
    hud.innerHTML = `
      <div class="v3-arriba">
        <div class="v3-info"><span class="ruta" id="v3-ruta"></span><div><span class="v3-eti">Próxima estación</span><b id="v3-proxima"></b></div><span class="v3-contador" id="v3-contador"></span></div>
        <div class="v3-botones">
          <button class="control" id="v3-pausa" aria-label="Pausar">❚❚</button>
          <button class="control" id="v3-vel" aria-label="Velocidad">×1</button>
          <button class="control" id="v3-voz" aria-pressed="false" title="Anunciar las estaciones en voz alta">Voz</button>
          <button class="control" id="v3-cerrar" aria-label="Cerrar la vista 3D">✕</button>
        </div>
      </div>
      <div class="v3-aviso" id="v3-aviso" hidden></div>
      <div class="v3-abajo">
        <ol class="v3-progreso" id="v3-progreso">${this.paradas.map((p, i) => `<li class="${p.tipo}" title="${esc(p.nombre)}"><i></i>${p.tipo !== 'parada' ? `<span>${esc(p.nombre)}</span>` : ''}</li>`).join('')}</ol>
        <p class="v3-nota"><span class="chip sim">Simulado</span> Distancias del esquema de la red, no de Bogotá. Viaje calculado por el motor (R5).</p>
      </div>`;
    this.capa.appendChild(hud);
    this.$ = (s) => hud.querySelector(s);
    this.$('#v3-cerrar').addEventListener('click', () => this.cerrar());
    this.$('#v3-pausa').addEventListener('click', () => this._alternarPausa());
    this.$('#v3-vel').addEventListener('click', () => {
      this.velocidad = this.velocidad === 1 ? 2 : this.velocidad === 2 ? 4 : 1;
      this.$('#v3-vel').textContent = '×' + this.velocidad;
    });
    this.$('#v3-voz').addEventListener('click', () => {
      this.voz = !this.voz && 'speechSynthesis' in window;
      this.$('#v3-voz').setAttribute('aria-pressed', this.voz);
      if (this.voz) this._hablar('Próxima estación: ' + this.paradas[this.siguiente]?.nombre);
      else window.speechSynthesis && speechSynthesis.cancel();
    });
    this.$('#v3-cerrar').focus();
  }

  _alternarPausa() {
    this.pausa = !this.pausa;
    this.$('#v3-pausa').textContent = this.pausa ? '▶' : '❚❚';
  }

  _hablar(texto) {
    if (!this.voz || !('speechSynthesis' in window)) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = 'es-CO';
    u.rate = 1.02;
    speechSynthesis.speak(u);
  }

  _aviso(html, ms) {
    const a = this.$('#v3-aviso');
    a.innerHTML = html;
    a.hidden = false;
    clearTimeout(this._tAviso);
    if (ms) this._tAviso = setTimeout(() => { a.hidden = true; }, ms);
  }

  _actualizarHud() {
    const t = this.tramos[this.tramoActual];
    const r = this.$('#v3-ruta');
    r.textContent = t.ruta;
    r.style.setProperty('--rc', colorRuta(t.ruta));
    const sig = this.paradas[this.siguiente];
    this.$('#v3-proxima').textContent = sig ? sig.nombre : '—';
    this.$('#v3-contador').textContent = `Parada ${Math.min(this.siguiente, this.paradas.length - 1)} de ${this.paradas.length - 1}`;
    [...this.$('#v3-progreso').children].forEach((li, i) => {
      li.classList.toggle('hecha', i < this.siguiente);
      li.classList.toggle('actual', i === this.siguiente);
    });
  }

  /* ---------------- movimiento */
  _reiniciar() {
    this.d = ENTRADA;
    this.siguiente = 1;
    this.tramoActual = 0;
    this.esperaHasta = performance.now() + 1200;
    this.puertaObjetivo = 0;
    this.terminado = false;
    this.$('#v3-aviso').hidden = true;
    this._ponerLetrero(this.tramos[0].ruta);
    this._ubicarBus(this.d);
    this._colocarCamara(true);
    this._actualizarHud();
    this._aviso(`Sube en <b>${esc(this.paradas[0].nombre)}</b> · ruta <span class="ruta" style="--rc:${colorRuta(this.tramos[0].ruta)}">${esc(this.tramos[0].ruta)}</span>`, 2200);
    this._hablar('Próxima estación: ' + this.paradas[1].nombre);
  }

  _llegar(p, ahora) {
    this.d = p.d;
    if (p.tipo === 'destino') {
      this.terminado = true;
      this.puertaObjetivo = 1;
      this._aviso(`<b>Llegaste a ${esc(p.nombre)}</b><div class="v3-fin"><button class="boton primario" id="v3-repetir">Repetir</button><button class="boton" id="v3-salir">Cerrar</button></div>`);
      this.$('#v3-repetir').addEventListener('click', () => this._reiniciar());
      this.$('#v3-salir').addEventListener('click', () => this.cerrar());
      this._hablar('Llegaste a ' + p.nombre);
      return;
    }
    if (p.tipo === 'transbordo') {
      const nuevo = this.tramos[p.siguienteTramo];
      this.puertaObjetivo = 1;
      this.esperaHasta = ahora + 3200 / this.velocidad;
      this._aviso(`Transbordo en <b>${esc(p.nombre)}</b> · cambia a <span class="ruta" style="--rc:${colorRuta(nuevo.ruta)}">${esc(nuevo.ruta)}</span>`, 3000);
      this._hablar('Transbordo en ' + p.nombre + '. Cambia a la ruta ' + nuevo.ruta.replace('-', ' guion '));
      setTimeout(() => { if (this.cerrado) return; this.tramoActual = p.siguienteTramo; this._ponerLetrero(nuevo.ruta); this._actualizarHud(); }, 1500 / this.velocidad);
    } else {
      this.esperaHasta = ahora + (p.cerrada ? 0 : 900 / this.velocidad);
      this.puertaObjetivo = p.cerrada ? 0 : 1;
    }
    this.siguiente++;
    this._actualizarHud();
    const proxima = this.paradas[this.siguiente];
    if (proxima) setTimeout(() => !this.cerrado && this._hablar('Próxima estación: ' + proxima.nombre), p.tipo === 'transbordo' ? 3300 / this.velocidad : 900 / this.velocidad);
  }

  _colocarCamara(inmediato) {
    const frente = this._en(this.d), atras = this._en(this.d - 3 * SEC);
    const dir = frente.clone().sub(atras).setY(0).normalize();
    this.direccionCamara.lerp(dir, inmediato ? 1 : 0.035).normalize();
    const centro = this._en(this.d - 1.5 * SEC - HUECO);
    const lado = new THREE.Vector3(this.direccionCamara.z, 0, -this.direccionCamara.x);
    const objetivo = centro.clone().addScaledVector(this.direccionCamara, -24).addScaledVector(lado, -7);
    objetivo.y = 11;
    if (inmediato) this.camara.position.copy(objetivo);
    else this.camara.position.lerp(objetivo, 0.08);
    this.relleno.position.copy(this.camara.position).add(new THREE.Vector3(0, 4, 0));
    const mirar = centro.clone().addScaledVector(this.direccionCamara, 16);
    mirar.y = 2;
    this.camara.lookAt(mirar);
  }

  _cuadro(ahora) {
    if (this.cerrado) return;
    const dt = Math.min(50, ahora - this.ultimo) / 1000;
    this.ultimo = ahora;
    if (!this.pausa && !this.terminado && ahora >= this.esperaHasta) {
      this.puertaObjetivo = 0;
      const p = this.paradas[this.siguiente];
      const falta = p.d - this.d;
      const v = Math.max(8, Math.min(46, falta * 1.4)) * this.velocidad;   // frena al acercarse
      this.d += v * dt;
      if (this.d >= p.d) this._llegar(p, ahora);
    }
    // puertas: se deslizan hacia afuera
    for (const puerta of this.puertas) {
      const abierto = puerta.userData.abierto || 0;
      const nuevo = abierto + (this.puertaObjetivo - abierto) * Math.min(1, dt * 6);
      puerta.userData.abierto = nuevo;
      puerta.position.z = puerta.userData.base + puerta.userData.lado * nuevo * 0.9;
      puerta.material.emissiveIntensity = nuevo * 0.8;
    }
    this._ubicarBus(this.d);
    this._colocarCamara(REDUCIDO);
    const pulso = 1 + Math.sin(ahora / 300) * 0.12;
    this.objetosParada.forEach((o, i) => {
      const base = this.paradas[i].tipo === 'parada' ? 9 : 16;
      o.brillo.scale.setScalar(i === this.siguiente ? base * 1.4 * pulso : base);
      // los letreros muy cercanos a la cámara se desvanecen para no tapar la vista
      const dist = o.nombre.position.distanceTo(this.camara.position);
      o.nombre.material.opacity = Math.max(0, Math.min(1, (dist - 22) / 26));
    });
    this.renderer.render(this.escena, this.camara);
    this.raf = requestAnimationFrame((t) => this._cuadro(t));
  }

  cerrar() {
    if (this.cerrado) return;
    this.cerrado = true;
    cancelAnimationFrame(this.raf);
    document.removeEventListener('keydown', this._alTeclear);
    this._alRedimensionar.disconnect();
    window.speechSynthesis && speechSynthesis.cancel();
    this.escena.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
      ms.forEach((m) => { if (m.map) m.map.dispose(); m.dispose(); });
    });
    this.renderer.dispose();
    this.capa.classList.add('saliendo');
    setTimeout(() => this.capa.remove(), 250);
  }
}
