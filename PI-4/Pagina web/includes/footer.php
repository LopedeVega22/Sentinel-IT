<!-- includes/footer.php -->
<footer class="mt-5 py-5" style="background:#080d1f; border-top:1px solid rgba(0,212,255,0.1)">
    <div class="container">
        <div class="row gy-4">
            <div class="col-md-4">
                <h5 class="fw-bold mb-3">
                    <i class="bi bi-shield-fill-check me-2" style="color:var(--color-primary)"></i>CyberGuard
                </h5>
                <p class="text-muted small">Protección inteligente basada en Raspberry Pi y AWS IoT Core. Detección en tiempo real, respuesta automatizada.</p>
            </div>
            <div class="col-md-4">
                <h6 class="fw-bold mb-3 text-light">Navegación</h6>
                <ul class="list-unstyled small">
                    <li><a href="/servicios.php"     class="text-muted text-decoration-none footer-link">Servicios</a></li>
                    <li><a href="/como-funciona.php" class="text-muted text-decoration-none footer-link">Cómo funciona</a></li>
                    <li><a href="/tecnologias.php"   class="text-muted text-decoration-none footer-link">Tecnologías</a></li>
                    <li><a href="/equipo.php"         class="text-muted text-decoration-none footer-link">Equipo</a></li>
                    <li><a href="/contacto.php"       class="text-muted text-decoration-none footer-link">Contacto</a></li>
                </ul>
            </div>
            <div class="col-md-4">
                <h6 class="fw-bold mb-3 text-light">Contacto</h6>
                <p class="text-muted small mb-1"><i class="bi bi-envelope me-2"></i>info@cyberguard.com</p>
                <p class="text-muted small mb-1"><i class="bi bi-telephone me-2"></i>+34 900 000 000</p>
                <p class="text-muted small"><i class="bi bi-geo-alt me-2"></i>España</p>
            </div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.08)">
        <p class="text-center text-muted small mb-0">© <?= date('Y') ?> CyberGuard — Todos los derechos reservados</p>
    </div>
</footer>

<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<!-- JS propio -->
<script src="/js/main.js"></script>

<?php if (basename($_SERVER['PHP_SELF']) === 'panel.php'): ?>
    <!-- Chart.js solo en el panel -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="/js/charts.js"></script>
<?php endif; ?>

</body>
</html>
