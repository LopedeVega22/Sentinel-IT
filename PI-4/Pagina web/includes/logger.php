<?php
/**
 * includes/logger.php
 * Sistema de logs de actividad para exportación por MQTT y visualización admin.
 */
 
if (!function_exists('log_activity')) {
    function log_activity($action, $details = []) {
        $log_dir  = __DIR__ . '/../logs';
        $log_file = $log_dir . '/activity_logs.json';
 
        // CAMBIO 1: Crear la carpeta logs/ automáticamente si no existe.
        // Sin esto, file_put_contents() falla en silencio y NUNCA se escribe nada.
        if (!is_dir($log_dir)) {
            mkdir($log_dir, 0755, true);
        }
 
        // Datos de sesión
        $user_id   = $_SESSION['usuario_id'] ?? 'invitado';
        $user_name = $_SESSION['nombre']     ?? 'anónimo';
        $user_role = $_SESSION['rol']        ?? 'fuera_de_sesion';
 
        // CAMBIO 2: Fix IP spoofing.
        // El original sobreescribía REMOTE_ADDR con HTTP_X_FORWARDED_FOR, que
        // cualquier atacante puede falsificar con el header que quiera.
        // Ahora: REMOTE_ADDR es la IP fiable; X-Forwarded-For solo se guarda
        // como campo extra informativo, claramente etiquetado.
        $real_ip      = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
        $forwarded_ip = isset($_SERVER['HTTP_X_FORWARDED_FOR'])
            ? trim(explode(',', $_SERVER['HTTP_X_FORWARDED_FOR'])[0])
            : null;
 
        $log_entry = [
            'timestamp'    => date('Y-m-d H:i:s'),
            'user_id'      => $user_id,
            'user_name'    => $user_name,
            'role'         => $user_role,
            'ip'           => $real_ip,
            'forwarded_ip' => $forwarded_ip, // informativo, puede ser falsificado
            'action'       => $action,
            'details'      => $details,
        ];
 
        // Leer logs existentes
        $logs = [];
        if (file_exists($log_file)) {
            $content = file_get_contents($log_file);
            $decoded = json_decode($content, true);
            if (is_array($decoded)) {
                $logs = $decoded;
            }
        }
 
        // Insertar al principio (más reciente primero)
        array_unshift($logs, $log_entry);
 
        // Limitar a 500 registros para que el archivo no crezca indefinidamente
        if (count($logs) > 500) {
            array_splice($logs, 500);
        }
 
        // CAMBIO 3: LOCK_EX para evitar que dos peticiones simultáneas corrompan el JSON
        file_put_contents(
            $log_file,
            json_encode($logs, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE),
            LOCK_EX
        );
    }
}
?>
