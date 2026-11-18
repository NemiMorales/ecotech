"""Prueba del CRUD contra MySQL real, en una base APARTE llamada 'ecotech_prueba'.

Requisitos: MySQL encendido (XAMPP) y el .env con DB_USER y DB_PASSWORD correctos.
Ejecutar desde la raíz del repo:  python -m tests.prueba_bd
"""

import logging
import os
import sys
from datetime import date
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

from ecotech.datos.conexion import Conexion
from ecotech.datos.repositorios import (
    ConsultaApiRepositorio,
    DepartamentoRepositorio,
    EmpleadoRepositorio,
    ProyectoRepositorio,
    RegistroTiempoRepositorio,
    UsuarioRepositorio,
)
from ecotech.excepciones import BaseDatosError, DatoInvalidoError, OperacionNoPermitidaError
from ecotech.modelos.departamento import Departamento
from ecotech.modelos.empleado import Empleado
from ecotech.modelos.gerente import Gerente
from ecotech.modelos.proyecto import Proyecto
from ecotech.modelos.registro_tiempo import RegistroTiempo
from ecotech.modelos.rol import Rol
from ecotech.seguridad.cifrado import ServicioCifrado

BD_PRUEBA = "ecotech_prueba"
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


def crear_bd_de_prueba() -> None:
    """Ejecuta sql/schema.sql cambiando el nombre de la base por la de prueba."""
    script = (Path(__file__).parent.parent / "sql" / "schema.sql").read_text(encoding="utf-8")
    script = script.replace("DATABASE IF NOT EXISTS ecotech", f"DATABASE IF NOT EXISTS {BD_PRUEBA}")
    script = script.replace("USE ecotech;", f"USE {BD_PRUEBA};")
    conexion = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
    )
    cur = conexion.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {BD_PRUEBA}")
    for sentencia in script.split(";"):
        lineas = [l for l in sentencia.splitlines() if not l.strip().startswith("--")]
        if "".join(lineas).strip():
            cur.execute("\n".join(lineas))
    conexion.commit()
    conexion.close()


logging.disable(logging.CRITICAL)  # los detalles técnicos van al log, no a la pantalla
load_dotenv()
crear_bd_de_prueba()
os.environ["DB_NAME"] = BD_PRUEBA
conexion = Conexion()
cifrado = ServicioCifrado(ServicioCifrado.generar_clave())

empleados = EmpleadoRepositorio(conexion, cifrado)
departamentos = DepartamentoRepositorio(conexion, cifrado)
proyectos = ProyectoRepositorio(conexion, cifrado)
registros = RegistroTiempoRepositorio(conexion)
usuarios = UsuarioRepositorio(conexion, cifrado)
consultas = ConsultaApiRepositorio(conexion)

conexion.probar()
comprobar("Conexión a MySQL", True)

# --- CREATE ---
pedro = Gerente("Pedro Soto", "Av. Siempre Viva 123", "+56911111111", "pedro@ecotech.cl",
                date(2020, 3, 1), 2_500_000, cifrado)
camila = Empleado("Camila Rojas", "Calle 1", "+56922222222", "camila@ecotech.cl",
                  date(2023, 5, 10), 900_000, cifrado)
id_pedro = empleados.crear(pedro)
id_camila = empleados.crear(camila)
comprobar("INSERT empleado y gerente con ID de AUTO_INCREMENT", (id_pedro, id_camila) == (1, 2))
with conexion.cursor() as cur:
    cur.execute("SELECT salario_cifrado FROM empleado WHERE id_empleado = %s", (id_camila,))
    guardado = cur.fetchall()[0]["salario_cifrado"]
comprobar("El salario se guarda cifrado en la BD", "900000" not in guardado)
debe_fallar("Email repetido", DatoInvalidoError, lambda: empleados.crear(
    Empleado("Otra", "Calle 2", "+56933333333", "camila@ecotech.cl", date(2024, 1, 1), 1, cifrado)))

depto = Departamento("Operaciones", pedro)
id_depto = departamentos.crear(depto)
departamentos.asignar_empleado(id_depto, id_camila)
debe_fallar("RF03: un empleado no se asigna dos veces", OperacionNoPermitidaError,
            lambda: departamentos.asignar_empleado(id_depto, id_camila))

proyecto = Proyecto("Paneles Solares Norte", "Instalación en Antofagasta", date(2026, 1, 15),
                    "Antofagasta", "CLP")
id_proyecto = proyectos.crear(proyecto)
proyecto_peru = Proyecto("Eólico Lima", "Parque eólico", date(2026, 2, 1), "Lima", "PEN")
proyectos.crear(proyecto_peru)
proyectos.asignar_empleado(id_proyecto, id_camila)

# --- READ ---
lista = empleados.listar()
comprobar("SELECT reconstruye Empleado y Gerente", [type(e).__name__ for e in lista] == ["Gerente", "Empleado"])
camila_bd = empleados.buscar_por_id(id_camila)
comprobar("El salario se recupera descifrado", camila_bd.get_salario(cifrado) == 900_000)
comprobar("La agregación se reconstruye", camila_bd.departamento.nombre == "Operaciones")
comprobar("El gerente queda a cargo de su departamento",
          departamentos.listar()[0].gerente.departamento_a_cargo.nombre == "Operaciones")
p_bd = proyectos.buscar_por_id(id_proyecto)
comprobar("Proyecto con ciudad, moneda y empleado asignado",
          (p_bd.ciudad, p_bd.moneda, len(p_bd.empleados_asignados)) == ("Antofagasta", "CLP", 1))
comprobar("Buscar ID inexistente devuelve None", empleados.buscar_por_id(999) is None)

# --- UPDATE ---
camila_bd.actualizar_contacto("+56944444444", "camila.rojas@ecotech.cl")
camila_bd.actualizar_salario(1_050_000, cifrado)
empleados.actualizar(camila_bd)
camila_bd = empleados.buscar_por_id(id_camila)
comprobar("UPDATE de contacto y salario",
          (camila_bd.email, camila_bd.get_salario(cifrado)) == ("camila.rojas@ecotech.cl", 1_050_000))

# --- Registro de horas ---
p_bd = proyectos.buscar_por_id(id_proyecto)
registro = RegistroTiempo(p_bd.buscar_asignado(id_camila), p_bd, date(2026, 11, 18), 7.5, "Montaje de paneles")
registros.crear(registro)
filas = registros.listar_por_proyecto(id_proyecto)
comprobar("Horas registradas", len(filas) == 1 and float(filas[0]["horas"]) == 7.5)

# --- DELETE ---
debe_fallar("No se borra un empleado con horas (RESTRICT)", OperacionNoPermitidaError,
            lambda: empleados.eliminar(id_camila))
debe_fallar("No se borra un gerente a cargo de un departamento", OperacionNoPermitidaError,
            lambda: empleados.eliminar(id_pedro))
debe_fallar("No se borra un proyecto con horas", OperacionNoPermitidaError,
            lambda: proyectos.eliminar(id_proyecto))
comprobar("DELETE de proyecto sin horas", proyectos.eliminar(proyecto_peru.id_proyecto))
comprobar("DELETE de departamento", departamentos.eliminar(id_depto))
comprobar("Agregación: el empleado sigue existiendo sin departamento",
          empleados.buscar_por_id(id_camila).departamento is None)

# --- Usuarios ---
pedro_bd = empleados.buscar_por_id(id_pedro)
usuario = pedro_bd.crear_usuario("psoto", ServicioCifrado.hash_password("Gerente2026!"), Rol.GERENTE)
usuarios.crear(usuario)
comprobar("Hay usuarios", usuarios.hay_usuarios())
leido = usuarios.buscar_por_nombre("psoto")
comprobar("Login con usuario leído de la BD", leido.autenticar("Gerente2026!"))
os.environ["MAX_INTENTOS_LOGIN"] = "3"
for _ in range(3):
    leido.autenticar("mala")
usuarios.guardar_estado_login(leido)
comprobar("El bloqueo sobrevive a reiniciar el programa", usuarios.buscar_por_nombre("psoto").bloqueado)
usuarios.desbloquear("psoto")
comprobar("El administrador puede desbloquear", not usuarios.buscar_por_nombre("psoto").bloqueado)
comprobar("La lista de usuarios no expone el hash", "password_hash" not in usuarios.listar()[0])
comprobar("Inyección SQL en el nombre de usuario no encuentra nada",
          usuarios.buscar_por_nombre("' OR '1'='1") is None)

# --- Consultas a APIs guardadas localmente ---
consultas.registrar("TIPO_CAMBIO", "CLP-USD", {"tasa": 0.00105}, usuarios.id_de("psoto"))
comprobar("Último valor de API guardado", consultas.ultimo_resultado("TIPO_CAMBIO", "CLP-USD")[0]["tasa"] == 0.00105)
comprobar("Sin datos previos devuelve None", consultas.ultimo_resultado("CLIMA", "Lima") is None)

# --- Errores de conexión ---
os.environ["DB_PASSWORD"] = "clave-incorrecta"
os.environ["DB_USER"] = "usuario_inexistente"
debe_fallar("Credenciales de MySQL incorrectas", BaseDatosError, lambda: Conexion().probar())
os.environ["DB_PORT"] = "3999"
debe_fallar("MySQL apagado o puerto incorrecto", BaseDatosError, lambda: Conexion().probar())

print("\nResultado:", "TODO OK" if fallos == 0 else f"{fallos} FALLA(S)")
sys.exit(1 if fallos else 0)
