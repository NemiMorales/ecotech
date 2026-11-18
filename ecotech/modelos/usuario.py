"""Clase Usuario para autenticación en el sistema."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from ecotech.excepciones import DatoInvalidoError, OperacionNoPermitidaError
from ecotech.modelos._validaciones import validar_texto, validar_tipo
from ecotech.modelos.rol import Rol
from ecotech.seguridad.cifrado import ServicioCifrado

if TYPE_CHECKING:  # Empleado importa Usuario; aquí solo se usa para type hints
    from ecotech.modelos.empleado import Empleado

# IA: adoptado
_PATRON_NOMBRE_USUARIO = re.compile(r"^[a-z0-9._]{3,30}$")
# Formato de un hash bcrypt: $2b$12$ + 53 caracteres. Rechaza contraseñas en texto plano.
_PATRON_HASH_BCRYPT = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")


# Permisos por rol (propuesta inicial, ajustar a las opciones reales del menú).
PERMISOS_POR_ROL: dict[Rol, frozenset[str]] = {
    Rol.ADMIN_RRHH: frozenset(
        {"empleados", "departamentos", "proyectos", "registros", "informes", "usuarios", "apis"}
    ),
    Rol.GERENTE: frozenset({"empleados", "proyectos", "registros", "informes", "apis"}),
    Rol.EMPLEADO: frozenset({"proyectos", "registros"}),
}


def _max_intentos() -> int:
    """Lee MAX_INTENTOS_LOGIN del .env; si falta o es inválido usa 3."""
    try:
        return max(1, int(os.getenv("MAX_INTENTOS_LOGIN", "3")))
    except ValueError:
        return 3


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
        self.__bloqueado: bool = False

    @staticmethod
    def __validar_nombre_usuario(valor: str) -> str:
        valor = validar_texto(valor, "Nombre de usuario", 30).lower()
        if not _PATRON_NOMBRE_USUARIO.fullmatch(valor):
            raise DatoInvalidoError(
                "Nombre de usuario inválido (3 a 30 caracteres: letras, números, '.' o '_')."
            )
        return valor

    @staticmethod
    def __validar_hash(valor: str) -> str:
        if not isinstance(valor, str) or not _PATRON_HASH_BCRYPT.fullmatch(valor):
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

    @property
    def bloqueado(self) -> bool:
        return self.__bloqueado

    # --- Métodos de seguridad del UML ---
    # IA: modificado - aporte de Fran; el límite de intentos se lee del .env (antes fijo en 5)
    def autenticar(self, password: str) -> bool:
        """UML: autenticar(password): boolean. Bloquea la cuenta al superar MAX_INTENTOS_LOGIN."""
        if self.__bloqueado:
            raise OperacionNoPermitidaError("La cuenta está bloqueada por intentos fallidos.")
        if ServicioCifrado.verificar_password(password, self.__password_hash):
            self.__intentos_fallidos = 0
            return True
        self.__registrar_intento_fallido()
        return False

    def __registrar_intento_fallido(self) -> None:
        self.__intentos_fallidos += 1
        if self.__intentos_fallidos >= _max_intentos():
            self.__bloqueado = True

    # IA: adoptado - aporte de Fran
    def cambiar_password(self, actual: str, nueva: str) -> bool:
        """UML: cambiarPassword(actual, nueva): boolean. Guarda solo el hash de la nueva."""
        if not self.autenticar(actual):
            return False
        if not isinstance(nueva, str) or len(nueva) < 8:
            raise DatoInvalidoError("La nueva contraseña debe tener al menos 8 caracteres.")
        if nueva == actual:
            raise DatoInvalidoError("La nueva contraseña debe ser distinta de la actual.")
        self.__password_hash = ServicioCifrado.hash_password(nueva)
        return True

    # IA: modificado - aporte de Fran; Modulo se representa como texto (decisión del equipo)
    def tiene_permiso(self, modulo: str) -> bool:
        """UML: tienePermiso(modulo: Modulo): boolean. Modulo = nombre del módulo del menú."""
        if not isinstance(modulo, str):
            return False
        return modulo.strip().lower() in PERMISOS_POR_ROL.get(self.__rol, frozenset())

    def __str__(self) -> str:
        return f"{self.__nombre_usuario} ({self.__rol}) - {self.__empleado.nombre}"
