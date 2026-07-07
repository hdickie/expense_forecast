<?php
require_once __DIR__ . '/config.php';
$dbconn = ef_pg_connect();

//business logic deletes rows with attempt_count 3 or greater
$confirmation_code_existence_query = "Select count(*) from email_confirmation_codes where email = '".$_POST["email"]."' and attempt_count < 3";
$confirmation_code_existence_query_obj = pg_query($dbconn,$confirmation_code_existence_query);
$confirmation_code_existence_query_result = pg_fetch_row($confirmation_code_existence_query_obj);
$confirmation_code_existence = $confirmation_code_existence_query_result[0];

if ( $confirmation_code_existence > 0 ) {
	//the attempt count filter is redundant here but I include it to make it clear that it is logically the same as above
	$confirmation_code_query = "Select confirmation_code from email_confirmation_codes where email = '".$_POST["email"]."' and attempt_count < 3";
	$conf_code_query_obj = pg_query($dbconn,$confirmation_code_query);
	$confirmation_code_query_result = pg_fetch_row($conf_code_query_obj);
	$expected_conf_code = $confirmation_code_query_result[0];

	$attempts_remaining_query = "Select attempt_count from email_confirmation_codes where email = '".$_POST["email"]."'";
	$attempts_remaining_query_obj = pg_query($dbconn,$attempts_remaining_query);
	$attempts_remaining_query_result = pg_fetch_row($attempts_remaining_query_obj);
	$attempts_count = $attempts_remaining_query_result[0];

	if ( $_POST["confirmation-code"] == $expected_conf_code ) {
		//todo update user table 

		$confirm_email_q = "UPDATE users SET email_is_confirmed = 'true'where email = '".$_POST["email"]."'";
		pg_query($dbconn,$confirm_email_q);

		$delete_codes_q = "DELETE FROM email_confirmation_codes where email = '".$_POST["email"]."'";
		pg_query($dbconn,$delete_codes_q);

		setcookie('email_confirmation_feedback', 'Success! Your email has been confirmed', time() + (86400/24), '/'); 
	} else {

		//increment attempt_count. if 3 or greater, delete
		if ( $attempts_count < 2 ) { //if attempts count was already 3, then delete
			$update_attempt_count_q = "UPDATE email_confirmation_codes SET attempt_count = attempt_count + 1 where email = '".$_POST["email"]."'";
			pg_query($dbconn,$update_attempt_count_q);
			$attempts_remaining = 2 - $attempts_count; //if this code is reached, then 1 attempt has already been used, hence 2 - $attempts_count
			setcookie('email_confirmation_feedback', 'Failed. '.$attempts_remaining.' attempts remaining', time() + (86400/24), '/'); 
		} else {
			$delete_codes_q = "DELETE FROM email_confirmation_codes where email = '".$_POST["email"]."'";
			pg_query($dbconn,$delete_codes_q);
			setcookie('email_confirmation_feedback', 'Max attempts reached. Please request a new email confirmation code.', time() + (86400/24), '/'); 
		}

		
		
	}
} else {
	setcookie('email_confirmation_feedback', 'Your confirmation code did not match or has expired. Please request a new one.', time() + (86400/24), '/'); 
}
header('Location: /confirm-email.php');
?>