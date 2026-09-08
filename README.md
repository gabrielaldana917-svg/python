# riesgo-api-v0

Servicio de puntuación de siniestros de la Aseguradora Santo Tomás.
Recibe los datos de una póliza y devuelve la probabilidad de que el siniestro
declarado termine en un pago alto.

## Instalación

```bash
pip install -r requirements.txt
```

El modelo entrenado (`modelo.pkl`) viene en el repositorio.

## Puesta en marcha

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El mismo comando sirve en el servidor de producción. `--reload` es cómodo
porque recoge los cambios sin reiniciar a mano.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/score` | Puntúa una póliza |
| GET | `/historial` | Evaluaciones hechas |
| GET | `/siniestros/{id}` | Consulta un siniestro |
| GET | `/exportar` | Exporta el histórico para el equipo de actuaría |
| GET | `/ping` | Comprobación rápida |
| GET | `/consulta-archivo` | Cuenta los registros del archivo de siniestros |
| GET | `/servicio-externo` | Consulta la tarifa de referencia del reasegurador |
| GET | `/calculo-pesado` | Recalcula la reserva agregada |

### Ejemplo

```bash
curl -X POST localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"poliza": "POL-2026-0413", "monto": 4200000, "antiguedad": 3, "siniestros_previos": 1}'
```

```json
{"poliza": "POL-2026-0413", "puntaje": 0.61, "alto_riesgo": false}
```

## Notas

- La clave de la API está en `config.py` para que el equipo pueda probar sin configurar nada.
- El histórico se exporta con `pickle`, que conserva los tipos de Python tal cual.

## Arranque

### Desarrollo
\`\`\`
uvicorn main:app --reload
\`\`\`

### Producción
\`\`\`
uvicorn main:app --workers 4
\`\`\`
Sin `--reload`: la recarga en caliente no es apta para producción porque reinicia el proceso worker
ante cualquier cambio de archivo, lo cual es inaceptable bajo carga real.