"""Clase base Persona con los datos comunes."""

from abc import ABC, abstractmethod

from ecotech.modelos._validaciones import (
    validar_email,
    validar_telefono,
    validar_texto,
)


# IA: adoptado
class Persona(ABC):
    """Clase abstracta (UML: <<abstract>> Persona) con los datos de contacto comunes.

    No se puede instanciar directamente: solo existen Empleado y Gerente.
    """

    def __init__(self, nombre: str, direccion: str, telefono: str, email: str) -> None:
        # Atributos privados (-): Python los renombra a _Persona__nombre, etc.
        self.__nombre: str = validar_texto(nombre, "Nombre")
        self.__direccion: str = validar_texto(direccion, "Dirección", 150)
        self.__telefono: str = validar_telefono(telefono)
        self.__email: str = validar_email(email)

    # --- Accesores (UML: getNombre(), getEmail()) ---
    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def direccion(self) -> str:
        return self.__direccion

    @property
    def telefono(self) -> str:
        return self.__telefono

    @property
    def email(self) -> str:
        return self.__email

    # --- Único punto de modificación de los datos de contacto ---
    def actualizar_contacto(self, telefono: str, email: str) -> None:
        """UML: actualizarContacto(telefono, email). Valida ambos antes de cambiar nada."""
        telefono_valido = validar_telefono(telefono)
        email_valido = validar_email(email)
        self.__telefono = telefono_valido
        self.__email = email_valido

    @abstractmethod
    def obtener_resumen(self) -> str:
        """UML: obtenerResumen() <<abstracto>>. Cada subclase define su propio resumen."""

    def __str__(self) -> str:
        # Polimorfismo: usa el obtener_resumen() de la subclase real (Empleado o Gerente).
        return self.obtener_resumen()
