"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""



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
from expense_forecast.log_methods import log_in_color, project_log_file, setup_logger
from expense_forecast.AccountSet import AccountSet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ConditionalScenarioTransitionSet import (
    ConditionalScenarioTransitionSet,
)
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.PolicyProgram import PolicyProgram

logger = setup_logger(__name__, project_log_file(__name__))

#TODO DOC manual review of ExpenseForecastInitialConditions._stable_df_payload docstring
def _stable_df_payload(df):
    """
    #TODO DOC one-line description of ExpenseForecastInitialConditions._stable_df_payload.

    #TODO DOC multi-line description of ExpenseForecastInitialConditions._stable_df_payload.
    #TODO DOC explain how ExpenseForecastInitialConditions._stable_df_payload participates in this module.
    #TODO DOC document important state, validation, or serialization behavior.

    Parameters
    ----------
    df : pd.DataFrame
        #TODO DOC one-line description of ExpenseForecastInitialConditions._stable_df_payload.df.

    Returns
    -------
    object
        #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._stable_df_payload.

    Contract
    --------
    - #TODO DOC contract lines for ExpenseForecastInitialConditions._stable_df_payload.
    - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._stable_df_payload.

    @interface-report: show
    """
    return (
        df.sort_index(axis=1)
        .reset_index(drop=True)
        .to_dict(orient="records")
    )

#TODO DOC manual review of ExpenseForecastInitialConditions docstring
class ExpenseForecastInitialConditions:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DOC manual review of ExpenseForecastInitialConditions._dataframe_to_json_data docstring
    @staticmethod
    def _dataframe_to_json_data(dataframe):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._dataframe_to_json_data.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._dataframe_to_json_data.
        #TODO DOC explain how ExpenseForecastInitialConditions._dataframe_to_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        dataframe : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions._dataframe_to_json_data.dataframe.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._dataframe_to_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._dataframe_to_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._dataframe_to_json_data.

        @interface-report: show
        """
        if dataframe is None:
            return None
        return json.loads(dataframe.to_json(orient="split", date_format="iso"))

    #TODO DOC manual review of ExpenseForecastInitialConditions._dataframe_from_json_data docstring
    @staticmethod
    def _dataframe_from_json_data(data):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._dataframe_from_json_data.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._dataframe_from_json_data.
        #TODO DOC explain how ExpenseForecastInitialConditions._dataframe_from_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastInitialConditions._dataframe_from_json_data.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._dataframe_from_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._dataframe_from_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._dataframe_from_json_data.

        @interface-report: show
        """
        if data is None:
            return None
        return pd.read_json(StringIO(json.dumps(data)), orient="split")

    #TODO DOC manual review of ExpenseForecastInitialConditions._object_to_json_data docstring
    @staticmethod
    def _object_to_json_data(obj):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._object_to_json_data.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._object_to_json_data.
        #TODO DOC explain how ExpenseForecastInitialConditions._object_to_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        obj : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions._object_to_json_data.obj.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._object_to_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._object_to_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._object_to_json_data.

        @interface-report: show
        """
        if obj is None:
            return None
        return json.loads(jsonpickle.encode(obj))

    #TODO DOC manual review of ExpenseForecastInitialConditions._object_from_json_data docstring
    @staticmethod
    def _object_from_json_data(data):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._object_from_json_data.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._object_from_json_data.
        #TODO DOC explain how ExpenseForecastInitialConditions._object_from_json_data participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastInitialConditions._object_from_json_data.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._object_from_json_data.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._object_from_json_data.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._object_from_json_data.

        @interface-report: show
        """
        if data is None:
            return None
        return jsonpickle.decode(json.dumps(data))

    #TODO DOC manual review of ExpenseForecastInitialConditions._date_from_dict_value docstring
    @staticmethod
    def _date_from_dict_value(value):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._date_from_dict_value.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._date_from_dict_value.
        #TODO DOC explain how ExpenseForecastInitialConditions._date_from_dict_value participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions._date_from_dict_value.value.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._date_from_dict_value.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._date_from_dict_value.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._date_from_dict_value.

        @interface-report: show
        """
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    #TODO DOC manual review of ExpenseForecastInitialConditions._account_set_from_dict docstring
    @classmethod
    def _account_set_from_dict(cls, data):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._account_set_from_dict.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._account_set_from_dict.
        #TODO DOC explain how ExpenseForecastInitialConditions._account_set_from_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastInitialConditions._account_set_from_dict.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._account_set_from_dict.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._account_set_from_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._account_set_from_dict.

        @interface-report: show
        """
        if "accounts" in data:
            return AccountSet.from_dict(data)
        return cls._object_from_json_data(data)

    #TODO DOC manual review of ExpenseForecastInitialConditions._line_item_set_from_dict docstring
    @classmethod
    def _line_item_set_from_dict(cls, data):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._line_item_set_from_dict.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._line_item_set_from_dict.
        #TODO DOC explain how ExpenseForecastInitialConditions._line_item_set_from_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastInitialConditions._line_item_set_from_dict.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._line_item_set_from_dict.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._line_item_set_from_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._line_item_set_from_dict.

        @interface-report: show
        """
        if "budget_items" not in data:
            return cls._object_from_json_data(data)
        return LineItemSet.from_dict(data)

    #TODO DOC manual review of ExpenseForecastInitialConditions._memo_rule_set_from_dict docstring
    @classmethod
    def _memo_rule_set_from_dict(cls, data):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._memo_rule_set_from_dict.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._memo_rule_set_from_dict.
        #TODO DOC explain how ExpenseForecastInitialConditions._memo_rule_set_from_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastInitialConditions._memo_rule_set_from_dict.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._memo_rule_set_from_dict.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._memo_rule_set_from_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._memo_rule_set_from_dict.

        @interface-report: show
        """
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

    #TODO DOC manual review of ExpenseForecastInitialConditions.compute_forecast_id docstring
    @staticmethod
    def compute_forecast_id(
        start_date: date,
        end_date: date,
        account_set,
        line_item_set,
        memo_rule_set
    ) -> str:

        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.compute_forecast_id.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.compute_forecast_id.
        #TODO DOC explain how ExpenseForecastInitialConditions.compute_forecast_id participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions.compute_forecast_id.start_date.

        end_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions.compute_forecast_id.end_date.

        account_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.compute_forecast_id.account_set.

        line_item_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.compute_forecast_id.line_item_set.

        memo_rule_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.compute_forecast_id.memo_rule_set.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.compute_forecast_id.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.compute_forecast_id.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.compute_forecast_id.

        @interface-report: show
        """
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        accounts_df = account_set.getAccounts()
        budget_df = line_item_set.getLineItems()
        memo_rules_df = memo_rule_set.getMemoRules()

        num_days = (end_date - start_date).days
        num_distinct_priority = budget_df["Priority"].nunique()

        payload: dict[str, Any] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "accounts": _stable_df_payload(accounts_df),
            "budget_items": _stable_df_payload(budget_df),
            "scenario_selections": dict(
                getattr(line_item_set, "scenario_selections", {})
            ),
            "scenario_timelines": getattr(line_item_set, "scenario_timelines", {}),
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


    #TODO DOC manual review of ExpenseForecastInitialConditions.__eq__ docstring
    def __eq__(self, other):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.__eq__.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.__eq__.
        #TODO DOC explain how ExpenseForecastInitialConditions.__eq__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        other : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__eq__.other.

        Returns
        -------
        bool
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.__eq__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.__eq__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.__eq__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement IO::__eq__

    #TODO DOC manual review of ExpenseForecastInitialConditions.__ne__ docstring
    def __ne__(self, other):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.__ne__.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.__ne__.
        #TODO DOC explain how ExpenseForecastInitialConditions.__ne__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        other : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__ne__.other.

        Returns
        -------
        bool
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.__ne__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.__ne__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.__ne__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement IO::__ne__

    #TODO DOC manual review of ExpenseForecastInitialConditions.__hash__ docstring
    def __hash__(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.__hash__.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.__hash__.
        #TODO DOC explain how ExpenseForecastInitialConditions.__hash__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.__hash__ takes no parameters beyond self/cls.

        Returns
        -------
        int
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.__hash__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.__hash__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.__hash__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement IO::__hash__ ; unclear on the purpose of this ?

    #TODO DOC manual review of ExpenseForecastInitialConditions._validate_start_and_end_dates docstring
    @classmethod
    def _validate_start_and_end_dates(cls, start_date, end_date):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._validate_start_and_end_dates.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._validate_start_and_end_dates.
        #TODO DOC explain how ExpenseForecastInitialConditions._validate_start_and_end_dates participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions._validate_start_and_end_dates.start_date.

        end_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions._validate_start_and_end_dates.end_date.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._validate_start_and_end_dates.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._validate_start_and_end_dates.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._validate_start_and_end_dates.

        @interface-report: show
        """
        if start_date == end_date:
            raise ValueError(f"start_date must not equal end date. start = {start_date} end = {end_date}")
        if start_date > end_date:
            raise ValueError(f"start_date must be before end date. start = {start_date} end = {end_date}")

    #TODO DOC manual review of ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection docstring
    @classmethod
    def _validate_account_budget_memo_rule_intersection(cls, account_set: AccountSet,
                                                        budget_item_set: LineItemSet,
                                                        memo_rule_set: MemoRuleSet):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.
        #TODO DOC explain how ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.account_set.

        budget_item_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.budget_item_set.

        memo_rule_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.memo_rule_set.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._validate_account_budget_memo_rule_intersection.

        @interface-report: show
        """
        accounts_df = account_set.getAccounts()
        budget_df = budget_item_set.getLineItems()
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

        A_names = {""}
        B_names = None
        try:


            for a in distinct_account_names__from_memo["Name"].tolist():
                A_names = A_names.union({a})
            A_names = {
                name for name in A_names
                if name is not None and not str(name).startswith("ALL_LOANS")
                and not str(name).startswith("ALL_CREDIT_CARDS")
                and not str(name).startswith("CHECKING_ABOVE:")
                and not str(name).startswith("CURRENT_STATEMENT_BALANCE:")
                and not str(name).startswith("SAVINGS_BELOW:")
            }

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

    #TODO DOC manual review of ExpenseForecastInitialConditions._preprocess_budget_items docstring
    @classmethod
    def _preprocess_budget_items(cls, start_date, end_date, line_item_set):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions._preprocess_budget_items.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions._preprocess_budget_items.
        #TODO DOC explain how ExpenseForecastInitialConditions._preprocess_budget_items participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions._preprocess_budget_items.start_date.

        end_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions._preprocess_budget_items.end_date.

        line_item_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions._preprocess_budget_items.line_item_set.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions._preprocess_budget_items.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions._preprocess_budget_items.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions._preprocess_budget_items.

        @interface-report: show
        """
        first_proposed_df = line_item_set.getLineItemSchedule()
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

    #TODO DOC manual review of ExpenseForecastInitialConditions.__init__ docstring
    def __init__(self,
                 start_date: date,
                 end_date: date,
                 account_set: AccountSet,
                 line_item_set: LineItemSet,
                 memo_rule_set: MemoRuleSet,
                 log_stack_depth=0, #TODO IO::init.log_stack_depth be a kwarg instead of a param w default?
                 **kwargs):

        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.__init__.
        #TODO DOC explain how ExpenseForecastInitialConditions.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.start_date.

        end_date : date
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.end_date.

        account_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.account_set.

        line_item_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.line_item_set.

        memo_rule_set : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.memo_rule_set.

        log_stack_depth : int
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.log_stack_depth.

        **kwargs : dict
            #TODO DOC one-line description of ExpenseForecastInitialConditions.__init__.kwargs.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.__init__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.__init__.

        @interface-report: show
        """
        allowed_kwargs = [
            'forecast_name',
            'forecast_set_name',
            'milestone_set',
            'transitions',
            'policy_set',
            'policy_program',
        ]
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        self.forecast_name = kwargs.get('forecast_name', None)
        self.forecast_set_name = kwargs.get('forecast_set_name', None)

        self._validate_start_and_end_dates(start_date, end_date)
        self.start_date = start_date
        self.end_date = end_date

        self._validate_account_budget_memo_rule_intersection(account_set, line_item_set, memo_rule_set)

        self.initial_account_set = copy.deepcopy(account_set)
        self.initial_line_item_set = copy.deepcopy(line_item_set)
        self.initial_memo_rule_set = copy.deepcopy(memo_rule_set)
        self.milestone_set = copy.deepcopy(kwargs.get('milestone_set') or MilestoneSet())
        self.transitions = copy.deepcopy(
            kwargs.get('transitions') or ConditionalScenarioTransitionSet()
        )
        if not isinstance(self.transitions, ConditionalScenarioTransitionSet):
            raise TypeError("transitions must be a ConditionalScenarioTransitionSet")
        self.transitions.validate(self.milestone_set, self.initial_line_item_set)
        if kwargs.get('policy_set') is not None and kwargs.get('policy_program') is not None:
            raise ValueError("Specify policy_set or policy_program, not both")
        configured_policies = kwargs.get('policy_program', kwargs.get('policy_set'))
        if configured_policies is None:
            configured_policies = ForecastPolicySet()
        self.policy_program = copy.deepcopy(
            configured_policies
            if isinstance(configured_policies, PolicyProgram)
            else PolicyProgram(configured_policies)
        )
        if not isinstance(self.policy_program, PolicyProgram):
            raise TypeError("policy_program must be a PolicyProgram")
        self.policy_set = self.policy_program.resolve(self.start_date)
        for boundary in self.policy_program.phase_boundaries(self.start_date, self.end_date):
            self.policy_program.resolve(boundary).validate(
                self.initial_account_set, self.initial_line_item_set
            )

        self.unique_id = ExpenseForecastInitialConditions.compute_forecast_id(
            start_date=self.start_date,
            end_date=self.end_date,
            account_set=self.initial_account_set,
            line_item_set=self.initial_line_item_set,
            memo_rule_set=self.initial_memo_rule_set)
        if self.policy_program:
            policy_json = json.dumps(
                self._object_to_json_data(self.policy_program), sort_keys=True
            )
            self.unique_id += "_" + hashlib.sha256(
                policy_json.encode("utf-8")
            ).hexdigest()[:10]

        # GPT doesn't like that ExpenseForecastInitialConditions is owning this logic
        # and that data frame manipulation is occuring inside __init__ here,
        # but I have decided to ignore this advice
        confirmed_df, proposed_df, deferred_df, skipped_df = self._preprocess_budget_items(start_date, end_date, line_item_set)

        self.initial_proposed_df = proposed_df
        self.initial_deferred_df = deferred_df
        self.initial_skipped_df = skipped_df
        self.initial_confirmed_df = confirmed_df


    #TODO DOC manual review of ExpenseForecastInitialConditions.__str__ docstring
    def __str__(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.__str__.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.__str__.
        #TODO DOC explain how ExpenseForecastInitialConditions.__str__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.__str__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.__str__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.__str__.

        @interface-report: show
        """
        raise NotImplementedError #TODO DEFER implement IO::__str__

    #TODO DOC manual review of ExpenseForecastInitialConditions.__repr__ docstring
    def __repr__(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.__repr__.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.__repr__.
        #TODO DOC explain how ExpenseForecastInitialConditions.__repr__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.__repr__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.__repr__.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.__repr__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.__repr__.

        @interface-report: show
        """
        raise NotImplementedError  #TODO DEFER implement IO::__repr__

    # Class methods for loading data
    #TODO DOC manual review of ExpenseForecastInitialConditions.load_csv_file docstring
    @classmethod
    def load_csv_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.load_csv_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.load_csv_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.load_csv_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.load_csv_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.load_csv_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.load_csv_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.load_csv_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.load_xml_file docstring
    @classmethod
    def load_xml_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.load_xml_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.load_xml_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.load_xml_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.load_xml_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.load_xml_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.load_xml_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.load_xml_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.load_json_file docstring
    @classmethod
    def load_json_file(cls, json_or_path):
        # logger.debug("ENTER ExpenseForecastInitialConditions.loadJSON")
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.load_json_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.load_json_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.load_json_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        json_or_path : str | Path
            #TODO DOC one-line description of ExpenseForecastInitialConditions.load_json_file.json_or_path.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.load_json_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.load_json_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.load_json_file.

        @interface-report: show
        """
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

    # TODO fix pylance type warning for IO::initialize_from_dict
    #TODO DOC manual review of ExpenseForecastInitialConditions.initialize_from_dict docstring
    @classmethod
    def initialize_from_dict(cls, data: dict):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.initialize_from_dict.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.initialize_from_dict.
        #TODO DOC explain how ExpenseForecastInitialConditions.initialize_from_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        data : dict
            #TODO DOC one-line description of ExpenseForecastInitialConditions.initialize_from_dict.data.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.initialize_from_dict.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.initialize_from_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.initialize_from_dict.

        @interface-report: show
        """
        return cls(
            start_date=cls._date_from_dict_value(data["start_date"]),
            end_date=cls._date_from_dict_value(data["end_date"]),
            account_set=cls._account_set_from_dict(data["account_set"]),
            line_item_set=cls._line_item_set_from_dict(data["line_item_set"]),
            memo_rule_set=cls._memo_rule_set_from_dict(data["memo_rule_set"]),
            milestone_set=cls._object_from_json_data(
                data.get("milestone_set")
            ) or MilestoneSet(),
            transitions=cls._object_from_json_data(
                data.get("transitions")
            ) or ConditionalScenarioTransitionSet(),
            policy_program=cls._object_from_json_data(
                data.get("policy_program")
            ) or PolicyProgram(
                cls._object_from_json_data(data.get("policy_set"))
                or ForecastPolicySet()
            ),
        ) #TODO forecast name

    #TODO DOC manual review of ExpenseForecastInitialConditions.load_database_tables docstring
    @classmethod
    def load_database_tables(cls):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.load_database_tables.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.load_database_tables.
        #TODO DOC explain how ExpenseForecastInitialConditions.load_database_tables participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.load_database_tables takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.load_database_tables.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.load_database_tables.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.load_database_tables.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.load_excel_file docstring
    @classmethod
    def load_excel_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.load_excel_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.load_excel_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.load_excel_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.load_excel_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.load_excel_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.load_excel_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.load_excel_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.load_pickle_file docstring
    @classmethod
    def load_pickle_file(cls):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.load_pickle_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.load_pickle_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.load_pickle_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.load_pickle_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.load_pickle_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.load_pickle_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.load_pickle_file.

        @interface-report: show
        """
        raise NotImplementedError

    # Instance methods for exporting data to strings
    #TODO DOC manual review of ExpenseForecastInitialConditions.to_csv_string docstring
    def to_csv_string(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.to_csv_string.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.to_csv_string.
        #TODO DOC explain how ExpenseForecastInitialConditions.to_csv_string participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.to_csv_string takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.to_csv_string.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.to_csv_string.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.to_csv_string.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.to_xml_string docstring
    def to_xml_string(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.to_xml_string.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.to_xml_string.
        #TODO DOC explain how ExpenseForecastInitialConditions.to_xml_string participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.to_xml_string takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.to_xml_string.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.to_xml_string.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.to_xml_string.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.to_json docstring
    def to_json(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.to_json.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.to_json.
        #TODO DOC explain how ExpenseForecastInitialConditions.to_json participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.to_json.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.to_json.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.to_json.

        @interface-report: show
        """
        return json.dumps(self.to_dict(), indent=4)

    # Instance methods for writing data to external sources
    #TODO DOC manual review of ExpenseForecastInitialConditions.write_csv_file docstring
    def write_csv_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.write_csv_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.write_csv_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.write_csv_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.write_csv_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.write_csv_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.write_csv_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.write_csv_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.write_xml_file docstring
    def write_xml_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.write_xml_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.write_xml_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.write_xml_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.write_xml_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.write_xml_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.write_xml_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.write_xml_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.write_json_file docstring
    def write_json_file(self, path_to_json):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.write_json_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.write_json_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.write_json_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        path_to_json : str | Path
            #TODO DOC one-line description of ExpenseForecastInitialConditions.write_json_file.path_to_json.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.write_json_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.write_json_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.write_json_file.

        @interface-report: show
        """
        return self.dumpJSON(path_to_json)

    #TODO DOC manual review of ExpenseForecastInitialConditions.dumpJSON docstring
    def dumpJSON(self, path_to_json):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.dumpJSON.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.dumpJSON.
        #TODO DOC explain how ExpenseForecastInitialConditions.dumpJSON participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        path_to_json : str | Path
            #TODO DOC one-line description of ExpenseForecastInitialConditions.dumpJSON.path_to_json.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.dumpJSON.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.dumpJSON.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.dumpJSON.

        @interface-report: show
        """
        target_path = Path(path_to_json)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(self.to_json())
        return True

    #TODO DOC manual review of ExpenseForecastInitialConditions.writeToJSONFile docstring
    def writeToJSONFile(self, output_dir="./"):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.writeToJSONFile.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.writeToJSONFile.
        #TODO DOC explain how ExpenseForecastInitialConditions.writeToJSONFile participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        output_dir : object
            #TODO DOC one-line description of ExpenseForecastInitialConditions.writeToJSONFile.output_dir.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.writeToJSONFile.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.writeToJSONFile.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.writeToJSONFile.

        @interface-report: show
        """
        output_path = Path(output_dir) / f"Forecast_{self.unique_id}.json"
        return self.dumpJSON(output_path)

    #TODO DOC manual review of ExpenseForecastInitialConditions.write_database_tables docstring
    def write_database_tables(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.write_database_tables.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.write_database_tables.
        #TODO DOC explain how ExpenseForecastInitialConditions.write_database_tables participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.write_database_tables takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.write_database_tables.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.write_database_tables.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.write_database_tables.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.write_excel_file docstring
    def write_excel_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.write_excel_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.write_excel_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.write_excel_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.write_excel_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.write_excel_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.write_excel_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.write_excel_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.write_pickle_file docstring
    def write_pickle_file(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.write_pickle_file.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.write_pickle_file.
        #TODO DOC explain how ExpenseForecastInitialConditions.write_pickle_file participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.write_pickle_file takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.write_pickle_file.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.write_pickle_file.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.write_pickle_file.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO DOC manual review of ExpenseForecastInitialConditions.to_dict docstring
    def to_dict(self):
        """
        #TODO DOC one-line description of ExpenseForecastInitialConditions.to_dict.

        #TODO DOC multi-line description of ExpenseForecastInitialConditions.to_dict.
        #TODO DOC explain how ExpenseForecastInitialConditions.to_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ExpenseForecastInitialConditions.to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            #TODO DOC one-line description of return value of ExpenseForecastInitialConditions.to_dict.

        Contract
        --------
        - #TODO DOC contract lines for ExpenseForecastInitialConditions.to_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ExpenseForecastInitialConditions.to_dict.

        @interface-report: show
        """
        policy_program = copy.deepcopy(self.policy_program)
        if not policy_program.dated_changes:
            # Preserve the long-standing mutable ``policy_set`` compatibility
            # view for callers that update a policy after construction.
            policy_program.base_policy_set = copy.deepcopy(self.policy_set)
        return {
            "unique_id": self.unique_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "account_set": self.initial_account_set.to_dict(),
            "line_item_set": self.initial_line_item_set.to_dict(),
            "memo_rule_set": self.initial_memo_rule_set.to_dict(),
            "milestone_set": self._object_to_json_data(self.milestone_set),
            "transitions": self._object_to_json_data(self.transitions),
            "policy_set": self._object_to_json_data(self.policy_set),
            "policy_program": self._object_to_json_data(policy_program),
        }
