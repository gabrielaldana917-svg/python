"""
riesgo-api-v0 — Servicio de puntuación de siniestros.
Aseguradora Santo Tomás · prototipo interno.
"""
import asyncio
import pickle
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

import config
from dominio import EvaluadorRiesgo, buscar_siniestro, cargar_siniestros, repositorio_global

BASE = Path(__file__).parent
app = FastAPI(title="Riesgo API", version="0.1.0")

# B6 — el modelo se carga una sola vez al iniciar el servicio, no en cada request
with open(BASE / config.RUTA_MODELO, "rb") as fh:
    MODELO = pickle.load(fh)

# Executor de procesos para el endpoint CPU-bound (Parte C)
executor_calculo = ProcessPoolExecutor(max_workers=2)


# --- Modelos de entrada y salida (B5) --------------------------------------

class ScoreRequest(BaseModel):
    poliza: str = Field(..., min_length=1)
    monto: float = Field(..., gt=0)
    antiguedad: int = Field(..., ge=0)
    siniestros_previos: int = Field(..., ge=0)

    @field_validator("poliza")
    @classmethod
    def poliza_no_vacia(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("poliza no puede estar vacía")
        return v


class ScoreResponse(BaseModel):
    poliza: str
    puntaje: float
    alto_riesgo: bool


class Evaluacion(BaseModel):
    poliza: str
    puntaje: float


class HistorialResponse(BaseModel):
    evaluaciones: list[Evaluacion]


class Siniestro(BaseModel):
    id: int
    poliza: str
    monto: float
    antiguedad: int
    siniestros_previos: int
    pago_alto: bool


class HealthResponse(BaseModel):
    status: str = "ok"


# --- Endpoints de negocio ----------------------------------------------------

@app.post("/score", response_model=ScoreResponse)
async def score(payload: ScoreRequest):
    evaluador = EvaluadorRiesgo(payload.poliza)
    puntaje = evaluador.puntuar(MODELO, payload.model_dump())
    evaluador.anotar(puntaje)

    return ScoreResponse(
        poliza=payload.poliza,
        puntaje=puntaje,
        alto_riesgo=evaluador.es_alto_riesgo(puntaje),
    )


@app.get("/historial", response_model=HistorialResponse)
async def historial():
    return HistorialResponse(evaluaciones=repositorio_global.todas())


@app.get("/siniestros/{id_siniestro}", response_model=Siniestro)
async def siniestro(id_siniestro: int):
    fila = buscar_siniestro(id_siniestro)
    if fila is None:
        raise HTTPException(status_code=404, detail=f"no existe el siniestro {id_siniestro}")
    return fila


@app.get("/exportar", response_model=list[Siniestro])
async def exportar():
    return cargar_siniestros()


# --- Endpoints de perfil de carga (Parte C) ---------------------------------

def _calculo_pesado_sync():
    total = 0.0
    for i in range(3_000_000):
        total += (i % 7) ** 0.5
    return round(total, 2)


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.get("/consulta-archivo")
def consulta_archivo():
    contenido = (BASE / config.RUTA_DATOS).read_text(encoding="utf-8")
    return {"lineas": len(contenido.splitlines())}


@app.get("/servicio-externo")
async def servicio_externo():
    await asyncio.sleep(0.3)
    return {"tarifa_referencia": 1.18}


@app.get("/calculo-pesado")
async def calculo_pesado():
    loop = asyncio.get_running_loop()
    total = await loop.run_in_executor(executor_calculo, _calculo_pesado_sync)
    return {"total": total}


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)