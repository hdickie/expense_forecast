#!/usr/bin/env python
# Thanks to opie4624 from Github:  https://gist.github.com/opie4624/3896526

# import modules used here -- sys is a very standard one
import sys, argparse, logging
from log_methods import log_in_color
from log_methods import setup_logger
logger = setup_logger('ef_cli', './log/ef_cli.log', level=logging.DEBUG)

sys.path.append('/Users/hume/Github/expense_forecast')
import ExpenseForecast
import ForecastHandler

import os

# Gather our code in a main() function
def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    if args.output_directory is None:
        output_dir = '.'
    else:
        output_dir = args.output_directory
    #os.environ['MPLCONFIGDIR'] = args.output_directory

    F = ForecastHandler.ForecastHandler()

    if args.source.lower() == 'database' or args.source.lower() == 'db':
        logging.info('Running based on data from database')
        E = ExpenseForecast.initialize_from_database(args.begin,
                             args.end,
                             account_set_table_name='prod.ef_account_set_'+args.username+'_temporary',
                             budget_set_table_name='prod.ef_budget_item_set_'+args.username+'_temporary',
                             memo_rule_set_table_name='prod.ef_memo_rule_set_'+args.username+'_temporary',
                             account_milestone_table_name='prod.ef_account_milestones_'+args.username+'_temporary',
                             memo_milestone_table_name='prod.ef_memo_milestones_'+args.username+'_temporary',
                             composite_milestone_table_name='prod.ef_composite_milestones_'+args.username+'_temporary',
                             database_hostname=args.database_hostname,
                             database_name=args.database_name,
                             database_username=args.database_username,
                             database_password=args.database_password,
                             database_port=args.database_port
                             )
        E.runForecast()
        E.appendSummaryLines()
        E.writeToJSONFile(output_dir)
        E.write_to_database(args.username,args.database_hostname, args.database_name, args.database_username, args.database_password, args.database_port, args.force)
        E.forecast_df.to_csv(output_dir+'/Forecast_'+str(E.unique_id)+'.csv',index=False)
        log_in_color(logger, 'green', 'info','Finished writing forecast data to ' + output_dir+'/Forecast_'+str(E.unique_id)+'.csv')
        F.generateHTMLReport(E, output_dir)
    elif args.source.lower() == 'file':
        logging.info('Running based on data from file')
        logging.info("Input: %s" % args.input_path)
        logging.info("Output directory: %s" % args.output_directory)
        E = ExpenseForecast.initialize_from_json_file(args.input_path)[0]
        E.runForecast()
        E.appendSummaryLines()
        E.writeToJSONFile(output_dir)
        E.forecast_df.to_csv(output_dir + '/Forecast_' + str(E.unique_id) + '.csv',index=False)
    else:
        logging.error('--source did not match DATABASE or FILE')

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Runs a Forecast or ForecastSet and displays a progress bar.",
        epilog="As an alternative to the commandline, params can be placed in a file, one per line, and specified on the commandline like '%(prog)s @params.conf'.",
        fromfile_prefix_chars='@')
    parser.add_argument(
        "-i",
        "--input_path",
        help="File path of Forecast or ForecastSet JSON file to run",
        action="store")
    parser.add_argument(
        "-o",
        "--output_directory",
        help="Output directory for JSON and HTML documents to be output.",
        action="store")
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true")
    parser.add_argument(
        "-u",
        "--username",
        help="username for filter on temp tables for running based on db data",
        action="store")
    parser.add_argument(
        "-s",
        "--source",
        help="run based on input from file or from database. value FILE or DATABASE",
        action="store")
    parser.add_argument(
        "-b",
        "--begin",
        help="start_date_YYYYMMDD",
        action="store")
    parser.add_argument(
        "-e",
        "--end",
        help="end_date_YYYYMMDD",
        action="store")
    parser.add_argument(
        "-f",
        "--force",
        help="Overwrite output data if present.",
        action="store_true")





    parser.add_argument(
        #"-",
        "--database_hostname",
        help="database hostname",
        action="store")
    parser.add_argument(
        #"-e",
        "--database_name",
        help="database name",
        action="store")
    parser.add_argument(
        #"-e",
        "--database_username",
        help="database username",
        action="store")
    parser.add_argument(
        #"-e",
        "--database_password",
        help="database password",
        action="store")
    parser.add_argument(
        #"-e",
        "--database_port",
        help="database port",
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