
import json
from io import StringIO
from pathlib import Path
import hashlib
import pandas as pd
import jsonpickle
from typing import Any
from datetime import date
import logging
import copy
from expense_forecast.log_methods import log_in_color
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet

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

class ExpenseForecastInitialConditions:

    @staticmethod
    def _dataframe_to_json_data(dataframe):
        if dataframe is None:
            return None
        return json.loads(dataframe.to_json(orient="split", date_format="iso"))

    @staticmethod
    def _dataframe_from_json_data(data):
        if data is None:
            return None
        return pd.read_json(StringIO(json.dumps(data)), orient="split")

    @staticmethod
    def _object_to_json_data(obj):
        if obj is None:
            return None
        return json.loads(jsonpickle.encode(obj))

    @staticmethod
    def _object_from_json_data(data):
        if data is None:
            return None
        return jsonpickle.decode(json.dumps(data))

    @staticmethod
    def _date_from_dict_value(value):
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    @classmethod
    def _account_set_from_dict(cls, data):
        if "accounts" not in data:
            return cls._object_from_json_data(data)

        account_set = AccountSet()
        for account_row in data["accounts"]:
            account_type = account_row["Account_Type"]
            if account_type == "checking":
                account_set.createCheckingAccount(
                    name=account_row["Name"],
                    balance=account_row["Balance"],
                    min_balance=account_row["Min_Balance"],
                    max_balance=account_row["Max_Balance"],
                    primary_checking_ind=account_row["Primary_Checking_Ind"],
                )
            elif account_type == "credit":
                account_set.createCreditCardAccount(
                    name=account_row["Name"],
                    current_statement_balance=account_row[
                        "Current_Statement_Balance"
                    ],
                    previous_statement_balance=account_row[
                        "Previous_Statement_Balance"
                    ],
                    min_balance=account_row["Min_Balance"],
                    max_balance=account_row["Max_Balance"],
                    billing_start_date=cls._date_from_dict_value(
                        account_row["Billing_Start_Date"]
                    ),
                    apr=account_row["APR"],
                    minimum_payment=account_row["Minimum_Payment"],
                    end_of_previous_cycle_balance=account_row[
                        "End_Of_Previous_Cycle_Balance"
                    ],
                )
                account = account_set.accounts[-1]
                if "Minimum_Payment_Floor" in account_row:
                    account.billing_state.minimum_payment_floor = account_set._money(
                        account_row["Minimum_Payment_Floor"]
                    )
                if "Minimum_Payment_Credit_Balance" in account_row:
                    account.billing_state.minimum_payment_credit_balance = (
                        account_set._money(
                            account_row["Minimum_Payment_Credit_Balance"]
                        )
                    )
            elif account_type == "loan":
                account_set.createLoanAccount(
                    name=account_row["Name"],
                    principal_balance=account_row["Principal_Balance"],
                    interest_balance=account_row["Interest_Balance"],
                    min_balance=account_row["Min_Balance"],
                    max_balance=account_row["Max_Balance"],
                    billing_start_date=cls._date_from_dict_value(
                        account_row["Billing_Start_Date"]
                    ),
                    apr=account_row["APR"],
                    minimum_payment=account_row["Minimum_Payment"],
                    end_of_previous_cycle_balance=account_row[
                        "End_Of_Previous_Cycle_Balance"
                    ],
                )
            else:
                raise NotImplementedError(
                    f"Cannot initialize account_type from dict: {account_type}"
                )

        return account_set

    @classmethod
    def _budget_set_from_dict(cls, data):
        if "budget_items" not in data:
            return cls._object_from_json_data(data)

        budget_set = BudgetSet()
        for budget_item in data["budget_items"]:
            budget_set.addBudgetItem(
                start_date=cls._date_from_dict_value(budget_item["Start_Date"]),
                end_date=cls._date_from_dict_value(budget_item["End_Date"]),
                priority=budget_item["Priority"],
                cadence=budget_item["Cadence"],
                amount=budget_item["Amount"],
                memo=budget_item["Memo"],
                income_flag=budget_item.get("Income_Flag", False),
                deferrable=budget_item.get("Deferrable"),
                partial_payment_allowed=budget_item.get("Partial_Payment_Allowed"),
            )
        return budget_set

    @classmethod
    def _memo_rule_set_from_dict(cls, data):
        if "memo_rules" not in data:
            return cls._object_from_json_data(data)

        memo_rule_set = MemoRuleSet()
        for memo_rule in data["memo_rules"]:
            memo_rule_set.addMemoRule(
                memo_regex=memo_rule["Memo_Regex"],
                account_from=memo_rule["Account_From"],
                account_to=memo_rule["Account_To"],
                transaction_priority=memo_rule["Transaction_Priority"],
            )
        return memo_rule_set
    
    #TODO stepsize will be added to this eventually
    @staticmethod
    def compute_forecast_id(
        start_date: date,
        end_date: date,
        account_set,
        budget_set,
        memo_rule_set
    ) -> str:

        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        accounts_df = account_set.getAccounts()
        budget_df = budget_set.getBudgetItems()
        memo_rules_df = memo_rule_set.getMemoRules()

        num_days = (end_date - start_date).days
        num_distinct_priority = budget_df["Priority"].nunique()

        payload: dict[str, Any] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "accounts": _stable_df_payload(accounts_df),
            "budget_items": _stable_df_payload(budget_df),
            "memo_rules": _stable_df_payload(memo_rules_df),
        }

        canonical_json = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:10]

        unique_id = (
            f"{start_date.strftime('%y%m%d')}_"
            f"{num_days}_"
            f"{num_distinct_priority}_"
            f"{digest}"
        )

        return unique_id


    def __eq__(self, other):
        raise NotImplementedError #todo

    def __ne__(self, other):
        raise NotImplementedError #todo

    def __hash__(self):
        raise NotImplementedError #todo

    # todo confirm that I don't need __getstate__, __setstate__. I think pickle can compress data frames and I might not want that
    
    def _validate_start_and_end_dates(self, start_date, end_date):
        assert start_date != end_date
        assert start_date < end_date

    def _validate_account_budget_memo_rule_intersection(self, account_set: AccountSet, 
                                                        budget_item_set: BudgetSet, 
                                                        memo_rule_set: MemoRuleSet):
        accounts_df = account_set.getAccounts()
        budget_df = budget_item_set.getBudgetItems()
        memo_df = memo_rule_set.getMemoRules()

        error_ind = False
        error_text = ""

        if accounts_df.shape[0] == 0:
            # if len(account_set) == 0:
            raise ValueError("There needs to be at least 1 account for ExpenseForecast to do anything.")

        
        distinct_base_account_names__from_acct = pd.DataFrame(
            pd.DataFrame(accounts_df.Name)
            .apply(lambda x: x.iloc[0].split(":")[0], axis=1)
            .drop_duplicates()
        ).rename(columns={0: "Name"})
        account_names__from_memo = pd.concat(
            [
                pd.DataFrame(memo_df[["Account_From"]]).rename(
                    columns={"Account_From": "Name"}
                ),
                pd.DataFrame(memo_df[["Account_To"]]).rename(
                    columns={"Account_To": "Name"}
                ),
            ]
        )

        distinct_account_names__from_memo = (
            account_names__from_memo.loc[
                account_names__from_memo["Name"] != "None", ["Name"]
            ]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        A_names = None
        B_names = None
        try:

            A_names = {""}
            for a in distinct_account_names__from_memo["Name"].tolist():
                A_names = A_names.union({a})
            A_names = A_names - {
                "ALL_LOANS"
            }  # if we have a memo rule for ALL_LOANS, we don't want that to be checked against the list of account names

            A2 = {""}
            for a in distinct_base_account_names__from_acct["Name"].tolist():
                A2 = A2.union({a})

            B_names = A_names.intersection(A2)

            assert A_names == B_names
        except Exception as e:
            error_text = str(e.args) + "\n"
            error_text += "An account name was mentioned in a memo rule that did not exist in the account set\n"
            error_text += "all accounts mentioned in memo rules:\n"
            error_text += distinct_account_names__from_memo["Name"].to_string() + "\n"
            error_text += "all defined accounts:\n"
            error_text += distinct_base_account_names__from_acct["Name"].to_string() + "\n"
            error_text += "intersection:\n"
            error_text += str(B_names) + "\n"
            error_text += "Accounts from Memo:\n"
            error_text += str(A_names) + "\n"
            error_ind = True

        for index, row in budget_df.iterrows():
            memo_rule_set.findMatchingMemoRule(
                row.Memo, row.Priority
            )  # this will throw errors as needed

        if error_ind:
            log_in_color(logger, "red", "error", error_text)
            raise ValueError(error_text)
        
    def _preprocess_budget_items(self, start_date, end_date, budget_set):
        first_proposed_df = budget_set.getBudgetSchedule()
        if not first_proposed_df.empty:
            first_proposed_df = first_proposed_df.copy()
            first_proposed_df["Date"] = pd.to_datetime(first_proposed_df["Date"]).dt.date

        date_range_sel_vec = (
            (first_proposed_df.Date >= start_date)
            & (first_proposed_df.Date <= end_date)
        )
        proposed_df = first_proposed_df[date_range_sel_vec]
        proposed_df.reset_index(drop=True, inplace=True)

        # otherwise proposed has no columns
        if proposed_df.empty:
            proposed_df = pd.DataFrame(
                {
                    "Date": [],
                    "Priority": [],
                    "Amount": [],
                    "Memo": [],
                    "Deferrable": [],
                    "Partial_Payment_Allowed": [],
                }
            )

        # take priority 1 items and put them in confirmed
        confirmed_df = proposed_df[proposed_df.Priority == 1]
        confirmed_df.reset_index(drop=True, inplace=True)

        proposed_df = proposed_df[proposed_df.Priority != 1]
        proposed_df.reset_index(drop=True, inplace=True)

        deferred_df = copy.deepcopy(proposed_df.head(0))
        skipped_df = copy.deepcopy(proposed_df.head(0))

        return confirmed_df, proposed_df, deferred_df, skipped_df

    def __init__(self, start_date: date, end_date: date, 
                account_set: AccountSet, 
                 budget_set: BudgetSet, 
                 memo_rule_set: MemoRuleSet, 
                 log_stack_depth,
                 **kwargs):

        allowed_kwargs = ['forecast_name',
                          'forecast_set_name',
                          'milestone_set'
                          ]
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        self._validate_start_and_end_dates(start_date, end_date)
        self.start_date = start_date
        self.end_date = end_date


        self._validate_account_budget_memo_rule_intersection(account_set, budget_set, memo_rule_set)

        self.initial_account_set = copy.deepcopy(account_set)
        self.initial_budget_set = copy.deepcopy(budget_set)
        self.initial_memo_rule_set = copy.deepcopy(memo_rule_set)

        confirmed_df, proposed_df, deferred_df, skipped_df = self._preprocess_budget_items(start_date, end_date, budget_set)

        self.unique_id = ExpenseForecastInitialConditions.compute_forecast_id(
            start_date=self.start_date,
            end_date=self.end_date,
            account_set=self.initial_account_set,
            budget_set=self.initial_budget_set,
            memo_rule_set=self.initial_memo_rule_set)

        self.initial_proposed_df = proposed_df
        self.initial_deferred_df = deferred_df
        self.initial_skipped_df = skipped_df
        self.initial_confirmed_df = confirmed_df

        self.forecast_name = kwargs.get('forecast_name', None)

        self.forecast_set_name = kwargs.get('forecast_set_name', None)


    def __str__(self):
        raise NotImplementedError #todo

    def __repr__(self):
        raise NotImplementedError #todo

    # Class methods for loading data
    @classmethod
    def load_csv_file(cls):
        raise NotImplementedError

    @classmethod
    def load_xml_file(cls):
        raise NotImplementedError

    @classmethod
    def loadJSON(cls, json_or_path):
        # logger.debug("ENTER ExpenseForecastInitialConditions.loadJSON")
        json_string_candidate = str(json_or_path).strip()
        # logger.debug(f"json_string_candidate: {json_string_candidate}")
        if isinstance(json_or_path, (str, Path)) and not json_string_candidate.startswith(("{", "[")):
            candidate_path = Path(json_or_path)
            json_string = candidate_path.read_text()
        else:
            json_string = str(json_or_path)

        data = json.loads(json_string)
        # logger.debug(f"Loaded JSON data: {str(data)}")
        return cls.initialize_from_dict(data)

    @classmethod
    def initialize_from_dict(cls, data: dict):
        return cls(
            start_date=cls._date_from_dict_value(data["start_date"]),
            end_date=cls._date_from_dict_value(data["end_date"]),
            account_set=cls._account_set_from_dict(data["account_set"]),
            budget_set=cls._budget_set_from_dict(data["budget_set"]),
            memo_rule_set=cls._memo_rule_set_from_dict(data["memo_rule_set"]),
            milestone_set=cls._object_from_json_data(
                data.get("milestone_set")
            ) or MilestoneSet(),
        ) #TODO forecast name 

    @classmethod
    def load_database_tables(cls):
        raise NotImplementedError

    @classmethod
    def load_excel_file(cls):
        raise NotImplementedError

    @classmethod
    def load_pickle_file(cls):
        raise NotImplementedError

    # Instance methods for exporting data to strings
    def to_csv_string(self):
        raise NotImplementedError

    def to_xml_string(self):
        raise NotImplementedError

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    # Instance methods for writing data to external sources
    def write_csv_file(self):
        raise NotImplementedError

    def write_xml_file(self):
        raise NotImplementedError

    def write_json_file(self, path_to_json):
        return self.dumpJSON(path_to_json)

    def dumpJSON(self, path_to_json):
        target_path = Path(path_to_json)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(self.to_json())
        return True

    def writeToJSONFile(self, output_dir="./"):
        output_path = Path(output_dir) / f"Forecast_{self.unique_id}.json"
        return self.dumpJSON(output_path)

    def write_database_tables(self):
        raise NotImplementedError

    def write_excel_file(self):
        raise NotImplementedError

    def write_pickle_file(self):
        raise NotImplementedError

    def to_dict(self):
        return {
            "unique_id": self.unique_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "account_set": self.initial_account_set.to_dict(),
            "budget_set": self.initial_budget_set.to_dict(),
            "memo_rule_set": self.initial_memo_rule_set.to_dict(),
            "milestone_set": self._object_to_json_data(self.milestone_set),
        }
