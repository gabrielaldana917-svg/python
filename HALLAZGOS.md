# Hallazgos — Parte A

**Grupo:** <número> · **Integrantes:** <Gabriel Felipe Aldana Vargas>, <Natalia Carrero Salinas>, <Harold Yesid Fúneme Mateus>

> No borren la fila de ejemplo hasta haber comprobado que su tabla se parsea.
> El formato es rígido: siete columnas, en este orden. Una tabla torcida se
> rechaza indicando la línea, no se «entiende igual».
>
> **Tuberías dentro de una celda:** si su comando lleva `|` —y varios lo llevarán,
> por `grep`, `head` o `jq`— escríbanlo `\|`. Sin escapar, Markdown lo lee como
> separador de columna y su fila pasa a tener ocho.

| ID | Síntoma observable | Causa | Módulo · Sección | SHA donde se observa | Comando de evidencia | Salida obtenida | Corrección aplicada |
|----|--------------------|-------|------------------|----------------------|----------------------|-----------------|---------------------|
| H1 | *(ejemplo de FORMATO, no un defecto de este repositorio)* `GET /ping` responde sin cabecera `Cache-Control` | El handler no declara política de caché | M2 · 2. El protocolo HTTP y la autenticación | `v0-semilla` | `curl -sI localhost:8000/ping \| grep -ci cache-control` | `0` | Se añade la cabecera en la respuesta |
| H2 | `POST /score` con `siniestros_previos` no numérico responde `200` con `puntaje: null`, no un error | El decorador `con_registro` en `utilidades.py` captura cualquier excepción y devuelve `None` en silencio | M1 · 6. Decoradores como guardianes | `v0-semilla` | `curl -s -X POST localhost:8000/score -H "Content-Type: application/json" -d '{"poliza":"POL-2026-0413","monto":1000,"antiguedad":3,"siniestros_previos":"muchos"}'` | `{"poliza":"POL-2026-0413","puntaje":null,"alto_riesgo":false}` | Se elimina el `try/except` que traga la excepción; el error se propaga y se traduce a un código HTTP apropiado |
| H3 | `EvaluadorRiesgo.puntuar` pierde su nombre real | El decorador `con_registro` no usa `@functools.wraps`, así que la función envuelta se llama `envoltura` | M1 · 6. Decoradores como guardianes | `v0-semilla` | `python3 -c "from dominio import EvaluadorRiesgo; print(EvaluadorRiesgo.puntuar.__name__)"` | `envoltura` | Se añade `@functools.wraps(func)` al decorador |
| H4 | Dos instancias distintas de `EvaluadorRiesgo` comparten el mismo historial de evaluaciones | `historial = []` está declarado como atributo de **clase**, no de instancia, así que `self.historial.append(...)` muta una lista compartida por todos los objetos | M3 · 3. Componentes: atributos de clase | `v0-semilla` | `python3 -c "from dominio import EvaluadorRiesgo as E; a=E('POL-A'); b=E('POL-B'); a.anotar(0.5); print(b.historial)"` | `[{'poliza': 'POL-A', 'puntaje': 0.5}]` | El historial pasa a ser un atributo de instancia (o se extrae a un colaborador inyectado), sin tocar la firma `EvaluadorRiesgo(poliza)` ni `anotar(puntaje)` |
| H5 | `POST /score` responde `200` con `{"error": ...}` en el cuerpo cuando falta `poliza` o `antiguedad` es negativa | El handler valida a mano con `if` y devuelve el error dentro del cuerpo JSON, sin cambiar el código de estado | M2 · 2. El protocolo HTTP y la autenticación | `v0-semilla` | `curl -s -o /dev/null -w "%{http_code}" -X POST localhost:8000/score -H "Content-Type: application/json" -d '{"monto":1000}'` | `200` | Se sustituye la validación manual por un modelo Pydantic; `ValidationError` se traduce a `422` |
| H6 | `POST /score` con `monto` negativo responde `500 Internal Server Error`, no `422` | El handler usa `assert payload["monto"] > 0`, que lanza `AssertionError` sin capturar en vez de una validación declarativa | M4 · 7. Del ValidationError al error HTTP 422 | `v0-semilla` | `curl -s -o /dev/null -w "%{http_code}" -X POST localhost:8000/score -H "Content-Type: application/json" -d '{"poliza":"POL-2026-0413","monto":-5,"antiguedad":3,"siniestros_previos":1}'` | `500` | Se reemplaza el `assert` por `Field(gt=0)` en el modelo Pydantic de entrada |
| H7 | `GET /siniestros/{id}` con un id inexistente responde `200` con `{"error": ...}`, no `404` | El handler retorna el diccionario de error sin fijar `status_code=404` | M2 · 2. El protocolo HTTP y la autenticación | `v0-semilla` | `curl -s -o /dev/null -w "%{http_code}" localhost:8000/siniestros/999999` | `200` | Se usa `HTTPException(status_code=404, ...)` cuando `buscar_siniestro` devuelve `None` |
| H8 | `GET /exportar` responde con `content-type: application/octet-stream`, no JSON | El handler serializa la respuesta con `pickle.dumps(datos)` en vez de devolver JSON | M2 · 3. JSON frente a Pickle | `v0-semilla` | `curl -s -D - -o /dev/null localhost:8000/exportar \| grep -i content-type` | `content-type: application/octet-stream` | Se reemplaza `pickle.dumps` por retornar la lista de dicts directamente (FastAPI la serializa a JSON) |
| H9 | No existe el endpoint `/health` | Nunca se declaró la ruta | M5 · 8. Resumen y mejores prácticas | `v0-semilla` | `curl -s -o /dev/null -w "%{http_code}" localhost:8000/health` | `404` | Se añade `@app.get("/health")` que responde `200` |

**Reglas que se verifican automáticamente:**

- `Módulo · Sección` debe citar una lección que exista en los módulos 1 a 5, con el
  título tal como aparece en el menú lateral del material.
- **`SHA donde se observa`** es el commit donde el defecto todavía está: normalmente
  `v0-semilla`, la etiqueta del repositorio tal como se lo entregamos. El calificador hace
  *checkout* de ese commit para reproducir la evidencia. Si lo dejan en el commit final —donde
  ya está corregido— el comando no reproducirá nada y la fila no cuenta.
- `Comando de evidencia` se ejecuta ahí. Escríbanlo contra `localhost:8000`; el calificador
  sustituye el puerto por el que use.
- `Salida obtenida` es literal, copiada de su terminal. **Se compara con lo que salga de
  verdad**, así que una salida inventada se detecta.
- Entre 6 y 12 hallazgos. Una fila que no corresponda a un defecto real resta la mitad de lo
  que suma una correcta: el máximo se alcanza con precisión, no con volumen.

---

# Parte C — Interpretación de las mediciones

## Parte C — Decisión sync/async, medida

**/ping** — trivial, sin dependencias externas ni cómputo. A concurrencia 1, p50/p95
(~1 ms) confirman una respuesta prácticamente instantánea, coherente con la
clasificación. A concurrencia 20, el p50 se mantiene bajo (1.4 ms) pero el p95 salta a
~2025 ms: una cola de unas pocas peticiones (de 50) queda muy rezagada, aunque el
handler no hace ningún trabajo. Como /ping no toca disco ni red, esto no se explica por
el código sino por el entorno: Uvicorn en Windows corre sobre el event loop estándar de
asyncio (uvloop no está disponible en Windows), y con un solo worker, un estallido de 20
conexiones simultáneas puede generar una cola de aceptación breve mientras el sistema
operativo procesa los sockets. La decisión `async def` sigue siendo correcta: no hay
nada que delegar a un thread ni a un proceso en un endpoint que no hace trabajo alguno.

**/consulta-archivo** — IO-bound (lectura de disco), decidido como `def` en vez de
`async def`, para que FastAPI lo ejecute en su threadpool interno sin bloquear el event
loop. A concurrencia 1, los tiempos (~1.2-1.6 ms) muestran que la lectura en sí es
barata: el archivo de datos es pequeño. A concurrencia 20, el p50 apenas cambia
(1.6 ms) y el p95 muestra el mismo patrón de cola que /ping (~2015 ms) — la misma
magnitud en un endpoint que ni siquiera corre en el event loop, lo que indica que ese
pico no depende de nuestra decisión sync/async sino del mismo techo de concurrencia del
entorno. Esto es justo el caso que avisa el enunciado en sus dos caras: seguir la regla
al pie de la letra («I/O va con async») aquí habría significado dejar el `read_text()`
bloqueante dentro de un `async def`, bloqueando el único event loop del proceso en cada
petición — peor que delegarlo al threadpool. Y a la inversa, la decisión que tomamos
«incumple» la regla superficial (usa `def`, no `async def`) y la medición muestra que,
para una lectura tan liviana, no hay ninguna penalización visible por hacerlo así.

**/servicio-externo** — IO-bound (llamada externa simulada), decidido como `async def`
con `await asyncio.sleep(0.3)` (espera realmente no bloqueante). A concurrencia 1, el
tiempo total (15.121 s / 50 peticiones ≈ 302 ms cada una) coincide casi exacto con los
0.3 s de espera fija, como se espera al no solaparse nada. A concurrencia 20, el tiempo
total cae a 2.919 s para las mismas 50 peticiones — unas 5 veces menos — mientras el p50
se mantiene cerca de los 304.5 ms: la mayoría de peticiones tarda apenas lo que tarda
una sola espera, porque el event loop solapa las 20 esperas en vez de hacerlas una tras
otra. Este es el caso donde «I/O va con async» sí cumple lo que promete: una espera
genuinamente no bloqueante escala muy por debajo de lo lineal con la concurrencia. El
p95 (2318 ms) refleja una cola de conexión similar a la de los otros endpoints, pero no
cambia la conclusión de fondo.

**/calculo-pesado** — CPU-bound, decidido como `async def` delegando a un
`ProcessPoolExecutor` de 2 workers. A concurrencia 1, p50 = 274.4 ms es aproximadamente
el costo real del cálculo en un núcleo. A concurrencia 20, el p50 sube a 2929 ms (~10.7
veces) y el p95 a 5515 ms: con solo 2 procesos disponibles, las 20 peticiones
concurrentes se encolan detrás de esos 2 cupos, y la mayoría espera a que terminen
cálculos anteriores antes de que el suyo siquiera empiece. Esto confirma la
clasificación: ningún truco de sync/async elimina trabajo de CPU, solo decide quién
queda bloqueado esperándolo. Usar el executor mantiene ese costo fuera del event loop
principal —los demás endpoints seguirían respondiendo mientras este se acumula—, pero no
sustituye tener suficiente capacidad: si el throughput de este endpoint importara en
producción, la solución sería más workers o menos trabajo por petición, no solo sacarlo
del event loop.
 