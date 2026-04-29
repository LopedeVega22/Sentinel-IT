<?php
/**
 * admin_logs.php
 * Visualización del registro de actividad en formato JSON.
 */
 
require_once 'db.php';
require_once 'includes/logger.php';
require_once 'includes/session_control.php';
$page_title = 'Logs de Actividad';
require 'includes/header.php';
 
// Protección: Solo admin
if (!validar_sesion_activa($pdo) || $_SESSION['rol'] !== 'admin') {
    header('Location: login.php');
    exit;
}
 
// CAMBIO: Ruta definida como constante local para no repetirla
$log_dir  = __DIR__ . '/logs';
$log_file = $log_dir . '/activity_logs.json';
$logs = [];
 
// Acción de limpiar logs
if (isset($_POST['accion']) && $_POST['accion'] === 'limpiar_logs') {
    // CAMBIO: Crear carpeta si no existe antes de intentar escribir
    if (!is_dir($log_dir)) {
        mkdir($log_dir, 0755, true);
    }
    file_put_contents($log_file, json_encode([]), LOCK_EX);
    log_activity('logs_limpiados');
    header('Location: admin_logs.php');
    exit;
}
 
if (file_exists($log_file)) {
    $content = file_get_contents($log_file);
    $logs = json_decode($content, true);
    if (!is_array($logs)) {
        $logs = [];
    }
}
 
require 'includes/navbar.php';
?>
 
<main class="container-fluid my-5 px-lg-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="section-title m-0">Registro de Actividad (JSON/MQTT)</h2>
            <p class="text-muted">Visualización de los últimos eventos registrados en el sistema.</p>
        </div>
        <div>
            <form method="POST" onsubmit="return confirm('¿Estás seguro de que quieres vaciar el registro de actividad?');" style="display:inline;">
                <input type="hidden" name="accion" value="limpiar_logs">
                <button type="submit" class="btn btn-outline-danger btn-sm"><i class="bi bi-trash me-1"></i>Limpiar Registro</button>
            </form>
            <a href="admin.php" class="btn-outline-cyber btn-sm ms-2"><i class="bi bi-arrow-left me-1"></i>Volver al Panel</a>
        </div>
    </div>
 
    <div class="card-cyber">
        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead style="background-color: var(--color-bg); color: var(--color-text);">
                    <tr>
                        <th style="width: 13%">Fecha y Hora</th>
                        <th style="width: 13%">Usuario</th>
                        <th style="width: 8%">Rol</th>
                        <th style="width: 13%">Acción</th>
                        <th style="width: 12%">IP Real</th>
                        <th style="width: 12%">IP Forwarded</th>
                        <th style="width: 29%">Detalles (JSON)</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($logs)): ?>
                    <tr>
                        <td colspan="7" class="text-center py-5 text-muted">
                            <i class="bi bi-journal-x d-block mb-3" style="font-size: 3rem; opacity: 0.3;"></i>
                            No hay registros de actividad disponibles.
                        </td>
                    </tr>
                    <?php else: ?>
                        <?php foreach ($logs as $log): ?>
                        <tr>
                            <td class="text-nowrap fw-bold"><?= htmlspecialchars($log['timestamp']) ?></td>
                            <td>
                                <strong><?= htmlspecialchars($log['user_name']) ?></strong><br>
                                <small class="text-muted">ID: <?= htmlspecialchars($log['user_id']) ?></small>
                            </td>
                            <td>
                                <?php
                                    $rol = $log['role'];
                                    $badge_class = 'bg-secondary';
                                    if ($rol === 'admin')          $badge_class = 'bg-danger';
                                    if ($rol === 'cliente')        $badge_class = 'bg-primary';
                                    if ($rol === 'invitado')       $badge_class = 'bg-warning text-dark';
                                    if ($rol === 'fuera_de_sesion') $badge_class = 'bg-secondary';
                                ?>
                                <span class="badge <?= $badge_class ?>"><?= htmlspecialchars($rol) ?></span>
                            </td>
                            <td>
                                <code class="px-2 py-1 rounded" style="background: rgba(0, 243, 255, 0.1); color: var(--color-primary);">
                                    <?= htmlspecialchars($log['action']) ?>
                                </code>
                            </td>
                            <td class="text-muted small"><?= htmlspecialchars($log['ip']) ?></td>
                            <!-- CAMBIO: Nueva columna forwarded_ip para distinguir IP real de la declarada -->
                            <td class="text-muted small">
                                <?php if (!empty($log['forwarded_ip'])): ?>
                                    <span title="Puede ser falsificada" style="color: var(--color-warning);">
                                        <?= htmlspecialchars($log['forwarded_ip']) ?>
                                        <i class="bi bi-exclamation-triangle-fill ms-1" style="font-size:0.7rem"></i>
                                    </span>
                                <?php else: ?>
                                    <span class="text-muted">—</span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <div class="details-json small text-muted" style="max-height: 60px; overflow-y: auto; font-family: monospace;">
                                    <?= htmlspecialchars(json_encode($log['details'], JSON_UNESCAPED_UNICODE)) ?>
                                </div>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</main>
 
<style>
    .details-json::-webkit-scrollbar { width: 4px; }
    .details-json::-webkit-scrollbar-thumb { background: rgba(0, 243, 255, 0.2); border-radius: 4px; }
    table tr:hover code { background: var(--color-primary) !important; color: #1a1a1a !important; }
</style>
 
<?php require 'includes/footer.php'; ?>
