"""Comando único para arrancar la app:  py app.py   (o  python3 app.py)

Levanta un servidor estático con la librería estándar y abre el navegador.
El motor corre DENTRO del navegador (Pyodide), así que no hace falta instalar
nada; solo se necesita internet la primera vez para descargar Pyodide.
Dueño: Miguel.
"""

import functools
import http.server
import os
import socket
import sys
import threading
import webbrowser

RAIZ = os.path.dirname(os.path.abspath(__file__))


def puerto_libre(preferido=8000):
    for p in range(preferido, preferido + 50):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise SystemExit("No hay puertos libres entre 8000 y 8049.")


class Manejador(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".py": "text/plain; charset=utf-8",
                      ".csv": "text/csv; charset=utf-8", ".json": "application/json"}

    def end_headers(self):
        # Que el navegador siempre revise si hay una versión nueva (evita mezclar
        # módulos viejos y nuevos mientras se desarrolla).
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, formato, *args):  # silencioso
        pass


def main():
    numeros = [a for a in sys.argv[1:] if a.isdigit()]
    puerto = puerto_libre(int(numeros[0]) if numeros else 8000)
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", puerto), functools.partial(Manejador, directory=RAIZ))
    url = "http://localhost:%d/web/" % puerto
    print("TransmiAlgoritmo en", url, "· Ctrl+C para salir", flush=True)
    if "--sin-navegador" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nHasta luego.")


if __name__ == "__main__":
    main()
