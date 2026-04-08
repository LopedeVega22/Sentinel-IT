<?php
require_once 'db.php';
$page_title = 'Sugerencias de Mejora';
require 'includes/header.php';

if (!isset($_SESSION['usuario_id'])) {
    header('Location: login.php');
    exit;
}

// Asegurarse de que la tabla sugerencias exista por si no han importado el schema.sql editado
$pdo->exec("CREATE TABLE IF NOT EXISTS sugerencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    comentario TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;");

$mensaje = '';
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['accion']) && $_POST['accion'] === 'crear_sugerencia') {
    $comentario = trim($_POST['comentario'] ?? '');
    if ($comentario) {
        $stmt = $pdo->prepare("INSERT INTO sugerencias (usuario_id, comentario) VALUES (?, ?)");
        $stmt->execute([$_SESSION['usuario_id'], $comentario]);
        $mensaje = '¡Gracias por tu sugerencia! Lo tendremos muy en cuenta.';
    } else {
        $error = 'El comentario no puede estar vacío.';
    }
}
?>
<?php require 'includes/navbar.php'; ?>

<main class="container-fluid my-5 px-lg-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="section-title m-0">Sugerencias y Mejoras</h2>
    </div>

    <div class="row g-4">
        <!-- Columna de formulario -->
        <div class="col-lg-5">
            <div class="card-cyber h-100">
                <h5 class="fw-bold mb-3">Envíanos tus ideas</h5>
                <?php if ($mensaje): ?>
                    <div class="alert alert-success"><?= htmlspecialchars($mensaje) ?></div>
                <?php endif; ?>
                <?php if ($error): ?>
                    <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
                <?php endif; ?>
                <form method="POST" action="sugerencias.php">
                    <input type="hidden" name="accion" value="crear_sugerencia">
                    <div class="mb-4">
                        <label class="form-label text-muted">¿Qué podemos mejorar del sistema?</label>
                        <textarea name="comentario" class="form-control form-control-cyber" rows="5" required placeholder="Escribe aquí tu sugerencia..."></textarea>
                    </div>
                    <button type="submit" class="btn-primary-cyber border-0 px-4 w-100"><i class="bi bi-send me-2"></i>Enviar Sugerencia</button>
                </form>
            </div>
        </div>
        
        <!-- Columna de comentarios (solo admin) -->
        <?php if ($_SESSION['rol'] === 'admin'): ?>
        <div class="col-lg-7">
            <div class="card-cyber h-100">
                <h5 class="fw-bold mb-3">Sugerencias Recibidas (Vista Admin)</h5>
                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead style="background-color: var(--color-bg); color: var(--color-text);">
                            <tr>
                                <th style="width: 25%">Usuario</th>
                                <th style="width: 55%">Sugerencia</th>
                                <th style="width: 20%">Fecha</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php
                            $stmt_sug = $pdo->query("SELECT s.*, u.nombre, u.email FROM sugerencias s JOIN usuarios u ON s.usuario_id = u.id ORDER BY s.id DESC");
                            if ($stmt_sug->rowCount() > 0):
                                while ($s = $stmt_sug->fetch(PDO::FETCH_ASSOC)):
                            ?>
                            <tr>
                                <td>
                                    <strong><?= htmlspecialchars($s['nombre']) ?></strong><br>
                                    <small class="text-muted"><?= htmlspecialchars($s['email']) ?></small>
                                </td>
                                <td><?= nl2br($s['comentario']) ?></td>
                                <td class="text-muted small"><?= htmlspecialchars($s['created_at']) ?></td>
                            </tr>
                            <?php 
                                endwhile; 
                            else:
                            ?>
                            <tr>
                                <td colspan="3" class="text-center text-muted py-4">No se han recibido sugerencias aún.</td>
                            </tr>
                            <?php endif; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <?php else: ?>
        <div class="col-lg-7 d-flex align-items-center justify-content-center">
            <div class="text-center text-muted">
                <i class="bi bi-lightbulb" style="font-size: 5rem; opacity: 0.2;"></i>
                <p class="mt-3">Apreciamos todos tus comentarios para seguir mejorando CyberGuard.</p>
            </div>
        </div>
        <?php endif; ?>
    </div>
</main>

<?php require 'includes/footer.php'; ?>
