<?php
// AJUSTA: pon tu email real aquí
define('EMAIL_DESTINO', 'tu@email.com');

$enviado = false;
$error   = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nombre  = htmlspecialchars(trim($_POST['nombre']  ?? ''));
    $email   = filter_var(trim($_POST['email']   ?? ''), FILTER_VALIDATE_EMAIL);
    $asunto  = htmlspecialchars(trim($_POST['asunto']  ?? 'Contacto web'));
    $mensaje = htmlspecialchars(trim($_POST['mensaje'] ?? ''));

    if ($nombre && $email && $mensaje) {
        $headers  = "From: noreply@SentinelIT.com\r\n";
        $headers .= "Reply-To: $email\r\n";
        $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

        $cuerpo = "Nombre: $nombre\nEmail: $email\n\n$mensaje";

        if (mail(EMAIL_DESTINO, "SentinelIT | $asunto", $cuerpo, $headers)) {
            $enviado = true;
        } else {
            $error = 'No se pudo enviar el mensaje. Inténtalo de nuevo o escríbenos directamente.';
        }
    } else {
        $error = 'Por favor rellena todos los campos correctamente.';
    }
}

$page_title = 'Contacto';
require 'includes/header.php';
require 'includes/navbar.php';
?>

<main class="container py-5">
    <div class="text-center mb-5">
        <span class="badge-cyber mb-3 d-inline-block">Estamos aquí</span>
        <h1 class="section-title">Contacto</h1>
        <div class="title-line"></div>
        <p class="section-subtitle">Cuéntanos tu caso y te explicamos cómo puede ayudarte el sistema.</p>
    </div>

    <div class="row justify-content-center">
        <div class="col-lg-6">

            <?php if ($enviado): ?>
                <div class="card-cyber text-center py-5">
                    <i class="bi bi-check-circle" style="font-size:3rem;color:var(--color-success)"></i>
                    <h4 class="fw-bold mt-3 mb-2">Mensaje enviado</h4>
                    <p class="text-muted mb-4">Gracias por contactarnos. Te respondemos en menos de 24h.</p>
                    <a href="index.php" class="btn-primary-cyber">Volver al inicio</a>
                </div>
            <?php else: ?>

                <?php if ($error): ?>
                    <div class="alert alert-danger rounded-3 mb-4"><?= $error ?></div>
                <?php endif; ?>

                <div class="card-cyber">
                    <form method="POST" novalidate>
                        <div class="mb-3">
                            <label class="form-label text-muted small">Nombre *</label>
                            <input type="text" name="nombre" class="form-control form-control-cyber"
                                   placeholder="Tu nombre completo"
                                   value="<?= htmlspecialchars($_POST['nombre'] ?? '') ?>" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted small">Email *</label>
                            <input type="email" name="email" class="form-control form-control-cyber"
                                   placeholder="tu@email.com"
                                   value="<?= htmlspecialchars($_POST['email'] ?? '') ?>" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted small">Asunto</label>
                            <input type="text" name="asunto" class="form-control form-control-cyber"
                                   placeholder="¿En qué podemos ayudarte?"
                                   value="<?= htmlspecialchars($_POST['asunto'] ?? '') ?>">
                        </div>
                        <div class="mb-4">
                            <label class="form-label text-muted small">Mensaje *</label>
                            <textarea name="mensaje" class="form-control form-control-cyber" rows="5"
                                      placeholder="Describe tu caso o consulta..." required><?= htmlspecialchars($_POST['mensaje'] ?? '') ?></textarea>
                        </div>
                        <button type="submit" class="btn-primary-cyber w-100">
                            <i class="bi bi-send me-2"></i>Enviar mensaje
                        </button>
                    </form>
                </div>

            <?php endif; ?>
        </div>

        <!-- Info lateral -->
        <div class="col-lg-4 offset-lg-1 mt-4 mt-lg-0">
            <div class="card-cyber mb-3">
                <i class="bi bi-envelope mb-2 d-block" style="color:var(--color-primary);font-size:1.4rem"></i>
                <h6 class="fw-bold">Email</h6>
                <p class="text-muted small mb-0">info@SentinelIT.com</p>
            </div>
            <div class="card-cyber mb-3">
                <i class="bi bi-clock mb-2 d-block" style="color:var(--color-primary);font-size:1.4rem"></i>
                <h6 class="fw-bold">Tiempo de respuesta</h6>
                <p class="text-muted small mb-0">Menos de 24 horas en días laborables.</p>
            </div>
            <div class="card-cyber">
                <i class="bi bi-activity mb-2 d-block" style="color:var(--color-success);font-size:1.4rem"></i>
                <h6 class="fw-bold">Sistema activo</h6>
                <p class="text-muted small mb-0">Monitorización 24/7 sin interrupciones.</p>
            </div>
        </div>
    </div>
</main>

<?php require 'includes/footer.php'; ?>

