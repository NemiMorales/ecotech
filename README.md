# EcoTech Solutions

Sistema de gestión de empleados desarrollado en Python con Programación Orientada a Objetos.
Permite administrar empleados, gerentes, departamentos, proyectos y registros de tiempo,
con autenticación segura de usuarios, persistencia en MySQL/MariaDB y consumo de APIs externas
(clima e indicadores económicos).

## Requisitos

- Python 3.11 o superior
- XAMPP con el servicio **MySQL** encendido (localhost:3306)
- Git

## Instalación

### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### Mac (Terminal)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Base de datos (ambos sistemas)

1. Abrir XAMPP y encender **Apache** y **MySQL**.
2. Entrar a phpMyAdmin: http://localhost/phpmyadmin
3. Crear la base de datos `ecotech`.
4. Seleccionarla → pestaña **Importar** → elegir `sql/schema.sql` → **Continuar**.
5. Revisar que los datos de `.env` coincidan con tu MySQL local.

### Ejecutar

```bash
python main.py
```

## Flujo de ramas

| Rama | Uso |
|---|---|
| `main` | Versión entregable. Solo recibe merges desde `develop`. |
| `develop` | Integración del trabajo de ambas integrantes. |
| `feature/<tema>` | Una rama por funcionalidad (ej: `feature/login`, `feature/modelos`). |

Flujo de trabajo:

1. Crear la rama desde `develop`: `git checkout develop && git pull && git checkout -b feature/<tema>`
2. Hacer commits pequeños y descriptivos.
3. Subir la rama y abrir un **Pull Request hacia `develop`**.
4. La otra integrante revisa y aprueba el PR antes de hacer merge.

## Convención de commits

| Prefijo | Uso |
|---|---|
| `feat:` | Nueva funcionalidad |
| `fix:` | Corrección de errores |
| `docs:` | Documentación |
| `refactor:` | Cambios de código sin alterar funcionalidad |
| `test:` | Pruebas |

Ejemplo: `feat: agregar clase Empleado`

## Uso de IA

Cada uso de IA se registra en `docs/ia/` usando la plantilla `docs/ia/PLANTILLA.md`.

## Integrantes

- _______________________
- _______________________
