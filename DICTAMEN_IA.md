# Dictamen sobre `ia_propuesta.py` — Parte D

**Grupo:** <4> · **Integrantes:** <Gabriel Felipe Aldana Vargas>, <Harold Yesid Fúneme Mateus>, <Natalia Carrero Salinas>

> Tres defectos. Las cuatro secciones de cada uno son obligatorias y se parsean.
> El peso está en **«Cómo lo comprobamos»**: afirmar que algo está mal no vale;
> demostrarlo, sí.

## Defecto 1

- **Qué está mal:** El validador `redondear_monto` (decorado con `@field_validator("monto")`)
  llama a `round(v, 2)` pero no retorna el resultado. Como Pydantic v2 usa el valor de
  retorno del validador para reemplazar el campo, `solicitud.monto` queda en `None`
  después de la validación — el monto original desaparece silenciosamente, sin ningún
  error ni advertencia.
- **Por qué es un defecto** (citando módulo · sección): M4 · Validación declarativa con
  Pydantic — un validador de campo debe devolver el valor transformado; omitir el
  `return` no es una advertencia de estilo, corrompe el dato en silencio, el mismo tipo
  de fallo silencioso que H2 de la Parte A (una excepción tragada sin avisar).
- **Cómo lo comprobamos:**
```python
  from ia_propuesta import SolicitudPuntuacion
  s = SolicitudPuntuacion(poliza="POL20260413", correo_analista="ana@usta.co",
                           monto=1234.567, antiguedad=3, siniestros_previos=1)
  print(s.monto)
```
  Salida obtenida: `None`
- **Corrección:** Agregar `return round(v, 2)` en el validador.

## Defecto 2

- **Qué está mal:** `_puntuar` es una corrutina (`async def`) pero usa `time.sleep(0.2)`,
  que es **bloqueante**. Bloquea el único hilo del event loop durante 0.2 s por cada
  llamada. `evaluar_lote` usa `asyncio.gather` esperando paralelismo, pero como cada
  tarea bloquea el loop entero, las tareas terminan ejecutándose una tras otra, no
  concurrentemente — exactamente lo contrario de lo que pidió el prompt original
  ("evalúe un lote de solicitudes concurrentemente").
- **Por qué es un defecto** (citando módulo · sección): M5 · Concurrencia y llamadas
  bloqueantes en handlers async — el mismo patrón que H2/H3 de la Parte A: declarar algo
  `async` no lo vuelve no bloqueante si por dentro usa una llamada síncrona.
- **Cómo lo comprobamos:**
```python
  import asyncio, time
  from ia_propuesta import SolicitudPuntuacion, evaluar_lote

  sols = [SolicitudPuntuacion(poliza="POL20260413", correo_analista="ana@usta.co",
                               monto=1000, antiguedad=3, siniestros_previos=i)
          for i in range(5)]
  t0 = time.perf_counter()
  asyncio.run(evaluar_lote(sols))
  print(round(time.perf_counter() - t0, 3))
```
  Salida obtenida: `1.005` (segundos, para 5 solicitudes — ≈ 5 × 0.2 s, tiempo serial,
  no concurrente)
- **Corrección:** Reemplazar `time.sleep(0.2)` por `await asyncio.sleep(0.2)` en
  `_puntuar` (y, al conectar con el servicio real, usar un cliente HTTP async como
  `httpx.AsyncClient` en vez de una espera simulada).

## Defecto 3

- **Qué está mal:** El patrón `^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,3}$` solo
  admite un dominio de **un solo nivel** antes del TLD (`usuario@dominio.tld`). Rechaza
  cualquier dominio con subniveles, como `usta.edu.co` — el dominio de correo de la
  propia universidad.
- **Por qué es un defecto** (citando módulo · sección): M4 · Validación declarativa con
  Pydantic — una restricción de formato (`pattern`) más estricta que el dominio real del
  negocio produce falsos rechazos: rechaza entradas válidas, no solo las inválidas.
- **Cómo lo comprobamos:**
```python
  from ia_propuesta import SolicitudPuntuacion
  from pydantic import ValidationError

  try:
      SolicitudPuntuacion(poliza="POL20260413", correo_analista="ana@usta.edu.co",
                           monto=1000, antiguedad=3, siniestros_previos=1)
      print("aceptado")
  except ValidationError as e:
      print("RECHAZADO")
```
  Salida obtenida: `RECHAZADO`
- **Corrección:** Ajustar el patrón para permitir múltiples niveles de dominio y TLDs de
  cualquier longitud ≥ 2:
  `^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$`