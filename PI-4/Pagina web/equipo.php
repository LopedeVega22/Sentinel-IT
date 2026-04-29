<?php
$page_title = 'Equipo';
require 'includes/header.php';
require 'includes/navbar.php';

// AJUSTA: cambia los datos del equipo con los reales
$equipo = [
    ['nombre'=>'Nombre Apellido', 'rol'=>'Arquitecto de seguridad',  'desc'=>'Especialista en infraestructura IoT y AWS. Diseño del sistema de agentes distribuidos.', 'linkedin'=>'#'],
    ['nombre'=>'Nombre Apellido', 'rol'=>'Desarrollador Python',     'desc'=>'Desarrollo de los agentes de monitorización y lógica de detección en tiempo real.',      'linkedin'=>'#'],
    ['nombre'=>'Nombre Apellido', 'rol'=>'Administrador de sistemas','desc'=>'Gestión de la infraestructura AWS, certificados IoT y despliegue en producción.',         'linkedin'=>'#'],
];
?>

<main class="container py-5">
    <div class="text-center mb-5">
        <span class="badge-cyber mb-3 d-inline-block">Las personas detrás del sistema</span>
        <h1 class="section-title">El equipo</h1>
        <div class="title-line"></div>
    </div>

    <div class="row g-4 justify-content-center">
        <?php foreach ($equipo as $persona): ?>
        <div class="col-md-6 col-lg-4">
            <div class="card-cyber h-100 text-center">
                <!-- Foto: pon la imagen real en img/team/ -->
                <div class="mx-auto mb-3" style="width:80px;height:80px;border-radius:50%;background:rgba(0,212,255,0.1);border:2px solid rgba(0,212,255,0.2);display:flex;align-items:center;justify-content:center;">
                    <i class="bi bi-person" style="font-size:2rem;color:var(--color-primary)"></i>
                </div>
                <h5 class="fw-bold mb-1"><?= htmlspecialchars($persona['nombre']) ?></h5>
                <p class="mb-2" style="color:var(--color-primary);font-size:0.85rem"><?= htmlspecialchars($persona['rol']) ?></p>
                <p class="text-muted small mb-3"><?= htmlspecialchars($persona['desc']) ?></p>
                <a href="<?= $persona['linkedin'] ?>" class="btn-outline-cyber py-1 px-3" style="font-size:0.85rem">
                    <i class="bi bi-linkedin me-1"></i>LinkedIn
                </a>
            </div>
        </div>
        <?php endforeach; ?>
    </div>

    <!-- Sobre la empresa -->
    <div class="row justify-content-center mt-5">
        <div class="col-lg-7 text-center">
            <h2 class="fw-bold mb-3">Sobre CyberGuard</h2>
            <p class="text-muted">
                Nacimos con el objetivo de democratizar la ciberseguridad activa usando hardware
                accesible y tecnologías cloud modernas. Nuestro sistema basado en Raspberry Pi
                ofrece capacidades de detección y respuesta que antes solo estaban al alcance
                de grandes corporaciones.
            </p>
        </div>
    </div>
</main>

<?php require 'includes/footer.php'; ?>
