<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

function is_session_active($pdo) {
    $session_php_id = session_id();
    if (!$session_php_id) {
        return false;
    }

    try {
        $stmt = $pdo->prepare("SELECT 1 FROM sesiones_activas WHERE session_php_id = ?");
        $stmt->execute([$session_php_id]);
        return (bool) $stmt->fetchColumn();
    } catch (PDOException $e) {
        error_log('Error comprobando sesión activa: ' . $e->getMessage());
        return false;
    }
}

function validar_sesion_activa($pdo) {
    if (!isset($_SESSION['usuario_id']) || !is_session_active($pdo)) {
        if (session_status() !== PHP_SESSION_NONE) {
            $_SESSION = [];
            @session_unset();
            @session_destroy();
        }
        return false;
    }
    return true;
}

function destroy_php_session_by_id($session_php_id) {
    if (!$session_php_id) {
        return false;
    }

    $savePath = session_save_path();
    if (!$savePath) {
        $savePath = sys_get_temp_dir();
    }

    $sessionFile = rtrim($savePath, '/\\') . DIRECTORY_SEPARATOR . 'sess_' . $session_php_id;
    if (file_exists($sessionFile)) {
        return @unlink($sessionFile);
    }

    return false;
}
