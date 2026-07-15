<?php
require_once __DIR__ . '/config.php';
$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn,"Select value from session where key = 'username' and login_token = '".$_COOKIE["login_token"]."'");
$query_result = pg_fetch_row($query_obj);
$username_according_to_server = $query_result[0];

$submit_ts = date('m/d/Y H:i:s', time());
$report_text = $_POST['bug-report-text'];

$insert_statement = "INSERT INTO bug_reports (username, submit_ts, report_text) Select '".$username_according_to_server."','".$submit_ts."','".$report_text."'";	
//echo $insert_statement;		
$query_obj = pg_query($dbconn, $insert_statement);


header('Location: /expense_forecast.php');
?>