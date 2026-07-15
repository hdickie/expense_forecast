<?php
require_once __DIR__ . '/php_script/config.php';
session_start();
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
ini_set('max_execution_time', '2147483647');

?>
<!DOCTYPE html>
<html xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title>Hume Dickie Portfolio</title>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
	<link rel="icon" type="image/x-icon" href="favicon.ico">
	<link rel="stylesheet" href="/css/style.css">
	
<meta name="viewport" content="width=device-width" />
    <link rel="stylesheet" href="/css/index.css">

	<script src="/script/jquery-3.6.1.js"></script>

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
span + span {
    margin-left: 10px;
}
</style>
   <body>
   
   <form id="login_form" method="POST" action="./php_script/login.php">
   <label for="username">Username:</label>
  <input type="text" id="username" name="username"><br>
  <label for="password"> Password:</label>
  <input type="password" id="password" name="password"><br>
  <button type="submit">Login</button>   
  <br>
  <span><a href="./register.php">Register</a></span>   <span><a href="./forgot_password.php">Recover Account</a></span>
  <br>
  <span id="login-feedback">
  </span>
	</form>

   </body>
   <script>
   login_feedback = document.getElementById("login-feedback");
   login_feedback.innerHTML += getCookie('login_feedback');
   document.cookie = "login_feedback=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
   </script>
<script>
	$('#login_form').submit(function() {
		form = document.getElementById("login_form");
		var formData = new FormData(form);
		localStorage.setItem('username',Object.fromEntries(formData)['username']);
	});
</script>
<script>
  //so that mobile actually uses localStorage
  window.addEventListener('unload', () => {
     saveToLocalStorage(store.getState());
});
</script>

</html>
