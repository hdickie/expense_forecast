#!/usr/bin/env python
# Thanks to opie4624 from Github:  https://gist.github.com/opie4624/3896526

# import modules used here -- sys is a very standard one
import sys, argparse, logging
from log_methods import log_in_color
from log_methods import setup_logger
logger = logging.getLogger(__name__)
#logger = setup_logger('ef_cli', './log/ef_cli.log', level=logging.DEBUG)
import os
import datetime
import hashlib

# Gather our code in a main() function
def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    os.environ["EF_LOG_DIR"] = args.log_directory

    sys.path.append('/Users/hume/Github/expense_forecast')
    import ExpenseForecast
    import ForecastHandler
    import ForecastSet

    import pandas as pd
    from sqlalchemy import create_engine
    import AccountSet
    import BudgetSet
    import MemoRuleSet
    import AccountMilestone
    import MemoMilestone
    import CompositeMilestone
    import MilestoneSet

    F = ForecastHandler.ForecastHandler()

    # print('ARGS:')
    # print(args)

    ### up front validations
    # always valid: --verbose, --log-directory

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

    assert len(args.action) <= 2
    assert args.action[0] in ['parameterize','run','list','ps','kill','report','export','import']
    if args.action[0] in ['parameterize','run','kill','report','export','import']:
        assert len(args.action) == 2
        assert args.action[1] in ['forecast','forecastset']

    if args.action[0] in ['list', 'kill', 'ps']:
        assert args.database_hostname is None
        assert args.database_name is None
        assert args.database_username is None
        assert args.database_port is None
        assert args.database_password is None

    if args.action[0] in ['parameterize']:
        assert args.filename is not None

    if args.action[0] in ['parameterize','run','report','export']:
        assert args.output_directory is not None
        assert os.path.isdir(args.output_directory)

    if args.action[0] in ['export','import']:
        assert args.database_hostname is not None
        assert args.database_name is not None
        assert args.database_username is not None
        assert args.database_port is not None
        assert args.database_password is not None

    if args.output_directory is not None:
        assert os.path.isdir(args.output_directory)
        assert args.action[0] in ['parameterize','run','report','export']

    #parameterize and reparameterize require start and end date
    if args.action[0] in ['parameterize', 'reparameterize']:
        assert args.start_date is not None
        assert args.end_date is not None

    # the label arg is only valid when used with parameterize and reparameterize
    if args.label is not None:
        assert args.action[0] in ['parameterize']

    assert os.path.isdir(args.log_directory) #check log_directory exists
    assert os.access(args.log_directory,os.W_OK) #check log_directory is writable

    if args.id is not None:
        assert args.action[0] != 'parameterize'

    if args.approximate:
        assert args.action[0] == 'run'

    if args.overwrite:
        assert args.action[0] == 'run'

    if args.id is not None:
        assert args.action[0] in ['run','kill','report','export','import']

    if args.filename is not None:
        assert os.access(args.filename, os.R_OK)  # check input file is readable

    #if any database args are defined, they must all be defined
    if args.database_hostname is not None or args.database_name is not None or args.database_username is not None or args.database_port is not None or args.database_password is not None:
        assert args.database_hostname is not None
        assert args.database_name is not None
        assert args.database_username is not None
        assert args.database_port is not None
        assert args.database_password is not None

        # try to connect
        connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
        engine = create_engine(connect_string)
        connection_test = pd.read_sql_query("select 'connection successful'", con=engine)

        assert args.action[0] in ['parameterize','export','import','run','report']

    if args.start_date is not None:
        datetime.datetime.strptime(args.start_date,'%Y%m%d') #will raise an exception if there is a problem

    if args.end_date is not None:
        datetime.datetime.strptime(args.end_date,'%Y%m%d')

    #print('Passed all validation tests')
    if len(args.action) == 1:
        pass

    if len(args.action) == 2:
        if args.action[0] == 'parameterize' and args.action[1] == 'forecast':
            E = ExpenseForecast.initialize_from_json_file(args.filename) #let this throw an exception if needed
            E.update_date_range(args.start_date,args.end_date)
            if args.label:
                E.forecast_name = args.label
            # print(E)
            E.writeToJSONFile('./out/')

        if args.action[0] == 'parameterize' and args.action[1] == 'forecastset':
            #print('Initializing')
            S = ForecastSet.initialize_from_json_file(args.filename) #let this throw an exception if needed
            #print('Updating')

            # for E_id, E in S.initialized_forecasts.items():
            #     print(E_id)

            S.update_date_range(args.start_date,args.end_date)
            #print('-----------')

            # for E_id, E in S.initialized_forecasts.items():
            #     print(E_id)

            #print('Naming')
            if args.label:
                S.forecast_set_name = args.label
            # print(S)
            #print('Writing')
            S.writeToJSONFile('./out/')
            #print('Done')

    # if args.action == 'run' and args.source == 'database' and args.target_type == 'stage':
    #     connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
    #     engine = create_engine(connect_string)
    #     # engine = create_engine('postgresql://bsdegjmy_humedick@localhost:5432/bsdegjmy_sandbox')
    #
    #     forecast_stage_table_name = 'prod.' + args.username + '_staged_forecast_details'
    #     forecast_stage_df = pd.read_sql_query('select * from ' + forecast_stage_table_name, con=engine)
    #
    #     account_set_table_name = 'prod.ef_account_set_' + args.username
    #     budget_set_table_name='prod.ef_budget_item_set_'+args.username
    #     memo_rule_set_table_name = 'prod.ef_memo_rule_set_' + args.username
    #     account_milestone_table_name = 'prod.ef_account_milestones_' + args.username
    #     memo_milestone_table_name = 'prod.ef_memo_milestones_' + args.username
    #     composite_milestone_table_name = 'prod.ef_composite_milestones_' + args.username
    #
    #     for index, row in forecast_stage_df.iterrows():
    #         forecast_id = row.forecast_id
    #         start_date = row.start_date
    #         end_date = row.end_date
    #         forecast_set_name = row.forecast_set_name
    #         forecast_name = row.forecast_name
    #         A_q = 'select * from ' + account_set_table_name + ' where forecast_id = \''+forecast_id+'\''
    #         B_q = 'select * from ' + budget_set_table_name + ' where forecast_id = \''+forecast_id+'\''
    #         M_q = 'select * from ' + memo_rule_set_table_name + ' where forecast_id = \''+forecast_id+'\''
    #         AM_q = 'select * from ' + account_milestone_table_name + ' where forecast_id = \''+forecast_id+'\''
    #         MM_q = 'select * from ' + memo_milestone_table_name + ' where forecast_id = \''+forecast_id+'\''
    #         CM_q = 'select * from ' + composite_milestone_table_name + ' where forecast_id = \''+forecast_id+'\''
    #         A = AccountSet.initialize_from_dataframe(pd.read_sql_query(A_q, con=engine))
    #         B = BudgetSet.initialize_from_dataframe(pd.read_sql_query(B_q, con=engine))
    #         M = MemoRuleSet.initialize_from_dataframe(pd.read_sql_query(M_q, con=engine))
    #         AM_df = pd.read_sql_query(AM_q, con=engine)
    #         MM_df = pd.read_sql_query(MM_q, con=engine)
    #         CM_df = pd.read_sql_query(CM_q, con=engine)
    #         MS = MilestoneSet.initialize_from_dataframe(AM_df, MM_df, CM_df)
    #         E = ExpenseForecast.ExpenseForecast(A, B, M, start_date, end_date, MS, args.log_directory, forecast_set_name, forecast_name)
    #         log_in_color(logger, 'white', 'info', E)
    #         if args.approximate:
    #             E.runForecastApproximate()
    #         else:
    #             E.runForecast()
    #
    #         E.appendSummaryLines()
    #         E.writeToJSONFile(args.output_directory)
    #         E.write_to_database(args.username,args.database_hostname, args.database_name, args.database_username, args.database_password, args.database_port, overwrite=args.force)
    #         E.forecast_df.to_csv(args.output_directory+'/Forecast_'+str(E.unique_id)+'.csv',index=False)
    #         log_in_color(logger, 'green', 'info','Finished writing forecast data to ' + args.output_directory+'/Forecast_'+str(E.unique_id)+'.csv')
    #         F.generateHTMLReport(E, args.output_directory)
    # elif args.action == 'list' and args.source == 'database' and args.target_type == 'stage':
    #     pass







    # if (args.source.lower() == 'DATABASE') and args.run_scenarios:
    #     logging.info('Running SCENARIOS based on data from database')
    #     base_E = ExpenseForecast.initialize_from_database(args.start_date,
    #                                                  args.end_date,
    #                                                  account_set_table_name='prod.ef_account_set_' + args.username + '_temporary',
    #                                                  budget_set_table_name='prod.ef_budget_item_set_' + args.username + '_temporary',
    #                                                  memo_rule_set_table_name='prod.ef_memo_rule_set_' + args.username + '_temporary',
    #                                                  account_milestone_table_name='prod.ef_account_milestones_' + args.username + '_temporary',
    #                                                  memo_milestone_table_name='prod.ef_memo_milestones_' + args.username + '_temporary',
    #                                                  composite_milestone_table_name='prod.ef_composite_milestones_' + args.username + '_temporary',
    #                                                  database_hostname=args.database_hostname,
    #                                                  database_name=args.database_name,
    #                                                  database_username=args.database_username,
    #                                                  database_password=args.database_password,
    #                                                  database_port=args.database_port,
    #                                                  log_directory=args.log_directory,
    #                                                  forecast_set_name=args.setname,
    #                                                  forecast_name=args.name
    #                                                  )
    #     A = base_E.initial_account_set
    #     M = base_E.initial_memo_rule_set
    #     start_date_YYYYMMDD = base_E.start_date_YYYYMMDD
    #     end_date_YYYYMMDD = base_E.end_date_YYYYMMDD
    #     MS = base_E.milestone_set
    #
    #     core_budget_set = base_E.initial_budget_set
    #
    #     connect_string = 'postgresql://' + args.database_username + ':' + args.database_password + '@' + args.database_hostname + ':' + args.database_port + '/' + args.database_name
    #     engine = create_engine(connect_string)
    #     # engine = create_engine('postgresql://bsdegjmy_humedick@localhost:5432/bsdegjmy_sandbox')
    #     option_budget_set_table_name = 'prod.ef_budget_item_set_optional_'+args.username+'_temporary'
    #     option_budget_set = BudgetSet.initialize_from_dataframe(pd.read_sql_query('select * from '+option_budget_set_table_name, con=engine))
    #
    #     S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)
    #
    #     scenario_table_name = 'prod.scenario_' + args.username + '_temporary'
    #     scenarios_df = pd.read_sql_query('select * from ' + scenario_table_name, con=engine)
    #
    #     choice_option_map = {}
    #     option_name_to_memo_regex_list_map = {}
    #     for index, row in scenarios_df.iterrows():
    #         if row.choice_name not in choice_option_map:
    #             choice_option_map[row.choice_name] = []
    #         if row.option_name not in choice_option_map[row.choice_name]:
    #             choice_option_map[row.choice_name].append(row.option_name)
    #
    #             # this is semicolon separated instead of a list
    #             option_name_to_memo_regex_list_map[row.choice_name+' | '+row.option_name] = row.memo_regexes
    #
    #     for choice_name, option_name_list in choice_option_map.items():
    #         list_of_lists_of_memo_regexes = []
    #         for option_name in option_name_list:
    #             list_of_lists_of_memo_regexes.append(option_name_to_memo_regex_list_map[choice_name + ' | ' + option_name].split(';'))
    #         S.addChoiceToAllScenarios(option_name_list, list_of_lists_of_memo_regexes)
    #
    #     print(S)
    #     E__dict = F.initialize_forecasts_with_scenario_set(A, S, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
    #     for key, value in E__dict.items():
    #         print('-------------------------------------------------------')
    #         print(value.unique_id)
    #
    #     result_dict = F.run_forecast_set_parallel(E__dict)
    #     print('-------------------------------------------------------')
    #     print('-------------------------------------------------------')
    #     for key, value in result_dict.items():
    #         print(value)
    #         print('-------------------------------------------------------')
    #         print('-------------------------------------------------------')
    #
    #
    #     for forecast_id, E in result_dict.items():
    #         E.appendSummaryLines()
    #         E.writeToJSONFile(args.output_directory)
    #         E.write_to_database(args.username, args.database_hostname, args.database_name, args.database_username,
    #                             args.database_password, args.database_port, args.force)
    #         E.forecast_df.to_csv(args.output_directory + '/Forecast_' + str(E.unique_id) + '.csv', index=False)
    #         log_in_color(logger, 'green', 'info',
    #                      'Finished writing forecast data to ' + args.output_directory + '/Forecast_' + str(E.unique_id) + '.csv')
    #         F.generateHTMLReport(E, args.output_directory)
    #
    # elif (args.source.lower() == 'database' or args.source.lower() == 'db') and not args.run_scenarios:
    #     logging.info('Running based on data from database')
    #     E = ExpenseForecast.initialize_from_database(args.start_date,
    #                          args.end_date,
    #                          account_set_table_name='prod.ef_account_set_'+args.username+'_temporary',
    #                          budget_set_table_name='prod.ef_budget_item_set_'+args.username+'_temporary',
    #                          memo_rule_set_table_name='prod.ef_memo_rule_set_'+args.username+'_temporary',
    #                          account_milestone_table_name='prod.ef_account_milestones_'+args.username+'_temporary',
    #                          memo_milestone_table_name='prod.ef_memo_milestones_'+args.username+'_temporary',
    #                          composite_milestone_table_name='prod.ef_composite_milestones_'+args.username+'_temporary',
    #                          database_hostname=args.database_hostname,
    #                          database_name=args.database_name,
    #                          database_username=args.database_username,
    #                          database_password=args.database_password,
    #                          database_port=args.database_port,
    #                          log_directory=args.log_directory,
    #                                                  forecast_set_name=args.forecast_set_name,
    #                                                  forecast_name=args.forecast_name
    #                          )
    #     log_in_color(logger, 'white', 'info', E)
    #     if args.approximate:
    #         E.runForecastApproximate()
    #     else:
    #         E.runForecast()
    #
    #     E.appendSummaryLines()
    #     E.writeToJSONFile(args.output_directory)
    #     E.write_to_database(args.username,args.database_hostname, args.database_name, args.database_username, args.database_password, args.database_port, overwrite=args.force)
    #     E.forecast_df.to_csv(args.output_directory+'/Forecast_'+str(E.unique_id)+'.csv',index=False)
    #     log_in_color(logger, 'green', 'info','Finished writing forecast data to ' + args.output_directory+'/Forecast_'+str(E.unique_id)+'.csv')
    #     F.generateHTMLReport(E, args.output_directory)
    # elif args.source.lower() == 'file' and not args.run_scenarios:
    #     logging.info('Running based on data from file')
    #     logging.info("Input: %s" % args.input_path)
    #     logging.info("Output directory: %s" % args.output_directory)
    #     E = ExpenseForecast.initialize_from_json_file(args.input_path)[0]
    #     if args.approximate:
    #         E.runForecastApproximate()
    #     else:
    #         E.runForecast()
    #     E.appendSummaryLines()
    #     E.writeToJSONFile(args.output_directory)
    #     E.forecast_df.to_csv(args.output_directory + '/Forecast_' + str(E.unique_id) + '.csv',index=False)
    # elif args.source.lower() == 'file' and args.run_scenarios:
    #     logging.error('--run_scenarios not implemented for file yet')
    # else:
    #     logging.error('--source did not match DATABASE or FILE')

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
                                 'reparameterize',
                                 'run',
                                 'list',
                                 'ps',
                                 'kill',
                                 'report',
                                 'export',
                                 'import',
                                 'forecast',
                                 'forecastset',
                                 ])
    parser.add_argument(
        "--filename",
        required=False,
        help="Path of Forecast or ForecastSet excel, JSON file or table to process.",
        action="store")
    parser.add_argument(
        "--output_directory",
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
        required=True,
        help="username for filter on temp tables for running based on db data",
        action="store")
    # parser.add_argument(
    #     "--source",
    #     choices=['file','database'],
    #     required=True,
    #     help="run based on input from file or from database. value FILE or DATABASE",
    #     action="store")
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

    # database_hostname=args.database_hostname,
    #                              database_name=args.database_name,
    #                              database_username=args.database_username,
    #                              database_password=args.database_password,
    #                              database_port=args.database_port


    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARNING

    main(args, loglevel)