/* Arranque de la aplicación: motor, mapa, vistas, reloj y panel de estación. Dueño: Miguel. */

import { colorRuta, Mapa } from './mapa.js';
import { crearIntro } from './intro.js';
import { Motor } from './motor.js';
import { crearSustentacion } from './sustentacion.js';
import { avisoConPersonalidad, esc, esperaTexto, fmtN, hhmm, tiempoMotor, toast } from './ui.js';
import { crearVistaHoraPico } from './vistas/horapico.js';
import { crearVistaOperacion } from './vistas/operacion.js';
import { crearVistaRed } from './vistas/red.js';
import { crearVistaRendimiento } from './vistas/rendimiento.js';
import { crearVistaViaje } from './vistas/viaje.js';

const $ = (s) => document.querySelector(s);
const intro = crearIntro();
const estados = new Map();      // nombre -> {abierta, buses, rutas}  (copia de lo que dice el motor)
let hora = 7 * 60 + 40;          // minutos; la línea de tiempo arranca a las 07:40
let reproduciendo = false, velocidad = 60, acumulado = 0, horaFlota = -1;
let vistaActual = null;
let estacionActual = 'RICAURTE';

const motor = new Motor({
  alProgresar: (m) => intro.progreso(m.pct, m.texto),
  alEstarListo: iniciar,
  alFallar: (e) => { intro.fallo(e); toast('No se pudo cargar el motor: ' + e, 'error'); },
});

const mapa = new Mapa($('#escenario'), { alSeleccionar: (n) => seleccionar(n, { delUsuario: true }) });

const ctx = {
  motor,
  mapa,
  horaTexto: () => hhmm(hora),
  existe: (n) => estados.has(n),
  cerrada: (n) => estados.has(n) && !estados.get(n).abierta,
  seleccionar: (n) => seleccionar(n),
  redCambio,
};

const vistas = {
  viaje: crearVistaViaje(ctx),
  red: crearVistaRed(ctx),
  operacion: crearVistaOperacion(ctx),
  horapico: crearVistaHoraPico(ctx),
  rendimiento: crearVistaRendimiento(ctx),
};
ctx.vistas = vistas;
ctx.irA = (id) => irA(id);
const sustentacion = crearSustentacion(ctx);
$('#sustentar').addEventListener('click', () => (sustentacion.abierta ? sustentacion.cerrar() : sustentacion.abrir()));

/* ------------------------------------------------------------ arranque */

async function iniciar(info) {
  $('#info-carga').textContent = `Motor listo en ${(info.ms_total / 1000).toFixed(1)} s · red cargada en ${Math.round(info.ms_carga)} ms`;
  const red = await motor.dato('red_completa');
  guardarEstados(red);
  const rutas = await motor.dato('rutas');
  $('#lista-rutas').innerHTML = rutas.map((r) => `<option value="${esc(r)}">`).join('');
  $('#cifras').innerHTML = `<strong>${red.estaciones.length}</strong> estaciones <strong>${contarAristas(red)}</strong> conexiones <strong>${red.rutas.length}</strong> rutas`;
  intro.alTerminar(async () => {
    mapa.cargar(red);
    await actualizarHora(true);
    irA(location.hash.slice(1) || 'viaje');
    seleccionar(estacionActual);
    pintarRanking();
    pintarHistograma();
    requestAnimationFrame(cuadro);
  });
}

function contarAristas(red) {
  const s = new Set();
  for (const { p } of red.rutas) for (let i = 1; i < p.length; i++) s.add(p[i - 1] < p[i] ? p[i - 1] + '|' + p[i] : p[i] + '|' + p[i - 1]);
  return s.size;
}

function guardarEstados(red) {
  estados.clear();
  red.estaciones.forEach((e) => estados.set(e.n, e));
}

async function redCambio() {
  const red = await motor.dato('red_completa');
  guardarEstados(red);
  mapa.actualizar(red);
  await actualizarHora(true);
  seleccionar(estacionActual);
  pintarRanking();
  if (!$('#lista-red').hidden) pintarLista();
  Object.values(vistas).forEach((v) => v !== vistaActual || !v.alCambiarRed || v.alCambiarRed());
}

/* ------------------------------------------------------------ vistas */

function irA(id) {
  if (!vistas[id]) id = 'viaje';
  if (vistaActual === vistas[id]) return;
  if (vistaActual) vistaActual.desactivar();
  vistaActual = vistas[id];
  document.querySelectorAll('.pestana').forEach((b) => b.setAttribute('aria-current', b.dataset.vista === id ? 'page' : 'false'));
  const izq = $('#panel-izq');
  izq.replaceChildren(vistaActual.panel);
  const alterno = $('#centro-alterno');
  if (vistaActual.centro) { alterno.replaceChildren(vistaActual.centro); alterno.hidden = false; } else alterno.hidden = true;
  document.body.dataset.vista = id;
  if (location.hash.slice(1) !== id) history.replaceState(null, '', '#' + id);
  transicionPuertas();
  vistaActual.activar();
}

document.querySelectorAll('.pestana').forEach((b) => b.addEventListener('click', () => irA(b.dataset.vista)));
window.addEventListener('hashchange', () => irA(location.hash.slice(1)));

function transicionPuertas() {
  const p = $('#puertas');
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  p.classList.remove('animando');
  void p.offsetWidth;
  p.classList.add('animando');
}

/* ------------------------------------------------------------ panel de estación (R1, R4, R6) */

async function seleccionar(nombre, { delUsuario = false } = {}) {
  estacionActual = nombre;
  const r = await motor.llamar('detalle_estacion', nombre, hhmm(hora));
  tiempoMotor(r.ms);
  const d = r.datos;
  if (!d) return;
  if (delUsuario && vistaActual && vistaActual.alSeleccionarEstacion) vistaActual.alSeleccionarEstacion(nombre);
  const abierta = d.estado === 'ABIERTA';
  $('#estacion').innerHTML = `
    <div class="est-cab"><span class="eyebrow">Estación <span class="req">R1</span></span>
      <h2 class="est-nombre">${esc(d.nombre)}</h2>
      <span class="estado ${abierta ? 'ok' : 'cerr'}">${abierta ? 'Abierta' : 'Cerrada · nadie sube, baja ni transborda'}</span></div>
    <div class="kv"><div><b>${fmtN(d.buses)}</b><span>buses al día</span></div><div><b>${d.rutas.length}</b><span>rutas paran aquí</span></div></div>
    <div class="seccion"><div class="seccion-cab"><span class="eyebrow">Próximos buses <span class="req">R4</span></span><span class="chip prog">Programado</span></div>
      ${abierta ? `<ul class="tablero" aria-label="Próximos buses desde las ${hhmm(hora)}">${d.proximos.slice(0, 8).map((p) => `
        <li><button class="ruta" style="--rc:${colorRuta(p.ruta)}" data-ruta="${esc(p.ruta)}">${esc(p.ruta)}</button>
        <span class="led">${p.hora}</span><span class="falta">${p.espera === 0 ? 'ahora' : 'en ' + esperaTexto(p.espera)}</span></li>`).join('') || '<li class="vacia">Sin buses programados</li>'}</ul>`
        : '<p class="pista">Estación cerrada: R4 no da próximos buses.</p>'}
    </div>
    <div class="botones"><button class="boton" data-accion="origen">Salir de aquí</button><button class="boton" data-accion="destino">Ir aquí</button></div>`;
  const cerca = d.proximos[0];
  if (delUsuario && abierta && cerca && cerca.espera <= 2 && document.body.dataset.vista === 'viaje') {
    avisoConPersonalidad('cerca-' + nombre + cerca.hora, `¡Uy, apúrale! El ${cerca.ruta} pasa por ${nombre} a las ${cerca.hora}.`);
  }
}

$('#estacion').addEventListener('click', (e) => {
  const r = e.target.closest('[data-ruta]');
  if (r) { irA('red'); vistas.red.verRuta(r.dataset.ruta); return; }
  const a = e.target.closest('[data-accion]');
  if (!a) return;
  irA('viaje');
  const o = $('#v-origen'), d = $('#v-destino');
  if (a.dataset.accion === 'origen') { o.value = estacionActual; if (d.value) vistas.viaje.planear(o.value, d.value); else d.focus(); }
  else { d.value = estacionActual; if (o.value) vistas.viaje.planear(o.value, d.value); else o.focus(); }
});

async function pintarRanking() {
  const r = await motor.llamar('ranking', 5);
  const top = r.datos;                      // R6: [[nombre, buses_por_dia], ...]
  const max = Math.max(1, ...top.map(([, b]) => b));
  $('#ranking').innerHTML = top.map(([n, b]) => `<li><button class="enlace" data-n="${esc(n)}">${esc(n)}</button>
    <span class="n">${fmtN(b)}</span><span class="barra"><i style="width:${(100 * b / max).toFixed(1)}%"></i></span></li>`).join('');
}
$('#ranking').addEventListener('click', (e) => { const b = e.target.closest('[data-n]'); if (b) seleccionar(b.dataset.n); });

/* ------------------------------------------------------------ reloj y línea de tiempo */

const rango = $('#hora');
const histograma = $('#histograma');

async function actualizarHora(forzar = false) {
  $('#reloj').textContent = hhmm(hora);
  rango.value = hora;
  rango.setAttribute('aria-valuetext', hhmm(hora));
  const hActual = Math.floor(hora / 60);
  [...histograma.children].forEach((b, i) => b.classList.toggle('on', i === hActual));
  document.documentElement.dataset.ambiente = hActual < 5 || hActual >= 21 ? 'noche' : hActual < 7 ? 'amanecer' : hActual >= 18 ? 'atardecer' : 'dia';
  const m = Math.floor(hora);
  if (forzar || m !== horaFlota) {
    horaFlota = m;
    const f = await motor.dato('flota', m);
    mapa.ponerFlota(f, m);
    $('#flota-n').textContent = fmtN(f.length);
    if (forzar || m % 60 === 0) mapa.aplicarPulso(await motor.dato('pulso', hActual));
  }
}

async function pintarHistograma() {
  // Buses programados por hora (dato real): suma del pulso de cada hora.
  const conteos = [];
  for (let hh = 0; hh < 24; hh++) conteos.push((await motor.dato('pulso', hh)).reduce((s, x) => s + x[2], 0));
  const max = Math.max(...conteos);
  histograma.innerHTML = conteos.map((c, i) => `<i style="height:${Math.max(2, (100 * c) / max)}%" title="${String(i).padStart(2, '0')}:00 · ${fmtN(c)} pasos de bus"></i>`).join('');
  actualizarHora();
  if (conteos[Math.floor(hora / 60)] > 0.8 * max) avisoConPersonalidad('pico', 'Hora pico: es de las horas con más buses programados del día. Paciencia, parcero.');
}

rango.addEventListener('input', () => { hora = +rango.value; actualizarHora(); });
rango.addEventListener('change', async () => {
  seleccionar(estacionActual);
  vistaActual && vistaActual.alCambiarHora && vistaActual.alCambiarHora();
});
$('#reproducir').addEventListener('click', () => {
  reproduciendo = !reproduciendo;
  $('#reproducir').setAttribute('aria-pressed', reproduciendo);
  $('#reproducir').textContent = reproduciendo ? '❚❚' : '▶';
  if (!reproduciendo) { seleccionar(estacionActual); vistaActual.alCambiarHora && vistaActual.alCambiarHora(); }
});
$('#velocidad').addEventListener('click', () => {
  velocidad = velocidad === 60 ? 600 : 60;
  $('#velocidad').textContent = '×' + velocidad;
});
$('#ahora').addEventListener('click', () => {
  const d = new Date();
  hora = d.getHours() * 60 + d.getMinutes();
  actualizarHora(true);
  seleccionar(estacionActual);
  vistaActual.alCambiarHora && vistaActual.alCambiarHora();
});

/* ------------------------------------------------------------ bucle de animación */

let ultimo = performance.now();
function cuadro(ahora) {
  const dt = Math.min(64, ahora - ultimo);
  ultimo = ahora;
  if (reproduciendo) {
    hora = (hora + (dt / 1000) * (velocidad / 60)) % 1440;
    acumulado += dt;
    if (Math.floor(hora) !== horaFlota) actualizarHora();
    else { $('#reloj').textContent = hhmm(hora); rango.value = hora; }
  }
  mapa.dibujarFlota(hora);
  mapa.animarBus(dt, ahora);
  requestAnimationFrame(cuadro);
}

/* ------------------------------------------------------------ atajos y ajustes */

$('#zoom-mas').addEventListener('click', () => mapa.acercar(1.5));
$('#zoom-menos').addEventListener('click', () => mapa.acercar(1 / 1.5));
$('#zoom-ajustar').addEventListener('click', () => mapa.ajustar());
function alternarPlano() {
  const on = mapa.alternarPlano();
  $('#plano').setAttribute('aria-pressed', on);
  $('#plano').setAttribute('aria-label', on ? 'Volver a la disposición por fuerzas' : 'Cambiar a plano de metro');
  toast(on ? 'Plano de metro: conexiones a 0°, 45° y 90°, como los planos de metro.' : 'Disposición por fuerzas: las conexiones atraen, las estaciones se repelen.');
  return on;
}
ctx.alternarPlano = alternarPlano;

/* Vista en lista: la misma red como tabla navegable con teclado y lector de pantalla. */
function pintarLista() {
  const filtro = $('#lista-filtro').value.trim().toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  const filas = [...estados.values()].filter((e) => !filtro || e.n.includes(filtro));
  $('#lista-cuerpo').innerHTML = filas.map((e) => `<tr>
    <th scope="row"><button class="enlace" data-n="${esc(e.n)}">${esc(e.n)}</button></th>
    <td><span class="chip ${e.abierta ? 'ok' : 'cerr'}">${e.abierta ? 'abierta' : 'cerrada'}</span></td>
    <td class="num">${fmtN(e.buses)}</td><td class="num">${e.rutas}</td></tr>`).join('')
    || '<tr><td colspan="4">Ninguna estación coincide con el filtro.</td></tr>';
}
function alternarLista(abrir) {
  const lista = $('#lista-red');
  const on = abrir ?? lista.hidden;
  lista.hidden = !on;
  $('#ver-lista').setAttribute('aria-pressed', on);
  if (on) { pintarLista(); $('#lista-filtro').focus(); } else $('#ver-lista').focus();
}
$('#ver-lista').addEventListener('click', () => alternarLista());
$('#lista-cerrar').addEventListener('click', () => alternarLista(false));
$('#lista-filtro').addEventListener('input', pintarLista);
$('#lista-cuerpo').addEventListener('click', (e) => { const b = e.target.closest('[data-n]'); if (b) seleccionar(b.dataset.n, { delUsuario: true }); });
$('#lista-red').addEventListener('keydown', (e) => { if (e.key === 'Escape') alternarLista(false); });
ctx.enPlano = () => mapa.modoPlano;
$('#plano').addEventListener('click', alternarPlano);

const serio = $('#modo-serio');
try { if (localStorage.getItem('modo-serio') === 'si') { document.documentElement.dataset.serio = 'si'; serio.setAttribute('aria-pressed', 'true'); } } catch (e) { /* nada */ }
serio.addEventListener('click', () => {
  const on = document.documentElement.dataset.serio !== 'si';
  document.documentElement.dataset.serio = on ? 'si' : 'no';
  serio.setAttribute('aria-pressed', on);
  try { localStorage.setItem('modo-serio', on ? 'si' : 'no'); } catch (e) { /* nada */ }
  toast(on ? 'Modo serio: sin avisos con personalidad.' : 'Modo normal: vuelven los avisos.');
});

document.addEventListener('keydown', (e) => {
  if (e.target.matches && e.target.matches('input, textarea')) return;
  if (sustentacion.abierta && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) return;
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); vistas.operacion.deshacer(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') { e.preventDefault(); vistas.operacion.rehacer(); }
  if (!e.ctrlKey && !e.metaKey && !e.altKey && '12345'.includes(e.key)) irA(['viaje', 'red', 'operacion', 'horapico', 'rendimiento'][+e.key - 1]);
});

/* Huevo de Pascua: cinco clics en el logo llenan la red de buses por un momento. */
let clicsLogo = 0, tLogo = 0;
$('.marca').addEventListener('click', async () => {
  const t = Date.now();
  clicsLogo = t - tLogo < 600 ? clicsLogo + 1 : 1;
  tLogo = t;
  if (clicsLogo === 5) {
    const guardada = hora;
    hora = 7 * 60 + 30;
    await actualizarHora(true);
    toast('Desfile de articulados: así se ve la red a las 07:30.', 'personalidad');
    setTimeout(() => { hora = guardada; actualizarHora(true); }, 5000);
  }
});
