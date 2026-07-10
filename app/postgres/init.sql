create schema deleted;
create schema backup;
create schema prod;
create schema shared;
create schema audit;

CREATE USER virtuoso_user WITH PASSWORD 'virtuoso_password';

--this really needs to change but I just want it to work and i am the only one using it rn
--this will be local anyway (unless multiple people using the same computer/container)
--for top notch security, this MUST be revised, but it is not a network vulnerability
GRANT ALL ON SCHEMA prod TO virtuoso_user;
--ALTER DEFAULT PRIVILEGES IN SCHEMA prod GRANT ALL PRIVILEGES ON TABLES TO PUBLIC;
--GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA prod TO staff;
--ALTER DEFAULT PRIVILEGES IN SCHEMA prod GRANT ALL PRIVILEGES ON TABLES TO virtuoso_user;

create table prod.all_forecasts (
	report_link text,
	forecast_id text,
	forecast_name text,
	username text,
	submit_ts timestamp,
	complete_ts timestamp,
	error_flag bool,
	satisfice_failed_flag bool,
	insert_ts timestamp,
	update_ts timestamp
);

create table public.passwords (
	hashed_password text,
	userid text
);

-- create table prod.ef_checking_accounts (
-- accountname text,
-- balance float,
-- min_balance float,
-- max_balance float,
-- forecast_id int
-- );

-- create table prod.ef_credit_accounts (
-- accountname text,
-- balance float,
-- min_balance float,
-- max_balance float,
-- prev_stmt_bal float,
-- apr float,
-- min_payment float,
-- interest_interval text,
-- billing_start_date date,
-- forecast_id int
-- );

-- create table prod.ef_investment_accounts (
-- accountname text,
-- balance float,
-- min_balance float,
-- max_balance float,
-- apr float,
-- interest_interval text,
-- billing_start_date date,
-- forecast_id int
-- );

-- create table prod.ef_loan_accounts (
-- accountname text,
-- balance float,
-- min_balance float,
-- max_balance float,
-- interest_balance float,
-- apr float,
-- min_payment float,
-- interest_interval text,
-- billing_start_date date,
-- forecast_id int
-- );


create table public.users (
	username text, 
	hashed_password text, 
	email text, 
	email_is_confirmed bool
);
grant select on public.users to public;
grant insert on public.users to public;

create table public.email_confirmation_codes (
	email text, 
	confirmation_code text, 
	valid_until timestamp, 
	attempt_count int
);
grant select on public.email_confirmation_codes to public;
grant insert on public.email_confirmation_codes to public;

create table public.session (
	login_token text,
	"key" text,
	"value" text
);
grant select on public.session to public;
grant insert on public.session to public;
