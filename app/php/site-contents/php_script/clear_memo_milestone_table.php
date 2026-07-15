<?php
require_once __DIR__ . '/config.php';
$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn,"Select value from session where key = 'username' and login_token = '".$_COOKIE["login_token"]."'");
$query_result = pg_fetch_row($query_obj);
$username_according_to_server = $query_result[0];

$query_obj = pg_query($dbconn,"TRUNCATE prod.ef_memo_milestones_".$username_according_to_server."_temporary");

//$query_result = pg_fetch_all($query_obj);

header('Location: /expense_forecast.php');
?>