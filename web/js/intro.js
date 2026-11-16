/* Bienvenida: un articulado cruza la pantalla mientras Python carga.
 * Avanza según el progreso REAL del worker; se puede saltar; solo una vez por
 * sesión; con movimiento reducido es un simple fundido. Dueño: Miguel. */

export function crearIntro() {
  const raiz = document.getElementById('intro');
  const bus = raiz.querySelector('.intro-bus');
  const texto = raiz.querySelector('.intro-etapa');
  const barra = raiz.querySelector('.intro-barra i');
  const reducido = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let vista = false;
  try { vista = sessionStorage.getItem('intro-vista') === 'si'; } catch (e) { /* almacenamiento bloqueado */ }

  let objetivo = 0.04, actual = 0, cerrada = false, alTerminar = null, rafId = 0;

  function cuadro() {
    actual += (objetivo - actual) * 0.06;
    raiz.style.setProperty('--avance', actual.toFixed(4));
    if (objetivo >= 1 && actual > 0.995) return terminar();
    rafId = requestAnimationFrame(cuadro);
  }

  function terminar() {
    if (cerrada) return;
    cerrada = true;
    cancelAnimationFrame(rafId);
    try { sessionStorage.setItem('intro-vista', 'si'); } catch (e) { /* nada */ }
    raiz.classList.add('saliendo');
    setTimeout(() => { raiz.hidden = true; alTerminar && alTerminar(); }, reducido ? 0 : 500);
  }

  raiz.querySelector('.intro-saltar').addEventListener('click', () => { objetivo = 1; actual = 1; terminar(); });

  if (vista || reducido) raiz.classList.add('rapida');
  rafId = requestAnimationFrame(cuadro);

  return {
    progreso(pct, etapa) {
      objetivo = Math.max(objetivo, Math.min(1, pct));
      texto.textContent = etapa;
      barra.style.width = Math.round(pct * 100) + '%';
      if (pct >= 1 && (vista || reducido)) { actual = 1; terminar(); }
      // respaldo: si el navegador no dibuja cuadros (pestaña en segundo plano), igual se cierra
      if (pct >= 1) setTimeout(terminar, 3500);
    },
    fallo(msg) {
      texto.textContent = 'No se pudo cargar el motor: ' + msg;
      raiz.classList.add('con-error');
      bus.style.animationPlayState = 'paused';
    },
    alTerminar(fn) { alTerminar = fn; if (cerrada) fn(); },
  };
}
