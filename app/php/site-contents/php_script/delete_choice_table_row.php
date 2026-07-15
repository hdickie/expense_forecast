<?php
require_once __DIR__ . '/config.php';
session_start();
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
ini_set('max_execution_time', '2147483647');


$dbconn = ef_pg_connect();

  $query_obj = pg_query($dbconn, "select value from session where key = 'username' and login_token = '".$_COOKIE['login_token']."'");
  $username = pg_fetch_row($query_obj)[0];

$del_q = "DELETE from prod.ef_choices_".$username."_temporary where option_name='".$_POST["option_name"]."' and choice_name='".$_POST["choice_name"]."' ";
echo $del_q.'<br>';
$query_obj = pg_query($dbconn, $del_q);
?>