"""Sesión del usuario autenticado: solo con una sesión activa se accede al menú y a las APIs."""

from __future__ import annotations

from datetime import datetime

from ecotech.excepciones import OperacionNoPermitidaError
from ecotech.modelos.usuario import Usuario


# IA: adoptado - aporte de Fran; se agregaron type hints y exigir_permiso()
class Sesion:
    """Representa la sesión de un usuario que ya pasó por Usuario.autenticar()."""

    def __init__(self, usuario: Usuario) -> None:
        if not isinstance(usuario, Usuario):
            raise OperacionNoPermitidaError("La sesión requiere un usuario válido.")
        self.__usuario: Usuario = usuario
        self.__fecha_inicio: datetime = datetime.now()
        self.__fecha_cierre: datetime | None = None
        self.__activa: bool = True

    @property
    def usuario(self) -> Usuario:
        return self.__usuario

    @property
    def fecha_inicio(self) -> datetime:
        return self.__fecha_inicio

    @property
    def fecha_cierre(self) -> datetime | None:
        return self.__fecha_cierre

    @property
    def activa(self) -> bool:
        return self.__activa

    def exigir_permiso(self, modulo: str) -> None:
        """Control de flujo: corta la operación si la sesión está cerrada o el rol no tiene permiso."""
        if not self.__activa:
            raise OperacionNoPermitidaError("Debe iniciar sesión para continuar.")
        if not self.__usuario.tiene_permiso(modulo):
            raise OperacionNoPermitidaError("No tiene permisos para acceder a esta opción.")

    def cerrar_sesion(self) -> None:
        if not self.__activa:
            raise OperacionNoPermitidaError("La sesión ya se encuentra cerrada.")
        self.__fecha_cierre = datetime.now()
        self.__activa = False

    def obtener_resumen(self) -> str:
        estado = "Activa" if self.__activa else "Cerrada"
        return (
            f"Usuario: {self.__usuario.nombre_usuario} ({self.__usuario.rol})\n"
            f"Inicio: {self.__fecha_inicio:%d-%m-%Y %H:%M}\n"
            f"Estado: {estado}"
        )

    def __str__(self) -> str:
        return self.obtener_resumen()
