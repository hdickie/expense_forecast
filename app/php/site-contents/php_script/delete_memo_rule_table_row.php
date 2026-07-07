<?php
require_once __DIR__ . '/config.php';
$dbconn = ef_pg_connect();

  $query_obj = pg_query($dbconn, "select value from session where key = 'username' and login_token = '".$_COOKIE['login_token']."'");
  $username = pg_fetch_row($query_obj)[0];
$query_obj = pg_query($dbconn, "DELETE from prod.ef_memo_rule_set_".$username."_temporary where memo_regex='".$_POST["memo_regex"]."'");
?>