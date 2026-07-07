<?php
require_once __DIR__ . '/config.php';
if (isset($_COOKIE['login_token'])) {
    unset($_COOKIE['login_token']); 
    setcookie('login_token', '', -1, '/'); 
} 
header('Location: /index.php');
?>