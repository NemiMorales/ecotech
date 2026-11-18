# Bitácora IA 04: Base de datos y CRUD

> **Nota de transparencia:** esta rama la desarrolló Claude a pedido de Noemí ("puedes hacer lo
> que falta") a partir del modelo UML ya implementado. Las decisiones quedan como **ADOPTAR
> provisorio**: el equipo debe revisarlas en el PR y, si cambia algo, actualizar esta bitácora.

## Registro N° 4

| Campo | Detalle |
|---|---|
| **Fecha** | 18-11-2026 |
| **Rama** | feature/bd-crud |
| **Herramienta** | Claude (Anthropic) |

### Prompt usado

```
"Revisa y ve qué falta según el proyecto, lo que pide y lo que evalúan."
"Puedes hacer lo que falta, por fa."
```

### Código sugerido

`sql/schema.sql`, `ecotech/datos/conexion.py`, `ecotech/datos/repositorios.py`,
`tests/prueba_bd.py` y ajustes mínimos al modelo (ver tabla de abajo).

### Decisiones de diseño

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| MySQL/MariaDB (XAMPP) con `mysql-connector-python` | `sqlite3` | Es lo que usa el curso; obliga a configurar host, puerto, usuario y clave (criterio 2.1.3.I.6). |
| Persona, Empleado y Gerente en **una tabla** con columna `tipo` | Una tabla por clase | Persona es abstracta (no tiene filas propias) y Gerente no agrega columnas. Menos JOIN. |
| `salario_cifrado TEXT` | `DECIMAL` | El token Fernet es texto largo. Costo: no se puede ordenar ni sumar salarios en SQL. |
| `ON DELETE` según la relación del UML | Borrar en cascada todo | Agregación → `SET NULL`; composición Usuario → `CASCADE`; RegistroTiempo → `RESTRICT` (trazabilidad). |
| **El modelo valida, el repositorio persiste** | Validar solo con SQL | Las reglas (RF02, RF03, horas 0–24) viven en las clases, no se duplican. |
| Consultas con parámetros `%s` | Armar el SQL con f-strings | Evita inyección SQL (probado en `prueba_bd.py`). |
| `Conexion.cursor()` con `with`: COMMIT o ROLLBACK y cierre en `finally` | Abrir y cerrar a mano | Nunca queda una conexión abierta ni una operación a medias. |
| Errores de MySQL traducidos a mensajes seguros | Mostrar el error original | El original expone usuario, consulta y estructura; el detalle va solo al log. |

### Problemas detectados durante el desarrollo

| # | Problema | Cómo se resolvió |
|---|---|---|
| 1 | Los IDs del modelo venían de un contador en memoria; al reiniciar el programa se repetirían. | `_fijar_id()` (uso interno) toma el ID de `AUTO_INCREMENT`. |
| 2 | Al registrar horas, el empleado leído de la BD y el que guardaba el proyecto eran **objetos distintos** aunque fueran la misma persona, y `esta_asignado()` fallaba. | `Proyecto.buscar_asignado(id)` entrega el mismo objeto que guarda el proyecto. |
| 3 | MariaDB devuelve el código 1698 (no 1045) para acceso denegado, y se mostraba un mensaje genérico. | Se agregó al mapa de errores de `conexion.py`. |
| 4 | Si se reconstruían los registros de horas como objetos, los de un empleado ya desasignado fallaban. | `listar_por_proyecto()` devuelve filas de solo lectura; el historial se conserva. |
| 5 | El bloqueo por intentos se perdía al cerrar el programa. | Se guardan `intentos_fallidos` y `bloqueado` en la tabla `usuario`. |
| 6 | El proyecto no tenía ciudad ni moneda, necesarias para la Unidad 3. | `Proyecto` recibe `ciudad` y `moneda` (opcionales, con validación ISO de 3 letras). |

### Decisión

- [x] ADOPTAR (provisorio, pendiente de revisión del equipo en el PR)
- [ ] MODIFICAR
- [ ] DESCARTAR

### Criterio

- **Seguridad:** consultas parametrizadas, credenciales de BD en `.env`, salario cifrado en la BD, hash bcrypt, mensajes de error sin detalles técnicos.
- **Coherencia con UML:** cada `ON DELETE` traduce el tipo de relación del diagrama.
- **Reutilización:** `RepositorioBase` concentra el manejo de cursores; los demás heredan.
- **Verificación:** `python -m tests.prueba_bd` (31 OK contra MariaDB real, en la base aparte `ecotech_prueba`).
