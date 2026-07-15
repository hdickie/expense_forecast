<?php
require_once __DIR__ . '/config.php';
$dbconn = ef_pg_connect();

//check that email is in use
$username_query = "Select count(*) from users where email = '".$_POST["email"]."'";
$username_query_obj = pg_query($dbconn,$username_query);
$username_query_result = pg_fetch_row($username_query_obj);

//check is not already confirmed
$not_confirmed_query = "Select count(*) from users where email = '".$_POST["email"]."' and email_is_confirmed='false'";
$conf_query_obj = pg_query($dbconn,$not_confirmed_query);
$conf_query_result = pg_fetch_row($conf_query_obj);

$server_feedback ='';

if ( $username_query_result[0] > 0 ) {

} else {
	$server_feedback = 'Email is not in use.';
	setcookie('request_new_email_confirmation_code_feedback', $server_feedback, time() + (86400/24) , '/'); 
	header('Location: /request-new-email-confirmation-code.php');
	exit();
}

if ( ( $username_query_result[0] > 0 ) && ( $conf_query_result[0] > 0 ) ){

	//delete any existing confirmation codes
	$delete_existing_conf_codes_query = "DELETE FROM email_confirmation_codes WHERE email = '".$_POST["email"]."'";
	//echo $delete_existing_conf_codes_query;
	$delete_existing_conf_codes_query_obj = pg_query($dbconn,$delete_existing_conf_codes_query);

	//generate new conf code
	$legal_chars_string = '0987654321QAZWSXEDCRFVTGBYHNUJMIKOLP';
	$confirmation_code = '';
	for ($x = 0; $x <= 5; $x++) {
	  $confirmation_code .= $legal_chars_string[rand(0,35)];
	  if ( $x == 2 ){
	  	$confirmation_code .= '-';
	  }
	}

	//insert to db
	$valid_until_ts = date("Y-m-d H:i:s", time() + ( 86400 ));
	$insert_q = "INSERT INTO email_confirmation_codes (email, confirmation_code, valid_until, attempt_count) VALUES ('".$_POST["email"]."','".$confirmation_code."','".$valid_until_ts."',0)";
	$query_obj = pg_query($dbconn,$insert_q);

	$headers = 'From: noreply@humedickie.com' . "\r\n" .'Reply-To: noreply@humedickie.com' . "\r\n" .'X-Mailer: PHP/' . phpversion();
	$headers .= "MIME-Version: 1.0\r\n";
	$headers .= "Content-Type: text/html; charset=UTF-8\r\n";

	//deliver
	mail('hume.dickie@live.com','Email Confirmation code for humedickie.com',"Hello from humedickie.com,<br><br>
		You new email confirmation code is ".$confirmation_code, $headers);

	$server_feedback = 'A new confirmation code has been sent.';

} else {
	$server_feedback = 'Email has already been confirmed.';
}


//set feedback
setcookie('request_new_email_confirmation_code_feedback', $server_feedback, time() + (86400/24) , '/'); 

//redirect
header('Location: /request-new-email-confirmation-code.php');
?>