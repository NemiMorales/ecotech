"""Validación y saneamiento de entradas del usuario (UML: ValidadorEntrada)."""

import re

from ecotech.excepciones import DatoInvalidoError
from ecotech.modelos._validaciones import validar_email, validar_telefono, validar_texto

# Caracteres de control (no imprimibles) que no deberían llegar a la BD ni a una API.
_CARACTERES_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# IA: adoptado - aporte de Fran; reutiliza las reglas de modelos/_validaciones.py
class ValidadorEntrada:
    """Punto único para validar lo que escribe el usuario en el menú.

    Reutiliza las reglas del modelo (no las duplica) y agrega el saneamiento de texto.
    """

    @staticmethod
    def sanitizar(valor: str) -> str:
        """Quita espacios exteriores y caracteres de control."""
        if not isinstance(valor, str):
            raise DatoInvalidoError("El valor a sanitizar debe ser texto.")
        return _CARACTERES_CONTROL.sub("", valor.strip())

    @staticmethod
    def validar_texto(valor: str, campo: str = "Texto", max_largo: int = 100) -> str:
        return validar_texto(ValidadorEntrada.sanitizar(valor), campo, max_largo)

    @staticmethod
    def validar_email(email: str) -> str:
        return validar_email(ValidadorEntrada.sanitizar(email))

    @staticmethod
    def validar_telefono(telefono: str) -> str:
        return validar_telefono(ValidadorEntrada.sanitizar(telefono))

    @staticmethod
    def validar_credenciales(nombre_usuario: str, password: str) -> tuple[str, str]:
        """Login: rechaza valores vacíos antes de consultar la BD (criterio 3.1.2)."""
        nombre = ValidadorEntrada.sanitizar(nombre_usuario or "")
        if not nombre or not isinstance(password, str) or not password:
            raise DatoInvalidoError("Usuario y contraseña son obligatorios.")
        return nombre.lower(), password
