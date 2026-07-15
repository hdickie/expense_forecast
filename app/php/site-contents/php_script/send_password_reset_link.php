<?php
require_once __DIR__ . '/config.php';
header( "refresh:5;url=/" );
echo 'A password reset link has been send to the email address associated with '.$_POST['username'].'.<br>';
echo 'You will be redirected in about 5 secs. If not, please click <a href="/">here</a>.';
?>