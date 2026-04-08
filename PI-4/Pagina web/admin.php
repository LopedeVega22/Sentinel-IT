<?php
require_once 'db.php';
// Header ya llama a session_start()
$page_title = 'Panel de Administración';
require 'includes/header.php';

if (!isset($_SESSION['usuario_id']) || $_SESSION['rol'] !== 'admin') {
    header('Location: login.php');
    exit;
}

$mensaje = '';
$error_usuario = '';
$exito_usuario = '';

// Guardar ajustes y procesos POST
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['accion']) && $_POST['accion'] === 'guardar_ajustes') {
        $nuevo_titulo = trim($_POST['site_title'] ?? '');
        $nuevo_email = trim($_POST['contact_email'] ?? '');

        if ($nuevo_titulo && $nuevo_email) {
            $stmt = $pdo->prepare("UPDATE ajustes SET valor = CASE clave WHEN 'site_title' THEN ? WHEN 'contact_email' THEN ? END WHERE clave IN ('site_title', 'contact_email')");
            $stmt->execute([$nuevo_titulo, $nuevo_email]);
            $mensaje = 'Ajustes actualizados correctamente.';
            // Recargar variables globales
            $site_title_global = $nuevo_titulo;
            $contact_email_global = $nuevo_email;
        }
    } elseif (isset($_POST['accion']) && $_POST['accion'] === 'crear_usuario') {
        $nombre = trim($_POST['new_user_nombre'] ?? '');
        $email = trim($_POST['new_user_email'] ?? '');
        $password = $_POST['new_user_password'] ?? '';
        $rol = $_POST['new_user_rol'] ?? 'cliente';

        if ($nombre && $email && $password) {
            try {
                $stmt = $pdo->prepare("SELECT id FROM usuarios WHERE email = ?");
                $stmt->execute([$email]);
                if ($stmt->fetch()) {
                    $error_usuario = "El correo ya está registrado en el sistema.";
                } else {
                    $hash = md5($password);
                    $stmt = $pdo->prepare("INSERT INTO usuarios (nombre, email, password, rol) VALUES (?, ?, ?, ?)");
                    $stmt->execute([$nombre, $email, $hash, $rol]);
                    $exito_usuario = "Usuario creado con éxito.";
                }
            } catch (PDOException $e) {
                $error_usuario = "Error de base de datos al crear el usuario.";
            }
        } else {
            $error_usuario = "Por favor, completa todos los campos del nuevo usuario.";
        }
    } elseif (isset($_POST['accion']) && $_POST['accion'] === 'cambiar_password') {
        $usuario_id = $_POST['usuario_id'] ?? '';
        $nueva_password = $_POST['nueva_password'] ?? '';

        if ($usuario_id && $nueva_password) {
            try {
                $hash = md5($nueva_password);
                $stmt = $pdo->prepare("UPDATE usuarios SET password = ? WHERE id = ?");
                $stmt->execute([$hash, $usuario_id]);
                // Reusing success var since they render in the same column
                $exito_usuario = "Contraseña de la cuenta actualizada exitosamente.";
            } catch (PDOException $e) {
                $error_usuario = "Error al actualizar la contraseña en la base de datos.";
            }
        } else {
            $error_usuario = "Por favor, selecciona un usuario y escribe la nueva contraseña.";
        }
    } elseif (isset($_POST['accion']) && $_POST['accion'] === 'eliminar_usuario') {
        $usuario_id = $_POST['usuario_id'] ?? '';
        
        if ($usuario_id && $usuario_id != $_SESSION['usuario_id']) {
            try {
                $stmt = $pdo->prepare("DELETE FROM usuarios WHERE id = ?");
                $stmt->execute([$usuario_id]);
                $exito_usuario = "Usuario eliminado con éxito.";
            } catch (PDOException $e) {
                $error_usuario = "Error al eliminar el usuario.";
            }
        } else {
            $error_usuario = "No puedes eliminar tu propia cuenta o ID inválido.";
        }
    }
}

// Obtener valor actual
$stmt = $pdo->query("SELECT clave, valor FROM ajustes");
$ajustes_actuales = [];
while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
    $ajustes_actuales[$row['clave']] = $row['valor'];
}
?>

<?php require 'includes/navbar.php'; ?>

<main class="container-fluid my-5 px-lg-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="section-title m-0">Panel de Administración</h2>
        <div>
            <a href="sugerencias.php" class="btn-outline-cyber me-2"><i class="bi bi-chat-left-text me-1"></i>Ver Sugerencias</a>
            <a href="panel.php" class="btn-outline-cyber">Ver Panel de Gráficas</a>
        </div>
    </div>

    <div class="row g-4 mb-4">
        <!-- Columna 1: Ajustes -->
        <div class="col-lg-4">
            <div class="card-cyber h-100">
                <h5 class="mb-3 fw-bold">Ajustes Rápidos</h5>
                <form method="POST" action="admin.php">
                    <input type="hidden" name="accion" value="guardar_ajustes">
                    <div class="mb-3">
                        <label for="site_title" class="form-label text-muted">Título de la web (Navbar, Header)</label>
                        <input type="text" class="form-control form-control-cyber" id="site_title" name="site_title" 
                               value="<?= htmlspecialchars($ajustes_actuales['site_title'] ?? '') ?>" required>
                    </div>
                    <div class="mb-4">
                        <label for="contact_email" class="form-label text-muted">Email de contacto (Footer)</label>
                        <input type="email" class="form-control form-control-cyber" id="contact_email" name="contact_email" 
                               value="<?= htmlspecialchars($ajustes_actuales['contact_email'] ?? '') ?>" required>
                    </div>
                    
                    <button type="submit" class="btn-primary-cyber w-100 border-0">Guardar Ajustes</button>
                </form>
            </div>
        </div>

        <!-- Columna 2: Añadir Usuario -->
        <div class="col-lg-4">
            <div class="card-cyber h-100">
                <h5 class="mb-3 fw-bold">Añadir Nuevo Usuario</h5>
                <form method="POST" action="admin.php">
                    <input type="hidden" name="accion" value="crear_usuario">
                    <div class="mb-3">
                        <label class="form-label text-muted">Nombre</label>
                        <input type="text" class="form-control form-control-cyber" name="new_user_nombre" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted">Correo electrónico</label>
                        <input type="email" class="form-control form-control-cyber" name="new_user_email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted">Contraseña</label>
                        <input type="password" class="form-control form-control-cyber" name="new_user_password" required>
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted">Rol en el sistema</label>
                        <select class="form-select form-control-cyber" name="new_user_rol">
                            <option value="cliente">Cliente (Acceso panel básico)</option>
                            <option value="admin">Administrador</option>
                        </select>
                    </div>
                    <button type="submit" class="btn-primary-cyber w-100 border-0">Crear Cuenta</button>
                </form>
            </div>
        </div>

        <!-- Columna 3: Cambiar Contraseña -->
        <div class="col-lg-4">
            <div class="card-cyber h-100">
                <h5 class="mb-3 fw-bold">Cambiar Contraseña</h5>
                <form method="POST" action="admin.php">
                    <input type="hidden" name="accion" value="cambiar_password">
                    <div class="mb-3">
                        <label class="form-label text-muted">Seleccionar Usuario</label>
                        <select class="form-select form-control-cyber" name="usuario_id" required>
                            <option value="">-- Elige un usuario --</option>
                            <?php
                            $stmt_dropdown = $pdo->query("SELECT id, nombre, email FROM usuarios ORDER BY nombre ASC");
                            while ($u_dd = $stmt_dropdown->fetch(PDO::FETCH_ASSOC)):
                            ?>
                                <option value="<?= htmlspecialchars($u_dd['id']) ?>">
                                    <?= htmlspecialchars($u_dd['nombre']) ?> (<?= htmlspecialchars($u_dd['email']) ?>)
                                </option>
                            <?php endwhile; ?>
                        </select>
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted">Nueva Contraseña</label>
                        <input type="password" class="form-control form-control-cyber" name="nueva_password" required>
                    </div>
                    <button type="submit" class="btn-primary-cyber w-100 border-0" style="background:var(--color-accent); color:#1a1a1a;">Actualizar Contraseña</button>
                </form>
            </div>
        </div>
    </div>

    <!-- Fila 2: Tabla de usuarios -->
    <div class="row">
        <div class="col-12">
            <div class="card-cyber">
                <h5 class="mb-4 fw-bold">Cuentas Registradas</h5>
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead style="background-color: var(--color-bg); color: var(--color-text);">
                            <tr>
                                <th>ID</th>
                                <th>Nombre</th>
                                <th>Email</th>
                                <th>Rol</th>
                                <th>Fecha Alta</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php
                            $stmt_users = $pdo->query("SELECT id, nombre, email, rol, created_at FROM usuarios ORDER BY id DESC");
                            while ($u = $stmt_users->fetch(PDO::FETCH_ASSOC)):
                            ?>
                            <tr>
                                <td><?= htmlspecialchars($u['id']) ?></td>
                                <td class="fw-bold"><?= htmlspecialchars($u['nombre']) ?></td>
                                <td><?= htmlspecialchars($u['email']) ?></td>
                                <td>
                                    <?php if($u['rol'] === 'admin'): ?>
                                        <span class="badge bg-danger">Admin</span>
                                    <?php else: ?>
                                        <span class="badge bg-primary">Cliente</span>
                                    <?php endif; ?>
                                </td>
                                <td class="text-muted small"><?= htmlspecialchars($u['created_at']) ?></td>
                                <td>
                                    <?php if ($u['id'] != $_SESSION['usuario_id']): ?>
                                        <form method="POST" action="admin.php" onsubmit="return confirm('¿Seguro que quieres eliminar este usuario?');" style="display:inline;">
                                            <input type="hidden" name="accion" value="eliminar_usuario">
                                            <input type="hidden" name="usuario_id" value="<?= htmlspecialchars($u['id']) ?>">
                                            <button type="submit" class="btn btn-sm btn-danger"><i class="bi bi-trash"></i> Eliminar</button>
                                        </form>
                                    <?php endif; ?>
                                </td>
                            </tr>
                            <?php endwhile; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</main>

<!-- Contenedor para Notificaciones Flotantes (Toasts) -->
<div class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 1100">
    <div id="cyberToast" class="toast align-items-center text-white border-0" role="alert" aria-live="assertive" aria-atomic="true" style="background: var(--color-bg-card); border: 1px solid var(--color-primary) !important;">
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-info-circle me-2 text-primary" id="toastIcon"></i>
                <span id="toastMessage"></span>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    <?php 
    $msg_final = $mensaje ?: $exito_usuario ?: $error_usuario;
    $tipo_msg = $error_usuario ? 'error' : 'success';
    if ($msg_final): 
    ?>
    const toastElem = document.getElementById('cyberToast');
    const toastBody = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');
    
    toastBody.textContent = "<?= addslashes($msg_final) ?>";
    
    if ("<?= $tipo_msg ?>" === 'error') {
        toastElem.style.borderColor = "var(--color-danger)";
        toastIcon.className = "bi bi-exclamation-triangle-fill me-2 text-danger";
    } else {
        toastElem.style.borderColor = "var(--color-primary)";
        toastIcon.className = "bi bi-check-circle-fill me-2 text-primary";
    }

    const toast = new bootstrap.Toast(toastElem, { delay: 4000 });
    toast.show();
    <?php endif; ?>
});
</script>

<?php require 'includes/footer.php'; ?>
