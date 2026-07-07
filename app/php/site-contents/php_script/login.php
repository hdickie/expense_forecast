<?php
require_once __DIR__ . '/config.php';
function debug_to_console($data) {
    $output = $data;
    if (is_array($output))
        $output = implode(',', $output);
}



$hostname = gethostname();

// debug_to_console("Hostname:");
// debug_to_console($hostname);
//localhost: HumeDickiesMBP.hsd1.ca.comcast.net
//remote: box5596.bluehost.com
//i am shocked that the remote legit redirected to my local machine.
//i know that only works for me and makes sense after I think about it
//but I am disappointed checking the hostname did not give me
//the behavior that I wanted

$username = $_POST["username"];

$dbconn = ef_pg_connect();

$username_existence_query_obj = pg_query($dbconn, "Select count(*) from users where username = '".$username."'");
$username_existence_query_result = pg_fetch_row($username_existence_query_obj);
$username_existence = $username_existence_query_result[0]; 



// echo '<br>pwd : '.$_POST["password"].'<br>';
// echo '<br>hash: '.$hashed_db_password.'<br>';

if ( $username_existence == 1 ){

    
    $query_obj = pg_query($dbconn, "Select hashed_password from users where username = '".$username."'");
    $query_result = pg_fetch_row($query_obj);
    $hashed_db_password = $query_result[0]; 
    if (password_verify($_POST["password"], $hashed_db_password)) {

    $auth_successful = True;

    if ( $_POST["username"] == 'hume' ) {
      $newURL = '/directory.php';
    } else {
      $newURL = '/expense_forecast.php';
    }

} else {

   $newURL = '/index.php';
   setcookie('login_feedback', '<br>Login failed.', time() + (86400 / 3), '/'); 
    $auth_successful = False;
 }

} else {
    $newURL = '/index.php';
   setcookie('login_feedback', '<br>User does not exist.', time() + (86400 / 3), '/'); 
    $auth_successful = False;
}




if ( $auth_successful ) {
    //echo 'auth success';
 
 $token = bin2hex(random_bytes(16));
 setcookie('username',$username, time() + (86400 / 3), "/");
 setcookie('login_token', $token, time() + (86400 / 3), "/"); // 86400 = 1 day, so cookie is valid for 8 hours
 $query_obj = pg_query($dbconn, "insert into session select '".$token."','username','".$_POST["username"]."'") or die('Error message: ' . pg_last_error());
 $query_obj = pg_query($dbconn, "insert into session select '".$token."','login_timestamp','".time()."'") or die('Error message: ' . pg_last_error());
 //$query_obj = pg_query($dbconn, "select * from test_table") or die('Error message: ' . pg_last_error());
 //$query_result = pg_fetch_row($query_obj);
    //var_dump($query_result);

 pg_close($dbconn);
} 
// else {
//     echo 'auth fail';
//  }




 //todo record session id


//debug_to_console('Redirecting to:');
//debug_to_console($newURL);
header('Location: '.$newURL);

//window.location = '<?php echo $domain_name /services.htm';
?>