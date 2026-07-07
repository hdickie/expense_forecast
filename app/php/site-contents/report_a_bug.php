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
	<title>Report a Bug</title>
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
<style>
	.Row {
  display: table;
  width: 100%; /*Optional*/
  table-layout: fixed; /*Optional*/
  padding:2px;
}
.Column {
  display: table-cell;

}
</style>
<body>
	<div id="all-view-page-header" class="Row">
		<div id="all-view-page-header-col1" class="Column" style="width:10%">
		</div>
		<div id="all-view-page-header-col2" class="Column">
			<h1 id="page-title">Report a Bug</h1>
			<label for="bug-report-text">Please describe the unexpected behavior:</label>
			<br><br>
			<form method="POST" action="./php_script/submit_bug_report.php">
	<textarea id="bug-report-text" name="bug-report-text" rows="4" cols="50"></textarea>
	<br>
	<input type="submit" value="Submit Bug Report">
</form>
		</div>
		<div id="all-view-page-header-login-panel" class="Column">

			<form id="logout_button" method="POST" action="./php_script/logout.php">
				<div id="logged-in-login-details">
					<label for="login-details" id="login-details-welcome-message">Welcome, </label>
					<input type="submit" value="Logout">
				</div>
				<div id="logged-out-login-details">
					Welcome, <b>Guest</b>. <a href="index.php">Login here</a>
				</div>


			</form>
		</div>
	</div>
	<h1></h1>
</body>
<script>
	lod = document.getElementById("logged-out-login-details");
	lid = document.getElementById("logged-in-login-details");
	welcome_message = document.getElementById("login-details-welcome-message");

	if ( localStorage.getItem('username') != 'null' ){
		lod.style.display = 'none';
		welcome_message.innerHTML += '<b>'+localStorage.getItem('username')+'</b>.';
	} else {
		lid.style.display = 'none';
	}


  //this does not suffice because they stay in the same vertical positon even when not showing
  //lod.style.display = "none";
  //lid.style.display = "none";
</script>
<script>
  //so that mobile actually uses localStorage
  window.addEventListener('unload', () => {
     saveToLocalStorage(store.getState());
});
</script>

</html>
