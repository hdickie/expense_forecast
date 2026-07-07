<?php
require_once __DIR__ . '/config.php';
if (isset($_COOKIE['forecastidtoload'])) {
    unset($_COOKIE['forecastidtoload']); 
    setcookie('forecastidtoload', '', -1, '/'); 
} 

$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn, "select value from session where key = 'username' and login_token = '".$_COOKIE['login_token']."'");
$username = pg_fetch_row($query_obj)[0];

pg_query($dbconn, "TRUNCATE prod.ef_account_set_".$username."_temporary");
pg_query($dbconn, "TRUNCATE prod.ef_budget_item_set_".$username."_temporary");
pg_query($dbconn, "TRUNCATE prod.ef_memo_rule_set_".$username."_temporary");
pg_query($dbconn, "TRUNCATE prod.ef_account_milestones_".$username."_temporary");
pg_query($dbconn, "TRUNCATE prod.ef_memo_milestones_".$username."_temporary");
pg_query($dbconn, "TRUNCATE prod.ef_composite_milestones_".$username."_temporary");

header('Location: /expense_forecast.php');
?>