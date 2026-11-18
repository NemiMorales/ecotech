"""Servicio de consulta de clima vía API externa (Open-Meteo, no requiere llave)."""

from __future__ import annotations

import math
import os
from typing import Any

import requests

from ecotech.excepciones import DatoInvalidoError, ServicioExternoError
from ecotech.seguridad.validador import ValidadorEntrada
from ecotech.servicios.servicio_api import ServicioAPI

# Códigos WMO que entrega Open-Meteo (weather_code).
_DESCRIPCION_WMO = {
    0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
    45: "Niebla", 48: "Niebla con escarcha",
    51: "Llovizna leve", 53: "Llovizna moderada", 55: "Llovizna intensa",
    56: "Llovizna helada leve", 57: "Llovizna helada intensa",
    61: "Lluvia leve", 63: "Lluvia moderada", 65: "Lluvia intensa",
    66: "Lluvia helada leve", 67: "Lluvia helada intensa",
    71: "Nevada leve", 73: "Nevada moderada", 75: "Nevada intensa", 77: "Granos de nieve",
    80: "Chubascos leves", 81: "Chubascos moderados", 82: "Chubascos violentos",
    85: "Chubascos de nieve leves", 86: "Chubascos de nieve intensos",
    95: "Tormenta", 96: "Tormenta con granizo leve", 99: "Tormenta con granizo intenso",
}
# Códigos que justifican reprogramar trabajo en terreno (lluvia, nieve, tormenta).
_CODIGOS_RIESGO = {55, 57, 63, 65, 66, 67, 71, 73, 75, 77, 81, 82, 85, 86, 95, 96, 99}
_VIENTO_RIESGO_KMH = 50


# IA: adoptado
class ServicioClima(ServicioAPI):
    """Obtiene el clima actual de la ciudad de un proyecto para apoyar su planificación."""

    NOMBRE = "Servicio de clima"

    def __init__(self, timeout: float | None = None, http: Any = requests) -> None:
        super().__init__(
            os.getenv("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast"), timeout, http
        )
        # Segunda API del mismo proveedor: convierte el nombre de la ciudad en coordenadas.
        self.__geocodificador = ServicioAPI(
            os.getenv("WEATHER_GEOCODING_URL", "https://geocoding-api.open-meteo.com/v1/search"),
            timeout, http,
        )
        self.__geocodificador.NOMBRE = self.NOMBRE

    def consultar(self, ciudad: str) -> dict[str, Any]:
        """Devuelve solo los datos útiles para el sistema (no el JSON completo)."""
        ciudad = ValidadorEntrada.validar_ciudad(ciudad)  # nunca se envía texto sin validar
        lugar = self.__ubicar(ciudad)
        datos = self._obtener_json(parametros={
            "latitude": lugar["latitud"],
            "longitude": lugar["longitud"],
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        })
        temperatura = self.__numero(self._extraer(datos, "current", "temperature_2m"))
        humedad = self.__numero(self._extraer(datos, "current", "relative_humidity_2m"))
        viento = self.__numero(self._extraer(datos, "current", "wind_speed_10m"))
        codigo = int(self.__numero(self._extraer(datos, "current", "weather_code")))
        return {
            "ciudad": lugar["nombre"],
            "pais": lugar["pais"],
            "temperatura_c": temperatura,
            "humedad_pct": humedad,
            "viento_kmh": viento,
            "estado": _DESCRIPCION_WMO.get(codigo, "Sin descripción"),
            "alerta": self.evaluar_riesgo(codigo, viento),
            "hora_medicion": self._extraer(datos, "current", "time"),
        }

    @staticmethod
    def evaluar_riesgo(codigo: int, viento_kmh: float) -> str | None:
        """Regla de negocio: ¿conviene reprogramar el trabajo en terreno?"""
        motivos = []
        if codigo in _CODIGOS_RIESGO:
            motivos.append(_DESCRIPCION_WMO.get(codigo, "precipitaciones").lower())
        if viento_kmh >= _VIENTO_RIESGO_KMH:
            motivos.append(f"viento fuerte ({viento_kmh:g} km/h)")
        if not motivos:
            return None
        return "Riesgo para trabajo en terreno: " + " y ".join(motivos) + ". Evaluar reprogramar."

    def __ubicar(self, ciudad: str) -> dict[str, Any]:
        datos = self.__geocodificador._obtener_json(
            parametros={"name": ciudad, "count": 1, "language": "es", "format": "json"}
        )
        resultados = datos.get("results") or []
        if not resultados:
            raise DatoInvalidoError(f"No se encontró la ciudad '{ciudad}'.")
        primero = resultados[0]
        return {
            "nombre": primero.get("name", ciudad),
            "pais": primero.get("country", "—"),
            "latitud": self.__numero(self._extraer(primero, "latitude")),
            "longitud": self.__numero(self._extraer(primero, "longitude")),
        }

    @staticmethod
    def __numero(valor: Any) -> float:
        """Verifica que el dato sea un número real antes de usarlo."""
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
            raise ServicioExternoError("El servicio de clima entregó un valor no numérico.")
        return float(valor)
