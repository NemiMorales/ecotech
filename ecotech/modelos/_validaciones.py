"""Validaciones básicas reutilizadas por todas las clases del modelo (evita duplicar reglas)."""

import re
from datetime import date

from ecotech.excepciones import DatoInvalidoError

# IA: adoptado
_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PATRON_TELEFONO = re.compile(r"^\+?[0-9 ]{8,15}$")


def validar_texto(valor: str, campo: str, max_largo: int = 100) -> str:
    """Devuelve el texto sin espacios extremos; falla si no es str, está vacío o es muy largo."""
    if not isinstance(valor, str) or not valor.strip():
        raise DatoInvalidoError(f"{campo} no puede estar vacío.")
    valor = valor.strip()
    if len(valor) > max_largo:
        raise DatoInvalidoError(f"{campo} no puede superar {max_largo} caracteres.")
    return valor


def validar_email(valor: str) -> str:
    """Valida el formato básico usuario@dominio.ext."""
    valor = validar_texto(valor, "Email", 120)
    if not _PATRON_EMAIL.match(valor):
        raise DatoInvalidoError("Email con formato inválido.")
    return valor.lower()


def validar_telefono(valor: str) -> str:
    """Acepta entre 8 y 15 dígitos, con '+' inicial y espacios opcionales."""
    valor = validar_texto(valor, "Teléfono", 20)
    if not _PATRON_TELEFONO.match(valor):
        raise DatoInvalidoError("Teléfono inválido (8 a 15 dígitos).")
    return valor


def validar_positivo(valor: float, campo: str) -> float:
    """Valida que sea un número mayor que 0 (bool se rechaza aunque sea subclase de int)."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise DatoInvalidoError(f"{campo} debe ser numérico.")
    if valor <= 0:
        raise DatoInvalidoError(f"{campo} debe ser mayor que 0.")
    return float(valor)


def validar_fecha(valor: date, campo: str) -> date:
    """Valida que el valor sea un objeto date (no un texto)."""
    if not isinstance(valor, date):
        raise DatoInvalidoError(f"{campo} debe ser una fecha (datetime.date).")
    return valor


def validar_tipo(valor: object, tipo: type, campo: str) -> object:
    """Valida que una referencia a otro objeto sea del tipo esperado por el UML."""
    if not isinstance(valor, tipo):
        raise DatoInvalidoError(f"{campo} debe ser de tipo {tipo.__name__}.")
    return valor
