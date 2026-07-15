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
	<title>Expense Forecast v1.0</title>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
	<link rel="icon" type="image/x-icon" href="favicon.ico">
	<link rel="stylesheet" href="/css/style.css">
	<link rel="stylesheet" href="/css/expense_forecast.css">
<link rel="stylesheet" href="/css/jquery-ui.css">

	<script src="/script/jquery-3.6.1.js"></script>
<script src="/script/jquery-ui.js"></script>
<script src="/script/d3.v4.min.js"></script>
<script src="/script/drawExpenseForecastPlot.js"></script>
<script src="/script/drawCompareExpenseForecastPlot.js"></script>

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
<?php 

  //can be SHOW_LOADED or SHOW_RUN or PAGE_LOAD.
if ( isset($_COOKIE['display_mode'])){
  $forecast_display_mode = $_COOKIE['display_mode'];
} else {
  $forecast_display_mode = 'PAGE_LOAD';
}


$dbconn = ef_pg_connect();
$query_obj = pg_query($dbconn, "select value from session where key = 'username' and login_token = '".$_COOKIE['login_token']."'");
$username = pg_fetch_row($query_obj)[0];

$forecast_set_id = '';
$forecast_set_file_path = '';
if ( isset($_COOKIE['forecastidtoload']) ) {

  $forecast_table_name = $username.'_forecast_'.$_COOKIE['forecastidtoload'];
  //and tableowner = '".$username."' todo tables are created by virtuoso_user no matter what
  //not really a problem for my current use cases so I'm moving on
  $table_existence_q = "SELECT count(*) FROM pg_catalog.pg_tables where schemaname = 'prod'  and tablename = '".strtolower($forecast_table_name)."'";
  $forecast_table_exists_obj = pg_query($dbconn, $table_existence_q);
  
  $forecast_metadata_exists_obj = pg_query($dbconn, "select count(*) from prod.".$username."_forecast_run_metadata where forecast_id = '".$_COOKIE['forecastidtoload']."'");

  $forecast_set_existence_q = "SELECT CASE WHEN count(*) > 0 THEN 1 ELSE 0 END FROM prod.".$username."_forecast_set_definitions where forecast_id = '".$_COOKIE['forecastidtoload']."'";
  //echo($forecast_set_existence_q);
  $forecast_set_existence_obj = pg_query($dbconn, $forecast_set_existence_q);
  $set_exists = pg_fetch_row($forecast_set_existence_obj)[0];

  $forecast_set_q = "SELECT * FROM prod.".$username."_forecast_set_definitions where forecast_id = '".$_COOKIE['forecastidtoload']."'";
  $forecast_set_obj = pg_query($dbconn, $forecast_set_q);
  
  $unique_sets_q = "SELECT distinct forecast_set_id FROM prod.".$username."_forecast_set_definitions where forecast_id = '".$_COOKIE['forecastidtoload']."'";
  $unique_sets_obj = pg_query($dbconn, $unique_sets_q);
  $unique_sets = pg_fetch_all($unique_sets_obj);

  $sibling_forecasts_q = "SELECT distinct q1.forecast_name FROM prod.".$username."_forecast_set_definitions q1 JOIN prod.".$username."_forecast_set_definitions q2 ON q1.forecast_set_id = q2.forecast_set_id where q2.forecast_id = '".$_COOKIE['forecastidtoload']."'";
  $sibling_forecasts_obj = pg_query($dbconn, $sibling_forecasts_q);
  $sibling_forecast_ids_pg = pg_fetch_all($sibling_forecasts_obj);

  $sibling_forecast_ids = array();
  foreach($sibling_forecast_ids_pg as $array) {
    array_push($sibling_forecast_ids,$array['forecast_name']); 
  }

  // echo '$forecast_set_exists:<br>';
  // echo $forecast_set_exists;
  // if ( $forecast_set_exists == 1 ) {
  //   // echo 'set exists<br>';
  //   $set_exists=1;
  // } else {
  //   echo 'set does not exist<br>';
  //   $set_exists=0;
  // }

  if ( pg_fetch_row($forecast_table_exists_obj)[0] == 0 ) {
    $table_exists=0;
  } else {
    $table_exists=1;
  }

  if ( pg_fetch_row($forecast_metadata_exists_obj)[0] == 0 ) {
    $metadata_exists=0;
  } else {
    $metadata_exists=1;
  }

    if ( $table_exists == 1 ) { //todo some more nuance can be added here
      $forecast_id = $_COOKIE["forecastidtoload"];
      $forecast_file_path = '../data/Forecast_'.$_COOKIE['forecastidtoload'].'.csv';
    } else {
      $forecast_id = '';
      $forecast_file_path = '';
    }

    //todo
    $parent_forecast_set_ids = array();
    if ( $set_exists == 1 ) {
      foreach($unique_sets as $array) {
        array_push($parent_forecast_set_ids,$array['forecast_set_id']); //a forecast MAY belong to multiple parents. These are those parents.

        //todo there is more logic here, but let's have our next focus be a toggle list of these parents
      }
      //print_r($parent_forecast_set_ids);
      //this will work when there is only 1 parent forecast, else will select one of them unstably.
      $forecast_set_file_path = '../data/ForecastSet_'.$parent_forecast_set_ids[0].'.json';
    } // else no siblings and thats fine, $sibling_forecast_ids will be empty

    
  } else {
    $forecast_id = '';
    $forecast_file_path = '';
  }
  

  //most recent forecast_run
  //$query_obj = pg_query($dbconn, "select forecast_id from prod.forecast_run_metadata where username = '".$username."' order by submit_ts desc limit 1");
  $query_obj_row = pg_fetch_row($query_obj);

  //if ( $query_obj_row == '') {
  //  $forecast_id = '';
  //} else {
  //  $forecast_id = $query_obj_row[0];
  //}
  
  ?>
  <?php 

  if ( isset($_SESSION['latest_server_feedback']) ) {
    $latest_server_feedback=addslashes($_SESSION['latest_server_feedback']);
    $_SESSION['latest_server_feedback'] = '';
  } else {
    $latest_server_feedback='';
  }

  ?>
  <style>
    .hide_table_button {
      transform:rotate(90deg);
    }
  </style>
  <script type="text/javascript">
    var latest_server_feedback=`<?php echo str_replace('`','',addslashes($latest_server_feedback));?>`;
    var forecast_id=`<?php echo $forecast_id ;?>`;
    var forecast_id_to_load=`<?php echo $_COOKIE["forecastidtoload"] ;?>`;
    var forecast_table_name = `<?php echo $forecast_table_name ;?>`;
    var forecast_file_path = `<?php echo $forecast_file_path ?>`;
    var table_existence_q = `<?php echo $table_existence_q ;?>`;

    console.log('forecast_id:');
    console.log(forecast_id);
    console.log('forecast_id_to_load:');
    console.log(forecast_id_to_load);
    console.log('forecast_table_name:');
    console.log(forecast_table_name);
    console.log('forecast_file_path:');
    console.log(forecast_file_path);
    console.log(latest_server_feedback);

  </script>
  <script type="text/javascript">

    function showNewView(){

      $( ".runview" ).css( "display", "none" );
      $( ".viewview" ).css( "display", "none" );
      $( ".compareview" ).css( "display", "none" );
      $( ".activityview" ).css( "display", "none" );
      $( ".exportview" ).css( "display", "none" );
      $( ".newview" ).css( "display", "block" );
      localStorage.setItem('displaymode', 'new');

      d3.selectAll("svg").remove();
    }
    function showRunView(){
      $( ".newview" ).css( "display", "none" );
      $( ".viewview" ).css( "display", "none" );
      $( ".compareview" ).css( "display", "none" );
      $( ".activityview" ).css( "display", "none" );
      $( ".exportview" ).css( "display", "none" );
      $( ".runview" ).css( "display", "block" );
      localStorage.setItem('displaymode', 'stage');
      d3.selectAll("svg").remove();
    }
    function showViewView(){
      $( ".newview" ).css( "display", "none" );
      $( ".runview" ).css( "display", "none" );
      $( ".compareview" ).css( "display", "none" );
      $( ".activityview" ).css( "display", "none" );
      $( ".exportview" ).css( "display", "none" );
      $( ".viewview" ).css( "display", "block" );
      localStorage.setItem('displaymode', 'view');
      drawExpenseForecastPlot(event, 'Plot Title: Net Worth','NetWorth', '<?php echo $forecast_file_path ?>' );
    }
    function showCompareView(){
      $( ".newview" ).css( "display", "none" );
      $( ".runview" ).css( "display", "none" );
      $( ".viewview" ).css( "display", "none" );
      $( ".activityview" ).css( "display", "none" );
      $( ".exportview" ).css( "display", "none" );
      $( ".compareview" ).css( "display", "block" );
      localStorage.setItem('displaymode', 'compare');
      drawCompareExpenseForecastPlot(event, 'Compare Plot Title: All', 'All', '<?php echo $forecast_set_file_path ?>');
    }
    function showActivityView(){
      $( ".newview" ).css( "display", "none" );
      $( ".runview" ).css( "display", "none" );
      $( ".viewview" ).css( "display", "none" );
      $( ".compareview" ).css( "display", "none" );
      $( ".exportview" ).css( "display", "none" );
      $( ".activityview" ).css( "display", "block" );
      localStorage.setItem('displaymode', 'list');
      d3.selectAll("svg").remove();
    }
    function showExportView(){
      $( ".newview" ).css( "display", "none" );
      $( ".runview" ).css( "display", "none" );
      $( ".viewview" ).css( "display", "none" );
      $( ".compareview" ).css( "display", "none" );
      $( ".activityview" ).css( "display", "none" );
      $( ".exportview" ).css( "display", "block" );
      localStorage.setItem('displaymode', 'export');
      d3.selectAll("svg").remove();
    }

    function updateActiveButton(modename) {
     tab = document.querySelector('#newmodebutton');
     tab.style.backgroundColor = 'grey';
     tab = document.querySelector('#stagemodebutton');
     tab.style.backgroundColor = 'grey';
     tab = document.querySelector('#viewmodebutton');
     tab.style.backgroundColor = 'grey';
     tab = document.querySelector('#comparemodebutton');
     tab.style.backgroundColor = 'grey';
     tab = document.querySelector('#listmodebutton');
     tab.style.backgroundColor = 'grey';
     tab = document.querySelector('#exportmodebutton');
     tab.style.backgroundColor = 'grey';

     if (modename == 'new') {
       tab = document.querySelector('#newmodebutton');
       tab.style.backgroundColor = '#33cfff';
       localStorage.setItem('displaymode', 'new');
     } else if (modename == 'stage') {
       tab = document.querySelector('#stagemodebutton');
       tab.style.backgroundColor = '#33cfff';
       localStorage.setItem('displaymode', 'stage');
     } else if (modename == 'view') {
       tab = document.querySelector('#viewmodebutton');
       tab.style.backgroundColor = '#33cfff';
       localStorage.setItem('displaymode', 'view');
     } else if (modename == 'compare') {
       tab = document.querySelector('#comparemodebutton');
       tab.style.backgroundColor = '#33cfff';
       localStorage.setItem('displaymode', 'compare');
     } else if (modename == 'list') {
       tab = document.querySelector('#listmodebutton');
       tab.style.backgroundColor = '#33cfff';
       localStorage.setItem('displaymode', 'list');
     } else if (modename == 'export') {
       tab = document.querySelector('#exportmodebutton');
       tab.style.backgroundColor = '#33cfff';
       localStorage.setItem('displaymode', 'export');
     }

   }

   function deleteScenarioTableRow(node){
    parent_tr = node.parentNode.parentNode;

    row_details = {};
    row_details['choice_name'] = parent_tr.querySelector('.choice_name').innerHTML;
    row_details['option_name'] = parent_tr.querySelector('.option_name').innerHTML;

    $.post('./php_script/delete_scenario_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteSavedForecastTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var forecast_id = parent_tr.querySelector('.forecast_id').innerHTML;
    row_details = {};
    row_details['forecast_id'] = forecast_id;
    $.post('./php_script/delete_forecast_set_definition_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteAccountTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var account_name = parent_tr.querySelector('.account_name').innerHTML;
// var balance = parent_tr.querySelector('.balance').innerHTML;
// var min_balance = parent_tr.querySelector('.min_balance').innerHTML;
// var max_balance = parent_tr.querySelector('.max_balance').innerHTML;
// var account_type = parent_tr.querySelector('.account_type').innerHTML;
// var billing_start_date_yyyymmdd = parent_tr.querySelector('.billing_start_date_yyyymmdd').innerHTML;
// var apr = parent_tr.querySelector('.apr').innerHTML;
// var interest_interval = parent_tr.querySelector('.interest_interval').innerHTML;
// var minimum_payment = parent_tr.querySelector('.minimum_payment').innerHTML;
// var primary_checking_ind = parent_tr.querySelector('.primary_checking_ind').innerHTML;

    row_details = {};
    row_details['account_name'] = account_name;
// row_details['balance'] = balance;
// row_details['min_balance'] = min_balance;
// row_details['max_balance'] = max_balance;
// row_details['account_type'] = account_type;
// row_details['billing_start_date_yyyymmdd'] = billing_start_date_yyyymmdd;
// row_details['apr'] = apr;
// row_details['interest_interval'] = interest_interval;
// row_details['minimum_payment'] = minimum_payment;
// row_details['primary_checking_ind'] = primary_checking_ind;

    $.post('./php_script/delete_account_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteOptionalBudgetItemTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var memo = parent_tr.querySelector('.memo').innerHTML;

    row_details = {};
    row_details['memo'] = memo;
    $.post('./php_script/delete_optional_budget_item_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteBudgetItemTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var memo = parent_tr.querySelector('.memo').innerHTML;

    row_details = {};
    row_details['memo'] = memo;
    $.post('./php_script/delete_budget_item_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteMemoRuleTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var memo_regex = parent_tr.querySelector('.memo_regex').innerHTML;

    row_details = {};
    row_details['memo_regex'] = memo_regex;
    $.post('./php_script/delete_memo_rule_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteAccountMilestoneTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var milestone_name = parent_tr.querySelector('.milestone_name').innerHTML;

    row_details = {};
    row_details['milestone_name'] = milestone_name;
    row_details['milestone_name'] = row_details['milestone_name'].replace('&lt;','<');
    row_details['milestone_name'] = row_details['milestone_name'].replace('&gt;','>');

    $.post('./php_script/delete_account_milestone_table_row.php', row_details , function (resp) {
      //console.log(row_details);
      parent_tr.remove();
    });
  }

  function deleteMemoMilestoneTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var milestone_name = parent_tr.querySelector('.milestone_name').innerHTML;

    row_details = {};
    row_details['milestone_name'] = milestone_name;
    $.post('./php_script/delete_memo_milestone_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteCompositeMilestoneTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var milestone_name = parent_tr.querySelector('.composite_milestone_name').innerHTML;

    row_details = {};
    row_details['composite_milestone_name'] = milestone_name;
    row_details['composite_milestone_name'] = row_details['composite_milestone_name'].replace('&lt;','<');
    row_details['composite_milestone_name'] = row_details['composite_milestone_name'].replace('&gt;','>');
    $.post('./php_script/delete_composite_milestone_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });
  }

  function deleteChoicesTableRow(node) {
    parent_tr = node.parentNode.parentNode;

    var option_name = parent_tr.querySelector('.option_name').innerHTML;
    var choice_name = parent_tr.querySelector('.choice_name').innerHTML;

    row_details = {};
    row_details['choice_name'] = choice_name.replace('&lt;','<');
    row_details['choice_name'] = row_details['choice_name'].replace('&gt;','>');

    row_details['option_name'] = option_name.replace('&lt;','<');
    row_details['option_name'] = row_details['option_name'].replace('&gt;','>');

  // console.log('row_details:');
  // console.log(row_details);

    $.post('./php_script/delete_choice_table_row.php', row_details , function (resp) {
      parent_tr.remove();
    });


 // $('#ChangePermission').click(function() {
 //     $.ajax({
 //         url: 'change_permission.php',
 //         type: 'POST',
 //         data: {
 //             'user': document.GetElementById("user").value,
 //             'perm': document.GetElementById("perm").value
 //         },
 //         success: function(result) { //we got the response
 //             alert('Successfully called');
 //         },
 //         error: function(jqxhr, status, exception) {
 //             alert('Exception:', exception);
 //         }
 //     })
 // })


  }

</script>
<script>
      //document.getElementById("defaultOpen").click();

 function openParameterTab(evt, tabName) {
    // Declare all variables
  var i, tabcontent, tablinks;

    // Get all elements with class="parametertabcontent" and hide them
  tabcontent = document.getElementsByClassName("parametertabcontent");
  for (i = 0; i < tabcontent.length; i++) {
   tabcontent[i].style.display = "none";
 }

    // Get all elements with class="tablinks" and remove the class "active"
 tablinks = document.getElementsByClassName("tablinks");
 for (i = 0; i < tablinks.length; i++) {
   tablinks[i].className = tablinks[i].className.replace(" active", "");
 }

// Show the current tab, and add an "active" class to the button that opened the tab
 document.getElementById(tabName).style.display = "block";
 if ( evt == '' ){
  localStorage.setItem('activeParameterTab','Run');
  document.getElementById('RunParameterTab').className += " active";
} else {
  localStorage.setItem('activeParameterTab',tabName);
  evt.currentTarget.className += " active";
}
}
//openParameterTab(-1, localStorage.getItem('activeParameterTab'));

</script>
<body>

  <div id="all-view-page-header" class="Row">
    <div id="all-view-page-header-interactmodepanel" class="Column">
      <div class="table">
        <div class="tr">
          <div class="td"><button id="newmodebutton" type="button" class="runmodebutton interactmodebutton Column" onclick="showNewView();updateActiveButton('new');">New</button></div>
          <div class="td"><button id="viewmodebutton" type="button" class="viewmodebutton interactmodebutton Column" onclick="showViewView();updateActiveButton('view');">View</button></div>
          <div class="td"><button id="listmodebutton" type="button" class="listmodebutton interactmodebutton Column notyetimplemented" onclick="showActivityView();updateActiveButton('runs');">Activity</button></div>
        </div>
        <div class="tr">
          <div class="td"><button id="stagemodebutton" type="button" class="stagemodebutton interactmodebutton Column" onclick="showRunView();updateActiveButton('run');">Run</button></div>
          <div class="td"><button id="comparemodebutton" type="button" class="comparemodebutton interactmodebutton Column notyetimplemented" style="color:red" onclick="showCompareView();updateActiveButton('compare');">Compare</button></div>
          <div class="td"><button id="exportmodebutton" type="button" class="exportmodebutton interactmodebutton Column notyetimplemented" style="color:red"  onclick="showExportView();updateActiveButton('export');">Export</button></div>
        </div>
      </div>
    </div>
    <div id="all-view-page-header-title-text" class="Column">
      <h1 id="page-title">Expense Forecast <span id="page-title-forecast-label">#000000</span></h1>
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
      <div id="all-view-page-header-report-a-bug-panel" class="Column">
        <a href="./report_a_bug.php" style="color:red;">Click here to report a bug</a>
      </div>
    </div>

  </div>

  <div class="leftcolumn">
   <div class="newview" style="display:none">
    <div class="table">
      <fieldset>

       <a class="tablinks" id="RunParameterTab" onclick="openParameterTab(event, 'Save')" class="defaultOpen">Save</a>
       <a class="tablinks" onclick="openParameterTab(event, 'Budget Items')">Budget Items</a>
       <a class="tablinks" onclick="openParameterTab(event, 'Choices')">Choices</a>
       <a class="tablinks" onclick="openParameterTab(event, 'Load')">Load</a><br>
       <a class="tablinks" onclick="openParameterTab(event, 'Accounts')">Accounts</a>
       <a class="tablinks" onclick="openParameterTab(event, 'Memo Rules')">Memo Rules</a>
       <a class="tablinks" onclick="openParameterTab(event, 'MilestoneParameters')">Milestones</a>
       
     </fieldset>
   </div>
   <div id="Save" class="parametertabcontent" style="display:none">
     <form id="stage-forecast-run-form" method="POST" autocomplete="off" action="./php_script/save_forecast_runs.php">
      <fieldset>
        <legend>Save:</legend>
        <label for="forecastlabel">Forecast Label:</label>
        <input type="text" id="forecastlabel" name="forecastlabel"><br>
        <label for="simulationstartdate">Start Date:</label>
        <input type="date" id="simulationstartdate" name="simulationstartdate" required><br>
        <label for="simulationenddate">End Date:</label>
        <input type="date" id="simulationenddate" name="simulationenddate" required><br>

        
        <input type="checkbox" id="stagescenarios" name="stagescenarios">
        <label for="stagescenarios">Save All Scenarios</label><br>
        
        <input type="submit" value="Save Forecast Run">
      </form>
      <form method="POST" autocomplete="off" action="./php_script/clear_cached_forecast.php">
        <input type="submit" value="Clear Cached Forecast">
      </form>
    </fieldset>
  </div>
  <div id="Accounts" class="parametertabcontent" style="display:none">

    <fieldset> 
      <form id='account-form' method="POST" autocomplete="off" action="./php_script/add_account_row_to_temp_table.php">
        <legend>New Account Parameters:</legend>
        <label for="accountname">Name:</label>
        <input type="text" id="accountname" name="accountname" required><br>
        <label for="balance">Balance:</label>
        <input type="text" id="balance" name="balance" required><br>

        <label for="minbalance">Min Balance:</label>
        <input type="text" id="minbalance" name="minbalance" required><br>
        <label for="maxbalance">Max Balance:</label>
        <input type="text" id="maxbalance" name="maxbalance" required><br>

        <label for="accounttype">Account Type:</label><br>
        <input type="radio" id="newaccounttypechecking" name="accounttype" value="Checking">
        <label for="accounttypechecking">Checking</label><br>
        <input type="radio" id="newaccounttypecredit" name="accounttype" value="Credit">
        <label for="accounttypecredit">Credit</label><br>
        <input type="radio" id="newaccounttypeinvestment" name="accounttype" value="Investment">
        <label for="accounttypeinvestment">Investment</label><br>
        <input type="radio" id="newaccounttypeloan" name="accounttype" value="Loan">
        <label for="accounttypeloan">Loan</label><br>


        <fieldset style="display:none" class="Checking accountspecificparametertab">
          <legend>Checking</legend>

          <label for="primary-checking-ind">Is Primary Checking Account:</label>
          <input type="checkbox" id="primary-checking-ind" name="primary-checking-ind">

        </fieldset>


        <fieldset style="display:none" class="Investment accountspecificparametertab" id="investment-account-fieldset">
          <legend>Investment</legend>
          <label for="investmentapr">APR:</label>
          <input type="text" id="investmentapr" name="investmentapr"><br>
          <label for="investmentinterestinterval">Interest interval:</label><br>
          <input type="radio" id="investmentinterestinterval" name="investmentinterestinterval" value="None" class="Investment accountspecificparameter">
          <label for="investmentinterestintervalnone">None</label><br>
          <input type="radio" id="investmentinterestintervaldaily" name="investmentinterestinterval" value="Daily" class="Investment accountspecificparameter">
          <label for="investmentinterestintervaldaily">Daily</label><br>
          <input type="radio" id="investmentaccountinterestintervalmonthly" name="investmentinterestinterval" value="Monthly" class="Investment accountspecificparameter">
          <label for="investmentaccountinterestintervalmonthly">Monthly</label><br>

          <label for="investmentbillingstartdate">Billing Start Date:</label>
          <input type="date" id="investmentbillingstartdate" name="investmentbillingstartdate"><br>

        </fieldset>


        <fieldset style="display:none" class="Credit accountspecificparametertab" id="credit-account-fieldset">
          <legend>Credit</legend>
          <label for="previousstatementbalancecredit">Prev Stmt Balance:</label>
          <input type="text" id="previousstatementbalancecredit" name="previousstatementbalancecredit"><br>
          <label for="creditapr">APR:</label>
          <input type="text" id="creditapr" name="creditapr"><br>
          <label for="creditminpayment">Min Payment:</label>
          <input type="creditminpayment" id="creditminpayment" name="creditminpayment"><br>
          <label for="creditinterestinterval">Interest interval:</label><br>
          <input type="radio" id="creditinterestintervalnone" name="creditinterestinterval" value="None">
          <label for="creditinterestintervalnone">None</label><br>
          <input type="radio" id="creditinterestintervaldaily" name="creditinterestinterval" value="Daily">
          <label for="creditinterestintervaldaily">Daily</label><br>
          <input type="radio" id="creditinterestintervalmonthly" name="creditinterestinterval" value="Monthly">
          <label for="creditinterestintervalmonthly">Monthly</label><br>

          <label for="creditbillingstartdate">Billing Start Date:</label>
          <input type="date" id="creditbillingstartdate" name="creditbillingstartdate"><br>

        </fieldset>
        <br>
        <fieldset style="display:none" class="Loan accountspecificparametertab" id="loan-account-fieldset">
          <legend>Loan</legend>
          <label for="interestbalance">Interest Balance:</label>
          <input type="text" id="interestbalance" name="interestbalance"><br>
          <label for="loanapr">APR:</label>
          <input type="text" id="loanapr" name="loanapr"><br>
          <label for="loanminpayment">Min Payment:</label>
          <input type="loanminpayment" id="loanminpayment" name="loanminpayment"><br>
          <label for="loaninterestinterval">Interest interval:</label><br>
          <input type="radio" id="loaninterestintervalnone" name="loaninterestinterval" value="None">
          <label for="loaninterestintervalnone">None</label><br>
          <input type="radio" id="loaninterestintervaldaily" name="loaninterestinterval" value="Daily">
          <label for="loaninterestintervaldaily">Daily</label><br>
          <input type="radio" id="loaninterestintervalmonthly" name="loaninterestinterval" value="Monthly">
          <label for="loaninterestintervalmonthly">Monthly</label><br>

          <label for="loanbillingstartdate">Billing Start Date:</label>
          <input type="date" id="loanbillingstartdate" name="loanbillingstartdate"><br>

        </fieldset>


        <input type="submit" value="Add New Account">

      </form>
      <form id='clear-accounts-form' method="POST" autocomplete="off" action="./php_script/clear_account_table.php">
        <input type="submit" id="clearaccounttable" name="clearaccounttable" value="Clear Account Table">
      </form>
    </fieldset>
  </div>
  <div id="Budget Items" class="parametertabcontent" style="display:none">
    <fieldset>
      <form id='budget-item-form' method="POST" autocomplete="off" action="./php_script/add_budget_item_row_to_temp_table.php">

        <legend>New Budget Item Parameters:</legend>
        <label for="budgetitemmemo">Memo:</label>
        <input type="text" id="budgetitemmemo" name="budgetitemmemo" required><br>
        <label for="budgetitempriority">Priority:</label>
        <input type="text" id="budgetitempriority" name="budgetitempriority" required><br>

        <label for="budgetitemstartdate">Start Date:</label>
        <input type="date" id="budgetitemstartdate" name="budgetitemstartdate" required><br>
        <label for="nobudgetitemenddate">No End Date?</label>
        <input type="checkbox" id="nobudgetitemenddate" name="nobudgetitemenddate"><br>
        <label for="budgetitemenddate">End Date:</label>
        <input type="date" id="budgetitemenddate" name="budgetitemenddate" required><br>

        <label for="budgetiteminterval">interval:</label><br>
        <input type="radio" id="budgetitemintervalonce" name="budgetiteminterval" value="Once" required>
        <label for="budgetitemintervaldaily">Once</label><br>
        <input type="radio" id="budgetitemintervaldaily" name="budgetiteminterval" value="Daily">
        <label for="budgetitemintervaldaily">Daily</label><br>
        <input type="radio" id="budgetitemintervalweekly" name="budgetiteminterval" value="Weekly">
        <label for="budgetitemintervalweekly">Weekly</label><br>
        <input type="radio" id="budgetitemintervalsemiweekly" name="budgetiteminterval" value="Semi-weekly">
        <label for="budgetitemintervalsemiweekly">Semi-weekly</label><br>
        <input type="radio" id="budgetitemintervalmonthly" name="budgetiteminterval" value="Monthly">
        <label for="budgetitemintervalmonthly">Monthly</label><br>
        <input type="radio" id="budgetitemintervalyearly" name="budgetiteminterval" value="Yearly">
        <label for="budgetitemintervalyearly">Yearly</label><br>
        <label for="budgetitemamount">Amount:</label>
        <input type="text" id="budgetitemamount" name="budgetitemamount" required><br>

        <input type="checkbox" id="budgetitemdeferrableyes" name="budgetitemdeferrableyes" value="Yes">
        <label for="budgetitemdeferrable">Deferrable</label><br>
        <input type="checkbox" id="budgetitempartialpaymentallowedyes" name="budgetitempartialpaymentallowedyes" value="Yes">
        <label for="budgetitemdeferrable">Partial Payment Allowed</label><br>
        <input type="checkbox" id="optionalbudgetitem" name="optionalbudgetitem" value="Yes">
        <label for="optionalbudgetitem">Optional (does not apply to all forecasts)</label><br>
        

        <input type="submit" value="Add New Budget Item">
      </form>
      <form id='clear-budget-items-form' method="POST" action="./php_script/clear_budget_item_set_table.php">
        <input type="submit" id="clearbudgettable" name="clearbudgettable" value="Clear Budget Table">
      </form>
    </fieldset>
    

  </div>
  <div id="Memo Rules" class="parametertabcontent" style="display:none">
    <fieldset>
      <form id='memo-rule-form' method="POST" autocomplete="off" action="./php_script/add_memo_rule_row_to_temp_table.php">

        <legend>New Memo Rule Parameters:</legend>
        <label for="memoregex">Memo Regex:</label>
        <input type="text" id="memoregex" name="memoregex" required><br>
        <label for="accountfrom">Account From:</label>
        <input type="text" id="accountfrom" name="accountfrom" required><br>
        <label for="accountto">Account To:</label>
        <input type="text" id="accountto" name="accountto" required><br>
        <label for="memorulepriority">Priority:</label>
        <input type="text" id="memorulepriority" name="memorulepriority" required><br>
        <input type="submit" value="Add New Memo Rule">

      </form>
      <form id='clear-memo-rule-form' method="POST" action="./php_script/clear_memo_rule_set_table.php">
        <input type="submit" id="clearmemoruletable" name="clearmemoruletable" value="Clear Memo Rule Table">
      </form>
    </fieldset>
    
  </div>

  <div id="MilestoneParameters" class="parametertabcontent" style="display:none">
    <fieldset>

      <legend>New Milestone Parameters:</legend>
      <label for="milestonetype">Milestone Type:</label><br>
      <input type="radio" id="milestonetypeaccount" name="milestonetype" value="Account" required>
      <label for="milestonetypeaccount">Account</label><br>
      <input type="radio" id="milestonetypememo" name="milestonetype" value="Memo">
      <label for="milestonetypememo">Memo</label><br>
      <input type="radio" id="milestonetypecomposite" name="milestonetype" value="Composite">
      <label for="milestonetypecomposite">Composite</label><br><br>



      <fieldset style="display:none" class="Account milestonespecificparametertab">
        <form id='milestone-form' autocomplete="off" method="POST" action="./php_script/add_account_milestone_to_temp_table.php">
          <legend>Account Milestone</legend>
          <label for="accountmilestonename">Milestone Name:</label>
          <input type="text" id="accountmilestonename" name="accountmilestonename"><br>  
          <label for="accountmilestonename">Account Name:</label>
          <input type="text" id="accountmilestoneaccountname" name="accountmilestoneaccountname"><br>  
          <label for="accountmilestoneminbalance">Min Balance:</label>
          <input type="text" id="accountmilestoneminbalance" name="accountmilestoneminbalance"><br>
          <label for="accountmilestonemaxbalance">Max Balance:</label>
          <input type="text" id="accountmilestonemaxbalance" name="accountmilestonemaxbalance"><br>
          <input type="submit" value="Add New Account Milestone">
        </form>
        <form id='clear-account-milestones-form' method="POST"  action="./php_script/clear_account_milestone_table.php">
          <input type="submit" id="clearaccountmilestones" name="clearaccountmilestones" value="Clear Account Milestone Table">
        </form>
      </fieldset>

      <fieldset style="display:none" class="Memo milestonespecificparametertab">
        <form id='milestone-form' autocomplete="off" method="POST" action="./php_script/add_memo_milestone_to_temp_table.php">
          <legend>Memo Milestone</legend>
          <label for="memomilestonename">Milestone Name:</label>
          <input type="text" id="memomilestonename" name="memomilestonename"><br>  
          <label for="memomilestonememoregex">Memo Regex:</label>
          <input type="text" id="memomilestonememoregex" name="memomilestonememoregex"><br>  
          <input type="submit" value="Add New Memo Milestone">
        </form>
        <form id='clear-memo-milestones-form' method="POST" action="./php_script/clear_memo_milestone_table.php">
          <input type="submit" id="clearmemomilestones" name="clearmemomilestones" value="Clear Memo Milestone Table">
        </form>
      </fieldset>

      <fieldset style="display:none" class="Composite milestonespecificparametertab">
        <form id='milestone-form' autocomplete="off" method="POST" action="./php_script/add_composite_milestone_to_temp_table.php">
          <legend>Composite Milestone</legend>
          <label for="compositemilestonename">Milestone Name:</label>
          <input type="text" id="compositemilestonename" name="compositemilestonename"><br>  
          <label for="compositemilestoneaccountmilestoneslist">Account Milestones:</label>
          <input type="text" id="compositemilestoneaccountmilestoneslist" name="compositemilestoneaccountmilestoneslist"><br>
          <label for="compositemilestonememomilestoneslist">Memo Milestones:</label>
          <input type="text" id="compositemilestonememomilestoneslist" name="compositemilestonememomilestoneslist"><br>
          <input type="submit" value="Add New Composite Milestone">
        </form>
        <form id='clear-composite-milestones-form' method="POST" action="./php_script/clear_composite_milestone_table.php">
          <input type="submit" id="clearcompositemilestones" name="clearcompositemilestones" value="Clear Composite Milestone Table">
        </form>
      </fieldset>
    </fieldset>
  </div>

  <div id="Load"  class="parametertabcontent" style="display:none">
    <form id="load-forecast-form" method="POST" autocomplete="off" action="./php_script/load_forecast.php">
      <fieldset>
        <legend>Load Forecast:</legend>
        <p>The forecast ID is a 6 digit number. A list of available forecasts can be found in the list tab. </p>

        <label for="forecastidtoload">Forecast Id:</label>
        <input type="text" id="forecastidtoload" name="forecastidtoload"><br>
        <input type="submit" value="Load Forecast">
      </fieldset>
    </form>
  </div>

  <div id="Choices"  class="parametertabcontent" style="display:none">
    <fieldset>
      <legend>
        Choices:
      </legend>
      This interface can be used to add choices to the base forecast.<br><br>
      <form id='choice-form' autocomplete="off" method="POST" action="./php_script/add_choice_to_temp_table.php">
        <label for="choice-name">Choice Label:</label>
        <input type="text" id="choice-name" name="choice-name"><br><br>
        <div id="option-input-list">
          <label for="option-name-1">Option 1 Label:</label>
          <input type="text" id="option-name-1" name="option-name-1"><br>
          <label for="memo-regexes-1">Memo Regexes:</label>
          <input type="text" id="memo-regexes-1" name="memo-regexes-1"><br>
        </div>
        <button type="button" id="add-option-button">Add Another Option</button><br><br>

        <input type="submit" value="Apply Choice to All Forecasts">
      </form>
      
    </fieldset>
  </div>

</div>

<div class="runview" style="display:none">

  <fieldset>
    <legend>Submit:</legend>
    <form id="submit-forecast-run-form" method="POST" autocomplete="off" action="./php_script/run_forecast.php">
      <label for="forecastlabel">Forecast Label:</label>
      <input type="text" id="forecastlabel" name="forecastlabel"><br>
      <input type="checkbox" id="overwriteforecast" name="overwriteforecast">
      <label for="overwriteforecast">Overwrite</label><br>
      <input type="checkbox" id="approximateforecast" name="approximateforecast">
      <label for="approximateforecast">Approximate</label><br>
      <input type="submit" value="Start">
    </form>
  </fieldset>
</div>

<div class="compareview" style="display:none">

  <fieldset>
    <legend>Compare Forecasts:</legend>
    <form  id="compare-dynamic-account-toggle-list">

      <!-- Forecast Set Id gets appended -->
      <div id="compare-forecast-set-id-list" class="notyetimplemented">Forecast Set Id:</div><br>
      <!-- then a toggle list -->

      <div id="sibling-forecast-id-list">Sibling Forecast Ids:</div><br>
      <!-- then a toggle list -->
      
      <!-- appended dynamically, submit button appended last -->
      <label for="compare-date-range">Date range:</label>
      <input type="text" id="compare-date-range" class="date-range-display" size="30" />
      <div id="compare-viz-slider-range"></div>
    </form>
  </fieldset>
  
</div>


<div class="viewview" style="display:none">
  <fieldset>
    <legend>Filter Forecast Data:</legend>
    <form id="dynamicaccounttogglelist">

      <!-- appended dynamically, submit button appended last -->
      <label for="vizfilterdaterange">Date range:</label>
      <input type="text" id="vizfilterdaterange" class="date-range-display" size="30" />
      <div id="viz-slider-range"></div>
    </form>
  </fieldset>
</div>

<div class="activityview" style="display:none">
  <fieldset>
   <legend>
    Search All Forecasts:
  </legend>
  <form>
    <label for="forecastidfilter" style="color:red">Forecast Name Regex:</label><br>
    <input type="text" name="forecastidfilter">
    <br>
    <label for="amount" style="color:red">Date range:</label>
    <input type="text" id="searchfilterdaterange" class="date-range-display" size="30" />
    <div id="search-slider-range"></div>
    <br>
    <input type="submit" name="submitallforecasttablefilter">
  </form>
</fieldset>
</div>

<div class="exportview" style="display:none">
  <fieldset>
   <legend>
    Export:
  </legend>
  <form>

    <input type="radio" id="exporttype" name="exporttype" value="pdf"><label for="exporttype">PDF</label><br>
    <input type="radio" id="exporttype" name="exporttype" value="excel"><label for="exporttype">excel</label><br>

    <input type="submit" name="submitexport"><br>
    <a href="/images/myw3schoolsimage.jpg" download>Download link</a>
  </form>
</fieldset>
</div>

</div>
<div class="rightcolumn">

  <p style="color:red" id="server-feedback">
  </p>

  <div class="viewview compareview">
    <fieldset style="width:65%">

      <div class="viewview">
     <a class="viewtablinks" id="NetWorthViewTab" onclick="drawExpenseForecastPlot(event, 'Plot Title: Net Worth', 'NetWorth', '<?php echo $forecast_file_path; ?>' )" class="defaultOpen">Net Worth</a>
     <a class="viewtablinks" onclick="drawExpenseForecastPlot(event, 'Plot Title: NetGainLoss', 'NetGainLoss', '<?php echo $forecast_file_path; ?>' )">Net Gain & Loss</a>
     <a class="viewtablinks" onclick="drawExpenseForecastPlot(event, 'Plot Title: AccountType', 'AccountType', '<?php echo $forecast_file_path; ?>' )">Account Type</a>
     <a class="viewtablinks" onclick="drawExpenseForecastPlot(event, 'Plot Title: Interest', 'Interest', '<?php echo $forecast_file_path; ?>' )">Interest</a>
     <a class="viewtablinks notyetimplemented">Milestones</a>
     <a class="viewtablinks" onclick="drawExpenseForecastPlot(event, 'Plot Title: All', 'All', '<?php echo $forecast_file_path; ?>' )">All</a>
     <a class="viewtablinks notyetimplemented">Sankey</a>
   </div>

   <div class="compareview" style="display:none">
     <a class="viewtablinks" id="NetWorthViewTab" onclick="drawCompareExpenseForecastPlot(event, 'Compare Plot Title: Net Worth', 'NetWorth', '<?php echo $forecast_set_file_path; ?>' )" class="defaultOpen">Net Worth</a>
     <a class="viewtablinks" onclick="drawCompareExpenseForecastPlot(event, 'Compare Plot Title: NetGainLoss', 'NetGainLoss', '<?php echo $forecast_set_file_path; ?>' )">Net Gain & Loss</a>
     <a class="viewtablinks" onclick="drawCompareExpenseForecastPlot(event, 'Compare Plot Title: AccountType', 'AccountType', '<?php echo $forecast_set_file_path; ?>' )">Account Type</a>
     <a class="viewtablinks" onclick="drawCompareExpenseForecastPlot(event, 'Compare Plot Title: Interest', 'Interest', '<?php echo $forecast_set_file_path; ?>' )">Interest</a>
     <a class="viewtablinks notyetimplemented">Milestones</a>
     <a class="viewtablinks" onclick="drawCompareExpenseForecastPlot(event, 'Compare Plot Title: All', 'All', '<?php echo $forecast_set_file_path; ?>' )">All</a>
     <a class="viewtablinks notyetimplemented">Sankey</a>
   </div>

   </fieldset>
   <br>
   <div id="svg-plot-parent">
   </div>
 </div>


 <div class="activityview" style="display:none">

  <h2>In Progress</h2>
  Some text.

  <h2>Completed</h2>
  <?php 

  $list_forecasts_query = "select forecast_set_id, forecast_id, forecast_title, forecast_subtitle, error_flag, satisfice_failed_flag, submit_ts, complete_ts from ( select forecast_set_id, forecast_id, forecast_title, forecast_subtitle, error_flag, satisfice_failed_flag, submit_ts, complete_ts, row_number() OVER( PARTITION BY forecast_id ORDER BY submit_ts DESC ) as rn from prod.".$username."_forecast_run_metadata ) where rn = 1 order by submit_ts desc";
  $query_obj = pg_query($dbconn, $list_forecasts_query);
  $query_result = pg_fetch_all($query_obj);


  echo '<table border="1">';
  echo '<thead>';
  echo '<tr style="text-align: right;">';
  echo '<th></th>';
  echo '<th>forecast_set_id</th>';
  echo '<th>forecast_id</th>';
  echo '<th>title</th>';
  echo '<th>subtitle</th>';
  echo '<th>error_flag</th>';
  echo '<th>satisfice_failed_flag</th>';
  echo '<th>submit_ts</th>';
  echo '<th>complete_ts</th>';
  echo '</tr>';
  echo '</thead>';
  echo '<tbody>';
  foreach($query_result as $array)
  {

    echo '<tr>
    <td><span class="list_forecasts_more_details_button" style="font-size:20px;display: inline-block;">&#9654;</span></td>
    <td><span class="forecast_set_id">'. $array['forecast_set_id'].'</span></td>
    <td><span class="forecast_id">'. $array['forecast_id'].'</span></td>
    <td><span class="forecast_title">'. $array['forecast_title'].'</span></td>
    <td><span class="forecast_subtitle">'. $array['forecast_subtitle'].'</span></td>
    <td><span class="error_flag">'. $array['error_flag'].'</span></td>
    <td><span class="satisfice_failed_flag">'. $array['satisfice_failed_flag'].'</span></td>
    <td><span class="submit_ts">'. $array['submit_ts'].'</span></td>
    <td><span class="complete_ts">'. $array['complete_ts'].'</span></td>
    </tr>';

          //forecast details
    $forecast_details_q = "select sd_ed.*, abp.*
    from (
    select src.forecast_id,
    count(distinct acc.account_name) as count_of_accounts,
    count(distinct bdg.memo) as count_of_budget_items,
    max(bdg.priority) as max_priority
    from prod.".$username."_forecast_run_metadata src
    LEFT JOIN prod.ef_account_set_".$username." acc
    ON src.forecast_id = acc.forecast_id
    LEFT JOIN prod.ef_budget_item_set_".$username." bdg
    ON src.forecast_id = bdg.forecast_id
    where src.forecast_id = '".$array['forecast_id']."'
    group by 1
    ) abp
    JOIN (
    select min(\"Date\") as start_date, max(\"Date\") as end_date
    from prod.".$username."_forecast_".$array['forecast_id']."
    ) sd_ed
    ON 1 = 1
    ";
    $details_query_obj = pg_query($dbconn, $forecast_details_q);
    $details_query_result = pg_fetch_all($details_query_obj);

    foreach($details_query_result as $details_array)
    {
      echo '<tr style="display:none" class="more_details_header_row-'.$array['forecast_id'].'">
      <td></td>
      <td></td>
      <th><span class="more_details_start_date_header">Start Date</span></th>
      <th><span class="more_details_end_date_header">End Date</span></th>
      <th><span class="more_details_max_priority_header">Max Priority</span></td>
      <th><span class="more_details_count_of_accounts_header"># of Accounts</span></th>
      <th><span class="more_details_count_of_budget_items_header"># of Budget Items</span></th>

      </tr>';
      echo '<tr style="display:none" class="more_details_first_value_row-'.$array['forecast_id'].'">
      <td></td>
      <td></td>
      <td><span class="more_details_start_date">'. $details_array['start_date'].'</span></td>
      <td><span class="more_details_end_date">'. $details_array['end_date'].'</span></td>
      <td><span class="more_details_end_date">'. $details_array['max_priority'].'</span></td>
      <td><span class="more_details_count_of_accounts">'. $details_array['count_of_accounts'].'</span></td>
      <td><span class="more_details_count_of_budget_items">'. $details_array['count_of_budget_items'].'</span></td>

      </tr>';
    }

            //add a row to create a clear separation from the next values to appear 
    echo '<tr style="display:none" class="more_details_empty_row-'.$array['forecast_id'].'">
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    </tr>';

    echo '<tr style="display:none" class="more_details_empty_row-'.$array['forecast_id'].'">
    <td></td>
    <th>Account Name</th>
    <th>Start Balance</th>
    <th>Final Balance</th>
    <th>Delta</th>
    <th>Milestone Name</th>
    <th>Milestone Date</th>
    </tr>';

            //start and end values
    $start_and_end_q = "select *
    FROM (select *, 
    row_number() OVER(ORDER BY \"Date\" DESC) as desc_rn,
    row_number() OVER(ORDER BY \"Date\" ASC) as asc_rn
    from prod.".$username."_forecast_".$array['forecast_id']."
    ) where desc_rn = 1 or asc_rn = 1
    order by \"Date\" asc
    ";


    //todo this needs a case for when this query returns 0 rows
    $start_and_end_obj = pg_query($dbconn, $start_and_end_q);
    $start_and_end_query_result = pg_fetch_all($start_and_end_obj);
            // e.g. 2 rows: Date, Checking, marginal_interest, net_gain, net_loss, net_worth, loan_total, cc_debt_total, liquid_total, memo, desc_rn, asc_rn

    $start_values_row = $start_and_end_query_result[0];
    $end_values_row = $start_and_end_query_result[1];

            // print_r($start_values_row);
            // echo '<br><br><br>';
            // print_r(array_keys($start_values_row));
            // echo '<br><br><br>';

    $account_names = array();
    $sd_array_keys = array_keys($start_values_row);
    $start_values_relevant_only = array();
    $end_values_relevant_only = array();
    for ( $i = 0 ; $i < count($start_values_row) ; $i++ ){
      $current_column_name = $sd_array_keys[$i];
      if ( $current_column_name != 'Date' 
        && $current_column_name != 'marginal_interest'
        && $current_column_name != 'net_gain'
        && $current_column_name != 'net_loss'
        && $current_column_name != 'desc_rn'
        && $current_column_name != 'asc_rn'
        && $current_column_name != 'memo' ){
        array_push($account_names,$current_column_name);
      array_push($start_values_relevant_only,$start_values_row[$current_column_name]);
      array_push($end_values_relevant_only,$end_values_row[$current_column_name]);
    }
  }

            //milestone results
            // if ( $forecast_id != '' ) {
            //   $milestone_result_q = "select milestone_name, milestone_type, result_date
            //   from prod.virtuoso_user_milestone_results_".$forecast_id."
            //   order by milestone_name";

            // } else {
  $milestone_result_q = "select '' as milestone_name, '' as milestone_type, '' as result_date";
            // }
  
  
  $milestone_result_obj = pg_query($dbconn, $milestone_result_q);
  $milestone_result_query_result = pg_fetch_all($milestone_result_obj);
            // e.g. N rows, milestone_name, result_date

  $nrows_of_sd_end_and_milestones = max(count($start_values_relevant_only),count($milestone_result_query_result));

            //there are 7 columns. We want:
            //Acct Name, Sbal, Fbal, BLANK, BLANK, Milestone_Name, Milestone_Type, Milestone_Date
  for ($i = 0; $i <= $nrows_of_sd_end_and_milestones; $i++) {

              //if there are still account balance values to output
    if ( $i < count($account_names) ){
                $v0 = $account_names[$i]; // acct name
                $v1 = $start_values_relevant_only[$i]; // sbal
                $v2 = $end_values_relevant_only[$i]; // fbal
              } else {
                $v0 = '';
                $v1 = '';
                $v2 = '';
              } 

              $v3 = '';

              //if there are still milestone values to output
              if ( $i < count($milestone_result_query_result) ){
                $v4 = $milestone_result_query_result[$i]['milestone_name']; // Milestone Name
                $v5 = $milestone_result_query_result[$i]['result_date']; // Milestone Date
              } else {
                $v4 = '';
                $v5 = '';
              }

              echo '<tr style="display:none" class="more_details_sd_ed_and_milestone_row-'.$array['forecast_id'].'">
              <td></td>
              <td><span>'.$v0.'</span></td>
              <td><span>'.$v1.'</span></td>
              <td><span>'.$v2.'</span></td>
              <td><span>'.((float)$v2 - (float)$v1).'</span></td>
              <td><span>'.$v4.'</span></td>
              <td><span>'.$v5.'</span></td>
              </tr>';
            }


          }
          echo '</tbody>';
          echo '</table>';
          ?>

        </div>

        <div class="runview" style="display:none">
          <h2><span id="hide-staged-forecast-runs-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Saved Forecast Runs</h2>
          <div id="staged-forecast-runs-table">
            <?php 


            $query_obj = pg_query($dbconn, "Select * from prod.".$username."_forecast_set_definitions");
            $query_result = pg_fetch_all($query_obj);

            echo '<table border="1">';
            echo '<thead>';
            echo '<tr style="text-align: right;">';
            echo '<th></th>';
            echo '<th>forecast_set_id</th>';
            echo '<th>forecast_id</th>';
            echo '<th>forecast_set_name</th>';
            echo '<th>forecast_name</th>';
            echo '<th>start_date</th>';
            echo '<th>end_date</th>';
            echo '</tr>';
            echo '</thead>';
            echo '<tbody>';
            foreach($query_result as $array)
            {
              echo '<tr>
              <td><span class="staged_forecast_row_delete_button" onclick="deleteSavedForecastTableRow(this)">Delete</span>'.'</td>
              <td><span class="forecast_set_id">'. $array['forecast_set_id'].'</span></td>
              <td><span class="forecast_id">'. $array['forecast_id'].'</span></td>
              <td><span class="forecast_set_name">'. $array['forecast_set_name'].'</span></td>
              <td><span class="forecast_name">'. $array['forecast_name'].'</span></td>
              <td><span class="start_date">'. $array['start_date'].'</span></td>
              <td><span class="end_date">'. $array['end_date'].'</span></td>

              </tr>';
            }
            echo '</tbody>';
            echo '</table>';
            ?>
          </div>
        </div>

        <div class="newview" style="display:none">

          <h2><span id="hide-core-bugdget-items-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Core Budget Items</h2>
          <div id="core-bugdget-items-table">
            <?php 

            $query_obj = pg_query($dbconn, "Select * from prod.ef_budget_item_set_".$username."_temporary");
            $query_result = pg_fetch_all($query_obj);

      // if ( $forecast_id != '' ){
      //   $query_obj = pg_query($dbconn, "Select * from prod.ef_budget_item_set_".$username." where forecast_id = '".$forecast_id."'");
      //   $query_result = pg_fetch_all($query_obj);
      // } else {
      //   $query_obj = pg_query($dbconn, "Select * from prod.ef_budget_item_set_".$username."_temporary");
      //   $query_result = pg_fetch_all($query_obj);
      // }

            echo '<table border="1">';
            echo '<thead>';
            echo '<tr style="text-align: right;">';
            echo '<th></th>';
            echo '<th>Start_Date</th>';
            echo '<th>End_Date</th>';
            echo '<th>Priority</th>';
            echo '<th>interval</th>';
            echo '<th>Amount</th>';
            echo '<th>Memo</th>';
            echo '<th>Deferrable</th>';
            echo '<th>Partial_Payment_Allowed</th>';
            echo '</tr>';
            echo '</thead>';
            echo '<tbody>';
            foreach($query_result as $array)
            {
              echo '<tr>
              <td><span class="budget_item_row_delete_button" onclick="deleteBudgetItemTableRow(this)">Delete</span>'.'</td>
              <td class="start_date">'. $array['start_date'].'</td>
              <td class="end_date">'. $array['end_date'].'</td>
              <td class="priority">'. $array['priority'].'</td>
              <td class="interval">'. $array['interval'].'</td>
              <td class="amount">'. $array['amount'].'</td>
              <td class="memo">'. $array['memo'].'</td>
              <td class="deferrable">'. $array['deferrable'].'</td>
              <td class="partial_payment_allowed">'. $array['partial_payment_allowed'].'</td>
              </tr>';
            }
            echo '</tbody>';
            echo '</table>';
            ?>
          </div>

          <h2><span id="hide-optional-bugdget-items-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Optional Budget Items</h2>
          <div id="optional-bugdget-items-table">
            <?php 

            $query_obj = pg_query($dbconn, "Select * from prod.ef_budget_item_set_optional_".$username."_temporary");
            $query_result = pg_fetch_all($query_obj);


            echo '<table border="1">';
            echo '<thead>';
            echo '<tr style="text-align: right;">';
            echo '<th></th>';
            echo '<th>Start_Date</th>';
            echo '<th>End_Date</th>';
            echo '<th>Priority</th>';
            echo '<th>interval</th>';
            echo '<th>Amount</th>';
            echo '<th>Memo</th>';
            echo '<th>Deferrable</th>';
            echo '<th>Partial_Payment_Allowed</th>';
            echo '</tr>';
            echo '</thead>';
            echo '<tbody>';
            foreach($query_result as $array)
            {
              echo '<tr>
              <td><span class="optional_budget_item_row_delete_button" style="color:red;" onclick="deleteOptionalBudgetItemTableRow(this)">Delete</span>'.'</td>
              <td class="start_date">'. $array['start_date'].'</td>
              <td class="end_date">'. $array['end_date'].'</td>
              <td class="priority">'. $array['priority'].'</td>
              <td class="interval">'. $array['interval'].'</td>
              <td class="amount">'. $array['amount'].'</td>
              <td class="memo">'. $array['memo'].'</td>
              <td class="deferrable">'. $array['deferrable'].'</td>
              <td class="partial_payment_allowed">'. $array['partial_payment_allowed'].'</td>
              </tr>';
            }
            echo '</tbody>';
            echo '</table>';
            ?>
          </div>

          <h2><span id="hide-choices-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Choices</h2>
          <div id="choices-table">
            <?php
            $query_obj = pg_query($dbconn, "Select * from prod.ef_choices_".$username."_temporary");
            $query_result = pg_fetch_all($query_obj);

            echo '<table border="1">';
            echo '<thead>';
            echo '<tr style="text-align: right;">';
            echo '<th></th>';
            echo '<th>Choice_Name</th>';
            echo '<th>Option_Name</th>';
            echo '<th>Memo_Regexes</th>';
            echo '</tr>';
            echo '</thead>';
            echo '<tbody>';
            foreach($query_result as $array)
            {
              echo '<tr>
              <td><span class="choice_row_delete_button" onclick="deleteChoicesTableRow(this)" style="color:red">Delete</span>'.'</td>
              <td class="choice_name">'. $array['choice_name'].'</td>
              <td class="option_name">'. $array['option_name'].'</td>
              <td class="option_memo_regexes">'. $array['memo_regexes'].'</td>
              </tr>';
            }
            echo '</tbody>';
            echo '</table>';
            ?>
          </div>

          <h2><span id="hide-accounts-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Accounts</h2>
          <div id="accounts-table">
           <?php 

      // if ( $forecast_id != '' ){
      //   $query_obj = pg_query($dbconn, "Select * from prod.ef_account_set_".$username." where forecast_id = '".$forecast_id."'");
      //   $query_result = pg_fetch_all($query_obj);
      // } else {
           $query_obj = pg_query($dbconn, "Select * from prod.ef_account_set_".$username."_temporary");
           $query_result = pg_fetch_all($query_obj);
      // }

           echo '<table border="1">';
           echo '<thead>';
           echo '<tr style="text-align: right;">';
           echo '<th></th>';
           echo '<th>Name</th>';
           echo '<th>Balance</th>';
           echo '<th>Min_Balance</th>';
           echo '<th>Max_Balance</th>';
           echo '<th>Account_Type</th>';
           echo '<th>Billing_Start_Date</th>';
           echo '<th>APR</th>';
           echo '<th>Interest_interval</th>';
           echo '<th>Minimum_Payment</th>';
           echo '<th>Primary_Checking_Ind</th>';
           echo '</tr>';
           echo '</thead>';
           echo '<tbody>';
           foreach($query_result as $array)
           {
            echo '<tr>
            <td><span class="account_row_delete_button" onclick="deleteAccountTableRow(this)">Delete</span>'.'</td>
            <td><span class="account_name">'. $array['account_name'].'</span></td>
            <td><span class="balance">'. $array['balance'].'</span></td>
            <td><span class="min_balance">'. $array['min_balance'].'</span></td>
            <td><span class="max_balance">'. $array['max_balance'].'</span></td>
            <td><span class="account_type">'. $array['account_type'].'</span></td>
            <td><span class="billing_start_date_yyyymmdd">'. $array['billing_start_date_yyyymmdd'].'</span></td>
            <td><span class="apr">'. $array['apr'].'</span></td>
            <td><span class="interest_interval">'. $array['interest_interval'].'</span></td>
            <td><span class="minimum_payment">'. $array['minimum_payment'].'</span></td>
            <td><span class="primary_checking_ind">'. $array['primary_checking_ind'].'</span></td>

            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-memo-rules-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Memo Rules</h2>
        <div id="memo-rules-table">
          <?php 

      // if ( $forecast_id != '' ){
      //   $query_obj = pg_query($dbconn, "Select * from prod.ef_memo_rule_set_".$username." where forecast_id = '".$forecast_id."'");
      //   $query_result = pg_fetch_all($query_obj);
      // } else {
          $query_obj = pg_query($dbconn, "Select * from prod.ef_memo_rule_set_".$username."_temporary");
          $query_result = pg_fetch_all($query_obj);
      // }

          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th></th>';
          echo '<th>Memo_Regex</th>';
          echo '<th>Priority</th>';
          echo '<th>Account_From</th>';
          echo '<th>Account_To</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td><span class="memo_rule_row_delete_button" onclick="deleteMemoRuleTableRow(this)">Delete</span>'.'</td>
            <td class="memo_regex">'. $array['memo_regex'].'</td>
            <td class="priority">'. $array['priority'].'</td>
            <td class="account_from">'. $array['account_from'].'</td>
            <td class="account_to">'. $array['account_to'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-account-milestones-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Account Milestones</h2>
        <div id="account-milestones-table">
          <?php 

      // if ( $forecast_id != '' ){
      //   $query_obj = pg_query($dbconn, "Select * from prod.ef_account_milestones_".$username." where forecast_id = '".$forecast_id."'");
      //   $query_result = pg_fetch_all($query_obj);
      // } else {
          $query_obj = pg_query($dbconn, "Select * from prod.ef_account_milestones_".$username."_temporary");
          $query_result = pg_fetch_all($query_obj);
      // }

          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th></th>';
          echo '<th>Milestone_Name</th>';
          echo '<th>Account_Name</th>';
          echo '<th>Min_Balance</th>';
          echo '<th>Max_Balance</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td><span class="account_milestone_row_delete_button" onclick="deleteAccountMilestoneTableRow(this)">Delete</span>'.'</td>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            <td class="account_name">'. $array['account_name'].'</td>
            <td class="min_balance">'. $array['min_balance'].'</td>
            <td class="max_balance">'. $array['max_balance'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-memo-milestones-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Memo Milestones</h2>
        <div id="memo-milestones-table">
          <?php 

      // if ( $forecast_id != '' ){
      //   $query_obj = pg_query($dbconn, "Select * from prod.ef_memo_milestones_".$username." where forecast_id = '".$forecast_id."'");
      //   $query_result = pg_fetch_all($query_obj);
      // } else {
          $query_obj = pg_query($dbconn, "Select * from prod.ef_memo_milestones_".$username."_temporary");
          $query_result = pg_fetch_all($query_obj);
      // }

          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th></th>';
          echo '<th>Milestone_Name</th>';
          echo '<th>Memo_Regex</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td><span class="memo_milestone_row_delete_button" onclick="deleteMemoMilestoneTableRow(this)">Delete</span>'.'</td>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            <td class="memo_regex">'. $array['memo_regex'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-composite-milestones-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Composite Milestones</h2>
        <div id="composite-milestones-table">
          <?php 

      // if ( $forecast_id != '' ){
      //   $query_obj = pg_query($dbconn, "Select * from prod.ef_composite_milestones_".$username." where forecast_id = '".$forecast_id."'");
      //   $query_result = pg_fetch_all($query_obj);
      // } else {
          $query_obj = pg_query($dbconn, "Select * from prod.ef_composite_milestones_".$username."_temporary");
          $query_result = pg_fetch_all($query_obj);
      // }

          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th></th>';
          echo '<th>Composite_Milestone_Name</th>';
          echo '<th>Account_Milestone_Name_List</th>';
          echo '<th>Memo_Milestone_Name_List</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td><span class="composite_milestone_row_delete_button" onclick="deleteCompositeMilestoneTableRow(this)">Delete</span>'.'</td>
            <td class="composite_milestone_name">'. $array['composite_milestone_name'].'</td>
            <td class="milestone_type">'. $array['account_milestone_name_list'].'</td>
            <td class="milestone_name">'. $array['memo_milestone_name_list'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>
      </div>

      <div class="viewview compareview" style="display:none">

        <h2><span id="hide-account-milestone-results-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Account Milestone Results</h2>
        <div id="account-milestone-results-table">
          <?php

          if ( $forecast_id != '' ){
        // $query_obj = pg_query($dbconn, "Select * from prod.".$username."_milestone_results_".$forecast_id." where milestone_type = 'Account'");
            $query_obj = pg_query($dbconn, "Select '' as milestone_name, '' as result_date");
            $query_result = pg_fetch_all($query_obj);
          }
      // there are no results if forecast has not been run

          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th>Milestone_Name</th>';
          echo '<th>Date</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            <td class="date">'. $array['result_date'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-memo-milestone-results-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Memo Milestone Results</h2>
        <div id="hide-memo-milestone-results-table-button">
          <?php

          if ( $forecast_id != '' ){
        //$query_obj = pg_query($dbconn, "Select * from prod.".$username."_milestone_results_".$forecast_id." where milestone_type = 'Memo'");
            $query_obj = pg_query($dbconn, "Select '' as milestone_name, '' as result_date");
            $query_result = pg_fetch_all($query_obj);
          }
      // there are no results if forecast has not been run

          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th>Milestone_Name</th>';
          echo '<th>Date</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            <td class="date">'. $array['result_date'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-composite-milestone-results-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Composite Milestone Results</h2>
        <div id="hide-composite-milestone-results-table-button">
          <?php

          if ( $forecast_id != '' ){
        //$query_obj = pg_query($dbconn, "Select * from prod.".$username."_milestone_results_".$forecast_id." where milestone_type = 'Composite'");
            $query_obj = pg_query($dbconn, "Select '' as milestone_name, '' as result_date");
            $query_result = pg_fetch_all($query_obj);
          }
      // there are no results if forecast has not been run

          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th>Milestone_Name</th>';
          echo '<th>Date</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            <td class="date">'. $array['result_date'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-cc-and-loan-payments-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Credit Card & Loan Payments</h2>
        <div id="cc-and-loan-payments-table">
          <?php
          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th></th>';
          echo '<th>Composite_Milestone_Name</th>';
          echo '<th>Milestone_Type</th>';
          echo '<th>Milestone_Name</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td class="composite_milestone_name">'. $array['composite_milestone_name'].'</td>
            <td class="milestone_type">'. $array['milestone_type'].'</td>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-aggregated-transactions-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Aggregated Transaction Schedule</h2>
        <div id="aggregated-transactions-table">
          <?php
          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th>Composite_Milestone_Name</th>';
          echo '<th>Milestone_Type</th>';
          echo '<th>Milestone_Name</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td class="composite_milestone_name">'. $array['composite_milestone_name'].'</td>
            <td class="milestone_type">'. $array['milestone_type'].'</td>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>

        <h2><span id="hide-forecast-data-table-button" class="hide_table_button" style="font-size:20px;display: inline-block;">&#9654;</span>Forecast Data</h2>
        <div id="forecast-data-table">
          <?php
          echo '<table border="1">';
          echo '<thead>';
          echo '<tr style="text-align: right;">';
          echo '<th>Composite_Milestone_Name</th>';
          echo '<th>Milestone_Type</th>';
          echo '<th>Milestone_Name</th>';
          echo '</tr>';
          echo '</thead>';
          echo '<tbody>';
          foreach($query_result as $array)
          {
            echo '<tr>
            <td class="composite_milestone_name">'. $array['composite_milestone_name'].'</td>
            <td class="milestone_type">'. $array['milestone_type'].'</td>
            <td class="milestone_name">'. $array['milestone_name'].'</td>
            </tr>';
          }
          echo '</tbody>';
          echo '</table>';
          ?>
        </div>
      </div>
<!-- 
</div>

</div> -->

</body>
<script>
  d3.csv( '<?php echo '../data/Forecast_'.$forecast_id.'.csv'; ?>', function(error, data) {
/* d3.csv( , function(error, data) { */
    if (error) throw error;

//todo min and max
    min_date = d3.min(data, function(d){
      return new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00')
    });

    max_date = d3.max(data, function(d){
      return new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00')
    });


    const date_format_options = {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric'
    };
    const dateTimeFormat = new Intl.DateTimeFormat('en', date_format_options);

//new Intl.DateTimeFormat('en-US', options1)

    //todo set date filter default value on page load
    document.getElementById("vizfilterdaterange").value = dateTimeFormat.format(min_date)+" - "+dateTimeFormat.format(max_date);
    document.getElementById("compare-date-range").value = dateTimeFormat.format(min_date)+" - "+dateTimeFormat.format(max_date);
    

    $(function () {

      $("#viz-slider-range").slider({
        range: true,
        min: new Date(min_date).getTime() / 1000,
        max: new Date(max_date).getTime() / 1000,
        step: 86400,
        values: [new Date(min_date).getTime() / 1000, new Date(max_date).getTime() / 1000],
        slide: function (event, ui) {
          $("#vizfilterdaterange").val((  dateTimeFormat.format(new Date(ui.values[0] * 1000))  ) + " - " + dateTimeFormat.format(new Date(ui.values[1] * 1000)) ) ;
        }
      });
      drawExpenseForecastPlot(event, 'Plot Title: Net Worth', 'NetWorth', '<?php echo '../data/Forecast_'.$forecast_id.'.csv'; ?>' );

      $("#compare-viz-slider-range").slider({
        range: true,
        min: new Date(min_date).getTime() / 1000,
        max: new Date(max_date).getTime() / 1000,
        step: 86400,
        values: [new Date(min_date).getTime() / 1000, new Date(max_date).getTime() / 1000],
        slide: function (event, ui) {
          $("#compare-date-range").val((  dateTimeFormat.format(new Date(ui.values[0] * 1000))  ) + " - " + dateTimeFormat.format(new Date(ui.values[1] * 1000)) ) ;
        }
      });
      // $("#search-slider-range").slider({
      //   range: true,
      //   min: new Date(min_date).getTime() / 1000,
      //   max: new Date(max_date).getTime() / 1000,
      //   step: 86400,
      //   values: [new Date(min_date).getTime() / 1000, new Date(max_date).getTime() / 1000],
      //   slide: function (event, ui) {
      //     $("#searchfilterdaterange").val((  dateTimeFormat.format(new Date(ui.values[0] * 1000))  ) + " - " + dateTimeFormat.format(new Date(ui.values[1] * 1000)) ) ;
      //   }
      // });

      $("#vizfilterdaterange").val( dateTimeFormat.format( new Date($("#viz-slider-range").slider("values", 0) * 1000) ) +
        " - " + dateTimeFormat.format(new Date($("#viz-slider-range").slider("values", 1) * 1000))  );

      $("#searchfilterdaterange").val( dateTimeFormat.format( new Date($("#viz-slider-range").slider("values", 0) * 1000) ) +
        " - " + dateTimeFormat.format(new Date($("#viz-slider-range").slider("values", 1) * 1000))  );

    });

  } )
</script>
<script type="text/javascript">
  //preserves open tab on refresh
  if (localStorage.getItem('displaymode') == 'new') {
    showNewView();
  } else if (localStorage.getItem('displaymode') == 'run') {
    showRunView();
  } else if (localStorage.getItem('displaymode') == 'view') {
    showViewView();
  } else if (localStorage.getItem('displaymode') == 'compare') {
    showCompareView();
  } else if (localStorage.getItem('displaymode') == 'activity') {
    showActivityView();
  } else if (localStorage.getItem('displaymode') == 'export') {
    showExportView();
  }

  updateActiveButton(localStorage.getItem('displaymode'));
</script>
<script>
  $('#logout_button').submit(function() {
    console.log('Setting username to null. This no longer works. login_token must be deleted from DB.');
    localStorage.setItem('username','null');
  });
</script>
<script>
  lod = document.getElementById("logged-out-login-details");
  lid = document.getElementById("logged-in-login-details");
  welcome_message = document.getElementById("login-details-welcome-message");
  
  //if viewing this page not logged in becomes supported, so logic to handle login panel display would be added here
  lod.style.display = 'none';
  welcome_message.innerHTML += '<b><?php echo $username ?></b>.';


  //this does not suffice because they stay in the same vertical positon even when not showing
  //lod.style.display = "none";
  //lid.style.display = "none";
</script>
<script>
  page_title_forecast_label = document.getElementById("page-title-forecast-label");
  page_title_forecast_label.innerHTML = '#'+forecast_id;
</script>
<script type="text/javascript">
  $(document).ready(function () {

    $('input[type="radio"]').
    click(
      function () {
        const inputValue = $(this).attr("value");
        const targetBox = ("." + inputValue);

        if ( ['Checking','Credit','Investment','Loan'].includes(inputValue) ) {
          $(".accountspecificparametertab").not(targetBox).hide();
          $(targetBox).show();
        }

        if ( ['Account','Memo','Composite'].includes(inputValue) ) {
          $(".milestonespecificparametertab").not(targetBox).hide();
          $(targetBox).show();
        }
      }
      );
  }); 
</script>
<script>
  $(document).ready(function() {
    $('input[type=radio][name=accounttype]').change(function() {
      if($(this).val() == 'Credit') {
        $("#previousstatementbalancecredit").attr('required', '');
        $("#creditapr").attr('required', '');
        $("#creditminpayment").attr('required', '');
        $("#creditinterestinterval").attr('required', '');
        $("#creditbillingstartdate").attr('required', '');
        $("#creditinterestintervalmonthly").attr('required', '');


        $("#interestbalance").removeAttr('required', '');
        $("#loanapr").removeAttr('required', '');
        $("#loanminpayment").removeAttr('required', '');
        $("#loaninterestinterval").removeAttr('required', '');
        $("#loanbillingstartdate").removeAttr('required', '');

        $("#investmentapr").removeAttr('required', '');
        $("#investmentinterestinterval").removeAttr('required', '');
        $("#investmentbillingstartdate").removeAttr('required', '');
      }
      else if($(this).val() == 'Loan') {

        $("#interestbalance").attr('required', '');
        $("#loanapr").attr('required', '');
        $("#loanminpayment").attr('required', '');
        $("#loaninterestinterval").attr('required', '');
        $("#loanbillingstartdate").attr('required', '');

        $("#previousstatementbalancecredit").removeAttr('required', '');
        $("#creditapr").removeAttr('required', '');
        $("#creditminpayment").removeAttr('required', '');
        $("#creditinterestinterval").removeAttr('required', '');
        $("#creditbillingstartdate").removeAttr('required', '');

        $("#investmentapr").removeAttr('required', '');
        $("#investmentinterestinterval").removeAttr('required', '');
        $("#investmentbillingstartdate").removeAttr('required', '');

        $("#creditinterestintervalmonthly").removeAttr('required', '');
      }       
      else if($(this).val() == 'Investment') {

        $("#investmentapr").attr('required', '');
        $("#investmentinterestinterval").attr('required', '');
        $("#investmentbillingstartdate").attr('required', '');

        $("#previousstatementbalancecredit").removeAttr('required', '');
        $("#creditapr").removeAttr('required', '');
        $("#creditminpayment").removeAttr('required', '');
        $("#creditinterestinterval").removeAttr('required', '');
        $("#creditbillingstartdate").removeAttr('required', '');

        $("#interestbalance").removeAttr('required', '');
        $("#loanapr").removeAttr('required', '');
        $("#loanminpayment").removeAttr('required', '');
        $("#loaninterestinterval").removeAttr('required', '');
        $("#loanbillingstartdate").removeAttr('required', '');

        $("#creditinterestintervalmonthly").removeAttr('required', '');

      } 

    });
  });
</script>
<script>


  <?php 
  echo "d3.select(\"#compare-forecast-set-id-list\")"."\r\n";
    echo ".append('br');"."\r\n";

  foreach ( $parent_forecast_set_ids as $forecast_set_id  ) {

    echo "d3.select(\"#compare-forecast-set-id-list\")"."\r\n";
    echo "  .append(\"input\")"."\r\n";
    echo "  .attr(\"type\",\"radio\")"."\r\n";
    echo "  .attr(\"id\",\"forecast_set_radio_button_".$forecast_set_id."\")"."\r\n";
    echo "  .attr(\"value\",\"".$forecast_set_id."\")"."\r\n";
    echo "  .attr(\"name\",\"forecast-set-radio-filter\")"."\r\n";
    //echo "  .attr(\"name\",\"".$forecast_set_id."\")"."\r\n";
    echo "  .attr(\"checked\",\"false\");"."\r\n";

    echo "d3.select(\"#compare-forecast-set-id-list\")"."\r\n";
    echo "  .append(\"label\")"."\r\n";
    echo "  .attr(\"for\",\"forecast_set_radio_button_".$forecast_set_id."\")"."\r\n";
    echo "  .text(\"".$forecast_set_id."\");";

    echo "d3.select(\"#compare-forecast-set-id-list\")"."\r\n";
    echo ".append('br');"."\r\n";

  }

  echo "d3.select(\"#sibling-forecast-id-list\")"."\r\n";
    echo ".append('br');"."\r\n";

    foreach ( $sibling_forecast_ids as $sibling_forecast_id  ) {

    echo "d3.select(\"#sibling-forecast-id-list\")"."\r\n";
    echo "  .append(\"input\")"."\r\n";
    echo "  .attr(\"type\",\"checkbox\")"."\r\n";
    echo "  .attr(\"id\",\"sibling_forecast_checkbox_".$sibling_forecast_id."\")"."\r\n";
    echo "  .attr(\"value\",\"".$sibling_forecast_id."\")"."\r\n";
    echo "  .attr(\"name\",\"sibling-forecast-radio-filter\")"."\r\n";
    //echo "  .attr(\"name\",\"".$sibling_forecast_id."\")"."\r\n";
    echo "  .attr(\"checked\",\"true\");"."\r\n";

    echo "d3.select(\"#sibling-forecast-id-list\")"."\r\n";
    echo "  .append(\"label\")"."\r\n";
    echo "  .attr(\"for\",\"sibling_forecast_checkbox_".$sibling_forecast_id."\")"."\r\n";
    echo "  .text(\"".$sibling_forecast_id."\");";

    echo "d3.select(\"#sibling-forecast-id-list\")"."\r\n";
    echo ".append('br');"."\r\n";

  }

   ?> 

  //this needs to be a forecast_set_def_file
  //also, forecast_set_id needs to be defined
  // d3.csv( '<?php echo '../data/Forecast_'.$forecast_id.'.csv'; ?>', function(error, data) {

  // });

  //create toggle checkboxes based on data
  d3.csv( '<?php echo '../data/Forecast_'.$forecast_id.'.csv'; ?>', function(error, data) {
    if (error) throw error;

      // console.log(data);


//<label for="amount">Date range:</label>
//<input type="text" id="amount" class="date-range-display" size="30" />
//<div id="slider-range"></div>

    d3.select("#dynamicaccounttogglelist")
    .append('br');

    d3.select("#compare-dynamic-account-toggle-list")
    .append('br');

    for ( column_index = 1 ; column_index < (data.columns.length - 1) ; column_index++ ){

        //select id dynamicaccounttogglelist
      d3.select("#dynamicaccounttogglelist")
      .append("input")
      .attr("type","checkbox")
      .attr("id","account_toggle_"+data.columns[column_index])
      .attr("name","account_toggle_checkbox_list")
      .attr("value",data.columns[column_index])
      .attr("checked","true");

      d3.select("#compare-dynamic-account-toggle-list")
      .append("input")
      .attr("type","checkbox")
      .attr("id","compare_account_toggle_"+data.columns[column_index])
      .attr("name","compare_account_toggle_checkbox_list")
      //.attr("name",data.columns[column_index])
      .attr("value",data.columns[column_index])
      .attr("checked","true");

      d3.select("#dynamicaccounttogglelist")
      .append("label")
      .attr("for",data.columns[column_index])
      .text(data.columns[column_index]);

      d3.select("#compare-dynamic-account-toggle-list")
      .append("label")
      .attr("for",data.columns[column_index])
      .text(data.columns[column_index]);

      d3.select("#dynamicaccounttogglelist")
      .append('br');

      d3.select("#compare-dynamic-account-toggle-list")
      .append('br');

    }

    d3.select("#dynamicaccounttogglelist")
    .append('input')
    .attr("type","submit")
    .attr("value","Submit");

    d3.select("#compare-dynamic-account-toggle-list")
    .append('input')
    .attr("type","submit")
    .attr("value","Submit");

  });

  document.getElementById("dynamicaccounttogglelist").addEventListener("submit", function (e) {
    e.preventDefault();

    drawExpenseForecastPlot('','Plot Title: All','All', '<?php echo '../data/Forecast_'.$forecast_id.'.csv'; ?>' );

  });


document.getElementById("compare-dynamic-account-toggle-list").addEventListener("submit", function (e) {
    e.preventDefault();

    drawCompareExpenseForecastPlot('','Plot Title: All','All', '<?php echo $forecast_set_file_path; ?>' );

  });

  



</script>
<script>
// var elements = document.getElementsByClassName('row_delete_button');
// console.log(elements);
//  for(var i=0;i<elements.length;i++){
//       elements[i].addEventListener("click", function(){console.log(getRowContents())}, false);   
//  }
</script>
<script>
 login_feedback = document.getElementById("server-feedback");
 login_feedback.innerHTML += latest_server_feedback;
   //login_feedback.innerHTML += getCookie('latest_server_feedback');
   //console.log(decodeURIComponent(document.cookie));
   //console.log(login_feedback);
   //document.cookie = "latest_server_feedback=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
</script>
<script>

// <label for="choice-name">Choice Label:</label>
// <input type="text" id="choice-name" name="choice-name"><br>
// <label for="memo-regexes">Memo Regexes:</label>
// <input type="text" id="memo-regexes-1" name="memo-regexes-1"><br>

  //addChoiceFieldToScenarioPanel
  option_input_list = document.getElementById("option-input-list");
  add_option_button = document.getElementById("add-option-button");
  add_option_button.addEventListener("click", function() {

    // if ( choice_input_list.children.length == 6 ){
    //   var index_of_next_ordinal = choice_input_list.children.length-5;
    // } else {
    //   var index_of_next_ordinal = choice_input_list.children.length-6;
    // }
    var index_of_next_ordinal = option_input_list.children.length-5;
    var count_of_choices = option_input_list.children[index_of_next_ordinal].id.split('-')[2];

    //console.log(choice_input_list.children)
    //first: 1     6     
    //second: 7    13    7
    //third: 14    20    7
    //fourth: 21   27    7

    new_choice_name_input_label = document.createElement("label");
    new_choice_name_input_fields = document.createElement("input");
    new_choice_memo_regexes_input_label = document.createElement("label");
    new_choice_memo_regexes_input_fields = document.createElement("input");

    //for, id, name

    new_choice_name_input_label.innerHTML = "Choice "+(parseInt(count_of_choices)+1)+" label:"
    new_choice_name_input_fields.id = "option-name-"+(parseInt(count_of_choices)+1)
    new_choice_name_input_fields.name = "option-name-"+(parseInt(count_of_choices)+1)

    new_choice_memo_regexes_input_label.innerHTML = "Memo Regexes:"
    new_choice_memo_regexes_input_fields.id = "memo-regexes-"+(parseInt(count_of_choices)+1)
    new_choice_memo_regexes_input_fields.name = "memo-regexes-"+(parseInt(count_of_choices)+1)
    
    option_input_list.append(document.createElement("br"));
    option_input_list.append(new_choice_name_input_label);
    option_input_list.append(new_choice_name_input_fields);
    option_input_list.append(document.createElement("br"));
    option_input_list.append(new_choice_memo_regexes_input_label);
    option_input_list.append(new_choice_memo_regexes_input_fields);
    option_input_list.append(document.createElement("br"));
  })

  hide_table_buttons = document.getElementsByClassName("hide_table_button");
  for (i = 0; i < hide_table_buttons.length; i++) {
    hide_table_buttons[i].addEventListener("click", function() {
      relevant_div = document.getElementById(this.id.replace("hide-","").replace("-button",""));

      if ( relevant_div.style.display == "" ){
        relevant_div.style.display = "none";
        this.style.transform = "rotate(0deg)";
      } else if ( relevant_div.style.display == "none" ){
        relevant_div.style.display = "";
        this.style.transform = "rotate(90deg)";
      }


      
    })
  }

  list_forecasts_more_details_buttons = document.getElementsByClassName("list_forecasts_more_details_button");
  for (i = 0; i < list_forecasts_more_details_buttons.length; i++) {
    list_forecasts_more_details_buttons[i].addEventListener("click", function() {

      selected_forecast_id = this.parentNode.parentNode.children[2].children[0].innerHTML;
      header_class_name = "more_details_header_row-"+selected_forecast_id;
      first_values_class_name = "more_details_first_value_row-"+selected_forecast_id;
      empty_rows_class_name = "more_details_empty_row-"+selected_forecast_id;
      sd_ed_and_milestone_class_name = "more_details_sd_ed_and_milestone_row-"+selected_forecast_id;

      header_rows = document.getElementsByClassName(header_class_name);
      firsts_value_rows = document.getElementsByClassName(first_values_class_name);
      empty_rows = document.getElementsByClassName(empty_rows_class_name);
      sd_ed_and_milestone_rows = document.getElementsByClassName(sd_ed_and_milestone_class_name);

      if (this.style.transform == "rotate(90deg)"){
        // hide forecast details
        this.style.transform = "rotate(0deg)";

        for (h_i = 0; h_i < header_rows.length; h_i++) {
          header_rows[h_i].style.display="none";
        }

        for (f_i = 0; f_i < firsts_value_rows.length; f_i++) {
          firsts_value_rows[f_i].style.display="none";
        }

        for (e_i = 0; e_i < empty_rows.length; e_i++) {
          empty_rows[e_i].style.display="none";
        }

        for (m_i = 0; m_i < sd_ed_and_milestone_rows.length; m_i++) {
          sd_ed_and_milestone_rows[m_i].style.display="none";
        }

      } else if ( (this.style.transform == "rotate(0deg)") || (this.style.transform == "") ) {
        //show forecast details
        this.style.transform = "rotate(90deg)";

        for (h_i = 0; h_i < header_rows.length; h_i++) {
          header_rows[h_i].style.display="";
        }

        for (f_i = 0; f_i < firsts_value_rows.length; f_i++) {
          firsts_value_rows[f_i].style.display="";
        }

        for (e_i = 0; e_i < empty_rows.length; e_i++) {
          empty_rows[e_i].style.display="";
        }

        for (m_i = 0; m_i < sd_ed_and_milestone_rows.length; m_i++) {
          sd_ed_and_milestone_rows[m_i].style.display="";
        }
      }
    });
  }


</script>
<script>
  //so that mobile actually uses localStorage
  window.addEventListener('unload', () => {
     saveToLocalStorage(store.getState());
});
</script>

</html>

<?php
  //populate data tables
?>