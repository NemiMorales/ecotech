"""Validación y saneamiento de entradas del usuario (UML: ValidadorEntrada)."""

import re

from ecotech.excepciones import DatoInvalidoError
from ecotech.modelos._validaciones import validar_email, validar_telefono, validar_texto

# Ciudad: letras (con tildes y ñ), espacios, punto, apóstrofo y guion. Nada de ; " < > ni números.
_PATRON_CIUDAD = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]{2,80}$")
# Monedas aceptadas para pagos internacionales (lista blanca, ISO 4217).
MONEDAS_PERMITIDAS = frozenset({"CLP", "USD", "EUR", "PEN", "ARS", "BRL", "COP", "MXN", "BOB", "UYU"})

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

    # IA: adoptado - Unidad 3: entradas que se envían a las APIs externas
    @staticmethod
    def validar_ciudad(ciudad: str) -> str:
        """Ciudad para la API de clima: solo letras y separadores comunes (2 a 80 caracteres)."""
        ciudad = " ".join(ValidadorEntrada.sanitizar(ciudad or "").split())
        if not _PATRON_CIUDAD.fullmatch(ciudad):
            raise DatoInvalidoError("Ciudad inválida: use solo letras y espacios (2 a 80 caracteres).")
        return ciudad

    @staticmethod
    def validar_moneda(moneda: str) -> str:
        """Moneda para la API de tipo de cambio: debe estar en la lista blanca."""
        moneda = ValidadorEntrada.sanitizar(moneda or "").upper()
        if moneda not in MONEDAS_PERMITIDAS:
            permitidas = ", ".join(sorted(MONEDAS_PERMITIDAS))
            raise DatoInvalidoError(f"Moneda no permitida. Opciones: {permitidas}.")
        return moneda

    @staticmethod
    def validar_credenciales(nombre_usuario: str, password: str) -> tuple[str, str]:
        """Login: rechaza valores vacíos antes de consultar la BD (criterio 3.1.2)."""
        nombre = ValidadorEntrada.sanitizar(nombre_usuario or "")
        if not nombre or not isinstance(password, str) or not password:
            raise DatoInvalidoError("Usuario y contraseña son obligatorios.")
        return nombre.lower(), password
