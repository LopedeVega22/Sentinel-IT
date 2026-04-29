<?php // includes/header.php 
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$ajustes_globales = [];
if (isset($pdo)) {
    try {
        $stmt_aj = $pdo->query("SELECT clave, valor FROM ajustes");
        while ($row = $stmt_aj->fetch(PDO::FETCH_ASSOC)) {
            $ajustes_globales[$row['clave']] = $row['valor'];
        }
    } catch (PDOException $e) { /* Ignorar error en header si no hay bd */ }
}
$site_title_global = $ajustes_globales['site_title'] ?? 'SentinelIT';
$contact_email_global = $ajustes_globales['contact_email'] ?? 'info@SentinelIT.com';
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="<?= htmlspecialchars($site_title_global) ?> — Soluciones de ciberseguridad basadas en Raspberry Pi y AWS IoT">
    <title><?= htmlspecialchars($page_title ?? $site_title_global) ?> | <?= htmlspecialchars($site_title_global) ?></title>

    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <!-- Estilos propios -->
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link href="css/main.css" rel="stylesheet">
</head>
<body>

