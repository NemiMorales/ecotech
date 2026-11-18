"""Prueba manual de la capa de seguridad: cifrado, login con bloqueo, permisos y sesión.

Ejecutar desde la raíz del repo:  python -m tests.prueba_seguridad
"""

import os
import sys
from datetime import date

from ecotech.excepciones import DatoInvalidoError, OperacionNoPermitidaError
from ecotech.modelos.departamento import Departamento
from ecotech.modelos.empleado import Empleado
from ecotech.modelos.gerente import Gerente
from ecotech.modelos.rol import Rol
from ecotech.seguridad.cifrado import ServicioCifrado
from ecotech.seguridad.sesion import Sesion
from ecotech.seguridad.validador import ValidadorEntrada

os.environ["MAX_INTENTOS_LOGIN"] = "3"
fallos = 0


def comprobar(descripcion: str, condicion: bool) -> None:
    global fallos
    print(f"[{'OK' if condicion else 'FALLA'}] {descripcion}")
    if not condicion:
        fallos += 1


def debe_fallar(descripcion: str, excepcion: type, funcion) -> None:
    try:
        funcion()
    except excepcion as error:
        comprobar(f"{descripcion} -> {type(error).__name__}: {error}", True)
    else:
        comprobar(f"{descripcion} (no lanzó {excepcion.__name__})", False)


# --- Cifrado reversible del salario (Fernet) ---
cifrado = ServicioCifrado(ServicioCifrado.generar_clave())
gerente = Gerente("Pedro Soto", "Av. Siempre Viva 123", "+56911111111",
                  "pedro@ecotech.cl", date(2020, 3, 1), 2_500_000, cifrado)
depto = Departamento("Operaciones", gerente)  # RF02: el departamento nace con gerente
camila = Empleado("Camila Rojas", "Calle 1", "+56922222222",
                  "camila@ecotech.cl", date(2023, 5, 10), 900_000, cifrado)
depto.asignar_empleado(camila)

comprobar("Salario se recupera con la clave correcta", camila.get_salario(cifrado) == 900_000)
otro_cifrado = ServicioCifrado(ServicioCifrado.generar_clave())
debe_fallar("Otra clave no puede leer el salario", DatoInvalidoError,
            lambda: camila.get_salario(otro_cifrado))
debe_fallar("Clave Fernet inválida", DatoInvalidoError, lambda: ServicioCifrado(b"clave-mala"))
debe_fallar("Salario infinito rechazado", DatoInvalidoError,
            lambda: camila.actualizar_salario(float("inf"), cifrado))

# --- Hash de contraseñas (bcrypt) ---
hash_ok = ServicioCifrado.hash_password("ClaveSegura123")
comprobar("El hash no contiene la contraseña", "ClaveSegura123" not in hash_ok)
comprobar("Dos hashes de la misma clave son distintos (salt)",
          hash_ok != ServicioCifrado.hash_password("ClaveSegura123"))

# --- Login con bloqueo ---
usuario = camila.crear_usuario("crojas", hash_ok, Rol.EMPLEADO)
comprobar("Login correcto", usuario.autenticar("ClaveSegura123"))
comprobar("Login con clave incorrecta devuelve False", not usuario.autenticar("otra"))
comprobar("Login con clave vacía devuelve False", not usuario.autenticar(""))
comprobar("Tercer intento fallido bloquea la cuenta",
          not usuario.autenticar("x") and usuario.bloqueado)
debe_fallar("Cuenta bloqueada no puede autenticar", OperacionNoPermitidaError,
            lambda: usuario.autenticar("ClaveSegura123"))

# --- Cambio de contraseña ---
usuario_g = gerente.crear_usuario("psoto", ServicioCifrado.hash_password("Gerente2026!"), Rol.GERENTE)
debe_fallar("Nueva contraseña corta rechazada", DatoInvalidoError,
            lambda: usuario_g.cambiar_password("Gerente2026!", "123"))
comprobar("Cambio de contraseña correcto", usuario_g.cambiar_password("Gerente2026!", "NuevaClave2026"))
comprobar("La contraseña antigua ya no sirve", not usuario_g.autenticar("Gerente2026!"))
comprobar("La contraseña nueva sí sirve", usuario_g.autenticar("NuevaClave2026"))

# --- Permisos y sesión ---
comprobar("Gerente puede usar APIs", usuario_g.tiene_permiso("apis"))
comprobar("Empleado no puede gestionar usuarios", not usuario.tiene_permiso("usuarios"))
sesion = Sesion(usuario_g)
sesion.exigir_permiso("proyectos")
comprobar("Sesión activa permite un módulo autorizado", sesion.activa)
debe_fallar("Sesión bloquea un módulo sin permiso", OperacionNoPermitidaError,
            lambda: sesion.exigir_permiso("usuarios"))
sesion.cerrar_sesion()
debe_fallar("Sesión cerrada bloquea todo", OperacionNoPermitidaError,
            lambda: sesion.exigir_permiso("proyectos"))
debe_fallar("Sesión sin usuario válido", OperacionNoPermitidaError, lambda: Sesion("admin"))

# --- Validador de entradas ---
comprobar("Sanitizar quita caracteres de control",
          ValidadorEntrada.sanitizar("  Ana\x00\x07 ") == "Ana")
debe_fallar("Credenciales vacías", DatoInvalidoError,
            lambda: ValidadorEntrada.validar_credenciales("  ", "clave"))
debe_fallar("Email con salto de línea al final", DatoInvalidoError,
            lambda: ValidadorEntrada.validar_email("ana@ecotech.cl\nDROP"))

print("\nResultado:", "TODO OK" if fallos == 0 else f"{fallos} FALLA(S)")
sys.exit(1 if fallos else 0)
