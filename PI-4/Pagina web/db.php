<?php
// ============================================================
// db.php — Conexión a MySQL
// AJUSTA: host, nombre de BD, usuario y contraseña
// ============================================================

define('DB_HOST', 'localhost');     // ← Cambia si tu MySQL está en otro servidor
define('DB_NAME', 'cyberguard');    // ← Nombre de tu base de datos
define('DB_USER', 'root');          // ← Tu usuario MySQL
define('DB_PASS', '');              // ← Tu contraseña MySQL

try {
    $pdo = new PDO(
        'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4',
        DB_USER,
        DB_PASS,
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
} catch (PDOException $e) {
    // Nunca mostrar el error real al usuario en producción
    error_log('Error BD: ' . $e->getMessage());
    die('<div style="text-align:center;padding:4rem;font-family:sans-serif;">
        <h2>Error de conexión</h2>
        <p>No se puede conectar a la base de datos. Revisa db.php.</p>
    </div>');
}
