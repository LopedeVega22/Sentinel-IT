<?php
$page_title = 'Panel de Control';
require 'includes/header.php';
require 'includes/navbar.php';
require 'db.php';

// ── Totales globales ─────────────────────────────────────────────────────────
$detectados = (int) $pdo->query('SELECT COUNT(*) FROM eventos WHERE tipo = "detectado"')->fetchColumn();
$bloqueados  = (int) $pdo->query('SELECT COUNT(*) FROM eventos WHERE tipo = "bloqueado"')->fetchColumn();
$exitoPct    = $detectados > 0 ? round(($bloqueados / $detectados) * 100) : 0;

// Total de eventos hoy
$hoy = (int) $pdo->query('SELECT COUNT(*) FROM eventos WHERE DATE(created_at) = CURDATE()')->fetchColumn();

// ── Actividad últimos 7 días (gráfica de línea) ──────────────────────────────
$rowsActividad = $pdo->query('
    SELECT DATE(created_at) AS dia, COUNT(*) AS total
    FROM eventos
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY dia
    ORDER BY dia
')->fetchAll(PDO::FETCH_ASSOC);

$diasData    = json_encode(array_column($rowsActividad, 'dia'));
$totalesData = json_encode(array_column($rowsActividad, 'total'));

// ── Ataques por servicio (gráfica de barras) ─────────────────────────────────
$rowsServicios = $pdo->query('
    SELECT servicio, COUNT(*) AS total
    FROM eventos
    GROUP BY servicio
    ORDER BY total DESC
')->fetchAll(PDO::FETCH_ASSOC);

$serviciosLabels = json_encode(array_column($rowsServicios, 'servicio'));
$serviciosData   = json_encode(array_column($rowsServicios, 'total'));

// ── Últimos 10 eventos (tabla) ───────────────────────────────────────────────
$ultimosEventos = $pdo->query('
    SELECT tipo, servicio, ip_origen, created_at
    FROM eventos
    ORDER BY created_at DESC
    LIMIT 10
')->fetchAll(PDO::FETCH_ASSOC);
?>

<main class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-5">
        <div>
            <span class="badge-cyber mb-2 d-inline-block">Sistema activo</span>
            <h1 class="section-title mb-0">Panel de Control</h1>
        </div>
        <span class="text-muted small">
            <i class="bi bi-arrow-clockwise me-1"></i>
            Actualizado: <?= date('d/m/Y H:i:s') ?>
        </span>
    </div>

    <!-- KPIs -->
    <div class="row g-4 mb-5">
        <div class="col-6 col-lg-3">
            <div class="kpi-card">
                <div class="kpi-value" style="color:var(--color-danger)"><?= number_format($detectados) ?></div>
                <div class="kpi-label">Detectados</div>
            </div>
        </div>
        <div class="col-6 col-lg-3">
            <div class="kpi-card">
                <div class="kpi-value" style="color:var(--color-success)"><?= number_format($bloqueados) ?></div>
                <div class="kpi-label">Bloqueados</div>
            </div>
        </div>
        <div class="col-6 col-lg-3">
            <div class="kpi-card">
                <div class="kpi-value" style="color:var(--color-primary)"><?= $exitoPct ?>%</div>
                <div class="kpi-label">Tasa de éxito</div>
            </div>
        </div>
        <div class="col-6 col-lg-3">
            <div class="kpi-card">
                <div class="kpi-value" style="color:var(--color-warning)"><?= number_format($hoy) ?></div>
                <div class="kpi-label">Eventos hoy</div>
            </div>
        </div>
    </div>

    <!-- Gráficas fila 1 -->
    <div class="row g-4 mb-4">
        <div class="col-lg-8">
            <div class="chart-container" style="height:280px">
                <canvas id="chart-actividad"></canvas>
            </div>
        </div>
        <div class="col-lg-4">
            <div class="chart-container" style="height:280px">
                <canvas id="chart-donut"></canvas>
            </div>
        </div>
    </div>

    <!-- Gráficas fila 2 -->
    <div class="row g-4 mb-5">
        <div class="col-lg-6">
            <div class="chart-container" style="height:240px">
                <canvas id="chart-servicios"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container" style="height:240px">
                <canvas id="chart-exito"></canvas>
            </div>
        </div>
    </div>

    <!-- Tabla de últimos eventos -->
    <div class="chart-container">
        <h6 class="fw-bold mb-3">Últimos eventos registrados</h6>
        <div class="table-responsive">
            <table class="table table-dark table-hover mb-0" style="font-size:0.85rem">
                <thead>
                    <tr style="color:var(--color-muted)">
                        <th>Tipo</th><th>Servicio</th><th>IP origen</th><th>Fecha</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($ultimosEventos as $ev): ?>
                    <tr>
                        <td>
                            <?php if ($ev['tipo'] === 'bloqueado'): ?>
                                <span class="badge" style="background:rgba(0,196,140,0.2);color:#00C48C">bloqueado</span>
                            <?php else: ?>
                                <span class="badge" style="background:rgba(255,59,92,0.2);color:#FF3B5C">detectado</span>
                            <?php endif; ?>
                        </td>
                        <td><code style="color:var(--color-primary)"><?= htmlspecialchars($ev['servicio']) ?></code></td>
                        <td style="font-family:var(--font-mono)"><?= htmlspecialchars($ev['ip_origen'] ?? '—') ?></td>
                        <td style="color:var(--color-muted)"><?= $ev['created_at'] ?></td>
                    </tr>
                    <?php endforeach; ?>
                    <?php if (empty($ultimosEventos)): ?>
                    <tr><td colspan="4" class="text-center text-muted py-4">Sin eventos registrados todavía</td></tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</main>

<!-- Variables PHP → JavaScript para Chart.js -->
<script>
    const diasData        = <?= $diasData ?>;
    const totalesData     = <?= $totalesData ?>;
    const detectadosTotal = <?= $detectados ?>;
    const bloqueadosTotal = <?= $bloqueados ?>;
    const serviciosLabels = <?= $serviciosLabels ?>;
    const serviciosData   = <?= $serviciosData ?>;
    const exitoPorcentaje = <?= $exitoPct ?>;
</script>

<?php require 'includes/footer.php'; ?>
