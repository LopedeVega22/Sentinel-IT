<?php
// ============================================================
// db.php — Conexión a MySQL
// AJUSTA: host, nombre de BD, usuario y contraseña
// ============================================================

define('DB_HOST', '127.0.0.1');     // ← Cambia si tu MySQL está en otro servidor
define('DB_NAME', 'SentinelIT');    // ← Nombre de tu base de datos
define('DB_USER', 'root');          // ← Tu usuario MySQL
define('DB_PASS', 'C0ntr4senAs3gur4');      // ← Tu contraseña MySQL

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
    die('<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Error de conexión</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body { background: #F8F9FA; color: #212529; font-family: "DM Sans", sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .error-container { text-align: center; background: #FFFFFF; padding: 3rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.12); max-width: 500px; }
        h2 { font-family: "Syne", sans-serif; color: #DC3545; margin-top: 0; font-size: 2rem; }
        p { color: #6C757D; line-height: 1.6; margin-bottom: 0; }
    </style>
</head>
<body>
    <div class="error-container">
        <h2>Error de conexión</h2>
        <p>No se ha podido conectar a la base de datos.<br>Por favor, revisa tus credenciales en <strong>db.php</strong>.</p>
    </div>
</body>
</html>');
}

