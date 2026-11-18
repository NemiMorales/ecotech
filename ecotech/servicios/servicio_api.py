"""Clase base para consumir APIs externas con requests."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlsplit

import requests

from ecotech.excepciones import DatoInvalidoError, ServicioExternoError

log = logging.getLogger(__name__)

# Mensajes para el usuario según el código HTTP. Son genéricos a propósito:
# no muestran la URL, los parámetros ni el cuerpo de la respuesta.
_MENSAJES_HTTP = {
    400: "la consulta enviada no es válida",
    401: "el servicio rechazó las credenciales",
    403: "el servicio negó el acceso",
    404: "no se encontró la información solicitada",
    429: "se superó el límite de consultas; intente en unos minutos",
}


# IA: adoptado
class ServicioAPI:
    """Lógica común a todas las APIs externas (herencia: Clima e Indicadores la reutilizan).

    Concentra en un solo lugar lo que pide la Unidad 3: tiempo de espera, errores de red,
    validación de códigos HTTP, JSON inválido y mensajes de error seguros.
    """

    NOMBRE = "servicio externo"

    def __init__(self, url_base: str, timeout: float | None = None, http: Any = requests) -> None:
        self._url_base = self.__validar_url(url_base)
        self._timeout = timeout if timeout is not None else self.__leer_timeout()
        self._http = http  # se puede reemplazar por un doble de prueba (sin internet)

    @staticmethod
    def __validar_url(url: str) -> str:
        """Solo HTTPS: los datos viajan cifrados y no se aceptan URLs mal escritas en el .env."""
        partes = urlsplit(url or "")
        if partes.scheme != "https" or not partes.netloc:
            raise DatoInvalidoError("La URL de la API debe comenzar con https://")
        return url.rstrip("/")

    @staticmethod
    def __leer_timeout() -> float:
        try:
            return max(1.0, float(os.getenv("API_TIMEOUT", "5")))
        except ValueError:
            return 5.0

    def _obtener_json(self, ruta: str = "", parametros: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET a la API y devuelve el JSON como diccionario, o lanza ServicioExternoError."""
        url = f"{self._url_base}/{ruta}" if ruta else self._url_base
        try:
            respuesta = self._http.get(url, params=parametros, timeout=self._timeout)
        except requests.Timeout as error:
            log.warning("%s: tiempo de espera agotado (%ss)", self.NOMBRE, self._timeout)
            raise ServicioExternoError(f"{self.NOMBRE}: el servicio no respondió a tiempo.") from error
        except requests.ConnectionError as error:
            log.warning("%s: error de conexión", self.NOMBRE)
            raise ServicioExternoError(
                f"{self.NOMBRE}: no hay conexión con el servicio. Revise su internet."
            ) from error
        except requests.RequestException as error:
            log.error("%s: error de red (%s)", self.NOMBRE, type(error).__name__)
            raise ServicioExternoError(f"{self.NOMBRE}: no fue posible completar la consulta.") from error

        self.__validar_estado(respuesta.status_code)
        try:
            datos = respuesta.json()
        except ValueError as error:  # incluye JSONDecodeError
            log.error("%s: la respuesta no es JSON", self.NOMBRE)
            raise ServicioExternoError(f"{self.NOMBRE}: el servicio respondió en un formato inválido.") from error
        if not isinstance(datos, dict):
            raise ServicioExternoError(f"{self.NOMBRE}: el servicio respondió en un formato inválido.")
        return datos

    def __validar_estado(self, codigo: int) -> None:
        """200 continúa; cualquier otro código se registra en el log y se traduce a un mensaje claro."""
        if codigo == 200:
            return
        log.warning("%s: respondió HTTP %s", self.NOMBRE, codigo)
        if 500 <= codigo <= 599:
            detalle = "el servicio no está disponible en este momento"
        else:
            detalle = _MENSAJES_HTTP.get(codigo, "respuesta inesperada del servicio")
        raise ServicioExternoError(f"{self.NOMBRE}: {detalle} (código {codigo}).")

    @staticmethod
    def _extraer(datos: dict[str, Any], *claves: str) -> Any:
        """Recorre el JSON (ej: 'current', 'temperature_2m'). Si falta algo, el formato cambió."""
        valor: Any = datos
        for clave in claves:
            if not isinstance(valor, dict) or clave not in valor:
                log.error("Formato inesperado: falta la clave '%s'", clave)
                raise ServicioExternoError("La respuesta del servicio no tiene el formato esperado.")
            valor = valor[clave]
        return valor
