"""Menú de consola: login, opciones según el rol y manejo de errores en cada opción."""

from __future__ import annotations

import logging
from collections.abc import Callable

from ecotech.datos.conexion import Conexion
from ecotech.datos.repositorios import (
    ConsultaApiRepositorio,
    DepartamentoRepositorio,
    EmpleadoRepositorio,
    ProyectoRepositorio,
    RegistroTiempoRepositorio,
    UsuarioRepositorio,
)
from ecotech.excepciones import (
    BaseDatosError,
    DatoInvalidoError,
    EcoTechError,
    OperacionNoPermitidaError,
    ServicioExternoError,
)
from ecotech.interfaz import entrada
from ecotech.modelos.departamento import Departamento
from ecotech.modelos.empleado import Empleado
from ecotech.modelos.gerente import Gerente
from ecotech.modelos.proyecto import Proyecto
from ecotech.modelos.registro_tiempo import RegistroTiempo
from ecotech.modelos.rol import Rol
from ecotech.seguridad.cifrado import ServicioCifrado
from ecotech.seguridad.sesion import Sesion
from ecotech.seguridad.validador import MONEDAS_PERMITIDAS, ValidadorEntrada
from ecotech.servicios.clima import ServicioClima
from ecotech.servicios.indicadores import ATRIBUCION, ServicioIndicadores

log = logging.getLogger(__name__)
MAX_INTENTOS_PANTALLA = 5  # intentos de login por ejecución (además del bloqueo por cuenta)


# IA: adoptado
class Aplicacion:
    """Une todas las capas: modelo, seguridad, base de datos y APIs."""

    def __init__(self, conexion: Conexion, cifrado: ServicioCifrado) -> None:
        self.__cifrado = cifrado
        self.__empleados = EmpleadoRepositorio(conexion, cifrado)
        self.__departamentos = DepartamentoRepositorio(conexion, cifrado)
        self.__proyectos = ProyectoRepositorio(conexion, cifrado)
        self.__registros = RegistroTiempoRepositorio(conexion)
        self.__usuarios = UsuarioRepositorio(conexion, cifrado)
        self.__consultas = ConsultaApiRepositorio(conexion)
        self.__clima = ServicioClima()
        self.__indicadores = ServicioIndicadores()
        self.__sesion: Sesion | None = None

    # =====================================================================
    # Inicio y login
    # =====================================================================
    def iniciar(self) -> None:
        if not self.__usuarios.hay_usuarios():
            self.__ejecutar(self.__crear_administrador_inicial)
            if not self.__usuarios.hay_usuarios():
                print("No se pudo crear el administrador. Vuelva a ejecutar el programa.")
                return
        while self.__iniciar_sesion():
            self.__menu_principal()

    def __crear_administrador_inicial(self) -> None:
        print("\n=== Configuración inicial: no hay usuarios registrados ===")
        print("Se creará la cuenta de Administrador de RR.HH. asociada a un empleado.\n")
        empleado = self.__pedir_datos_empleado(Empleado)
        while True:  # primero se valida la cuenta completa; recién después se guarda en la BD
            try:
                usuario = empleado.crear_usuario(
                    entrada.pedir("Nombre de usuario: ", lambda v: ValidadorEntrada.sanitizar(v).lower()),
                    ServicioCifrado.hash_password(self.__pedir_password_nueva()),
                    Rol.ADMIN_RRHH,
                )
                break
            except DatoInvalidoError as error:
                print(f"   ⚠ {error}")
        self.__empleados.crear(empleado)
        self.__usuarios.crear(usuario)
        print("✔ Administrador creado. Ya puede iniciar sesión.")

    def __iniciar_sesion(self) -> bool:
        """Devuelve True si alguien inició sesión; False si se eligió salir."""
        print("\n========== EcoTech Solutions ==========")
        if not entrada.confirmar("¿Desea iniciar sesión?"):
            return False
        for _ in range(MAX_INTENTOS_PANTALLA):
            try:
                nombre, clave = ValidadorEntrada.validar_credenciales(
                    input("Usuario: "), entrada.password("Contraseña: ")
                )
                usuario = self.__usuarios.buscar_por_nombre(nombre)
                if usuario is None:
                    # Mismo mensaje que con clave incorrecta: no se revela qué usuarios existen.
                    print("✖ Usuario o contraseña incorrectos.")
                    continue
                correcto = usuario.autenticar(clave)
                self.__usuarios.guardar_estado_login(usuario)
                if correcto:
                    self.__sesion = Sesion(usuario)
                    print(f"\n✔ Bienvenido/a, {usuario.empleado.nombre} ({usuario.rol}).")
                    return True
                print("✖ Usuario o contraseña incorrectos.")
                if usuario.bloqueado:
                    print("✖ La cuenta quedó bloqueada. Contacte a un administrador.")
            except OperacionNoPermitidaError as error:  # cuenta bloqueada
                print(f"✖ {error} Contacte a un administrador.")
            except DatoInvalidoError as error:
                print(f"⚠ {error}")
            except BaseDatosError as error:
                print(f"✖ {error}")
                return False
        print("Demasiados intentos. Vuelva a intentarlo más tarde.")
        return False

    # =====================================================================
    # Menú principal: solo muestra lo que el rol puede usar
    # =====================================================================
    def __menu_principal(self) -> None:
        opciones: list[tuple[str, str | None, Callable[[], None]]] = [
            ("Empleados", "empleados", self.__menu_empleados),
            ("Departamentos", "departamentos", self.__menu_departamentos),
            ("Proyectos", "proyectos", self.__menu_proyectos),
            ("Registro de horas", "registros", self.__menu_registros),
            ("Clima de un proyecto (API)", "apis", self.__consultar_clima),
            ("Pago internacional (API)", "apis", self.__calcular_pago),
            ("Usuarios", "usuarios", self.__menu_usuarios),
            ("Cambiar mi contraseña", None, self.__cambiar_password),
        ]
        usuario = self.__sesion.usuario
        visibles = [(t, m, f) for t, m, f in opciones if m is None or usuario.tiene_permiso(m)]
        while self.__sesion.activa:
            print("\n----- Menú principal -----")
            for numero, (titulo, _, _) in enumerate(visibles, start=1):
                print(f"{numero}. {titulo}")
            print("0. Cerrar sesión")
            opcion = entrada.entero("Opción: ")
            if opcion == 0:
                self.__sesion.cerrar_sesion()
                print("Sesión cerrada.")
            elif opcion <= len(visibles):
                _, modulo, funcion = visibles[opcion - 1]
                self.__ejecutar(funcion, modulo)
            else:
                print("⚠ Opción inválida.")

    def __ejecutar(self, funcion: Callable[[], None], modulo: str | None = None) -> None:
        """Toda opción pasa por aquí: control de acceso + manejo de errores.

        El programa nunca se cae: cada error muestra un mensaje claro y vuelve al menú.
        Los detalles técnicos se guardan en logs/ecotech.log, no en pantalla.
        """
        try:
            if modulo is not None and self.__sesion is not None:
                self.__sesion.exigir_permiso(modulo)  # control de flujo y sesión (3.1.2.G.15)
            funcion()
        except (DatoInvalidoError, OperacionNoPermitidaError) as error:
            print(f"⚠ {error}")
        except ServicioExternoError as error:
            print(f"✖ {error}")
        except BaseDatosError as error:
            print(f"✖ {error}")
        except EcoTechError as error:
            print(f"✖ {error}")
        except Exception:  # último recurso: nada inesperado detiene el sistema
            log.exception("Error inesperado en la opción %s", getattr(funcion, "__name__", "?"))
            print("✖ Ocurrió un error inesperado. El detalle quedó registrado en logs/ecotech.log.")

    def __submenu(self, titulo: str, opciones: list[tuple]) -> None:
        """Cada opción puede pedir un permiso propio: (texto, función) o (texto, función, módulo)."""
        visibles = [o for o in opciones if len(o) == 2 or self.__sesion.usuario.tiene_permiso(o[2])]
        while True:
            print(f"\n--- {titulo} ---")
            for numero, opcion in enumerate(visibles, start=1):
                print(f"{numero}. {opcion[0]}")
            print("0. Volver")
            elegida = entrada.entero("Opción: ")
            if elegida == 0:
                return
            if elegida <= len(visibles):
                opcion = visibles[elegida - 1]
                self.__ejecutar(opcion[1], opcion[2] if len(opcion) == 3 else None)
            else:
                print("⚠ Opción inválida.")

    # =====================================================================
    # Empleados (CRUD)
    # =====================================================================
    def __menu_empleados(self) -> None:
        self.__submenu("Empleados", [
            ("Listar", self.__listar_empleados),
            ("Registrar empleado", lambda: self.__registrar_empleado(Empleado)),
            ("Registrar gerente", lambda: self.__registrar_empleado(Gerente)),
            ("Actualizar contacto", self.__actualizar_contacto),
            ("Actualizar salario", self.__actualizar_salario),
            ("Eliminar", self.__eliminar_empleado),
        ])

    def __listar_empleados(self) -> bool:
        lista = self.__empleados.listar()
        if not lista:
            print("No hay empleados registrados.")
            return False
        for empleado in lista:
            print(f"  {empleado}")  # usa obtener_resumen() de Empleado o Gerente (polimorfismo)
        return True

    def __pedir_datos_empleado(self, clase: type[Empleado]) -> Empleado:
        nombre = entrada.texto("Nombre completo: ", "Nombre")
        direccion = entrada.texto("Dirección: ", "Dirección")
        telefono = entrada.pedir("Teléfono (+569...): ", ValidadorEntrada.validar_telefono)
        email = entrada.pedir("Email: ", ValidadorEntrada.validar_email)
        inicio = entrada.fecha("Fecha de inicio de contrato (dd-mm-aaaa): ")
        while True:
            try:
                return clase(nombre, direccion, telefono, email, inicio,
                             entrada.decimal("Salario en CLP: "), self.__cifrado)
            except DatoInvalidoError as error:
                print(f"   ⚠ {error}")

    def __registrar_empleado(self, clase: type[Empleado]) -> None:
        empleado = self.__pedir_datos_empleado(clase)
        self.__empleados.crear(empleado)
        print(f"✔ Registrado con ID {empleado.id_empleado}.")

    def __elegir_empleado(self) -> Empleado:
        if not self.__listar_empleados():
            raise OperacionNoPermitidaError("Primero registre empleados.")
        empleado = self.__empleados.buscar_por_id(entrada.entero("ID del empleado: ", 1))
        if empleado is None:
            raise OperacionNoPermitidaError("No existe un empleado con ese ID.")
        return empleado

    def __actualizar_contacto(self) -> None:
        empleado = self.__elegir_empleado()
        telefono = entrada.pedir(f"Nuevo teléfono [{empleado.telefono}]: ", ValidadorEntrada.validar_telefono)
        email = entrada.pedir(f"Nuevo email [{empleado.email}]: ", ValidadorEntrada.validar_email)
        empleado.actualizar_contacto(telefono, email)
        self.__empleados.actualizar(empleado)
        print("✔ Contacto actualizado.")

    def __actualizar_salario(self) -> None:
        empleado = self.__elegir_empleado()
        print(f"Salario actual: ${empleado.get_salario(self.__cifrado):,.0f} CLP".replace(",", "."))
        empleado.actualizar_salario(entrada.decimal("Nuevo salario en CLP: "), self.__cifrado)
        self.__empleados.actualizar(empleado)
        print("✔ Salario actualizado (se guarda cifrado).")

    def __eliminar_empleado(self) -> None:
        empleado = self.__elegir_empleado()
        if entrada.confirmar(f"¿Eliminar a {empleado.nombre}? Se borrará también su cuenta de usuario"):
            self.__empleados.eliminar(empleado.id_empleado)
            print("✔ Empleado eliminado.")

    # =====================================================================
    # Departamentos
    # =====================================================================
    def __menu_departamentos(self) -> None:
        self.__submenu("Departamentos", [
            ("Listar", self.__listar_departamentos),
            ("Crear", self.__crear_departamento),
            ("Asignar empleado", lambda: self.__mover_empleado(asignar=True)),
            ("Quitar empleado", lambda: self.__mover_empleado(asignar=False)),
            ("Eliminar", self.__eliminar_departamento),
        ])

    def __listar_departamentos(self) -> bool:
        lista = self.__departamentos.listar()
        if not lista:
            print("No hay departamentos registrados.")
            return False
        for depto in lista:
            print(f"  {depto}")
            for empleado in depto.empleados:
                print(f"      · {empleado.nombre}")
        return True

    def __crear_departamento(self) -> None:
        libres = [e for e in self.__empleados.listar()
                  if isinstance(e, Gerente) and e.departamento_a_cargo is None]
        if not libres:
            raise OperacionNoPermitidaError("Se necesita un gerente sin departamento (regístrelo en Empleados).")
        print("Gerentes disponibles:")
        for gerente in libres:
            print(f"  [{gerente.id_empleado}] {gerente.nombre}")
        nombre = entrada.texto("Nombre del departamento: ", "Nombre del departamento")
        id_gerente = entrada.entero("ID del gerente: ", 1)
        gerente = next((g for g in libres if g.id_empleado == id_gerente), None)
        if gerente is None:
            raise OperacionNoPermitidaError("Ese ID no corresponde a un gerente disponible.")
        departamento = Departamento(nombre, gerente)  # RF02: no existe departamento sin gerente
        self.__departamentos.crear(departamento)
        print(f"✔ Departamento creado con ID {departamento.id_departamento}.")

    def __mover_empleado(self, asignar: bool) -> None:
        if not self.__listar_departamentos():
            return
        id_depto = entrada.entero("ID del departamento: ", 1)
        id_empleado = self.__elegir_empleado().id_empleado
        if asignar:
            self.__departamentos.asignar_empleado(id_depto, id_empleado)
        else:
            self.__departamentos.remover_empleado(id_depto, id_empleado)
        print("✔ Cambio guardado.")

    def __eliminar_departamento(self) -> None:
        if self.__listar_departamentos():
            id_depto = entrada.entero("ID del departamento: ", 1)
            if entrada.confirmar("¿Eliminar? Los empleados quedarán sin departamento"):
                if not self.__departamentos.eliminar(id_depto):
                    raise OperacionNoPermitidaError("No existe un departamento con ese ID.")
                print("✔ Departamento eliminado.")

    # =====================================================================
    # Proyectos
    # =====================================================================
    def __menu_proyectos(self) -> None:
        self.__submenu("Proyectos", [
            ("Listar", self.__listar_proyectos),
            ("Crear", self.__crear_proyecto, "gestion_proyectos"),
            ("Asignar empleado", lambda: self.__asignacion_proyecto(asignar=True), "gestion_proyectos"),
            ("Desasignar empleado", lambda: self.__asignacion_proyecto(asignar=False), "gestion_proyectos"),
            ("Eliminar", self.__eliminar_proyecto, "gestion_proyectos"),
        ])

    def __listar_proyectos(self) -> bool:
        lista = self.__proyectos.listar()
        if not lista:
            print("No hay proyectos registrados.")
            return False
        for proyecto in lista:
            print(f"  {proyecto}")
            for empleado in proyecto.empleados_asignados:
                print(f"      · [{empleado.id_empleado}] {empleado.nombre}")
        return True

    def __elegir_proyecto(self) -> Proyecto:
        if not self.__listar_proyectos():
            raise OperacionNoPermitidaError("Primero cree un proyecto.")
        proyecto = self.__proyectos.buscar_por_id(entrada.entero("ID del proyecto: ", 1))
        if proyecto is None:
            raise OperacionNoPermitidaError("No existe un proyecto con ese ID.")
        return proyecto

    def __crear_proyecto(self) -> None:
        nombre = entrada.texto("Nombre del proyecto: ", "Nombre del proyecto")
        descripcion = entrada.texto("Descripción: ", "Descripción", 500)
        inicio = entrada.fecha("Fecha de inicio (dd-mm-aaaa): ")
        ciudad = entrada.pedir("Ciudad donde se ejecuta: ", ValidadorEntrada.validar_ciudad)
        print(f"Monedas: {', '.join(sorted(MONEDAS_PERMITIDAS))}")
        moneda = entrada.pedir("Moneda del país: ", ValidadorEntrada.validar_moneda)
        proyecto = Proyecto(nombre, descripcion, inicio, ciudad, moneda)
        self.__proyectos.crear(proyecto)
        print(f"✔ Proyecto creado con ID {proyecto.id_proyecto}.")

    def __asignacion_proyecto(self, asignar: bool) -> None:
        proyecto = self.__elegir_proyecto()
        id_empleado = self.__elegir_empleado().id_empleado
        if asignar:
            self.__proyectos.asignar_empleado(proyecto.id_proyecto, id_empleado)
        else:
            self.__proyectos.desasignar_empleado(proyecto.id_proyecto, id_empleado)
        print("✔ Cambio guardado.")

    def __eliminar_proyecto(self) -> None:
        proyecto = self.__elegir_proyecto()
        if entrada.confirmar(f"¿Eliminar el proyecto {proyecto.nombre}?"):
            self.__proyectos.eliminar(proyecto.id_proyecto)
            print("✔ Proyecto eliminado.")

    # =====================================================================
    # Registro de horas
    # =====================================================================
    def __menu_registros(self) -> None:
        self.__submenu("Registro de horas", [
            ("Registrar horas", self.__registrar_horas),
            ("Ver horas de un proyecto", self.__ver_horas),
        ])

    def __registrar_horas(self) -> None:
        proyecto = self.__elegir_proyecto()
        usuario = self.__sesion.usuario
        if usuario.rol is Rol.EMPLEADO:
            # Un empleado solo declara SUS horas: no puede elegir a otra persona.
            empleado = proyecto.buscar_asignado(usuario.empleado.id_empleado)
            if empleado is None:
                raise OperacionNoPermitidaError("Usted no está asignado a este proyecto.")
        else:
            if not proyecto.empleados_asignados:
                raise OperacionNoPermitidaError("El proyecto no tiene empleados asignados.")
            empleado = proyecto.buscar_asignado(entrada.entero("ID del empleado asignado: ", 1))
            if empleado is None:
                raise OperacionNoPermitidaError("Ese empleado no está asignado al proyecto.")
        registro = RegistroTiempo(
            empleado, proyecto,
            entrada.fecha("Fecha (dd-mm-aaaa): "),
            entrada.decimal("Horas trabajadas: "),
            entrada.texto("Descripción: ", "Descripción", 255),
        )
        self.__registros.crear(registro)
        print("✔ Horas registradas.")

    def __ver_horas(self) -> None:
        proyecto = self.__elegir_proyecto()
        filas = self.__registros.listar_por_proyecto(proyecto.id_proyecto)
        if not filas:
            print("Sin horas registradas.")
            return
        for fila in filas:
            print(f"  {fila['fecha']:%d-%m-%Y}  {fila['empleado']:<25} {float(fila['horas']):>5g} h  {fila['descripcion']}")
        print(f"  Total: {sum(float(f['horas']) for f in filas):g} h")

    # =====================================================================
    # APIs externas (Unidad 3)
    # =====================================================================
    def __id_usuario_actual(self) -> int | None:
        return self.__usuarios.id_de(self.__sesion.usuario.nombre_usuario)

    def __consultar_clima(self) -> None:
        proyecto = self.__elegir_proyecto()
        try:
            clima = self.__clima.consultar(proyecto.ciudad)
            self.__consultas.registrar("CLIMA", proyecto.ciudad, clima, self.__id_usuario_actual())
            origen = "en línea"
        except ServicioExternoError as error:
            guardado = self.__consultas.ultimo_resultado("CLIMA", proyecto.ciudad)
            if guardado is None:
                raise
            print(f"⚠ {error}")
            clima, fecha = guardado
            origen = f"ÚLTIMO DATO GUARDADO ({fecha:%d-%m-%Y %H:%M}), puede no estar actualizado"
        print(f"\nClima en {clima['ciudad']}, {clima['pais']} — {origen}")
        print(f"  Estado:      {clima['estado']}")
        print(f"  Temperatura: {clima['temperatura_c']:g} °C")
        print(f"  Humedad:     {clima['humedad_pct']:g} %")
        print(f"  Viento:      {clima['viento_kmh']:g} km/h")
        print(f"  ⚠ {clima['alerta']}" if clima["alerta"] else "  ✔ Sin riesgos para trabajo en terreno.")

    def __calcular_pago(self) -> None:
        proyecto = self.__elegir_proyecto()
        if not proyecto.empleados_asignados:
            raise OperacionNoPermitidaError("El proyecto no tiene empleados asignados.")
        empleado = proyecto.buscar_asignado(entrada.entero("ID del empleado asignado: ", 1))
        if empleado is None:
            raise OperacionNoPermitidaError("Ese empleado no está asignado al proyecto.")
        salario = empleado.get_salario(self.__cifrado)
        parametro = f"CLP-{proyecto.moneda}"
        try:
            tasa = self.__indicadores.obtener_tasa(proyecto.moneda)
            self.__consultas.registrar("TIPO_CAMBIO", parametro, tasa, self.__id_usuario_actual())
            origen = "tasa en línea"
        except ServicioExternoError as error:
            guardado = self.__consultas.ultimo_resultado("TIPO_CAMBIO", parametro)
            if guardado is None:
                raise
            print(f"⚠ {error}")
            tasa, fecha = guardado
            origen = f"ÚLTIMA TASA GUARDADA ({fecha:%d-%m-%Y %H:%M}), confirmar antes de pagar"
        pago = ServicioIndicadores.convertir(salario, tasa)
        print(f"\nPago de {empleado.nombre} — proyecto {proyecto.nombre} ({proyecto.ciudad})")
        print(f"  Salario:   ${pago['monto_clp']:,.0f} CLP".replace(",", "."))
        print(f"  Tasa:      1 CLP = {pago['tasa']:.6f} {pago['moneda']} ({origen})")
        print(f"  A pagar:   {_formato_cl(pago['monto_convertido'])} {pago['moneda']}")
        print(f"  {ATRIBUCION}")

    # =====================================================================
    # Usuarios y contraseña
    # =====================================================================
    def __menu_usuarios(self) -> None:
        self.__submenu("Usuarios", [
            ("Listar", self.__listar_usuarios),
            ("Crear cuenta para un empleado", self.__crear_usuario),
            ("Desbloquear cuenta", self.__desbloquear_usuario),
        ])

    def __listar_usuarios(self) -> None:
        for fila in self.__usuarios.listar():
            estado = "BLOQUEADO" if fila["bloqueado"] else "activo"
            print(f"  {fila['nombre_usuario']:<15} {Rol(fila['rol'])!s:<12} {estado:<10} {fila['empleado']}")

    def __crear_usuario(self) -> None:
        empleado = self.__elegir_empleado()
        print("Roles: 1. Admin RR.HH.  2. Gerente  3. Empleado")
        rol = [Rol.ADMIN_RRHH, Rol.GERENTE, Rol.EMPLEADO][
            entrada.pedir("Rol: ", lambda v: _opcion(v, 3)) - 1]
        usuario = empleado.crear_usuario(
            entrada.pedir("Nombre de usuario: ", lambda v: ValidadorEntrada.sanitizar(v).lower()),
            ServicioCifrado.hash_password(self.__pedir_password_nueva()),
            rol,
        )
        self.__usuarios.crear(usuario)
        print(f"✔ Cuenta '{usuario.nombre_usuario}' creada.")

    def __desbloquear_usuario(self) -> None:
        nombre = ValidadorEntrada.sanitizar(input("Usuario a desbloquear: ")).lower()
        if not self.__usuarios.desbloquear(nombre):
            raise OperacionNoPermitidaError("No existe ese usuario.")
        print("✔ Cuenta desbloqueada.")

    def __cambiar_password(self) -> None:
        usuario = self.__sesion.usuario
        actual = entrada.password("Contraseña actual: ")
        nueva = self.__pedir_password_nueva()
        correcto = usuario.cambiar_password(actual, nueva)
        self.__usuarios.guardar_estado_login(usuario)
        if not correcto:
            raise OperacionNoPermitidaError("La contraseña actual no es correcta.")
        self.__usuarios.actualizar_password(usuario)
        print("✔ Contraseña actualizada.")

    @staticmethod
    def __pedir_password_nueva() -> str:
        while True:
            nueva = entrada.password("Nueva contraseña (mín. 8 caracteres): ")
            if len(nueva) < 8:
                print("   ⚠ Debe tener al menos 8 caracteres.")
            elif nueva != entrada.password("Repita la contraseña: "):
                print("   ⚠ Las contraseñas no coinciden.")
            else:
                return nueva


def _opcion(valor: str, maximo: int) -> int:
    valor = ValidadorEntrada.sanitizar(valor)
    if not valor.isdigit() or not 1 <= int(valor) <= maximo:
        raise DatoInvalidoError(f"Elija un número entre 1 y {maximo}.")
    return int(valor)


def _formato_cl(monto: float) -> str:
    """Formato chileno: punto para miles y coma para decimales (3.510,00)."""
    return f"{monto:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
