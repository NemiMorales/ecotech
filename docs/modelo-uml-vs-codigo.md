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
| Usuario | `ecotech/modelos/usuario.py` | `__nombre_usuario`, `__password_hash`, `__intentos_fallidos`, `__rol`, `__empleado` | Composición `Empleado 1 ◆ 0..1 Usuario`; asociación `Usuario → Rol` | Lo crea solo el Empleado con `empleado.crear_usuario(...)` (dueño del ciclo de vida, máximo uno). Solo acepta un hash bcrypt; no hay accesor para el hash. `autenticar`, `cambiar_password` y `tiene_permiso` quedan como TODO para la etapa de seguridad. |
| Rol «enumeration» | `ecotech/modelos/rol.py` | `ADMIN_RRHH`, `GERENTE`, `EMPLEADO` | Usado por Usuario | `class Rol(Enum)`. El administrador es un valor del Enum, no una subclase de Persona. |

## Elementos agregados que no están en el UML

| Elemento | Motivo |
|---|---|
| Parámetro `cifrado` en el constructor de Empleado y Gerente | El UML recibe `salario: double`, pero el salario debe guardarse cifrado y no hay otra forma de cifrarlo al crear el objeto. |
| `Empleado.__usuario` y `crear_usuario()` | Necesarios para que el Empleado sea dueño de su Usuario (composición ◆). |
| `_asignar_departamento()` y `_asignar_departamento_a_cargo()` | Métodos de uso interno (un guion bajo) para que Departamento mantenga la relación en ambos sentidos sin exponer setters públicos. |
| `__contador_id` en Departamento, Proyecto y RegistroTiempo | El UML no recibe el ID en el constructor. Es provisorio: cuando se integre MySQL, el ID lo dará `AUTO_INCREMENT`. |
| `ecotech/modelos/_validaciones.py` | Reglas de validación comunes escritas una sola vez (evita duplicar código). |
| Excepciones `EcoTechError`, `DatoInvalidoError`, `OperacionNoPermitidaError` | Errores de dominio propios; `DatoInvalidoError` también es `ValueError`. |
| RegistroTiempo exige que el empleado esté asignado al proyecto | Evita registrar horas en proyectos ajenos (problema de "errores de asignación" del caso). |

## Pendiente de decidir

- `Usuario.tienePermiso(modulo: Modulo)`: el tipo `Modulo` no está definido en el diagrama.
