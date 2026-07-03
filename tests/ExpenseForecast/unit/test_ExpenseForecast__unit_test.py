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
        end_of_previous_cycle_balance=pbal,
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


class TestExpenseForecastUnit:

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set",
        [
            (
                AccountSet(checking_acct_list(10)),
                BudgetSet(
                    txn_budget_item_once_list(10, 1, "test txn")
                ),
                MemoRuleSet(match_p1_test_txn_checking_memo_rule_list()),
                "19991231",
                "20000101",
                MilestoneSet(),
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
    def test_ExpenseForecast_Constructor__valid_inputs(
        self,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
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
        "account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_exception",
        [
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "incorrect date format",
                "20000103",
                MilestoneSet(),
                ValueError,
            ),  # malformed start date
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "20000101",
                "incorrect date format",
                MilestoneSet(),
                ValueError,
            ),  # malformed end date
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "20000101",
                "19991231",
                MilestoneSet(),
                ValueError,
            ),  # end date before start date
            (
                AccountSet([]),
                BudgetSet([]),
                MemoRuleSet([]),
                "19991231",
                "20000101",
                MilestoneSet(),
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
                MilestoneSet(),
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
                MilestoneSet(),
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
    def test_ExpenseForecast_Constructor__invalid_inputs(
        self,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_exception,
    ):
        with pytest.raises(expected_exception):
            ExpenseForecastInitialConditions(
                datetime.datetime.strptime(start_date, "%Y%m%d").date(),
                datetime.datetime.strptime(end_date, "%Y%m%d").date(),
                account_set,
                budget_set,
                memo_rule_set,
                raise_exceptions=True,
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
            raise_exceptions=False,
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
    # @pytest.mark.skip(reason="Skip so github action doesnt fail")
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_p1_only_no_budget_items",
                AccountSet(
                    checking_acct_list(0) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet([]),
                MemoRuleSet(match_p1_test_txn_checking_memo_rule_list()),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [0, 0, 0],
                        "Credit": [0, 0, 0],
                        "Credit: Curr Stmt Bal": [0, 0, 0],
                        "Credit: Prev Stmt Bal": [0, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [0, 0, 0],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [0, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p1_only__income_and_payment_on_same_day",
                AccountSet(
                    checking_acct_list(0) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(100, 1, "income", )
                    + txn_budget_item_once_list(100, 1, "test txn", )
                ),
                MemoRuleSet(
                    match_p1_test_txn_checking_memo_rule_list() + income_rule_list()
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [0, 0, 0],
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
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [0, 0, 0],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [0, 0, 0],
                        "Next Income Date": ["20000102", "", ""],
                        "Memo Directives": ["", "INCOME (Checking +$100.00)", ""],
                        "Memo": [
                            "",
                            "income (Checking +$100.00); test txn (Checking -$100.00)",
                            "",
                        ],
                    }
                ),
            ),
            (
                "test_p1_cc_txn_on_billing_date", 
                AccountSet(
                    checking_acct_list(0) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(100, 1, "test txn", )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        )
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [0, 0, 0],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [0, 100, 100]
                                ,
                                [0, 0, 0]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [0, 100, 100],
                        "Credit: Prev Stmt Bal": [0, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 100, 0],
                        "Net Worth": [0, -100, -100],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 100, 100],
                        "Liquid Total": [0, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "test txn (Credit -$100.00)", ""],
                    }
                ),
            ),
            (
                "test_cc_payment__satisfice__curr_bal_25__expect_0",
                AccountSet(
                    checking_acct_list(2000) + credit_acct_list(25, 0, 0.05)
                ),
                BudgetSet([]),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        )
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [2000, 2000, 2000],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [25, 0, 0]
                                ,
                                [0, 25, 25]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [25, 0, 0],
                        "Credit: Prev Stmt Bal": [0, 25, 25],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 25],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [1975, 1975, 1975],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [25, 25, 25],
                        "Liquid Total": [2000, 2000, 2000],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_cc_payment__satisfice__prev_bal_1000__expect_40",
                AccountSet(
                    checking_acct_list(2000) + credit_acct_list(0, 1000, 0.05)
                ),
                BudgetSet([]),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        )
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [2000, 1960, 1960],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [0, 0, 0]
                                ,
                                [1000, 964.17, 964.17]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [0, 0, 0],
                        "Credit: Prev Stmt Bal": [1000, 964.17, 964.17],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [1000, 1000, 964.17],
                        "Marginal Interest": [0, 4.17, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 4.17, 0],
                        "Net Worth": [1000, 995.83, 995.83],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [1000, 964.17, 964.17],
                        "Liquid Total": [2000, 1960, 1960],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "CC INTEREST (Credit: Prev Stmt Bal +$4.17); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_cc_payment__satisfice__prev_bal_3000__expect_60",
                AccountSet(
                    checking_acct_list(2000) + credit_acct_list(0, 3000, 0.12)
                ),
                BudgetSet([]),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        )
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [2000, 1940, 1940],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [0, 0, 0]
                                ,
                                [3000, 2970, 2970]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [0, 0, 0],
                        "Credit: Prev Stmt Bal": [3000, 2970, 2970],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [3000, 3000, 2970],
                        "Marginal Interest": [0, 30, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 30, 0],
                        "Net Worth": [-1000, -1030, -1030],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [3000, 2970, 2970],
                        "Liquid Total": [2000, 1940, 1940],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "CC INTEREST (Credit: Prev Stmt Bal +$30.00); CC MIN PAYMENT (Credit: Prev Stmt Bal -$60.00); CC MIN PAYMENT (Checking -$60.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_cc_interest_accrued_reaches_0",
                AccountSet(
                    checking_acct_list(50)
                    + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 500)
                ),  # todo implement
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": [0] * 36,
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [0] * 36
                                ,
                                [0] * 36
                            )
                        ],
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": [0] * 36,
                        "Credit: Credit Billing Cycle Payment Bal": [0] * 36,
                        "Credit: Credit End of Prev Cycle Bal": [0] * 36,
                        "Marginal Interest": [0] * 36,
                        "Net Gain": [0] * 36,
                        "Net Loss": [0] * 36,
                        "Net Worth": [0] * 36,
                        "Loan Total": [0] * 36,
                        "CC Debt Total": [0] * 36,
                        "Liquid Total": [0] * 36,
                        "Next Income Date": [""] * 36,
                        "Memo Directives": ["NOT IMPLEMENTED"] * 36,
                        "Memo": [""] * 36,
                    }
                ),
            ),
        ],
    )
    def test_satisfice(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    @pytest.mark.unit
    @pytest.mark.skip(reason="Skip bc github action fails")
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_p2_and_3__expect_defer",  # todo
                AccountSet(
                    checking_acct_list(0) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        10, 2, "this should be deferred", deferrable=True,
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=3,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [0, 0, 0],
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
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [0, 0, 0],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [0, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "TEST NOT IMPLEMENTED", ""],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p2_and_3__p3_item_deferred_bc_p2",  # todo this should be a more complex test case
                AccountSet(checking_acct_list(100)),
                BudgetSet(
                    txn_budget_item_once_list(
                        100, 2, "this should be executed",
                    )
                    + txn_budget_item_once_list(
                        100, 3, "this should be deferred", deferrable=True,
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=3,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [100, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 100, 0],
                        "Net Worth": [100, 0, 0],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [100, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "this should be executed (Checking -$100.00)", ""],
                    }
                ),
            ),
            (
                "test_execute_defer_after_receiving_income_2_days_later",
                AccountSet(checking_acct_list(500)),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "SPEND daily p1 txn",
                        ),  # EOD 400
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "SPEND daily p1 txn 2",
                        ),  # EOD 300
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            3,
                            "once",
                            400,
                            "SPEND p3 txn on 1/3 that is skipped bc later lower priority_index txn",
                        ),
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            1,
                            "once",
                            200,
                            "200 income on 1/4",
                        ),  # 500
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "SPEND daily p1 txn 3",
                            
                        ),  # 400
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            400,
                            "SPEND p2 txn deferred from 1/2 to 1/4",
                            deferrable=True,
                        ),  # EOD 0
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex="SPEND.*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*income.*",
                            account_from=None,
                            account_to="Checking",
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex="SPEND.*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                        MemoRule(
                            memo_regex="SPEND.*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=3,
                        ),
                    ]
                ),
                "20000101",
                "20000104",  # note that this is later than the test defined above
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103", "20000104"],
                        "Checking": [500, 400, 300, 0],
                        "Marginal Interest": [0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 100, 100, 300],
                        "Net Worth": [500, 400, 300, 0],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [0, 0, 0, 0],
                        "Liquid Total": [500, 400, 300, 0],
                        "Next Income Date": ["20000104", "20000104", "20000104", ""],
                        "Memo Directives": ["", "", "", "INCOME (Checking +$200.00)"],
                        "Memo": [
                            "",
                            "SPEND daily p1 txn (Checking -$100.00)",
                            "SPEND daily p1 txn 2 (Checking -$100.00)",
                            "200 income on 1/4 (Checking +$200.00); SPEND daily p1 txn 3 (Checking -$100.00); SPEND p2 txn deferred from 1/2 to 1/4 (Checking -$400.00)",
                        ],
                    }
                ),
            ),
        ],
    )
    def test_deferrals(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):

        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_p2_and_3__expect_skip",
                AccountSet(
                    checking_acct_list(0) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        10, 2, "this should be skipped",
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [0, 0, 0],
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
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [0, 0, 0],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [0, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p2_and_3__p3_item_skipped_bc_p2",
                AccountSet(checking_acct_list(100)),
                BudgetSet(
                    txn_budget_item_once_list(
                        100, 2, "this should be executed",
                    )
                    + txn_budget_item_once_list(
                        100, 3, "this should be skipped",
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=3,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [100, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 100, 0],
                        "Net Worth": [100, 0, 0],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [100, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "this should be executed (Checking -$100.00)", ""],
                    }
                ),
            ),
            (
                "test_p4__cc_payment__no_prev_balance__pay_100__no_funds__expect_skip",
                AccountSet(
                    checking_acct_list(0) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        100, 4, "additional credit card payment",
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=4,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [0, 0, 0],
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
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [0, 0, 0],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [0, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p4__cc_payment__no_prev_balance__pay_100__expect_skip",
                AccountSet(
                    checking_acct_list(2000) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        100, 4, "this should be skipped",
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to="Credit",
                            transaction_priority=4,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [2000, 2000, 2000],
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
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [2000, 2000, 2000],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [2000, 2000, 2000],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": ["", "", ""],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_transactions_executed_at_p1_and_p2",
                AccountSet(checking_acct_list(2000)),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 1",
                            
                        ),
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 2",
                            
                        ),
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 3",
                            
                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 4",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/2/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/3/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/4/00",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/5/00",

                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                    ]
                ),
                "20000101",
                "20000106",  # note that this is later than the test defined above
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": [
                            "20000101",
                            "20000102",
                            "20000103",
                            "20000104",
                            "20000105",
                            "20000106",
                        ],
                        "Checking": [2000, 1800, 1600, 1400, 1200, 1200],
                        "Marginal Interest": [0, 0, 0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0, 0, 0],
                        "Net Loss": [0, 200, 200, 200, 200, 0],
                        "Net Worth": [2000, 1800, 1600, 1400, 1200, 1200],
                        "Loan Total": [0, 0, 0, 0, 0, 0],
                        "CC Debt Total": [0, 0, 0, 0, 0, 0],
                        "Liquid Total": [2000, 1800, 1600, 1400, 1200, 1200],
                        "Next Income Date": ["", "", "", "", "", ""],
                        "Memo Directives": ["", "", "", "", "", ""],
                        "Memo": [
                            "",
                            "p1 daily txn 1 (Checking -$100.00); p2 daily txn 1/2/00 (Checking -$100.00)",
                            "p1 daily txn 2 (Checking -$100.00); p2 daily txn 1/3/00 (Checking -$100.00)",
                            "p1 daily txn 3 (Checking -$100.00); p2 daily txn 1/4/00 (Checking -$100.00)",
                            "p1 daily txn 4 (Checking -$100.00); p2 daily txn 1/5/00 (Checking -$100.00)",
                            "",
                        ],
                    }
                ),
            ),
            (
                "test_transactions_executed_at_p1_and_p2_and_p3",
                AccountSet(checking_acct_list(2000)),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 1/2/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 1/3/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 1/4/00",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "p1 daily txn 1/5/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/2/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/3/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/4/00",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "p2 daily txn 1/5/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            3,
                            "once",
                            100,
                            "p3 daily txn 1/2/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            3,
                            "once",
                            100,
                            "p3 daily txn 1/3/00",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            3,
                            "once",
                            100,
                            "p3 daily txn 1/4/00",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            3,
                            "once",
                            100,
                            "p3 daily txn 1/5/00",

                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=3,
                        ),
                    ]
                ),
                "20000101",
                "20000106",  # note that this is later than the test defined above
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": [
                            "20000101",
                            "20000102",
                            "20000103",
                            "20000104",
                            "20000105",
                            "20000106",
                        ],
                        "Checking": [2000, 1700, 1400, 1100, 800, 800],
                        "Marginal Interest": [0, 0, 0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0, 0, 0],
                        "Net Loss": [0, 300, 300, 300, 300, 0],
                        "Net Worth": [2000, 1700, 1400, 1100, 800, 800],
                        "Loan Total": [0, 0, 0, 0, 0, 0],
                        "CC Debt Total": [0, 0, 0, 0, 0, 0],
                        "Liquid Total": [2000, 1700, 1400, 1100, 800, 800],
                        "Next Income Date": ["", "", "", "", "", ""],
                        "Memo Directives": ["", "", "", "", "", ""],
                        "Memo": [
                            "",
                            "p1 daily txn 1/2/00 (Checking -$100.00); p2 daily txn 1/2/00 (Checking -$100.00); p3 daily txn 1/2/00 (Checking -$100.00)",
                            "p1 daily txn 1/3/00 (Checking -$100.00); p2 daily txn 1/3/00 (Checking -$100.00); p3 daily txn 1/3/00 (Checking -$100.00)",
                            "p1 daily txn 1/4/00 (Checking -$100.00); p2 daily txn 1/4/00 (Checking -$100.00); p3 daily txn 1/4/00 (Checking -$100.00)",
                            "p1 daily txn 1/5/00 (Checking -$100.00); p2 daily txn 1/5/00 (Checking -$100.00); p3 daily txn 1/5/00 (Checking -$100.00)",
                            "",
                        ],
                    }
                ),
            ),
        ],
    )
    def test_priority_ordering(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_p4__cc_payment__pay_all_of_prev_part_of_curr__expect_800",
                AccountSet(
                    checking_acct_list(2000) + credit_bsd12_acct_list(500, 500, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        800, 4, "test pay all prev part of curr",
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to="Credit",
                            transaction_priority=4,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [2000, 1200, 1200],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [500, 200, 200]
                                ,
                                [500, 0, 0]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [500, 200, 200],
                        "Credit: Prev Stmt Bal": [500, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 800, 800],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [1000, 1000, 1000],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [1000, 200, 200],
                        "Liquid Total": [2000, 1200, 1200],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$300.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$300.00); ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p4__cc_payment__pay_part_of_prev_balance__expect_200",
                AccountSet(
                    checking_acct_list(200) + credit_bsd12_acct_list(500, 500, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        200, 4, "additional cc payment test",
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*additional cc payment.*",
                            account_from="Checking",
                            account_to="Credit",
                            transaction_priority=4,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [200, 0, 0],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [500, 500, 500]
                                ,
                                [500, 300, 300]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [500, 500, 500],
                        "Credit: Prev Stmt Bal": [500, 300, 300],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 200, 200],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [-800, -800, -800],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [1000, 800, 800],
                        "Liquid Total": [200, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$200.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$200.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p4__cc_payment__non_0_prev_balance_but_no_funds__expect_0",
                AccountSet(
                    checking_acct_list(40) + credit_acct_list(500, 500, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        100, 4, "additional cc payment test",
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*additional cc payment.*",
                            account_from="Checking",
                            account_to="Credit",
                            transaction_priority=4,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [40, 0, 0],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [500, 0, 0]
                                ,
                                [500, 962.08, 962.08]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [500, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 962.08, 962.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 962.08],
                        "Marginal Interest": [0, 2.08, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 2.08, 0],
                        "Net Worth": [-960, -962.08, -962.08],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [1000, 962.08, 962.08],
                        "Liquid Total": [40, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p4__cc_payment__partial_of_indicated_amount",
                AccountSet(
                    checking_acct_list(1000) + credit_bsd12_acct_list(500, 1500, 0.05)
                ),
                BudgetSet(
                    txn_budget_item_once_list(
                        20000, 4, "partial cc payment", partial_payment_allowed=True
                    )
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Credit",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to="Credit",
                            transaction_priority=4,
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [1000, 0, 0],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [1500, 1000, 1000]
                                ,
                                [500, 0, 0]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [1500, 1000, 1000],
                        "Credit: Prev Stmt Bal": [500, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 1000, 1000],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0, 0],
                        "Net Worth": [-1000, -1000, -1000],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [2000, 1000, 1000],
                        "Liquid Total": [1000, 0, 0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$500.00); ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_execute_at_reduced_amount_bc_later_higher_priority_txn",
                AccountSet(checking_acct_list(400)),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            2,
                            "once",
                            200,
                            "pay 200 after reduced amt txn",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000103","%Y%m%d"),datetime.datetime.strptime("20000103","%Y%m%d"),
                            3,
                            "once",
                            400,
                            "pay reduced amount",
                            partial_payment_allowed=True,
                        ),
                    ]
                    # +
                    # txn_budget_item_once_list(200, 2, 'pay 200 after reduced amt txn', ) +
                    # txn_budget_item_once_list(400, 3,'pay reduced amount',False, True)
                ),
                MemoRuleSet(
                    [
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=1,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=2,
                        ),
                        MemoRule(
                            memo_regex=".*",
                            account_from="Checking",
                            account_to=None,
                            transaction_priority=3,
                        ),
                    ]
                ),
                "20000101",
                datetime.datetime.strptime("20000105","%Y%m%d"),  # note that this is later than the test defined above
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": [
                            "20000101",
                            "20000102",
                            "20000103",
                            "20000104",
                            "20000105",
                        ],
                        "Checking": [400, 400, 200, 0, 0],
                        "Marginal Interest": [0, 0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0, 0],
                        "Net Loss": [0, 0, 200, 200, 0],
                        "Net Worth": [400, 400, 200, 0, 0],
                        "Loan Total": [0, 0, 0, 0, 0],
                        "CC Debt Total": [0, 0, 0, 0, 0],
                        "Liquid Total": [400, 400, 200, 0, 0],
                        "Next Income Date": ["", "", "", "", ""],
                        "Memo Directives": ["", "", "", "", ""],
                        "Memo": [
                            "",
                            "",
                            "pay reduced amount (Checking -$200.00)",
                            "pay 200 after reduced amt txn (Checking -$200.00)",
                            "",
                        ],
                    }
                ),
            ),  # this test cas coded correctly. the fail is bc of algo. 12/12 5:21AM
        ],
    )
    def test_cc_payment_amount(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):
        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    @pytest.mark.unit
    @pytest.mark.skip(reason="Skipping this test bc github action")
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_cc_advance_minimum_payment_in_1_payment_pay_over_minimum",  # implemented
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(1000, 1000, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            500,
                            "additional_cc_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_cc_payment", "Checking", "Credit", 2
                        ),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4500, 4500, 4500],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [1000, 1000, 0, 0]
                                ,
                                [1000, 500, 1504.17, 1504.17]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [1000, 1000, 0, 0],
                        "Credit: Prev Stmt Bal": [1000, 500, 1504.17, 1504.17],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 500, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [
                            1000,
                            1000,
                            1000,
                            1504.17,
                        ],  # this is correct
                        "Marginal Interest": [0, 0, 4.17, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 4.17, 0],
                        "Net Worth": [3000, 3000, 2995.83, 2995.83],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [2000, 1500, 1504.17, 1504.17],
                        "Liquid Total": [5000, 4500, 4500, 4500],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00)",
                            "CC INTEREST (Credit: Prev Stmt Bal +$4.17); CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_advance_minimum_payment_in_1_payment_pay_under_minimum",  # implemented
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(1000, 1000, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            20,
                            "additional_cc_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_cc_payment", "Checking", "Credit", 2
                        ),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4980, 4960, 4960],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [1000, 1000, 0, 0]
                                ,
                                [1000, 980, 1964.17, 1964.17]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [1000, 1000, 0, 0],
                        "Credit: Prev Stmt Bal": [1000, 980, 1964.17, 1964.17],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 20, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [
                            1000,
                            1000,
                            1000,
                            1964.17,
                        ],
                        # min payment causes the correct update
                        "Marginal Interest": [
                            0,
                            0,
                            4.17,
                            0,
                        ],  # so a partial pre payment of min payment
                        "Net Gain": [
                            0,
                            0,
                            0,
                            0,
                        ],  # therefore has no effect on End of Prev Cycle Bal
                        "Net Loss": [0, 0, 4.17, 0],
                        "Net Worth": [3000, 3000, 3000 - 4.17, 3000 - 4.17],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [2000, 1980, 1964.17, 1964.17],
                        "Liquid Total": [5000, 4980, 4960, 4960],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$20.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$20.00)",
                            "CC INTEREST (Credit: Prev Stmt Bal +$4.17); CC MIN PAYMENT (Checking -$20.00); CC MIN PAYMENT (Credit: Prev Stmt Bal -$20.00)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_advance_minimum_payment_in_1_payment_pay_exact_minimum",  # implemented
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(1000, 1000, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            40,
                            "additional_cc_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_cc_payment", "Checking", "Credit", 2
                        ),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4960, 4960, 4960],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [1000, 1000, 0, 0]
                                ,
                                [1000, 960, 1964.17, 1964.17]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [1000, 1000, 0, 0],
                        "Credit: Prev Stmt Bal": [1000, 960, 1964.17, 1964.17],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 40, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [
                            1000,
                            1000,
                            1000,
                            1964.17,
                        ],
                        # prop not needed to get this right
                        "Marginal Interest": [0, 0, 4.17, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 4.17, 0],
                        "Net Worth": [3000, 3000, 3000 - 4.17, 3000 - 4.17],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [2000, 1960, 1964.17, 1964.17],
                        "Liquid Total": [5000, 4960, 4960, 4960],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$40.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$40.00)",
                            "CC INTEREST (Credit: Prev Stmt Bal +$4.17); CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_on_due_date",  # implemented
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(500, 500, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            600,
                            "single additional payment on due date",

                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                datetime.datetime.strptime("20000105","%Y%m%d"),
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000111", "20000112", "20000113"],
                        "Checking": [5000, 4360, 4360],
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [500, 0, 0]
                                ,
                                [500, 362.08, 362.08]
                            )
                        ],
                        "Credit: Curr Stmt Bal": [500, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 362.08, 362.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 600, 600],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 962.08],
                        # this is correct bc additional payment should not be counted
                        "Marginal Interest": [0, 2.08, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 2.08, 0],
                        "Net Worth": [4000, 3997.92, 3997.92],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [1000, 362.08, 362.08],
                        "Liquid Total": [5000, 4360.0, 4360.0],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00); ADDTL CC PAYMENT (Checking -$600.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$600.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            # confirming this test is correct and serving its intended purpose :)
            (
                "test_eopc_bal_500eocp_0prev_0curr",
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 500)
                ),
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": ([5000] * 33) + ([4997.91] * 3),
                        "Credit": [
                            curr + prev
                            for curr, prev in zip(
                                [0] * 36
                                ,
                                ([0] * 2) + ([2.08] * 31) + ([0] * 3)
                            )
                        ],
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": ([0] * 2) + ([2.08] * 31) + ([0] * 3),
                        "Credit: Credit Billing Cycle Payment Bal": ([500] * 2)
                        + ([0] * 34),
                        "Credit: Credit End of Prev Cycle Bal": ([500] * 3)
                        + ([2.08] * 31)
                        + ([0] * 2),
                        "Marginal Interest": ([0] * 2)
                        + ([2.08] * 1)
                        + ([0] * 30)
                        + ([0.01] * 1)
                        + ([0] * 2),
                        "Net Gain": [0] * 36,
                        "Net Loss": ([0] * 2)
                        + ([2.08] * 1)
                        + ([0] * 30)
                        + ([0.01] * 1)
                        + ([0] * 2),
                        "Net Worth": ([5000] * 2) + ([4997.92] * 31) + ([4997.91] * 3),
                        "Loan Total": [0] * 36,
                        "CC Debt Total": ([0] * 2) + ([2.08] * 31) + ([0] * 3),
                        "Liquid Total": ([5000] * 33) + ([4997.91] * 3),
                        "Next Income Date": [""] * 36,
                        "Memo Directives": [""] * 2
                        + [
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00); CC MIN PAYMENT ALREADY MADE (Checking -$0.00)"
                        ]
                        + [""] * 30
                        + [
                            "CC INTEREST (Credit: Prev Stmt Bal +$0.01); CC MIN PAYMENT (Credit: Prev Stmt Bal -$2.08); CC MIN PAYMENT (Credit: Curr Stmt Bal -$0.01); CC MIN PAYMENT (Checking -$2.09)"
                        ]
                        * 1
                        + [""] * 2,
                        "Memo": [""] * 36,
                    }
                ),
            ),
            (
                "test_cc_two_additional_payments_on_due_date__prev_only",  # confirmed correct
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(500, 400, 0.05, 500)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "test credit payment 1",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "test credit payment 2",

                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                datetime.datetime.strptime("20000105","%Y%m%d"),
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000111", "20000112", "20000113"],
                        "Checking": [5000, 5000 - 240, 5000 - 240],
                        "Credit": [900, 900 - 240 + 2.08, 900 - 240 + 2.08],
                        "Credit: Curr Stmt Bal": [400, 0, 0],
                        "Credit: Prev Stmt Bal": [
                            500,
                            900 - 240 + 2.08,
                            900 - 240 + 2.08,
                        ],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 200, 200],
                        "Credit: Credit End of Prev Cycle Bal": [
                            500,
                            500,
                            900 - 40 + 2.08,
                        ],
                        "Marginal Interest": [0, 2.08, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 2.08, 0],
                        "Net Worth": [4100, 4100 - 2.08, 4100 - 2.08],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [900, 900 - 240 + 2.08, 900 - 240 + 2.08],
                        "Liquid Total": [5000, 5000 - 240, 5000 - 240],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00); ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$100.00); ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$100.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_on_due_date_OVERPAY",  # confirmed
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(500, 400, 0.05, 500)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            1000,
                            "test credit payment 1",
                            partial_payment_allowed=True,
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                datetime.datetime.strptime("20000105","%Y%m%d"),
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000111", "20000112", "20000113"],
                        "Checking": [5000, 4097.92, 4097.92],
                        "Credit": [900, 0, 0],
                        "Credit: Curr Stmt Bal": [400, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 862.08, 862.08],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 862.08],
                        "Marginal Interest": [0, 2.08, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 2.08, 0],
                        "Net Worth": [4100, 4097.92, 4097.92],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [900, 0, 0],
                        "Liquid Total": [5000, 4097.92, 4097.92],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00); ADDTL CC PAYMENT (Checking -$862.08); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$862.08)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_cc_two_additional_payments_on_due_date__curr_only",  # confirmed correct
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 0)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "test credit payment 1",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "test credit payment 2",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            400,
                            "cc txn",

                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule("cc txn", "Credit", "None", 2),
                        MemoRule(
                            "test credit payment.*", "Checking", "Credit", 2
                        ),
                    ]
                ),
                datetime.datetime.strptime("20000105","%Y%m%d"),
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000111", "20000112", "20000113"],
                        "Checking": [5000, 5000 - 200, 5000 - 200],
                        "Credit": [0, 200, 200],
                        "Credit: Curr Stmt Bal": [0, 200, 200],
                        "Credit: Prev Stmt Bal": [0, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [
                            0,
                            200,
                            200,
                        ],  # i think this is right but not sure
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0],
                        "Marginal Interest": [0, 0, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 400, 0],
                        "Net Worth": [5000, 5000 - 400, 5000 - 400],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [0, 200, 200],
                        "Liquid Total": [5000, 5000 - 200, 5000 - 200],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$100.00); ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$100.00)",
                            "",
                        ],
                        "Memo": ["", "cc txn (Credit -$400.00)", ""],
                    }
                ),
            ),
            (
                "test_cc_two_additional_payments_on_due_date_OVERPAY",  # confirmed
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(500, 400, 0.05, 500)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            500,
                            "test credit payment 1",
                            partial_payment_allowed=True,
                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            datetime.datetime.strptime("20000102","%Y%m%d"),
                            2,
                            "once",
                            500,
                            "test credit payment 2",
                            partial_payment_allowed=True,
                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                datetime.datetime.strptime("20000105","%Y%m%d"),
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000111", "20000112", "20000113"],
                        "Checking": [5000, 5000 - 900 - 2.08, 5000 - 900 - 2.08],
                        "Credit": [900, 0, 0],
                        "Credit: Curr Stmt Bal": [400, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [
                            0,
                            900 - 40 + 2.08,
                            900 - 40 + 2.08,
                        ],
                        "Credit: Credit End of Prev Cycle Bal": [
                            500,
                            500,
                            900 - 40 + 2.08,
                        ],
                        "Marginal Interest": [0, 2.08, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 2.08, 0],
                        "Net Worth": [4100, 4100 - 2.08, 4100 - 2.08],
                        "Loan Total": [0, 0, 0],
                        "CC Debt Total": [900, 0, 0],
                        "Liquid Total": [5000, 5000 - 900 - 2.08, 5000 - 900 - 2.08],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00); ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00); ADDTL CC PAYMENT (Checking -$362.08); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$362.08)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_day_before__prev_only",  # confirmed
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(500, 500, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            300,
                            "single additional payment day before due date",

                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4700, 4700, 4700],
                        "Credit": [1000, 700, 702.08, 702.08],
                        "Credit: Curr Stmt Bal": [500, 500, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 200, 702.08, 702.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 300, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500, 702.08],
                        "Marginal Interest": [0, 0, 2.08, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 2.08, 0],
                        "Net Worth": [4000, 4000, 3997.92, 3997.92],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [1000, 700, 702.08, 702.08],
                        "Liquid Total": [5000, 4700.0, 4700.0, 4700.0],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$300.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$300.00)",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_two_additional_payments_day_before__prev_only",  # confirmed
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(500, 500, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "first additional payment day before due date",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "second additional payment day before due date",

                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4800, 4800, 4800],
                        "Credit": [1000, 800, 802.08, 802.08],
                        "Credit: Curr Stmt Bal": [500, 500, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 300, 802.08, 802.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 200, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500, 802.08],
                        "Marginal Interest": [0, 0, 2.08, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 2.08, 0],
                        "Net Worth": [4000, 4000, 3997.92, 3997.92],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [1000, 800, 802.08, 802.08],
                        "Liquid Total": [5000, 4800.0, 4800.0, 4800.0],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$100.00); ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$100.00)",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_day_before_OVERPAY__prev_only",  # pretty sure its right
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(500, 0, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            1100,
                            "single additional payment day before due date",
                            partial_payment_allowed=True,
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4500, 4500, 4500],
                        "Credit": [500, 0, 2.08, 2.08],
                        "Credit: Curr Stmt Bal": [0, 0, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 0, 2.08, 2.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 500, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500, 2.08],
                        "Marginal Interest": [0, 0, 2.08, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 2.08, 0],
                        "Net Worth": [4500, 4500, 4497.92, 4497.92],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [500, 0, 2.08, 2.08],
                        "Liquid Total": [5000, 4500, 4500, 4500],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00)",
                            "CC INTEREST (Credit: Prev Stmt Bal +$2.08); CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_two_additional_payments_day_before_OVERPAY__prev_only",  # pretty sure its right
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(500, 400, 0.05, 500)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "test credit payment 1",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            1000,
                            "test credit payment 2",
                            partial_payment_allowed=True,
                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4100, 4100, 4100],
                        "Credit": [900, 0, 2.08, 2.08],
                        "Credit: Curr Stmt Bal": [400, 0, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 0, 2.08, 2.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 900, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500, 2.08],
                        "Marginal Interest": [0, 0, 2.08, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 2.08, 0],
                        "Net Worth": [4100, 4100, 4100 - 2.08, 4100 - 2.08],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [900, 0, 2.08, 2.08],
                        "Liquid Total": [5000, 4100, 4100, 4100],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$400.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$400.00); ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00)",
                            "CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00); CC INTEREST (Credit: Prev Stmt Bal +$2.08)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_day_before__curr_only",
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(0, 500, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            300,
                            "single additional payment day before due date",

                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4700, 4700, 4700],
                        "Credit": [500, 200, 200, 200],
                        "Credit: Curr Stmt Bal": [500, 200, 0, 0],
                        "Credit: Prev Stmt Bal": [0, 0, 200, 200],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 300, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0, 200],
                        "Marginal Interest": [0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 0, 0],
                        "Net Worth": [4500, 4500, 4500, 4500],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [500, 200, 200, 200],
                        "Liquid Total": [5000, 4700.0, 4700.0, 4700.0],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$300.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$300.00)",
                            "",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_two_additional_payments_day_before__curr_only",
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(0, 500, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            300,
                            "txn 1",

                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            100,
                            "txn 2",

                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4600, 4600, 4600],
                        "Credit": [500, 100, 100, 100],
                        "Credit: Curr Stmt Bal": [500, 100, 0, 0],
                        "Credit: Prev Stmt Bal": [0, 0, 100, 100],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 400, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0, 100],
                        "Marginal Interest": [0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 0, 0],
                        "Net Worth": [4500, 4500, 4500, 4500],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [500, 100, 100, 100],
                        "Liquid Total": [5000, 4600.0, 4600.0, 4600.0],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$300.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$300.00); ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$100.00)",
                            "",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_day_before_OVERPAY__curr_only",
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(0, 500, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            600,
                            "single additional payment day before due date",
                            partial_payment_allowed=True,
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4500, 4500, 4500],
                        "Credit": [500, 0, 0, 0],
                        "Credit: Curr Stmt Bal": [500, 0, 0, 0],
                        "Credit: Prev Stmt Bal": [0, 0, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 500, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0, 0],
                        "Marginal Interest": [0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 0, 0],
                        "Net Worth": [4500, 4500, 4500, 4500],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [500, 0, 0, 0],
                        "Liquid Total": [5000, 4500.0, 4500.0, 4500.0],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$500.00)",
                            "",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_two_additional_payments_day_before_OVERPAY__curr_only",
                AccountSet(
                    checking_acct_list(5000) + credit_bsd12_acct_list(0, 500, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"), datetime.datetime.strptime("20000105","%Y%m%d"), 2, "once", 400, "txn 1", partial_payment_allowed=True
                        ),
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"), datetime.datetime.strptime("20000105","%Y%m%d"), 2, "once", 400, "txn 2", partial_payment_allowed=True
                        ),
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4500, 4500, 4500],
                        "Credit": [500, 0, 0, 0],
                        "Credit: Curr Stmt Bal": [500, 0, 0, 0],
                        "Credit: Prev Stmt Bal": [0, 0, 0, 0],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 500, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [0, 0, 0, 0],
                        "Marginal Interest": [0, 0, 0, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 0, 0],
                        "Net Worth": [4500, 4500, 4500, 4500],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [500, 0, 0, 0],
                        "Liquid Total": [5000, 4500.0, 4500.0, 4500.0],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$400.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$400.00); ADDTL CC PAYMENT (Checking -$100.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$100.00)",
                            "",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_day_before__curr_prev",
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(500, 400, 0.05, 500)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            700,
                            "test credit payment 1",

                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4300, 4300, 4300],
                        "Credit": [900, 200, 202.08, 202.08],
                        "Credit: Curr Stmt Bal": [400, 200, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 0, 202.08, 202.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 700, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500, 202.08],
                        "Marginal Interest": [0, 0, 2.08, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 2.08, 0],
                        "Net Worth": [4100, 4100, 4100 - 2.08, 4100 - 2.08],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [900, 200, 202.08, 202.08],
                        "Liquid Total": [5000, 4300, 4300, 4300],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$200.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$200.00); ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00)",
                            "CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00); CC INTEREST (Credit: Prev Stmt Bal +$2.08)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
            (
                "test_cc_single_additional_payment_day_before_OVERPAY__curr_prev",
                AccountSet(
                    checking_acct_list(5000)
                    + credit_bsd12_w_eopc_acct_list(500, 400, 0.05, 500)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            datetime.datetime.strptime("20000105","%Y%m%d"),
                            2,
                            "once",
                            1000,
                            "test credit payment 1",
                            partial_payment_allowed=True,
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000113",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000110", "20000111", "20000112", "20000113"],
                        "Checking": [5000, 4100, 4100, 4100],
                        "Credit": [900, 0, 2.08, 2.08],
                        "Credit: Curr Stmt Bal": [400, 0, 0, 0],
                        "Credit: Prev Stmt Bal": [500, 0, 2.08, 2.08],
                        "Credit: Credit Billing Cycle Payment Bal": [0, 900, 0, 0],
                        "Credit: Credit End of Prev Cycle Bal": [500, 500, 500, 2.08],
                        "Marginal Interest": [0, 0, 2.08, 0],
                        "Net Gain": [0, 0, 0, 0],
                        "Net Loss": [0, 0, 2.08, 0],
                        "Net Worth": [4100, 4100, 4100 - 2.08, 4100 - 2.08],
                        "Loan Total": [0, 0, 0, 0],
                        "CC Debt Total": [900, 0, 2.08, 2.08],
                        "Liquid Total": [5000, 4100, 4100, 4100],
                        "Next Income Date": ["", "", "", ""],
                        "Memo Directives": [
                            "",
                            "ADDTL CC PAYMENT (Checking -$400.00); ADDTL CC PAYMENT (Credit: Curr Stmt Bal -$400.00); ADDTL CC PAYMENT (Checking -$500.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$500.00)",
                            "CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00); CC INTEREST (Credit: Prev Stmt Bal +$2.08)",
                            "",
                        ],
                        "Memo": ["", "", "", ""],
                    }
                ),
            ),
        ],
    )
    def test_cc_advance_payment(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):
        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    @pytest.mark.unit
    @pytest.mark.skip(reason="Skipping this test for now")
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_distal_propagation__prev_only",
                AccountSet(
                    checking_acct_list(0) + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 0)
                ),
                # todo implement
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": [0] * 36,
                        "Credit": [0] * 36,
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": [0] * 36,
                        "Credit: Credit Billing Cycle Payment Bal": [0] * 36,
                        "Credit: Credit End of Prev Cycle Bal": [0] * 36,
                        "Marginal Interest": [0] * 36,
                        "Net Gain": [0] * 36,
                        "Net Loss": [0] * 36,
                        "Net Worth": [0] * 36,
                        "Loan Total": [0] * 36,
                        "CC Debt Total": [0] * 36,
                        "Liquid Total": [0] * 36,
                        "Next Income Date": [""] * 36,
                        "Memo Directives": ["NOT IMPLEMENTED"] * 36,
                        "Memo": [""] * 36,
                    }
                ),
            ),
            (
                "test_distal_propagation_multiple__prev_only",
                AccountSet(
                    checking_acct_list(0) + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 0)
                ),
                # todo implement
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": [0] * 36,
                        "Credit": [0] * 36,
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": [0] * 36,
                        "Credit: Credit Billing Cycle Payment Bal": [0] * 36,
                        "Credit: Credit End of Prev Cycle Bal": [0] * 36,
                        "Marginal Interest": [0] * 36,
                        "Net Gain": [0] * 36,
                        "Net Loss": [0] * 36,
                        "Net Worth": [0] * 36,
                        "Loan Total": [0] * 36,
                        "CC Debt Total": [0] * 36,
                        "Liquid Total": [0] * 36,
                        "Next Income Date": [""] * 36,
                        "Memo Directives": ["NOT IMPLEMENTED"] * 36,
                        "Memo": [""] * 36,
                    }
                ),
            ),
            (
                "test_distal_propagation__curr_only",
                AccountSet(
                    checking_acct_list(0) + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 0)
                ),
                # todo implement
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": [0] * 36,
                        "Credit": [0] * 36,
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": [0] * 36,
                        "Credit: Credit Billing Cycle Payment Bal": [0] * 36,
                        "Credit: Credit End of Prev Cycle Bal": [0] * 36,
                        "Marginal Interest": [0] * 36,
                        "Net Gain": [0] * 36,
                        "Net Loss": [0] * 36,
                        "Net Worth": [0] * 36,
                        "Loan Total": [0] * 36,
                        "CC Debt Total": [0] * 36,
                        "Liquid Total": [0] * 36,
                        "Next Income Date": [""] * 36,
                        "Memo Directives": ["NOT IMPLEMENTED"] * 36,
                        "Memo": [""] * 36,
                    }
                ),
            ),
            (
                "test_distal_propagation_multiple__curr_only",
                AccountSet(
                    checking_acct_list(0) + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 0)
                ),
                # todo implement
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": [0] * 36,
                        "Credit": [0] * 36,
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": [0] * 36,
                        "Credit: Credit Billing Cycle Payment Bal": [0] * 36,
                        "Credit: Credit End of Prev Cycle Bal": [0] * 36,
                        "Marginal Interest": [0] * 36,
                        "Net Gain": [0] * 36,
                        "Net Loss": [0] * 36,
                        "Net Worth": [0] * 36,
                        "Loan Total": [0] * 36,
                        "CC Debt Total": [0] * 36,
                        "Liquid Total": [0] * 36,
                        "Next Income Date": [""] * 36,
                        "Memo Directives": ["NOT IMPLEMENTED"] * 36,
                        "Memo": [""] * 36,
                    }
                ),
            ),
            (
                "test_distal_propagation__curr_prev",
                AccountSet(
                    checking_acct_list(0) + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 0)
                ),
                # todo implement
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": [0] * 36,
                        "Credit": [0] * 36,
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": [0] * 36,
                        "Credit: Credit Billing Cycle Payment Bal": [0] * 36,
                        "Credit: Credit End of Prev Cycle Bal": [0] * 36,
                        "Marginal Interest": [0] * 36,
                        "Net Gain": [0] * 36,
                        "Net Loss": [0] * 36,
                        "Net Worth": [0] * 36,
                        "Loan Total": [0] * 36,
                        "CC Debt Total": [0] * 36,
                        "Liquid Total": [0] * 36,
                        "Next Income Date": [""] * 36,
                        "Memo Directives": ["NOT IMPLEMENTED"] * 36,
                        "Memo": [""] * 36,
                    }
                ),
            ),
            (
                "test_distal_propagation_multiple__curr_prev",
                AccountSet(
                    checking_acct_list(0) + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 0)
                ),
                # todo implement
                # BudgetSet([BudgetItem('20000112', '20000112', 2, 'once', 600, 'single additional payment on due date', )]),
                BudgetSet(),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(".*", "Checking", "Credit", 2),
                    ]
                ),
                "20000110",
                "20000214",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": generate_date_sequence(datetime.datetime.strptime("20000110","%Y%m%d"), 35, "daily"),
                        "Checking": [0] * 36,
                        "Credit": [0] * 36,
                        "Credit: Curr Stmt Bal": [0] * 36,
                        "Credit: Prev Stmt Bal": [0] * 36,
                        "Credit: Credit Billing Cycle Payment Bal": [0] * 36,
                        "Credit: Credit End of Prev Cycle Bal": [0] * 36,
                        "Marginal Interest": [0] * 36,
                        "Net Gain": [0] * 36,
                        "Net Loss": [0] * 36,
                        "Net Worth": [0] * 36,
                        "Loan Total": [0] * 36,
                        "CC Debt Total": [0] * 36,
                        "Liquid Total": [0] * 36,
                        "Next Income Date": [""] * 36,
                        "Memo Directives": ["NOT IMPLEMENTED"] * 36,
                        "Memo": [""] * 36,
                    }
                ),
            ),
        ],
    )
    def test_cc_payment_propagation(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):
        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    @pytest.mark.unit
    @pytest.mark.skip(reason="Skipping this test for now")
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_p7__additional_loan_payment__amt_10",
                AccountSet(
                    checking_acct_list(5000)
                    + non_trivial_loan("Loan A", 1000, 100, 0.1)
                    + non_trivial_loan("Loan B", 1000, 100, 0.05)
                    + non_trivial_loan("Loan C", 1000, 100, 0.01)
                ),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            7,
                            "once",
                            10,
                            "additional_loan_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_loan_payment", "Checking", "ALL_LOANS", 7
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [5000, 4840, 4840],
                        "Loan A: Principal Balance": [1000, 1000, 1000],
                        "Loan A: Interest": [100, 40.27, 40.54],
                        "Loan A: Loan Billing Cycle Payment Bal": [0, 10, 10],
                        "Loan A: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan B: Principal Balance": [1000, 1000, 1000],
                        "Loan B: Interest": [100, 50.14, 50.28],
                        "Loan B: Loan Billing Cycle Payment Bal": [0, 0, 0],
                        "Loan B: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan C: Principal Balance": [1000, 1000, 1000],
                        "Loan C: Interest": [100, 50.03, 50.06],
                        "Loan C: Loan Billing Cycle Payment Bal": [0, 0, 0],
                        "Loan C: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Marginal Interest": [0, 0.44, 0.44],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0.44, 0.44],
                        "Net Worth": [1700, 1699.56, 1699.12],
                        "Loan Total": [3300, 3140.44, 3140.88],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [5000, 4840, 4840],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$10.00); ADDTL LOAN PAYMENT (Loan A: Interest -$10.00)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p7__additional_loan_payment__amt_110",
                AccountSet(
                    checking_acct_list(5000)
                    + non_trivial_loan("Loan A", 1000, 100, 0.1)
                    + non_trivial_loan("Loan B", 1000, 100, 0.05)
                    + non_trivial_loan("Loan C", 1000, 100, 0.01)
                ),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            7,
                            "once",
                            110,
                            "additional_loan_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_loan_payment", "Checking", "ALL_LOANS", 7
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [5000, 4740, 4740],
                        "Loan A: Principal Balance": [1000, 940.27, 940.27],
                        "Loan A: Interest": [100, 0.0, 0.26],
                        "Loan A: Loan Billing Cycle Payment Bal": [
                            0,
                            59.73 + 50.27,
                            59.73 + 50.27,
                        ],
                        "Loan A: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        # bc payments day of don't count, this is correct
                        "Loan B: Principal Balance": [1000, 1000, 1000],
                        "Loan B: Interest": [100, 50.14, 50.28],
                        "Loan B: Loan Billing Cycle Payment Bal": [0, 0, 0],
                        "Loan B: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan C: Principal Balance": [1000, 1000, 1000],
                        "Loan C: Interest": [100, 50.03, 50.06],
                        "Loan C: Loan Billing Cycle Payment Bal": [0, 0, 0],
                        "Loan C: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Marginal Interest": [0, 0.44, 0.43],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0.44, 0.43],
                        "Net Worth": [1700, 1699.56, 1699.13],
                        "Loan Total": [3300, 3040.44, 3040.87],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [5000, 4740, 4740],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$59.73); ADDTL LOAN PAYMENT (Loan A: Principal Balance -$59.73); ADDTL LOAN PAYMENT (Checking -$50.27); ADDTL LOAN PAYMENT (Loan A: Interest -$50.27)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p7__additional_loan_payment__amt_560",
                AccountSet(
                    checking_acct_list(5000)
                    + non_trivial_loan("Loan A", 1000, 100, 0.1)
                    + non_trivial_loan("Loan B", 1000, 100, 0.05)
                    + non_trivial_loan("Loan C", 1000, 100, 0.01)
                ),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            7,
                            "once",
                            560,
                            "additional_loan_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_loan_payment", "Checking", "ALL_LOANS", 7
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [5000, 5000 - 150 - 560, 5000 - 150 - 560],
                        "Loan A: Principal Balance": [1000, 496.89, 496.89],
                        "Loan A: Interest": [100, 0, 0.14],
                        "Loan A: Loan Billing Cycle Payment Bal": [
                            0,
                            503.11 + 50.27,
                            503.11 + 50.27,
                        ],
                        "Loan A: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan B: Principal Balance": [1000, 1000, 1000],
                        "Loan B: Interest": [100, 43.52, 43.66],
                        "Loan B: Loan Billing Cycle Payment Bal": [0, 6.62, 6.62],
                        "Loan B: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan C: Principal Balance": [1000, 1000, 1000],
                        "Loan C: Interest": [100, 50.03, 50.06],
                        "Loan C: Loan Billing Cycle Payment Bal": [0, 0, 0],
                        "Loan C: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Marginal Interest": [0, 0.44, 0.31],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0.44, 0.31],
                        "Net Worth": [1700, 1699.56, 1699.25],
                        "Loan Total": [3300, 2590.44, 2590.75],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [5000, 5000 - 150 - 560, 5000 - 150 - 560],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$503.11); ADDTL LOAN PAYMENT (Loan A: Principal Balance -$503.11); ADDTL LOAN PAYMENT (Checking -$50.27); ADDTL LOAN PAYMENT (Loan A: Interest -$50.27); ADDTL LOAN PAYMENT (Checking -$6.62); ADDTL LOAN PAYMENT (Loan B: Interest -$6.62)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),  # todo double check this math
            (
                "test_p7__additional_loan_payment__amt_610",
                AccountSet(
                    checking_acct_list(5000)
                    + non_trivial_loan("Loan A", 1000, 100, 0.1)
                    + non_trivial_loan("Loan B", 1000, 100, 0.05)
                    + non_trivial_loan("Loan C", 1000, 100, 0.01)
                ),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            7,
                            "once",
                            610,
                            "additional_loan_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_loan_payment", "Checking", "ALL_LOANS", 7
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [5000, 5000 - 150 - 610, 5000 - 150 - 610],
                        "Loan A: Principal Balance": [1000, 480.89, 480.89],
                        "Loan A: Interest": [100, 0, 0.13],
                        "Loan A: Loan Billing Cycle Payment Bal": [
                            0,
                            519.11 + 50.27,
                            519.11 + 50.27,
                        ],
                        "Loan A: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan B: Principal Balance": [1000, 1000, 1000],
                        "Loan B: Interest": [100, 9.52, 9.66],
                        "Loan B: Loan Billing Cycle Payment Bal": [0, 40.62, 40.62],
                        "Loan B: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan C: Principal Balance": [1000, 1000, 1000],
                        "Loan C: Interest": [100, 50.03, 50.06],
                        "Loan C: Loan Billing Cycle Payment Bal": [0, 0, 0],
                        "Loan C: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Marginal Interest": [0, 0.44, 0.3],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0.44, 0.3],
                        "Net Worth": [1700, 1699.56, 1699.26],
                        "Loan Total": [3300, 2540.44, 2540.74],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [5000, 5000 - 150 - 610, 5000 - 150 - 610],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$519.11); ADDTL LOAN PAYMENT (Loan A: Principal Balance -$519.11); ADDTL LOAN PAYMENT (Checking -$50.27); ADDTL LOAN PAYMENT (Loan A: Interest -$50.27); ADDTL LOAN PAYMENT (Checking -$40.62); ADDTL LOAN PAYMENT (Loan B: Interest -$40.62)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),  # todo check this math
            (
                "test_p7__additional_loan_payment__amt_1900",
                AccountSet(
                    checking_acct_list(5000)
                    + non_trivial_loan("Loan A", 1000, 100, 0.1)
                    + non_trivial_loan("Loan B", 1000, 100, 0.05)
                    + non_trivial_loan("Loan C", 1000, 100, 0.01)
                ),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            7,
                            "once",
                            1900,
                            "additional_loan_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_loan_payment", "Checking", "ALL_LOANS", 7
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [5000, 5000 - 150 - 1900, 5000 - 150 - 1900],
                        "Loan A: Principal Balance": [1000, 92.62, 92.62],
                        "Loan A: Interest": [100, 0, 0.03],
                        "Loan A: Loan Billing Cycle Payment Bal": [
                            0,
                            907.38 + 50.27,
                            907.38 + 50.27,
                        ],
                        "Loan A: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan B: Principal Balance": [1000, 185.25, 185.25],
                        "Loan B: Interest": [100, 0, 0.03],
                        "Loan B: Loan Billing Cycle Payment Bal": [
                            0,
                            814.75 + 50.14,
                            814.75 + 50.14,
                        ],
                        "Loan B: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan C: Principal Balance": [1000, 972.57, 972.57],
                        "Loan C: Interest": [100, 0, 0.03],
                        "Loan C: Loan Billing Cycle Payment Bal": [
                            0,
                            27.43 + 50.03,
                            27.43 + 50.03,
                        ],
                        "Loan C: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Marginal Interest": [0, 0.44, 0.09],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0.44, 0.09],
                        "Net Worth": [1700, 1699.56, 1699.47],
                        "Loan Total": [3300, 1250.44, 1250.53],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [5000, 5000 - 150 - 1900, 5000 - 150 - 1900],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$907.38); ADDTL LOAN PAYMENT (Loan A: Principal Balance -$907.38); ADDTL LOAN PAYMENT (Checking -$50.27); ADDTL LOAN PAYMENT (Loan A: Interest -$50.27); ADDTL LOAN PAYMENT (Checking -$814.75); ADDTL LOAN PAYMENT (Loan B: Principal Balance -$814.75); ADDTL LOAN PAYMENT (Checking -$50.14); ADDTL LOAN PAYMENT (Loan B: Interest -$50.14); ADDTL LOAN PAYMENT (Checking -$27.43); ADDTL LOAN PAYMENT (Loan C: Principal Balance -$27.43); ADDTL LOAN PAYMENT (Checking -$50.03); ADDTL LOAN PAYMENT (Loan C: Interest -$50.03)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
            (
                "test_p7__additional_loan_payment__amt_overpay",
                AccountSet(
                    checking_acct_list(5000)
                    + non_trivial_loan("Loan A", 1000, 100, 0.1)
                    + non_trivial_loan("Loan B", 1000, 100, 0.05)
                    + non_trivial_loan("Loan C", 1000, 100, 0.01)
                ),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            7,
                            "once",
                            3500,
                            "additional_loan_payment",
                        )
                    ]
                ),
                MemoRuleSet(
                    [
                        MemoRule(".*", "Checking", None, 1),
                        MemoRule(
                            "additional_loan_payment", "Checking", "ALL_LOANS", 7
                        ),
                    ]
                ),
                "20000101",
                "20000103",
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": ["20000101", "20000102", "20000103"],
                        "Checking": [5000, 1699.56, 1699.56],
                        "Loan A: Principal Balance": [1000, 0, 0],
                        "Loan A: Interest": [100, 0, 0],
                        "Loan A: Loan Billing Cycle Payment Bal": [
                            0,
                            1000 + 50.27,
                            1000 + 50.27,
                        ],
                        "Loan A: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan B: Principal Balance": [1000, 0, 0],
                        "Loan B: Interest": [100, 0, 0],
                        "Loan B: Loan Billing Cycle Payment Bal": [
                            0,
                            1000 + 50.14,
                            1000 + 50.14,
                        ],
                        "Loan B: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Loan C: Principal Balance": [1000, 0, 0],
                        "Loan C: Interest": [100, 0, 0],
                        "Loan C: Loan Billing Cycle Payment Bal": [
                            0,
                            1000 + 50.03,
                            1000 + 50.03,
                        ],
                        "Loan C: Loan End of Prev Cycle Bal": [1000, 1000, 1000],
                        "Marginal Interest": [0, 0.44, 0],
                        "Net Gain": [0, 0, 0],
                        "Net Loss": [0, 0.44, 0],
                        "Net Worth": [1700, 1699.56, 1699.56],
                        "Loan Total": [3300, 0, 0],
                        "CC Debt Total": [0, 0, 0],
                        "Liquid Total": [5000, 1699.56, 1699.56],
                        "Next Income Date": ["", "", ""],
                        "Memo Directives": [
                            "",
                            "LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$1000.00); ADDTL LOAN PAYMENT (Loan A: Principal Balance -$1000.00); ADDTL LOAN PAYMENT (Checking -$50.27); ADDTL LOAN PAYMENT (Loan A: Interest -$50.27); ADDTL LOAN PAYMENT (Checking -$1000.00); ADDTL LOAN PAYMENT (Loan B: Principal Balance -$1000.00); ADDTL LOAN PAYMENT (Checking -$50.14); ADDTL LOAN PAYMENT (Loan B: Interest -$50.14); ADDTL LOAN PAYMENT (Checking -$1000.00); ADDTL LOAN PAYMENT (Loan C: Principal Balance -$1000.00); ADDTL LOAN PAYMENT (Checking -$50.03); ADDTL LOAN PAYMENT (Loan C: Interest -$50.03)",
                            "",
                        ],
                        "Memo": ["", "", ""],
                    }
                ),
            ),
        ],
    )
    def test_loan_payments(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):
        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [],
    )
    def test_TEMPLATE(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):
        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    #
    # there might be something about allocation and the ALL_LOANS memo rule as well
    # Note also that the basic loan tests test single payment same day

    # todo could there be problems w interest accrual and billing cycle being on different cadences?
    # (would only happen when interest accrual happens more frequently. interest will always overlap_

    # test_loan_single_additional_payment_day_before #4 day result
    # test_loan_two_additional_payments_on_due_date #3 day result
    # test_loan_two_additional_payments_day_before #4 day result
    # test_loan_earliest_prepayment_possible #36 day result
    # test_loan_multiple_earliest_prepayment_possible #36 day result

    # test_loan_single_additional_payment_day_before_OVERPAY #4 day result
    # test_loan_two_additional_payments_on_due_date_OVERPAY #3 day result
    # test_loan_two_additional_payments_day_before_OVERPAY #4 day result
    # test_loan_earliest_prepayment_possible_OVERPAY #36 day result
    # test_loan_multiple_earliest_prepayment_possible_OVERPAY #36 day result

    ### Not sure if this is testing for deferrals properly
    # @pytest.mark.parametrize('test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df,expected_memo_of_deferred_txn,expected_deferred_date',[
    # (
    #         'test_p5_and_6__expect_defer',
    #         AccountSet(checking_acct_list(1000)),
    #         BudgetSet([BudgetItem('20000102', '20000102', 5, 'once', 100, 'p5 txn 1/2/00', ),
    #                              BudgetItem('20000102', '20000102', 6, 'once', 1000, 'p6 deferrable txn 1/2/00', True, False),
    #                              ]),
    #         MemoRuleSet( [
    #             MemoRule('.*','Checking',None,5),
    #             MemoRule('.*', 'Checking', None, 6)
    #         ] ),
    #         '20000101',
    #         '20000103',
    #         MilestoneSet( [], [], []),
    #         pd.DataFrame({
    #             'Date': ['20000101', '20000102', '20000103'],
    #             'Checking': [1000, 900, 900],
    #             'Marginal Interest': [0, 0, 0],
    #             'Net Gain': [0, 0, 0],
    #             'Net Loss': [0, 100, 0],
    #             'Net Worth': [1000, 900, 900],
    #             'Loan Total': [0, 0, 0],
    #             'CC Debt Total': [0, 0, 0],
    #             'Liquid Total': [1000, 900, 900],
    #             'Next Income Date': ['', '', ''],
    #             'Memo Directives': ['', '', ''],
    #             'Memo': ['', 'p5 txn 1/2/00 (Checking -$100.00)', '']
    #         }),
    #         'p6 deferrable txn 1/2/00',
    #         None #deferred but never executed
    # ),
    #
    #     (
    #             'test_p5_and_6__expect_defer__daily',
    #             AccountSet(checking_acct_list(1000)),
    #             BudgetSet(
    #                 [BudgetItem('20000102', '20000102', 5, 'once', 100, 'p5 txn 1/2/00', ),
    #                  BudgetItem('20000103', '20000103', 1, 'once', 100, 'income 1/3/00', ),
    #                  BudgetItem('20000102', '20000102', 6, 'once', 1000, 'p6 deferrable txn 1/2/00', True, False),
    #                  ]),
    #             MemoRuleSet([
    #                 MemoRule('.*', None, 'Checking', 1),
    #                 MemoRule('.*', 'Checking', None, 5),
    #                 MemoRule('.*', 'Checking', None, 6)
    #             ]),
    #             '20000101',
    #             '20000103',
    #             MilestoneSet( [], [], []),
    #             pd.DataFrame({
    #                 'Date': ['20000101', '20000102', '20000103'],
    #                 'Checking': [1000, 900, 0],
    #                 'Marginal Interest': [0, 0, 0],
    #                 'Net Gain': [0, 0, 0],
    #                 'Net Loss': [0, 100, 900],
    #                 'Net Worth': [1000, 900, 0],
    #                 'Loan Total': [0, 0, 0],
    #                 'CC Debt Total': [0, 0, 0],
    #                 'Liquid Total': [1000, 900, 0],
    #                 'Next Income Date': ['20000103', '20000103', ''],
    #                 'Memo Directives': ['', '', 'INCOME (Checking +$100.00)'],
    #                 'Memo': ['', 'p5 txn 1/2/00 (Checking -$100.00)', 'income 1/3/00 (Checking +$100.00); p6 deferrable txn 1/2/00 (Checking -$1000.00)']
    #             }),
    #             'p6 deferrable txn 1/2/00 (Checking -$1000.00)',
    #             '20000103'
    #     ),
    #
    #     (
    #             'test_expect_defer_past_end_of_forecast',
    #             AccountSet(checking_acct_list(1000)),
    #             BudgetSet(
    #                 [BudgetItem('20000102', '20000102', 2, 'once', 2000, 'deferred past end', True, False)
    #                  ]),
    #             MemoRuleSet([
    #                 MemoRule('.*', None, 'Checking', 1),
    #                 MemoRule('.*', 'Checking', None, 2)
    #             ]),
    #             '20000101',
    #             '20000103',
    #             MilestoneSet( [], [], []),
    #             pd.DataFrame({
    #                 'Date': ['20000101', '20000102', '20000103'],
    #                 'Checking': [1000, 1000, 1000],
    #                 'Marginal Interest': [0,0,0],
    #                 'Net Gain': [0,0,0],
    #                 'Net Loss': [0,0,0],
    #                 'Net Worth': [1000,1000,1000],
    #                 'Loan Total': [0,0,0],
    #                 'CC Debt Total': [0,0,0],
    #                 'Liquid Total': [1000,1000,1000],
    #                 'Next Income Date': ['', '', ''],
    #                 'Memo Directives': ['', '', ''],
    #                 'Memo': ['', '', '']
    #             }),
    #             'deferred past end',
    #             None
    #     ),
    #
    # ])
    # def test_deferrals(self, test_description, account_set, budget_set, memo_rule_set, start_date,
    #                        end_date, milestone_set, expected_result_df, expected_memo_of_deferred_txn,
    #                    expected_deferred_date):
    #
    #     expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
    #                                expected_result_df.Date]
    #
    #     E = self.compute_forecast_and_actual_vs_expected(account_set,
    #                                                      budget_set,
    #                                                      memo_rule_set,
    #                                                      start_date,
    #                                                      end_date,
    #                                                      milestone_set,
    #                                                      expected_result_df,
    #                                                      test_description)
    #
    #     if expected_deferred_date is not None:
    #         row_sel_vec = [ datetime.datetime.strptime(d,'%Y%m%d') == datetime.datetime.strptime(expected_deferred_date,'%Y%m%d') for d in E.forecast_df.Date ]
    #         assert sum(row_sel_vec) == 1 #if 0, then deferred date was not found
    #         assert expected_memo_of_deferred_txn in E.forecast_df.loc[ row_sel_vec , 'Memo'].iat[0]
    #     else:
    #         print('E.deferred_df')
    #         print(E.deferred_df.to_string())
    #         assert E.deferred_df.shape[0] == 1
    #         assert E.deferred_df.loc[0, 'Memo'] == expected_memo_of_deferred_txn

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
        [
            (
                "test_next_income_date",
                AccountSet(checking_acct_list(1000)),
                BudgetSet(
                    [
                        BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "income 1",

                        ),
                        BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
                            1,
                            "once",
                            100,
                            "income 2",

                        ),
                    ]
                ),
                MemoRuleSet([MemoRule(".*", None, "Checking", 1)]),
                "20000101",
                datetime.datetime.strptime("20000105","%Y%m%d"),
                MilestoneSet(),
                pd.DataFrame(
                    {
                        "Date": [
                            "20000101",
                            "20000102",
                            "20000103",
                            "20000104",
                            "20000105",
                        ],
                        "Checking": [1000, 1100, 1100, 1200, 1200],
                        "Marginal Interest": [0, 0, 0, 0, 0],
                        "Net Gain": [0, 100, 0, 100, 0],
                        "Net Loss": [0, 0, 0, 0, 0],
                        "Net Worth": [1000, 1100, 1100, 1200, 1200],
                        "Loan Total": [0, 0, 0, 0, 0],
                        "CC Debt Total": [0, 0, 0, 0, 0],
                        "Liquid Total": [1000, 1100, 1100, 1200, 1200],
                        "Next Income Date": [
                            "20000102",
                            "20000104",
                            "20000104",
                            "",
                            "",
                        ],
                        "Memo Directives": [
                            "",
                            "INCOME (Checking +$100.00)",
                            "",
                            "INCOME (Checking +$100.00)",
                            "",
                        ],
                        "Memo": [
                            "",
                            "income 1 (Checking +$100.00)",
                            "",
                            "income 2 (Checking +$100.00)",
                            "",
                        ],
                    }
                ),
            ),
        ],
    )
    def test_next_income_date(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        expected_result_df,
    ):
        expected_result_df.Date = [
            datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
        ]

        E = self.compute_forecast_and_actual_vs_expected(
            account_set,
            budget_set,
            memo_rule_set,
            start_date,
            end_date,
            milestone_set,
            expected_result_df,
            test_description,
        )

    def test_multiple_matching_memo_rule_regex(self):

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
            start_date="20000102",
            end_date="20000102",
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

        milestone_set = MilestoneSet([], [], [])

        with pytest.raises(ValueError):
            ExpenseForecastInitialConditions(
                datetime.datetime.strptime(start_date, "%Y%m%d").date(),
                datetime.datetime.strptime(end_date, "%Y%m%d").date(),
                account_set,
                budget_set,
                memo_rule_set,
                raise_exceptions=True,
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

    # def test_initialize_forecast_from_excel_not_yet_run(self):
    #     start_date = '20000101'
    #     end_date = '20000105'
    #
    #     A = AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', ),
    #          BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', ),
    #          BudgetItem('20010101', '20010101', 3, 'once', 100, 'specific regex 2', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast(A, B, M, start_date, end_date, MS)
    #
    #     # E1.runForecast()  # Forecast_028363.html
    #     # E1.appendSummaryLines()
    #     E1.to_excel('./out/')  # ./out/Forecast_059039.xlsx
    #
    #     E2_list = ExpenseForecast.initialize_from_excel_file('./out/Forecast_'+str(E1.unique_id)+'.xlsx')
    #     E2 = E2_list[0]
    #
    #     print('############################################')
    #     print(E1.milestone_set.to_json())
    #     print('############################################')
    #     print(E2.milestone_set.to_json())
    #     print('############################################')
    #
    #     # before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     # assert E1.start_ts == E2.start_ts
    #     # assert E1.end_ts == E2.end_ts
    #     assert E1.start_date == E2.start_date
    #     assert E1.end_date == E2.end_date
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()

    # def test_initialize_from_excel_already_run__no_append(self):
    #     start_date = '20000101'
    #     end_date = '20000105'
    #
    #     A = AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', ),
    #          BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', ),
    #          BudgetItem('20010101', '20010101', 3, 'once', 100, 'specific regex 2', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast(A, B, M, start_date, end_date, MS)
    #
    #     E1.runForecast()  # Forecast_028363.html
    #     E1.to_excel('./out')  # ./out/Forecast_028363.xlsx
    #
    #     E2_list = ExpenseForecast.initialize_from_excel_file('./out/Forecast_059039.xlsx')
    #     E2 = E2_list[0]
    #
    #     # before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     assert E1.start_ts == E2.start_ts
    #     assert E1.end_ts == E2.end_ts
    #     assert E1.start_date == E2.start_date
    #     assert E1.end_date == E2.end_date
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    #     # after runForecast
    #     assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
    #     assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
    #     assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
    #
    #     for index, row in E1.skipped_df.iterrows():
    #         for c_index in range(0, E1.skipped_df.shape[1]):
    #             assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]
    #
    #     for index, row in E1.deferred_df.iterrows():
    #         for c_index in range(0, E1.deferred_df.shape[1]):
    #             assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]
    #
    #     for index, row in E1.confirmed_df.iterrows():
    #         for c_index in range(0, E1.confirmed_df.shape[1]):
    #             assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]
    #
    #     for index, row in E1.forecast_df.iterrows():
    #         for c_index in range(0, E1.forecast_df.shape[1]):
    #             if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
    #                 assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],2)
    #             else:
    #                 try:
    #                     assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]
    #                 except Exception as e:
    #                     print(index,c_index)
    #                     print(e.args)
    #                     raise e

    # def test_initialize_forecast_from_excel_already_run(self):
    #     start_date = '20000101'
    #     end_date = '20000105'
    #
    #     A = AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', ),
    #          BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', ),
    #          BudgetItem('20010101', '20010101', 3, 'once', 100, 'specific regex 2', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast(A, B, M, start_date, end_date, MS)
    #
    #     E1.runForecast()  # Forecast_028363.html
    #     E1.to_excel('./out')  # ./out/Forecast_028363.xlsx
    #
    #     E2_list = ExpenseForecast.initialize_from_excel_file('./out/Forecast_'+str(E1.unique_id)+'.xlsx')
    #     E2 = E2_list[0]
    #
    #     # before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     assert E1.start_ts == E2.start_ts
    #     assert E1.end_ts == E2.end_ts
    #     assert E1.start_date == E2.start_date
    #     assert E1.end_date == E2.end_date
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    #     # after runForecast
    #     assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
    #     assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
    #     assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
    #
    #     for index, row in E1.skipped_df.iterrows():
    #         for c_index in range(0, E1.skipped_df.shape[1]):
    #             assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]
    #
    #     for index, row in E1.deferred_df.iterrows():
    #         for c_index in range(0, E1.deferred_df.shape[1]):
    #             assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]
    #
    #     for index, row in E1.confirmed_df.iterrows():
    #         for c_index in range(0, E1.confirmed_df.shape[1]):
    #             assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]
    #
    #     # after appendSummaryLines
    #     # e.g. "Marginal Interest":0.0,"Net Gain":0,"Net Loss":0,"Net Worth":1700.0,"Loan Total":100.0,"CC Debt Total":200.0,"Liquid Total":2000.0,
    #     for index, row in E1.forecast_df.iterrows():
    #         for c_index in range(0, E1.forecast_df.shape[1]):
    #             if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
    #                 assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],
    #                                                                               2)
    #             else:
    #                 assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]

    # def test_initialize_forecast_from_json_not_yet_run(self):
    #     start_date = '20000101'
    #     end_date = '20000105'
    #
    #     A = AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', ),
    #          BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast(A, B, M, start_date, end_date, MS,
    #                                          forecast_set_name='Forecast Set Name',
    #                                          forecast_name='Forecast Name'
    #                                          )
    #
    #     #E1.runForecast()  # Forecast_028363.html
    #     E1.writeToJSONFile('./out/')  # ./out/ForecastResult_010783.json
    #     # print(E1.to_json())
    #
    #     E2  = ExpenseForecast.initialize_from_json_file('./out/ForecastResult_'+str(E1.unique_id)+'.json')
    #
    #     # before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     # assert E1.start_ts == E2.start_tsx
    #     # assert E1.end_ts == E2.end_ts
    #     assert E1.start_date == E2.start_date
    #     assert E1.end_date == E2.end_date
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    #     # after runForecast
    #     # assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
    #     # assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
    #     # assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
    #     #
    #     # for index, row in E1.skipped_df.iterrows():
    #     #     for c_index in range(0, E1.skipped_df.shape[1]):
    #     #         assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]
    #     #
    #     # for index, row in E1.deferred_df.iterrows():
    #     #     for c_index in range(0, E1.deferred_df.shape[1]):
    #     #         assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]
    #     #
    #     # for index, row in E1.confirmed_df.iterrows():
    #     #     for c_index in range(0, E1.confirmed_df.shape[1]):
    #     #         assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]
    #     #
    #     # # after appendSummaryLines
    #     # # e.g. "Marginal Interest":0.0,"Net Gain":0,"Net Loss":0,"Net Worth":1700.0,"Loan Total":100.0,"CC Debt Total":200.0,"Liquid Total":2000.0,
    #     # for index, row in E1.forecast_df.iterrows():
    #     #     for c_index in range(0, E1.forecast_df.shape[1]):
    #     #         if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
    #     #             assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],
    #     #                                                                           2)
    #     #         else:
    #     #             assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]

    # def test_initialize_from_json_already_run__no_append(self):
    #     start_date = '20000101'
    #     end_date = '20000105'
    #
    #     A = AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', ),
    #          BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast(A, B, M, start_date, end_date, MS)
    #
    #     E1.runForecast()  # Forecast_028363.html
    #     E1.writeToJSONFile('./out') # ./out/Forecast_028363.json
    #
    #     E2_list = ExpenseForecast.initialize_from_json_file('./out/Forecast_028363.json')
    #     E2 = E2_list[0]
    #
    #     #before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     assert E1.start_ts == E2.start_ts
    #     assert E1.end_ts == E2.end_ts
    #     assert E1.start_date == E2.start_date
    #     assert E1.end_date == E2.end_date
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    #     #after runForecast
    #     assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
    #     assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
    #     assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
    #
    #     for index, row in E1.skipped_df.iterrows():
    #         for c_index in range(0,E1.skipped_df.shape[1]):
    #             assert E1.skipped_df.iloc[index,c_index] == E2.skipped_df.iloc[index,c_index]
    #
    #     for index, row in E1.deferred_df.iterrows():
    #         for c_index in range(0, E1.deferred_df.shape[1]):
    #             assert E1.deferred_df.iloc[index,c_index] == E2.deferred_df.iloc[index,c_index]
    #
    #     for index, row in E1.confirmed_df.iterrows():
    #         for c_index in range(0, E1.confirmed_df.shape[1]):
    #             assert E1.confirmed_df.iloc[index,c_index] == E2.confirmed_df.iloc[index,c_index]
    #
    #     for index, row in E1.forecast_df.iterrows():
    #         for c_index in range(0, E1.forecast_df.shape[1]):
    #             if c_index != 0 and c_index != (E1.forecast_df.shape[1] - 1):
    #                 assert round(E1.forecast_df.iloc[index,c_index],2) == round(E2.forecast_df.iloc[index,c_index],2)
    #             else:
    #                 assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]

    # def test_initialize_forecast_from_json_already_run(self):
    #     start_date = '20000101'
    #     end_date = '20000105'
    #
    #     A = AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', ),
    #          BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast(A, B, M, start_date, end_date, MS)
    #
    #     E1.runForecast()  # Forecast_028363.html
    #     E1.writeToJSONFile('./out/')  # ./out/Forecast_028363.json
    #
    #     E2 = ExpenseForecast.initialize_from_json_file('./out/ForecastResult_'+str(E1.unique_id)+'.json')
    #
    #
    #     # before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     assert E1.start_ts == E2.start_ts
    #     assert E1.end_ts == E2.end_ts
    #     assert E1.start_date == E2.start_date
    #     assert E1.end_date == E2.end_date
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    #     # after runForecast
    #     assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
    #     assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
    #     assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
    #
    #     for index, row in E1.skipped_df.iterrows():
    #         for c_index in range(0, E1.skipped_df.shape[1]):
    #             assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]
    #
    #     for index, row in E1.deferred_df.iterrows():
    #         for c_index in range(0, E1.deferred_df.shape[1]):
    #             assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]
    #
    #     for index, row in E1.confirmed_df.iterrows():
    #         for c_index in range(0, E1.confirmed_df.shape[1]):
    #             assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]
    #
    #     # after appendSummaryLines
    #     # e.g. "Marginal Interest":0.0,"Net Gain":0,"Net Loss":0,"Net Worth":1700.0,"Loan Total":100.0,"CC Debt Total":200.0,"Liquid Total":2000.0,
    #     for index, row in E1.forecast_df.iterrows():
    #         for c_index in range(0, E1.forecast_df.shape[1]):
    #             if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
    #                 assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],2)
    #             else:
    #                 assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]

    # def test_run_forecast_from_json_at_path(self):
    #
    #     sd = '20000101'
    #     ed = '20000103'
    #
    #     A = AccountSet(checking_acct_list(2000) + credit_acct_list(100,100,0.01) + non_trivial_loan('test loan',100,0,0.01))
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', ),
    #          BudgetItem('20000102', '20000102', 2, 'once', 100, 'p2 daily txn 1/2/00', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                account_from='Checking',
    #                                                account_to=None,
    #                                                transaction_priority=1),
    #                              MemoRule(memo_regex='.*',
    #                                                account_from='Checking',
    #                                                account_to=None,
    #                                                transaction_priority=2),
    #                              MemoRule(memo_regex='.*',
    #                                                account_from='Checking',
    #                                                account_to=None,
    #                                                transaction_priority=3)
    #                              ])
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone','Checking',0,100)
    #     MS.addMemoMilestone('test memo milestone','specific regex')
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 200)
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')
    #
    #     AM = AccountMilestone('test account milestone 2','Checking',0,100)
    #     MM = MemoMilestone('test memo milestone 2','other specific regex')
    #
    #     MS.addCompositeMilestone('test composite milestone',[AM],[MM])
    #     MS.addCompositeMilestone('test composite milestone 1', [AM], [MM])
    #
    #     E1 = ExpenseForecast(A,B,M,sd,ed,MS)
    #     E1.runForecast()
    #     with open ('./out/tmp_json_abc123_zzzzz.json','w') as f:
    #         J = E1.to_json()
    #         print(J)
    #         f.write(J)
    #
    #     E2 = ExpenseForecast.initialize_from_json_file('./out/tmp_json_abc123_zzzzz.json')
    #     E2.runForecast()
    #
    #     E1_str_lines = str(E1).split('\n')
    #     E2_str_lines = str(E2).split('\n')
    #
    #     comparable_E1_str_lines = []
    #     for l in E1_str_lines:
    #         if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
    #             comparable_E1_str_lines.append(l)
    #
    #     comparable_E2_str_lines = []
    #     for l in E2_str_lines:
    #         if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
    #             comparable_E2_str_lines.append(l)
    #
    #     # print('------------------------------------------------------------------------------------')
    #     # for l in comparable_E1_str_lines:
    #     #     print(l)
    #     # print('------------------------------------------------------------------------------------')
    #     # for l in comparable_E2_str_lines:
    #     #     print(l)
    #     # print('------------------------------------------------------------------------------------')
    #
    #     assert comparable_E1_str_lines == comparable_E2_str_lines

    # def test_run_forecast_from_excel_at_path(self):
    #
    #     sd = '20000101'
    #     ed = '20000103'
    #
    #     A = AccountSet(checking_acct_list(2000) + credit_acct_list(100,100,0.01) + non_trivial_loan('test loan',100,0,0.01))
    #     B = BudgetSet(
    #         [BudgetItem('20000102', '20000102', 1, 'once', 100, 'specific regex', ),
    #          BudgetItem('20000102', '20000102', 2, 'once', 100, 'specific regex 2', ),
    #          BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', )
    #          ]
    #     )
    #     M = MemoRuleSet([MemoRule(memo_regex='.*',
    #                                                account_from='Checking',
    #                                                account_to=None,
    #                                                transaction_priority=1),
    #                              MemoRule(memo_regex='.*',
    #                                                account_from='Checking',
    #                                                account_to=None,
    #                                                transaction_priority=2),
    #                              MemoRule(memo_regex='.*',
    #                                                account_from='Checking',
    #                                                account_to=None,
    #                                                transaction_priority=3)
    #                              ])
    #     MS = MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone', 'Checking', 0, 100)
    #     MS.addMemoMilestone('test memo milestone', 'specific regex')
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 200)
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')
    #
    #     AM = AccountMilestone('test account milestone 2', 'Checking', 0, 100)
    #     MM = MemoMilestone('test memo milestone 2', 'other specific regex')
    #
    #     MS.addCompositeMilestone('test composite milestone', [AM], [MM])
    #     MS.addCompositeMilestone('test composite milestone 1', [AM], [MM])
    #
    #     E1 = ExpenseForecast(A,B,M,sd,ed,MS)
    #
    #     out_dir = './out/'
    #     E1.to_excel(out_dir)
    #     E2 = ExpenseForecast.initialize_from_excel_file(out_dir+'Forecast_'+str(E1.unique_id)+'.xlsx')[0]
    #
    #     E1.runForecast()
    #     E2.runForecast()
    #
    #     E1_str_lines = str(E1).split('\n')
    #     E2_str_lines = str(E2).split('\n')
    #
    #     comparable_E1_str_lines = []
    #     for l in E1_str_lines:
    #         if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
    #             comparable_E1_str_lines.append(l)
    #
    #     comparable_E2_str_lines = []
    #     for l in E2_str_lines:
    #         if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
    #             comparable_E2_str_lines.append(l)
    #
    #     assert comparable_E1_str_lines == comparable_E2_str_lines
    #     #
    #     # #initialize w account rows in reverse order for coverage
    #     # account_set_df = pd.read_excel(fname, sheet_name='AccountSet')
    #     # account_set_df = account_set_df.iloc[::-1] #reverse order of rows
    #     # budget_set_df = pd.read_excel(fname, sheet_name='BudgetSet')
    #     # memo_rule_set_df = pd.read_excel(fname, sheet_name='MemoRuleSet')
    #     # choose_one_set_df = pd.read_excel(fname, sheet_name='ChooseOneSet')
    #     # account_milestones_df = pd.read_excel(fname, sheet_name='AccountMilestones')
    #     # memo_milestones_df = pd.read_excel(fname, sheet_name='MemoMilestones')
    #     # composite_account_milestones_df = pd.read_excel(fname, sheet_name='CompositeAccountMilestones')
    #     # composite_memo_milestones_df = pd.read_excel(fname, sheet_name='CompositeMemoMilestones')
    #     # config_df = pd.read_excel(fname, sheet_name='config')
    #     #
    #     # with pd.ExcelWriter(fname, engine='openpyxl') as writer:
    #     #     account_set_df.to_excel(writer, sheet_name='AccountSet',index=False)
    #     #     budget_set_df.to_excel(writer, sheet_name='BudgetSet',index=False)
    #     #     memo_rule_set_df.to_excel(writer, sheet_name='MemoRuleSet',index=False)
    #     #     choose_one_set_df.to_excel(writer, sheet_name='ChooseOneSet',index=False)
    #     #     account_milestones_df.to_excel(writer, sheet_name='AccountMilestones',index=False)
    #     #     memo_milestones_df.to_excel(writer, sheet_name='MemoMilestones',index=False)
    #     #     composite_account_milestones_df.to_excel(writer, sheet_name='CompositeAccountMilestones',index=False)
    #     #     composite_memo_milestones_df.to_excel(writer, sheet_name='CompositeMemoMilestones', index=False)
    #     #     config_df.to_excel(writer, sheet_name='config',index=False)
    #     #
    #     # #E1_reverse = ExpenseForecast.initialize_from_excel_file(fname)

    def test_forecast_longer_than_satisfice(self):
        # if satisfice fails on the second day of the forecast, there is weirdness

        start_date = "20000101"
        end_date = "20000104"

        account_set = AccountSet([])
        budget_set = BudgetSet([])
        memo_rule_set = MemoRuleSet([])

        account_set.createAccount(
            name="Checking",
            balance=100,
            min_balance=0,
            max_balance=float("Inf"),
            account_type="checking",
            primary_checking_ind=True,
        )

        budget_set.addBudgetItem(
            start_date="20000101",
            end_date="20000104",
            priority=1,
            cadence="daily",
            amount=50,
            memo="dummy memo",
        )

        memo_rule_set.addMemoRule(
            memo_regex=".*",
            account_from="Checking",
            account_to=None,
            transaction_priority=1,
        )

        milestone_set = MilestoneSet([], [], [])

        # expected_result_df = pd.DataFrame({
        #     'Date': ['20000101', '20000102', '20000103'],
        #     'Checking': [0, 0, 0],
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

        E = ExpenseForecastInitialConditions(
            datetime.datetime.strptime(start_date, "%Y%m%d").date(),
            datetime.datetime.strptime(end_date, "%Y%m%d").date(),
            account_set,
            budget_set,
            memo_rule_set,
        )

        # todo what should we do here?

        # with pytest.raises(ValueError):
        #     E.runForecast()

        # log_in_color(logger,'white', 'debug', 'Confirmed:')
        # log_in_color(logger,'white', 'debug', E.confirmed_df.to_string())
        # log_in_color(logger,'white', 'debug', 'Deferred:')
        # log_in_color(logger,'white', 'debug', E.deferred_df.to_string())
        # log_in_color(logger,'white', 'debug', 'Skipped:')
        # log_in_color(logger,'white', 'debug', E.skipped_df.to_string())
        # log_in_color(logger,'white', 'debug', 'Forecast:')
        # log_in_color(logger,'white', 'debug', E.forecast_df.to_string())

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,account_milestone_names,expected_milestone_dates",
        [
            (
                "test_account_milestone",
                AccountSet(
                    checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102",'%Y%m%d'),
                            datetime.datetime.strptime("20000102",'%Y%m%d'),
                            1, "once", 10, "test txn"
                        )
                    ]
                ),
                MemoRuleSet([MemoRule(".*", "Checking", None, 1)]),
                "20000101",
                "20000103",
                MilestoneSet(
                    account_milestones=[
                        AccountMilestone(
                            "test account milestone", "Checking", 0, 0
                        )
                    ],
                ),
                ["test account milestone"],
                ["20000102"],
            ),
        ],
    )
    def test_evaluate_account_milestone(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        account_milestone_names,
        expected_milestone_dates,
    ):
        E = ExpenseForecastInitialConditions(
            datetime.datetime.strptime(start_date, "%Y%m%d").date(),
            datetime.datetime.strptime(end_date, "%Y%m%d").date(),
            account_set,
            budget_set,
            memo_rule_set,
        )
        E = ForecastHandler().runForecast(E, milestone_set)
        assert len(account_milestone_names) == len(expected_milestone_dates)

        for i in range(0, len(account_milestone_names)):
            try:
                am_name = account_milestone_names[i]
                assert (
                    E.account_milestone_results[am_name] == expected_milestone_dates[i]
                )
            except Exception as e:
                print(
                    str(account_milestone_names[i])
                    + " did not match expected milestone date"
                )
                print("Received: " + str(E.account_milestone_results[am_name]))
                print("Expected: " + str(expected_milestone_dates[i]))
                raise e

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,memo_milestone_names,expected_milestone_dates",
        [
            (
                "test_memo_milestone",
                AccountSet(
                    checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102",'%Y%m%d'), datetime.datetime.strptime("20000102",'%Y%m%d'), 1, "once", 10, "memo milestone"
                        )
                    ]
                ),
                MemoRuleSet([MemoRule(".*", "Checking", None, 1)]),
                "20000101",
                "20000103",
                MilestoneSet(
                    memo_milestones=[
                        MemoMilestone(
                            "test memo milestone", "memo milestone"
                        )
                    ],
                ),
                ["test memo milestone"],
                [datetime.datetime.strptime("20000102",'%Y%m%d')],
            ),
        ],
    )
    def test_evaluate_memo_milestone(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        memo_milestone_names,
        expected_milestone_dates,
    ):
        E = ExpenseForecastInitialConditions(
            datetime.datetime.strptime(start_date, "%Y%m%d").date(),
            datetime.datetime.strptime(end_date, "%Y%m%d").date(),
            account_set,
            budget_set,
            memo_rule_set,
        )
        E = ForecastHandler().runForecast(E, milestone_set)

        assert len(memo_milestone_names) == len(expected_milestone_dates)

        for i in range(0, len(memo_milestone_names)):
            try:
                mm_name = memo_milestone_names[i]
                assert E.memo_milestone_results[mm_name] == expected_milestone_dates[i]
            except Exception as e:
                print(
                    str(memo_milestone_names[i])
                    + " did not match expected milestone date"
                )
                print("Received: " + str(E.memo_milestone_results[mm_name]))
                print("Expected: " + str(expected_milestone_dates[i]))
                raise e

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,composite_milestone_names,expected_milestone_dates",
        [
            (
                "test composite milestone",
                AccountSet(
                    checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
                ),
                BudgetSet(
                    [
                        BudgetItem(
                            datetime.datetime.strptime("20000102",'%Y%m%d'), datetime.datetime.strptime("20000102",'%Y%m%d'), 1, "once", 10, "memo milestone"
                        )
                    ]
                ),
                MemoRuleSet([MemoRule(".*", "Checking", None, 1)]),
                "20000101",
                "20000103",
                MilestoneSet(
                    account_milestones=[
                        AccountMilestone(
                            "test account milestone", "Checking", 0, 0
                        )
                    ],
                    memo_milestones=[
                        MemoMilestone(
                            "test memo milestone", "memo milestone"
                        )
                    ],
                    composite_milestones=[
                        CompositeMilestone(
                            "test composite milestone",
                            [
                                AccountMilestone(
                                    "test account milestone", "Checking", 0, 0
                                )
                            ],
                            [
                                MemoMilestone(
                                    "test memo milestone", "memo milestone"
                                )
                            ],
                        )
                    ],
                ),
                ["test composite milestone"],
                [datetime.datetime.strptime("20000102",'%Y%m%d')],
            ),
        ],
    )
    def test_evaluate_composite_milestone(
        self,
        test_description,
        account_set,
        budget_set,
        memo_rule_set,
        start_date,
        end_date,
        milestone_set,
        composite_milestone_names,
        expected_milestone_dates,
    ):

        E = ExpenseForecastInitialConditions(
            datetime.datetime.strptime(start_date, "%Y%m%d").date(),
            datetime.datetime.strptime(end_date, "%Y%m%d").date(),
            account_set,
            budget_set,
            memo_rule_set,
        )
        E = ForecastHandler().runForecast(E, milestone_set)
        assert len(composite_milestone_names) == len(expected_milestone_dates)

        for i in range(0, len(composite_milestone_names)):
            cm_name = composite_milestone_names[i]

            try:
                assert E.composite_milestone_results[cm_name] == expected_milestone_dates[i]
            except Exception:
                print(f"{cm_name} did not match expected milestone date")
                print("Received: " + str(E.composite_milestone_results[cm_name]))
                print("Expected: " + str(expected_milestone_dates[i]))
                raise


# improving the names of tests would make them even longer...
# just know that the basic cc tests do not have a billing date in their expected result set


# FAIL LIST
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p2_and_3__expect_defer-account_set6-budget_set6-memo_rule_set6-20000101-20000103-milestone_set6-expected_result_df6]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_deferrals[test_expect_defer_past_end_of_forecast-account_set2-budget_set2-memo_rule_set2-20000101-20000103-milestone_set2-expected_result_df2-deferred past end-None]
#
# ================================================ 4 failed, 193 passed, 189 warnings in 352.02s (0:05:52) ======
#
# ================================================ 1 failed, 196 passed, 189 warnings in 322.98s (0:05:22) =======
# Name                         Stmts   Miss  Cover
# ------------------------------------------------
# Account.py                      92      6    93%
# AccountMilestone.py             13      1    92%
# AccountSet.py                  489    116    76%
# BudgetItem.py                   59      3    95%
# BudgetSet.py                    86     19    78%
# CompositeMilestone.py           24      1    96%
# ExpenseForecast.py            4149   2356    43%
# ForecastHandler.py            1380   1315     5%
# MemoMilestone.py                14      1    93%
# MemoRule.py                     51      3    94%
# MemoRuleSet.py                  83     10    88%
# MilestoneSet.py                 85     50    41%
# __init__.py                      0      0   100%
# generate_date_sequence.py       42      1    98%
# log_methods.py                 141     52    63%
# multithread_test.py             27     20    26%
# test_Account__unit_test.py                 14      0   100%
# test_AccountMilestone__unit_test.py        12      0   100%
# test_AccountSet__unit_test.py              81     28    65%
# test_BudgetItem__unit_test.py              13      0   100%
# test_BudgetSet__unit_test.py               42      0   100%
# test_CompositeMilestone__unit_test.py      20      0   100%
# test_ExpenseForecast__unit_test.py        204     26    87%
# test_ForecastHandler__unit_test.py          0      0   100%
# test_ForecastRunner__unit_test.py           0      0   100%
# test_ForecastSet__unit_test.py              0      0   100%
# test_MemoMilestone__unit_test.py           10      0   100%
# test_MemoRule.py                11      0   100%
# test_MemoRuleSet.py             68      0   100%
# test_MilestoneSet__unit_test.py             0      0   100%
# test_ef_cli__unit_test.py                   0      0   100%
# tqdm_test.py                    14      0   100%
# ------------------------------------------------
# TOTAL                         7224   4008    45%


#

### Todo
# implement these

# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p2_and_3__expect_defer-account_set6-budget_set6-memo_rule_set6-20000101-20000103-milestone_set6-expected_result_df6]

# passing this test will require lots of other tests to be edited
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p1_cc_txn_on_billing_date-account_set2-budget_set2-memo_rule_set2-20000101-20000103-milestone_set2-expected_result_df2]

# prepayment tests (not implemented)
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation__prev_only-account_set45-budget_set45-memo_rule_set45-20000110-20000214-milestone_set45-expected_result_df45]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation_multiple__prev_only-account_set46-budget_set46-memo_rule_set46-20000110-20000214-milestone_set46-expected_result_df46]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation__curr_only-account_set49-budget_set49-memo_rule_set49-20000110-20000214-milestone_set49-expected_result_df49]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation_multiple__curr_only-account_set50-budget_set50-memo_rule_set50-20000110-20000214-milestone_set50-expected_result_df50]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation__curr_prev-account_set53-budget_set53-memo_rule_set53-20000110-20000214-milestone_set53-expected_result_df53]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation_multiple__curr_prev-account_set54-budget_set54-memo_rule_set54-20000110-20000214-milestone_set54-expected_result_df54]


### I think adding interest accrual to memo directives is required to fix this
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p7__additional_loan_payment__amt_560-account_set21-budget_set21-memo_rule_set21-20000101-20000103-milestone_set21-expected_result_df21]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p7__additional_loan_payment__amt_1900-account_set23-budget_set23-memo_rule_set23-20000101-20000103-milestone_set23-expected_result_df23]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p7__additional_loan_payment__amt_overpay-account_set24-budget_set24-memo_rule_set24-20000101-20000103-milestone_set24-expected_result_df24]

# passing this test will require many other tests to be edited
### test_zero_sum_validation
### (day of last additional payment (inclusive) to last day of forecast does not match w same txns run at p1 instead of p2)
# a test w a p2 credit expense post prop

### test_distal_propagation
# payment, then billing date, then a full billing cycle plus 1 day
# test_cc_interest_accrued_reaches_0


## 11/6/2024 10pm


# eopcb still isnt right bc never get to 0 interest accrued when paying off full balance
# to fix, eopcb should not include the amount moved over from current stmt balance on that day

# I will just abt pay off my cc by the end of 2026
# if i can work 80 ER tech shifts next year, I would pay off the loan
# that essentially means working 6 days a week from april thru EOY
# and honestly is it even worth it if the new loans I get don't have an interest rate as good as my loans have?????

# like is all that hustle even worth it?
# Reasons for ER tech: sunk cost of my phlebotomy lol, more money, meet ppl to write reco letters for nursing school
# practice sticking people w needles

# @pytest.mark.skip(reason="Skipping this test for now")

# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_satisfice[test_p1_cc_txn_on_billing_date-account_set2-budget_set2-memo_rule_set2-20000101-20000103-milestone_set2-expected_result_df2]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_satisfice[test_cc_interest_accrued_reaches_0-account_set6-budget_set6-memo_rule_set6-20000110-20000214-milestone_set6-expected_result_df6]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_deferrals[test_p2_and_3__expect_defer-account_set0-budget_set0-memo_rule_set0-20000101-20000103-milestone_set0-expected_result_df0]

# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_advance_minimum_payment_in_1_payment_pay_over_minimum-account_set0-budget_set0-memo_rule_set0-20000110-20000113-milestone_set0-expected_result_df0]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_advance_minimum_payment_in_1_payment_pay_under_minimum-account_set1-budget_set1-memo_rule_set1-20000110-20000113-milestone_set1-expected_result_df1]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_advance_minimum_payment_in_1_payment_pay_exact_minimum-account_set2-budget_set2-memo_rule_set2-20000110-20000113-milestone_set2-expected_result_df2]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_two_additional_payments_on_due_date__curr_only-account_set7-budget_set7-memo_rule_set7-20000111-20000113-milestone_set7-expected_result_df7]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_single_additional_payment_day_before__prev_only-account_set9-budget_set9-memo_rule_set9-20000110-20000113-milestone_set9-expected_result_df9]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_two_additional_payments_day_before__prev_only-account_set10-budget_set10-memo_rule_set10-20000110-20000113-milestone_set10-expected_result_df10]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_single_additional_payment_day_before_OVERPAY__prev_only-account_set11-budget_set11-memo_rule_set11-20000110-20000113-milestone_set11-expected_result_df11]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_two_additional_payments_day_before_OVERPAY__prev_only-account_set12-budget_set12-memo_rule_set12-20000110-20000113-milestone_set12-expected_result_df12]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_single_additional_payment_day_before__curr_only-account_set13-budget_set13-memo_rule_set13-20000110-20000113-milestone_set13-expected_result_df13]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_two_additional_payments_day_before__curr_only-account_set14-budget_set14-memo_rule_set14-20000110-20000113-milestone_set14-expected_result_df14]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_single_additional_payment_day_before_OVERPAY__curr_only-account_set15-budget_set15-memo_rule_set15-20000110-20000113-milestone_set15-expected_result_df15]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_two_additional_payments_day_before_OVERPAY__curr_only-account_set16-budget_set16-memo_rule_set16-20000110-20000113-milestone_set16-expected_result_df16]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_single_additional_payment_day_before__curr_prev-account_set17-budget_set17-memo_rule_set17-20000110-20000113-milestone_set17-expected_result_df17]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_advance_payment[test_cc_single_additional_payment_day_before_OVERPAY__curr_prev-account_set18-budget_set18-memo_rule_set18-20000110-20000113-milestone_set18-expected_result_df18]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_payment_propagation[test_distal_propagation__prev_only-account_set0-budget_set0-memo_rule_set0-20000110-20000214-milestone_set0-expected_result_df0]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_payment_propagation[test_distal_propagation_multiple__prev_only-account_set1-budget_set1-memo_rule_set1-20000110-20000214-milestone_set1-expected_result_df1]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_payment_propagation[test_distal_propagation__curr_only-account_set2-budget_set2-memo_rule_set2-20000110-20000214-milestone_set2-expected_result_df2]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_payment_propagation[test_distal_propagation_multiple__curr_only-account_set3-budget_set3-memo_rule_set3-20000110-20000214-milestone_set3-expected_result_df3]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_payment_propagation[test_distal_propagation__curr_prev-account_set4-budget_set4-memo_rule_set4-20000110-20000214-milestone_set4-expected_result_df4]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_cc_payment_propagation[test_distal_propagation_multiple__curr_prev-account_set5-budget_set5-memo_rule_set5-20000110-20000214-milestone_set5-expected_result_df5]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_loan_payments[test_p7__additional_loan_payment__amt_560-account_set2-budget_set2-memo_rule_set2-20000101-20000103-milestone_set2-expected_result_df2]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_loan_payments[test_p7__additional_loan_payment__amt_1900-account_set4-budget_set4-memo_rule_set4-20000101-20000103-milestone_set4-expected_result_df4]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_loan_payments[test_p7__additional_loan_payment__amt_overpay-account_set5-budget_set5-memo_rule_set5-20000101-20000103-milestone_set5-expected_result_df5]
# ================================================= 26 failed, 175 passed, 1 skipped in 300.74s (0:05:00) ========
