# Integrantes

| Integrante | Rol transversal | Requisitos del motor |
|---|---|---|
| Miguel Preciado | Coordinación, interfaz y experiencia de usuario | R1, R2, R3, R8 |
| Tomás Gómez | Datos, validación y pruebas | R4, R6, R10 |
| Daniel Bernate | Arquitectura, algoritmos e integración | R5, R7, R9 |

## Archivos de cada integrante

**Miguel Preciado**
- Motor: `motor/estructuras/tabla_hash.py` y `motor/estructuras/avl.py`; `motor/consultas.py` (R1, R2, R3); `motor/cierres.py` (R8).
- Pruebas: `test_tabla_hash.py`, `test_avl.py`, `test_r1_r2_r3_consultas.py`, `test_r8_cierres.py`.
- Interfaz: todo `web/` salvo el cliente y el worker del motor, incluidos el mapa con plano de metro, la vista 3D (`vista3d.js`), la carrera de algoritmos y el modo sustentación (`sustentacion.js`); `app.py`, `netlify.toml`.
- Documentación: `README.md`, `docs/`.

**Tomás Gómez**
- Motor: `motor/estructuras/cola_circular.py` y `motor/estructuras/ordenamiento.py`; `motor/carga.py`; `motor/horarios.py` (R4); `motor/ranking.py` (R6); `motor/fila.py` (R10).
- Pruebas: validador de reglas (`test_reglas_motor.py`), firmas del contrato (`test_contrato.py`), `apoyo.py`, la mini red de prueba, `test_carga.py`, `test_r4_proximo_bus.py`, `test_r6_ranking.py`, `test_r10_fila.py`, `test_cola_circular.py`, `test_ordenamiento.py`.
- Rendimiento: `benchmarks/` (generador de redes y medición de R11).
- Datos: `conversion/gtfs_a_csv.py` (GTFS a los tres CSV), con su GTFS de prueba y `test_conversion.py`.

**Daniel Bernate**
- Motor: contrato y fachada `motor/red.py`, `motor/__init__.py`, `motor/modelo.py`; `motor/estructuras/lista_doble.py` y `motor/estructuras/pila.py`; `motor/edicion.py` (R7); `motor/comandos.py` (R9); `motor/viaje.py` (R5, con la traza que anima los rayos X).
- Pruebas: `test_lista_doble.py`, `test_pila.py`, `test_r5_viaje.py`, `test_r7_edicion.py`, `test_r9_deshacer.py`, `test_web.py`.
- Integración: `web/python/puente.py` (el lado Python del front: impacto de un cierre y pruebas en vivo), `web/js/motor.js`, `web/js/motor-worker.js`.
