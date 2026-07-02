from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.ForecastSet import ForecastSet
from expense_forecast.MemoRuleSet import MemoRuleSet 
from expense_forecast.MilestoneSet import MilestoneSet 
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions 
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult 
import hashlib
import hashlib
import json
from datetime import date
from typing import Any
import datetime
from expense_forecast.log_methods import log_in_color
import logging
import tqdm
import pandas as pd
import re
import copy 

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(levelname)-8s - %(message)s")
fileHandler = logging.FileHandler(__name__ + ".log", mode="w")
fileHandler.setFormatter(formatter)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.setLevel(logging.DEBUG) 
logger.handlers.clear()
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.propagate = False

def _stable_df_payload(df):
    return (
        df.sort_index(axis=1)
        .reset_index(drop=True)
        .to_dict(orient="records")
    )

class ForecastHandler:
    # def __init__(self):
    #     self.forecast_set = None
    #     self.account_set = None
    #     self.budget_set = None
    #     self.memo_rule_set = None
    #     self.milestone_set = None

    # def load_forecast_set(self, forecast_set: ForecastSet):
    #     self.forecast_set = forecast_set

    # def load_account_set(self, account_set: AccountSet):
    #     self.account_set = account_set

    # def load_budget_set(self, budget_set: BudgetSet):
    #     self.budget_set = budget_set

    # def load_memo_rule_set(self, memo_rule_set: MemoRuleSet):
    #     self.memo_rule_set = memo_rule_set

    # def load_milestone_set(self, milestone_set: MilestoneSet):
    #     self.milestone_set = milestone_set

    
    def runForecast(self, IO: ExpenseForecastInitialConditions, 
                    ):
        # print('Starting Forecast #'+str(self.unique_id))
        self.start_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_in_color(
            logger, "white", "info", "Starting Forecast " + str(IO.unique_id)
        )

        sd = IO.start_date
        ed = IO.end_date
        predicted__satisfice_runtime_in_simulated_days = (ed - sd).days

        # On second thought, I would rather deal wit ha stilted progress bar than figuring out how to track progress in recursion
        no_of_p2plus_priority_levels = len(set(IO.initial_proposed_df.Priority))
        total_predicted_max_runtime_in_simulated_days = (
            predicted__satisfice_runtime_in_simulated_days
            + predicted__satisfice_runtime_in_simulated_days
            * no_of_p2plus_priority_levels
        )
        progress_bar = tqdm.tqdm(
            range(total_predicted_max_runtime_in_simulated_days),
            total=total_predicted_max_runtime_in_simulated_days,
            desc=IO.unique_id,
            disable=True,
        )  # disabled tqdm

        forecast_df, skipped_df, confirmed_df, deferred_df = (
            self._computeOptimalForecast(
                start_date=IO.start_date,
                end_date=IO.end_date,
                confirmed_df=pd.DataFrame(IO.initial_confirmed_df, copy=True),
                proposed_df=pd.DataFrame(IO.initial_proposed_df, copy=True),
                deferred_df=pd.DataFrame(IO.initial_deferred_df, copy=True),
                skipped_df=pd.DataFrame(IO.initial_skipped_df, copy=True),
                account_set=copy.deepcopy(IO.initial_account_set), #TODO copy may not be needed here?
                memo_rule_set=copy.deepcopy(IO.initial_memo_rule_set), 
                raise__satisfice_failed_exception=False,
                progress_bar=progress_bar,
            )
        )

        # Round all values in Memo and Memo Directives
        # (I think I can round other columns as needed w display.precision without changing the data)
        for index, row in forecast_df.iterrows():
            new_memo_lines = []
            for m in row["Memo"].split(";"):
                if m.strip() == "":
                    continue
                try:
                    og_amt = float(re.search(".*\\$(.*)\\)", m).group(1))
                except Exception as e:
                    print("Offending memo: " + str(m))
                    raise e
                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 29) _update_memo_amount')
                new_m = self._update_memo_amount(m, new_amount).strip()
                new_memo_lines.append(new_m)

            new_md_lines = []
            for md in row["Memo Directives"].split(";"):
                if md.strip() == "":
                    continue
                try:
                    og_amt = float(re.search(".*\\$(.*)\\)", md).group(1))
                except Exception as e:
                    print("Offending memo directive: " + str(md))
                    raise e
                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 30) _update_memo_amount')
                new_md = self._update_memo_amount(md, new_amount).strip()
                new_md_lines.append(new_md)

            forecast_df.loc[index, "Memo"] = "; ".join(new_memo_lines)
            forecast_df.loc[index, "Memo Directives"] = "; ".join(new_md_lines)

        self.forecast_df = forecast_df
        self.skipped_df = skipped_df
        self.confirmed_df = confirmed_df
        self.deferred_df = deferred_df

        self.end_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._appendSummaryLines()
        self.evaluateMilestones()

        # This creates a dependecy on the environment that I don't know how I feel about
        pd.set_option("display.precision", 2)
        log_in_color(
            logger, "white", "info", "Finished Forecast " + str(IO.unique_id)
        )
        log_in_color(logger, "white", "info", self.forecast_df.to_string())
        # if play_notification_sound:
        #     notification_sounds.play_notification_sound()

        # self.forecast_df.to_csv('./out//Forecast_' + self.unique_id + '.csv') #this is only the forecast not the whole ExpenseForecast object
        # self.writeToJSONFile() #this is the whole ExpenseForecast object #todo this should accept a path parameter

    
    
