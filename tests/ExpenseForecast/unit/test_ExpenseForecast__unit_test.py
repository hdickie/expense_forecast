import unittest, pytest

from expense_forecast.AccountMilestone import AccountMilestone
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
import pandas as pd, numpy as np
import datetime, logging
import tempfile
from expense_forecast.BudgetItem import BudgetItem
from expense_forecast.CompositeMilestone import CompositeMilestone
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.MemoRule import MemoRule

from datetime import date

pd.options.mode.chained_assignment = (
    None  # apparently this warning can throw false positives???
)
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.log_methods import log_in_color
from expense_forecast.Account import Account
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.MemoRuleSet import MemoRuleSet
import copy

from expense_forecast.generate_date_sequence import generate_date_sequence

# from log_methods import setup_logger
# logger = setup_logger('test_ExpenseForecast', './log/test_ExpenseForecast.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

from expense_forecast.log_methods import display_test_result


def _diff_column_to_actual_column_name(column_name):
    return column_name.removesuffix(" (Diff) ").removesuffix(" (Diff)")


def _format_forecast_numeric_value(value):
    if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value):
        return f"{value:.2f}"
    return value


def _format_forecast_difference_message(
    comparison_df_diffs_only,
    comparison_df,
    actual_df,
    expected_df,
    diff_columns,
    max_rows=25,
):
    mismatch_rows = []
    for row_index, row in comparison_df_diffs_only.iterrows():
        for diff_column in diff_columns:
            diff_value = row[diff_column]
            if pd.isna(diff_value) or diff_value == 0:
                continue

            actual_column = _diff_column_to_actual_column_name(diff_column)
            expected_column = f"{actual_column} (Expected)"
            expected_value = (
                comparison_df.at[row_index, expected_column]
                if expected_column in comparison_df.columns
                else expected_df.at[row_index, actual_column]
            )
            actual_value = (
                comparison_df.at[row_index, actual_column]
                if actual_column in comparison_df.columns
                else actual_df.at[row_index, actual_column]
            )
            mismatch_rows.append(
                {
                    "Date": row.get("Date", row_index),
                    "Column": actual_column,
                    "Expected": _format_forecast_numeric_value(expected_value),
                    "Actual": _format_forecast_numeric_value(actual_value),
                    "Diff": _format_forecast_numeric_value(diff_value),
                }
            )

    mismatch_df = pd.DataFrame(mismatch_rows)
    if mismatch_df.empty:
        return "Forecast comparison failed, but no nonzero diff cells were found."

    truncated_message = ""
    if mismatch_df.shape[0] > max_rows:
        truncated_message = (
            f"\n\nShowing first {max_rows} of {mismatch_df.shape[0]} mismatches."
        )
        mismatch_df = mismatch_df.head(max_rows)

    return (
        "Forecast numeric values did not match expected results.\n\n"
        + mismatch_df.to_string(index=False)
        + truncated_message
    )


def checking_acct_list(balance):
    A = AccountSet([])
    A.createCheckingAccount(
        "Checking",
        balance=balance,
        min_balance=0,
        max_balance=100000,
        primary_checking_ind=True,
    )
    return A.accounts


def credit_acct_list(curr_balance, prev_balance, apr):
    A = AccountSet([])
    A.createAccount(
        name="Credit",
        balance=curr_balance + prev_balance,
        min_balance=0,
        max_balance=20000,
        account_type="credit",
        billing_start_date=datetime.datetime.strptime("20000102",'%Y%m%d'),
        #interest_type=None,
        apr=apr,
        interest_cadence="monthly",
        minimum_payment=40,
        previous_statement_balance=prev_balance,
        current_statement_balance=curr_balance,
        end_of_previous_cycle_balance=prev_balance,
    )
    return A.accounts


def credit_bsd12_acct_list(prev_balance, curr_balance, apr):
    A = AccountSet([])
    A.createAccount(
        name="Credit",
        balance=curr_balance + prev_balance,
        min_balance=0,
        max_balance=20000,
        account_type="credit",
        billing_start_date=datetime.datetime.strptime("20000112",'%Y%m%d'),
        apr=apr,
        interest_cadence="monthly",
        minimum_payment=40,
        previous_statement_balance=prev_balance,
        current_statement_balance=curr_balance,
        end_of_previous_cycle_balance=prev_balance,
    )
    return A.accounts


def txn_budget_item_once_list(
    amount, priority, memo, **kwargs
):

    return [
        BudgetItem(
            datetime.datetime.strptime("20000102",'%Y%m%d'),
            datetime.datetime.strptime("20000102",'%Y%m%d'),
            priority,
            "once",
            amount,
            memo,
            deferrable=kwargs.get('deferrable', False),
            partial_payment_allowed=kwargs.get('partial_payment_allowed', False)
            # {'deferrable':deferrable,
            #  'partial_payment_allowed': partial_payment_allowed}
        )
    ]


def match_all_p1_checking_memo_rule_list():
    return [MemoRule(".*", "Checking", None, 1)]


def match_p1_test_txn_checking_memo_rule_list():
    return [MemoRule("test txn", "Checking", None, 1)]


def match_p1_test_txn_credit_memo_rule_list():
    return [MemoRule("test txn", "Credit", None, 1)]


def income_rule_list():
    return [MemoRule(".*income.*", None, "Checking", 1)]


def non_trivial_loan(name, pbal, interest, apr):
    A = AccountSet([])
    A.createAccount(
        name=name,
        balance=pbal + interest,
        min_balance=0,
        max_balance=9999,
        account_type="loan",
        billing_start_date=datetime.datetime.strptime("20000102",'%Y%m%d'),
        apr=apr,
        interest_cadence="daily",
        minimum_payment=50,
        principal_balance=pbal,
        interest_balance=interest,
        billing_cycle_payment_balance=0,
    )

    return A.accounts


def credit_bsd12_w_eopc_acct_list(
    prev_balance, curr_balance, apr, end_of_prev_cycle_balance
):
    A = AccountSet([])
    A.createAccount(
        name="Credit",
        balance=curr_balance + prev_balance,
        min_balance=0,
        max_balance=20000,
        account_type="credit",
        billing_start_date=datetime.datetime.strptime("19990112",'%Y%m%d'),
        apr=apr,
        interest_cadence="monthly",
        minimum_payment=40,
        previous_statement_balance=prev_balance,
        current_statement_balance=curr_balance,
        end_of_previous_cycle_balance=end_of_prev_cycle_balance,
    )
    return A.accounts


class TestExpenseForecastInitialConditionsUnit:

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_set,budget_set,memo_rule_set,start_date,end_date",
        [
            (
                AccountSet(checking_acct_list(10)),
                BudgetSet(
                    txn_budget_item_once_list(10, 1, "test txn")
                ),
                MemoRuleSet(match_p1_test_txn_checking_memo_rule_list()),
                "19991231",
                "20000101",
            )
            # (AccountSet([]),
            #  BudgetSet([]),
            #  MemoRuleSet([]),
            #  start_date,
            #  end_date,
            #  MilestoneSet([])
            #  ),
        ],
    )
    def test_ExpenseForecastInitialConditions_Constructor__valid_inputs(
        self,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
    ):
        ExpenseForecastInitialConditions(
            datetime.datetime.strptime(start_date, "%Y%m%d").date(),
            datetime.datetime.strptime(end_date, "%Y%m%d").date(),
            account_set,
            budget_set,
            memo_rule_set,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_set,budget_set,memo_rule_set,start_date,end_date,expected_exception",
        [
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "incorrect date format",
                "20000103",
                ValueError,
            ),  # malformed start date
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "20000101",
                "incorrect date format",
                ValueError,
            ),  # malformed end date
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "20000101",
                "19991231",
                ValueError,
            ),  # end date before start date
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "19991231",
                "20000101",
                ValueError,
            ),  # empty account_set
            (
                AccountSet(checking_acct_list(10)),
                BudgetSet(
                    txn_budget_item_once_list(10, 1, "test txn", )
                ),
                MemoRuleSet([]),
                "19991231",
                "20000101",
                ValueError,
            ),  # A budget memo x priority element does not have a matching regex in memo rule set
            (
                AccountSet(checking_acct_list(10)),
                BudgetSet(
                    txn_budget_item_once_list(10, 1, "test txn", )
                ),
                MemoRuleSet(match_p1_test_txn_credit_memo_rule_list()),
                "19991231",
                "20000101",
                ValueError,
            ),  # A memo rule has an account that does not exist in AccountSet
            # (AccountSet([]),
            #  BudgetSet([]),
            #  MemoRuleSet([]),
            #  'start_date',
            #  'end_date',
            #  MilestoneSet(
            #      [],
            #      [],
            #      []),
            #  ValueError
            #  ),
        ],
    )
    def test_ExpenseForecastInitialConditions_Constructor__invalid_inputs(
        self,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        expected_exception,
    ):
        with pytest.raises(expected_exception):
            ExpenseForecastInitialConditions(
                datetime.datetime.strptime(start_date, "%Y%m%d").date(),
                datetime.datetime.strptime(end_date, "%Y%m%d").date(),
                account_set,
                budget_set,
                memo_rule_set,
            )

    def compute_forecast_and_actual_vs_expected(
        self,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
        test_description,
    ):

        IO = ExpenseForecastInitialConditions(
            datetime.datetime.strptime(start_date, "%Y%m%d").date(),
            datetime.datetime.strptime(end_date, "%Y%m%d").date(),
            account_set,
            budget_set,
            memo_rule_set,
        )
        F = ForecastHandler()
        R = F.runForecast(IO, milestone_set, include_debug_columns=True)
        # E.forecast_df.to_csv(test_description+'.csv')
        comparison_df_diffs_only = F.compute_forecast_difference(
            copy.deepcopy(R.forecast_df),
            copy.deepcopy(expected_result_df),
            label=test_description,
            make_plots=False,
            diffs_only=True,
            require_matching_columns=True,
            require_matching_date_range=True,
            append_expected_values=False,
            return_type="dataframe",
        )

        comparison_df = F.compute_forecast_difference(
            copy.deepcopy(R.forecast_df),
            copy.deepcopy(expected_result_df),
            label=test_description,
            make_plots=False,
            diffs_only=False,
            require_matching_columns=True,
            require_matching_date_range=True,
            append_expected_values=True,
            return_type="dataframe",
        )

        # print(f.T.to_string()) #TODO log_in_color

        try:
            # log_in_color(
            #     logger, "white", "debug", "###################################"
            # )
            # log_in_color(logger, "white", "debug", diff.to_string())
            # log_in_color(
            #     logger, "white", "debug", "###################################"
            # )
            # log_in_color(logger, "white", "debug", diff2.T.to_string())
            # log_in_color(
            #     logger, "white", "debug", "###################################"
            # )
            display_test_result(logger, test_description, comparison_df_diffs_only)
        except Exception as e:
            raise e

        try:
            boilerplate_columns = {
                "Date",
                "Memo",
                "Memo Directives",
                "Next Income Date",
            }
            non_boilerplate_columns = [
                column
                for column in comparison_df_diffs_only.columns
                if column not in boilerplate_columns
            ]

            non_boilerplate_values = comparison_df_diffs_only.loc[
                :, non_boilerplate_columns
            ].to_numpy()

            if not np.all(non_boilerplate_values == 0):
                raise AssertionError(
                    _format_forecast_difference_message(
                        comparison_df_diffs_only=comparison_df_diffs_only,
                        comparison_df=comparison_df,
                        actual_df=R.forecast_df,
                        expected_df=expected_result_df,
                        diff_columns=non_boilerplate_columns,
                    )
                )

            try:
                for i in range(0, expected_result_df.shape[0]):
                    assert (
                        expected_result_df.loc[i, "Memo"].strip()
                        == R.forecast_df.loc[i, "Memo"].strip()
                    )
            except Exception as e:
                log_in_color(
                    logger, "red", "error", "Forecasts matched but the memo did not"
                )
                date_memo1_memo2_df = pd.DataFrame()
                date_memo1_memo2_df["Date"] = expected_result_df.Date
                date_memo1_memo2_df["Expected_Memo"] = expected_result_df.Memo
                date_memo1_memo2_df["Actual_Memo"] = R.forecast_df.Memo
                log_in_color(logger, "red", "error", date_memo1_memo2_df.to_string())
                raise e

            try:
                for i in range(0, expected_result_df.shape[0]):
                    assert (
                        expected_result_df.loc[i, "Memo Directives"].strip()
                        == R.forecast_df.loc[i, "Memo Directives"].strip()
                    )
            except Exception as e:
                log_in_color(
                    logger,
                    "red",
                    "error",
                    "Forecasts and memo matched but the Memo Directives did not",
                )
                date_memo1_memo2_df = pd.DataFrame()
                date_memo1_memo2_df["Date"] = expected_result_df.Date
                date_memo1_memo2_df["Expected_Memo_Directives"] = expected_result_df[
                    "Memo Directives"
                ]
                date_memo1_memo2_df["Actual_Memo_Directives"] = R.forecast_df[
                    "Memo Directives"
                ]
                log_in_color(logger, "red", "error", date_memo1_memo2_df.to_string())
                raise e

            try:
                for i in range(0, expected_result_df.shape[0]):
                    expected_next_income_date = ForecastHandler._normalize_date_value(
                        expected_result_df.loc[i, "Next Income Date"]
                    )
                    actual_next_income_date = ForecastHandler._normalize_date_value(
                        R.forecast_df.loc[i, "Next Income Date"]
                    )
                    assert (
                        expected_next_income_date
                        == actual_next_income_date
                    )
            except Exception as e:
                log_in_color(
                    logger,
                    "red",
                    "error",
                    "Forecasts, Memo and Md matched, but next_income_date did not",
                )
                date_id1_id2_df = pd.DataFrame()
                date_id1_id2_df["Date"] = expected_result_df.Date
                date_id1_id2_df["Expected Next Income Date"] = expected_result_df[
                    "Next Income Date"
                ]
                date_id1_id2_df["Actual Next Income Date"] = R.forecast_df[
                    "Next Income Date"
                ]
                log_in_color(logger, "red", "error", date_id1_id2_df.to_string())
                raise e

        except Exception as e:
            # print(test_description) #todo use log methods
            # print(f.T.to_string())
            raise e

        return R 


    @pytest.mark.unit
    def test_multiple_matching_memo_rule_regex(self):

        start_date = date(2000,1,1)
        end_date = date(2000,1,3)

        account_set = AccountSet([])
        budget_set = BudgetSet([])
        memo_rule_set = MemoRuleSet([])

        account_set.createAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("Inf"),
            account_type="checking",
            primary_checking_ind=True,
        )

        account_set.createAccount(
            name="Credit",
            balance=0,
            min_balance=0,
            max_balance=20000,
            account_type="credit",
            billing_start_date=date(2000,1,2),
            apr=0.05,
            interest_cadence="monthly",
            minimum_payment=40,
            previous_statement_balance=0,
            current_statement_balance=0,
            end_of_previous_cycle_balance=0,
        )

        budget_set.addBudgetItem(
            start_date=date(2000,1,2),
            end_date=date(2000,1,2),
            priority=2,
            cadence="once",
            amount=0,
            memo="test memo"
        )

        memo_rule_set.addMemoRule(
            memo_regex=".*",
            account_from="Credit",
            account_to=None,
            transaction_priority=1,
        )
        memo_rule_set.addMemoRule(
            memo_regex=".*",
            account_from="Credit",
            account_to=None,
            transaction_priority=2,
        )
        memo_rule_set.addMemoRule(
            memo_regex="test memo",
            account_from="Credit",
            account_to=None,
            transaction_priority=2,
        )

        milestone_set = MilestoneSet()

        with pytest.raises(ValueError):
            ExpenseForecastInitialConditions(
                start_date,
                end_date,
                account_set,
                budget_set,
                memo_rule_set,
            )

        # expected_result_df = pd.DataFrame({
        #     'Date': ['20000101', '20000102', '20000103'],
        #     'Checking': [1000, 1000, 1000],
        #     'Credit: Curr Stmt Bal': [0, 0, 0],
        #     'Credit: Prev Stmt Bal': [0, 0, 0],
        #     'Memo': ['', '', '']
        # })
        # expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
        #                            expected_result_df.Date]
        #
        # E = self.compute_forecast_and_actual_vs_expected(account_set,
        #                                                  budget_set,
        #                                                  memo_rule_set,
        #                                                  start_date,
        #                                                  end_date,
        #                                                  expected_result_df,
        #                                                  test_description)

    @pytest.mark.skip(reason="__str__ for ExpenseForecastInitialConditions. Not sure this needs a programmatic test bc __str__ is meant for human readability.")
    def test_str(self):
        start_date = "20000101"
        end_date = "20000103"

        account_set = AccountSet([])
        budget_set = BudgetSet([])
        memo_rule_set = MemoRuleSet([])

        account_set.createAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("Inf"),
            account_type="checking",
            primary_checking_ind=True,
        )

        account_set.createAccount(
            name="Credit",
            balance=0,
            min_balance=0,
            max_balance=20000,
            account_type="credit",
            billing_start_date=datetime.datetime.strptime("20000102", "%Y%m%d"),
            apr=0.05,
            interest_cadence="monthly",
            minimum_payment=40,
            previous_statement_balance=0,
            current_statement_balance=0,
            end_of_previous_cycle_balance=0,
        )

        budget_set.addBudgetItem(
            start_date="20000101",
            end_date="20000103",
            priority=1,
            cadence="daily",
            amount=0,
            memo="dummy memo"
        )

        memo_rule_set.addMemoRule(
            memo_regex=".*",
            account_from="Credit",
            account_to=None,
            transaction_priority=1,
        )

        expected_result_df = pd.DataFrame(
            {
                "Date": ["20000101", "20000102", "20000103"],
                "Checking": [1000, 0, 0],
                "Credit": [
                    curr + prev
                    for curr, prev in zip(
                        [0, 0, 0]
                        ,
                        [0, 0, 0]
                    )
                ],
                "Credit: Curr Stmt Bal": [0, 0, 0],
                "Credit: Prev Stmt Bal": [0, 0, 0],
                "Credit: Credit Billing Cycle Payment Bal": [0, 0, 0],
                "Memo": ["", "", ""],
            }
        )
        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        milestone_set = MilestoneSet([], [], [])

        E = ExpenseForecastInitialConditions(
            datetime.datetime.strptime(start_date, "%Y%m%d").date(),
            datetime.datetime.strptime(end_date, "%Y%m%d").date(),
            account_set,
            budget_set,
            memo_rule_set,
        )

        str(E)

        E = ForecastHandler().runForecast(E, milestone_set)

        str(E)

    @pytest.mark.unit
    def test_initialize_from_dict(self):
        original = ExpenseForecastInitialConditions(
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31),
            account_set=AccountSet(checking_acct_list(1000)),
            budget_set=BudgetSet([]),
            memo_rule_set=MemoRuleSet([]),
            milestone_set=MilestoneSet(),
        )

        data = original.to_dict()

        restored = ExpenseForecastInitialConditions.initialize_from_dict(data)

        assert restored.start_date == original.start_date
        assert restored.end_date == original.end_date

        pd.testing.assert_frame_equal(
            restored.initial_account_set.getAccounts(),
            original.initial_account_set.getAccounts(),
        )

        pd.testing.assert_frame_equal(
            restored.initial_budget_set.getBudgetItems(),
            original.initial_budget_set.getBudgetItems(),
        )

        pd.testing.assert_frame_equal(
            restored.initial_memo_rule_set.getMemoRules(),
            original.initial_memo_rule_set.getMemoRules(),
        )

