<?php
// includes/navbar.php
$actual = basename($_SERVER['PHP_SELF']);
function activo($archivo) {
    global $actual;
    return $actual === $archivo ? 'active' : '';
}
?>
<nav class="navbar navbar-expand-lg navbar-light sticky-top" id="mainNav">
    <div class="container">
        <a class="navbar-brand fw-bold" href="index.php">
            <i class="bi bi-shield-fill-check me-2" style="color:var(--color-primary)"></i><?= htmlspecialchars($site_title_global ?? 'CyberGuard') ?>
        </a>
        <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMenu">
            <ul class="navbar-nav ms-auto align-items-lg-center gap-lg-1">
                <li class="nav-item">
                    <a class="nav-link <?= activo('index.php') ?>" href="index.php">Inicio</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= activo('servicios.php') ?>" href="servicios.php">Servicios</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= activo('como-funciona.php') ?>" href="como-funciona.php">Cómo funciona</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= activo('tecnologias.php') ?>" href="tecnologias.php">Tecnologías</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= activo('equipo.php') ?>" href="equipo.php">Equipo</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= activo('contacto.php') ?>" href="contacto.php">Contacto</a>
                </li>
                <?php if (isset($_SESSION['usuario_id'])): ?>
                    <li class="nav-item ms-lg-2">
                        <a class="nav-link btn-cyber px-3 py-2 rounded <?= activo('panel.php') ?>" href="panel.php">
                            <i class="bi bi-activity me-1"></i>Panel Live
                        </a>
                    </li>
                    <?php if ($_SESSION['rol'] === 'admin'): ?>
                        <li class="nav-item ms-lg-2">
                            <a class="nav-link btn-cyber px-3 py-2 rounded <?= activo('admin.php') ?>" href="admin.php" style="background:var(--color-warning);color:#000!important;border-color:var(--color-warning)">
                                <i class="bi bi-gear-fill me-1"></i>Ajustes
                            </a>
                        </li>
                    <?php endif; ?>
                    <li class="nav-item ms-lg-2">
                        <a class="nav-link px-3 py-2 text-danger" href="logout.php">
                            <i class="bi bi-box-arrow-right"></i> Salir (<?= htmlspecialchars($_SESSION['nombre']) ?>)
                        </a>
                    </li>
                <?php else: ?>
                    <li class="nav-item ms-lg-2">
                        <a class="nav-link btn-cyber px-3 py-2 rounded <?= activo('login.php') ?>" href="login.php">
                            <i class="bi bi-person-circle me-1"></i>Acceso Clientes
                        </a>
                    </li>
                <?php endif; ?>
            </ul>
        </div>
    </div>
</nav>
