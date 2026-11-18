# Guía para la defensa oral (criterios I · 30 pts)

Cada integrante explica **su aporte** y defiende las decisiones de **todo** el sistema.
Para cada criterio: qué decir, dónde mostrarlo y qué preguntas pueden aparecer.
Antes de la defensa, abre los archivos indicados y repasa las bitácoras en `docs/ia/`.

---

## 2.1.1.I.2 · UML ↔ código (1,8 pts)

**Mostrar:** `docs/modelo-uml-vs-codigo.md` (tabla completa) y `ecotech/modelos/`.

- Cada clase del diagrama tiene un archivo en `modelos/`; `-atributo` → `self.__atributo`; `getX()` → `@property`.
- **Herencia:** `class Empleado(Persona)` y `class Gerente(Empleado)`, con `super().__init__(...)`.
- **Agregación** (rombo vacío) Departamento ◇ Empleado: lista de referencias a empleados creados afuera.
- **Composición** (rombo lleno) Empleado ◆ Usuario: solo `empleado.crear_usuario()` crea el Usuario.
- **Asociación** RegistroTiempo → Empleado/Proyecto: el constructor exige ambos objetos (multiplicidad 1).

**Preguntas probables:** ¿Cómo se ve en el código la diferencia entre agregación y composición?
¿Qué agregaron que no estaba en el UML y por qué? (tabla "Elementos agregados").

## 2.1.2.I.4 · Encapsulamiento y reutilización (2,4 pts)

**Mostrar:** `persona.py`, `empleado.py` (salario), `_validaciones.py`, `repositorios.py` (`RepositorioBase`), `servicio_api.py`.

- Doble guion bajo → Python renombra el atributo (`_Empleado__salario_cifrado`); no se accede desde afuera.
- Sin setters para ID, hash ni registros de horas; el salario solo existe cifrado.
- Las listas internas se devuelven **copiadas**: nadie salta las reglas con `.append()`.
- **Sin duplicación:** `_validaciones.py` (reglas una vez), `RepositorioBase` (cursores), `ServicioAPI` (errores HTTP); Gerente reutiliza todo Empleado.
- **Abstracción:** `Persona(ABC)` con `@abstractmethod obtener_resumen()`; `__str__` usa el de cada subclase (polimorfismo).

## 2.1.3.I.6 · Conexión y CRUD (3,0 pts)

**Mostrar:** `.env.example`, `ecotech/datos/conexion.py`, `repositorios.py`, `sql/schema.sql`.

- Librería oficial `mysql-connector-python`. Parámetros: `host`, `port`, `user`, `password`, `database` (leídos del `.env`), `connection_timeout=5`, `autocommit=False`.
- `with conexion.cursor(confirmar=True)` → COMMIT si todo sale bien, ROLLBACK si falla, y siempre cierra la conexión (`finally`).
- **El modelo valida, el repositorio persiste:** primero se crea el objeto (aplica reglas del UML), luego el INSERT.
- Consultas con `%s` (parametrizadas) → sin inyección SQL.
- `ON DELETE` según el UML: agregación `SET NULL`, composición `CASCADE`, registros de horas `RESTRICT`.

**Pregunta probable:** ¿Por qué `salario_cifrado` es `TEXT` y no `DECIMAL`? ¿Qué pierden con eso?

## 2.1.4.I.8 · try/except y validaciones (3,6 pts)

**Mostrar:** `Aplicacion.__ejecutar()` en `interfaz/menu.py`, `Conexion.cursor()`, `interfaz/entrada.py`.

Fallas que se capturan y dónde:

| Falla | Excepción | Dónde |
|---|---|---|
| Dato inválido (email, salario ≤ 0, horas > 24) | `DatoInvalidoError` | modelo y `entrada.py` |
| Regla de negocio (gerente con dos deptos, empleado ya asignado) | `OperacionNoPermitidaError` | modelo |
| MySQL apagado / clave incorrecta / BD inexistente | `mysql.connector.Error` → `BaseDatosError` | `conexion.py` |
| Email repetido, borrar algo con horas | `IntegrityError` (1062, 1451) | `conexion.py` |
| Cualquier error inesperado | `Exception` → se registra en el log | `menu.py` |

**Pregunta probable:** ¿Por qué no basta con un solo `except Exception`? (pierdes el mensaje específico y escondes errores de programación).

## 2.1.5.I.10 y 3.1.4.I.22 · Uso de IA (4,2 + 4,2 pts)

**Mostrar:** `docs/ia/01` a `06` y los comentarios `# IA:` del código.

- Sé transparente: qué fragmentos vinieron de IA, con qué herramienta y con qué prompt.
- Ten **2 o 3 ejemplos propios** de errores de la IA que se corrigieron. Algunos reales del proyecto:
  - El zip de Fran: departamento sin gerente (rompía RF02), nombres cambiados que rompían las pruebas, `MAX_INTENTOS` fijo (bitácora 03).
  - Un empleado podía crear y eliminar proyectos: se detectó probando y se corrigió (bitácora 06).
  - "850.000" se leía como 850 (bitácora 06).
  - Errores típicos de código de IA evitados en las APIs: `requests.get` sin `timeout`, sin revisar `status_code`, `json()` sin `try` (bitácora 05).
- Criterios para adoptar, modificar o descartar: **seguridad, eficiencia, coherencia con el UML**.

## 3.1.1.I.13 · APIs y JSON (3,0 pts)

**Mostrar:** `servicios/servicio_api.py`, `clima.py`, `indicadores.py`, opciones 5 y 6 del menú.

- `requests.get(url, params=..., timeout=...)` → `respuesta.json()` → se extraen solo los datos útiles.
- **Clima:** ciudad → coordenadas (geocodificación) → temperatura, humedad, viento, estado; alerta si hay riesgo para trabajo en terreno.
- **Tipo de cambio:** tasa CLP → moneda del país del proyecto → pago del empleado.
- Integración al flujo: cada consulta se guarda en `consulta_api`; si la API falla se usa el último valor guardado.

## 3.1.2.I.16 · Autenticación y datos sensibles (3,6 pts)

**Mostrar:** `seguridad/cifrado.py`, `modelos/usuario.py`, `seguridad/sesion.py`, `seguridad/validador.py`, `.gitignore`.

- **bcrypt** (hash con salt, no reversible) para contraseñas; **Fernet** (reversible con clave) para salarios.
- Bloqueo tras `MAX_INTENTOS_LOGIN` intentos, guardado en la BD (sobrevive a reiniciar).
- Mensaje genérico de login: no revela si el usuario existe.
- `Sesion.exigir_permiso()` antes de cada opción; permisos por rol y por opción.
- Entradas para APIs: ciudad con patrón de letras, moneda con lista blanca; una entrada inválida **no llega** a la API.
- Credenciales y claves en `.env`, que está en `.gitignore`.

**Pregunta probable:** ¿Por qué no usar el mismo método para contraseña y salario?

## 3.1.3.I.19 · Errores de red y códigos HTTP (4,2 pts)

**Mostrar:** `ServicioAPI._obtener_json()` y `__validar_estado()`; `tests/prueba_apis.py`.

- `requests.Timeout`, `requests.ConnectionError`, `requests.RequestException` → `ServicioExternoError`.
- Códigos: 200 continúa; 400, 401, 403, 404, 429 y 5xx tienen mensaje propio.
- JSON inválido (`ValueError`) y claves faltantes (`_extraer()`) también se controlan.
- **Continuidad:** si la API falla, se usa el último dato guardado con su fecha.
- **Comunicación segura:** el usuario ve un mensaje simple; el detalle va a `logs/ecotech.log`, sin URLs ni datos internos.
- Las pruebas simulan las respuestas porque así se prueban casos imposibles de provocar a mano.
