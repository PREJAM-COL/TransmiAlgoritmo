/* Cliente del motor: la ÚNICA puerta entre la interfaz y Python. Dueño: Daniel.
 * Cada llamada devuelve una promesa con { datos, ms } (ms = tiempo dentro de Python). */

export class Motor {
  constructor({ alProgresar, alEstarListo, alFallar } = {}) {
    this.pendientes = new Map();
    this.siguienteId = 1;
    this.listo = false;
    this.worker = new Worker(new URL('./motor-worker.js', import.meta.url));
    this.worker.onmessage = (e) => {
      const m = e.data;
      if (m.tipo === 'progreso') alProgresar && alProgresar(m);
      else if (m.tipo === 'listo') { this.listo = true; this.info = m.info; alEstarListo && alEstarListo(m.info); }
      else if (m.tipo === 'fallo') alFallar && alFallar(m.error);
      else if (m.tipo === 'prueba') { const p = this.pendientes.get(m.id); p && p.alAvanzar && p.alAvanzar(m.datos); }
      else if (m.tipo === 'respuesta') {
        const p = this.pendientes.get(m.id);
        if (!p) return;
        this.pendientes.delete(m.id);
        m.ok ? p.resolver({ datos: m.datos, ms: m.ms }) : p.rechazar(new Error(m.error));
      }
    };
  }

  llamar(op, ...args) {
    const id = this.siguienteId++;
    return new Promise((resolver, rechazar) => {
      this.pendientes.set(id, { resolver, rechazar });
      this.worker.postMessage({ id, op, args });
    });
  }

  async dato(op, ...args) {
    return (await this.llamar(op, ...args)).datos;
  }

  /** Corre la suite de pruebas en Python; alAvanzar recibe cada prueba terminada. */
  correrPruebas(alAvanzar) {
    const id = this.siguienteId++;
    return new Promise((resolver, rechazar) => {
      this.pendientes.set(id, { resolver, rechazar, alAvanzar });
      this.worker.postMessage({ id, op: 'correr_pruebas', args: [] });
    }).then((r) => r.datos);
  }
}
