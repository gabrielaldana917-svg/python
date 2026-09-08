"""Configuración del servicio."""
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["API_KEY"]
CLAVE_FIRMA = os.environ["CLAVE_FIRMA"]

UMBRAL_ALTO_RIESGO = float(os.environ.get("UMBRAL_ALTO_RIESGO", "0.7"))
RUTA_MODELO = "modelo.pkl"
RUTA_DATOS = "datos/siniestros.csv"