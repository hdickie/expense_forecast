<?php
require_once __DIR__ . '/config.php';
$POSTGRES_NULL_DATE = '(CAST(null AS date))';

$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn,"Select value from session where key = 'username' and login_token = '".$_COOKIE["login_token"]."'");
$query_result = pg_fetch_row($query_obj);
$username_according_to_server = $query_result[0];

//var_dump($_POST);
//echo '<br><br><br><br>';

$error_message = '';
$error_ind = False;

// ["budgetitemmemo"]=> string(4) "test" 
// ["budgetitempriority"]=> string(1) "1" 
// ["budgetitemstartdate"]=> string(10) "2024-03-07" 
// ["budgetitemenddate"]=> string(10) "2024-03-28" 
// ["budgetitemcadence"]=> string(5) "Daily" 
// ["budgetitemamount"]=> string(2) "10" 
// ["budgetitemdeferrableyes"]=> string(3) "Yes" 
// ["budgetitempartialpaymentallowedyes"]=> string(3) "Yes"


if ( isset($_POST["budgetitemdeferrableyes"]) ){
	$deferrable = 'true';
} else {
	$deferrable = 'false';
}

if ( isset($_POST["budgetitempartialpaymentallowedyes"]) ){
	$partial_payment_allowed = 'true';
} else {
	$partial_payment_allowed = 'false';
}

if ( isset($_POST["nobudgetitemenddate"]) ){
	$budget_item_end_date = '2200-12-31';
} else {
	$budget_item_end_date = $_POST["budgetitemenddate"];
}




$insert_statement = "INSERT INTO prod.ef_budget_item_set_optional_".$username_according_to_server."_temporary (start_date, end_date, priority, cadence, amount, memo, \"deferrable\", partial_payment_allowed) Select '".$_POST["budgetitemstartdate"]."','".$budget_item_end_date."',".$_POST["budgetitempriority"].",'".$_POST["budgetitemcadence"]."',".$_POST["budgetitemamount"].",'".$_POST["budgetitemmemo"]."',".$deferrable.",".$partial_payment_allowed;
//echo '<br>'.$insert_statement.'<br>';		
$query_obj = pg_query($dbconn, $insert_statement);


//$query_result = pg_fetch_all($query_obj);

header('Location: /expense_forecast.php');
?>