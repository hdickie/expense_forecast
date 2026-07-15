<?php
require_once __DIR__ . '/config.php';
//if username already exists, redirect back to register.php
//if email already exists, redirect back to register.php

// if ( $_POST["new_password"] != $_POST["check_password"]) {
// 	setcookie('account_registration_feedback', 'Passwords do not match.', time() + (86400 / 3), '/'); 
// 	header('Location: /register.php');
// 	exit();
// }

$hashed_password = password_hash($_POST["new_password"], PASSWORD_DEFAULT);

$superuser_dbconn = ef_pg_connect();

$username_query = "Select count(*) from users where username = '".$_POST["username"]."'";
$query_obj = pg_query($superuser_dbconn,$username_query);
$username_query_result = pg_fetch_row($query_obj);
if ( $username_query_result[0] > 0 ) {
	//username already exists
	setcookie('account_registration_feedback', 'Account already exists', time() + (86400 / 3), '/'); 
	header('Location: /register.php');
	exit();
}

$email_query = "Select count(*) from users where email = '".$_POST["email"]."'";
$query_obj = pg_query($superuser_dbconn,$email_query);
$email_query_result = pg_fetch_row($query_obj);
if ( $email_query_result[0] > 0 ) {
	//email already exists
	setcookie('account_registration_feedback', 'Email already in use', time() + (86400 / 3), '/'); 
	header('Location: /register.php');
	exit();
}

//create account
$insert_q = "INSERT INTO users (username, hashed_password, email, email_is_confirmed) VALUES ('".$_POST["username"]."','".$hashed_password."','".$_POST["email"]."',False)";
$query_obj = pg_query($superuser_dbconn,$insert_q);

//generate email confirmation code
//get randint in [0,35] 6 times
$legal_chars_string = '0987654321QAZWSXEDCRFVTGBYHNUJMIKOLP';
$confirmation_code = '';
for ($x = 0; $x <= 5; $x++) {
  $confirmation_code .= $legal_chars_string[rand(0,35)];
  if ( $x == 2 ){
  	$confirmation_code .= '-';
  }
}

$valid_until_ts = date("Y-m-d H:i:s", time() + ( 86400 ));
$insert_q = "INSERT INTO email_confirmation_codes (email, confirmation_code, valid_until, attempt_count) VALUES ('".$_POST["email"]."','".$confirmation_code."','".$valid_until_ts."',0)";
$query_obj = pg_query($superuser_dbconn,$insert_q);

//send email confirmation email
$headers = 'From: noreply@humedickie.com' . "\r\n" .'Reply-To: noreply@humedickie.com' . "\r\n" .'X-Mailer: PHP/' . phpversion();
$headers .= "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/html; charset=UTF-8\r\n";
mail('hume.dickie@live.com','Account Created for humedickie.com',"Hello from humedickie.com,<br><br><a href=\"https://www.humedickie.com\">Click this link to confirm your email.</a> This link will remain valid for 24 hours.<br><br> Alternatively, go to <a href=\"https://www.humedickie.com/confirm-email/\">humedickie.com/confirm-email.php</a> and enter the following code:<br><br>".$confirmation_code." <br><br>Note that 3 failed attempts will require you to request a new confirmation code. You can request a new code here if you need it: <a href=\"https://www.humedickie.com/request-new-email-confirmation-code.php\">www.humedickie.com</a><br><br>Thanks,<br>Hume", $headers);

//prepare database to run ExpenseForecast for this user
include('prepare_database_for_new_expense_forecast_user.php');

header('Location: /index.php');
exit();
?>