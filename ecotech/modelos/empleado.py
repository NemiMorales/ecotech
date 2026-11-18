"""Clase Empleado, hereda de Persona."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from ecotech.excepciones import DatoInvalidoError, OperacionNoPermitidaError
from ecotech.modelos._validaciones import validar_fecha, validar_positivo
from ecotech.modelos.persona import Persona
from ecotech.modelos.rol import Rol
from ecotech.modelos.usuario import Usuario

if TYPE_CHECKING:  # solo para type hints, evita importaciones circulares
    from ecotech.modelos.departamento import Departamento
    from ecotech.seguridad.cifrado import ServicioCifrado


# IA: adoptado
class Empleado(Persona):
    """Trabajador de EcoTech (UML: Empleado hereda de Persona)."""

    # UML: -contadorId: int <<static>>. Atributo de clase compartido por todas las instancias.
    __contador_id: int = 0

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
        super().__init__(nombre, direccion, telefono, email)  # reutiliza validaciones de Persona
        Empleado.__contador_id += 1
        self.__id_empleado: int = Empleado.__contador_id  # sin setter: no se puede manipular
        self.__fecha_inicio_contrato: date = validar_fecha(fecha_inicio, "Fecha de inicio")
        self.__salario_cifrado: str = ""
        self.__departamento: Departamento | None = None
        self.__usuario: Usuario | None = None
        self.actualizar_salario(salario, cifrado)  # el salario nunca se guarda en texto plano

    # --- Accesores ---
    @property
    def id_empleado(self) -> int:
        return self.__id_empleado

    @property
    def fecha_inicio_contrato(self) -> date:
        return self.__fecha_inicio_contrato

    @property
    def departamento(self) -> Departamento | None:
        return self.__departamento

    @property
    def usuario(self) -> Usuario | None:
        return self.__usuario

    # IA: adoptado - integración con MySQL: el ID real lo entrega AUTO_INCREMENT
    def _fijar_id(self, nuevo_id: int) -> None:
        """Uso interno del repositorio: reemplaza el ID provisorio por el de la base de datos."""
        if isinstance(nuevo_id, bool) or not isinstance(nuevo_id, int) or nuevo_id <= 0:
            raise DatoInvalidoError("El ID debe ser un entero positivo.")
        self.__id_empleado = nuevo_id

    # --- Salario protegido: solo se lee/modifica a través de ServicioCifrado ---
    def get_salario(self, cifrado: ServicioCifrado) -> float:
        """UML: getSalario(c: ServicioCifrado): double."""
        return float(cifrado.descifrar(self.__salario_cifrado))

    def actualizar_salario(self, monto: float, cifrado: ServicioCifrado) -> None:
        """UML: actualizarSalario(monto, c). Valida monto > 0 y lo guarda cifrado."""
        monto = validar_positivo(monto, "Salario")
        self.__salario_cifrado = cifrado.cifrar(str(monto))

    # --- Agregación con Departamento (lo llama solo Departamento) ---
    def _asignar_departamento(self, departamento: Departamento | None) -> None:
        """Uso interno: Departamento lo invoca para mantener la relación en ambos sentidos."""
        self.__departamento = departamento

    # --- Composición Empleado 1 ◆ 0..1 Usuario ---
    def crear_usuario(self, nombre_usuario: str, password_hash: str, rol: Rol) -> Usuario:
        """El Empleado crea y es dueño de su Usuario (máximo uno)."""
        if self.__usuario is not None:
            raise OperacionNoPermitidaError("El empleado ya tiene una cuenta de usuario.")
        self.__usuario = Usuario(self, nombre_usuario, password_hash, rol)
        return self.__usuario

    def obtener_resumen(self) -> str:
        """UML: obtenerResumen(). Implementa el método abstracto de Persona."""
        depto = self.__departamento.nombre if self.__departamento else "Sin departamento"
        return f"[{self.__id_empleado}] {self.nombre} <{self.email}> - Depto: {depto}"
