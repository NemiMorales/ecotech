"""Clase Proyecto y su relación con empleados."""

from datetime import date

from ecotech.modelos._validaciones import validar_fecha, validar_texto, validar_tipo
from ecotech.modelos.empleado import Empleado


# IA: adoptado
class Proyecto:
    """Iniciativa de la empresa.

    Asociación N:N Proyecto 0..* — 0..* Empleado. Siguiendo la flecha del UML
    (Proyecto --> Empleado), el Proyecto guarda la lista de sus empleados asignados.
    """

    __contador_id: int = 0

    def __init__(self, nombre: str, descripcion: str, fecha_inicio: date) -> None:
        Proyecto.__contador_id += 1
        self.__id_proyecto: int = Proyecto.__contador_id
        self.__nombre: str = validar_texto(nombre, "Nombre del proyecto")
        self.__descripcion: str = validar_texto(descripcion, "Descripción", 500)
        self.__fecha_inicio: date = validar_fecha(fecha_inicio, "Fecha de inicio")
        self.__empleados_asignados: list[Empleado] = []

    # --- Accesores ---
    @property
    def id_proyecto(self) -> int:
        return self.__id_proyecto

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def descripcion(self) -> str:
        return self.__descripcion

    @property
    def fecha_inicio(self) -> date:
        return self.__fecha_inicio

    @property
    def empleados_asignados(self) -> list[Empleado]:
        """Devuelve una copia: la lista interna solo cambia con asignar/desasignar."""
        return list(self.__empleados_asignados)

    # --- Asociación N:N con Empleado ---
    def esta_asignado(self, e: Empleado) -> bool:
        """UML: estaAsignado(e): boolean."""
        return e in self.__empleados_asignados

    def asignar_empleado(self, e: Empleado) -> bool:
        """UML: asignarEmpleado(e): boolean. False si ya estaba asignado (evita duplicados)."""
        validar_tipo(e, Empleado, "Empleado")
        if self.esta_asignado(e):
            return False
        self.__empleados_asignados.append(e)
        return True

    def desasignar_empleado(self, e: Empleado) -> bool:
        """UML: desasignarEmpleado(e): boolean. False si no estaba asignado."""
        if not self.esta_asignado(e):
            return False
        self.__empleados_asignados.remove(e)
        return True

    def __str__(self) -> str:
        return (
            f"[{self.__id_proyecto}] {self.__nombre} (desde {self.__fecha_inicio:%d-%m-%Y})"
            f" - {len(self.__empleados_asignados)} asignado(s)"
        )
