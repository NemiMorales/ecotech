# Correspondencia modelo UML vs código Python

Fuente de verdad: diagrama de clases final (Informe ES1, Figura 4 / Anexo A).

## Reglas de traducción usadas

| UML (estilo Java) | Python |
|---|---|
| Atributo privado `-nombre` | `self.__nombre` (doble guion bajo: Python lo renombra a `_Clase__nombre`) |
| `getNombre()` sin parámetros | `@property nombre` (se lee como `obj.nombre`, no se puede asignar) |
| Método con parámetros, ej. `getSalario(c)`, `asignarEmpleado(e)` | Método en snake_case: `get_salario(c)`, `asignar_empleado(e)` (PEP 8) |
| `camelCase` en atributos | `snake_case`: `fechaInicioContrato` → `fecha_inicio_contrato` |
| `<<abstract>>` y método `*` | `class Persona(ABC)` + `@abstractmethod` |
| `-contadorId: int$` (static) | Atributo de clase `__contador_id` |
| `<<enumeration>>` | `class Rol(Enum)` |
| `Date`, `double`, `String`, `List<T>` | `datetime.date`, `float`, `str`, `list[T]` |
| Método privado `-validarHoras()` | `def __validar_horas(...)` |

## Tabla de correspondencia

| Clase UML | Archivo | Atributos | Relación UML | Cómo se implementó en Python |
|---|---|---|---|---|
| Persona «abstract» | `ecotech/modelos/persona.py` | `__nombre`, `__direccion`, `__telefono`, `__email` | Generalización de Empleado | `Persona(ABC)` con `obtener_resumen()` como `@abstractmethod`; instanciarla lanza `TypeError`. Solo `actualizar_contacto()` modifica teléfono y email. `__str__` llama a `obtener_resumen()` (polimorfismo). |
| Empleado | `ecotech/modelos/empleado.py` | `__contador_id` (clase), `__id_empleado`, `__fecha_inicio_contrato`, `__salario_cifrado`, `__departamento`, `__usuario` | Herencia `Persona <\|-- Empleado` | `class Empleado(Persona)` y `super().__init__(...)`. ID desde el contador estático, sin setter. El salario se guarda solo cifrado (`actualizar_salario(monto, c)` / `get_salario(c)`). |
| Gerente | `ecotech/modelos/gerente.py` | `__departamento_a_cargo` | Herencia `Empleado <\|-- Gerente` | `class Gerente(Empleado)`, `super().__init__(...)`; redefine `obtener_resumen()` usando `super().obtener_resumen()`. |
| Departamento | `ecotech/modelos/departamento.py` | `__id_departamento`, `__nombre`, `__gerente`, `__empleados` | Agregación `Departamento 0..1 ◇ 0..* Empleado`; asociación `Departamento 0..1 → 1 Gerente` | Agregación: guarda una lista de **referencias** a empleados creados afuera; `remover_empleado()` no los destruye. Bidireccional: avisa al empleado con `e._asignar_departamento(self)`. `asignar_empleado()` retorna `False` si el empleado ya tiene departamento (RF03). Asociación con Gerente: el constructor lo exige; `cambiar_gerente()` impide que un gerente dirija dos departamentos. `empleados` devuelve una copia. |
| Proyecto | `ecotech/modelos/proyecto.py` | `__id_proyecto`, `__nombre`, `__descripcion`, `__fecha_inicio`, `__empleados_asignados` | Asociación N:N `Proyecto 0..* → 0..* Empleado` | Lista de referencias en Proyecto (según el sentido de la flecha). `esta_asignado()` evita duplicados; `asignar_empleado()` / `desasignar_empleado()` retornan `bool`. |
| RegistroTiempo | `ecotech/modelos/registro_tiempo.py` | `__id_registro`, `__fecha`, `__horas`, `__descripcion`, `__empleado`, `__proyecto` | Asociación `0..* → 1 Empleado` y `0..* → 1 Proyecto` | El constructor exige un `Empleado` y un `Proyecto` (multiplicidad 1). No es composición: el registro se conserva aunque el empleado sea desasignado. `__validar_horas()` es privado y rechaza ≤ 0 o > 24. Sin setters. |
| Usuario | `ecotech/modelos/usuario.py` | `__nombre_usuario`, `__password_hash`, `__intentos_fallidos`, `__rol`, `__empleado` | Composición `Empleado 1 ◆ 0..1 Usuario`; asociación `Usuario → Rol` | Lo crea solo el Empleado con `empleado.crear_usuario(...)` (dueño del ciclo de vida, máximo uno). Solo acepta un hash bcrypt; no hay accesor para el hash. `autenticar()` verifica con `ServicioCifrado.verificar_password` y bloquea la cuenta al llegar a `MAX_INTENTOS_LOGIN` (del `.env`). `cambiar_password()` exige la clave actual y guarda solo el nuevo hash. `tiene_permiso()` consulta `PERMISOS_POR_ROL`. |
| Rol «enumeration» | `ecotech/modelos/rol.py` | `ADMIN_RRHH`, `GERENTE`, `EMPLEADO` | Usado por Usuario | `class Rol(Enum)`. El administrador es un valor del Enum, no una subclase de Persona. |

## Elementos agregados que no están en el UML

| Elemento | Motivo |
|---|---|
| Parámetro `cifrado` en el constructor de Empleado y Gerente | El UML recibe `salario: double`, pero el salario debe guardarse cifrado y no hay otra forma de cifrarlo al crear el objeto. |
| `Empleado.__usuario` y `crear_usuario()` | Necesarios para que el Empleado sea dueño de su Usuario (composición ◆). |
| `_asignar_departamento()` y `_asignar_departamento_a_cargo()` | Métodos de uso interno (un guion bajo) para que Departamento mantenga la relación en ambos sentidos sin exponer setters públicos. |
| `__contador_id` en Departamento, Proyecto y RegistroTiempo | El UML no recibe el ID en el constructor. Es un ID provisorio en memoria. |
| `_fijar_id()` en Empleado, Departamento, Proyecto y RegistroTiempo | Uso interno del repositorio: reemplaza el ID provisorio por el de `AUTO_INCREMENT` de MySQL. |
| `Proyecto.ciudad` y `Proyecto.moneda` | Unidad 3: la ciudad se usa para consultar el clima y la moneda para calcular pagos internacionales. |
| `Proyecto.buscar_asignado(id)` | Al leer de la BD, el mismo empleado puede llegar como objetos distintos; entrega el que guarda el proyecto. |
| `Usuario._restaurar_estado()` y `_hash_para_persistir()` | Uso interno de `UsuarioRepositorio` para guardar y recuperar el bloqueo y el hash. No se usan desde el menú. |
| `ecotech/modelos/_validaciones.py` | Reglas de validación comunes escritas una sola vez (evita duplicar código). |
| Excepciones `EcoTechError`, `DatoInvalidoError`, `OperacionNoPermitidaError` | Errores de dominio propios; `DatoInvalidoError` también es `ValueError`. |
| RegistroTiempo exige que el empleado esté asignado al proyecto | Evita registrar horas en proyectos ajenos (problema de "errores de asignación" del caso). |

| ServicioCifrado | `ecotech/seguridad/cifrado.py` | `__cifrador` (Fernet) | Usado por Empleado (`getSalario(c)`) y Usuario | Fernet (reversible) para el salario; bcrypt (hash con salt, no reversible) para contraseñas. La clave se lee de `FERNET_KEY` en el `.env` con `desde_entorno()`. |
| ValidadorEntrada | `ecotech/seguridad/validador.py` | — (métodos estáticos) | Usado por el menú | Reutiliza las reglas de `modelos/_validaciones.py` y agrega `sanitizar()` y `validar_credenciales()`. |

## Elementos de seguridad agregados que no están en el UML

| Elemento | Motivo |
|---|---|
| `Usuario.__bloqueado` y `bloqueado` | El UML tiene `intentosFallidos`; el bloqueo es la consecuencia de superar el límite. |
| `PERMISOS_POR_ROL` | Implementa `tienePermiso(modulo)`. **Decisión:** `Modulo` se representa como texto (`"empleados"`, `"apis"`…), no como clase nueva. `"proyectos"` permite ver y `"gestion_proyectos"` crear, asignar y eliminar. |
| `Sesion` (`ecotech/seguridad/sesion.py`) | Controla que solo un usuario autenticado y con permiso acceda al menú y a las APIs (criterio 3.1.2.G.15). |

## Del modelo a las tablas (MySQL)

| Relación UML | Tabla / columna | Regla `ON DELETE` | Qué significa |
|---|---|---|---|
| Herencia Persona → Empleado → Gerente | `empleado.tipo` (`EMPLEADO` / `GERENTE`) | — | Una sola tabla: Persona es abstracta y Gerente no agrega columnas. |
| Agregación Departamento ◇ Empleado | `empleado.id_departamento` | `SET NULL` | Si se borra el departamento, el empleado sigue existiendo. |
| Departamento → 1 Gerente | `departamento.id_gerente` `NOT NULL UNIQUE` | `RESTRICT` | Siempre hay gerente y uno no dirige dos departamentos. |
| Proyecto N:N Empleado | `empleado_proyecto` | `CASCADE` | Borrar un proyecto borra solo sus asignaciones. |
| RegistroTiempo → Empleado / Proyecto | `registro_tiempo.id_empleado`, `id_proyecto` | `RESTRICT` | No se pierde el historial de horas. |
| Composición Empleado ◆ Usuario | `usuario.id_empleado` `UNIQUE` | `CASCADE` | Sin empleado no hay cuenta (sin cuentas huérfanas). |
