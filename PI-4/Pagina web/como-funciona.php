<?php
$page_title = 'Cómo funciona';
require 'includes/header.php';
require 'includes/navbar.php';
?>

<main class="container py-5">
    <div class="text-center mb-5">
        <span class="badge-cyber mb-3 d-inline-block">Arquitectura del sistema</span>
        <h1 class="section-title">Cómo funciona</h1>
        <div class="title-line"></div>
        <p class="section-subtitle">Un sistema distribuido de detección de amenazas basado en hardware accesible y cloud profesional.</p>
    </div>

    <!-- Componentes -->
    <div class="row g-4 mb-5">
        <div class="col-md-6 col-lg-3">
            <div class="card-cyber h-100 text-center">
                <div class="icon-wrap mx-auto"><i class="bi bi-cpu"></i></div>
                <h6 class="fw-bold">Sensor (Pi4)</h6>
                <p class="text-muted small">Raspberry Pi 4 instalada en la red del cliente. Monitoriza logs SSH, FTP y Apache en tiempo real.</p>
                <span class="badge-cyber">agente_monitor.py</span>
            </div>
        </div>
        <div class="col-md-6 col-lg-3">
            <div class="card-cyber h-100 text-center">
                <div class="icon-wrap mx-auto" style="background:rgba(0,196,140,0.1);color:#00C48C"><i class="bi bi-cloud-arrow-up"></i></div>
                <h6 class="fw-bold">AWS IoT Core</h6>
                <p class="text-muted small">Broker MQTT en la nube. Recibe los eventos de todos los sensores con cifrado mTLS extremo a extremo.</p>
                <span class="badge-cyber">MQTT / TLS 1.2</span>
            </div>
        </div>
        <div class="col-md-6 col-lg-3">
            <div class="card-cyber h-100 text-center">
                <div class="icon-wrap mx-auto" style="background:rgba(255,184,0,0.1);color:#FFB800"><i class="bi bi-diagram-3"></i></div>
                <h6 class="fw-bold">Coordinador (Pi5)</h6>
                <p class="text-muted small">Raspberry Pi 5 que recibe los eventos, los analiza con IA y ordena bloqueos automáticos al sensor.</p>
                <span class="badge-cyber">coordinador.py</span>
            </div>
        </div>
        <div class="col-md-6 col-lg-3">
            <div class="card-cyber h-100 text-center">
                <div class="icon-wrap mx-auto" style="background:rgba(255,59,92,0.1);color:#FF3B5C"><i class="bi bi-bar-chart"></i></div>
                <h6 class="fw-bold">Panel web</h6>
                <p class="text-muted small">Dashboard accesible desde el navegador con estadísticas, gráficas y estado del sistema en tiempo real.</p>
                <span class="badge-cyber">PHP + Chart.js</span>
            </div>
        </div>
    </div>

    <!-- Timeline del flujo de un ataque -->
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <h2 class="fw-bold mb-4 text-center">Flujo de un ataque detectado</h2>
            <div class="timeline-step">
                <div class="timeline-num">1</div>
                <div>
                    <h6 class="fw-bold mb-1">Intento de acceso</h6>
                    <p class="text-muted small mb-0">Un atacante intenta conectarse por SSH con usuario y contraseña incorrectos. El sistema operativo escribe la línea en el log.</p>
                </div>
            </div>
            <div class="timeline-step">
                <div class="timeline-num">2</div>
                <div>
                    <h6 class="fw-bold mb-1">Captura en tiempo real</h6>
                    <p class="text-muted small mb-0">El agente en la Pi4 detecta la línea mediante <code style="color:var(--color-primary)">journalctl -f</code> y extrae la IP con expresiones regulares.</p>
                </div>
            </div>
            <div class="timeline-step">
                <div class="timeline-num">3</div>
                <div>
                    <h6 class="fw-bold mb-1">Envío a la nube</h6>
                    <p class="text-muted small mb-0">El evento se serializa a JSON y se publica en AWS IoT Core mediante MQTT con cifrado TLS en menos de un segundo.</p>
                </div>
            </div>
            <div class="timeline-step">
                <div class="timeline-num">4</div>
                <div>
                    <h6 class="fw-bold mb-1">Análisis por el coordinador</h6>
                    <p class="text-muted small mb-0">La Pi5 recibe el evento, comprueba el historial de esa IP y decide si debe bloquearse según las reglas configuradas.</p>
                </div>
            </div>
            <div class="timeline-step">
                <div class="timeline-num">5</div>
                <div>
                    <h6 class="fw-bold mb-1">Bloqueo automático</h6>
                    <p class="text-muted small mb-0">El coordinador publica una orden de bloqueo. El agente la recibe y ejecuta <code style="color:var(--color-primary)">iptables -A INPUT -s IP -j DROP</code> en el sistema.</p>
                </div>
            </div>
        </div>
    </div>
</main>

<?php require 'includes/footer.php'; ?>
