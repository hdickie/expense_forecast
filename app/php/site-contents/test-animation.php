<?php
require_once __DIR__ . '/php_script/config.php';
session_start();
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
ini_set('max_execution_time', '2147483647');

     $dbconn = ef_pg_connect();

    if (isset($_COOKIE['login_token'])) {
      $query_obj = pg_query($dbconn, "select * from session where login_token = '".$_COOKIE['login_token']."'") or die('Error message: ' . pg_last_error());
        $query_result = pg_fetch_row($query_obj);

       if ( $query_result ) {
          $auth_successful = True;

          //the cookie is supposed to expire after 8 hours, but a malicious actor could keep it alive longer
          //therefore, we check the timeout server side as well
          $query_obj = pg_query($dbconn, "select value from session where login_token = '".$_COOKIE['login_token']."' and key = 'login_timestamp'") or die('Error message: ' . pg_last_error());
          $query_result = pg_fetch_row($query_obj);

          $seconds_since_login = (time() - (int)$query_result[0]);

          if ( $seconds_since_login > 60*60*8 ) {
             setcookie('login_token', '', -1, "/");
             header('Location: /index.php');
          }


        } else {
          header('Location: /index.php');
        } //there is no corresonding session key in the database
        pg_close($dbconn);
    } else {
       $auth_successful = False;
       header('Location: /index.php');
    }
    
?>
<!DOCTYPE html>
<html xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title></title>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
	<link rel="icon" type="image/x-icon" href="favicon.ico">
	<link rel="stylesheet" href="/css/style.css">
	<link rel="stylesheet" href="/css/jquery-ui.css">

	<script src="/script/jquery-3.6.1.js"></script>
<script src="/script/jquery-ui.js"></script>

	<!-- Google tag (gtag.js) -->
	<script async src="https://www.googletagmanager.com/gtag/js?id=G-QPWQ8W194J"></script>
	<script>
		window.dataLayer = window.dataLayer || [];
		function gtag(){dataLayer.push(arguments);}
		gtag('js', new Date());

		gtag('config', 'G-QPWQ8W194J');
	</script>
</head>
<script>

function setCookie(name,value,days) {
var expires = "";
if (days) {
    var date = new Date();
    date.setTime(date.getTime() + (days*24*60*60*1000));
    expires = "; expires=" + date.toUTCString(); 
}
document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}
function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}
function eraseCookie(name) {   
    document.cookie = name +'=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}
    
</script>
<style>

  body {
    padding:25px;
  }

  #animated_div {
    position: fixed;
    inset: 0px;
    width: 12rem;
    height: 5rem;
    max-width: 100vw;
    max-height: 100dvh;
    margin: auto;

    width:70px;
    height:47px;
    background: #92B901;
    color: #ffffff;
    position: absolute;
    padding:10px;
    animation:animated_div 0.5s 1;
    -moz-animation:animated_div 0.5s 1;
    -webkit-animation:animated_div 0.5s 1;
    -o-animation:animated_div 0.5s 1;
    border-radius:5px;
    -webkit-border-radius:5px;
    animation-fill-mode: forwards;
    animation-timing-function: linear;

  }

  @keyframes animated_div
  {
    0% {}
/* 25% {transform: rotate(20deg);left:0px;width:25%;height:25%;}
50% {transform: rotate(0deg);left:500px;width:50%;height:50%;}
55% {transform: rotate(0deg);left:500px;width:55%;height:55%;}
70% {transform: rotate(0deg);left:500px;width:70%;height:70%;background:#1ec7e6;}*/
100% {width:1200px;height:600px;}
}

</style>
<body>
  <form id="animated_div">
    Input current account balances<br>
    Previous Forecast: ### 2024-04-01 -> 2024-06-01<br>
    Forecast Name:
    <br><br>
    <table>
      <tr>
        <th>Account Name</th>
        <th>Previous Value</th>
        <th>Current Value</th>
        <th></th>
      </tr>
      <tr>
        <td>Checking</td>
        <td>$00,000.00</td>
        <td><input type="text" id="fname" name="fname"></td>
        <td><button type="submit" value="Submit">Use Old Value</button></td>
      </tr>
      <tr>
        <td>Credit</td>
        <td>$00,000.00</td>
        <td><input type="text" id="fname" name="fname"></td>
        <td><button type="submit" value="Submit">Use Old Value</button></td>
      </tr>
    </table>
    
    <button type="button">Submit</button>
  </form>
  <div>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
    Some text i want to be covered up.<br>
  </div>
  

</body>
<script>
  $("button").click(function () {
    var msg = $("#message");
    msg[0].style.cssText = "";
    msg.text("Item saved!");
    msg.fadeIn('slow').animate({
      "bottom": "3px",
      "height": "17px",
      "font-size": "1em",
      "left": "80px",
      "line-height": "17px",
      "width": "100px"
    });
  });

</script>
<script>
  //so that mobile actually uses localStorage
  window.addEventListener('unload', () => {
     saveToLocalStorage(store.getState());
});
</script>

</html>
