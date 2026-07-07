<?php
require_once __DIR__ . '/config.php';
session_start();
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
ini_set('max_execution_time', '2147483647');


//forecast_set_id	forecast_id	forecast_set_name	forecast_name	start_date	end_date
$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn, "select value from session where key = 'username' and login_token = '".$_COOKIE['login_token']."'");
$username = pg_fetch_row($query_obj)[0];

$log_directory = '/var/www/html/log/';

// $listed_forecast_set_id='';
// $forecast_set_ids=array();
$latest_server_feedback='';
if ( isset($_POST['stagescenarios']) ) {
  $action = ' parameterize forecastset ';
  $command = '(python3 /var/www/html/src/expense_forecast/ef_cli.py '.$action.' --source database --id None  --working_directory /var/www/html/data/ --start_date '.$_POST["simulationstartdate"].' --end_date '.$_POST["simulationenddate"].' --username '.$_COOKIE["username"].ef_cli_database_args().' --log_directory '.$log_directory.'  --label "'.$_POST["forecastlabel"].'") 2>&1'; 
  exec($command, $output, $return_code);

  // $scenario_strings = array();
  // $scenario_index = 0;
  foreach ($output as &$line) {
    $latest_server_feedback=$latest_server_feedback.$line.'<br>';

    // //scenario strings come before id tuples
    // if ( str_starts_with($line,'Core | ') ){
    //   array_push($scenario_strings, $line);
    // }


    // if ( str_starts_with($line,'(forecast_set_id, forecast_id)=') ){
    //   $listed_forecast_set_id_and_id = explode('=',$line)[1];
    //   $forecast_set_id = explode(',',$listed_forecast_set_id_and_id)[0];
    //   $forecast_id = explode(',',$listed_forecast_set_id_and_id)[1];

    //   $forecast_set_name = $_POST["forecastlabel"];
    //   $forecast_name = $scenario_strings[$scenario_index];
    //   $scenario_index = $scenario_index + 1;

    //   $q = "INSERT INTO prod.".$username."_staged_forecast_details Select '".$forecast_set_id."','".$forecast_id."','".$forecast_set_name."','".$forecast_name."','".$_POST["simulationstartdate"]."','".$_POST["simulationenddate"]."'";

    //   $query_obj = pg_query($dbconn, $q);

    //   // //apparently array[] notation is more appropriate when inserting just one element but that is a micro-optimization for my use case at this point so I am purposely not worrying about it
    //   // array_push($forecast_set_ids,$forecast_id); 
    // }
  }
} else {
  $action = ' parameterize forecast ';
  $command = '(python3 /var/www/html/src/expense_forecast/ef_cli.py '.$action.' --source database --id None --working_directory /var/www/html/data/ --start_date '.$_POST["simulationstartdate"].' --end_date '.$_POST["simulationenddate"].' --username '.$_COOKIE["username"].ef_cli_database_args().' --log_directory '.$log_directory.'  --label "'.$_POST["forecastlabel"].'") 2>&1'; 
  exec($command, $output, $return_code);
  foreach ($output as &$line) {
    $latest_server_feedback=$latest_server_feedback.$line.'<br>';
    // if ( str_starts_with($line,'forecast_id=') ){
    //   $forecast_id = explode('=',$line)[1];
    //   $forecast_set_id = '';

    //   $forecast_set_name = '';
    //   $forecast_name = $_POST["forecastlabel"];

    //   $q = "INSERT INTO prod.".$username."_staged_forecast_details Select '".$forecast_set_id."','".$forecast_id."','".$forecast_set_name."','".$forecast_name."','".$_POST["simulationstartdate"]."','".$_POST["simulationenddate"]."'";

    //   $query_obj = pg_query($dbconn, $q);
    // } else {
    //   $latest_server_feedback=$latest_server_feedback.$line.'<br>';
    // }
  }
}

$_SESSION['latest_server_feedback'] = $latest_server_feedback;


//POST vars
// forecastname  
//overwriteforecast approximateforecast runscenarios


  //setid, id, title, subtitle

header('Location: /expense_forecast.php');
?>
