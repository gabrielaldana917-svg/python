"""Lógica de dominio: evaluación de riesgo de pólizas."""
import csv
from pathlib import Path

import config
from utilidades import con_registro

BASE = Path(__file__).parent


class RepositorioEvaluaciones:
    """Guarda las evaluaciones registradas, compartido entre instancias de EvaluadorRiesgo."""

    def __init__(self):
        self._evaluaciones = []

    def registrar(self, evaluacion):
        self._evaluaciones.append(evaluacion)

    def todas(self):
        return list(self._evaluaciones)


repositorio_global = RepositorioEvaluaciones()


class EvaluadorRiesgo:
    """Evalúa el riesgo de una póliza y guarda lo que ha evaluado."""

    umbral = config.UMBRAL_ALTO_RIESGO

    def __init__(self, poliza, repositorio=None):
        self.poliza = poliza
        self.historial = []
        self.repositorio = repositorio if repositorio is not None else repositorio_global

    @con_registro
    def puntuar(self, modelo, payload):
        rasgos = [[
            payload["monto"],
            payload["antiguedad"],
            payload["siniestros_previos"],
        ]]
        return float(modelo.predict_proba(rasgos)[0][1])

    def anotar(self, puntaje):
        evaluacion = {"poliza": self.poliza, "puntaje": puntaje}
        self.historial.append(evaluacion)
        self.repositorio.registrar(evaluacion)

    def es_alto_riesgo(self, puntaje):
        return puntaje is not None and puntaje > self.umbral


def cargar_siniestros():
    with open(BASE / config.RUTA_DATOS, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def buscar_siniestro(id_siniestro):
    for fila in cargar_siniestros():
        if fila["id"] == str(id_siniestro):
            return fila
    return None