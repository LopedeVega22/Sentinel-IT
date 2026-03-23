<?php
$page_title = 'Tecnologías';
require 'includes/header.php';
require 'includes/navbar.php';

$tecnologias = [
    ['nombre'=>'Raspberry Pi 4/5', 'icono'=>'bi-cpu',           'color'=>'primary', 'desc'=>'Hardware de bajo coste que actúa como sensor y coordinador. ARM64, 4-8GB RAM, consumo mínimo.'],
    ['nombre'=>'Python 3.11',      'icono'=>'bi-code-slash',     'color'=>'success', 'desc'=>'Lenguaje principal de los agentes. Manejo de threads, regex, sockets y comunicación MQTT.'],
    ['nombre'=>'AWS IoT Core',     'icono'=>'bi-cloud',          'color'=>'warning', 'desc'=>'Broker MQTT gestionado de Amazon. Autenticación mTLS, políticas por dispositivo, alta disponibilidad.'],
    ['nombre'=>'MQTT',             'icono'=>'bi-arrow-left-right','color'=>'danger', 'desc'=>'Protocolo de mensajería ligero. Diseñado para IoT. QoS 1 garantiza entrega de eventos críticos.'],
    ['nombre'=>'PHP 8',            'icono'=>'bi-filetype-php',   'color'=>'primary', 'desc'=>'Backend del panel web. Consultas a MySQL y generación dinámica de páginas.'],
    ['nombre'=>'MySQL',            'icono'=>'bi-database',       'color'=>'success', 'desc'=>'Almacenamiento de eventos y estadísticas. Consultas de agregación para el dashboard.'],
    ['nombre'=>'Bootstrap 5',      'icono'=>'bi-bootstrap',      'color'=>'warning', 'desc'=>'Framework CSS para la interfaz. Diseño responsivo y componentes listos para usar.'],
    ['nombre'=>'Chart.js',         'icono'=>'bi-bar-chart',      'color'=>'danger',  'desc'=>'Librería de gráficas JavaScript. Cuatro tipos de gráficas en el panel con datos reales.'],
    ['nombre'=>'iptables',         'icono'=>'bi-shield-lock',    'color'=>'primary', 'desc'=>'Firewall de Linux. Los agentes ejecutan reglas de bloqueo automático de IPs atacantes.'],
    ['nombre'=>'systemd',          'icono'=>'bi-gear',           'color'=>'success', 'desc'=>'Gestión del servicio del agente como daemon del sistema. Arranque automático y reinicio ante fallos.'],
    ['nombre'=>'Docker',           'icono'=>'bi-box',            'color'=>'warning', 'desc'=>'Contenedorización opcional del agente para despliegue reproducible en cualquier plataforma.'],
    ['nombre'=>'Git / GitHub',     'icono'=>'bi-git',            'color'=>'danger',  'desc'=>'Control de versiones del código. Flujo de desarrollo con ramas y revisión de cambios.'],
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
        <span class="badge-cyber mb-3 d-inline-block">Stack tecnológico</span>
        <h1 class="section-title">Tecnologías</h1>
        <div class="title-line"></div>
        <p class="section-subtitle">Herramientas open source y servicios cloud que componen el sistema.</p>
    </div>

    <div class="row g-4">
        <?php foreach ($tecnologias as $t):
            $c = $color_map[$t['color']]; ?>
        <div class="col-sm-6 col-lg-4">
            <div class="card-cyber d-flex gap-3 align-items-start">
                <div class="icon-wrap flex-shrink-0" style="background:<?= $c['bg'] ?>;color:<?= $c['color'] ?>">
                    <i class="bi <?= $t['icono'] ?>"></i>
                </div>
                <div>
                    <h6 class="fw-bold mb-1"><?= $t['nombre'] ?></h6>
                    <p class="text-muted small mb-0"><?= $t['desc'] ?></p>
                </div>
            </div>
        </div>
        <?php endforeach; ?>
    </div>
</main>

<?php require 'includes/footer.php'; ?>
