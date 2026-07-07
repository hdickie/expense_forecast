import pandas as pd

import re
import copy
from .BudgetSet import BudgetSet
import logging
import json
from pathlib import Path
from .ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ScenarioSpace import ScenarioSpace
from .ExpenseForecastResult import ExpenseForecastResult
from .MilestoneSet import MilestoneSet
from .log_methods import log_in_color
import os

# logger = setup_logger('ForecastSet', './log/ForecastSet.log', level=logging.WARNING)
# logger = logging.getLogger(__name__)
from sqlalchemy import create_engine
import hashlib
import psycopg2
import datetime

# thread_id = str(math.floor(random.random() * 1000))
# try:
#     logger = setup_logger(
#         __name__,
#         os.environ["EF_LOG_DIR"] + __name__ + "_" + thread_id + ".log",
#         level=logging.INFO,
#     )
# except KeyError:

logger = logging.getLogger(__name__)

def initialize_from_json_string(json_string):
    return ForecastSet.initialize_from_json_string(json_string)

def initialize_from_dict(data):
    return ForecastSet.initialize_from_dict(data)

def initialize_from_json_file(path_to_json):
    return ForecastSet.initialize_from_json_file(path_to_json)

def initialize_forecast_set_from_database(
    set_id,
    username,
    database_hostname,
    database_name,
    database_username,
    database_password,
    database_port,
):
    # I hate this so much but the appropriate thing to do here is input validation and error checking
    # print('ENTER initialize_forecast_set_from_database set_id='+str(set_id))
    connect_string = (
        "postgresql://"
        + database_username
        + ":"
        + database_password
        + "@"
        + database_hostname
        + ":"
        + str(database_port)
        + "/"
        + database_name
    )
    engine = create_engine(connect_string)

    # here, we will assert that date range is same for all
    # as of 4/24, I acknowledge that #todo date range match for forecastset does not happen in JSON bc json.load just worked
    # but 'technically works' and 'makes consistent sense' are different and that does make me want to kill myself
    # but the definition of ForecastSet I have committed to is: same date range &, A, B, M
    # therefore, even if the loaded forecasts are valid on their own, we must reject the set if they don't match

    # set_id, id, set_name, name, start_date, end_date
    # forecast_stage_df = pd.read_sql_query("select * from prod.virtuoso_user_staged_forecast_details where forecast_set_id = '" + set_id + "'", con=engine)
    # assert forecast_stage_df.shape[0] > 0 #else there is no work to do (stage it to fix this error)ti
    # FInally after sleeping on it my brain came up with another solution: use forecast_set even for single forecasts
    # this makes stage unnecessary if we move names and start dates to forecast_set_definition
    # Yes, w the current implementation, start date and end date would be duplicate information
    # But, it doesn't HAVE to be in principal. Maybe 30, 60, 90 day forecasts are part of the same set?
    # Implementation of set identified would have to change but I have talked myself into this alternate implementation

    # username, forecast_set_id, forecast_id, insert_ts
    forecast_set_def_q = (
        "select * from prod."
        + username
        + "_forecast_set_definitions where forecast_set_id = '"
        + set_id
        + "'"
    )
    # print('username:')
    # print(username)
    # print('set_id:'+str(set_id))
    # print('forecast_set_def_q:')
    # print(forecast_set_def_q)
    forecast_set_definition_df = pd.read_sql_query(forecast_set_def_q, con=engine)
    # print('forecast_set_definition_df:')
    # print(forecast_set_definition_df.to_string())
    assert (
        forecast_set_definition_df.shape[0] > 0
    )  # else set has no definition (stage it to fix this error)

    forecast_set_name = forecast_set_definition_df["forecast_set_name"].iat[0]

    # option_budget_set (there may be 0 rows)
    option_budget_set_df = pd.read_sql_query(
        "select * from prod.ef_budget_item_set_"
        + username
        + " where forecast_id = 'O"
        + set_id
        + "'",
        con=engine,
    )
    option_budget_set = BudgetSet.initialize_from_dataframe(option_budget_set_df)

    initialized_forecasts = {}
    id_to_name = {}
    base_forecast = None
    # print('forecast_set_definition_df:')
    # print(forecast_set_definition_df.to_string())
    for index, row in forecast_set_definition_df.iterrows():
        # print('ForecastSet::initialize_forecast_set_from_database calling initialize_from_database_with_id')
        # print('row.forecast_set_id:'+row.forecast_set_id)
        # print('row.forecast_id:' + row.forecast_id)
        E = ExpenseForecast.initialize_from_database_with_id(
            username=username,
            forecast_set_id=row.forecast_set_id,
            forecast_id=row.forecast_id,
            database_hostname=database_hostname,
            database_name=database_name,
            database_username=database_username,
            database_password=database_password,
            database_port=database_port,
        )
        assert E.unique_id == row.forecast_id

        id_to_name[E.unique_id] = row.forecast_name
        if row.forecast_name.strip() == "Core":
            base_forecast = E
        else:
            initialized_forecasts[E.unique_id] = E

    assert base_forecast is not None
    S = ForecastSet(
        base_forecast, option_budget_set, initialized_forecasts, forecast_set_name
    )
    S.id_to_name = id_to_name
    # print('ForecastSet::initialize_forecast_set_from_database unique_id = ' + S.unique_id)
    return S

# new id format: e.g. 042424_90_####_1_A.json
# April 24, 2024 90 days, scenario #1, approximate
# new id format: e.g. 042424_90_####_0.json (0 is always base forecast or forecast doesnt belong to set)
# April 24, 2024 90 days
class ForecastSetInitialConditions:

    @staticmethod
    def _stable_hash(values):
        return str(
            int(hashlib.sha1(str(sorted(values)).encode("utf-8")).hexdigest(), 16)
            % 1000
        ).rjust(4, "0")

    @staticmethod
    def _scenario_id_parts(base_forecast):
        return [
            base_forecast.unique_id.split("_")[0],
            base_forecast.unique_id.split("_")[1],
            base_forecast.unique_id.split("_")[2],
        ]

    @classmethod
    def _load_initial_conditions(cls, data):
        if isinstance(data, ExpenseForecastInitialConditions):
            return data
        return ExpenseForecastInitialConditions.initialize_from_dict(data)

    @classmethod
    def _load_result(cls, data):
        if isinstance(data, ExpenseForecastResult):
            return data
        return ExpenseForecastResult.initialize_from_dict(data)

    @classmethod
    def _load_budget_set(cls, data):
        if isinstance(data, BudgetSet):
            return data
        if data is None:
            return BudgetSet()
        return ExpenseForecastInitialConditions._budget_set_from_dict(data)

    @classmethod
    def initialize_from_json_string(cls, json_string):
        return cls.initialize_from_dict(json.loads(json_string))

    @classmethod
    def initialize_from_json_file(cls, path_to_json):
        return cls.initialize_from_dict(json.loads(Path(path_to_json).read_text()))

    @classmethod
    def initialize_from_dict(cls, data):
        base_forecast = cls._load_initial_conditions(data["base_forecast"])
        option_budget_set = cls._load_budget_set(data.get("option_budget_set"))
        initialized_forecasts = {
            forecast_id: cls._load_initial_conditions(forecast_data)
            for forecast_id, forecast_data in data.get("initialized_forecasts", {}).items()
        }
        forecast_results = {
            forecast_id: cls._load_result(result_data)
            for forecast_id, result_data in data.get("forecast_results", {}).items()
        }

        forecast_set = cls(
            base_forecast=base_forecast,
            option_budget_set=option_budget_set,
            initialized_forecasts=initialized_forecasts,
            forecast_set_name=data.get("forecast_set_name", ""),
        )
        forecast_set.forecast_results = forecast_results
        forecast_set.id_to_name.update(data.get("id_to_name", {}))
        forecast_set.unique_id = data.get("unique_id", forecast_set.unique_id)
        return forecast_set

    def _validate_initial_conditions_and_scenario_space_are_compatible(self, 
                                                                                     initial_conditions: ExpenseForecastInitialConditions, 
                                                                                     scenario_space: ScenarioSpace):
        
        raise NotImplementedError

    def __init__(
        self,
        E_IO: ExpenseForecastInitialConditions,
        scenario_space: ScenarioSpace,
        forecast_set_name="",
    ):

        self._validate_initial_conditions_and_scenario_space_are_compatible(E_IO, 
                                                                            scenario_space)
        self.scenario_space = scenario_space
        self.initial_conditions = E_IO


        base_forecast.forecast_name = "Core"
        self.base_forecast = base_forecast

        self.core_budget_set = base_forecast.initial_budget_set
        self.option_budget_set = option_budget_set or BudgetSet()

        intersection = pd.merge(
            self.core_budget_set.getBudgetItems(),
            self.option_budget_set.getBudgetItems(),
            how="inner",
        )
        if not intersection.empty:
            raise ValueError("overlap detected in Core and Option Budgetsets")

        self.forecast_set_name = forecast_set_name

        # keys are forecast_name
        # self.forecast_name_to_budget_item_set__dict = {}
        self.initialized_forecasts = initialized_forecasts
        self.forecast_results = {}
        self.id_to_name = {}
        self.id_to_name[base_forecast.unique_id] = "Core"
        for forecast_id, forecast in self.initialized_forecasts.items():
            forecast_name = forecast.forecast_name or forecast_id
            self.id_to_name[forecast_id] = forecast_name

        # apparently this is not correct
        # self.initialized_forecasts[base_forecast.unique_id] = base_forecast

        id_sd, id_num_days, id_distinct_p = self._scenario_id_parts(self.base_forecast)
        id_set_hash = self._stable_hash(list(self.initialized_forecasts.keys()))
        self.unique_id = (
            "S"
            + str(id_sd)
            + "_"
            + str(id_num_days)
            + "_"
            + str(id_distinct_p)
            + "_"
            + str(id_set_hash)
        )

    def writeToDatabase(
        self,
        database_hostname,
        database_name,
        database_username,
        database_password,
        database_port,
        username,
        overwrite=True,
    ):
        # print('writeToDatabase')
        # print("\n")
        connection = psycopg2.connect(
            host=database_hostname,
            database=database_name,
            user=database_username,
            password=database_password,
            port=str(database_port),
        )
        connection.autocommit = True
        cursor = connection.cursor()

        # todo check for overwrites up front to prevent duplicated work

        log_in_color(
            logger,
            "green",
            "info",
            "Writing base forecast "
            + str(self.base_forecast.unique_id)
            + " to database for forecast set "
            + str(self.unique_id),
        )
        cursor.execute(
            "DELETE FROM prod."
            + username
            + "_forecast_set_definitions WHERE forecast_set_id = '"
            + str(self.unique_id)
            + "'"
        )

        # # insert set definition row for base forecast
        assert self.base_forecast.forecast_name == "Core"
        core_set_def_q = (
            "INSERT INTO prod."
            + username
            + "_forecast_set_definitions SELECT '"
            + self.unique_id
            + "' as forecast_set_id, "
        )
        core_set_def_q += (
            "'"
            + self.forecast_set_name
            + "' as forecast_set_name, '"
            + str(self.base_forecast.unique_id)
            + "' as forecast_id, '"
        )
        core_set_def_q += (
            str(self.base_forecast.forecast_name)
            + "' as forecast_name, '"
            + self.base_forecast.start_date_YYYYMMDD
            + "' as start_date, "
        )
        core_set_def_q += (
            "'" + self.base_forecast.end_date_YYYYMMDD + "' as end_date, '"
        )
        core_set_def_q += (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "' as insert_ts"
        )
        # print(core_set_def_q)
        cursor.execute(core_set_def_q)

        # todo _forecast_run_metadata start_ts and end_ts

        self.base_forecast.write_to_database(
            database_hostname=database_hostname,
            database_name=database_name,
            database_username=database_username,
            database_password=database_password,
            database_port=database_port,
            username=username,
            overwrite=overwrite,
        )

        # This is base_forecast
        # cursor.execute(
        #     "DELETE FROM " + account_set_table_name + " WHERE forecast_id = \'" + str(self.base_forecast.unique_id) + "\'")
        # for index, row in self.base_forecast.initial_account_set.getAccounts().iterrows():
        #     if row.Billing_Start_Date is None:
        #         bsd = "Null"
        #     else:
        #         bsd = "'" + str(row.Billing_Start_Date) + "'"
        #     if row.APR is None:
        #         apr = "Null"
        #     else:
        #         apr = "'" + str(row.APR) + "'"
        #     if row.Minimum_Payment is None:
        #         min_payment = "Null"
        #     else:
        #         min_payment = str(row.Minimum_Payment)
        #
        #     insert_account_row_q = "INSERT INTO " + account_set_table_name + " (forecast_id, account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) VALUES "
        #     insert_account_row_q += "('" + str(self.base_forecast.unique_id) + "', '" + str(row.Name) + "', " + str(
        #         row.Balance) + ", " + str(row.Min_Balance) + ", " + str(row.Max_Balance) + ", '" + str(
        #         row.Account_Type) + "', " + str(bsd) + ", " + apr + ", '" + str(
        #         row.Interest_Cadence) + "', " + min_payment + ", '" + str(row.Primary_Checking_Ind) + "')"
        #     cursor.execute(insert_account_row_q)
        #
        # cursor.execute("DELETE FROM " + budget_set_table_name + " WHERE forecast_id = \'" + str(self.base_forecast.unique_id) + "\'")
        # for index, row in self.base_forecast.initial_budget_set.getBudgetItems().iterrows():
        #     insert_budget_item_row_q = "INSERT INTO " + budget_set_table_name + " (forecast_id, memo, priority, start_date, end_date, cadence, amount, \"deferrable\", partial_payment_allowed) VALUES "
        #     insert_budget_item_row_q += "('" + str(self.base_forecast.unique_id) + "','" + str(row.Memo) + "'," + str(
        #         row.Priority) + ",'" + str(row.Start_Date) + "','" + str(row.End_Date) + "','" + str(
        #         row.Cadence) + "'," + str(row.Amount) + ",'" + str(row.Deferrable) + "','" + str(
        #         row.Partial_Payment_Allowed) + "')"
        #     cursor.execute(insert_budget_item_row_q)
        #
        # cursor.execute(
        #     "DELETE FROM " + memo_rule_set_table_name + " WHERE forecast_id = \'" + str(self.base_forecast.unique_id) + "\'")
        # for index, row in self.base_forecast.initial_memo_rule_set.getMemoRules().iterrows():
        #     insert_memo_rule_row_q = "INSERT INTO " + memo_rule_set_table_name + " (forecast_id, memo_regex, account_from, account_to, priority ) VALUES "
        #     insert_memo_rule_row_q += "('" + str(self.base_forecast.unique_id) + "','" + str(row.Memo_Regex) + "','" + str(
        #         row.Account_From) + "','" + str(row.Account_To) + "'," + str(row.Transaction_Priority) + ")"
        #     cursor.execute(insert_memo_rule_row_q)

        # note that if there are no rows for this, then nothing is written, which is indistinguishable from an error
        # print('Writing Budget Set to database:')
        forecast_id_for_budget_set = "O" + self.unique_id
        cursor.execute(
            "DELETE FROM prod.ef_budget_item_set_"
            + username
            + " WHERE forecast_id = '"
            + forecast_id_for_budget_set
            + "'"
        )
        for index, row in self.option_budget_set.getBudgetItems().iterrows():
            q = (
                "INSERT INTO prod.ef_budget_item_set_"
                + username
                + " SELECT '"
                + forecast_id_for_budget_set
                + "','"
            )
            q += (
                row.Memo
                + "',"
                + str(row.Priority)
                + ",'"
                + str(row.Start_Date)
                + "','"
                + str(row.End_Date)
                + "','"
            )
            q += (
                row.Cadence
                + "',"
                + str(row.Amount)
                + ","
                + str(row.Deferrable)
                + ","
                + str(row.Partial_Payment_Allowed)
            )
            cursor.execute(q)

        # Base forecast should be a part of this
        for unique_id, E in self.initialized_forecasts.items():
            # print('Writing '+str(unique_id)+' to database')
            log_in_color(
                logger, "green", "info", "Writing " + str(unique_id) + " to database"
            )

            E.write_to_database(
                database_hostname=database_hostname,
                database_name=database_name,
                database_username=database_username,
                database_password=database_password,
                database_port=database_port,
                username=username,
                overwrite=overwrite,
            )

            # forecast_set_id, forecast_set_name, forecast_id, forecast_name, start_date, end_date, insert_ts
            insert_def_q = (
                "INSERT INTO prod."
                + str(username)
                + "_forecast_set_definitions SELECT '"
                + self.unique_id
                + "' as forecast_set_id, '"
            )
            insert_def_q += (
                self.forecast_set_name
                + "' as forecast_set_name, '"
                + E.unique_id
                + "' as forecast_id, '"
            )
            insert_def_q += (
                E.forecast_name
                + "' as forecast_name, '"
                + E.start_date_YYYYMMDD
                + "' as start_date, '"
            )
            insert_def_q += E.end_date_YYYYMMDD + "' as end_date, "
            insert_def_q += (
                "'"
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                + "' as insert_ts"
            )
            # print(insert_def_q)
            # print("\n")
            cursor.execute(insert_def_q)

            # forecast_name = self.id_to_name[E.unique_id]
            # insert_stage_q = "INSERT INTO prod." + str(username) + "_staged_forecast_details Select '" + str(
            #     self.unique_id) + "','" + str(E.unique_id) + "','" + str(self.forecast_set_name) + "','" + str(
            #     forecast_name) + "','" + str(E.start_date_YYYYMMDD) + "','" + str(E.end_date_YYYYMMDD) + "'"
            # cursor.execute(insert_stage_q)

    def initialize_forecast_set_from_json(self, path):
        raise NotImplementedError

    def initialize_forecast_set_from_excel(self, path):
        raise NotImplementedError

    def to_excel(self):
        raise NotImplementedError

    def to_dict(self):
        return {
            "unique_id": self.unique_id,
            "forecast_set_name": self.forecast_set_name,
            "id_to_name": self.id_to_name,
            "base_forecast": self.base_forecast.to_dict(),
            "core_budget_set": self.core_budget_set.to_dict(),
            "option_budget_set": self.option_budget_set.to_dict(),
            "initialized_forecasts": {
                forecast_id: forecast.to_dict()
                for forecast_id, forecast in self.initialized_forecasts.items()
            },
            "forecast_results": {
                forecast_id: result.to_dict()
                for forecast_id, result in self.forecast_results.items()
            },
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    # def initialize_forecasts(self):
    #     new_id_to_name = {}
    #     new_initialized_forecasts = {}
    #     for forecast_name, budget_set in self.forecast_name_to_budget_item_set__dict.items():
    #         #print('Initializing '+forecast_name)
    #         new_E = ExpenseForecast(account_set=self.base_forecast.initial_account_set,
    #                                                 budget_set=budget_set,
    #                                                 memo_rule_set=self.base_forecast.initial_memo_rule_set,
    #                                                 start_date_YYYYMMDD=self.base_forecast.start_date_YYYYMMDD,
    #                                                 end_date_YYYYMMDD=self.base_forecast.end_date_YYYYMMDD,
    #                                                 milestone_set=self.base_forecast.milestone_set,
    #                                                 forecast_set_name=self.forecast_set_name,
    #                                                 forecast_name=forecast_name
    #                                                 )
    #         new_id_to_name[new_E.unique_id] = forecast_name
    #         new_initialized_forecasts[new_E.unique_id] = new_E
    #     self.id_to_name = new_id_to_name
    #     self.initialized_forecasts = new_initialized_forecasts
    #
    #     id_sd = self.base_forecast.unique_id.split('_')[0]
    #     id_num_days = self.base_forecast.unique_id.split('_')[1]
    #     id_distinct_p = self.base_forecast.unique_id.split('_')[2]
    #     keys_list = list(self.initialized_forecasts.keys())
    #     keys_list.sort() #this has to be stable for the hash to be the same every time
    #     id_set_hash = str(int(hashlib.sha1(str(keys_list).encode("utf-8")).hexdigest(), 16) % 1000).rjust(4,'0')
    #     self.unique_id = 'S' + str(id_sd) + '_' + str(id_num_days) + '_' + str(id_distinct_p) + '_' + str(id_set_hash)

    def get_id_to_forecast_name_map(self):
        return self.id_to_name

    def get_id_to_forecast_map(self):
        return {
            self.base_forecast.unique_id: self.base_forecast,
            **self.initialized_forecasts,
        }

    def get_id_to_result_map(self):
        return self.forecast_results

    def get_forecast_name_to_forecast_map(self):
        name_to_forecast_map = {}
        for id, forecast_name in self.id_to_name.items():
            if id == self.base_forecast.unique_id:
                name_to_forecast_map[forecast_name] = self.base_forecast
            elif id in self.initialized_forecasts:
                name_to_forecast_map[forecast_name] = self.initialized_forecasts[id]
        return name_to_forecast_map

    def addChoiceToAllForecasts(
        self, list_of_choice_names, list_of_lists_of_memo_regexes
    ):
        # log_in_color(logger, 'white', 'info', 'ENTER addChoiceToAllScenarios')

        # if len(self.forecast_name_to_budget_item_set__dict) == 0:
        #     self.forecast_name_to_budget_item_set__dict['Core'] = self.core_budget_set

        if len(self.initialized_forecasts) == 0:
            # log_in_color(logger, 'white', 'info', 'i_f empty, setting i_f[core] = b_f')
            self.initialized_forecasts[self.base_forecast.unique_id] = self.base_forecast

        new_dict_of_scenarios = {}
        choice_index = 0
        for list_of_memo_regexes in list_of_lists_of_memo_regexes:
            choice_name = list_of_choice_names[choice_index]
            # log_in_color(logger, 'white', 'info', 'choice_index ' + str(choice_index))
            # log_in_color(logger, 'white', 'info', 'choice_name ' + str(choice_name))

            for E_id, E in self.initialized_forecasts.items():
                s_key = E.forecast_name or self.id_to_name.get(E_id, E_id)
                s_value = E.initial_budget_set
                # for s_key, s_value in self.forecast_name_to_budget_item_set__dict.items():
                # log_in_color(logger, 'white', 'info', 's_key ' + str(s_key))
                new_option_budget_set = copy.deepcopy(s_value)

                new_option_budget_set_list = new_option_budget_set.budget_items
                for bi in self.option_budget_set.budget_items:
                    # log_in_color(logger, 'white', 'info', 'bi ' + str(bi))
                    for memo_regex in list_of_memo_regexes:
                        # print((memo_regex, bi.memo))
                        match_result = re.search(memo_regex, bi.memo)
                        try:
                            match_result.group(0)
                            new_option_budget_set_list.append(bi)
                        except Exception:
                            pass
                new_option_budget_set = BudgetSet(new_option_budget_set_list)
                new_dict_of_scenarios[s_key + " | " + choice_name] = (
                    new_option_budget_set
                )

            choice_index += 1

        # log_in_color(logger, 'white', 'info', 'self.initialized_forecasts:' + str(self.initialized_forecasts.keys()))
        # for k, v in new_dict_of_scenarios.items():
        #     log_in_color(logger, 'white', 'info', 'k:' + str(k))
        #     log_in_color(logger, 'white', 'info', 'v:' + str(v.getBudgetItems().to_string()))

        new_id_to_name = {self.base_forecast.unique_id: "Core"}
        new_initialized_forecasts = {}
        # for E_id, E in self.initialized_forecasts.items():
        for forecast_name, budget_set in new_dict_of_scenarios.items():
            # for s_key, s_value in self.forecast_name_to_budget_item_set__dict.items():
            # print('Initializing '+forecast_name)
            new_E = ExpenseForecastInitialConditions(
                start_date=self.base_forecast.start_date,
                end_date=self.base_forecast.end_date,
                account_set=self.base_forecast.initial_account_set,
                budget_set=budget_set,
                memo_rule_set=self.base_forecast.initial_memo_rule_set,
                forecast_set_name=self.forecast_set_name,
                forecast_name=forecast_name,
            )
            new_id_to_name[new_E.unique_id] = forecast_name
            new_initialized_forecasts[new_E.unique_id] = new_E
        self.id_to_name = new_id_to_name
        self.initialized_forecasts = new_initialized_forecasts
        self.forecast_results = {
            forecast_id: result
            for forecast_id, result in self.forecast_results.items()
            if forecast_id in self.id_to_name
        }

        id_sd, id_num_days, id_distinct_p = self._scenario_id_parts(self.base_forecast)
        id_set_hash = self._stable_hash(list(self.initialized_forecasts.keys()))
        self.unique_id = (
            "S"
            + str(id_sd)
            + "_"
            + str(id_num_days)
            + "_"
            + str(id_distinct_p)
            + "_"
            + str(id_set_hash)
        )

        # log_in_color(logger, 'white', 'info', 'EXIT addChoiceToAllScenarios')

    def __str__(self):
        return_string = "------------------------------------------------------------------------------------------------\n"
        return_string += "Id: " + self.unique_id + "\n"
        return_string += "------------------------------------------------------------------------------------------------\n"
        return_string += "Core Set " + self.base_forecast.unique_id + ":\n"
        return_string += self.core_budget_set.getBudgetItems().to_string() + "\n"
        return_string += "------------------------------------------------------------------------------------------------\n"
        return_string += "Optional Set:\n"
        return_string += self.option_budget_set.getBudgetItems().to_string() + "\n"
        return_string += "------------------------------------------------------------------------------------------------\n"
        return_string += "Initialized Forecasts:\n"
        return_string += "id              sd          ed          Complete  Forecast Name\n"
        for k, v in self.get_id_to_forecast_map().items():
            completed_flag = k in self.forecast_results
            return_string += (
                str(k)
                + " "
                + v.start_date.isoformat()
                + " "
                + v.end_date.isoformat()
                + " "
                + str(completed_flag)
                + "    "
            )
            return_string += str(v.forecast_name or self.id_to_name.get(k, k))
            return_string += " \n"
        return_string += "------------------------------------------------------------------------------------------------\n"

        return return_string

    def renameForecast(self, old_label, new_label):
        matching_ids = [
            forecast_id
            for forecast_id, forecast_name in self.id_to_name.items()
            if forecast_name == old_label
        ]
        if not matching_ids:
            raise ValueError("Forecast Name not found")

        for forecast_id in matching_ids:
            self.id_to_name[forecast_id] = new_label
            if forecast_id == self.base_forecast.unique_id:
                self.base_forecast.forecast_name = new_label
            elif forecast_id in self.initialized_forecasts:
                self.initialized_forecasts[forecast_id].forecast_name = new_label

    def update_date_range(self, start_date_YYYYMMDD, end_date_YYYYMMDD):
        start_date = (
            start_date_YYYYMMDD
            if isinstance(start_date_YYYYMMDD, datetime.date)
            else datetime.datetime.strptime(str(start_date_YYYYMMDD), "%Y%m%d").date()
        )
        end_date = (
            end_date_YYYYMMDD
            if isinstance(end_date_YYYYMMDD, datetime.date)
            else datetime.datetime.strptime(str(end_date_YYYYMMDD), "%Y%m%d").date()
        )

        def rebuild(old_forecast):
            return ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=old_forecast.initial_account_set,
                budget_set=old_forecast.initial_budget_set,
                memo_rule_set=old_forecast.initial_memo_rule_set,
                forecast_set_name=old_forecast.forecast_set_name,
                forecast_name=old_forecast.forecast_name,
            )

        old_id_to_name = self.id_to_name.copy()
        self.base_forecast = rebuild(self.base_forecast)
        self.core_budget_set = self.base_forecast.initial_budget_set

        new_initialized_forecasts = {}
        new_id_to_name = {self.base_forecast.unique_id: "Core"}
        for old_id, old_forecast in self.initialized_forecasts.items():
            new_forecast = rebuild(old_forecast)
            new_initialized_forecasts[new_forecast.unique_id] = new_forecast
            new_id_to_name[new_forecast.unique_id] = old_id_to_name.get(
                old_id, new_forecast.forecast_name or new_forecast.unique_id
            )

        self.initialized_forecasts = new_initialized_forecasts
        self.id_to_name = new_id_to_name
        self.forecast_results = {}

        # forecast id structure e.g. 240331_41_####
        # same for set, but add S and hash the hashes
        id_sd, id_num_days, id_distinct_p = self._scenario_id_parts(self.base_forecast)
        id_set_hash = self._stable_hash(list(self.initialized_forecasts.keys()))
        self.unique_id = (
            "S"
            + str(id_sd)
            + "_"
            + str(id_num_days)
            + "_"
            + str(id_distinct_p)
            + "_"
            + str(id_set_hash)
        )

    def writeToJSONFile(self, output_dir="./"):
        output_path = Path(output_dir)
        if output_path.suffix:
            target_path = output_path
        else:
            target_path = output_path / f"ForecastSet_{self.unique_id}.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        log_in_color(
            logger,
            "green",
            "info",
            "Writing to " + str(target_path),
        )
        target_path.write_text(self.to_json())
        return True

    def runAllForecasts(self, log_level="WARNING", include_debug_columns=False, include_core=True):
        from .ForecastHandler import ForecastHandler

        forecasts_to_run = self.get_id_to_forecast_map() if include_core else self.initialized_forecasts
        for unique_id, initial_conditions in forecasts_to_run.items():
            log_in_color(
                logger,
                "green",
                "info",
                "ForecastSet::runAllForecasts - start " + unique_id,
            )
            milestone_set = getattr(initial_conditions, "milestone_set", MilestoneSet())
            self.forecast_results[unique_id] = ForecastHandler().runForecast(
                initial_conditions,
                milestone_set,
                include_debug_columns=include_debug_columns,
            )
        return self.forecast_results

    def runAllForecastsApproximate(self):
        return self.runAllForecasts()

    def generateHTMLReports(self, output_dir="./"):
        from .ForecastHandler import ForecastHandler

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        handler = ForecastHandler()
        for forecast_id, result in self.forecast_results.items():
            handler.generateHTMLReport(result, output_path)

    def runForecastSet(self, *args, **kwargs):
        return self.runAllForecasts(*args, **kwargs)
