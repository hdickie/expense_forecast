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
	<title>Register</title>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
	<link rel="icon" type="image/x-icon" href="favicon.ico">
	<link rel="stylesheet" href="/css/style.css">
	
<meta name="viewport" content="width=device-width" />
    
	
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
<script>
function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}
</script>
<body>
<form id="registration-form" method="POST" action="./php_script/create_user_account.php" autocomplete="off" required>

<label for="username">Username (between 4 and 20 characters, alphanumeric):</label><br>
<input type="text" id="username" name="username" autocomplete="off" pattern="^(?=[a-zA-Z0-9._]{4,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"><br> <!-- I acknowledge that this is a weird regex to use -->
<label for="new_password">New Password (Minimum eight characters, at least one letter, one number and one special character):</label><br>
<input type="password" id="new_password" name="new_password" autocomplete="off" pattern="^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"><br>
<label for="check_password">Re-enter Password:</label><br>
<input type="password" id="check_password" name="check_password" autocomplete="off" oninput="check()"><br>
<label for="email">Email address:</label><br>
<input type="text" id="email" name="email" autocomplete="off" pattern="^([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$"><br>
<input type="submit" value="Create Account">
</form>
<span id="account-registration-feedback"></span>
</body>
<script>
function check() {
    var new_password = document.getElementById('new_password');
    if (new_password.value != document.getElementById('check_password').value) {
        new_password.setCustomValidity('Passwords must match');
    } else {
        // input is valid -- reset the error message
        new_password.setCustomValidity('');
    }
}
</script>
<script>
   login_feedback = document.getElementById("account-registration-feedback");
   login_feedback.innerHTML += getCookie('account_registration_feedback');
   document.cookie = "login_feedback=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
   </script>
<script>
  //so that mobile actually uses localStorage
  window.addEventListener('unload', () => {
     saveToLocalStorage(store.getState());
});
</script>

</html>
