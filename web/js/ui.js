/* Componentes de interfaz reutilizables (dueño: Miguel). */

export const fmtN = (n) => Number(n).toLocaleString('es-CO');
export const minutos = (h) => { const [a, b] = h.split(':').map(Number); return a * 60 + b; };
export const hhmm = (m) => { m = ((Math.floor(m) % 1440) + 1440) % 1440; return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };
export const esperaTexto = (min) => (min < 1 ? 'ya' : min < 60 ? `${min} min` : `${Math.floor(min / 60)} h ${min % 60} min`);
export const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export function h(html) {
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

/* ------------------------------------------------------------ autocompletar (R2) */

let contadorAuto = 0;

/** Convierte un <input> en combobox accesible. Las sugerencias las da el motor (R2). */
export function autocompletar(input, motor, { alElegir, k = 7, alMedir } = {}) {
  const id = 'sug-' + ++contadorAuto;
  const lista = h(`<ul class="sugerencias" id="${id}" role="listbox" hidden></ul>`);
  input.parentElement.appendChild(lista);
  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-controls', id);
  input.setAttribute('aria-autocomplete', 'list');
  input.setAttribute('aria-expanded', 'false');
  input.autocomplete = 'off';
  let sel = -1, items = [], pedido = 0;

  const cerrar = () => { lista.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); };
  const elegir = (v) => { input.value = v; cerrar(); alElegir && alElegir(v); };
  const marcar = () => items.forEach((li, i) => { li.setAttribute('aria-selected', i === sel); if (i === sel) input.setAttribute('aria-activedescendant', li.id); });

  input.addEventListener('input', async () => {
    const p = input.value.toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const yo = ++pedido;
    if (!p) { cerrar(); return; }
    const r = await motor.llamar('autocompletar', p, k);
    if (yo !== pedido) return;
    alMedir && alMedir(r.ms);
    sel = -1;
    lista.innerHTML = r.datos.map((n, i) => `<li role="option" id="${id}-${i}" aria-selected="false" data-v="${esc(n)}"><mark>${esc(n.slice(0, p.length))}</mark>${esc(n.slice(p.length))}</li>`).join('')
      || '<li class="vacio" aria-disabled="true">Ninguna estación abierta empieza así</li>';
    items = [...lista.querySelectorAll('li[data-v]')];
    lista.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  });
  input.addEventListener('keydown', (e) => {
    if (lista.hidden || !items.length) { if (e.key === 'Enter') { e.preventDefault(); input.dispatchEvent(new Event('input')); } return; }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length; marcar(); }
    else if (e.key === 'Enter') { e.preventDefault(); elegir(items[sel >= 0 ? sel : 0].dataset.v); }
    else if (e.key === 'Escape') cerrar();
  });
  input.addEventListener('blur', () => setTimeout(cerrar, 150));
  lista.addEventListener('mousedown', (e) => { const li = e.target.closest('li[data-v]'); if (li) { e.preventDefault(); elegir(li.dataset.v); } });
}

/* ------------------------------------------------------------ avisos */

let temporizador;
export function toast(texto, tipo = '') {
  const t = document.getElementById('toast');
  t.className = 'toast ' + tipo;
  t.textContent = texto;
  t.hidden = false;
  clearTimeout(temporizador);
  temporizador = setTimeout(() => { t.hidden = true; }, 4200);
}

/* Avisos con personalidad: solo se disparan con datos reales, máximo uno
 * cada 25 s, y se apagan con el "modo serio". */
const ultimoAviso = { t: 0, claves: new Set() };
export function avisoConPersonalidad(clave, texto) {
  if (document.documentElement.dataset.serio === 'si') return;
  const ahora = Date.now();
  if (ahora - ultimoAviso.t < 25000 || ultimoAviso.claves.has(clave)) return;
  ultimoAviso.t = ahora;
  ultimoAviso.claves.add(clave);
  toast(texto, 'personalidad');
}

/* ------------------------------------------------------------ tiempo del motor */

/** El reloj de Python en el navegador no distingue menos de ~1 µs. */
export const textoMs = (ms) => (ms < 0.001 ? '< 1 µs' : ms < 1 ? (ms * 1000).toFixed(0) + ' µs' : ms.toFixed(1) + ' ms');

export function tiempoMotor(ms) {
  const e = document.getElementById('ms-motor');
  if (!e || ms == null) return;
  e.textContent = textoMs(ms);
  e.classList.remove('pulso');
  void e.offsetWidth;
  e.classList.add('pulso');
}
