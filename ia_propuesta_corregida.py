"""
Propuesta generada por un asistente de IA para riesgo-api-v0 — corregida.

Defectos corregidos respecto al original (ver DICTAMEN_IA.md):
1. El validador de `monto` no retornaba el valor redondeado (quedaba en None).
2. `_puntuar` usaba `time.sleep` bloqueante dentro de una corrutina, anulando
   la concurrencia de `evaluar_lote`.
3. La regex de `correo_analista` rechazaba dominios multinivel válidos
   (ej. usta.edu.co).
"""
import asyncio
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SolicitudPuntuacion(BaseModel):
    """Datos de entrada para puntuar una póliza."""

    poliza: str = Field(min_length=8, max_length=20)
    correo_analista: str = Field(
        pattern=r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
    )
    monto: float = Field(gt=0)
    antiguedad: int = Field(ge=0, le=60)
    siniestros_previos: int = Field(ge=0)
    observaciones: Optional[str] = Field(default=None, max_length=200)

    @field_validator("monto")
    @classmethod
    def redondear_monto(cls, v: float) -> float:
        """Redondea el monto a dos decimales para evitar ruido de coma flotante."""
        return round(v, 2)


class RespuestaPuntuacion(BaseModel):
    """Resultado de la evaluación."""

    poliza: str
    puntaje: float = Field(ge=0.0, le=1.0)
    alto_riesgo: bool


async def _puntuar(solicitud: SolicitudPuntuacion) -> float:
    """Consulta el servicio externo de scoring y devuelve la probabilidad."""
    await asyncio.sleep(0.2)  # latencia típica del servicio de scoring (no bloqueante)
    base = 0.18 * solicitud.siniestros_previos - 0.01 * solicitud.antiguedad
    return max(0.0, min(1.0, 0.4 + base))


async def evaluar_lote(solicitudes) -> list:
    """Evalúa un lote de solicitudes de forma concurrente."""
    return await asyncio.gather(*[_puntuar(s) for s in solicitudes])