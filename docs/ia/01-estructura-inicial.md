# Bitácora IA 01: Estructura inicial del proyecto

---

## Registro N° 1

| Campo | Detalle |
|---|---|
| **Fecha** | 10-11-2026 |
| **Rama** | main |
| **Herramienta** | Claude Code (Anthropic) |

### Prompt usado

```
Actúa como desarrollador senior de Python. Necesito que prepares SOLO el esqueleto
inicial de un proyecto universitario. NO escribas lógica de negocio, clases completas
ni consultas SQL: deja archivos vacíos o con un comentario TODO, porque el código lo
desarrollamos nosotras y debemos poder defenderlo.
(Contexto: EcoTech Solutions, POO, MySQL en XAMPP, mysql-connector-python, requests,
python-dotenv, bcrypt, Git con main/develop/feature/*, Python 3.11+, venv.
Se pidió la estructura de carpetas ecotech/, sql/, docs/ia/, tests/, main.py,
.env.example, .gitignore, requirements.txt, README.md y los comandos de terminal.)
```

### Código sugerido

Estructura de carpetas y archivos sin lógica:

- `ecotech/modelos/`, `ecotech/datos/`, `ecotech/seguridad/`, `ecotech/servicios/` y `ecotech/excepciones.py`: cada `.py` con solo un docstring de una línea.
- `sql/schema.sql` y `main.py`: solo un comentario TODO.
- `.env.example` con valores de ejemplo, `.gitignore`, `requirements.txt` con versiones fijas, `docs/ia/PLANTILLA.md` y `README.md`.
- Comandos para crear el venv, `git init`, primer commit, rama `develop` y push a GitHub.

Commit: `156574f chore: estructura inicial del proyecto`

### Problemas o vulnerabilidades detectadas

- No se detectaron problemas que obliguen a cambiar la estructura.
- Se verificó que `.env` está en `.gitignore` y no se subió al repositorio; `.env.example` solo tiene valores de ejemplo.
- Se verificó que los archivos `.py` solo tienen un docstring y que `main.py` y `sql/schema.sql` solo tienen un TODO, sin lógica generada por IA.

### Decisión

- [x] ADOPTAR
- [ ] MODIFICAR
- [ ] DESCARTAR

### Criterio (seguridad, eficiencia, coherencia con UML)

- **Seguridad:** las credenciales quedan fuera del repositorio (`.env` ignorado) y las dependencias tienen versión fija.
- **Coherencia con UML:** los archivos de `ecotech/modelos/` corresponden a las clases del diagrama final (Persona, Empleado, Gerente, Departamento, Proyecto, RegistroTiempo, Usuario, Rol).
- **Defensa del código:** la IA solo generó la estructura; la lógica la desarrolla el equipo.

### Código final o commit

```
156574f chore: estructura inicial del proyecto
```
