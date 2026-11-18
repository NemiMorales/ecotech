# EcoTech Solutions

Sistema de gestión de empleados en Python con Programación Orientada a Objetos (TI3V21, INACAP).
Administra empleados, gerentes, departamentos, proyectos y horas trabajadas, con:

- **Login seguro:** contraseñas con hash bcrypt, bloqueo por intentos y permisos por rol.
- **Base de datos MySQL/MariaDB (XAMPP):** CRUD completo con `mysql-connector-python`.
- **Salarios cifrados** con Fernet (la clave vive en el `.env`).
- **APIs externas:** clima de la ciudad del proyecto (Open-Meteo) y tipo de cambio para pagos
  internacionales (ExchangeRate-API). Ninguna requiere llave.
- **Manejo de errores:** el programa no se cae ante datos inválidos, sin internet o con MySQL apagado.

## Requisitos

- Python 3.11 o superior
- XAMPP con el servicio **MySQL** encendido (localhost:3306)
- Git

## Instalación

### 1. Entorno virtual y dependencias

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

**Mac (Terminal)**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Clave de cifrado

Genere la clave **una sola vez** y péguela en `FERNET_KEY` del `.env`.
Las dos integrantes deben usar **la misma** (compartirla por privado, nunca en el repositorio):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Base de datos

1. Abrir XAMPP y encender **MySQL**.
2. Entrar a phpMyAdmin: http://localhost/phpmyadmin
3. Pestaña **Importar** → elegir `sql/schema.sql` → **Continuar**. El script crea la base `ecotech` con sus tablas.
4. Revisar que `DB_USER` y `DB_PASSWORD` del `.env` coincidan con su MySQL (en XAMPP: `root` sin contraseña).

> ⚠ Volver a importar `schema.sql` **borra todos los datos**.

### 4. Ejecutar

```bash
python main.py
```

La primera vez, el programa pide crear la cuenta del **Administrador de RR.HH.**

## Roles

| Rol | Puede usar |
|---|---|
| Admin RR.HH. | Todo: empleados, departamentos, proyectos, horas, APIs, usuarios |
| Gerente | Empleados, proyectos (con gestión), horas, APIs |
| Empleado | Ver proyectos y registrar **sus propias** horas |

## Pruebas

```bash
python -m tests.prueba_modelo      # clases del UML (33)
python -m tests.prueba_seguridad   # cifrado, login, sesión (24)
python -m tests.prueba_apis        # APIs simuladas: timeout, códigos HTTP, JSON roto (29)
python -m tests.prueba_bd          # CRUD contra MySQL, en la base aparte "ecotech_prueba" (31)
```

## Estructura

```
ecotech/
├── modelos/      Clases del UML (Persona, Empleado, Gerente, Departamento, Proyecto...)
├── seguridad/    ServicioCifrado, Sesion, ValidadorEntrada
├── datos/        Conexion (MySQL) y repositorios CRUD
├── servicios/    ServicioAPI (base), ServicioClima, ServicioIndicadores
└── interfaz/     Menú de consola y lectura de datos
sql/schema.sql    Tablas de la base de datos
docs/             Bitácoras de IA, tabla UML ↔ código y guía de defensa
main.py           Punto de entrada
```

## Flujo de ramas

| Rama | Uso |
|---|---|
| `main` | Versión entregable. Solo recibe merges desde `develop`. |
| `develop` | Integración del trabajo de ambas integrantes. |
| `feature/<tema>` | Una rama por funcionalidad. |

1. Crear la rama desde `develop`: `git checkout develop && git pull && git checkout -b feature/<tema>`
2. Commits pequeños y descriptivos.
3. Pull Request hacia `develop`, revisado por la otra integrante antes del merge.

## Convención de commits

`feat:` funcionalidad · `fix:` corrección · `docs:` documentación · `refactor:` reestructura · `test:` pruebas

## Uso de IA

Cada uso de IA se registra en `docs/ia/` con la plantilla `docs/ia/PLANTILLA.md`, y los fragmentos
apoyados por IA llevan el comentario `# IA: adoptado` o `# IA: modificado - <motivo>`.

Tasas de cambio: Rates By Exchange Rate API (https://www.exchangerate-api.com).
Clima: Open-Meteo (https://open-meteo.com).

## Integrantes

- Noemí Morales
- Francisco Torres
