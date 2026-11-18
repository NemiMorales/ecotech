"""Clase RegistroTiempo para horas trabajadas por empleado."""

from datetime import date

from ecotech.excepciones import DatoInvalidoError, OperacionNoPermitidaError
from ecotech.modelos._validaciones import validar_fecha, validar_texto, validar_tipo
from ecotech.modelos.empleado import Empleado
from ecotech.modelos.proyecto import Proyecto


# IA: adoptado
class RegistroTiempo:
    """Declaración de horas de un empleado en un proyecto y una fecha.

    Asociación RegistroTiempo 0..* → 1 Empleado y 0..* → 1 Proyecto (NO composición):
    si el empleado o el proyecto cambian, el registro se conserva para la trazabilidad.
    Todos los datos se fijan en el constructor y no tienen setter.
    """

    __contador_id: int = 0
    HORAS_MAXIMAS_DIA: float = 24

    def __init__(self, e: Empleado, p: Proyecto, fecha: date, horas: float, desc: str) -> None:
        validar_tipo(e, Empleado, "Empleado")
        validar_tipo(p, Proyecto, "Proyecto")
        if not p.esta_asignado(e):
            raise OperacionNoPermitidaError(
                f"{e.nombre} no está asignado al proyecto {p.nombre}."
            )
        if not self.__validar_horas(horas):
            raise DatoInvalidoError(
                f"Las horas deben ser mayores que 0 y como máximo {self.HORAS_MAXIMAS_DIA}."
            )
        RegistroTiempo.__contador_id += 1
        self.__id_registro: int = RegistroTiempo.__contador_id
        self.__empleado: Empleado = e
        self.__proyecto: Proyecto = p
        self.__fecha: date = validar_fecha(fecha, "Fecha")
        self.__horas: float = float(horas)
        self.__descripcion: str = validar_texto(desc, "Descripción", 255)

    def __validar_horas(self, horas: float) -> bool:
        """UML: -validarHoras(horas): boolean (privado). Rechaza valores <= 0 o > 24 (RF04)."""
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            return False
        return 0 < horas <= self.HORAS_MAXIMAS_DIA

    # IA: adoptado - integración con MySQL: el ID real lo entrega AUTO_INCREMENT
    def _fijar_id(self, nuevo_id: int) -> None:
        """Uso interno del repositorio: reemplaza el ID provisorio por el de la base de datos."""
        if isinstance(nuevo_id, bool) or not isinstance(nuevo_id, int) or nuevo_id <= 0:
            raise DatoInvalidoError("El ID debe ser un entero positivo.")
        self.__id_registro = nuevo_id

    # --- Accesores (solo lectura) ---
    @property
    def id_registro(self) -> int:
        return self.__id_registro

    @property
    def horas(self) -> float:
        """UML: getHoras(): double."""
        return self.__horas

    @property
    def fecha(self) -> date:
        return self.__fecha

    @property
    def descripcion(self) -> str:
        return self.__descripcion

    @property
    def empleado(self) -> Empleado:
        return self.__empleado

    @property
    def proyecto(self) -> Proyecto:
        return self.__proyecto

    def __str__(self) -> str:
        return (
            f"[{self.__id_registro}] {self.__fecha:%d-%m-%Y} - {self.__empleado.nombre}"
            f" - {self.__proyecto.nombre}: {self.__horas:g} h ({self.__descripcion})"
        )
