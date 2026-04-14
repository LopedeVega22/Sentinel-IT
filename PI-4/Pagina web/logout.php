<?php
require_once 'db.php';
session_start();
require_once 'includes/logger.php';

// Eliminar sesión de BD
$session_id = session_id();
try {
    $stmt = $pdo->prepare("DELETE FROM sesiones_activas WHERE session_php_id = ?");
    $stmt->execute([$session_id]);
} catch (PDOException $e) {
    error_log('Error eliminando sesión: ' . $e->getMessage());
}

log_activity('logout');
session_destroy();
header('Location: index.php');
exit;
