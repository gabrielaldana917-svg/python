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

> Un párrafo por endpoint. Expliquen **los tiempos que ustedes obtuvieron**, no la
> teoría general. Si un resultado los sorprendió, dígan­lo: eso se premia.

## `/ping`

## `/consulta-archivo`

## `/servicio-externo`

## `/calculo-pesado`
 