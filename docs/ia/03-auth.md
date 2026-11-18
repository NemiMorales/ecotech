# Bitácora IA 03: Autenticación, cifrado y sesión

## Registro N° 3

| Campo | Detalle |
|---|---|
| **Fecha** | 16 al 18-11-2026 |
| **Rama** | feature/auth |
| **Herramientas** | (1) Herramienta de IA usada por Fran (**completar: cuál fue**). (2) Claude (Anthropic) para revisar e integrar. |

### Prompt usado

```
(1) Fran: COMPLETAR con el prompt que usó para generar cifrado.py, sesion.py y validador_entrada.py.

(2) Noemí, a Claude: "la idea es que se mantenga todo desde el UML que envié, o sea depto con
gerente, y arreglar lo demás". Se pidió comparar el zip de Fran con el repo e integrarlo.
```

### Código sugerido

Zip `EcoTech_Solutions_Codigo_Corregido.zip` con `cifrado.py`, `sesion.py`, `validador_entrada.py`
y una versión reescrita de todas las clases de `modelos/`. Según su propio README, las clases
"se reconstruyeron a partir de la revisión y el código compartido en la conversación" con la IA.

### Problemas o vulnerabilidades detectadas

| # | Dónde | Problema | Decisión |
|---|---|---|---|
| 1 | `main` | Se subieron 4 commits directo a `main` (sin PR) con ejemplos de uso comentados; quedaron `)` sin comentar y `cifrado.py` y `validador.py` daban `SyntaxError`. | **DESCARTAR**: se revirtieron los 4 commits. |
| 2 | Estructura | Los archivos venían en `ecotech/` y no en `ecotech/seguridad/`. | **MODIFICAR**: se movieron a `seguridad/` y se corrigieron los imports. |
| 3 | Modelos | La IA renombró accesores (`id_empleado` → `id`) y cambió el orden de parámetros de `RegistroTiempo`. Rompía `tests/prueba_modelo.py` y la tabla UML ↔ código. | **DESCARTAR** la reescritura de modelos: se mantiene la versión fiel al UML. |
| 4 | Departamento | La IA permitía crear un departamento sin gerente. El UML dice `Departamento → 1 Gerente` (RF02). | **DESCARTAR**: el constructor sigue exigiendo gerente. |
| 5 | Modelos | La IA eliminó type hints, docstrings con referencia al UML y marcas `# IA:`. | **DESCARTAR**: se pierde trazabilidad para la defensa (2.1.1 y 2.1.5). |
| 6 | Usuario | `MAX_INTENTOS = 5` escrito en el código, contradiciendo `MAX_INTENTOS_LOGIN=3` del `.env`. | **MODIFICAR**: se lee del `.env` (por defecto 3). |
| 7 | Dependencias | Usaba `cryptography` pero no estaba en `requirements.txt`. | **MODIFICAR**: se agregó `cryptography==50.0.2`. |
| 8 | Clave Fernet | Generar una clave nueva en cada ejecución deja los salarios ilegibles. | **MODIFICAR**: `FERNET_KEY` en `.env` y `ServicioCifrado.desde_entorno()`. |
| 9 | Validaciones | `NaN` e `inf` pasaban como salario válido; `match` aceptaba un salto de línea final; `datetime` pasaba como fecha. | **ADOPTAR** las mejoras de Fran en `_validaciones.py` (`math.isfinite`, `fullmatch`, rechazo de `datetime`). |
| 10 | Seguridad | `autenticar()`, `cambiar_password()`, `tiene_permiso()`, `Sesion`, `sanitizar()`. | **ADOPTAR** con ajustes: type hints, `Sesion.exigir_permiso()` y `validar_credenciales()`. |

### Decisión

- [x] ADOPTAR: lógica de seguridad (cifrado, login, sesión, validador) y mejoras de validación
- [x] MODIFICAR: ubicación, imports, límite de intentos, clave desde `.env`, dependencias
- [x] DESCARTAR: reescritura de los modelos y los commits directos a `main`

### Criterio (seguridad, eficiencia, coherencia con UML)

- **Seguridad:** contraseñas con bcrypt (hash con salt, no reversible); salario con Fernet (reversible solo con la clave del `.env`); bloqueo por intentos; mensajes de error genéricos (no revelan si falló el usuario o la clave, ni si falló la clave Fernet o el dato).
- **Coherencia con UML:** se mantienen nombres, firmas y multiplicidades del diagrama; las diferencias quedan en `docs/modelo-uml-vs-codigo.md`.
- **Eficiencia / reutilización:** `ValidadorEntrada` reutiliza `_validaciones.py` en vez de duplicar reglas.
- **Verificación:** `python -m tests.prueba_modelo` (33 OK) y `python -m tests.prueba_seguridad` (24 OK).

### Código final o commit

Rama `feature/auth` → Pull Request hacia `develop` (revisa Fran).
