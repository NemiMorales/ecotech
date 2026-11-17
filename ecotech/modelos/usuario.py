"""Clase Usuario para autenticación en el sistema."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ecotech.excepciones import DatoInvalidoError
from ecotech.modelos._validaciones import validar_texto, validar_tipo
from ecotech.modelos.rol import Rol

if TYPE_CHECKING:  # Empleado importa Usuario; aquí solo se usa para type hints
    from ecotech.modelos.empleado import Empleado

# IA: adoptado
_PATRON_NOMBRE_USUARIO = re.compile(r"^[a-z0-9._]{3,30}$")
# Formato de un hash bcrypt: $2b$12$ + 53 caracteres. Rechaza contraseñas en texto plano.
_PATRON_HASH_BCRYPT = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")


# IA: adoptado
class Usuario:
    """Cuenta de acceso de un empleado.

    Composición Empleado 1 ◆ 0..1 Usuario: NO se crea directamente, se crea con
    ``empleado.crear_usuario(...)``; el Usuario no tiene sentido sin su Empleado.
    Guarda solo el hash de la contraseña, nunca el texto plano.
    """

    def __init__(self, empleado: Empleado, nombre_usuario: str, password_hash: str, rol: Rol) -> None:
        self.__empleado: Empleado = empleado
        self.__nombre_usuario: str = self.__validar_nombre_usuario(nombre_usuario)
        self.__password_hash: str = self.__validar_hash(password_hash)
        self.__rol: Rol = validar_tipo(rol, Rol, "Rol")
        self.__intentos_fallidos: int = 0

    @staticmethod
    def __validar_nombre_usuario(valor: str) -> str:
        valor = validar_texto(valor, "Nombre de usuario", 30).lower()
        if not _PATRON_NOMBRE_USUARIO.match(valor):
            raise DatoInvalidoError(
                "Nombre de usuario inválido (3 a 30 caracteres: letras, números, '.' o '_')."
            )
        return valor

    @staticmethod
    def __validar_hash(valor: str) -> str:
        if not isinstance(valor, str) or not _PATRON_HASH_BCRYPT.match(valor):
            raise DatoInvalidoError("La contraseña debe llegar como hash bcrypt, nunca en texto plano.")
        return valor

    # --- Accesores (no existe accesor para el hash: no se expone) ---
    @property
    def nombre_usuario(self) -> str:
        return self.__nombre_usuario

    @property
    def rol(self) -> Rol:
        return self.__rol

    @property
    def intentos_fallidos(self) -> int:
        return self.__intentos_fallidos

    @property
    def empleado(self) -> Empleado:
        return self.__empleado

    # --- Métodos de seguridad del UML: se implementan junto con seguridad/cifrado.py ---
    def autenticar(self, password: str) -> bool:
        """UML: autenticar(password): boolean."""
        # TODO: comparar con bcrypt.checkpw contra self.__password_hash y sumar intentos fallidos.
        raise NotImplementedError("Pendiente: se implementa con ServicioCifrado.")

    def cambiar_password(self, actual: str, nueva: str) -> bool:
        """UML: cambiarPassword(actual, nueva): boolean."""
        # TODO: verificar 'actual' con el hash y guardar el hash de 'nueva' (nunca el texto).
        raise NotImplementedError("Pendiente: se implementa con ServicioCifrado.")

    def tiene_permiso(self, modulo: str) -> bool:
        """UML: tienePermiso(modulo: Modulo): boolean."""
        # TODO: el tipo Modulo no está definido en el UML; decidir con el equipo cómo representarlo.
        raise NotImplementedError("Pendiente: definir el tipo Modulo.")

    def __str__(self) -> str:
        return f"{self.__nombre_usuario} ({self.__rol}) - {self.__empleado.nombre}"
