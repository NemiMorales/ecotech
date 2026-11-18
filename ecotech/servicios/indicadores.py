"""Servicio de indicadores económicos: tipo de cambio para pagos internacionales.

Fuente: ExchangeRate-API, acceso abierto (no requiere llave). Sus condiciones piden
mostrar la atribución "Rates By Exchange Rate API" donde se usan las tasas.
"""

from __future__ import annotations

import math
import os
from typing import Any

import requests

from ecotech.excepciones import DatoInvalidoError, ServicioExternoError
from ecotech.modelos._validaciones import validar_positivo
from ecotech.seguridad.validador import ValidadorEntrada
from ecotech.servicios.servicio_api import ServicioAPI

ATRIBUCION = "Rates By Exchange Rate API (https://www.exchangerate-api.com)"


# IA: adoptado
class ServicioIndicadores(ServicioAPI):
    """Consulta el tipo de cambio desde el peso chileno (CLP) a la moneda del país del proyecto."""

    NOMBRE = "Servicio de tipo de cambio"
    MONEDA_BASE = "CLP"  # los salarios se registran en pesos chilenos

    def __init__(self, timeout: float | None = None, http: Any = requests) -> None:
        super().__init__(
            os.getenv("INDICADORES_API_URL", "https://open.er-api.com/v6/latest"), timeout, http
        )

    def obtener_tasa(self, moneda: str) -> dict[str, Any]:
        """Cuántas unidades de 'moneda' equivalen a 1 CLP, con la fecha de actualización."""
        moneda = ValidadorEntrada.validar_moneda(moneda)
        if moneda == self.MONEDA_BASE:
            return {"moneda": moneda, "tasa": 1.0, "actualizado": "—"}
        datos = self._obtener_json(self.MONEDA_BASE)
        if datos.get("result") != "success":
            raise ServicioExternoError(f"{self.NOMBRE}: el servicio informó un error en la consulta.")
        tasas = self._extraer(datos, "rates")
        if moneda not in tasas:
            raise DatoInvalidoError(f"El servicio no informa tasa para {moneda}.")
        tasa = tasas[moneda]
        if isinstance(tasa, bool) or not isinstance(tasa, (int, float)) or not math.isfinite(tasa) or tasa <= 0:
            raise ServicioExternoError(f"{self.NOMBRE}: la tasa recibida no es válida.")
        return {"moneda": moneda, "tasa": float(tasa), "actualizado": datos.get("time_last_update_utc", "—")}

    @staticmethod
    def convertir(monto_clp: float, datos_tasa: dict[str, Any]) -> dict[str, Any]:
        """Calcula el pago. Es estático para poder usarlo también con una tasa guardada en la BD."""
        monto_clp = validar_positivo(monto_clp, "Monto")
        return {
            "monto_clp": monto_clp,
            "moneda": datos_tasa["moneda"],
            "tasa": datos_tasa["tasa"],
            "monto_convertido": round(monto_clp * datos_tasa["tasa"], 2),
            "actualizado": datos_tasa.get("actualizado", "—"),
        }

    def calcular_pago(self, monto_clp: float, moneda: str) -> dict[str, Any]:
        """Pago ajustado al país donde se ejecuta el proyecto."""
        return self.convertir(monto_clp, self.obtener_tasa(moneda))
