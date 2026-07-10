<?php
require_once __DIR__ . '/config.php';
setcookie('forecastidtoload',$_POST["forecastidtoload"], time() + (86400 / 3), "/");
setcookie('display_mode','SHOW_LOADED', time() + (86400 / 3), "/");

$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn, "select value from session where key = 'username' and login_token = '".$_COOKIE['login_token']."'");
$username = pg_fetch_row($query_obj)[0];


pg_query($dbconn, "TRUNCATE prod.ef_account_set_".$username."_temporary");
pg_query($dbconn, "INSERT INTO prod.ef_account_set_".$username."_temporary Select account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_interval, minimum_payment, primary_checking_ind from prod.ef_account_set_".$username." where forecast_id = '".$_POST["forecastidtoload"]."'");
 
pg_query($dbconn, "TRUNCATE prod.ef_budget_item_set_".$username."_temporary");
pg_query($dbconn, "INSERT INTO prod.ef_budget_item_set_".$username."_temporary Select memo, priority, start_date, end_date, interval, amount, \"deferrable\", partial_payment_allowed from prod.ef_budget_item_set_".$username." where forecast_id = '".$_POST["forecastidtoload"]."'");

pg_query($dbconn, "TRUNCATE prod.ef_memo_rule_set_".$username."_temporary");
pg_query($dbconn, "INSERT INTO prod.ef_memo_rule_set_".$username."_temporary Select memo_regex, account_from, account_to, priority from prod.ef_memo_rule_set_".$username." where forecast_id = '".$_POST["forecastidtoload"]."'");


pg_query($dbconn, "TRUNCATE prod.ef_account_milestones_".$username."_temporary");
pg_query($dbconn, "INSERT INTO prod.ef_account_milestones_".$username."_temporary Select milestone_name, account_name, min_balance, max_balance from prod.ef_account_milestones_".$username." where forecast_id = '".$_POST["forecastidtoload"]."'");

pg_query($dbconn, "TRUNCATE prod.ef_memo_milestones_".$username."_temporary");
pg_query($dbconn, "INSERT INTO prod.ef_memo_milestones_".$username."_temporary Select milestone_name, memo_regex from prod.ef_memo_milestones_".$username." where forecast_id = '".$_POST["forecastidtoload"]."'");

pg_query($dbconn, "TRUNCATE prod.ef_composite_milestones_".$username."_temporary");
pg_query($dbconn, "INSERT INTO prod.ef_composite_milestones_".$username."_temporary Select composite_milestone_name, account_milestone_name_list, memo_milestone_name_list from prod.ef_composite_milestones_".$username." where forecast_id = '".$_POST["forecastidtoload"]."'");



header('Location: /expense_forecast.php');

?>