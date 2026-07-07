<?php
require_once __DIR__ . '/config.php';
session_start();
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
ini_set('max_execution_time', '2147483647');


setcookie('display_mode','SHOW_RUN', time() + (86400 / 3), "/");

if ( isset($_POST["overwriteforecast"]) ){
	$force_flag = ' --overwrite ';
} else {
	$force_flag = '';
}


if ( isset($_POST["approximateforecast"]) ){
	$approximate_flag = ' --approximate ';
} else {
	$approximate_flag = '';
}

//todo add anchor for start of string. Usually ^ but i want to look it up instead of test to check bc reasons
if ( preg_match("/S/", $_POST["forecastlabel"] )) {
	$action = ' run forecastset ';
} else {
	$action = ' run forecast ';
}


$log_directory = '/var/www/html/log/';

//get staged forecast ids
$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn,"Select value from session where key = 'username' and login_token = '".$_COOKIE["login_token"]."'");
$query_result = pg_fetch_row($query_obj);
$username_according_to_server = $query_result[0];


//$_POST["forecastidtorun"]

$command = '(python3 /var/www/html/src/expense_forecast/ef_cli.py '.$action.' --source database --id '.$_POST["forecastlabel"].' --working_directory /var/www/html/data/ --username '.$username_according_to_server.$force_flag.ef_cli_database_args().$approximate_flag.' --log_directory '.$log_directory.') 2>&1 &';
exec($command, $output, $return_code); 


 //ob_start(); 


// > '.$_COOKIE["username"].'_Forecast.log'
// echo '<br>';
// echo $command;
// echo '<br>';
// echo '<br>';
// echo '<br>';

$formatted_output = '';
$forecast_id  = $_POST["forecastlabel"];
if ( $action == ' run forecast ' ){
	foreach ($output as &$line) {
	    //e.g. 2024-04-22 11:41:21,529
	    // if ( preg_match("/[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}/", $line ) ) {
	    // 	$formatted_output = $formatted_output.'<br>'.$line;
	    // } else {
	    // 	$forecast_id = $line; //this is problematic
	 	// }
	 	 // if ( preg_match("/[0-9]{6}_[0-9]+_[0-9]+_[0-9]{4}/", $line ) ) { //this is problematic and doesn't really work
	 	 // 	$forecast_id = $line; 
	 	 // } else {
	 	 // 	$formatted_output = $formatted_output.'<br>'.$line;
	 	 // }
		$formatted_output = $formatted_output.'<br>'.$line;
	}
} elseif ( $action == ' run forecastset ' ){
	foreach ($output as &$line) {
		if ( preg_match("/S[0-9]{6}/", $line ) ) { //this is problematic, but mostly works
	 	 	$forecast_id = $line; 
	 	 } else {
	 	 	$formatted_output = $formatted_output.'<br>'.$line;
	 	 }
 	}
}

//echo $formatted_output;
if ( $return_code == 0 ){
	
	// echo $forecast_id;
	// setcookie('latest_server_feedback',"", time() + (86400 / 3), "/");
	setcookie('forecastidtoload',$forecast_id, time() + (86400 / 3), "/");
	
}
$_SESSION['latest_server_feedback'] = $formatted_output;
//echo $formatted_output;
#setcookie('latest_server_feedback',$formatted_output, time() + (86400 / 3), "/");

//echo $_SESSION['latest_server_feedback'];
// echo '<br><br><br>@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@<br><br><br>';
// print_r($_COOKIE);
// echo '<br><br><br>@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@<br><br><br>';
// $headers = apache_request_headers();
// ob_end_clean();
// foreach ($headers as $header => $value) {
//     echo "$header: $value <br />\n";
// }

// echo $command;
// echo '<br>';
// echo $formatted_output;
header('Location: /expense_forecast.php');
?>
