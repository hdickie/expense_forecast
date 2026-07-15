<?php
require_once __DIR__ . '/config.php';
session_start();
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
ini_set('max_execution_time', '2147483647');


$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn,"Select value from session where key = 'username' and login_token = '".$_COOKIE["login_token"]."'");
$query_result = pg_fetch_row($query_obj);
$username_according_to_server = $query_result[0];

//print_r($_POST);

$choice_name = '';
$insert_statements = array();
$current_option_name = '';
foreach($_POST as $key => $value)
{
	if ( $key == 'choice-name' ){
		$choice_name = $value;
	} else if ( str_starts_with($key, 'option-name-') ) {
		$current_option_name = $value;
	} else if ( str_starts_with($key, 'memo-regexes-') ) {

		$new_insert_query = 'INSERT INTO prod.ef_choices_'.$username_according_to_server.'_temporary ( choice_name, option_name, memo_regexes ) SELECT \''.$choice_name.'\',\''.$current_option_name.'\',\''.$value.'\'';
		array_push($insert_statements, $new_insert_query);
		$current_option_name = '';
	}
}

foreach($insert_statements as $q) {
	$query_obj = pg_query($dbconn, $q);
}
// $insert_statement = ""
// 

header('Location: /expense_forecast.php');
?>