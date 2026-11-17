"""Prueba manual del modelo POO: crea objetos de cada clase y verifica relaciones y validaciones.

Ejecutar desde la raíz del repo:  python -m tests.prueba_modelo
"""

import base64
import sys
from datetime import date

import bcrypt

from ecotech.excepciones import DatoInvalidoError, OperacionNoPermitidaError
from ecotech.modelos.departamento import Departamento
from ecotech.modelos.empleado import Empleado
from ecotech.modelos.gerente import Gerente
from ecotech.modelos.persona import Persona
from ecotech.modelos.proyecto import Proyecto
from ecotech.modelos.registro_tiempo import RegistroTiempo
from ecotech.modelos.rol import Rol


# IA: adoptado
class CifradoDePrueba:
    """Doble de prueba de ServicioCifrado (aún no implementado). Base64 NO es cifrado real."""

    def cifrar(self, dato: str) -> str:
        return base64.b64encode(dato.encode()).decode()

    def descifrar(self, dato: str) -> str:
        return base64.b64decode(dato.encode()).decode()


fallos = 0


def comprobar(descripcion: str, condicion: bool) -> None:
    global fallos
    print(f"[{'OK' if condicion else 'FALLA'}] {descripcion}")
    if not condicion:
        fallos += 1


def debe_fallar(descripcion: str, excepcion: type, funcion) -> None:
    try:
        funcion()
    except excepcion as e:
        comprobar(f"{descripcion} -> {type(e).__name__}: {e}", True)
    else:
        comprobar(f"{descripcion} (no lanzó {excepcion.__name__})", False)


c = CifradoDePrueba()

print("\n== Herencia y abstracción ==")
debe_fallar("Persona no se puede instanciar", TypeError,
            lambda: Persona("A", "B", "+56911111111", "a@b.cl"))
camila = Empleado("Camila Rojas", "Av. Siempre Viva 123", "+56 9 1234 5678",
                  "crojas@ecotech.cl", date(2024, 3, 1), 950000, c)
pedro = Empleado("Pedro Soto", "Los Olmos 45", "+56987654321",
                 "psoto@ecotech.cl", date(2025, 1, 15), 800000, c)
ana = Gerente("Ana Díaz", "Calle Uno 1", "+56922223333",
              "adiaz@ecotech.cl", date(2020, 6, 1), 2500000, c)
comprobar("Gerente es Empleado y Persona", isinstance(ana, Empleado) and isinstance(ana, Persona))
comprobar("IDs automáticos únicos", len({camila.id_empleado, pedro.id_empleado, ana.id_empleado}) == 3)
print("  ", camila)
print("  ", ana)

print("\n== Encapsulamiento ==")
comprobar("Salario guardado cifrado y legible solo con el servicio", camila.get_salario(c) == 950000)
comprobar("No existe atributo público 'salario'", not hasattr(camila, "salario"))
debe_fallar("No se puede asignar el ID", AttributeError, lambda: setattr(camila, "id_empleado", 99))
debe_fallar("Salario negativo", DatoInvalidoError, lambda: camila.actualizar_salario(-100, c))
debe_fallar("Salario 0 se captura también como ValueError", ValueError, lambda: camila.actualizar_salario(0, c))
debe_fallar("Nombre vacío", DatoInvalidoError,
            lambda: Empleado("  ", "Dir", "+56911111111", "x@y.cl", date.today(), 1000, c))
debe_fallar("Email inválido", DatoInvalidoError, lambda: camila.actualizar_contacto("+56911111111", "sin-arroba"))
debe_fallar("Fecha como texto", DatoInvalidoError,
            lambda: Empleado("X", "Dir", "+56911111111", "x@y.cl", "2024-01-01", 1000, c))

print("\n== Departamento (agregación) y Gerente (asociación) ==")
ventas = Departamento("Ventas", ana)
comprobar("El gerente conoce su departamento", ana.departamento_a_cargo is ventas)
comprobar("Asignar empleado", ventas.asignar_empleado(camila))
comprobar("Empleado conoce su departamento", camila.departamento is ventas)
idi = Departamento("Investigación y Desarrollo", Gerente(
    "Luis Paz", "Calle Dos 2", "+56933334444", "lpaz@ecotech.cl", date(2021, 1, 1), 2400000, c))
comprobar("No puede estar en dos departamentos (RF03)", idi.asignar_empleado(camila) is False)
debe_fallar("Un gerente no dirige dos departamentos", OperacionNoPermitidaError,
            lambda: Departamento("Recursos Humanos", ana))
copia = ventas.empleados
copia.clear()
comprobar("La lista expuesta es una copia", len(ventas.empleados) == 1)
comprobar("Remover empleado", ventas.remover_empleado(camila) and camila.departamento is None)
comprobar("El empleado sigue existiendo y se reasigna", idi.asignar_empleado(camila))
print("  ", ventas)
print("  ", idi)

print("\n== Proyecto (asociación N:N) ==")
solar = Proyecto("Planta Solar Rancagua", "Instalación de paneles", date(2026, 1, 10))
eolico = Proyecto("Parque Eólico", "Estudio de factibilidad", date(2026, 3, 1))
comprobar("Asignar a un proyecto", solar.asignar_empleado(camila))
comprobar("No se duplica la asignación", solar.asignar_empleado(camila) is False)
comprobar("Un empleado en varios proyectos", eolico.asignar_empleado(camila))
comprobar("Un proyecto con varios empleados", solar.asignar_empleado(pedro) and len(solar.empleados_asignados) == 2)
print("  ", solar)

print("\n== RegistroTiempo (asociación, trazabilidad) ==")
reg = RegistroTiempo(camila, solar, date(2026, 10, 15), 6, "Levantamiento de requisitos")
comprobar("Registro guarda empleado y proyecto", reg.empleado is camila and reg.proyecto is solar)
debe_fallar("Horas > 24", DatoInvalidoError,
            lambda: RegistroTiempo(camila, solar, date.today(), 25, "Turno"))
debe_fallar("Horas = 0", DatoInvalidoError,
            lambda: RegistroTiempo(camila, solar, date.today(), 0, "Nada"))
debe_fallar("Empleado no asignado al proyecto", OperacionNoPermitidaError,
            lambda: RegistroTiempo(pedro, eolico, date.today(), 4, "Visita"))
solar.desasignar_empleado(camila)
comprobar("El registro se conserva tras desasignar", reg.proyecto is solar and reg.horas == 6)
print("  ", reg)

print("\n== Usuario (composición) y Rol ==")
hash_ok = bcrypt.hashpw(b"ClaveDePrueba123", bcrypt.gensalt()).decode()
u = camila.crear_usuario("crojas", hash_ok, Rol.EMPLEADO)
comprobar("El empleado es dueño de su usuario", camila.usuario is u and u.empleado is camila)
debe_fallar("Solo un usuario por empleado (0..1)", OperacionNoPermitidaError,
            lambda: camila.crear_usuario("otro", hash_ok, Rol.EMPLEADO))
debe_fallar("Contraseña en texto plano rechazada", DatoInvalidoError,
            lambda: pedro.crear_usuario("psoto", "ClaveDePrueba123", Rol.EMPLEADO))
debe_fallar("Rol inválido", DatoInvalidoError,
            lambda: pedro.crear_usuario("psoto", hash_ok, "ADMIN"))
comprobar("El hash no se expone", not hasattr(u, "password_hash"))
print("  ", u)

print(f"\nResultado: {'TODO OK' if fallos == 0 else f'{fallos} prueba(s) fallaron'}")
sys.exit(1 if fallos else 0)
