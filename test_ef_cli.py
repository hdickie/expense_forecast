import pytest
import subprocess
import ExpenseForecast
import BudgetSet
import AccountSet
import MemoRuleSet
import MilestoneSet
import datetime
import ForecastSet

#import ef_cli #these tests should be carried out with subprocess

## db details, output_directory optional for these
#  1. ef_cli parameterize forecast --filename FILE_NAME --start_date START_DATE --end_date END_DATE --username USERNAME
#  2. ef_cli parameterize forecast --filename FILE_NAME --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
#  3. ef_cli parameterize forecastset --filename FILE_NAME --start_date START_DATE --end_date END_DATE --username USERNAME
#  4. ef_cli parameterize forecastset --filename FILE_NAME --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
#  5. ef_cli parameterize forecast --id FORECAST_ID --start_date START_DATE --end_date END_DATE --username USERNAME
#  6. ef_cli parameterize forecast --id FORECAST_ID --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
#  7. ef_cli parameterize forecastset --id FORECAST_ID --start_date START_DATE --end_date END_DATE --username USERNAME
#  8. ef_cli parameterize forecastset --id FORECAST_ID --start_date START_DATE --end_date END_DATE --label LABEL --username USERNAME
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

### Names
# 1. parameterize_file_forecast_no_label                X
# 2. parameterize_file_forecast_with_label              X
# 3. parameterize_file_forecastset_no_label             X
# 4. parameterize_file_forecastset_with_label           X
# 5. parameterize_db_forecast_no_label                  O
# 6. parameterize_db_forecast_with_label                O
# 7. parameterize_db_forecastset_no_label               O
# 8. parameterize_db_forecastset_with_label             O
# 9. run_forecast                                       X
# 10. run_forecastset                                   X
# 11. run_approximate_forecast                          O
# 12. run_approximate_forecastset                       O
# 13. run_forecast_overwrite                            O
# 14. run_forecastset_overwrite                         O
# 15. run_overwrite_approximate_forecast                0
# 16. run_overwrite_approximate_forecastset             0
# 17. report_forecast                                   X
# 18. report_forecastset                                X
# 19. export_forecast                                   O
# 20. export_forecastset                                O
# 21. import_forecast                                   O
# 22. import_forecastset                                O
# 23. list                                              X
# 24. ps                                                O
# 24. kill forecast                                     O
# 24. kill forecastset                                  O

start_date = datetime.datetime.now().strftime('%Y%m%d')
end_date = '20241110'

A = AccountSet.AccountSet([])
B1 = BudgetSet.BudgetSet([])
B2 = BudgetSet.BudgetSet([])
B3 = BudgetSet.BudgetSet([])
B4 = BudgetSet.BudgetSet([])
B5 = BudgetSet.BudgetSet([])
M = MemoRuleSet.MemoRuleSet([])

A.createCheckingAccount('Checking', 5000, 0, 99999)
B1.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 1', False, False)
B2.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 2', False, False)
B3.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 3', False, False)
B4.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 4', False, False)
B5.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 5', False, False)
M.addMemoRule('.*', 'Checking', 'None', 1)

MS = MilestoneSet.MilestoneSet([], [], [])
E1 = ExpenseForecast.ExpenseForecast(A, B1, M, start_date, end_date, MS) #031987
E2 = ExpenseForecast.ExpenseForecast(A, B2, M, start_date, end_date, MS) #093122
E3 = ExpenseForecast.ExpenseForecast(A, B3, M, start_date, end_date, MS) #051928
E4 = ExpenseForecast.ExpenseForecast(A, B4, M, start_date, end_date, MS) #064210
E5 = ExpenseForecast.ExpenseForecast(A, B5, M, start_date, end_date, MS) #052438

class TestEFCLIMethods:

    @pytest.mark.parametrize('cmd_string',
                             [('cmd_string'),
                              ])
    def test_help(self, cmd_string):
        cmd = "python -m ef_cli "+cmd_string
        cmd_arg_list = cmd.split(" ")
        completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)
        for l in completed_process.stderr.splitlines():
            print(l)

    @pytest.mark.parametrize('cmd_string',
                             [('parameterize forecast --id 031987 --source file --start_date 20240101 --end_date 20241231 --username hume --log_directory ./out/'),
                              ])
    def test_parameterize_file_forecast_no_label(self, cmd_string):
        cmd = "python -m ef_cli " + cmd_string
        cmd_arg_list = cmd.split(" ")
        completed_process = subprocess.run(cmd_arg_list, capture_output=True)

        #the change in date range will change the id to ForecastResult_032472.json, which should load successfully
        E = ExpenseForecast.initialize_from_json_file('./out/ForecastResult_032472.json')
        assert E.start_date_YYYYMMDD == '20240101'
        assert E.end_date_YYYYMMDD == '20241231'

    @pytest.mark.parametrize('cmd_string',
                             [(
                              'parameterize forecast --id 031987 --source file --start_date 20240101 --end_date 20241231 --username hume --log_directory ./out/ --label FORECAST_LABEL'),
                              ])
    def test_parameterize_file_forecast_with_label(self, cmd_string):
        cmd = "python -m ef_cli " + cmd_string
        cmd_arg_list = cmd.split(" ")
        completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)

        # the change in date range will change the id to ForecastResult_032472.json, which should load successfully
        E = ExpenseForecast.initialize_from_json_file('./out/ForecastResult_032472.json')
        print(E)
        assert E.start_date_YYYYMMDD == '20240101'
        assert E.end_date_YYYYMMDD == '20241231'
        assert E.forecast_name == 'FORECAST_LABEL'

    @pytest.mark.parametrize('cmd_string',
                             [('parameterize forecastset --source file --id S --username hume --output_directory ./out/ --start_date 20240120 --end_date 20240601'),
                              ('parameterize forecastset --source file --id S --username hume --output_directory ./out/ --start_date 20000120 --end_date 20000601'),
                              ('parameterize forecastset --source file --id S --username hume --output_directory ./out/ --start_date 20240420 --end_date 20240601')
                              ])
    def test_parameterize_file_forecastset_no_label(self, cmd_string):
        cmd = "python -m ef_cli " + cmd_string
        cmd_arg_list = cmd.split(" ")
        sd = cmd_arg_list[12]
        ed = cmd_arg_list[14]
        completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)
        for l in completed_process.stdout.splitlines():
            if 'Writing to ' in str(l):
                output_file_path = str(l)[13:44] #not robust at all

        S = ForecastSet.initialize_from_json_file(output_file_path)
        # print(output_file_path)
        # print(S)
        assert S.base_forecast.start_date_YYYYMMDD == sd
        assert S.base_forecast.end_date_YYYYMMDD == ed
        for unique_id, E in S.initialized_forecasts.items():
            assert E.start_date_YYYYMMDD == sd
            assert E.end_date_YYYYMMDD == ed

    @pytest.mark.parametrize('cmd_string',
                             [(
                              'parameterize forecastset --filename S.json --start_date 20000601 --end_date 20001231 --username hume --label NEW_FORECAST_SET_NAME'),
                              ])
    def test_parameterize_file_forecastset_with_label(self, cmd_string):
        cmd = "python -m ef_cli " + cmd_string
        cmd_arg_list = cmd.split(" ")
        completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)

        S = ForecastSet.initialize_from_json_file('./out/ForecastSet_S074621.json')

        for unique_id, E in S.initialized_forecasts.items():
            assert E.start_date_YYYYMMDD == '20000601'
            assert E.end_date_YYYYMMDD == '20001231'

        assert S.forecast_set_name == 'NEW_FORECAST_SET_NAME'

    @pytest.mark.parametrize('cmd_string',
                             [('run forecast --id 062822 --source file --username hume --working_directory ./out/'),
                              ('run forecast --id 062822 --source file --username hume --working_directory ./out/ --approximate'),
                              ('run forecast --id 062822 --source file --username hume --working_directory ./out/ --overwrite'),
                              ('run forecast --id 062822 --source file --username hume --working_directory ./out/ --approximate --overwrite'),
                             ])
    def test_run_forecast(self, cmd_string):
        cmd = "python -m ef_cli " + cmd_string
        cmd_arg_list = cmd.split(" ")
        completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)

        E = ExpenseForecast.initialize_from_json_file('./out/ForecastResult_094984.json')
        E.runForecast()
        E.appendSummaryLines()
        E.writeToJSONFile('./out/')

    @pytest.mark.parametrize('cmd_string',
                             [('run forecastset --source file --id S033683 --username hume --working_directory ./out/'),
                              ('run forecastset --source file --id S033683 --username hume --working_directory ./out/ --approximate'),
                              ('run forecastset --source file --id S033683 --username hume --working_directory ./out/ --overwrite'),
                              ('run forecastset --source file --id S033683 --username hume --working_directory ./out/ --approximate --overwrite'),
                             ])
    def test_run_forecastset(self, cmd_string):
        cmd = "python -m ef_cli " + cmd_string
        cmd_arg_list = cmd.split(" ")
        completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)

        S = ForecastSet.initialize_from_json_file('S.json')
        for unique_id, E in S.initialized_forecasts.items():
            assert E.forecast_df is None
        S.runAllForecasts()
        for unique_id, E in S.initialized_forecasts.items():
            assert not E.forecast_df is None

    @pytest.mark.parametrize('cmd_string',
                             [('list'),
                              ])
    def test_list(self, cmd_string):
        cmd = "python -m ef_cli " + cmd_string
        cmd_arg_list = cmd.split(" ")
        completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)

        for l in completed_process.stdout.splitlines():
            print(l)

