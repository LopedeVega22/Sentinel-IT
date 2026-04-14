-- ============================================================
-- schema.sql — Base de datos SentinelIT
-- ============================================================
-- Cómo ejecutarlo:
--   mysql -u root -p < schema.sql
-- O desde phpMyAdmin: importar este archivo
-- ============================================================

-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS SentinelIT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE SentinelIT;

-- ── Tabla principal de eventos ───────────────────────────────────────────────
-- Aquí llegan todos los eventos que envían los agentes (Pi4, Pi5, etc.)
CREATE TABLE IF NOT EXISTS eventos (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    tipo        ENUM('detectado', 'bloqueado') NOT NULL,
    servicio    VARCHAR(20) NOT NULL,         -- 'ssh', 'ftp', 'web'
    ip_origen   VARCHAR(45) DEFAULT NULL,     -- IPv4 o IPv6
    sensor_id   VARCHAR(50) DEFAULT NULL,     -- 'Pi4-Felix', 'Pi4-Lopez', etc.
    created_at  DATETIME    DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_tipo       (tipo),
    INDEX idx_servicio   (servicio),
    INDEX idx_created_at (created_at),
    INDEX idx_ip         (ip_origen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================================
-- DATOS DE DEMOSTRACIÓN
-- Ejecuta este bloque para que el panel muestre gráficas
-- desde el primer día sin esperar eventos reales.
-- ============================================================

INSERT INTO eventos (tipo, servicio, ip_origen, sensor_id, created_at) VALUES
-- Hoy
('detectado', 'ssh', '185.220.101.5',  'Pi4-Felix', NOW()),
('bloqueado',  'ssh', '185.220.101.5', 'Pi4-Felix', NOW()),
('detectado', 'ftp', '91.108.4.15',   'Pi4-Felix', NOW()),
('detectado', 'web', '45.33.32.156',  'Pi4-Felix', NOW()),
('bloqueado',  'web', '45.33.32.156', 'Pi4-Felix', NOW()),

-- Ayer
('detectado', 'ssh', '194.165.16.99',  'Pi4-Felix', NOW() - INTERVAL 1 DAY),
('detectado', 'ssh', '194.165.16.99',  'Pi4-Felix', NOW() - INTERVAL 1 DAY),
('bloqueado',  'ssh', '194.165.16.99', 'Pi4-Felix', NOW() - INTERVAL 1 DAY),
('detectado', 'ftp', '185.142.236.34', 'Pi4-Felix', NOW() - INTERVAL 1 DAY),
('bloqueado',  'ftp', '185.142.236.34','Pi4-Felix', NOW() - INTERVAL 1 DAY),
('detectado', 'web', '104.21.8.200',   'Pi4-Felix', NOW() - INTERVAL 1 DAY),

-- Hace 2 días
('detectado', 'ssh', '45.95.147.21',  'Pi4-Felix', NOW() - INTERVAL 2 DAY),
('detectado', 'ssh', '45.95.147.21',  'Pi4-Felix', NOW() - INTERVAL 2 DAY),
('detectado', 'ssh', '45.95.147.21',  'Pi4-Felix', NOW() - INTERVAL 2 DAY),
('bloqueado',  'ssh', '45.95.147.21', 'Pi4-Felix', NOW() - INTERVAL 2 DAY),
('detectado', 'web', '162.55.37.9',   'Pi4-Felix', NOW() - INTERVAL 2 DAY),

-- Hace 3 días
('detectado', 'ftp', '185.220.101.7', 'Pi4-Felix', NOW() - INTERVAL 3 DAY),
('detectado', 'ftp', '185.220.101.7', 'Pi4-Felix', NOW() - INTERVAL 3 DAY),
('bloqueado',  'ftp', '185.220.101.7','Pi4-Felix', NOW() - INTERVAL 3 DAY),
('detectado', 'ssh', '91.240.118.22', 'Pi4-Felix', NOW() - INTERVAL 3 DAY),
('bloqueado',  'ssh', '91.240.118.22','Pi4-Felix', NOW() - INTERVAL 3 DAY),

-- Hace 4 días
('detectado', 'ssh', '193.32.162.44', 'Pi4-Felix', NOW() - INTERVAL 4 DAY),
('detectado', 'web', '104.18.22.110', 'Pi4-Felix', NOW() - INTERVAL 4 DAY),
('detectado', 'web', '104.18.22.110', 'Pi4-Felix', NOW() - INTERVAL 4 DAY),
('bloqueado',  'web', '104.18.22.110','Pi4-Felix', NOW() - INTERVAL 4 DAY),

-- Hace 5 días
('detectado', 'ftp', '185.156.73.91', 'Pi4-Felix', NOW() - INTERVAL 5 DAY),
('bloqueado',  'ftp', '185.156.73.91','Pi4-Felix', NOW() - INTERVAL 5 DAY),
('detectado', 'ssh', '176.97.210.4',  'Pi4-Felix', NOW() - INTERVAL 5 DAY),
('bloqueado',  'ssh', '176.97.210.4', 'Pi4-Felix', NOW() - INTERVAL 5 DAY),

-- Hace 6 días
('detectado', 'ssh', '5.188.206.17',  'Pi4-Felix', NOW() - INTERVAL 6 DAY),
('detectado', 'ssh', '5.188.206.17',  'Pi4-Felix', NOW() - INTERVAL 6 DAY),
('bloqueado',  'ssh', '5.188.206.17', 'Pi4-Felix', NOW() - INTERVAL 6 DAY),
('detectado', 'web', '2.56.245.1',    'Pi4-Felix', NOW() - INTERVAL 6 DAY);

-- ============================================================
-- NUEVAS TABLAS: Usuarios y Ajustes
-- ============================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    rol         ENUM('admin', 'cliente') NOT NULL DEFAULT 'cliente',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ajustes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    clave       VARCHAR(50) NOT NULL UNIQUE,
    valor       VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO usuarios (id, nombre, email, password, rol) VALUES
(1, 'Administrador', 'admin@SentinelIT.com', '0192023a7bbd73250516f069df18b500', 'admin'), -- admin123
(2, 'Cliente Especial', 'cliente1@SentinelIT.com', '53609805908f9a9415f3ec61bad26027', 'cliente'), -- cliente123
(3, 'Cliente Básico', 'cliente2@SentinelIT.com', '53609805908f9a9415f3ec61bad26027', 'cliente'); -- cliente123

INSERT INTO ajustes (clave, valor) VALUES 
('site_title', 'SentinelIT'),
('contact_email', 'info@SentinelIT.com');

CREATE TABLE IF NOT EXISTS sugerencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    comentario TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

