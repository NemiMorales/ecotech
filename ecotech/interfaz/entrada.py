"""Lectura de datos por consola: pregunta hasta recibir un valor válido (nunca se cae)."""

from __future__ import annotations

import getpass
import re
import sys
from collections.abc import Callable
from datetime import date, datetime
from typing import TypeVar

from ecotech.excepciones import DatoInvalidoError
from ecotech.seguridad.validador import ValidadorEntrada

T = TypeVar("T")
_MILES_CON_PUNTO = re.compile(r"^\d{1,3}(\.\d{3})+$")


# IA: adoptado
def pedir(mensaje: str, convertir: Callable[[str], T]) -> T:
    """Repite la pregunta mientras el dato no sea válido; muestra el motivo del rechazo."""
    while True:
        try:
            return convertir(input(mensaje))
        except DatoInvalidoError as error:
            print(f"   ⚠ {error}")


def texto(mensaje: str, campo: str, max_largo: int = 100) -> str:
    return pedir(mensaje, lambda v: ValidadorEntrada.validar_texto(v, campo, max_largo))


def entero(mensaje: str, minimo: int = 0) -> int:
    def convertir(valor: str) -> int:
        valor = ValidadorEntrada.sanitizar(valor)
        if not valor.isdigit() or int(valor) < minimo:
            raise DatoInvalidoError(f"Ingrese un número entero mayor o igual a {minimo}.")
        return int(valor)
    return pedir(mensaje, convertir)


def decimal(mensaje: str) -> float:
    def convertir(valor: str) -> float:
        limpio = ValidadorEntrada.sanitizar(valor)
        # Formato chileno: "850.000" son miles y "7,5" es decimal.
        if _MILES_CON_PUNTO.fullmatch(limpio.split(",")[0]):
            limpio = limpio.replace(".", "")
        limpio = limpio.replace(",", ".")
        try:
            return float(limpio)
        except ValueError as error:
            raise DatoInvalidoError("Ingrese un número (ej: 850.000 o 7,5).") from error
    return pedir(mensaje, convertir)


def fecha(mensaje: str) -> date:
    def convertir(valor: str) -> date:
        try:
            return datetime.strptime(ValidadorEntrada.sanitizar(valor), "%d-%m-%Y").date()
        except ValueError as error:
            raise DatoInvalidoError("Use el formato dd-mm-aaaa (ej: 18-11-2026).") from error
    return pedir(mensaje, convertir)


def confirmar(mensaje: str) -> bool:
    def convertir(valor: str) -> bool:
        valor = ValidadorEntrada.sanitizar(valor).lower()
        if valor not in ("s", "n"):
            raise DatoInvalidoError("Responda s o n.")
        return valor == "s"
    return pedir(f"{mensaje} (s/n): ", convertir)


def password(mensaje: str) -> str:
    """En una terminal real no se muestra lo que se escribe (getpass)."""
    return getpass.getpass(mensaje) if sys.stdin.isatty() else input(mensaje)
