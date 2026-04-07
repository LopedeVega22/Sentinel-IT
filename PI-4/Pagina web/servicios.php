<?php
$page_title = 'Servicios';
require 'includes/header.php';
require 'includes/navbar.php';

$servicios = [
    ['icono'=>'bi-shield-check',    'color'=>'primary', 'titulo'=>'Monitorización SSH',     'desc'=>'Detección en tiempo real de intentos de acceso remoto. Bloqueo automático de IPs que superen el umbral de fallos.'],
    ['icono'=>'bi-hdd-network',     'color'=>'success', 'titulo'=>'Protección FTP',          'desc'=>'Identificación de ataques de diccionario contra servidores FTP. Respuesta automática antes de que el atacante acceda.'],
    ['icono'=>'bi-globe2',          'color'=>'warning', 'titulo'=>'Análisis de tráfico web', 'desc'=>'Captura y análisis de peticiones HTTP. Detección de escaneos de directorios y exploits conocidos contra Apache.'],
    ['icono'=>'bi-cpu',             'color'=>'danger',  'titulo'=>'Agentes distribuidos',    'desc'=>'Red de sensores Raspberry Pi desplegados en diferentes puntos de la red. Cada agente opera de forma autónoma.'],
    ['icono'=>'bi-cloud-arrow-up',  'color'=>'primary', 'titulo'=>'Nube AWS IoT Core',       'desc'=>'Todos los eventos se transmiten cifrados a AWS IoT Core. Trazabilidad completa con historial en la nube.'],
    ['icono'=>'bi-bar-chart-line',  'color'=>'success', 'titulo'=>'Panel de control',        'desc'=>'Dashboard web con estadísticas en tiempo real. Gráficas de actividad, tasas de éxito y resumen de amenazas.'],
];

$color_map = [
    'primary' => ['bg'=>'rgba(0,212,255,0.1)',  'color'=>'#00D4FF'],
    'success' => ['bg'=>'rgba(0,196,140,0.1)',  'color'=>'#00C48C'],
    'warning' => ['bg'=>'rgba(255,184,0,0.1)',  'color'=>'#FFB800'],
    'danger'  => ['bg'=>'rgba(255,59,92,0.1)',  'color'=>'#FF3B5C'],
];
?>

<main class="container py-5">
    <div class="text-center mb-5">
        <span class="badge-cyber mb-3 d-inline-block">Lo que ofrecemos</span>
        <h1 class="section-title">Nuestros servicios</h1>
        <div class="title-line"></div>
        <p class="section-subtitle">Soluciones de ciberseguridad activa para proteger tu infraestructura en tiempo real.</p>
    </div>

    <div class="row g-4">
        <?php foreach ($servicios as $s):
            $c = $color_map[$s['color']]; ?>
        <div class="col-md-6 col-lg-4">
            <div class="card-cyber h-100">
                <div class="icon-wrap" style="background:<?= $c['bg'] ?>;color:<?= $c['color'] ?>">
                    <i class="bi <?= $s['icono'] ?>"></i>
                </div>
                <h5 class="fw-bold mb-2"><?= $s['titulo'] ?></h5>
                <p class="text-muted small mb-0"><?= $s['desc'] ?></p>
            </div>
        </div>
        <?php endforeach; ?>
    </div>

    <!-- CTA -->
    <div class="text-center mt-5 pt-3">
        <p class="text-muted mb-4">¿Quieres saber cómo desplegamos el sistema en tu entorno?</p>
        <a href="como-funciona.php" class="btn-primary-cyber me-3">Ver cómo funciona</a>
        <a href="contacto.php"      class="btn-outline-cyber">Contactar</a>
    </div>
</main>

<?php require 'includes/footer.php'; ?>
