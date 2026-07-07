<?php
require_once __DIR__ . '/config.php';
$dbconn = ef_pg_connect();


  $query_obj = pg_query($dbconn, "select value from session where key = 'username' and login_token = '".$_COOKIE['login_token']."'");
  $username = pg_fetch_row($query_obj)[0];

$q = "INSERT INTO prod.ef_account_milestones_".$username."_temporary Select '".$_POST["accountmilestonename"]."','".$_POST["accountmilestoneaccountname"]."',".$_POST["accountmilestoneminbalance"].",".$_POST["accountmilestonemaxbalance"];

$query_obj = pg_query($dbconn, $q);
header('Location: /expense_forecast.php');
?>