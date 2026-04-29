<?php
/**
 * cerrar_sesion_admin.php
 * Script para que el ADMIN DEL SERVER cierre sesiones de usuarios
 * 
 * USO DESDE LÍNEA DE COMANDOS:
 * php cerrar_sesion_admin.php --listar
 * php cerrar_sesion_admin.php --cerrar-usuario 3
 * php cerrar_sesion_admin.php --cerrar-nombre "Admin"
 * php cerrar_sesion_admin.php --cerrar-email admin@cybergard.com
 * php cerrar_sesion_admin.php --cerrar-sesion abc123xyz789
 * 
 * O DESDE NAVEGADOR (NO RECOMENDADO EN PRODUCCIÓN):
 * http://localhost/PI-4/Pagina%20web/cerrar_sesion_admin.php?action=listar
 * http://localhost/PI-4/Pagina%20web/cerrar_sesion_admin.php?action=cerrar_usuario&usuario_id=3
 * http://localhost/PI-4/Pagina%20web/cerrar_sesion_admin.php?action=cerrar_nombre&nombre=Admin
 * http://localhost/PI-4/Pagina%20web/cerrar_sesion_admin.php?action=cerrar_email&email=admin@cybergard.com
 */

require_once 'db.php';
require_once 'includes/session_control.php';

// Detectar si es CLI o HTTP
$is_cli = php_sapi_name() === 'cli';
$mode = $is_cli ? 'cli' : 'http';

// ============================================================
// FUNCIÓN: Listar todas las sesiones activas
// ============================================================
function listar_sesiones_activas($pdo) {
    try {
        $stmt = $pdo->query("
            SELECT id, usuario_id, nombre_usuario, email, session_php_id, 
                   ip_origen, creada_en, ultima_actividad
            FROM sesiones_activas
            ORDER BY ultima_actividad DESC
        ");
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (PDOException $e) {
        return ['error' => $e->getMessage()];
    }
}

// ============================================================
// FUNCIÓN: Cerrar sesión específica
// ============================================================
function cerrar_sesion($pdo, $session_php_id) {
    try {
        $stmt = $pdo->prepare("
            SELECT usuario_id, nombre_usuario, email 
            FROM sesiones_activas 
            WHERE session_php_id = ?
        ");
        $stmt->execute([$session_php_id]);
        $sesion = $stmt->fetch();
        
        if (!$sesion) {
            return ['error' => 'Sesión no encontrada'];
        }
        
        $stmt_delete = $pdo->prepare("DELETE FROM sesiones_activas WHERE session_php_id = ?");
        $stmt_delete->execute([$session_php_id]);
        destroy_php_session_by_id($session_php_id);
        
        return [
            'success' => true,
            'mensaje' => 'Sesión cerrada',
            'usuario' => $sesion['nombre_usuario'],
            'email' => $sesion['email']
        ];
    } catch (PDOException $e) {
        return ['error' => $e->getMessage()];
    }
}

// ============================================================
// FUNCIÓN: Cerrar todas las sesiones de un usuario
// ============================================================
function cerrar_todas_usuario($pdo, $usuario_id) {
    try {
        $stmt_get = $pdo->prepare("
            SELECT id, nombre_usuario, email, COUNT(*) as total
            FROM sesiones_activas 
            WHERE usuario_id = ?
            GROUP BY usuario_id
        ");
        $stmt_get->execute([$usuario_id]);
        $usuario = $stmt_get->fetch();
        
        if (!$usuario) {
            return ['error' => 'Usuario no tiene sesiones activas'];
        }
        
        $stmt_get = $pdo->prepare("SELECT session_php_id FROM sesiones_activas WHERE usuario_id = ?");
        $stmt_get->execute([$usuario_id]);
        $sesiones = $stmt_get->fetchAll(PDO::FETCH_ASSOC);
        foreach ($sesiones as $s) {
            destroy_php_session_by_id($s['session_php_id']);
        }

        $stmt_delete = $pdo->prepare("DELETE FROM sesiones_activas WHERE usuario_id = ?");
        $stmt_delete->execute([$usuario_id]);
        
        return [
            'success' => true,
            'mensaje' => 'Todas las sesiones del usuario cerradas',
            'usuario' => $usuario['nombre_usuario'],
            'sesiones_cerradas' => $usuario['total']
        ];
    } catch (PDOException $e) {
        return ['error' => $e->getMessage()];
    }
}

// ============================================================
// FUNCIÓN: Cerrar sesiones activas por nombre (incluso si usuario no existe en DB)
// ============================================================
function cerrar_sesiones_por_nombre_activo($pdo, $nombre) {
    try {
        $stmt_get = $pdo->prepare("
            SELECT session_php_id, nombre_usuario, email, COUNT(*) as total
            FROM sesiones_activas 
            WHERE LOWER(nombre_usuario) = LOWER(?)
            GROUP BY nombre_usuario
        ");
        $stmt_get->execute([$nombre]);
        $usuario = $stmt_get->fetch();
        
        if (!$usuario) {
            return ['error' => 'No hay sesiones activas para este nombre'];
        }
        
        $stmt_get_sessions = $pdo->prepare("SELECT session_php_id FROM sesiones_activas WHERE LOWER(nombre_usuario) = LOWER(?)");
        $stmt_get_sessions->execute([$nombre]);
        $sesiones = $stmt_get_sessions->fetchAll(PDO::FETCH_ASSOC);
        foreach ($sesiones as $s) {
            destroy_php_session_by_id($s['session_php_id']);
        }

        $stmt_delete = $pdo->prepare("DELETE FROM sesiones_activas WHERE LOWER(nombre_usuario) = LOWER(?)");
        $stmt_delete->execute([$nombre]);
        
        return [
            'success' => true,
            'mensaje' => 'Sesiones cerradas por nombre (usuario puede no existir en DB)',
            'usuario' => $usuario['nombre_usuario'],
            'sesiones_cerradas' => $usuario['total']
        ];
    } catch (PDOException $e) {
        return ['error' => $e->getMessage()];
    }
}

// ============================================================
// FUNCIÓN: Cerrar todas las sesiones de un usuario por nombre
// ============================================================
function cerrar_por_nombre($pdo, $nombre) {
    try {
        // Primero intenta buscar en tabla usuarios
        $stmt = $pdo->prepare("SELECT id, nombre, email FROM usuarios WHERE LOWER(nombre) = LOWER(?)");
        $stmt->execute([$nombre]);
        $usuario = $stmt->fetch();
        
        if ($usuario) {
            // Usuario existe en DB, cierra por ID
            return cerrar_todas_usuario($pdo, $usuario['id']);
        } else {
            // Usuario no existe, busca en sesiones activas
            return cerrar_sesiones_por_nombre_activo($pdo, $nombre);
        }
    } catch (PDOException $e) {
        return ['error' => $e->getMessage()];
    }
}

// ============================================================
// FUNCIÓN: Cerrar todas las sesiones de un usuario por email
// ============================================================
function cerrar_por_email($pdo, $email) {
    try {
        // Primero intenta buscar en tabla usuarios
        $stmt = $pdo->prepare("SELECT id, nombre, email FROM usuarios WHERE LOWER(email) = LOWER(?)");
        $stmt->execute([$email]);
        $usuario = $stmt->fetch();
        
        if ($usuario) {
            // Usuario existe en DB, cierra por ID
            return cerrar_todas_usuario($pdo, $usuario['id']);
        } else {
            // Usuario no existe, busca en sesiones activas
            return cerrar_sesiones_por_email_activo($pdo, $email);
        }
    } catch (PDOException $e) {
        return ['error' => $e->getMessage()];
    }
}

if ($is_cli) {
    // ========== MODO CLI (línea de comandos) ==========
    
    global $argv;
    $action = $argv[1] ?? null;
    
    if (!$action) {
        echo " Error: Especifica una acción\n";
        echo "\nUSOː\n";
        echo "  php cerrar_sesion_admin.php --listar\n";
        echo "  php cerrar_sesion_admin.php --cerrar-usuario <usuario_id>\n";
        echo "  php cerrar_sesion_admin.php --cerrar-nombre <nombre_usuario>\n";
        echo "  php cerrar_sesion_admin.php --cerrar-email <email_usuario>\n";
        echo "  php cerrar_sesion_admin.php --cerrar-sesion <session_id>\n";
        echo "\nEjemplos:\n";
        echo "  php cerrar_sesion_admin.php --listar\n";
        echo "  php cerrar_sesion_admin.php --cerrar-usuario 3\n";
        echo "  php cerrar_sesion_admin.php --cerrar-nombre 'Admin'\n";
        echo "  php cerrar_sesion_admin.php --cerrar-email admin@cybergard.com\n";
        echo "  php cerrar_sesion_admin.php --cerrar-sesion abc123xyz789\n";
        exit(1);
    }
    
    switch ($action) {
        case '--listar':
            $sesiones = listar_sesiones_activas($pdo);
            if (isset($sesiones['error'])) {
                echo " Error: {$sesiones['error']}\n";
                exit(1);
            }
            
            if (empty($sesiones)) {
                echo "ℹ  No hay sesiones activas\n";
                exit(0);
            }
            
            echo " SESIONES ACTIVAS (" . count($sesiones) . ")\n";
            echo str_repeat("=", 100) . "\n";
            echo sprintf(
                "%-3s %-4s %-20s %-30s %-15s %-20s %s\n",
                "ID", "UID", "Usuario", "Email", "IP Origen", "Conectado", "Última Act."
            );
            echo str_repeat("-", 100) . "\n";
            
            foreach ($sesiones as $s) {
                echo sprintf(
                    "%-3d %-4d %-20s %-30s %-15s %-20s %s\n",
                    $s['id'],
                    $s['usuario_id'],
                    substr($s['nombre_usuario'], 0, 20),
                    substr($s['email'], 0, 30),
                    $s['ip_origen'],
                    date('d/m H:i', strtotime($s['creada_en'])),
                    date('H:i:s', strtotime($s['ultima_actividad']))
                );
            }
            echo str_repeat("=", 100) . "\n";
            break;
        
        case '--cerrar-usuario':
            $usuario_id = $argv[2] ?? null;
            if (!$usuario_id) {
                echo " Error: Especifica usuario_id\n";
                echo "USO: php cerrar_sesion_admin.php --cerrar-usuario <usuario_id>\n";
                exit(1);
            }
            
            $resultado = cerrar_todas_usuario($pdo, $usuario_id);
            
            if (isset($resultado['error'])) {
                echo " Error: {$resultado['error']}\n";
                exit(1);
            }
            
            echo " {$resultado['mensaje']}\n";
            echo "   Usuario: {$resultado['usuario']}\n";
            echo "   Sesiones cerradas: {$resultado['sesiones_cerradas']}\n";
            break;
        
        case '--cerrar-nombre':
            $nombre = $argv[2] ?? null;
            if (!$nombre) {
                echo " Error: Especifica nombre de usuario\n";
                echo "USO: php cerrar_sesion_admin.php --cerrar-nombre <nombre_usuario>\n";
                exit(1);
            }
            
            $resultado = cerrar_por_nombre($pdo, $nombre);
            
            if (isset($resultado['error'])) {
                echo " Error: {$resultado['error']}\n";
                exit(1);
            }
            
            echo " {$resultado['mensaje']}\n";
            echo "   Usuario: {$resultado['usuario']}\n";
            echo "   Sesiones cerradas: {$resultado['sesiones_cerradas']}\n";
            break;
        
        case '--cerrar-email':
            $email = $argv[2] ?? null;
            if (!$email) {
                echo " Error: Especifica email de usuario\n";
                echo "USO: php cerrar_sesion_admin.php --cerrar-email <email_usuario>\n";
                exit(1);
            }
            
            $resultado = cerrar_por_email($pdo, $email);
            
            if (isset($resultado['error'])) {
                echo " Error: {$resultado['error']}\n";
                exit(1);
            }
            
            echo " {$resultado['mensaje']}\n";
            echo "   Usuario: {$resultado['usuario']}\n";
            echo "   Sesiones cerradas: {$resultado['sesiones_cerradas']}\n";
            break;
        
        case '--cerrar-sesion':
            $session_id = $argv[2] ?? null;
            if (!$session_id) {
                echo " Error: Especifica session_id\n";
                echo "USO: php cerrar_sesion_admin.php --cerrar-sesion <session_id>\n";
                exit(1);
            }
            
            $resultado = cerrar_sesion($pdo, $session_id);
            
            if (isset($resultado['error'])) {
                echo " Error: {$resultado['error']}\n";
                exit(1);
            }
            
            echo " {$resultado['mensaje']}\n";
            echo "   Usuario: {$resultado['usuario']}\n";
            echo "   Email: {$resultado['email']}\n";
            break;
        
        default:
            echo " Error: Acción no reconocida: $action\n";
            exit(1);
    }
    
} else {
    // ========== MODO HTTP (navegador) ==========
    header('Content-Type: application/json; charset=utf-8');
    
    $action = $_GET['action'] ?? null;
    
    if (!$action) {
        http_response_code(400);
        echo json_encode(['error' => 'Acción no especificada']);
        exit;
    }
    
    switch ($action) {
        case 'listar':
            $sesiones = listar_sesiones_activas($pdo);
            echo json_encode(['sesiones' => $sesiones]);
            break;
        
        case 'cerrar_usuario':
            $usuario_id = $_GET['usuario_id'] ?? null;
            if (!$usuario_id) {
                http_response_code(400);
                echo json_encode(['error' => 'usuario_id requerido']);
                exit;
            }
            $resultado = cerrar_todas_usuario($pdo, $usuario_id);
            echo json_encode($resultado);
            break;
        
        case 'cerrar_nombre':
            $nombre = $_GET['nombre'] ?? null;
            if (!$nombre) {
                http_response_code(400);
                echo json_encode(['error' => 'nombre requerido']);
                exit;
            }
            $resultado = cerrar_por_nombre($pdo, $nombre);
            echo json_encode($resultado);
            break;
        
        case 'cerrar_email':
            $email = $_GET['email'] ?? null;
            if (!$email) {
                http_response_code(400);
                echo json_encode(['error' => 'email requerido']);
                exit;
            }
            $resultado = cerrar_por_email($pdo, $email);
            echo json_encode($resultado);
            break;
        
        case 'cerrar_sesion':
            $session_id = $_GET['session_id'] ?? null;
            if (!$session_id) {
                http_response_code(400);
                echo json_encode(['error' => 'session_id requerido']);
                exit;
            }
            $resultado = cerrar_sesion($pdo, $session_id);
            echo json_encode($resultado);
            break;
        
        default:
            http_response_code(400);
            echo json_encode(['error' => 'Acción no reconocida']);
    }
}
