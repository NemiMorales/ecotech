"""Prueba del consumo de APIs SIN internet: se simulan las respuestas del servidor.

Así se pueden probar casos difíciles de provocar a mano (timeout, error 500, JSON roto).
Ejecutar desde la raíz del repo:  python -m tests.prueba_apis
"""

import logging
import sys

import requests

from ecotech.excepciones import DatoInvalidoError, ServicioExternoError
from ecotech.servicios.clima import ServicioClima
from ecotech.servicios.indicadores import ServicioIndicadores
from ecotech.servicios.servicio_api import ServicioAPI

logging.disable(logging.CRITICAL)
fallos = 0


def comprobar(descripcion: str, condicion: bool) -> None:
    global fallos
    print(f"[{'OK' if condicion else 'FALLA'}] {descripcion}")
    if not condicion:
        fallos += 1


def debe_fallar(descripcion: str, excepcion: type, funcion) -> str:
    try:
        funcion()
    except excepcion as error:
        comprobar(f"{descripcion} -> {type(error).__name__}: {error}", True)
        return str(error)
    comprobar(f"{descripcion} (no lanzó {excepcion.__name__})", False)
    return ""


class RespuestaFalsa:
    def __init__(self, codigo: int, cuerpo=None, json_invalido: bool = False) -> None:
        self.status_code = codigo
        self.__cuerpo = cuerpo
        self.__json_invalido = json_invalido

    def json(self):
        if self.__json_invalido:
            raise requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)
        return self.__cuerpo


class HttpFalso:
    """Reemplaza al módulo requests: devuelve respuestas según la URL o lanza un error de red."""

    def __init__(self, respuestas: dict, error: Exception | None = None) -> None:
        self.respuestas = respuestas
        self.error = error
        self.llamadas: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append({"url": url, "params": params, "timeout": timeout})
        if self.error:
            raise self.error
        for fragmento, respuesta in self.respuestas.items():
            if fragmento in url:
                return respuesta
        return RespuestaFalsa(404, {})


GEO_OK = RespuestaFalsa(200, {"results": [
    {"name": "Antofagasta", "country": "Chile", "latitude": -23.65, "longitude": -70.4}]})
CLIMA_LLUVIA = RespuestaFalsa(200, {"current": {
    "time": "2026-11-18T15:00", "temperature_2m": 14.2, "relative_humidity_2m": 88,
    "weather_code": 63, "wind_speed_10m": 22.0}})
CLIMA_DESPEJADO = RespuestaFalsa(200, {"current": {
    "time": "2026-11-18T15:00", "temperature_2m": 24.0, "relative_humidity_2m": 30,
    "weather_code": 0, "wind_speed_10m": 8.0}})
TASAS_OK = RespuestaFalsa(200, {"result": "success", "base_code": "CLP",
                                "time_last_update_utc": "Wed, 18 Nov 2026 00:02:31 +0000",
                                "rates": {"CLP": 1, "USD": 0.00105, "PEN": 0.0039}})

# --- 3.1.1: solicitud HTTP, JSON y extracción de datos ---
http = HttpFalso({"geocoding": GEO_OK, "forecast": CLIMA_LLUVIA})
clima = ServicioClima(http=http).consultar("antofagasta")
comprobar("Clima: extrae solo los datos útiles",
          (clima["ciudad"], clima["temperatura_c"], clima["humedad_pct"], clima["estado"])
          == ("Antofagasta", 14.2, 88.0, "Lluvia moderada"))
comprobar("Clima: alerta para reprogramar trabajo en terreno", clima["alerta"] is not None)
comprobar("Toda solicitud lleva timeout", all(l["timeout"] for l in http.llamadas))
comprobar("Coordenadas de la ciudad se envían a la API de clima",
          http.llamadas[1]["params"]["latitude"] == -23.65)
http = HttpFalso({"geocoding": GEO_OK, "forecast": CLIMA_DESPEJADO})
comprobar("Clima despejado sin alerta", ServicioClima(http=http).consultar("Antofagasta")["alerta"] is None)

indicadores = ServicioIndicadores(http=HttpFalso({"latest/CLP": TASAS_OK}))
pago = indicadores.calcular_pago(1_000_000, "usd")
comprobar("Tipo de cambio: pago de 1.000.000 CLP en USD", pago["monto_convertido"] == 1050.0)
comprobar("Pago en CLP no consulta la API", ServicioIndicadores(http=HttpFalso({}, error=AssertionError()))
          .calcular_pago(500, "CLP")["monto_convertido"] == 500)

# --- 3.1.2: validación de entradas antes de llamar a la API ---
http = HttpFalso({})
debe_fallar("Ciudad con caracteres peligrosos", DatoInvalidoError,
            lambda: ServicioClima(http=http).consultar("Santiago'; DROP TABLE x;--"))
debe_fallar("Ciudad vacía", DatoInvalidoError, lambda: ServicioClima(http=http).consultar("   "))
comprobar("Una entrada inválida NO llega a la API", http.llamadas == [])
debe_fallar("Moneda fuera de la lista blanca", DatoInvalidoError,
            lambda: ServicioIndicadores(http=http).calcular_pago(1000, "XYZ"))
debe_fallar("URL sin HTTPS en el .env", DatoInvalidoError, lambda: ServicioAPI("http://api.inseguro.com"))
debe_fallar("Monto negativo", DatoInvalidoError, lambda: indicadores.calcular_pago(-5, "USD"))

# --- 3.1.3: errores de red y tiempos de espera ---
for nombre, error in [("Timeout", requests.Timeout()), ("Sin conexión", requests.ConnectionError()),
                      ("Error de red genérico", requests.RequestException())]:
    debe_fallar(nombre, ServicioExternoError,
                lambda e=error: ServicioIndicadores(http=HttpFalso({}, error=e)).calcular_pago(1000, "USD"))

# --- 3.1.3: códigos HTTP ---
for codigo in (400, 401, 404, 429, 500, 503):
    debe_fallar(f"HTTP {codigo}", ServicioExternoError, lambda c=codigo: ServicioIndicadores(
        http=HttpFalso({"latest": RespuestaFalsa(c, {})})).calcular_pago(1000, "USD"))
debe_fallar("Ciudad que no existe", DatoInvalidoError, lambda: ServicioClima(
    http=HttpFalso({"geocoding": RespuestaFalsa(200, {})})).consultar("Ciudadinventada"))

# --- Respuestas mal formadas ---
debe_fallar("JSON inválido (HTML de error)", ServicioExternoError, lambda: ServicioIndicadores(
    http=HttpFalso({"latest": RespuestaFalsa(200, json_invalido=True)})).calcular_pago(1000, "USD"))
debe_fallar("JSON sin la clave esperada", ServicioExternoError, lambda: ServicioClima(
    http=HttpFalso({"geocoding": GEO_OK, "forecast": RespuestaFalsa(200, {"otra": 1})})).consultar("Lima"))
debe_fallar("API informa error en el cuerpo", ServicioExternoError, lambda: ServicioIndicadores(
    http=HttpFalso({"latest": RespuestaFalsa(200, {"result": "error"})})).calcular_pago(1000, "USD"))
debe_fallar("Tasa no numérica", ServicioExternoError, lambda: ServicioIndicadores(
    http=HttpFalso({"latest": RespuestaFalsa(200, {"result": "success", "rates": {"USD": "NaN"}})}))
    .calcular_pago(1000, "USD"))

# --- Comunicación segura de errores ---
mensaje = debe_fallar("Mensaje de error de un 500", ServicioExternoError, lambda: ServicioIndicadores(
    http=HttpFalso({"latest": RespuestaFalsa(500, {"stack": "Traceback secreto"})})).calcular_pago(1, "USD"))
comprobar("El mensaje no expone la URL ni el detalle del servidor",
          "http" not in mensaje and "Traceback" not in mensaje)

print("\nResultado:", "TODO OK" if fallos == 0 else f"{fallos} FALLA(S)")
sys.exit(1 if fallos else 0)
