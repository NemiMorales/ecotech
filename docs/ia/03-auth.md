# Bitácora IA 03: Fusión del modelo UML con el aporte de seguridad de Fran

## Registro N° 3

| Campo | Detalle |
|---|---|
| **Fecha** | 16 al 18-11-2026 |
| **Rama** | feature/auth |
| **Herramientas** | (1) Herramienta de IA usada por Fran (**completar: cuál fue**). (2) Claude (Anthropic), usado en **modo validación**. |
| **Integrantes** | Noemí Morales (modelo POO desde el UML) · Fran (capa de seguridad) |

---

## 1. Qué se fusionó

Esta rama **no es código nuevo generado desde cero**. Es la **fusión de dos trabajos que ya existían**,
usando el diagrama UML final (Informe ES1, Anexo A) como fuente de verdad:

| Origen | Qué aportó | Dónde estaba |
|---|---|---|
| **Noemí** | Modelo POO completo y fiel al UML: `Persona` abstracta, `Empleado`, `Gerente`, `Departamento` (con gerente obligatorio, RF02), `Proyecto`, `RegistroTiempo`, `Usuario`, `Rol`; validaciones comunes; tabla UML ↔ código; `tests/prueba_modelo.py`. | Rama `feature/modelo-poo` (PR #1) |
| **Fran** | Capa de seguridad: `ServicioCifrado` (bcrypt + Fernet), `Sesion`, `ValidadorEntrada` con `sanitizar()`; implementación de `autenticar()`, `cambiar_password()` y `tiene_permiso()` en `Usuario`; mejoras de validación (NaN/infinito, `fullmatch`, rechazo de `datetime`). | Zip `EcoTech_Solutions_Codigo_Corregido.zip` y 4 commits directos a `main` |

**Regla de la fusión:** cuando las dos versiones chocaban, **ganaba la que respetaba el UML**.
Por eso la estructura del modelo es la de Noemí y la lógica de seguridad es la de Fran.

```
  UML (fuente de verdad)
          │
          ▼
  Modelo POO de Noemí ──────┐
                            ├──► validación con IA ──► feature/auth ──► PR #2 → develop
  Seguridad de Fran (zip) ──┘     (comparar, probar,
                                   detectar choques)
```

---

## 2. Qué significa "modo validación"

La IA (Claude) **no se usó para escribir el sistema**, sino para **revisar y combinar** el código de
las dos integrantes. Concretamente:

1. **Comparó** el zip de Fran contra el repositorio, archivo por archivo (`diff`).
2. **Ejecutó** el código: compiló todos los `.py` y corrió `tests/prueba_modelo.py` con y sin los cambios de Fran.
3. **Detectó** errores y choques con el UML (tabla de la sección 4).
4. **Integró** lo que pasaba la validación, con ajustes mínimos de ubicación, imports y configuración.
5. **Verificó** el resultado con pruebas automáticas.

### Lo que la IA agregó (para ser transparentes)

Además de validar, la IA escribió estas piezas pequeñas para que la fusión funcionara.
Todas están marcadas en el código con `# IA:` y el equipo las debe revisar en el PR:

| Pieza | Archivo | Por qué |
|---|---|---|
| `ServicioCifrado.desde_entorno()` | `seguridad/cifrado.py` | Leer la clave Fernet del `.env` en vez de generarla en cada ejecución. |
| `_max_intentos()` | `modelos/usuario.py` | Leer `MAX_INTENTOS_LOGIN` del `.env` (el zip lo tenía fijo en 5). |
| Módulo `"apis"` en `PERMISOS_POR_ROL` | `modelos/usuario.py` | Para restringir el consumo de APIs por rol (Unidad 3). |
| `Sesion.exigir_permiso()` | `seguridad/sesion.py` | Control de flujo: corta el acceso sin sesión activa o sin permiso (3.1.2.G.15). |
| `ValidadorEntrada.validar_credenciales()` | `seguridad/validador.py` | Rechazar usuario o contraseña vacíos antes del login (3.1.2.G.14). |
| `tests/prueba_seguridad.py` | `tests/` | Comprobar la capa de seguridad (24 pruebas). |

---

## 3. Prompts usados

```
(1) Fran: COMPLETAR con el prompt que usó para generar cifrado.py, sesion.py y validador_entrada.py.
```

```
(2) Noemí, a Claude (modo validación):
"Puedes ver los cambios que hizo Fran en el zip con lo mío en GitHub, y qué falta o cómo va."
"La idea es que se mantenga todo desde el UML que envié, o sea depto con gerente, y arreglar lo demás."
```

---

## 4. Problemas detectados en la validación y decisión

| # | Dónde | Problema | Decisión |
|---|---|---|---|
| 1 | `main` | 4 commits directos a `main` (sin PR) con ejemplos comentados; quedaron `)` sin comentar y `cifrado.py` y `validador.py` daban `SyntaxError`. | **DESCARTAR**: se revirtieron. |
| 2 | Estructura | Los archivos de Fran venían en `ecotech/` y no en `ecotech/seguridad/`. | **MODIFICAR**: se movieron y se corrigieron los imports. |
| 3 | Modelos | El zip renombraba accesores (`id_empleado` → `id`) y cambiaba el orden de parámetros de `RegistroTiempo`; `tests/prueba_modelo.py` fallaba. | **DESCARTAR** esa parte: se mantienen los nombres del UML. |
| 4 | Departamento | El zip permitía crear un departamento sin gerente. El UML dice `Departamento → 1 Gerente` (RF02). | **DESCARTAR**: el constructor sigue exigiendo gerente. |
| 5 | Modelos | El zip quitaba type hints, docstrings con referencia al UML y marcas `# IA:`. | **DESCARTAR**: se pierde trazabilidad para la defensa (2.1.1 y 2.1.5). |
| 6 | Usuario | `MAX_INTENTOS = 5` fijo en el código, distinto de `MAX_INTENTOS_LOGIN=3` del `.env`. | **MODIFICAR**: se lee del `.env`. |
| 7 | Dependencias | Se usaba `cryptography` sin estar en `requirements.txt`. | **MODIFICAR**: se agregó `cryptography==50.0.2`. |
| 8 | Clave Fernet | Generar una clave nueva en cada ejecución deja ilegibles los salarios guardados. | **MODIFICAR**: `FERNET_KEY` en `.env`. |
| 9 | Validaciones | `NaN` e `inf` pasaban como salario; `match` aceptaba un salto de línea final; `datetime` pasaba como fecha. | **ADOPTAR** las mejoras de Fran. |
| 10 | Seguridad | `ServicioCifrado`, `autenticar()`, `cambiar_password()`, `tiene_permiso()`, `Sesion`, `sanitizar()`. | **ADOPTAR** con type hints y los agregados de la sección 2. |

### Decisión

- [x] **ADOPTAR**: lógica de seguridad de Fran y sus mejoras de validación
- [x] **MODIFICAR**: ubicación, imports, límite de intentos, clave desde `.env`, dependencias
- [x] **DESCARTAR**: reescritura de los modelos del zip y los commits directos a `main`

---

## 5. Criterios técnicos

- **Coherencia con UML:** el modelo de Noemí se mantiene intacto en nombres, firmas y multiplicidades. Las diferencias con el diagrama quedan en `docs/modelo-uml-vs-codigo.md`.
- **Seguridad:** contraseñas con bcrypt (hash con salt, no reversible); salario con Fernet (reversible solo con la clave del `.env`); bloqueo por intentos; mensajes de error genéricos que no revelan qué falló.
- **Eficiencia / reutilización:** `ValidadorEntrada` reutiliza `modelos/_validaciones.py` en vez de duplicar reglas.
- **Verificación:** `python -m tests.prueba_modelo` (33 OK) y `python -m tests.prueba_seguridad` (24 OK).

---

## 6. Código final

Rama `feature/auth` → **PR #2 hacia `develop`**, revisado por Fran antes del merge.
