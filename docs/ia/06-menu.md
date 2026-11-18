# Bitácora IA 06: Menú, login y manejo de errores

> **Nota de transparencia:** esta rama la desarrolló Claude a pedido de Noemí ("puedes hacer lo
> que falta"). Las decisiones quedan como **ADOPTAR provisorio** hasta que el equipo las revise en el PR.

## Registro N° 6

| Campo | Detalle |
|---|---|
| **Fecha** | 18-11-2026 |
| **Rama** | feature/menu |
| **Herramienta** | Claude (Anthropic) |

### Prompt usado

```
"Puedes hacer lo que falta, por fa."  (continuación de la revisión contra la pauta)
```

### Código sugerido

`main.py`, `ecotech/interfaz/menu.py`, `ecotech/interfaz/entrada.py` y un ajuste de permisos en
`ecotech/modelos/usuario.py`.

### Decisiones de diseño

| Decisión | Por qué |
|---|---|
| `main.py` corto; el menú vive en `ecotech/interfaz/` | Separar la interfaz de la lógica: el modelo no sabe que existe una consola. |
| Todas las opciones pasan por `Aplicacion.__ejecutar()` | Un solo `try/except` para todo el menú: el sistema nunca se cae y vuelve al menú con un mensaje claro (2.1.4). |
| `__ejecutar()` llama a `Sesion.exigir_permiso()` antes de cada opción | Control de flujo y sesión (3.1.2.G.15): aunque alguien llegue a una opción, sin permiso no se ejecuta. |
| Las funciones de `entrada.py` repiten la pregunta hasta recibir un dato válido | Un error de tipeo no obliga a empezar de nuevo. |
| Login: mismo mensaje para usuario inexistente y clave incorrecta | No revela qué usuarios existen. |
| `getpass` para contraseñas | La clave no se ve en pantalla al escribirla. |
| Si la API falla, se usa el último dato guardado en `consulta_api`, avisando su fecha | Continuidad operativa (3.1.3.G.18): el pago se puede calcular igual, con advertencia. |
| Errores técnicos a `logs/ecotech.log`; en pantalla, un mensaje simple | Comunicación segura de errores. El log no guarda contraseñas, hashes, salarios ni URLs con parámetros. |

### Problemas detectados durante las pruebas

Se probó el programa completo con sesiones simuladas (datos válidos, datos inválidos a propósito,
sin internet y con cuentas bloqueadas). Esto encontró:

| # | Problema | Cómo se resolvió |
|---|---|---|
| 1 | **Fallo de seguridad:** un usuario con rol Empleado veía "Crear" y "Eliminar" dentro de Proyectos, porque el permiso era por módulo completo. | Permisos por opción: se agregó `gestion_proyectos` (solo Admin y Gerente). El empleado ahora solo ve "Listar". |
| 2 | Un empleado podía registrar horas a nombre de otra persona. | Si el rol es Empleado, el sistema usa automáticamente su propio empleado. |
| 3 | Al escribir el salario como "850.000" (formato chileno), Python lo leía como 850. | `entrada.decimal()` reconoce el punto de miles y la coma decimal. |
| 4 | Si el nombre del primer administrador era inválido, el empleado quedaba guardado sin cuenta. | Primero se valida la cuenta completa y recién después se guarda en la BD. |
| 5 | Al leer de un archivo (pruebas automáticas) `getpass` no funciona. | Si la entrada no es una terminal, se usa `input()`. |

### Decisión

- [x] ADOPTAR (provisorio, pendiente de revisión del equipo en el PR)
- [ ] MODIFICAR
- [ ] DESCARTAR

### Criterio

- **Seguridad:** permisos por rol y por opción, sesión obligatoria, bloqueo persistente, mensajes genéricos.
- **Estabilidad:** ninguna entrada inválida ni falla externa detiene el programa (probado sin internet y con MySQL apagado).
- **Verificación:** dos sesiones completas simuladas de punta a punta, más las 4 pruebas automáticas.
