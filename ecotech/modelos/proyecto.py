"""Clase Proyecto y su relación con empleados."""

import re
from datetime import date

from ecotech.excepciones import DatoInvalidoError
from ecotech.modelos._validaciones import validar_fecha, validar_texto, validar_tipo
from ecotech.modelos.empleado import Empleado

# Código ISO 4217 de moneda: tres letras mayúsculas (CLP, USD, PEN...).
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")


# IA: adoptado
class Proyecto:
    """Iniciativa de la empresa.

    Asociación N:N Proyecto 0..* — 0..* Empleado. Siguiendo la flecha del UML
    (Proyecto --> Empleado), el Proyecto guarda la lista de sus empleados asignados.
    """

    __contador_id: int = 0

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        fecha_inicio: date,
        ciudad: str = "Santiago",
        moneda: str = "CLP",
    ) -> None:
        Proyecto.__contador_id += 1
        self.__id_proyecto: int = Proyecto.__contador_id
        self.__nombre: str = validar_texto(nombre, "Nombre del proyecto")
        self.__descripcion: str = validar_texto(descripcion, "Descripción", 500)
        self.__fecha_inicio: date = validar_fecha(fecha_inicio, "Fecha de inicio")
        self.__empleados_asignados: list[Empleado] = []
        # IA: adoptado - Unidad 3: ubicación (para el clima) y moneda del país (para los pagos)
        self.__ciudad: str = validar_texto(ciudad, "Ciudad", 80)
        self.__moneda: str = self.__validar_moneda(moneda)

    @staticmethod
    def __validar_moneda(moneda: str) -> str:
        moneda = validar_texto(moneda, "Moneda", 3).upper()
        if not _PATRON_MONEDA.fullmatch(moneda):
            raise DatoInvalidoError("La moneda debe ser un código de 3 letras (ej: CLP, USD, PEN).")
        return moneda

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
    def ciudad(self) -> str:
        return self.__ciudad

    @property
    def moneda(self) -> str:
        return self.__moneda

    @property
    def empleados_asignados(self) -> list[Empleado]:
        """Devuelve una copia: la lista interna solo cambia con asignar/desasignar."""
        return list(self.__empleados_asignados)

    # IA: adoptado - integración con MySQL: el ID real lo entrega AUTO_INCREMENT
    def _fijar_id(self, nuevo_id: int) -> None:
        """Uso interno del repositorio: reemplaza el ID provisorio por el de la base de datos."""
        if isinstance(nuevo_id, bool) or not isinstance(nuevo_id, int) or nuevo_id <= 0:
            raise DatoInvalidoError("El ID debe ser un entero positivo.")
        self.__id_proyecto = nuevo_id

    # --- Asociación N:N con Empleado ---
    def esta_asignado(self, e: Empleado) -> bool:
        """UML: estaAsignado(e): boolean."""
        return e in self.__empleados_asignados

    # IA: adoptado - al leer de la BD, el mismo empleado puede llegar como otro objeto
    def buscar_asignado(self, id_empleado: int) -> Empleado | None:
        """Devuelve el empleado asignado con ese ID (el mismo objeto que guarda el proyecto)."""
        return next((e for e in self.__empleados_asignados if e.id_empleado == id_empleado), None)

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
            f"[{self.__id_proyecto}] {self.__nombre} - {self.__ciudad} ({self.__moneda})"
            f" desde {self.__fecha_inicio:%d-%m-%Y}"
            f" - {len(self.__empleados_asignados)} asignado(s)"
        )
