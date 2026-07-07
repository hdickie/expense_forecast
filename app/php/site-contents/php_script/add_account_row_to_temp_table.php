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

$account_name = $_POST['accountname'];
$min_balance = $_POST['minbalance'];
$max_balance = $_POST['maxbalance'];
if ( isset($_POST["accounttype"]) ) {
	$account_type = $_POST['accounttype'];
	$balance = $_POST['balance'];

	if ( $_POST["accounttype"] == 'Checking' ){
		$account_type = 'Checking';
		$apr = 'NULL';
		$billing_start_date_yyyymmdd = '(CAST(null AS date))';
		$current_statement_balance = 'NULL';
		$interest_balance = 'NULL';
		$interest_cadence = 'NULL';
		$minimum_payment = 'NULL';
		$previous_statement_balance = 'NULL';

		if ( isset($_POST["primary-checking-ind"]) ) {
			$primary_checking_ind = 'true';
		} else {
			$primary_checking_ind = 'false';
		}
		

		$principal_balance = 'NULL';

	} else if ( $_POST["accounttype"] == 'Credit' ){
		$apr = $_POST['creditapr'];
		$billing_start_date_yyyymmdd = "'".$_POST['creditbillingstartdate']."'";
		$current_statement_balance = $_POST['balance'] - $_POST['previousstatementbalancecredit'];
		$interest_balance = 'NULL';
		$interest_cadence = $_POST['creditinterestcadence'];
		$minimum_payment = $_POST['creditminpayment'];
		$previous_statement_balance = $_POST['previousstatementbalancecredit'];
		$primary_checking_ind = 'NULL';
		$principal_balance = 'NULL';

	} else if ( $_POST["accounttype"] == 'Loan' ){
		$apr = $_POST['loanapr'];
		$billing_start_date_yyyymmdd = "'".$_POST['loanbillingstartdate']."'";
		$current_statement_balance = 'NULL';
		$interest_balance = $_POST['interestbalance'];
		$interest_cadence = $_POST['loaninterestcadence'];
		$minimum_payment = $_POST['loanminpayment'];
		$previous_statement_balance = 'NULL';
		$primary_checking_ind = 'NULL';
		$principal_balance = $_POST['balance'] - $_POST['interestbalance'];

	} else if ( $_POST["accounttype"] == 'Investment' ){
		$apr = $_POST['investmentapr'];
		$billing_start_date_yyyymmdd = "'".$_POST['investmentbillingstartdate']."'";
		$current_statement_balance = 'NULL';
		$interest_balance = 'NULL';
		$interest_cadence = $_POST['investmentinterestcadence'];
		$minimum_payment = 'NULL';
		$previous_statement_balance = 'NULL';
		$primary_checking_ind = 'NULL';
		$principal_balance = 'NULL';
	}

	////Sanitizing empty/null values? it might be unnecessary



	if ( ! $error_ind ){
		if ( $_POST["accounttype"] == 'Checking' ){
			$insert_statement = "INSERT INTO prod.ef_account_set_".$username_according_to_server."_temporary (account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) Select '".$account_name."',".$balance.",".$min_balance.",".$max_balance.",'Checking',NULL,NULL,NULL,NULL,".$primary_checking_ind;
			//echo '<br>'.$insert_statement.'<br>';
			$query_obj = pg_query($dbconn, $insert_statement);
		}

		if ( $_POST["accounttype"] == 'Credit' ){
			$account_type = 'curr stmt bal';
			$insert_statement = "INSERT INTO prod.ef_account_set_".$username_according_to_server."_temporary ( account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) Select '".$account_name.": Curr Stmt Bal',".$current_statement_balance.",".$min_balance.",".$max_balance.",'".$account_type."',".$POSTGRES_NULL_DATE.",NULL,NULL,NULL,NULL";
			//echo '<br>'.$insert_statement.'<br>';
			$query_obj = pg_query($dbconn, $insert_statement);

			$account_type = 'prev stmt bal';
			$insert_statement = "INSERT INTO prod.ef_account_set_".$username_according_to_server."_temporary ( account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) Select '".$account_name.": Prev Stmt Bal',".$previous_statement_balance.",".$min_balance.",".$max_balance.",'".$account_type."',".$billing_start_date_yyyymmdd.",".$apr.",'".$interest_cadence."',".$minimum_payment.",".$primary_checking_ind;
			//echo '<br>'.$insert_statement.'<br>';
			$query_obj = pg_query($dbconn, $insert_statement);
		}

		if ( $_POST["accounttype"] == 'Loan' ){
			$account_type = 'principal balance';
			$insert_statement = "INSERT INTO prod.ef_account_set_".$username_according_to_server."_temporary ( account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) Select '".$account_name.": Principal Balance',".$principal_balance.",".$min_balance.",".$max_balance.",'".$account_type."',".$billing_start_date_yyyymmdd.",".$apr.",'".$interest_cadence."',".$minimum_payment.",NULL";
			//echo '<br>'.$insert_statement.'<br>';
			$query_obj = pg_query($dbconn, $insert_statement);

			$account_type = 'interest';
			$insert_statement = "INSERT INTO prod.ef_account_set_".$username_according_to_server."_temporary ( account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) Select '".$account_name.": Interest',".$interest_balance.",".$min_balance.",".$max_balance.",'".$account_type."',".$POSTGRES_NULL_DATE.",NULL,NULL,NULL,NULL";
			//echo '<br>'.$insert_statement.'<br>';
			$query_obj = pg_query($dbconn, $insert_statement);
		}
	}
	//todo investment

} else {
	$error_message = $error_message.'Account Type must have a value.<br>';
	$error_ind = True;
}

//echo 'error_ind:'.((int) $error_ind).'<br>';

// if ( $error_ind ) {
// 	echo $error_message;
// }
//$query_result = pg_fetch_all($query_obj);

header('Location: /expense_forecast.php');
?>