<?php
session_start();
require_once 'includes/logger.php';
log_activity('logout');
session_destroy();
header('Location: index.php');
exit;
