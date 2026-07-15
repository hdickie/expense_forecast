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
	<title>New User Information</title>
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
.pad {
  margin: auto;  
  padding: 10px 40px 10px 40px;
  text-align: left;
}
</style>
<body class="pad">
<h2>Welcome!</h2>
<p>If you are seeing this page, it is because I have invited you to use the same automated data analysis tools that I am using for myself.</p>
<p>Because I paid for the cheaper version of web hosting, this website cannot run these tools for you. I have made a docker image that will run a local version of this website on your own device. If you would like to be able to login to humedickie.com to access your data from anywhere, you can set that up too, but it is not required.</p>

<h2>Step 1: Set up the docker image</h2>
<ol>
<li><a href="https://docs.docker.com/engine/install/">Install Docker</a></li>
<li>Download the docker image</li>
</ol>



</body>
<script>
  //so that mobile actually uses localStorage
  window.addEventListener('unload', () => {
     saveToLocalStorage(store.getState());
});
</script>

</html>
