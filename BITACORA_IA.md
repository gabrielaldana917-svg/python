# Bitácora de uso de IA

**Grupo:** <número> · **Integrantes:** <Gabriel Felipe Aldana Vargas>, <Natalia Carrero Salinas>, <Harold Yesid Fúneme Mateus>
**Herramientas usadas:** <p. ej. ChatGPT 5, Claude, Copilot>

> Las tres secciones son obligatorias. **`## Rechazado` es la que se califica.**
> Una bitácora que solo lista prompts aceptados vale la mitad.

## Prompts

| # | Parte | Quién | Prompt (resumido si es largo) |
|---|-------|-------|-------------------------------|
| 1 | A | Asistente IA (diagnóstico) | Ayuda para identificar los defectos del servicio riesgo-api-v0 (síntomas, causa, cita al material del curso, comando de evidencia) para llenar HALLAZGOS.md |
| 2 | B | Antigravity IDE | "Actúa como un desarrollador experto en Python... En dominio.py, EvaluadorRiesgo tiene historial = [] como atributo de clase... refactorízalo para que sea atributo de instancia... En utilidades.py, con_registro oculta el nombre real y traga excepciones; usa functools.wraps y elimina el try/except" |
| 3 | B | Asistente IA (refactor completo) | Refactor de main.py, dominio.py y config.py para cumplir las restricciones B1-B9 del enunciado (códigos de estado correctos, sin pickle, dominio en clases, validación con Pydantic, modelo cargado al inicio, /health, secretos fuera del código, arranque de producción documentado) |

## Aceptado

| # | Qué propuso la IA | Por qué lo aceptamos | Qué cambiamos antes de usarlo |
|---|--------------------|-----------------------|--------------------------------|
| 1 | Añadir `@functools.wraps(func)` al decorador `con_registro` y eliminar el `try/except` que devolvía `None` en silencio | Corrige exactamente H2 y H3: el decorador dejaba de ocultar el nombre real de la función y de tragarse excepciones sin avisar | Ninguno, se aplicó tal cual lo propuso Antigravity |
| 2 | Reemplazar la validación manual (`if`, `assert`) en `/score` por un modelo `ScoreRequest(BaseModel)` con `Field(gt=0)`, `Field(ge=0)` y un `field_validator` en `poliza`, dejando que `ValidationError` se traduzca a 422 | Corrige H1, H5 y H6 a la vez, y cumple B5 (entradas declaradas con BaseModel, restricciones con Field, al menos un validador) sin tocar el contrato de rutas ni el de `EvaluadorRiesgo` | Ajustamos los nombres de campo (`poliza`, `monto`, `antiguedad`, `siniestros_previos`) para que coincidieran exactamente con las claves que ya usa `EvaluadorRiesgo.puntuar` |
| 3 | Cargar `modelo.pkl` una sola vez a nivel de módulo (fuera del handler de `/score`) y crear el endpoint `/health` | Corrige H9 y cumple B6 y B7 directamente; evitar reabrir el archivo del modelo en cada request también evita I/O innecesario por petición | Ninguno |

## Rechazado

| # | Qué propuso la IA | Por qué lo rechazamos | Qué hicimos en su lugar |
|---|--------------------|-------------------------|---------------------------|
| 1 | (Antigravity) Mover `historial` de atributo de clase a `self.historial = []` en `__init__`, sin ningún otro cambio | Al probarlo con el refactor completo detectamos que rompía `/historial`: cada `EvaluadorRiesgo` se crea y se descarta dentro de una sola request de `/score`, así que el historial de instancia nunca sobrevive entre peticiones y `/historial` queda vacío siempre. La IA resolvió el síntoma de H4 (estado compartido indebido) pero introdujo un defecto nuevo no contemplado en el prompt original | Se creó `RepositorioEvaluaciones`, inyectado como colaborador opcional (`EvaluadorRiesgo(poliza, repositorio=None)`), que preserva el historial compartido de forma explícita sin volver a un atributo de clase mutable. Mantiene la firma exigida por el enunciado (`EvaluadorRiesgo("POL-2026-0413")`) |
