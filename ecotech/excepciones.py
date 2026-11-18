"""Excepciones personalizadas del sistema."""


# IA: adoptado
class EcoTechError(Exception):
    """Excepción base del sistema: permite capturar todos los errores propios con un solo except."""


class DatoInvalidoError(EcoTechError, ValueError):
    """Un dato no cumple las reglas del modelo (texto vacío, salario <= 0, horas fuera de rango...).

    Hereda también de ValueError para que un ``except ValueError`` la siga capturando.
    """


class OperacionNoPermitidaError(EcoTechError):
    """Se intenta una operación que rompe una regla de negocio (ej: gerente que ya dirige otro departamento)."""


# IA: adoptado - Unidad 2 (BD) y Unidad 3 (APIs)
class BaseDatosError(EcoTechError):
    """Falla de conexión o de consulta en MySQL. El mensaje es seguro para mostrar al usuario."""


class ServicioExternoError(EcoTechError):
    """Falla al consumir una API externa (red, tiempo de espera, código HTTP o JSON inválido)."""
