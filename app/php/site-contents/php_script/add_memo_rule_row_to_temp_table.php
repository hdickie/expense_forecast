<?php
require_once __DIR__ . '/config.php';
$POSTGRES_NULL_DATE = '(CAST(null AS date))';

$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn,"Select value from session where key = 'username' and login_token = '".$_COOKIE["login_token"]."'");
$query_result = pg_fetch_row($query_obj);
$username_according_to_server = $query_result[0];

//var_dump($_POST);
//echo '<br><br><br><br>';


$insert_statement = "INSERT INTO prod.ef_memo_rule_set_".$username_according_to_server."_temporary (memo_regex,account_from,account_to,priority) Select '".$_POST["memoregex"]."','".$_POST["accountfrom"]."','".$_POST["accountto"]."',".$_POST["memorulepriority"];
//echo '<br>'.$insert_statement.'<br>';		
$query_obj = pg_query($dbconn, $insert_statement);


//$query_result = pg_fetch_all($query_obj);

header('Location: /expense_forecast.php');
?>