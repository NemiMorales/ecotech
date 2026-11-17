"""Clase Departamento de la empresa."""

from ecotech.excepciones import OperacionNoPermitidaError
from ecotech.modelos._validaciones import validar_texto, validar_tipo
from ecotech.modelos.empleado import Empleado
from ecotech.modelos.gerente import Gerente


# IA: adoptado
class Departamento:
    """Unidad organizacional.

    - Agregación Departamento 0..1 ◇ 0..* Empleado: guarda referencias a empleados que
      existen por sí solos; eliminar el departamento NO elimina a sus empleados.
    - Asociación Departamento 0..1 → 1 Gerente: siempre tiene exactamente un gerente.
    """

    __contador_id: int = 0

    def __init__(self, nombre: str, gerente: Gerente) -> None:
        Departamento.__contador_id += 1
        self.__id_departamento: int = Departamento.__contador_id
        self.__nombre: str = validar_texto(nombre, "Nombre del departamento")
        self.__gerente: Gerente | None = None
        self.__empleados: list[Empleado] = []
        self.cambiar_gerente(gerente)  # el constructor exige gerente (RF02)

    # --- Accesores ---
    @property
    def id_departamento(self) -> int:
        return self.__id_departamento

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def gerente(self) -> Gerente:
        return self.__gerente

    @property
    def empleados(self) -> list[Empleado]:
        """UML: getEmpleados(). Devuelve una COPIA para que nadie modifique la lista interna."""
        return list(self.__empleados)

    # --- Agregación con Empleado ---
    def asignar_empleado(self, e: Empleado) -> bool:
        """UML: asignarEmpleado(e): boolean. False si ya pertenece a este u otro departamento (RF03)."""
        validar_tipo(e, Empleado, "Empleado")
        if e.departamento is not None:
            return False
        self.__empleados.append(e)
        e._asignar_departamento(self)  # mantiene la relación en ambos sentidos
        return True

    def remover_empleado(self, e: Empleado) -> bool:
        """UML: removerEmpleado(e): boolean. El empleado sigue existiendo, solo queda sin departamento."""
        if e not in self.__empleados:
            return False
        self.__empleados.remove(e)
        e._asignar_departamento(None)
        return True

    # --- Asociación con Gerente ---
    def cambiar_gerente(self, g: Gerente) -> None:
        """UML: cambiarGerente(g). Un gerente dirige a lo más un departamento."""
        validar_tipo(g, Gerente, "Gerente")
        if g is self.__gerente:
            return
        if g.departamento_a_cargo is not None:
            raise OperacionNoPermitidaError(
                f"{g.nombre} ya dirige el departamento {g.departamento_a_cargo.nombre}."
            )
        if self.__gerente is not None:
            self.__gerente._asignar_departamento_a_cargo(None)  # libera al gerente anterior
        self.__gerente = g
        g._asignar_departamento_a_cargo(self)

    def __str__(self) -> str:
        return (
            f"[{self.__id_departamento}] {self.__nombre} - Gerente: {self.__gerente.nombre}"
            f" - {len(self.__empleados)} empleado(s)"
        )
