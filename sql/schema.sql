-- =====================================================================
-- EcoTech Solutions - Esquema de la base de datos (MySQL / MariaDB)
-- Importar en phpMyAdmin (pestaña Importar) o con:
--   mysql -u root < sql/schema.sql
-- Cada tabla refleja una clase del diagrama UML. Las reglas ON DELETE
-- traducen el tipo de relación del diagrama (ver comentarios).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS ecotech
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecotech;

-- Orden inverso de dependencias para poder re-ejecutar el script.
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS consulta_api;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS registro_tiempo;
DROP TABLE IF EXISTS empleado_proyecto;
DROP TABLE IF EXISTS proyecto;
DROP TABLE IF EXISTS departamento;
DROP TABLE IF EXISTS empleado;
SET FOREIGN_KEY_CHECKS = 1;

-- Persona (abstracta) + Empleado + Gerente en UNA tabla.
-- Persona no se puede instanciar, así que no tiene tabla propia;
-- la columna "tipo" indica si la fila es un Empleado o un Gerente (herencia).
CREATE TABLE empleado (
    id_empleado           INT AUTO_INCREMENT PRIMARY KEY,
    tipo                  ENUM('EMPLEADO', 'GERENTE') NOT NULL DEFAULT 'EMPLEADO',
    nombre                VARCHAR(100) NOT NULL,
    direccion             VARCHAR(100) NOT NULL,
    telefono              VARCHAR(20)  NOT NULL,
    email                 VARCHAR(120) NOT NULL UNIQUE,
    fecha_inicio_contrato DATE         NOT NULL,
    -- Token Fernet: texto largo y distinto en cada cifrado. Por eso es TEXT y no DECIMAL.
    salario_cifrado       TEXT         NOT NULL,
    id_departamento       INT          NULL
) ENGINE = InnoDB;

-- Departamento 0..1 -> 1 Gerente: id_gerente obligatorio y único
-- (un gerente dirige a lo más un departamento).
CREATE TABLE departamento (
    id_departamento INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    id_gerente      INT          NOT NULL UNIQUE,
    CONSTRAINT fk_depto_gerente FOREIGN KEY (id_gerente)
        REFERENCES empleado (id_empleado) ON DELETE RESTRICT
) ENGINE = InnoDB;

-- Agregación Departamento 0..1 <> 0..* Empleado:
-- si se borra el departamento, el empleado SIGUE existiendo (SET NULL).
ALTER TABLE empleado
    ADD CONSTRAINT fk_empleado_depto FOREIGN KEY (id_departamento)
        REFERENCES departamento (id_departamento) ON DELETE SET NULL;

CREATE TABLE proyecto (
    id_proyecto  INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL UNIQUE,
    descripcion  VARCHAR(500) NOT NULL,
    fecha_inicio DATE         NOT NULL,
    ciudad       VARCHAR(80)  NOT NULL DEFAULT 'Santiago',  -- Unidad 3: clima
    moneda       CHAR(3)      NOT NULL DEFAULT 'CLP'        -- Unidad 3: pagos
) ENGINE = InnoDB;

-- Asociación N:N Proyecto 0..* -- 0..* Empleado (tabla intermedia).
CREATE TABLE empleado_proyecto (
    id_proyecto INT NOT NULL,
    id_empleado INT NOT NULL,
    PRIMARY KEY (id_proyecto, id_empleado),
    CONSTRAINT fk_ep_proyecto FOREIGN KEY (id_proyecto)
        REFERENCES proyecto (id_proyecto) ON DELETE CASCADE,
    CONSTRAINT fk_ep_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleado (id_empleado) ON DELETE CASCADE
) ENGINE = InnoDB;

-- Asociación RegistroTiempo 0..* -> 1 Empleado / 1 Proyecto (NO composición):
-- RESTRICT impide borrar un empleado o proyecto con horas registradas (trazabilidad).
CREATE TABLE registro_tiempo (
    id_registro INT AUTO_INCREMENT PRIMARY KEY,
    id_empleado INT          NOT NULL,
    id_proyecto INT          NOT NULL,
    fecha       DATE         NOT NULL,
    horas       DECIMAL(4,2) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    CONSTRAINT ck_horas CHECK (horas > 0 AND horas <= 24),
    CONSTRAINT fk_rt_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleado (id_empleado) ON DELETE RESTRICT,
    CONSTRAINT fk_rt_proyecto FOREIGN KEY (id_proyecto)
        REFERENCES proyecto (id_proyecto) ON DELETE RESTRICT
) ENGINE = InnoDB;

-- Composición Empleado 1 <*> 0..1 Usuario:
-- id_empleado UNIQUE (máximo una cuenta) y CASCADE (sin cuentas huérfanas).
CREATE TABLE usuario (
    id_usuario        INT AUTO_INCREMENT PRIMARY KEY,
    id_empleado       INT          NOT NULL UNIQUE,
    nombre_usuario    VARCHAR(30)  NOT NULL UNIQUE,
    password_hash     CHAR(60)     NOT NULL,  -- solo el hash bcrypt, nunca la contraseña
    rol               ENUM('ADMIN_RRHH', 'GERENTE', 'EMPLEADO') NOT NULL,
    intentos_fallidos INT          NOT NULL DEFAULT 0,
    bloqueado         BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_usuario_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleado (id_empleado) ON DELETE CASCADE
) ENGINE = InnoDB;

-- Unidad 3: datos obtenidos desde APIs externas, guardados localmente.
-- Sirven de respaldo si la API no responde (último valor conocido).
CREATE TABLE consulta_api (
    id_consulta INT AUTO_INCREMENT PRIMARY KEY,
    tipo        ENUM('CLIMA', 'TIPO_CAMBIO') NOT NULL,
    parametro   VARCHAR(80) NOT NULL,           -- ciudad o par de monedas (CLP-USD)
    resultado   TEXT        NOT NULL,           -- JSON con los datos ya extraídos
    fecha       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_usuario  INT         NULL,
    INDEX idx_tipo_parametro (tipo, parametro, fecha),
    CONSTRAINT fk_consulta_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE SET NULL
) ENGINE = InnoDB;
