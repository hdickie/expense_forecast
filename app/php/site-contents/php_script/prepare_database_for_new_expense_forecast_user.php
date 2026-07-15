<?php
require_once __DIR__ . '/config.php';
//relevant env: dbconn, $_POST["username"]

//
$superuser_dbconn = ef_pg_connect(true);

$create_user_query = "CREATE USER ".$_POST["username"]." WITH PASSWORD '".$_POST["new_password"]."';";
pg_query($superuser_dbconn,$create_user_query);

$dbconn = ef_pg_connect();

$create_single_user_account_set_table_query = "
create table prod.ef_account_set_".$_POST["username"]." (
	forecast_id text,
	account_name text,
	balance float,
	min_balance float,
	max_balance float,
	account_type text,
	billing_start_date_yyyymmdd date,
	apr float,
	interest_interval text,
	minimum_payment float,
	primary_checking_ind bool
)";

$create_single_user_budget_item_table_query = "
create table prod.ef_budget_item_set_".$_POST["username"]." (
	forecast_id text,
	memo text,
	priority int,
	start_date date,
	end_date date,
	interval text,
	amount float,
	\"deferrable\" bool,
	partial_payment_allowed bool
)";

$create_single_user_optional_budget_item_table_query = "
create table prod.ef_optional_budget_item_set_".$_POST["username"]." (
	forecast_id text,
	memo text,
	priority int,
	start_date date,
	end_date date,
	interval text,
	amount float,
	\"deferrable\" bool,
	partial_payment_allowed bool
)";


$create_single_user_memo_rule_set_table_query = "
create table prod.ef_memo_rule_set_".$_POST["username"]." (
	forecast_id text,
	memo_regex text,
	account_from text,
	account_to text,
	priority int
)";

$create_single_user_account_milestone_table_query = "
create table prod.ef_account_milestones_".$_POST["username"]." (
	forecast_id text,
	milestone_name text,
	account_name text,
	min_balance float,
	max_balance float
)";

$create_single_user_memo_milestone_table_query = "
create table prod.ef_memo_milestones_".$_POST["username"]." (
	forecast_id text,
	milestone_name text,
	memo_regex text
)";

$create_single_user_composite_milestone_table_query = "
create table prod.ef_composite_milestones_".$_POST["username"]." (
	forecast_id text,
	composite_milestone_name text,
	account_milestone_name_list text,
	memo_milestone_name_list text
)
";

$create_single_user_account_set_temporary_table_query = "
create table prod.ef_account_set_".$_POST["username"]."_temporary (
	account_name text,
	balance float,
	min_balance float,
	max_balance float,
	account_type text,
	billing_start_date_yyyymmdd date,
	apr float,
	interest_interval text,
	minimum_payment float,
	primary_checking_ind bool
)";

$create_single_user_budget_item_temporary_table_query = "
create table prod.ef_budget_item_set_".$_POST["username"]."_temporary (
	memo text,
	priority int,
	start_date date,
	end_date date,
	interval text,
	amount float,
	\"deferrable\" bool,
	partial_payment_allowed bool
)";

$create_single_user_optional_budget_item_temporary_table_query = "
create table prod.ef_budget_item_set_optional_".$_POST["username"]."_temporary (
	memo text,
	priority int,
	start_date date,
	end_date date,
	interval text,
	amount float,
	\"deferrable\" bool,
	partial_payment_allowed bool
)";

$create_single_user_memo_rule_set_temporary_table_query = "
create table prod.ef_memo_rule_set_".$_POST["username"]."_temporary (
	memo_regex text,
	account_from text,
	account_to text,
	priority int
)";

$create_single_user_account_milestone_temporary_table_query = "
create table prod.ef_account_milestones_".$_POST["username"]."_temporary (
	milestone_name text,
	account_name text,
	min_balance float,
	max_balance float
)";

$create_single_user_memo_milestone_temporary_table_query = "
create table prod.ef_memo_milestones_".$_POST["username"]."_temporary (
	milestone_name text,
	memo_regex text
)";

$create_single_user_composite_milestone_temporary_table_query = "
create table prod.ef_composite_milestones_".$_POST["username"]."_temporary (
	composite_milestone_name text,
	account_milestone_name_list text,
	memo_milestone_name_list text
);";

$create_single_user_choices_temporary_table_query = "
create table prod.ef_choices_".$_POST["username"]."_temporary (
	choice_name text,
	option_name text,
	memo_regexes text
);";
//grant all privileges on prod.scenario_virtuoso_user_temporary to public;

$create_single_user_milestone_results_temporary_table_query = "
create table prod.".$_POST["username"]."_milestone_results_temporary (
	milestone_name text, 
	milestone_type text, 
	result_date date
);";
//grant all privileges on prod.scenario_virtuoso_user_temporary to public;

$create_single_user_staged_forecast_details = "
create table prod.".$_POST["username"]."_staged_forecast_details (
	forecast_set_id text,
	forecast_id text,
	forecast_set_name text,
	forecast_name text,
	start_date date,
	end_date date
);";

$create_forecast_run_metadata_table = "
create table prod.".$_POST["username"]."_forecast_run_metadata (
forecast_set_id text,
forecast_id text,
forecast_title text,
forecast_subtitle text,
submit_ts timestamp,
complete_ts timestamp,
error_flag bool,
satisfice_failed_flag bool,
insert_ts timestamp
);
";

$create_forecast_set_definitions_table = "
create table prod.".$_POST["username"]."_forecast_set_definitions (
	forecast_set_id text,
	forecast_set_name text,
	forecast_id text,
	forecast_name text,
	start_date date,
	end_date date,
	insert_ts timestamp
);
";

$create_optional_budget_item_set_q = "create table prod.".$_POST["username"]."_budget_item_post_run_category (
	category text,
	forecast_id text,
	\"date\" date,
	priority int,
	amount float,
	memo text,
	\"deferrable\" bool,
	partial_payment_allowed bool
)";



pg_query($dbconn,$create_single_user_account_set_table_query);
pg_query($dbconn,$create_single_user_budget_item_table_query);
pg_query($dbconn,$create_single_user_optional_budget_item_table_query);
pg_query($dbconn,$create_single_user_memo_rule_set_table_query);
pg_query($dbconn,$create_single_user_account_milestone_table_query);
pg_query($dbconn,$create_single_user_memo_milestone_table_query);
pg_query($dbconn,$create_single_user_composite_milestone_table_query);
pg_query($dbconn,$create_single_user_account_set_temporary_table_query);
pg_query($dbconn,$create_single_user_budget_item_temporary_table_query);
pg_query($dbconn,$create_single_user_optional_budget_item_temporary_table_query);
pg_query($dbconn,$create_single_user_memo_rule_set_temporary_table_query);
pg_query($dbconn,$create_single_user_account_milestone_temporary_table_query);
pg_query($dbconn,$create_single_user_memo_milestone_temporary_table_query);
pg_query($dbconn,$create_single_user_composite_milestone_temporary_table_query);
pg_query($dbconn,$create_single_user_choices_temporary_table_query);
pg_query($dbconn,$create_single_user_milestone_results_temporary_table_query);
pg_query($dbconn,$create_single_user_staged_forecast_details);
pg_query($dbconn,$create_forecast_run_metadata_table);
pg_query($dbconn,$create_forecast_set_definitions_table);
pg_query($dbconn,$create_optional_budget_item_set_q);