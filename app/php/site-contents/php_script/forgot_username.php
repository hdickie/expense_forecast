<?php
require_once __DIR__ . '/config.php';
$dbconn = ef_pg_connect();
$username_query = "Select username from users where email = '".$_POST["email"]."'";
$username_query_obj = pg_query($dbconn,$username_query);
$username_query_result = pg_fetch_row($username_query_obj);
setcookie('forgotten_username', $username_query_result[0], time() + (86400), '/'); 
header('Location: /forgot_password.php');
?>