"""Clase Gerente, hereda de Empleado."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from ecotech.modelos.empleado import Empleado

if TYPE_CHECKING:
    from ecotech.modelos.departamento import Departamento
    from ecotech.seguridad.cifrado import ServicioCifrado


# IA: adoptado
class Gerente(Empleado):
    """Empleado especializado que dirige un departamento (UML: Gerente hereda de Empleado)."""

    def __init__(
        self,
        nombre: str,
        direccion: str,
        telefono: str,
        email: str,
        fecha_inicio: date,
        salario: float,
        cifrado: ServicioCifrado,
    ) -> None:
        # Reutiliza todo Empleado (validaciones, ID automático, salario cifrado).
        super().__init__(nombre, direccion, telefono, email, fecha_inicio, salario, cifrado)
        # Lo fija Departamento, no se recibe por parámetro (relación 0..1 — 1).
        self.__departamento_a_cargo: Departamento | None = None

    @property
    def departamento_a_cargo(self) -> Departamento | None:
        """UML: getDepartamentoACargo(): Departamento."""
        return self.__departamento_a_cargo

    def _asignar_departamento_a_cargo(self, departamento: Departamento | None) -> None:
        """Uso interno: lo invoca Departamento al crearse o al cambiar de gerente."""
        self.__departamento_a_cargo = departamento

    def obtener_resumen(self) -> str:
        """UML: obtenerResumen() redefinido (polimorfismo): agrega el departamento a cargo."""
        a_cargo = self.__departamento_a_cargo.nombre if self.__departamento_a_cargo else "ninguno"
        return f"{super().obtener_resumen()} | Gerente de: {a_cargo}"
