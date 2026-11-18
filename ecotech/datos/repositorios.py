"""Repositorios CRUD para cada entidad del modelo.

Idea central: **el modelo valida, el repositorio persiste**. Antes de escribir en la BD
siempre se pasa por las clases del modelo (que aplican las reglas del UML) y recién
después se ejecuta el SQL. Todas las consultas usan parámetros (%s) para evitar
inyección SQL: los datos del usuario nunca se pegan dentro del texto de la consulta.
"""

from __future__ import annotations

import json
from typing import Any

from ecotech.datos.conexion import Conexion
from ecotech.excepciones import DatoInvalidoError, OperacionNoPermitidaError
from ecotech.modelos.departamento import Departamento
from ecotech.modelos.empleado import Empleado
from ecotech.modelos.gerente import Gerente
from ecotech.modelos.proyecto import Proyecto
from ecotech.modelos.registro_tiempo import RegistroTiempo
from ecotech.modelos.rol import Rol
from ecotech.modelos.usuario import Usuario
from ecotech.seguridad.cifrado import ServicioCifrado


# IA: adoptado
class RepositorioBase:
    """Código común a todos los repositorios (herencia para no repetir el manejo de cursores)."""

    def __init__(self, conexion: Conexion) -> None:
        self._conexion = conexion

    def _consultar(self, sql: str, parametros: tuple = ()) -> list[dict[str, Any]]:
        with self._conexion.cursor() as cur:
            cur.execute(sql, parametros)
            return cur.fetchall()

    def _ejecutar(self, sql: str, parametros: tuple = ()) -> tuple[int, int]:
        """Ejecuta INSERT/UPDATE/DELETE con COMMIT. Devuelve (id_generado, filas_afectadas)."""
        with self._conexion.cursor(confirmar=True) as cur:
            cur.execute(sql, parametros)
            return cur.lastrowid, cur.rowcount


# IA: adoptado
class EmpleadoRepositorio(RepositorioBase):
    """CRUD de Empleado y Gerente (misma tabla, columna 'tipo')."""

    def __init__(self, conexion: Conexion, cifrado: ServicioCifrado) -> None:
        super().__init__(conexion)
        self.__cifrado = cifrado

    # --- CREATE ---
    def crear(self, empleado: Empleado) -> int:
        tipo = "GERENTE" if isinstance(empleado, Gerente) else "EMPLEADO"
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO empleado (tipo, nombre, direccion, telefono, email, "
            "fecha_inicio_contrato, salario_cifrado) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (tipo, empleado.nombre, empleado.direccion, empleado.telefono, empleado.email,
             empleado.fecha_inicio_contrato, self.__salario_cifrado(empleado)),
        )
        empleado._fijar_id(nuevo_id)
        return nuevo_id

    # --- READ ---
    def listar(self) -> list[Empleado]:
        """Devuelve todos los empleados ya conectados con su departamento."""
        empleados, _ = cargar_organizacion(self._conexion, self.__cifrado)
        return list(empleados.values())

    def buscar_por_id(self, id_empleado: int) -> Empleado | None:
        empleados, _ = cargar_organizacion(self._conexion, self.__cifrado)
        return empleados.get(id_empleado)

    # --- UPDATE ---
    def actualizar(self, empleado: Empleado) -> None:
        """Guarda contacto y salario. Los cambios ya fueron validados por el modelo."""
        _, filas = self._ejecutar(
            "UPDATE empleado SET telefono = %s, email = %s, salario_cifrado = %s "
            "WHERE id_empleado = %s",
            (empleado.telefono, empleado.email, self.__salario_cifrado(empleado), empleado.id_empleado),
        )
        if filas == 0:
            raise OperacionNoPermitidaError("El empleado no existe.")

    # --- DELETE ---
    def eliminar(self, id_empleado: int) -> bool:
        """Falla con OperacionNoPermitidaError si tiene horas registradas o dirige un departamento."""
        _, filas = self._ejecutar("DELETE FROM empleado WHERE id_empleado = %s", (id_empleado,))
        return filas > 0

    def __salario_cifrado(self, empleado: Empleado) -> str:
        # Fernet genera un token distinto cada vez: se vuelve a cifrar el valor actual.
        return self.__cifrado.cifrar(str(empleado.get_salario(self.__cifrado)))


# IA: adoptado
class DepartamentoRepositorio(RepositorioBase):
    """CRUD de Departamento. Las reglas de asignación las aplica la clase Departamento."""

    def __init__(self, conexion: Conexion, cifrado: ServicioCifrado) -> None:
        super().__init__(conexion)
        self.__cifrado = cifrado

    def crear(self, departamento: Departamento) -> int:
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO departamento (nombre, id_gerente) VALUES (%s, %s)",
            (departamento.nombre, departamento.gerente.id_empleado),
        )
        departamento._fijar_id(nuevo_id)
        return nuevo_id

    def listar(self) -> list[Departamento]:
        _, departamentos = cargar_organizacion(self._conexion, self.__cifrado)
        return list(departamentos.values())

    def asignar_empleado(self, id_departamento: int, id_empleado: int) -> None:
        empleados, departamentos = cargar_organizacion(self._conexion, self.__cifrado)
        departamento = _obtener(departamentos, id_departamento, "Departamento")
        empleado = _obtener(empleados, id_empleado, "Empleado")
        if not departamento.asignar_empleado(empleado):  # regla RF03 del modelo
            raise OperacionNoPermitidaError("El empleado ya pertenece a un departamento.")
        self._ejecutar(
            "UPDATE empleado SET id_departamento = %s WHERE id_empleado = %s",
            (id_departamento, id_empleado),
        )

    def remover_empleado(self, id_departamento: int, id_empleado: int) -> None:
        empleados, departamentos = cargar_organizacion(self._conexion, self.__cifrado)
        departamento = _obtener(departamentos, id_departamento, "Departamento")
        if not departamento.remover_empleado(_obtener(empleados, id_empleado, "Empleado")):
            raise OperacionNoPermitidaError("El empleado no pertenece a ese departamento.")
        self._ejecutar("UPDATE empleado SET id_departamento = NULL WHERE id_empleado = %s", (id_empleado,))

    def eliminar(self, id_departamento: int) -> bool:
        """Agregación: los empleados quedan sin departamento (ON DELETE SET NULL), no se borran."""
        _, filas = self._ejecutar("DELETE FROM departamento WHERE id_departamento = %s", (id_departamento,))
        return filas > 0


# IA: adoptado
class ProyectoRepositorio(RepositorioBase):
    """CRUD de Proyecto y de su asociación N:N con Empleado."""

    def __init__(self, conexion: Conexion, cifrado: ServicioCifrado) -> None:
        super().__init__(conexion)
        self.__cifrado = cifrado

    def crear(self, proyecto: Proyecto) -> int:
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO proyecto (nombre, descripcion, fecha_inicio, ciudad, moneda) "
            "VALUES (%s, %s, %s, %s, %s)",
            (proyecto.nombre, proyecto.descripcion, proyecto.fecha_inicio, proyecto.ciudad, proyecto.moneda),
        )
        proyecto._fijar_id(nuevo_id)
        return nuevo_id

    def listar(self) -> list[Proyecto]:
        empleados, _ = cargar_organizacion(self._conexion, self.__cifrado)
        proyectos: dict[int, Proyecto] = {}
        for fila in self._consultar("SELECT * FROM proyecto ORDER BY id_proyecto"):
            proyecto = Proyecto(fila["nombre"], fila["descripcion"], fila["fecha_inicio"],
                                fila["ciudad"], fila["moneda"])
            proyecto._fijar_id(fila["id_proyecto"])
            proyectos[fila["id_proyecto"]] = proyecto
        for fila in self._consultar("SELECT id_proyecto, id_empleado FROM empleado_proyecto"):
            proyectos[fila["id_proyecto"]].asignar_empleado(empleados[fila["id_empleado"]])
        return list(proyectos.values())

    def buscar_por_id(self, id_proyecto: int) -> Proyecto | None:
        return next((p for p in self.listar() if p.id_proyecto == id_proyecto), None)

    def asignar_empleado(self, id_proyecto: int, id_empleado: int) -> None:
        proyecto = _obtener({p.id_proyecto: p for p in self.listar()}, id_proyecto, "Proyecto")
        empleados, _ = cargar_organizacion(self._conexion, self.__cifrado)
        if not proyecto.asignar_empleado(_obtener(empleados, id_empleado, "Empleado")):
            raise OperacionNoPermitidaError("El empleado ya está asignado a este proyecto.")
        self._ejecutar(
            "INSERT INTO empleado_proyecto (id_proyecto, id_empleado) VALUES (%s, %s)",
            (id_proyecto, id_empleado),
        )

    def desasignar_empleado(self, id_proyecto: int, id_empleado: int) -> None:
        _, filas = self._ejecutar(
            "DELETE FROM empleado_proyecto WHERE id_proyecto = %s AND id_empleado = %s",
            (id_proyecto, id_empleado),
        )
        if filas == 0:
            raise OperacionNoPermitidaError("El empleado no estaba asignado a ese proyecto.")

    def eliminar(self, id_proyecto: int) -> bool:
        """Falla si el proyecto tiene horas registradas (ON DELETE RESTRICT, trazabilidad)."""
        _, filas = self._ejecutar("DELETE FROM proyecto WHERE id_proyecto = %s", (id_proyecto,))
        return filas > 0


# IA: adoptado
class RegistroTiempoRepositorio(RepositorioBase):
    """Registro y consulta de horas trabajadas."""

    def crear(self, registro: RegistroTiempo) -> int:
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO registro_tiempo (id_empleado, id_proyecto, fecha, horas, descripcion) "
            "VALUES (%s, %s, %s, %s, %s)",
            (registro.empleado.id_empleado, registro.proyecto.id_proyecto, registro.fecha,
             registro.horas, registro.descripcion),
        )
        registro._fijar_id(nuevo_id)
        return nuevo_id

    def listar_por_proyecto(self, id_proyecto: int) -> list[dict[str, Any]]:
        """Consulta de solo lectura: devuelve filas para mostrar, sin reconstruir objetos.

        Así se conservan las horas de empleados que ya fueron desasignados del proyecto.
        """
        return self._consultar(
            "SELECT r.id_registro, r.fecha, r.horas, r.descripcion, e.nombre AS empleado "
            "FROM registro_tiempo r JOIN empleado e ON e.id_empleado = r.id_empleado "
            "WHERE r.id_proyecto = %s ORDER BY r.fecha",
            (id_proyecto,),
        )


# IA: adoptado
class UsuarioRepositorio(RepositorioBase):
    """Cuentas de acceso. Solo se guarda el hash bcrypt y el estado de bloqueo."""

    def __init__(self, conexion: Conexion, cifrado: ServicioCifrado) -> None:
        super().__init__(conexion)
        self.__cifrado = cifrado

    def hay_usuarios(self) -> bool:
        return self._consultar("SELECT COUNT(*) AS total FROM usuario")[0]["total"] > 0

    def crear(self, usuario: Usuario) -> int:
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO usuario (id_empleado, nombre_usuario, password_hash, rol) VALUES (%s, %s, %s, %s)",
            (usuario.empleado.id_empleado, usuario.nombre_usuario, usuario._hash_para_persistir(),
             usuario.rol.value),
        )
        return nuevo_id

    def buscar_por_nombre(self, nombre_usuario: str) -> Usuario | None:
        filas = self._consultar("SELECT * FROM usuario WHERE nombre_usuario = %s", (nombre_usuario,))
        if not filas:
            return None
        fila = filas[0]
        empleados, _ = cargar_organizacion(self._conexion, self.__cifrado)
        empleado = empleados[fila["id_empleado"]]
        # Composición: el Usuario se reconstruye a través de su Empleado dueño.
        usuario = empleado.crear_usuario(fila["nombre_usuario"], fila["password_hash"], Rol(fila["rol"]))
        usuario._restaurar_estado(fila["intentos_fallidos"], fila["bloqueado"])
        return usuario

    def id_de(self, nombre_usuario: str) -> int | None:
        filas = self._consultar("SELECT id_usuario FROM usuario WHERE nombre_usuario = %s", (nombre_usuario,))
        return filas[0]["id_usuario"] if filas else None

    def guardar_estado_login(self, usuario: Usuario) -> None:
        """Persiste intentos y bloqueo: reiniciar el programa no reinicia los intentos."""
        self._ejecutar(
            "UPDATE usuario SET intentos_fallidos = %s, bloqueado = %s WHERE nombre_usuario = %s",
            (usuario.intentos_fallidos, usuario.bloqueado, usuario.nombre_usuario),
        )

    def actualizar_password(self, usuario: Usuario) -> None:
        self._ejecutar(
            "UPDATE usuario SET password_hash = %s WHERE nombre_usuario = %s",
            (usuario._hash_para_persistir(), usuario.nombre_usuario),
        )

    def desbloquear(self, nombre_usuario: str) -> bool:
        """Acción de administrador: reinicia los intentos fallidos."""
        _, filas = self._ejecutar(
            "UPDATE usuario SET intentos_fallidos = 0, bloqueado = FALSE WHERE nombre_usuario = %s",
            (nombre_usuario,),
        )
        return filas > 0

    def listar(self) -> list[dict[str, Any]]:
        """Lista para administración. No incluye el hash."""
        return self._consultar(
            "SELECT u.nombre_usuario, u.rol, u.bloqueado, e.nombre AS empleado "
            "FROM usuario u JOIN empleado e ON e.id_empleado = u.id_empleado ORDER BY u.nombre_usuario"
        )


# IA: adoptado
class ConsultaApiRepositorio(RepositorioBase):
    """Almacenamiento local de datos obtenidos desde APIs (Unidad 3)."""

    TIPOS = ("CLIMA", "TIPO_CAMBIO")

    def registrar(self, tipo: str, parametro: str, resultado: dict[str, Any], id_usuario: int | None) -> None:
        if tipo not in self.TIPOS:
            raise DatoInvalidoError("Tipo de consulta no válido.")
        self._ejecutar(
            "INSERT INTO consulta_api (tipo, parametro, resultado, id_usuario) VALUES (%s, %s, %s, %s)",
            (tipo, parametro, json.dumps(resultado, ensure_ascii=False, default=str), id_usuario),
        )

    def ultimo_resultado(self, tipo: str, parametro: str) -> tuple[dict[str, Any], Any] | None:
        """Último dato guardado: respaldo cuando la API no responde."""
        filas = self._consultar(
            "SELECT resultado, fecha FROM consulta_api WHERE tipo = %s AND parametro = %s "
            "ORDER BY fecha DESC, id_consulta DESC LIMIT 1",
            (tipo, parametro),
        )
        if not filas:
            return None
        return json.loads(filas[0]["resultado"]), filas[0]["fecha"]


# --- Funciones de apoyo -------------------------------------------------------

def _obtener(diccionario: dict[int, Any], clave: int, entidad: str) -> Any:
    if clave not in diccionario:
        raise OperacionNoPermitidaError(f"{entidad} con ID {clave} no existe.")
    return diccionario[clave]


# IA: adoptado
def cargar_organizacion(
    conexion: Conexion, cifrado: ServicioCifrado
) -> tuple[dict[int, Empleado], dict[int, Departamento]]:
    """Reconstruye empleados, gerentes y departamentos con sus relaciones del UML.

    1. Crea cada fila de 'empleado' como Empleado o Gerente (herencia por columna 'tipo').
    2. Crea cada Departamento con su Gerente (el constructor lo exige, RF02).
    3. Asigna los empleados a su departamento usando el método del modelo (agregación).
    """
    repo = RepositorioBase(conexion)
    empleados: dict[int, Empleado] = {}
    for fila in repo._consultar("SELECT * FROM empleado ORDER BY id_empleado"):
        clase = Gerente if fila["tipo"] == "GERENTE" else Empleado
        salario = float(cifrado.descifrar(fila["salario_cifrado"]))
        empleado = clase(fila["nombre"], fila["direccion"], fila["telefono"], fila["email"],
                         fila["fecha_inicio_contrato"], salario, cifrado)
        empleado._fijar_id(fila["id_empleado"])
        empleados[fila["id_empleado"]] = empleado

    departamentos: dict[int, Departamento] = {}
    for fila in repo._consultar("SELECT * FROM departamento ORDER BY id_departamento"):
        departamento = Departamento(fila["nombre"], empleados[fila["id_gerente"]])
        departamento._fijar_id(fila["id_departamento"])
        departamentos[fila["id_departamento"]] = departamento

    for fila in repo._consultar("SELECT id_empleado, id_departamento FROM empleado "
                                "WHERE id_departamento IS NOT NULL"):
        departamentos[fila["id_departamento"]].asignar_empleado(empleados[fila["id_empleado"]])
    return empleados, departamentos
