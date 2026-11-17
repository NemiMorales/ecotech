"""Definición de roles y permisos de usuario."""

from enum import Enum


# IA: adoptado
class Rol(Enum):
    """Conjunto cerrado de roles del sistema (UML: <<enumeration>> Rol).

    El administrador es un rol de Usuario, no una subclase de Persona.
    """

    ADMIN_RRHH = "ADMIN_RRHH"
    GERENTE = "GERENTE"
    EMPLEADO = "EMPLEADO"

    def __str__(self) -> str:
        """Texto legible para mostrar en el menú."""
        return self.name.replace("_", " ").title()
