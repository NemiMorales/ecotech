"""Gestión de la conexión a MySQL/MariaDB usando variables de entorno."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager

import mysql.connector
from mysql.connector import errorcode

from ecotech.excepciones import BaseDatosError, DatoInvalidoError, OperacionNoPermitidaError

log = logging.getLogger(__name__)

# Errores de MySQL traducidos a mensajes seguros: explican qué hacer sin mostrar
# la consulta, la contraseña ni el detalle técnico (ese va solo al archivo de log).
_MENSAJES_CONEXION = {
    errorcode.ER_ACCESS_DENIED_ERROR: "Usuario o contraseña de MySQL incorrectos. Revise DB_USER y DB_PASSWORD en el .env.",
    1698: "Usuario o contraseña de MySQL incorrectos. Revise DB_USER y DB_PASSWORD en el .env.",  # variante MariaDB
    errorcode.ER_BAD_DB_ERROR: "La base de datos no existe. Importe sql/schema.sql en phpMyAdmin.",
    errorcode.CR_CONN_HOST_ERROR: "No se pudo conectar a MySQL. ¿Está encendido en XAMPP?",
    errorcode.CR_CONNECTION_ERROR: "No se pudo conectar a MySQL. ¿Está encendido en XAMPP?",
}
_ERROR_DUPLICADO = errorcode.ER_DUP_ENTRY                 # 1062: UNIQUE repetido
_ERROR_FK_EN_USO = errorcode.ER_ROW_IS_REFERENCED_2       # 1451: borrar algo referenciado
_ERROR_FK_NO_EXISTE = errorcode.ER_NO_REFERENCED_ROW_2    # 1452: referencia a algo inexistente


# IA: adoptado
class Conexion:
    """Crea conexiones con mysql-connector-python (librería oficial de Oracle para MySQL).

    Los parámetros se leen del .env: nunca se escriben en el código ni se suben al repositorio.
    """

    def __init__(self) -> None:
        self.__parametros = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": self.__leer_puerto(),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "ecotech"),
            "connection_timeout": 5,   # no quedarse colgado si MySQL no responde
            "autocommit": False,       # cada operación confirma o revierte completa
        }

    @staticmethod
    def __leer_puerto() -> int:
        try:
            return int(os.getenv("DB_PORT", "3306"))
        except ValueError as error:
            raise BaseDatosError("DB_PORT en el .env debe ser un número (ej: 3306).") from error

    def __conectar(self) -> mysql.connector.MySQLConnection:
        try:
            return mysql.connector.connect(**self.__parametros)
        except mysql.connector.Error as error:
            log.error("Fallo de conexión a MySQL (errno=%s)", error.errno)
            mensaje = _MENSAJES_CONEXION.get(error.errno, "No fue posible conectarse a la base de datos.")
            raise BaseDatosError(mensaje) from error

    def probar(self) -> None:
        """Verifica la conexión al iniciar el programa. Lanza BaseDatosError con un mensaje claro."""
        with self.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchall()

    @contextmanager
    def cursor(self, confirmar: bool = False) -> Iterator:
        """Entrega un cursor y SIEMPRE cierra la conexión (también si hay error).

        Con confirmar=True hace COMMIT al terminar bien y ROLLBACK si algo falla,
        para que nunca quede una operación a medias en la base de datos.
        """
        conexion = self.__conectar()
        cur = conexion.cursor(dictionary=True)
        try:
            yield cur
            if confirmar:
                conexion.commit()
        except mysql.connector.IntegrityError as error:
            conexion.rollback()
            raise self.__traducir_integridad(error) from error
        except mysql.connector.Error as error:
            conexion.rollback()
            log.error("Error de MySQL (errno=%s)", error.errno)
            raise BaseDatosError("Ocurrió un error al acceder a la base de datos.") from error
        except Exception:
            conexion.rollback()
            raise
        finally:
            cur.close()
            conexion.close()

    @staticmethod
    def __traducir_integridad(error: mysql.connector.IntegrityError) -> Exception:
        """Convierte errores de restricciones (UNIQUE, FOREIGN KEY) en errores del dominio."""
        log.warning("Restricción de integridad (errno=%s)", error.errno)
        if error.errno == _ERROR_DUPLICADO:
            return DatoInvalidoError("Ya existe un registro con ese dato (nombre, email o usuario repetido).")
        if error.errno == _ERROR_FK_EN_USO:
            return OperacionNoPermitidaError(
                "No se puede eliminar: tiene información asociada (ej: horas registradas o departamento a cargo)."
            )
        if error.errno == _ERROR_FK_NO_EXISTE:
            return DatoInvalidoError("El registro relacionado no existe.")
        return BaseDatosError("Los datos no cumplen las reglas de la base de datos.")
