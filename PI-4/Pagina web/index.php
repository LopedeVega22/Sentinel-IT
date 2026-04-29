<?php
$page_title = 'Inicio';
require 'includes/header.php';
require 'includes/navbar.php';
?>

<!-- HERO -->
<section class="hero px-3">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-lg-7">
                <span class="badge-cyber mb-4 d-inline-block">Sistema activo 24/7</span>
                <h1 class="hero-title mb-4">
                    Ciberseguridad<br>
                    <span>inteligente</span><br>
                    en tiempo real
                </h1>
                <p class="hero-subtitle mb-5">
                    Detectamos y bloqueamos amenazas automáticamente usando Raspberry Pi,
                    agentes distribuidos y AWS IoT Core. Sin intervención humana.
                </p>
                <div class="d-flex flex-wrap gap-3">
                    <a href="/servicios.php"     class="btn-primary-cyber">Ver servicios</a>
                    <a href="/como-funciona.php" class="btn-outline-cyber">Cómo funciona</a>
                </div>
            </div>
            <div class="col-lg-5 d-none d-lg-flex justify-content-center mt-5 mt-lg-0">
                <!-- Diagrama decorativo SVG -->
                <svg viewBox="0 0 320 320" width="320" height="320" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="160" cy="160" r="140" fill="none" stroke="rgba(0,212,255,0.08)" stroke-width="1"/>
                    <circle cx="160" cy="160" r="100" fill="none" stroke="rgba(0,212,255,0.12)" stroke-width="1"/>
                    <circle cx="160" cy="160" r="60"  fill="none" stroke="rgba(0,212,255,0.18)" stroke-width="1"/>
                    <circle cx="160" cy="160" r="28"  fill="rgba(0,212,255,0.1)" stroke="#00D4FF" stroke-width="1.5"/>
                    <text x="160" y="165" text-anchor="middle" fill="#00D4FF" font-size="14" font-family="JetBrains Mono">SOC</text>
                    <!-- Nodos -->
                    <circle cx="160" cy="30"  r="14" fill="#111827" stroke="#00C48C" stroke-width="1.5"/>
                    <circle cx="290" cy="160" r="14" fill="#111827" stroke="#00C48C" stroke-width="1.5"/>
                    <circle cx="160" cy="290" r="14" fill="#111827" stroke="#FFB800" stroke-width="1.5"/>
                    <circle cx="30"  cy="160" r="14" fill="#111827" stroke="#FF3B5C" stroke-width="1.5"/>
                    <line x1="160" y1="44"  x2="160" y2="132" stroke="rgba(0,212,255,0.3)" stroke-width="1" stroke-dasharray="4"/>
                    <line x1="276" y1="160" x2="188" y2="160" stroke="rgba(0,212,255,0.3)" stroke-width="1" stroke-dasharray="4"/>
                    <line x1="160" y1="276" x2="160" y2="188" stroke="rgba(0,212,255,0.3)" stroke-width="1" stroke-dasharray="4"/>
                    <line x1="44"  y1="160" x2="132" y2="160" stroke="rgba(0,212,255,0.3)" stroke-width="1" stroke-dasharray="4"/>
                    <text x="160" y="24"  text-anchor="middle" fill="#8892A4" font-size="9" font-family="JetBrains Mono">Pi4</text>
                    <text x="294" y="154" text-anchor="start"  fill="#8892A4" font-size="9" font-family="JetBrains Mono">AWS</text>
                    <text x="160" y="316" text-anchor="middle" fill="#8892A4" font-size="9" font-family="JetBrains Mono">Pi5</text>
                    <text x="8"   y="154" text-anchor="start"  fill="#8892A4" font-size="9" font-family="JetBrains Mono">Web</text>
                </svg>
            </div>
        </div>
    </div>
</section>

<!-- PROPUESTA DE VALOR -->
<section class="py-6 section-dark py-5">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="section-title">Por qué elegirnos</h2>
            <div class="title-line"></div>
        </div>
        <div class="row g-4">
            <div class="col-md-6 col-lg-3">
                <div class="card-cyber h-100">
                    <div class="icon-wrap"><i class="bi bi-activity"></i></div>
                    <h5 class="fw-bold mb-2">Tiempo real</h5>
                    <p class="text-muted small mb-0">Detección y respuesta en menos de 30 segundos ante cualquier amenaza.</p>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="card-cyber h-100">
                    <div class="icon-wrap" style="background:rgba(0,196,140,0.1);color:var(--color-success)"><i class="bi bi-robot"></i></div>
                    <h5 class="fw-bold mb-2">Automatizado</h5>
                    <p class="text-muted small mb-0">Los agentes bloquean IPs y servicios sin intervención humana.</p>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="card-cyber h-100">
                    <div class="icon-wrap" style="background:rgba(255,184,0,0.1);color:var(--color-warning)"><i class="bi bi-cloud-check"></i></div>
                    <h5 class="fw-bold mb-2">Cloud nativo</h5>
                    <p class="text-muted small mb-0">Infraestructura sobre AWS IoT Core con cifrado mTLS extremo a extremo.</p>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="card-cyber h-100">
                    <div class="icon-wrap" style="background:rgba(255,59,92,0.1);color:var(--color-danger)"><i class="bi bi-graph-up-arrow"></i></div>
                    <h5 class="fw-bold mb-2">Escalable</h5>
                    <p class="text-muted small mb-0">Añade sensores (Raspberry Pi) a la red sin tocar la infraestructura central.</p>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ESTADÍSTICAS -->
<section class="py-5">
    <div class="container">
        <div class="row g-4 text-center">
            <div class="col-6 col-md-3">
                <div class="stat-counter" data-target="12847">0</div>
                <div class="stat-label">Ataques detectados</div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-counter" data-target="11203">0</div>
                <div class="stat-label">Ataques bloqueados</div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-counter" data-target="98">0</div>
                <div class="stat-label">% tasa de éxito</div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-counter" data-target="24">0</div>
                <div class="stat-label">Horas monitorizando</div>
            </div>
        </div>
    </div>
</section>

<!-- CTA FINAL -->
<section class="py-5 section-dark">
    <div class="container text-center py-3">
        <h2 class="section-title mb-3">¿Listo para proteger tu infraestructura?</h2>
        <p class="text-muted mb-4">Contacta con nosotros y te explicamos cómo desplegar el sistema en tu entorno.</p>
        <a href="/contacto.php" class="btn-primary-cyber">Hablar con el equipo</a>
    </div>
</section>

<?php require 'includes/footer.php'; ?>
