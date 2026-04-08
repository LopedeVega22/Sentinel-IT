<?php
require_once 'db.php';
session_start();

// Si ya está logueado
if (isset($_SESSION['usuario_id'])) {
    header('Location: ' . ($_SESSION['rol'] === 'admin' ? 'admin.php' : 'panel.php'));
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email'] ?? '');
    $password = $_POST['password'] ?? '';

        if ($email && $password) {
            $stmt = $pdo->prepare("SELECT id, nombre, password, rol FROM usuarios WHERE email = ?");
            $stmt->execute([$email]);
            $user = $stmt->fetch();

            if ($user && md5($password) === $user['password']) {
                // Login correcto
                $_SESSION['usuario_id'] = $user['id'];
                $_SESSION['nombre'] = $user['nombre'];
                $_SESSION['rol'] = $user['rol'];
            
            header('Location: ' . ($user['rol'] === 'admin' ? 'admin.php' : 'panel.php'));
            exit;
        } else {
            $error = 'Credenciales incorrectas.';
        }
    } else {
        $error = 'Por favor, rellena todos los campos.';
    }
}

$page_title = 'Iniciar Sesión';
require 'includes/header.php';
require 'includes/navbar.php';
?>

<main class="container my-5" style="max-width: 500px">
    <h2 class="section-title text-center mb-4">Iniciar Sesión</h2>
    
    <?php if ($error): ?>
        <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <div class="card-cyber">
        <form method="POST" action="login.php">
            <div class="mb-3">
                <label for="email" class="form-label">Correo electrónico</label>
                <input type="text" class="form-control form-control-cyber" id="email" name="email" required placeholder="correo@ejemplo.com">
            </div>
            <div class="mb-4">
                <label for="password" class="form-label">Contraseña</label>
                <input type="password" class="form-control form-control-cyber" id="password" name="password" required>
            </div>
            <button type="submit" class="btn-primary-cyber w-100 text-center border-0">Entrar</button>
        </form>
    </div>
</main>

<?php require 'includes/footer.php'; ?>