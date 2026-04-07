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

// Guardar ajustes
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
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
}

// Obtener valor actual
$stmt = $pdo->query("SELECT clave, valor FROM ajustes");
$ajustes_actuales = [];
while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
    $ajustes_actuales[$row['clave']] = $row['valor'];
}
?>

<?php require 'includes/navbar.php'; ?>

<main class="container my-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="section-title m-0">Ajustes Rápidos</h2>
        <a href="panel.php" class="btn-outline-cyber">Ver Panel de Gráficas</a>
    </div>

    <?php if ($mensaje): ?>
        <div class="alert alert-success"><?= htmlspecialchars($mensaje) ?></div>
    <?php endif; ?>

    <div class="card-cyber" style="max-width: 600px;">
        <form method="POST" action="admin.php">
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
</main>

<?php require 'includes/footer.php'; ?>
