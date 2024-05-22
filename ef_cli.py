#!/usr/bin/env python
# Thanks to opie4624 from Github:  https://gist.github.com/opie4624/3896526

# import modules used here -- sys is a very standard one
import sys, argparse, logging

import ExpenseForecast
import ForecastSet
from log_methods import log_in_color
import pandas as pd
import psycopg2
import AccountSet
import BudgetSet
import MemoRuleSet
import MilestoneSet

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
fileHandler = logging.FileHandler(__name__+".log", mode='w')
fileHandler.setFormatter(formatter)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
# logger.setLevel(logging.INFO) #this gets overwritten
logger.handlers.clear()
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.propagate = False

import os
import datetime
import hashlib
from time import sleep

def scrape_dir_for_forecast_details(target_directory):
    return_df = pd.DataFrame([],columns=['source','type','id', 'num_4casts', 'start_date', 'end_date','load_err','start_ts','run_err','end_ts','done','resource_name'])
    for file_name in os.listdir(target_directory):
        if file_name.startswith('ForecastSet') and file_name.endswith('.json'):
            id_from_fname = file_name.split('_')[1].split('.')[0]
            try:
                S = ForecastSet.initialize_from_json_file(target_directory+file_name)
                new_row_df = pd.DataFrame(['file','Set', S.base_forecast.unique_id,len(S.forecast_name_to_budget_item_set__dict),
                                           datetime.datetime.strptime(S.base_forecast.start_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d'),
                                           datetime.datetime.strptime(S.base_forecast.end_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d'),
                                                     0, S.base_forecast.start_ts,
                                                     0,
                                                     S.base_forecast.end_ts,
                                                     0  # todo satisfice failed flag
                                                     ,file_name]).T
                new_row_df.columns = return_df.columns
                return_df = pd.concat([return_df, new_row_df])
            except Exception as e:
                new_row_df = pd.DataFrame(['file','Set', id_from_fname,'?',None, None, 1, None, 0, None, None,file_name]).T
                new_row_df.columns = return_df.columns
                return_df = pd.concat([return_df, new_row_df])
                raise e
        elif file_name.startswith('Forecast') and file_name.endswith('.json'):
            id_from_fname = file_name.split('_')[1].split('.')[0]
            try:
                E = ExpenseForecast.initialize_from_json_file(target_directory+file_name)

                satisfice_failed_ind = not E.forecast_df.tail(1).Date.iat[0] == E.end_date_YYYYMMDD #todo not sure if this is correct
                forecast_is_done_ind = not E.forecast_df is None

                new_row_df = pd.DataFrame(['file','F', E.unique_id, 1,
                              datetime.datetime.strptime(E.start_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d'),
                              datetime.datetime.strptime(E.end_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d'),
                              0, E.start_ts,
                              satisfice_failed_ind,# todo satisfice failed flag
                              E.end_ts,
                              forecast_is_done_ind,
                              file_name]).T
                new_row_df.columns = return_df.columns
                return_df = pd.concat([return_df,
                                       new_row_df ])
            except Exception as e:
                new_row_df = pd.DataFrame(['file','F', id_from_fname, 1, None, None, 1, None, 0, None, None,file_name ]).T
                new_row_df.columns = return_df.columns
                return_df = pd.concat([return_df, new_row_df])
                raise e

    return_df.reset_index(inplace=True,drop=True)
    return return_df


# Gather our code in a main() function
def main(args, loglevel):
    #logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
    os.environ["EF_LOG_DIR"] = args.log_directory
    try:
        config_lines = ""
        config_args = {}
        with open(args.config, 'r') as f:
            log_in_color(logger,'green','debug',"Loading " + str(args.config))
            config_lines = f.readlines()
            for l in config_lines:
                l = l.replace('\n', '')
                l_split = l.split('=')
                log_in_color(logger, 'green', 'debug',"SET " + l_split[0]+"="+l_split[1])
                config_args[l_split[0]] = l_split[1]
    except:
        log_in_color(logger, 'red', 'warning', "Could not read config file "+str(os.getcwd())+"/"+str(args.config))

    sys.path.append('/Users/hume/Github/expense_forecast')
    import ExpenseForecast
    import ForecastHandler
    import ForecastSet
    import pandas as pd
    from sqlalchemy import create_engine

    F = ForecastHandler.ForecastHandler()

    # print('ARGS:')

    ### up front validations
    # always valid: --log-directory

    ## db details, output_directory optional for these
    #  1. ef_cli parameterize forecast --filename FILE_NAME --start_date START_DATE --end_date END_DATE --username USERNAME
    #  2. ef_cli parameterize forecast --filename FILE_NAME --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
    #  3. ef_cli parameterize forecastset --filename FILE_NAME --start_date START_DATE --end_date END_DATE --username USERNAME
    #  4. ef_cli parameterize forecastset --filename FILE_NAME --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
    #  5. ef_cli reparameterize forecast --id FORECAST_ID --start_date START_DATE --end_date END_DATE --username USERNAME
    #  6. ef_cli reparameterize forecast --id FORECAST_ID --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
    #  7. ef_cli reparameterize forecastset --id FORECAST_SET_ID --start_date START_DATE --end_date END_DATE --username USERNAME
    #  8. ef_cli reparameterize forecastset --id FORECAST_SET_ID --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
    #  9. ef_cli run forecast --id FORECAST_ID --username USERNAME
    # 10. ef_cli run forecastset --id FORECAST_SET_ID --username USERNAME
    # 11. ef_cli run forecast --id FORECAST_ID --approximate --username USERNAME
    # 12. ef_cli run forecastset --id FORECAST_SET_ID --approximate --username USERNAME
    # 13. ef_cli run forecast --id FORECAST_ID --overwrite --username USERNAME
    # 14. ef_cli run forecastset --id FORECAST_SET_ID --overwrite --username USERNAME
    # 15. ef_cli run forecast --id FORECAST_ID --approximate --overwrite --username USERNAME
    # 16. ef_cli run forecastset --id FORECAST_SET_ID --approximate --overwrite --username USERNAME
    # 17. ef_cli report forecast --id FORECAST_ID --username USERNAME
    # 18. ef_cli report forecastset --id FORECAST_SET_ID --username USERNAME

    ## db details required for these
    # 19.  ef_cli export forecast --id FORECAST_ID
    # 20.  ef_cli export forecastset --id FORECAST_SET_ID
    # 21.  ef_cli import forecast --id FORECAST_ID
    # 22.  ef_cli import forecastset --id FORECAST_SET_ID

    ## db details not valid for these
    # 23.  ef_cli list
    # 24.  ef_cli ps
    # 25.  ef_cli kill forecast --id FORECAST_ID
    # 26.  ef_cli kill forecastset --id FORECAST_SET_ID

    # if any db params are defined, and filename is not passed explicitly, then file.
    # At this point though, let's set a garbage value for debugging
    # this is technically deprecated but may have some debugging use so let's leep for now

    assert len(args.action) <= 2
    assert args.action[0] in ['parameterize','run','list','ps','kill','report','export','import','inspect']
    if args.action[0] in ['parameterize','run','kill','report','export','import']:
        assert len(args.action) == 2
        assert args.action[1] in ['forecast','forecastset']

    #this is before config is loaded
    if args.action[0] in ['kill', 'ps']:
        assert args.database_hostname is None
        assert args.database_name is None
        assert args.database_username is None
        assert args.database_port is None
        assert args.database_password is None

    # if args.action[0] in ['parameterize']:
    #     assert args.filename is not None

    if args.action[0] in ['parameterize','run','report','export']:
        assert args.working_directory is not None
        assert os.path.isdir(args.working_directory)

    if args.action[0] in ['export','import']:
        assert args.database_hostname is not None
        assert args.database_name is not None
        assert args.database_username is not None
        assert args.database_port is not None
        assert args.database_password is not None

    # not valid bc there is a default value
    # if args.output_directory is not None:
    #     assert os.path.isdir(args.output_directory)
    #     assert args.action[0] in ['parameterize','run','report','export']

    #parameterize and reparameterize require start and end date
    if args.action[0] in ['parameterize']:
        assert args.start_date is not None
        assert args.end_date is not None
        assert args.id is not None # the string literal 'None' is a valid option for database

    # the label arg is only valid when used with parameterize and reparameterize
    if args.label is not None:
        assert args.action[0] in ['parameterize']

    assert os.path.isdir(args.log_directory) #check log_directory exists
    assert os.access(args.log_directory,os.W_OK) #check log_directory is writable

    if args.approximate:
        assert args.action[0] == 'run'

    if args.overwrite:
        assert args.action[0] == 'run'

    if args.id is not None:
        assert args.action[0] in ['run','kill','report','export','import','parameterize']

    if args.start_date is not None:
        args.start_date = args.start_date.replace('-','')
        datetime.datetime.strptime(args.start_date,'%Y%m%d') #will raise an exception if there is a problem

    if args.end_date is not None:
        args.end_date = args.end_date.replace('-', '')
        datetime.datetime.strptime(args.end_date,'%Y%m%d')

    #this would happen if neither filename nor database was passed explicitly
    #in that case, we check loaded config for db details
    #if there are no db details, then error, because there is no input to process
    if args.database_hostname is None:
        try:
            args.database_hostname = config_args["database_hostname"]
        except Exception as e:
            raise ValueError("db hostname not specified on cmd line or in config")

    if args.database_name is None:
        try:
            args.database_name = config_args["database_name"]
        except Exception as e:
            raise ValueError("db name not specified on cmd line or in config")

    if args.database_username is None:
        try:
            args.database_username = config_args["database_username"]
        except Exception as e:
            raise ValueError("db username not specified on cmd line or in config")

    if args.database_port is None:
        try:
            args.database_port = config_args["database_port"]
        except Exception as e:
            raise ValueError("db port not specified on cmd line or in config")

    if args.database_password is None:
        try:
            args.database_password = config_args["database_password"]
        except Exception as e:
            raise ValueError("db password not specified on cmd line or in config")

    if args.source == 'database' or args.source == 'both':
        # try to connect
        connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
        engine = create_engine(connect_string)
        connection_test = pd.read_sql_query("select 'connection successful'", con=engine)

        assert args.action[0] in ['parameterize','export','import','run','report','list']

    # if inferred_data_source_type == "undefined":
    #     raise ValueError("Input not sufficiently specificed. No filename or db details as params or from config on file.")

    #print('Passed all validation tests')
    if len(args.action) == 1:
        if args.action[0] == 'list' and args.source == 'file':
            forecast_file_details = scrape_dir_for_forecast_details(args.working_directory)
            if forecast_file_details.shape[0] == 0:
                print("No data to show.")
            else:
                print(forecast_file_details.to_string())
        elif args.action[0] == 'list' and args.source == 'database':
            # ['type','id', 'num_4casts', 'start_date', 'end_date','load_err','start_ts','run_err','end_ts','done','filename'])

            assert args.username is not None #temp for debug

            connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
            engine = create_engine(connect_string)
            forecast_database_details = pd.read_sql_query("""
select distinct 'db' as source,
'Set' as "type", 
deets.forecast_set_id as "id", 
count(distinct meta.forecast_id) as num_4casts,
start_date, 
end_date,
0 as load_err,
submit_ts as start_ts,
0 as run_err,
complete_ts as end_ts,
0 as done,
'' as resource_name
from prod.virtuoso_user_staged_forecast_details deets
LEFT JOIN prod."""+args.username+"""_forecast_run_metadata meta
ON deets.forecast_set_id = meta.forecast_set_id
where deets.forecast_set_id is not null and deets.forecast_set_id <> ''
group by 1,2,3,5,6,7,8,9,10,11
UNION
Select distinct 'db' as source,
'F' as "type", 
deets.forecast_id as "id", 
1 as num_4casts,
start_date, 
end_date,
0 as load_err,
meta.submit_ts as start_ts,
0 as run_err,
meta.complete_ts as end_ts,
0 as done,
CONCAT('prod.""" + args.username + """_forecast_',deets.forecast_id) as resource_name
from prod.virtuoso_user_staged_forecast_details deets
LEFT JOIN prod."""+args.username+"""_forecast_run_metadata meta
ON deets.forecast_set_id = meta.forecast_set_id
            """, con=engine)

            for index, row in forecast_database_details.iterrows():
                pass
                if row.type == 'F':
                    try:
                        table_existence_q = """ SELECT count(*)
                        FROM pg_catalog.pg_tables
                        where schemaname = 'prod'
                        and tableowner = '""" + args.username + """'
                        and tablename = '""" + args.username + """_forecast_"""+str(row.id) + "'"
                        table_existence_ind = pd.read_sql_query(table_existence_q, con=engine).iat[0,0]
                        forecast_database_details.iloc[index, 10] = table_existence_ind
                    except Exception as e:
                        forecast_database_details.iloc[index, 10] = 0
                        row.done = False

            if forecast_database_details.shape[0] == 0:
                print("No data to show.")
            else:
                print(forecast_database_details.to_string())
        elif args.action[0] == 'list' and args.source == 'both':
            forecast_file_details = scrape_dir_for_forecast_details(args.working_directory)
            connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
            engine = create_engine(connect_string)
            # ['source','type','id', 'num_4casts', 'start_date', 'end_date','load_err','start_ts','run_err','end_ts','done','file_name']
            forecast_database_details = pd.read_sql_query("""
            Select distinct 'db' as source,
'F' as "type", 
deets.forecast_id as "id", 
1 as num_4casts,
start_date, 
end_date,
0 as load_err,
meta.submit_ts as start_ts,
0 as run_err,
meta.complete_ts as end_ts,
0 as done,
CONCAT('prod.""" + args.username + """_forecast_',deets.forecast_id) as resource_name
from (
select forecast_id
from prod.""" + args.username + """_staged_forecast_details
UNION
select forecast_id
from prod.""" + args.username + """_forecast_run_metadata
) all_forecasts_all_states
LEFT JOIN prod.""" + args.username + """_staged_forecast_details deets
ON all_forecasts_all_states.forecast_id = deets.forecast_id
LEFT JOIN prod.""" + args.username + """_forecast_run_metadata meta
ON all_forecasts_all_states.forecast_id = meta.forecast_id
                        """, con=engine)

            #todo modify forecast_database_details based on forecast table existence

            both_forecast_details = pd.concat([forecast_file_details,forecast_database_details])
            both_forecast_details.reset_index(inplace=True,drop=True)
            if both_forecast_details.shape[0] == 0:
                print("No data to show.")
            else:
                print(both_forecast_details.to_string())

        if args.action[0] == 'inspect':
            #todo args.filename could be a path
            if args.filename.startswith('ForecastSet') and args.filename.endswith('.json'):
                try:
                    S = ForecastSet.initialize_from_json_file(args.filename)
                    print(S)
                except:
                    print('Failed to parse ForecastSet')
            elif args.filename.startswith('Forecast') and args.filename.endswith('.json'):
                try:
                    E = ExpenseForecast.initialize_from_json_file(args.filename)
                    print(E)
                except:
                    print('Failed to parse Forecast')
            else:
                print('filename does not match an expected pattern')

    if len(args.action) == 2:
        if args.action[0] == 'parameterize' and args.action[1] == 'forecast' and args.source == "file":

            E = ExpenseForecast.initialize_from_json_file(args.filename) #let this throw an exception if needed
            E.update_date_range(args.start_date,args.end_date)
            if args.label:
                E.forecast_name = args.label
            E.writeToJSONFile(args.working_directory)
            os.remove(args.filename)
        elif args.action[0] == 'parameterize' and args.action[1] == 'forecastset' and args.source == "file":
            S = ForecastSet.initialize_from_json_file(args.filename) #let this throw an exception if needed
            # print('BEFORE')
            # print(S)
            S.update_date_range(args.start_date,args.end_date)
            # print('AFTER')
            # print(S)
            if args.label:
                S.forecast_set_name = args.label
            S.writeToJSONFile(args.working_directory)
            os.remove(args.filename)
        elif args.action[0] == 'run' and args.action[1] == 'forecast' and args.source == "file":

            forecast_found = False
            for f in os.listdir(args.working_directory):
                if f.startswith('Forecast') and not f.startswith('ForecastSet') and f.endswith('.json') and str(args.id) in f:
                    forecast_found = True
                    #print('Starting forecast '+str(args.id))
                    E = ExpenseForecast.initialize_from_json_file(os.path.join(args.working_directory, f)) #let this throw an exception if needed
                    if args.label:
                        E.forecast_name = args.label
                    if args.approximate:
                        E.runForecastApproximate()
                    else:
                        E.runForecast()
                    E.appendSummaryLines()
                    E.writeToJSONFile(args.working_directory)
                    F = ForecastHandler.ForecastHandler()
                    F.generateHTMLReport(E)
                    break #bc only running a single forecast
            if not forecast_found:
                print('Forecast '+str(args.id)+' not found')
        elif args.action[0] == 'run' and args.action[1] == 'forecastset' and args.source == "file":
            forecast_set_found = False
            for f in os.listdir(args.working_directory):
                if f.startswith('ForecastSet') and f.endswith('.json') and str(args.id) in f:
                    forecast_set_found = True
                    S = ForecastSet.initialize_from_json_file(os.path.join(args.working_directory, f)) #let this throw an exception if needed
                    #S.initialize_forecasts()
                    if args.approximate:
                        S.runAllForecastsApproximate()
                    else:
                        S.runAllForecasts()

                    # for id, E in S.initialized_forecasts.items():
                    #     print(E.forecast_df.shape)

                    S.writeToJSONFile(args.working_directory) #todo this is not writing forecast_df and indeed some of the other data frames as intended
                    F = ForecastHandler.ForecastHandler()
                    for unique_id, E in S.initialized_forecasts.items():
                        E.writeToJSONFile(args.working_directory)
                        F.generateHTMLReport(E)
                    break  # bc only running a single forecast set
            if not forecast_set_found:
                print('Forecast Set ' + str(args.id) + ' not found')
        elif args.action[0] == 'run' and args.action[1] == 'forecast' and args.source == "database":

            connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
            engine = create_engine(connect_string)

            forecast_found = False
            try:
                E = ExpenseForecast.initialize_from_database_with_id(
                                        args.username,
                                        forecast_set_id='',
                                        forecast_id=args.id,
                                         database_hostname=args.database_hostname,
                                         database_name=args.database_name,
                                         database_username=args.database_username,
                                         database_password=args.database_password,
                                         database_port=args.database_port
                                                                      )
                #
                # print(E.initial_account_set.getAccounts().to_string())
                # print(E.initial_memo_rule_set.getMemoRules().to_string())
                # log_in_color(logger, 'magenta', 'info', E)
                # assert False

                if args.approximate:
                    E.runForecastApproximate()
                else:
                    E.runForecast(log_level='WARNING')
                forecast_found = True
            except Exception as e:
                raise e

            # log_in_color(logger, 'magenta', 'info', E)
            # log_in_color(logger, 'magenta', 'info', 'AccountSet df')
            # log_in_color(logger, 'magenta', 'info', E.initial_account_set.getAccounts().to_string())
            # log_in_color(logger, 'magenta', 'info', 'Results before writing to db')
            # log_in_color(logger, 'magenta', 'info', E.forecast_df.to_string())

            E.writeToJSONFile(args.working_directory)
            # log_in_color(logger, 'green', 'info', 'Finished writing json data to file')
            E.write_to_database(username=args.username,
                                database_hostname=args.database_hostname,
                                database_name=args.database_name,
                                database_username=args.database_username,
                                database_password=args.database_password,
                                database_port=args.database_port, overwrite=args.overwrite)
            # log_in_color(logger, 'green', 'info', 'Finished writing forecast data to database')
            E.forecast_df.to_csv(args.working_directory + '/Forecast_' + str(E.unique_id) + '.csv', index=False)
            # log_in_color(logger, 'green', 'info',
            #              'Finished writing forecast data to ' + args.working_directory + '/Forecast_' + str(
            #                  E.unique_id) + '.csv')
            F.generateHTMLReport(E, args.working_directory)
            # log_in_color(logger, 'green', 'info', 'Finished writing forecast report to ' + args.working_directory)

            # engine = create_engine('postgresql://bsdegjmy_humedick@localhost:5432/bsdegjmy_sandbox')

            # forecast_stage_table_name = 'prod.' + args.username + '_forecast_run_metadata'
            # forecast_stage_df = pd.read_sql_query('select * from ' + forecast_stage_table_name, con=engine)
            #
            # account_set_table_name = 'prod.ef_account_set_' + args.username
            # budget_set_table_name='prod.ef_budget_item_set_'+args.username
            # memo_rule_set_table_name = 'prod.ef_memo_rule_set_' + args.username
            # account_milestone_table_name = 'prod.ef_account_milestones_' + args.username
            # memo_milestone_table_name = 'prod.ef_memo_milestones_' + args.username
            # composite_milestone_table_name = 'prod.ef_composite_milestones_' + args.username
            #
            # for index, row in forecast_stage_df.iterrows():
            #     forecast_id = row.forecast_id
            #     start_date = str(row.start_date).replace('-','')
            #     end_date = str(row.end_date).replace('-','')
            #     forecast_set_name = row.forecast_set_name
            #     forecast_name = row.forecast_name
            #     A_q = 'select * from ' + account_set_table_name + ' where forecast_id = \''+forecast_id+'\''
            #     B_q = 'select * from ' + budget_set_table_name + ' where forecast_id = \''+forecast_id+'\''
            #     M_q = 'select * from ' + memo_rule_set_table_name + ' where forecast_id = \''+forecast_id+'\''
            #     AM_q = 'select * from ' + account_milestone_table_name + ' where forecast_id = \''+forecast_id+'\''
            #     MM_q = 'select * from ' + memo_milestone_table_name + ' where forecast_id = \''+forecast_id+'\''
            #     CM_q = 'select * from ' + composite_milestone_table_name + ' where forecast_id = \''+forecast_id+'\''
            #     A = AccountSet.initialize_from_dataframe(pd.read_sql_query(A_q, con=engine))
            #     B = BudgetSet.initialize_from_dataframe(pd.read_sql_query(B_q, con=engine))
            #     M = MemoRuleSet.initialize_from_dataframe(pd.read_sql_query(M_q, con=engine))
            #     AM_df = pd.read_sql_query(AM_q, con=engine)
            #     MM_df = pd.read_sql_query(MM_q, con=engine)
            #     CM_df = pd.read_sql_query(CM_q, con=engine)
            #     MS = MilestoneSet.initialize_from_dataframe(AM_df, MM_df, CM_df)
            #     E = ExpenseForecast.ExpenseForecast(A, B, M, start_date, end_date, MS, args.log_directory, forecast_set_name, forecast_name)
            #     log_in_color(logger, 'white', 'info', E)
            #     if args.approximate:
            #         E.runForecastApproximate()
            #     else:
            #         E.runForecast()
            #     print(E.unique_id) #it is very important that this is the only print statement
            #
            #     #todo delete row from forecast stage
            #
            #     E.appendSummaryLines()
            # E.writeToJSONFile(args.working_directory)
            # log_in_color(logger, 'green', 'info', 'Finished writing json data to file')
            # E.write_to_database(args.username,args.database_hostname, args.database_name, args.database_username, args.database_password, args.database_port, overwrite=args.overwrite)
            # log_in_color(logger, 'green', 'info','Finished writing forecast data to database')
            # E.forecast_df.to_csv(args.working_directory+'/Forecast_'+str(E.unique_id)+'.csv',index=False)
            # log_in_color(logger, 'green', 'info','Finished writing forecast data to ' + args.working_directory+'/Forecast_'+str(E.unique_id)+'.csv')
            # F.generateHTMLReport(E, args.working_directory)
            # log_in_color(logger, 'green', 'info', 'Finished writing forecast report to ' + args.working_directory)
        elif args.action[0] == 'run' and args.action[1] == 'forecastset' and args.source == "database":
            forecast_set_found = False

            # connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
            # engine = create_engine(connect_string)

            # single_set_stage_details_q = "select distinct forecast_set_id, forecast_id from prod.virtuoso_user_staged_forecast_details where forecast_set_id = '"+str(args.id)+"'"
            # single_set_stage_details_df = pd.read_sql_query(single_set_stage_details_q, con=engine)

            # heads up there may be forecasts that belong to a forecast set that were deleted from stage
            try:
                S = ForecastSet.initialize_forecast_set_from_database(set_id=args.id,
                                                                      username=args.username,
                                                                      database_hostname=args.database_hostname,
                                                                      database_name=args.database_name,
                                                                      database_username=args.database_username,
                                                                      database_password=args.database_password,
                                                                      database_port=args.database_port)
                forecast_set_found = True
            except Exception as e:
                raise e
            #S.initialize_forecasts()
            #print('len(S.initialized_forecasts):'+str(len(S.initialized_forecasts)))
            if args.approximate:
                S.runAllForecastsApproximate()
            else:
                S.runAllForecasts()
            S.writeToDatabase(database_hostname=args.database_hostname,
                                          database_name=args.database_name,
                                          database_username=args.database_username,
                                          database_password=args.database_password,
                                          database_port=args.database_port,
                              username=args.username)

            # print('Writing ForecastSet json to file HELLO')
            S.writeToJSONFile(args.working_directory)
            F = ForecastHandler.ForecastHandler()
            #todo also write Set JSON and report. i think 'write child reports' could be a parameter
            for unique_id, E in S.initialized_forecasts.items():
                E.writeToJSONFile(args.working_directory)
                E.forecast_df.to_csv(args.working_directory+'Forecast_'+E.unique_id+'.csv',index=False)
                F.generateHTMLReport(E)
            if not forecast_set_found:
                print('Forecast Set ' + str(args.id) + ' not found')
        elif args.action[0] == 'parameterize' and args.action[1] == 'forecast' and args.source == "database":
            connection = psycopg2.connect(host=args.database_hostname,
                                          database=args.database_name,
                                          user=args.database_username,
                                          password=args.database_password,
                                          port=args.database_port)
            connection.autocommit = True
            cursor = connection.cursor()

            account_set_table_name = 'prod.ef_account_set_' + args.username
            budget_set_table_name = 'prod.ef_budget_item_set_' + args.username
            memo_rule_set_table_name = 'prod.ef_memo_rule_set_' + args.username
            date_range_table_name = 'prod.'+args.username+'_forecast_date_ranges'

            temporary_account_set_table_name = 'prod.ef_account_set_' + args.username + '_temporary'
            temporary_budget_set_table_name = 'prod.ef_budget_item_set_' + args.username + '_temporary'
            temporary_memo_rule_set_table_name = 'prod.ef_memo_rule_set_' + args.username + '_temporary'
            temporary_account_milestone_table_name = 'prod.ef_account_milestones_' + args.username + '_temporary'
            temporary_memo_milestone_table_name = 'prod.ef_memo_milestones_' + args.username + '_temporary'
            temporary_composite_milestone_table_name = 'prod.ef_composite_milestones_' + args.username + '_temporary'

            forecast_set_def_name = 'prod.' + args.username + '_forecast_set_definitions'

            account_set_select_q = "select * from " + temporary_account_set_table_name
            budget_set_select_q =  "select * from " + temporary_budget_set_table_name
            memo_rule_set_select_q = "select * from " + temporary_memo_rule_set_table_name
            account_milestone_select_q = "select * from " + temporary_account_milestone_table_name
            memo_milestone_select_q = "select * from " + temporary_memo_milestone_table_name
            composite_milestone_select_q = "select * from " + temporary_composite_milestone_table_name

            # this is just the source of forecase_name so a row of blanks is fine
            # forecast_set_id, forecast_set_name, forecast_id, forecast_name, start_date, end_date, insert_ts
            set_def_q = """
                           select '' as forecast_set_id, '' as forecast_set_name, '' as forecast_id, '""" + args.label + """' as forecast_name, 
                           '' as start_date, '' as end_date, '' as insert_ts
                           """

            # it has to be forecast_set bc if forecast hasnt been run yet we still need that info
            # a 0-row response is valid
            metadata_q = """
                           select forecast_set_id, forecast_id, forecast_title, forecast_subtitle,
                           submit_ts, complete_ts, error_flag, satisfice_failed_flag
                           from (
                           select *, row_number() over(partition by forecast_id order by insert_ts desc) as rn
                           from prod.""" + args.username + """_forecast_run_metadata
                           where forecast_id = 'FORECAST NOT YET RUN'
                           order by forecast_id
                           ) where rn = 1 and forecast_id = 'FORECAST NOT YET RUN'
                           """

            # Forecast not yet run so an empty row response is valid
            budget_item_post_run_category_select_q = "select * from prod." + args.username + "_budget_item_post_run_category where forecast_id = 'FORECAST_NOT_YET_RUN'"

            # If no forecast, this query will fail downstream
            forecast_select_q = "Nonsense query bc forecast does not exist on db yet"

            E = ExpenseForecast.initialize_from_database_with_select(args.start_date,
                                                              args.end_date,
                                                              account_set_select_q=account_set_select_q,
                                                              budget_set_select_q=budget_set_select_q,
                                                              memo_rule_set_select_q=memo_rule_set_select_q,
                                                              account_milestone_select_q=account_milestone_select_q,
                                                              memo_milestone_select_q=memo_milestone_select_q,
                                                              composite_milestone_select_q=composite_milestone_select_q,
                                                                     set_def_q=set_def_q,
                                                                     metadata_q=metadata_q,
                                                                     budget_item_post_run_category_select_q=budget_item_post_run_category_select_q,
                                                                     forecast_select_q=forecast_select_q,
                                                              database_hostname=args.database_hostname,
                                                              database_name=args.database_name,
                                                              database_username=args.database_username,
                                                              database_password=args.database_password,
                                                              database_port=args.database_port,
                                                              log_directory=args.log_directory,
                                                              forecast_set_name='',
                                                              forecast_name=args.label
                                                              )

            #log_in_color(logger, 'white', 'info', E)
            A_insert_q = "INSERT INTO " + account_set_table_name + " Select '" + E.unique_id + "', account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind from "+temporary_account_set_table_name
            cursor.execute(A_insert_q)
            B_insert_q = "INSERT INTO " + budget_set_table_name + " Select '" + E.unique_id + "', memo, priority, start_date, end_date,  cadence, amount, \"deferrable\", partial_payment_allowed from "+temporary_budget_set_table_name
            cursor.execute(B_insert_q)
            M_insert_q = "INSERT INTO " + memo_rule_set_table_name + " Select '" + E.unique_id + "', memo_regex, account_from, account_to, priority from " + temporary_memo_rule_set_table_name
            cursor.execute(M_insert_q)

            forecast_set_delete_q = "DELETE FROM "+forecast_set_def_name+" where forecast_id = '"+E.unique_id+"'"

            # forecast_set_id text,
            # 	forecast_set_name text,
            # 	forecast_id text,
            # 	forecast_name text,
            # 	start_date date,
            # 	end_date date,
            # 	insert_ts timestamp
            forecast_set_insert_q = "INSERT INTO "+forecast_set_def_name+" select '' as forecast_set_id, '' as forecast_set_name, "
            forecast_set_insert_q += "'"+E.unique_id+"' as forecast_id, '"+E.forecast_name+"' as forecast_name, '"+E.start_date_YYYYMMDD+"', '"
            forecast_set_insert_q += E.end_date_YYYYMMDD+"','"+datetime.datetime.now().strftime('%Y%m%d')+"'"
            cursor.execute(forecast_set_delete_q)
            cursor.execute(forecast_set_insert_q)
            # date_range_q = "DELETE FROM " + date_range_table_name + " WHERE forecast_id = '" + E.unique_id + "'"
            # cursor.execute(date_range_q)
            # date_range_q = "INSERT INTO " + date_range_table_name + " Select '" + E.unique_id + "','" + args.start_date + "','" + args.end_date + "','" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "'"
            # cursor.execute(date_range_q)
            #
            # stage_row_q = "INSERT INTO prod." + str(args.username) + "_staged_forecast_details Select '', '"+str(E.unique_id)+"','','"+str(args.label)+"','"+str(args.start_date)+"','"+str(args.end_date)+"'"
            # cursor.execute(stage_row_q)

            # todo milestone tables

        elif args.action[0] == 'parameterize' and args.action[1] == 'forecastset' and args.source == "database":
            #todo the logic in this block assumes the forecast is run, bc even if it did we don't plan on using it
            #while this would most often produce expected results, it may not be strictly true (there may be cached data)
            #if there is cached data there COULD be unexpected results. I haven't thought it all the way through

            temporary_account_set_table_name = 'prod.ef_account_set_' + args.username + '_temporary'
            temporary_budget_set_table_name = 'prod.ef_budget_item_set_' + args.username + '_temporary'
            temporary_memo_rule_set_table_name = 'prod.ef_memo_rule_set_' + args.username + '_temporary'
            temporary_account_milestone_table_name = 'prod.ef_account_milestones_' + args.username + '_temporary'
            temporary_memo_milestone_table_name = 'prod.ef_memo_milestones_' + args.username + '_temporary'
            temporary_composite_milestone_table_name = 'prod.ef_composite_milestones_' + args.username + '_temporary'

            account_set_table_name = 'prod.ef_account_set_' + args.username
            budget_set_table_name = 'prod.ef_budget_item_set_' + args.username
            memo_rule_set_table_name = 'prod.ef_memo_rule_set_' + args.username
            account_milestone_table_name = 'prod.ef_account_milestones_' + args.username
            memo_milestone_table_name = 'prod.ef_memo_milestones_' + args.username
            composite_milestone_table_name = 'prod.ef_composite_milestones_' + args.username

            forecast_set_def_name = 'prod.' + args.username + '_forecast_set_definitions'

            account_set_select_q = "select * from " + temporary_account_set_table_name
            budget_set_select_q = "select * from " + temporary_budget_set_table_name
            memo_rule_set_select_q = "select * from " + temporary_memo_rule_set_table_name
            account_milestone_select_q = "select * from " + temporary_account_milestone_table_name
            memo_milestone_select_q = "select * from " + temporary_memo_milestone_table_name
            composite_milestone_select_q = "select * from " + temporary_composite_milestone_table_name

            # this is just the source of forecase_name so a row of blanks is fine
            # forecast_set_id, forecast_set_name, forecast_id, forecast_name, start_date, end_date, insert_ts
            set_def_q = """
               select '' as forecast_set_id, '' as forecast_set_name, '' as forecast_id, '' as forecast_name, 
               '' as start_date, '' as end_date, '' as insert_ts
               """

            # it has to be forecast_set bc if forecast hasnt been run yet we still need that info
            # a 0-row response is valid
            metadata_q = """
               select forecast_set_id, forecast_id, forecast_title, forecast_subtitle,
               submit_ts, complete_ts, error_flag, satisfice_failed_flag
               from (
               select *, row_number() over(partition by forecast_id order by insert_ts desc) as rn
               from prod.""" + args.username + """_forecast_run_metadata
               where forecast_id = 'FORECAST NOT YET RUN'
               order by forecast_id
               ) where rn = 1 and forecast_id = 'FORECAST NOT YET RUN'
               """

            #Forecast not yet run so an empty row response is valid
            budget_item_post_run_category_select_q = "select * from prod." + args.username + "_budget_item_post_run_category where forecast_id = 'FORECAST_NOT_YET_RUN'"

            # If no forecast, this query will fail downstream
            forecast_select_q = "Nonsense query bc forecast does not exist on db yet"

            base_E = ExpenseForecast.initialize_from_database_with_select(args.start_date,
                    args.end_date,
                    account_set_select_q=account_set_select_q,
                    budget_set_select_q=budget_set_select_q,
                    memo_rule_set_select_q=memo_rule_set_select_q,
                    account_milestone_select_q=account_milestone_select_q,
                    memo_milestone_select_q=memo_milestone_select_q,
                    composite_milestone_select_q=composite_milestone_select_q,
                    set_def_q=set_def_q,
                    metadata_q=metadata_q,
                    budget_item_post_run_category_select_q=budget_item_post_run_category_select_q,
                    forecast_select_q=forecast_select_q,
                    database_hostname=args.database_hostname,
                    database_name=args.database_name,
                    database_username=args.database_username,
                    database_password=args.database_password,
                    database_port=args.database_port,
                    log_directory=args.log_directory,
                    forecast_set_name=args.label,
                    forecast_name='Core'
                    )

            A = base_E.initial_account_set
            M = base_E.initial_memo_rule_set
            start_date_YYYYMMDD = base_E.start_date_YYYYMMDD
            end_date_YYYYMMDD = base_E.end_date_YYYYMMDD
            MS = base_E.milestone_set

            core_budget_set = base_E.initial_budget_set

            connection = psycopg2.connect(host=args.database_hostname,
                                          database=args.database_name,
                                          user=args.database_username,
                                          password=args.database_password,
                                          port=args.database_port)
            connection.autocommit = True
            cursor = connection.cursor()

            connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
            engine = create_engine(connect_string)
            # engine = create_engine('postgresql://bsdegjmy_humedick@localhost:5432/bsdegjmy_sandbox')
            option_budget_set_table_name = 'prod.ef_budget_item_set_optional_'+args.username+'_temporary'
            option_budget_set = BudgetSet.initialize_from_dataframe(pd.read_sql_query('select * from '+option_budget_set_table_name, con=engine))

            S = ForecastSet.ForecastSet(base_E, option_budget_set, forecast_set_name=args.label)
            choice_table_name = 'prod.ef_choices_' + args.username + '_temporary'
            choices_df = pd.read_sql_query('select * from ' + choice_table_name, con=engine)

            choice_option_map = {}
            option_name_to_memo_regex_list_map = {}
            for index, row in choices_df.iterrows():
                if row.choice_name not in choice_option_map:
                    choice_option_map[row.choice_name] = []
                if row.option_name not in choice_option_map[row.choice_name]:
                    choice_option_map[row.choice_name].append(row.option_name)

                    # this is semicolon separated instead of a list
                    option_name_to_memo_regex_list_map[row.choice_name+' | '+row.option_name] = row.memo_regexes

            for choice_name, option_name_list in choice_option_map.items():
                list_of_lists_of_memo_regexes = []
                for option_name in option_name_list:
                    list_of_lists_of_memo_regexes.append(option_name_to_memo_regex_list_map[choice_name + ' | ' + option_name].split(';'))
                S.addChoiceToAllForecasts(option_name_list, list_of_lists_of_memo_regexes)
            S.writeToDatabase(args.database_hostname,
                                          args.database_name,
                                          args.database_username,
                                          args.database_password,
                                          args.database_port,
                              args.username)
            # # print(S)
            # cursor.execute("DELETE FROM prod.forecast_set_definitions WHERE forecast_set_id = \'" + str(S.unique_id) + "\'")
            # for unique_id, E in S.initialized_forecasts.items():
            #     cursor.execute("DELETE FROM " + account_set_table_name + " WHERE forecast_id = \'" + str(E.unique_id) + "\'")
            #     for index, row in E.initial_account_set.getAccounts().iterrows():
            #         if row.Billing_Start_Date is None:
            #             bsd = "Null"
            #         else:
            #             bsd = "'" + str(row.Billing_Start_Date) + "'"
            #         if row.APR is None:
            #             apr = "Null"
            #         else:
            #             apr = "'" + str(row.APR) + "'"
            #         if row.Minimum_Payment is None:
            #             min_payment = "Null"
            #         else:
            #             min_payment = str(row.Minimum_Payment)
            #
            #         insert_account_row_q = "INSERT INTO " + account_set_table_name + " (forecast_id, account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) VALUES "
            #         insert_account_row_q += "('"+str(E.unique_id)+"', '"+str(row.Name)+"', "+str(row.Balance)+", "+str(row.Min_Balance)+", "+str(row.Max_Balance)+", '"+str(row.Account_Type)+"', "+str(bsd)+", "+apr+", '"+str(row.Interest_Cadence)+"', "+min_payment+", '"+str(row.Primary_Checking_Ind)+"')"
            #         cursor.execute(insert_account_row_q)
            #
            #     cursor.execute("DELETE FROM " + budget_set_table_name + " WHERE forecast_id = \'" + str(E.unique_id) + "\'")
            #     for index, row in E.initial_budget_set.getBudgetItems().iterrows():
            #         insert_budget_item_row_q = "INSERT INTO " + budget_set_table_name + " (forecast_id, memo, priority, start_date, end_date, cadence, amount, \"deferrable\", partial_payment_allowed) VALUES "
            #         insert_budget_item_row_q += "('"+str(E.unique_id)+"','"+str(row.Memo)+"',"+str(row.Priority)+",'"+str(row.Start_Date)+"','"+str(row.End_Date)+"','"+str(row.Cadence)+"',"+str(row.Amount)+",'"+str(row.Deferrable)+"','"+str(row.Partial_Payment_Allowed)+"')"
            #         cursor.execute(insert_budget_item_row_q)
            #
            #     cursor.execute("DELETE FROM " + memo_rule_set_table_name + " WHERE forecast_id = \'" + str(E.unique_id) + "\'")
            #     for index, row in E.initial_memo_rule_set.getMemoRules().iterrows():
            #         insert_memo_rule_row_q = "INSERT INTO " + memo_rule_set_table_name + " (forecast_id, memo_regex, account_from, account_to, priority ) VALUES "
            #         insert_memo_rule_row_q += "('"+str(E.unique_id)+"','"+str(row.Memo_Regex)+"','"+str(row.Account_From)+"','"+str(row.Account_To)+"',"+str(row.Transaction_Priority)+")"
            #         cursor.execute(insert_memo_rule_row_q)
            #
            #     # todo account milestone set
            #     # todo memo milestone set
            #     # todo composite milestone set
            #
            #     #todo insert into a forecastset table
            #     cursor.execute("INSERT INTO prod.forecast_set_definitions SELECT '"+args.username+"', '"+S.unique_id+"','"+E.unique_id+"','"+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"'")
            #
            #     forecast_name = S.id_to_name[E.unique_id]
            #     insert_stage_q = "INSERT INTO prod." + str(args.username) + "_staged_forecast_details Select '"+str(S.unique_id)+"','"+str(E.unique_id)+"','"+str(args.label)+"','"+str(forecast_name)+"','"+str(args.start_date)+"','"+str(args.end_date)+"'"
            #     cursor.execute(insert_stage_q)


# ef_cli parameterize forecast
# ef_cli reparameterize forecast
# ef_cli reparameterize forecastset
# ef_cli run forecast
# ef_cli run forecastset
# ef_cli list
# ef_cli ps
# ef_cli kill forecast
# ef_cli kill forecastset
# ef_cli report forecast --id FORECAST_ID
# ef_cli report forecastset --id FORECAST_SET_ID
# ef_cli export
# ef_cli import
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Runs a Forecast or ForecastSet and displays a progress bar.",
        epilog="As an alternative to the commandline, params can be placed in a file, one per line, and specified on the commandline like '%(prog)s @params.conf'.",
        fromfile_prefix_chars='@')
    parser.add_argument('action',
                        nargs = '*',
                        choices=['parameterize',
                                 'run',
                                 'list',
                                 'ps',
                                 'kill',
                                 'report',
                                 'export',
                                 'import',
                                 'forecast',
                                 'forecastset',
                                 'inspect'
                                 ])
    parser.add_argument(
        "--working_directory",
        default='./',
        required=False,
        help="Directory where JSON, csv and HTML files will be output.",
        action="store")
    parser.add_argument(
        "-v",
        "--verbose",
        required=False,
        help="increase output verbosity",
        action="store_true")
    parser.add_argument(
        "--username",
        required=False,
        default='ef_user',
        help="username for filter on temp tables for running based on db data",
        action="store")
    parser.add_argument(
        "--overwrite",
        required=False,
        help="Overwrite output data if present.",
        action="store_true")
    parser.add_argument(
        "--database_hostname",
        required=False,
        help="database hostname",
        action="store")
    parser.add_argument(
        "--database_name",
        required=False,
        help="database name",
        action="store")
    parser.add_argument(
        "--database_username",
        required=False,
        help="database username",
        action="store")
    parser.add_argument(
        "--database_password",
        required=False,
        help="database password",
        action="store")
    parser.add_argument(
        "--database_port",
        required=False,
        help="database port",
        action="store")
    parser.add_argument(
        "--log_directory",
        default='./log/',
        required=False, #default ./log/
        help="Log directory",
        action="store")
    parser.add_argument(
        "--approximate",
        required=False,
        help="Run a forecast based on the first of each month.",
        action="store_true")
    parser.add_argument(
        "--id",
        help="Id of forecastset or forecast to run.",
        action="store")
    parser.add_argument(
        "--start_date",
        help="Start date",
        action="store")
    parser.add_argument(
        "--end_date",
        help="End date",
        action="store")
    parser.add_argument(
        "--label",
        required=False,
        help="add a nickname to this forecast run. Uniqueness not enforced.",
        action="store")
    parser.add_argument(
        "--config",
        required=False,
        default='./ef_cli.config',
        help="Default ./ef_cli.config. path of config file, else other values such as db conn details and username are expected",
        action="store")
    parser.add_argument(
        "--log_level",
        required=False,
        default="INFO",
        help="Log level. Default is WARNING",
        action="store")
    parser.add_argument(
        "--source",
        required=False,
        default="both",
        help="both, file or database.",
        action="store")

    args = parser.parse_args()
    if args.log_level == 'DEBUG':
        loglevel = logging.DEBUG
    elif args.log_level == 'INFO':
        loglevel = logging.INFO
    elif args.log_level == 'WARNING':
        loglevel = logging.WARNING
    elif args.log_level == 'ERROR':
        loglevel = logging.ERROR
    elif args.log_level == 'CRITICAL':
        loglevel = logging.CRITICAL
    else:
        loglevel = logging.WARNING
    #loglevel = logging.INFO
    logger.setLevel(loglevel)

    # print('args:')
    # print(args)

    main(args, loglevel)