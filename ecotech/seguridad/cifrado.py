"""Cifrado reversible de datos sensibles (Fernet) y hash de contraseñas (bcrypt)."""

from __future__ import annotations

import os

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from ecotech.excepciones import DatoInvalidoError

# bcrypt solo considera los primeros 72 bytes de la contraseña: sobre eso se rechaza.
_MAX_BYTES_BCRYPT = 72


# IA: modificado - aporte de Fran; se movió a seguridad/ y se agregó desde_entorno()
class ServicioCifrado:
    """UML: ServicioCifrado (módulo Seguridad).

    - Salario y otros datos que se deben RECUPERAR: cifrado reversible con Fernet (clave secreta).
    - Contraseñas, que NUNCA se recuperan: hash de una vía con bcrypt (incluye salt).
    """

    def __init__(self, clave: bytes) -> None:
        if not isinstance(clave, bytes):
            raise DatoInvalidoError("La clave de cifrado debe ser de tipo bytes.")
        try:
            self.__cifrador = Fernet(clave)
        except (ValueError, TypeError) as error:
            raise DatoInvalidoError("La clave de cifrado no es válida.") from error

    @classmethod
    def desde_entorno(cls, variable: str = "FERNET_KEY") -> ServicioCifrado:
        """Crea el servicio leyendo la clave desde el .env (nunca escrita en el código)."""
        clave = os.getenv(variable)
        if not clave:
            raise DatoInvalidoError(f"Falta la variable {variable} en el archivo .env.")
        return cls(clave.encode("utf-8"))

    @staticmethod
    def generar_clave() -> bytes:
        """Genera una clave Fernet nueva. Se ejecuta UNA vez y se guarda en el .env."""
        return Fernet.generate_key()

    # --- Cifrado reversible (salario) ---
    def cifrar(self, dato: str) -> str:
        """Cifra un texto y devuelve el token como str."""
        if not isinstance(dato, str) or not dato:
            raise DatoInvalidoError("El dato a cifrar no puede estar vacío.")
        return self.__cifrador.encrypt(dato.encode("utf-8")).decode("utf-8")

    def descifrar(self, dato_cifrado: str) -> str:
        """Descifra un token Fernet. Falla si la clave no corresponde o el token fue alterado."""
        if not isinstance(dato_cifrado, str) or not dato_cifrado:
            raise DatoInvalidoError("El dato cifrado no puede estar vacío.")
        try:
            return self.__cifrador.decrypt(dato_cifrado.encode("utf-8")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError) as error:
            # Mensaje genérico: no se revela si falló la clave o el dato.
            raise DatoInvalidoError("No fue posible descifrar el dato.") from error

    # --- Hash de contraseñas ---
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash bcrypt con salt aleatorio."""
        if not isinstance(password, str) or not password:
            raise DatoInvalidoError("La contraseña no puede estar vacía.")
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > _MAX_BYTES_BCRYPT:
            raise DatoInvalidoError("La contraseña no puede superar los 72 bytes.")
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verificar_password(password: str, password_hash: str) -> bool:
        """Compara una contraseña con su hash. Ante cualquier dato raro responde False."""
        if not isinstance(password, str) or not isinstance(password_hash, str):
            return False
        try:
            password_bytes = password.encode("utf-8")
            if len(password_bytes) > _MAX_BYTES_BCRYPT:
                return False
            return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
        except (ValueError, TypeError, UnicodeEncodeError):
            return False
