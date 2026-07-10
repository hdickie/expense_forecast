import logging

import pytest
import pandas as pd
import tempfile
from expense_forecast.Account import Account
from expense_forecast.AccountSet import AccountSet
import doctest, copy
from datetime import date
from decimal import Decimal

from expense_forecast.CheckingBillingState import CheckingBillingState
from expense_forecast.CreditCardBillingState import CreditCardBillingState
from expense_forecast.LoanBillingState import LoanBillingState
from expense_forecast.log_methods import log_in_color

import pandas as pd
import pytest

from expense_forecast.AccountSet import AccountSet

def checking_billing_state(balance=0, is_primary=True):
    return CheckingBillingState(
        balance=Decimal(str(balance)),
        is_primary=is_primary,
    )


def credit_billing_state(
    previous_statement_balance=0,
    current_statement_balance=0,
    billing_cycle_payment_balance=0,
    minimum_payment=50,
    billing_cycle_start_date=date(2000, 1, 1),
    interest_type="compound",
    interest_interval="monthly",
    apr=0.01,
):
    return CreditCardBillingState(
        billing_cycle_start_date=billing_cycle_start_date,
        previous_statement_balance=Decimal(str(previous_statement_balance)),
        current_statement_balance=Decimal(str(current_statement_balance)),
        billing_cycle_payment_balance=Decimal(str(billing_cycle_payment_balance)),
        minimum_payment=Decimal(str(minimum_payment)),
        interest_type=interest_type,
        interest_interval=interest_interval,
        apr=Decimal(str(apr)),
    )


def loan_billing_state(
    previous_statement_balance=0,
    current_statement_balance=0,
    billing_cycle_payment_balance=0,
    minimum_payment=50,
    billing_cycle_start_date=date(2000, 1, 1),
    interest_type="simple",
    interest_interval="daily",
    apr=0.01,
):
    return LoanBillingState(
        billing_cycle_start_date=billing_cycle_start_date,
        previous_statement_balance=Decimal(str(previous_statement_balance)),
        current_statement_balance=Decimal(str(current_statement_balance)),
        billing_cycle_payment_balance=Decimal(str(billing_cycle_payment_balance)),
        minimum_payment=Decimal(str(minimum_payment)),
        interest_type=interest_type,
        interest_interval=interest_interval,
        apr=Decimal(str(apr)),
    )


def compound_loan_A():
    A = AccountSet([])
    A.createAccount(
        "test loan A",
        balance=1100,
        min_balance=0,
        max_balance=1100,
        account_type="loan",
        billing_start_date=date(2024, 1, 1),
        interest_type="compound",
        apr=0.1,
        interest_interval="monthly",
        minimum_payment=50,
        principal_balance=1000,
        interest_balance=100,
        billing_cycle_payment_balance=0,
    )
    return A.accounts


def compound_loan_A_no_interest():
    A = AccountSet([])
    A.createAccount(
        "test loan A",
        balance=1000,
        min_balance=0,
        max_balance=1100,
        account_type="loan",
        billing_start_date=date(2024, 1, 1),
        interest_type="compound",
        apr=0.1,
        interest_interval="monthly",
        minimum_payment=50,
        principal_balance=1000,
        interest_balance=0,
        billing_cycle_payment_balance=0,
    )
    return A.accounts


def compound_loan_B():
    A = AccountSet([])
    A.createAccount(
        "test loan B",
        balance=1600,
        min_balance=0,
        max_balance=1600,
        account_type="loan",
        billing_start_date=date(2024, 1, 1),
        interest_type="compound",
        apr=0.01,
        interest_interval="monthly",
        minimum_payment=50,
        principal_balance=1500,
        interest_balance=100,
        billing_cycle_payment_balance=0,
    )
    return A.accounts


def compound_loan_B_no_interest():
    A = AccountSet([])
    A.createAccount(
        "test loan B",
        balance=1500,
        min_balance=0,
        max_balance=1600,
        account_type="loan",
        billing_start_date=date(2024, 1, 1),
        interest_type="compound",
        apr=0.01,
        interest_interval="monthly",
        minimum_payment=50,
        principal_balance=1500,
        interest_balance=0,
        billing_cycle_payment_balance=0,
    )
    return A.accounts


def compound_loan_C():
    A = AccountSet([])
    A.createAccount(
        "test loan C",
        balance=2600,
        min_balance=0,
        max_balance=2600,
        account_type="loan",
        billing_start_date=date(2024, 1, 1),
        interest_type="compound",
        apr=0.05,
        interest_interval="monthly",
        minimum_payment=50,
        principal_balance=2500,
        interest_balance=100,
        billing_cycle_payment_balance=0,
    )
    return A.accounts


def compound_loan_C_no_interest():
    A = AccountSet([])
    A.createAccount(
        "test loan C",
        balance=2500,
        min_balance=0,
        max_balance=2600,
        account_type="loan",
        billing_start_date=date(2024, 1, 1),
        interest_type="compound",
        apr=0.05,
        interest_interval="monthly",
        minimum_payment=50,
        principal_balance=2500,
        interest_balance=0,
        billing_cycle_payment_balance=0,
    )
    return A.accounts


def checking():
    A = AccountSet([])
    A.createAccount(
        "test checking",
        balance=10000,
        min_balance=0,
        max_balance=10000,
        account_type="checking",
        primary_checking_ind=True,
    )
    return A.accounts


def cc(curr_bal, prev_bal, apr, bsd):
    A = AccountSet([])
    A.createAccount(
        name="test cc",
        balance=curr_bal + prev_bal,
        min_balance=0,
        max_balance=20000,
        account_type="credit",
        billing_start_date=bsd,
        apr=apr,
        interest_interval="monthly",
        minimum_payment=40,
        previous_statement_balance=prev_bal,
        current_statement_balance=curr_bal,
        end_of_previous_cycle_balance=prev_bal,
    )
    return A.accounts


def one_loan__p_1000__i_100__apr_01():
    return AccountSet(checking() + compound_loan_A())


def two_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001():
    return AccountSet(checking() + compound_loan_A() + compound_loan_B())


def three_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001___p_2500__i_100__apr_005():
    return AccountSet(
        checking() + compound_loan_A() + compound_loan_B() + compound_loan_C()
    )


# def one_loan__p_1000__i_000__apr_01():
#     return AccountSet(checking()+compound_loan_A_no_interest())
#
# def two_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001():
#     return AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest())


# todo should these be fixtures?
def three_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001___p_2500__i_000__apr_005():
    return AccountSet(
        checking()
        + compound_loan_A_no_interest()
        + compound_loan_B_no_interest()
        + compound_loan_C_no_interest()
    )


class TestAccountSet:

    # @pytest.mark.unit
    # @pytest.mark.skip(reason="do I still need this?")
    # def test_AccountSet_doctests(self):
    #     # doctest.testmod(doctest_AccountSet,name="doctest_AccountSet")
    #     # doctest.DocTestSuite(module='doctest_AccountSet')
    #     # doctest.testfile('doctest_AccountSet.py')
    #     # doctest.run_docstring_examples('doctest_AccountSet.py',globs={})
    #     doctest.testmod(AccountSet)

    def _checking_account(self, name="test checking", balance=0, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="checking",
            billing_state=checking_billing_state(balance=balance, is_primary=True),
        )

    def _principal_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="loan",
            billing_state=loan_billing_state(
                previous_statement_balance=balance,
                current_statement_balance=balance,
            ),
        )

    def _interest_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="loan",
            billing_state=loan_billing_state(
                previous_statement_balance=balance,
                current_statement_balance=balance,
            ),
        )

    def _loan_billing_cycle_payment_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="loan",
            billing_state=loan_billing_state(
                previous_statement_balance=balance,
                current_statement_balance=balance,
                billing_cycle_payment_balance=balance,
            ),
        )

    def _loan_end_of_prev_cycle_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="loan",
            billing_state=loan_billing_state(
                previous_statement_balance=balance,
                current_statement_balance=balance,
            ),
        )

    def _credit_curr_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="credit",
            billing_state=credit_billing_state(
                current_statement_balance=balance,
            ),
        )

    def _credit_prev_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="credit",
            billing_state=credit_billing_state(
                previous_statement_balance=balance,
            ),
        )

    def _credit_billing_cycle_payment_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="credit",
            billing_state=credit_billing_state(
                billing_cycle_payment_balance=balance,
            ),
        )

    def _credit_end_of_prev_cycle_account(self, name, balance, min_balance=0, max_balance=100):
        return Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="credit",
            billing_state=credit_billing_state(
                previous_statement_balance=balance,
            ),
        )

    def _valid_transaction_account_set(self):
        account_set = AccountSet([])
        account_set.createCheckingAccount(
            "test checking",
            balance=1000.0,
            min_balance=0.0,
            max_balance=float("inf"),
            primary_checking_ind=False,
        )
        account_set.createCreditCardAccount(
            "test credit",
            current_statement_balance=1000.0,
            previous_statement_balance=500.0,
            min_balance=0.0,
            max_balance=20000.0,
            billing_start_date=date(2000, 1, 7),
            apr=0.2479,
            minimum_payment=20.0,
            end_of_previous_cycle_balance=500.0,
        )
        account_set.createLoanAccount(
            "test loan",
            principal_balance=900.0,
            interest_balance=100.0,
            min_balance=0,
            max_balance=26000.0,
            billing_start_date=date(2023, 3, 3),
            apr=0.067,
            minimum_payment=223.19,
            billing_cycle_payment_balance=0,
        )
        return account_set

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "accounts__list",
        [
            [],
            [
                Account(
                    name="test checking",
                    balance=0,
                    min_balance=0,
                    max_balance=100,
                    account_type="checking",
                    billing_state=checking_billing_state(balance=0, is_primary=True),
                )
            ],
        ],
    )
    def test_AccountSet_Constructor__valid_inputs(self, accounts__list):
        AccountSet(accounts__list)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "accounts__list",
        [
            [
                _principal_account(None, "test combined total violates maximum", 60, 0, 100),
                _interest_account(None, "test combined total violates maximum", 60, 0, 100),
                _loan_billing_cycle_payment_account(None, "test combined total violates maximum", 0, 0, 100),
                _loan_end_of_prev_cycle_account(None, "test combined total violates maximum", 60, 0, 100),
            ],
            [
                _credit_curr_account(None, "test cc", 60, 0, 100),
                _credit_prev_account(None, "test cc", 60, 0, 100),
                _credit_billing_cycle_payment_account(None, "test cc", 0, 0, 100),
                _credit_end_of_prev_cycle_account(None, "test cc", 60, 0, 100),
            ],
            [
                _interest_account(None, "loan", 60, 0, 100),
                _loan_billing_cycle_payment_account(None, "loan", 0, 0, 100),
                _loan_end_of_prev_cycle_account(None, "loan", 60, 0, 100),
            ],
            [
                Account(
                    name="duplicate",
                    balance=0,
                    min_balance=0,
                    max_balance=100,
                    account_type="checking",
                    billing_state=checking_billing_state(balance=0, is_primary=True),
                ),
                Account(
                    name="duplicate",
                    balance=0,
                    min_balance=0,
                    max_balance=100,
                    account_type="checking",
                    billing_state=checking_billing_state(balance=0, is_primary=False),
                ),
            ],
        ],
    )
    def test_AccountSet_Constructor__invalid_inputs(self, accounts__list):
        with pytest.raises(Exception):
            AccountSet(accounts__list)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "Account_From,Account_To,Amount,income_flag,expected_result_vector",
        [
            ("test checking", None, 0.0, False, [1000.0, 1500.0, 1000.0]),
            ("test checking", None, 100.0, False, [900.0, 1500.0, 1000.0]),
            (None, "test checking", 100.0, True, [1100.0, 1500.0, 1000.0]),
            ("test credit", None, 100.0, False, [1000.0, 1600.0, 1000.0]),
            ("test checking", "test credit", 50.0, False, [950.0, 1450.0, 1000.0]),
            ("test checking", "test credit", 501.0, False, [499.0, 999.0, 1000.0]),
            ("test checking", "test loan", 50.0, False, [950.0, 1500.0, 950.0]),
            ("test checking", "test loan", 150.0, False, [850.0, 1500.0, 850.0]),
        ],
    )
    def test_execute_transaction_valid_inputs(
        self, Account_From, Account_To, Amount, income_flag, expected_result_vector
    ):
        test_account_set = self._valid_transaction_account_set()

        test_account_set.executeTransaction(
            Account_From=Account_From,
            Account_To=Account_To,
            Amount=Amount,
            income_flag=income_flag,
        )

        result_vector = list(test_account_set.getAccounts().iloc[:, 1])
        assert result_vector == expected_result_vector

    @pytest.mark.unit
    def test_allocate_additional_loan_payments_uses_refactored_loan_accounts(self):
        test_account_set = AccountSet([])
        test_account_set.createCheckingAccount(
            "test checking",
            balance=1000.0,
            min_balance=0.0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )
        test_account_set.createLoanAccount(
            "higher marginal interest loan",
            principal_balance=1000.0,
            interest_balance=10.0,
            min_balance=0,
            max_balance=2000.0,
            billing_start_date=date(2026, 1, 1),
            apr=0.1,
            minimum_payment=40.0,
        )
        test_account_set.createLoanAccount(
            "lower marginal interest loan",
            principal_balance=1000.0,
            interest_balance=10.0,
            min_balance=0,
            max_balance=2000.0,
            billing_start_date=date(2026, 1, 1),
            apr=0.05,
            minimum_payment=40.0,
        )

        result = test_account_set.allocate_additional_loan_payments(
            100.0, account_from="test checking"
        )

        assert result == [
            ["test checking", "higher marginal interest loan", Decimal("100.0")]
        ]

    @pytest.mark.unit
    def test_execute_transaction_all_loans_uses_refactored_loan_accounts(self):
        test_account_set = AccountSet([])
        test_account_set.createCheckingAccount(
            "test checking",
            balance=1000.0,
            min_balance=0.0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )
        test_account_set.createLoanAccount(
            "higher marginal interest loan",
            principal_balance=1000.0,
            interest_balance=10.0,
            min_balance=0,
            max_balance=2000.0,
            billing_start_date=date(2026, 1, 1),
            apr=0.1,
            minimum_payment=40.0,
        )
        test_account_set.createLoanAccount(
            "lower marginal interest loan",
            principal_balance=1000.0,
            interest_balance=10.0,
            min_balance=0,
            max_balance=2000.0,
            billing_start_date=date(2026, 1, 1),
            apr=0.05,
            minimum_payment=40.0,
        )

        test_account_set.executeTransaction(
            Account_From="test checking",
            Account_To="ALL_LOANS",
            Amount=100.0,
        )

        result = test_account_set.getAccounts().set_index("Name")
        assert result.loc["test checking", "Balance"] == Decimal("900.0")
        assert (
            result.loc["higher marginal interest loan", "Balance"]
            == Decimal("910.0")
        )
        assert (
            result.loc["lower marginal interest loan", "Balance"]
            == Decimal("1010.0")
        )

    @pytest.mark.unit
    def test_allocate_additional_loan_payments_treats_near_equal_marginal_interest_as_tied(self):
        test_account_set = AccountSet([])
        test_account_set.createCheckingAccount(
            "test checking",
            balance=10000.0,
            min_balance=0.0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )
        test_account_set.createLoanAccount(
            "barely higher loan",
            principal_balance=3540.710620300949,
            interest_balance=12.48,
            min_balance=0,
            max_balance=10000.0,
            billing_start_date=date(2030, 12, 1),
            apr=0.0429,
            minimum_payment=40.0,
        )
        test_account_set.createLoanAccount(
            "effectively tied loan",
            principal_balance=1518.9648561091071,
            interest_balance=12.48,
            min_balance=0,
            max_balance=10000.0,
            billing_start_date=date(2030, 12, 1),
            apr=0.1,
            minimum_payment=40.0,
        )

        result = test_account_set.allocate_additional_loan_payments(
            5500.0, account_from="test checking"
        )

        allocated_amount = sum(payment[2] for payment in result)
        assert allocated_amount == pytest.approx(Decimal("5084.64"), abs=0.01)
        assert {payment[1] for payment in result} == {
            "barely higher loan",
            "effectively tied loan",
        }

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "name,balance,min_balance,max_balance,account_type,kwargs",
        [
            (
                "test loan",
                100,
                0,
                100,
                "loan",
                {
                    "billing_start_date": date(2000, 1, 1),
                    "apr": 0.1,
                    "interest_interval": "monthly",
                    "minimum_payment": 50,
                    "interest_balance": 100,
                    "billing_cycle_payment_balance": 0,
                },
            ),
            (
                "test loan",
                100,
                0,
                100,
                "loan",
                {
                    "billing_start_date": date(2000, 1, 1),
                    "apr": 0.1,
                    "interest_interval": "monthly",
                    "minimum_payment": 50,
                    "principal_balance": 100,
                    "billing_cycle_payment_balance": 0,
                },
            ),
            (
                "test credit",
                100,
                0,
                100,
                "credit",
                {
                    "billing_start_date": date(2000, 1, 1),
                    "apr": 0.1,
                    "interest_interval": "monthly",
                    "minimum_payment": 50,
                    "end_of_previous_cycle_balance": 100,
                },
            ),
            (
                "test loan",
                100,
                0,
                100,
                "loan",
                {
                    "billing_start_date": date(2000, 1, 1),
                    "apr": 0.1,
                    "interest_interval": "monthly",
                    "minimum_payment": 50,
                    "principal_balance": 100,
                    "interest_balance": 100,
                    "billing_cycle_payment_balance": 0,
                },
            ),
            # ( #this looks like valid input to me
            #     "test checking",
            #     0,
            #     0,
            #     100,
            #     "checking",
            #     {"primary_checking_ind": True},
            # ),
        ],
    )
    def test_createAccount__invalid_inputs(
        self, name, balance, min_balance, max_balance, account_type, kwargs
    ):
        with pytest.raises(ValueError):
            A = AccountSet([])
            A.createAccount(
                name,
                balance,
                min_balance,
                max_balance,
                account_type,
                **kwargs,
            )

    @pytest.mark.unit
    def test_getAccounts(self):
        test_account_set = AccountSet([self._checking_account()])
        test_df = test_account_set.getAccounts()

        assert list(test_df.columns) == [
            "Name",
            "Balance",
            "Min_Balance",
            "Max_Balance",
            "Account_Type",
            "Billing_Start_Date",
            "Interest_Type",
            "APR",
            "Interest_interval",
            "Minimum_Payment",
            "Primary_Checking_Ind",
        ]
        assert test_df.iloc[0].Name == "test checking"

    @pytest.mark.unit
    def test_str(self):
        test_str_account_set = AccountSet([self._checking_account()])

        assert "test checking" in str(test_str_account_set)

    @pytest.mark.unit
    def test_validate_one_and_only_one_primary_checking_account(self):
        # exactly one primary checking account: valid
        A = AccountSet()
        A.createAccount(
            name="Checking",
            balance=100,
            min_balance=0,
            max_balance=999999,
            account_type="checking",
            primary_checking_ind=True,
        )

        AccountSet._validate_one_and_only_one_primary_checking_account(A.getAccounts())

        # zero primary checking accounts: invalid
        A = AccountSet()
        A.createAccount(
            name="Checking",
            balance=100,
            min_balance=0,
            max_balance=999999,
            account_type="checking",
            primary_checking_ind=False,
        )

        with pytest.raises(ValueError, match="AccountSet must have one and only one primary checking account"):
            AccountSet._validate_one_and_only_one_primary_checking_account(A.getAccounts())

        # two primary checking accounts: invalid
        A = AccountSet()
        A.createAccount(
            name="Checking 1",
            balance=100,
            min_balance=0,
            max_balance=999999,
            account_type="checking",
            primary_checking_ind=True,
        )
        with pytest.raises(ValueError, match="AccountSet must have one and only one primary checking account"):
            # AccountSet._validate_one_and_only_one_primary_checking_account(A.getAccounts())
            A.createAccount(
                name="Checking 2",
                balance=200,
                min_balance=0,
                max_balance=999999,
                account_type="checking",
                primary_checking_ind=True,
            )

        

    #

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "accounts__list,expected_exception",
    #     [
    #         (
    #             [
    #                 Account(
    #                     name="test combined total violates maximum : Principal Balance",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test combined total violates maximum : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test combined total violates maximum : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates max (loan)
    #         (
    #             [
    #                 Account(
    #                     name="test cc : Prev Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test cc : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test cc : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates max (cc)
    #         (
    #             [
    #                 Account(
    #                     name="test cc : Prev Stmt Bal",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test cc : Curr Stmt Bal",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test cc : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates min (cc)
    #         (
    #             [
    #                 Account(
    #                     name="test : Principal Balance",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test : Interest",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates min (loan)
    #         (
    #             [
    #                 Account(
    #                     name="test combined total violates maximum : Principal Balance",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test combined total violates maximum : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test combined total violates maximum : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching max_balance (loan)
    #         (
    #             [
    #                 Account(
    #                     name="test combined total violates maximum : Prev Stm Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test combined total violates maximum : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=60,
    #                     max_balance=1000,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test combined total violates maximum : Credit Billing Cycle Payment Bal",
    #                     balance=60,
    #                     min_balance=60,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching min_balance (cc)
    #         (
    #             [
    #                 Account(
    #                     name="test : Principal Balance",
    #                     balance=10,
    #                     min_balance=10,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching min_balance (loan)
    #         (
    #             [
    #                 Account(
    #                     name="test : Prev Stmt Bal",
    #                     balance=10,
    #                     min_balance=10,
    #                     max_balance=100,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching min_balance (cc)
    #         (
    #             [
    #                 Account(
    #                     name="test : Prev Stmt Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=110,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account(
    #                     name="test : Curr Stmt Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching max_balance (cc)
    #         (
    #             [
    #                 Account(
    #                     name="loan : Principal Balance",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # pbal no interest
    #         (
    #             [
    #                 Account(
    #                     name="loan : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account(
    #                     name="loan : Loan Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="loan billing cycle payment bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # interest no pbal
    #         (
    #             [
    #                 Account(
    #                     name="cc : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # curr no prev
    #         (
    #             [
    #                 Account(
    #                     name="cc : Prev Stmt Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # prev no curr
    #         (
    #             [
    #                 Account(
    #                     name="test loan : Principal Balance",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=date(2000, 1, 1),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_interval="monthly",
    #                     minimum_payment=50,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # pbal no int
    #         (
    #             [
    #                 Account(
    #                     name="test loan : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_interval=None,
    #                     minimum_payment=None,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # int no pbal
    #         # [Account(
    #         #     name,
    #         #     balance,
    #         #     min_balance,
    #         #     max_balance,
    #         #     account_type,
    #         #     billing_start_date=None,
    #         #     interest_type=None,
    #         #     apr=None,
    #         #     interest_interval=None,
    #         #     minimum_payment=None
    #         # )],
    #     ],
    # )
    # def test_AccountSet_Constructor__invalid_inputs(
    #     self, accounts__list, expected_exception
    # ):
    #
    #     with pytest.raises(expected_exception):
    #         AccountSet(accounts__list)

    # @pytest.mark.parametrize(
    #     "accounts__list",
    #     [
    #         ([]),  # empty list as input
    #         (
    #             [
    #                 Account(
    #                     name="test checking",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="checking",
    #                     primary_checking_ind=True
    #                 )
    #             ]
    #         ),
    #     ],
    # )
    # def test_AccountSet_Constructor__valid_inputs(self, accounts__list):
    #
    #     AccountSet(accounts__list)

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "Account_From, Account_To, Amount,income_flag,expected_result_vector",
    #     [
    #         (
    #             "test checking",
    #             None,
    #             0.0,
    #             False,
    #             [1000.0, 1000.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # txn for 0
    #         (
    #             "test checking",
    #             None,
    #             100.0,
    #             False,
    #             [900.0, 1000.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # withdraw from checking account
    #         (
    #             None,
    #             "test checking",
    #             100.0,
    #             True,
    #             [1100.0, 1000.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # deposit to checking account
    #         (
    #             "test credit",
    #             None,
    #             100.0,
    #             False,
    #             [1000.0, 1100.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # pay using credit
    #         (
    #             "test checking",
    #             "test credit",
    #             50.0,
    #             False,
    #             [950.0, 1000.0, 450.0, 50, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # credit payment, less than credit prev stmt bal and credit curr stmt bal > 0
    #         (
    #             "test checking",
    #             "test credit",
    #             501.0,
    #             False,
    #             [499.0, 999.0, 0.0, 501, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # credit payment, less than total balance, more than credit prev stmt balance, credit curr stmt bal != 0
    #         (
    #             "test checking",
    #             "test loan",
    #             50.0,
    #             False,
    #             [950.0, 1000.0, 500.0, 0, 500, 900.0, 50.0, 50, 900.0],
    #         ),  # loan payment, less than interest
    #         (
    #             "test checking",
    #             "test loan",
    #             150.0,
    #             False,
    #             [850.0, 1000.0, 500.0, 0, 500, 850.0, 0.0, 150, 900.0],
    #         ),  # loan payment, more than interest
    #         (
    #             "test checking",
    #             "ALL_LOANS",
    #             150.0,
    #             False,
    #             [850.0, 1000.0, 500.0, 0, 500, 850.0, 0.0, 150, 900.0],
    #         ),  # loan payment, more than interest
    #     ],
    # )
    # def test_execute_transaction_valid_inputs(
    #     self, Account_From, Account_To, Amount, income_flag, expected_result_vector
    # ):
    #     test_account_set = AccountSet([])
    #     test_account_set.createAccount(
    #         name="test checking",
    #         balance=1000.0,
    #         min_balance=0.0,
    #         max_balance=float("inf"),
    #         account_type="checking",
    #         billing_start_date=None,
    #         interest_type=None,
    #         apr=None,
    #         interest_interval=None,
    #         minimum_payment=None,
    #         previous_statement_balance=None,
    #         principal_balance=None,
    #         interest_balance=None,
    #         billing_cycle_payment_balance=0,
    #         primary_checking_ind=True,
    #         print_debug_messages=False,
    #     )
    #
    #     test_account_set.createAccount(
    #         name="test credit",
    #         balance=1500.0,
    #         min_balance=0.0,
    #         max_balance=20000.0,
    #         account_type="credit",
    #         billing_start_date="20000107",
    #         interest_type=None,
    #         apr=0.2479,
    #         interest_interval="monthly",
    #         minimum_payment=20.0,
    #         previous_statement_balance=500.0,
    #         current_statement_balance=1000.0,
    #         principal_balance=None,
    #         interest_balance=None,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=500.0,
    #         print_debug_messages=False,
    #     )
    #
    #     test_account_set.createAccount(
    #         name="test loan",
    #         balance=1000.0,
    #         min_balance=0,
    #         max_balance=26000.0,
    #         account_type="loan",
    #         billing_start_date="20230303",
    #         interest_type="simple",
    #         apr=0.067,
    #         interest_interval="daily",
    #         minimum_payment="223.19",
    #         previous_statement_balance=None,
    #         principal_balance=900.0,
    #         interest_balance=100.0,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=900,
    #         print_debug_messages=False,
    #     )
    #
    #     test_account_set.executeTransaction(
    #         Account_From=Account_From,
    #         Account_To=Account_To,
    #         Amount=Amount,
    #         income_flag=income_flag,
    #     )
    #     result_vector = list(test_account_set.getAccounts().iloc[:, 1])
    #     assert result_vector == expected_result_vector

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "name,balance,min_balance,max_balance,account_type,billing_start_date,interest_type,apr,interest_interval,minimum_payment,previous_statement_balance,principal_balance,interest_balance,expected_exception",
    #     [
    #         (
    #             "test loan",
    #             100,
    #             0,
    #             100,
    #             "loan",
    #             "20000101",
    #             "compoung",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             None,
    #             100,
    #             ValueError,
    #         ),  # miss pbal for type loan
    #         (
    #             "test loan",
    #             100,
    #             0,
    #             100,
    #             "loan",
    #             "20000101",
    #             "compoung",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             100,
    #             None,
    #             ValueError,
    #         ),  # missing interest for type loan
    #         (
    #             "test credit",
    #             100,
    #             0,
    #             100,
    #             "credit",
    #             "20000101",
    #             "compound",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             None,
    #             None,
    #             ValueError,
    #         ),  # missing credit prev stmt bal for type credit
    #         (
    #             "test loan",
    #             100,
    #             0,
    #             100,
    #             "loan",
    #             "20000101",
    #             "compoung",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             100,
    #             100,
    #             ValueError,
    #         ),  # pbal + interest != balance
    #         # (name,
    #         #  balance,
    #         #  min_balance,
    #         #  max_balance,
    #         #  account_type,
    #         #  billing_start_date,
    #         #  interest_type,
    #         #  apr,
    #         #  interest_interval,
    #         #  minimum_payment,
    #         #  previous_statement_balance,
    #         #  principal_balance,
    #         #  interest_balance
    #         #  , ValueError),  # missing interest for type loan
    #     ],
    # )
    # def test_createAccount__invalid_inputs(
    #     self,
    #     name,
    #     balance,
    #     min_balance,
    #     max_balance,
    #     account_type,
    #     billing_start_date,
    #     interest_type,
    #     apr,
    #     interest_interval,
    #     minimum_payment,
    #     previous_statement_balance,
    #     principal_balance,
    #     interest_balance,
    #     expected_exception,
    # ):
    #
    #     with pytest.raises(expected_exception):
    #         A = AccountSet([])
    #         A.createAccount(
    #             name,
    #             balance,
    #             min_balance,
    #             max_balance,
    #             account_type,
    #             billing_start_date,
    #             interest_type,
    #             apr,
    #             interest_interval,
    #             minimum_payment,
    #             previous_statement_balance,
    #             principal_balance,
    #             interest_balance,
    #         )

    ### I think this test isn't very strong and will be covered in E2E cases
    # @pytest.mark.unit
    # def test_getAccounts(self):
    #     test_account_set = AccountSet([])
    #
    #     test_account_set.createAccount(
    #         name="test checking",
    #         balance=0,
    #         min_balance=0,
    #         max_balance=0,
    #         account_type="checking",
    #     )
    #     test_df = test_account_set.getAccounts()
    #     assert test_df is not None

    ### belongs in integration tests
    # @pytest.mark.unit
    # @pytest.mark.skip(reason="this test needs to be improved")
    # def test_str(self):
    #     test_str_account_set = AccountSet([])
    #
    #     # create a non-loan and non-credit type account
    #     test_str_account_set.createAccount(
    #         name="test checking",
    #         balance=0,
    #         min_balance=0,
    #         max_balance=0,
    #         account_type="checking",
    #     )
    #
    #     # create a credit card type account
    #     test_str_account_set.createAccount(
    #         name="test credit",
    #         balance=0,
    #         min_balance=0,
    #         max_balance=0,
    #         account_type="credit",
    #         billing_start_date="20220101",
    #         interest_type=None,
    #         apr=0.05,
    #         interest_interval="monthly",
    #         minimum_payment=0,
    #         previous_statement_balance=0,
    #         current_statement_balance=0,
    #         principal_balance=None,
    #         interest_balance=None,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=0,
    #     )
    #
    #     # create a loan type account
    #     test_str_account_set.createAccount(
    #         name="test loan",
    #         balance=1000,
    #         min_balance=0,
    #         max_balance=10000,
    #         account_type="loan",
    #         billing_start_date="20220101",
    #         interest_type="simple",
    #         apr=0.03,
    #         interest_interval="daily",
    #         minimum_payment=1,
    #         previous_statement_balance=None,
    #         principal_balance=900,
    #         interest_balance=100,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=0,
    #     )
    #
    #     str(test_str_account_set)

    # These test cases were selected using math to ensure coverage of all cases.
    # See the gist of explanation here:
    # https://gist.github.com/hdickie/98e35458aac8a5cfd4cd7e268cf3bd55
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_name, advance_payment_amount, interest_accrued_this_cycle, principal_due_this_cycle, total_balance_post_accrual, min_payment, expected_result",
        [
            ("NZ_20210_0111", 100, 400, 100, 300, 200, 400),  # gpt helped
            ("Z_02110_1001", 0, 200, 100, 100, 100, 300),  # gpt helped
            # ("Z_42010_1110", 200, 300, 100, 300, 0, -1,),  # todo get rid of these or make them real
            # ("NZ_23100_1001", 200, 200, 100, 300, 200, -1),
            # ("NZ_11010_0100", 200, 100, 100, 200, 200, -1),
            # ("Z_41100_1111", 300, 100, 200, 400, 0, -1),
            # ("NZ_20200_0001", 100, 100, 100, 200, 100, -1),
            # ("NZ_10010_0001", 100, 100, 100, 200, 100, -1),
            # ("Z_03100_1011", 0, 200, 100, 300, 100, -1),
            # ("NZ_01000_0010", 100, 100, 100, 200, 200, -1),
        ],
    )
    def test_determineMinPaymentAmount(
        self,
        test_name,
        advance_payment_amount,
        interest_accrued_this_cycle,
        principal_due_this_cycle,
        total_balance_post_accrual,
        min_payment,
        expected_result,
    ):
        if expected_result == -1:
            pass
        else:
            try:
                print(
                    "test_name, advance_payment_amount, interest_accrued_this_cycle, principal_due_this_cycle, total_balance_post_accrual, min_payment, expected_result"
                )
                print(
                    test_name,
                    advance_payment_amount,
                    interest_accrued_this_cycle,
                    principal_due_this_cycle,
                    total_balance_post_accrual,
                    min_payment,
                    expected_result,
                )
                assert float(expected_result) == AccountSet.determineMinPaymentAmount(
                    float(advance_payment_amount),
                    float(interest_accrued_this_cycle),
                    float(principal_due_this_cycle),
                    float(total_balance_post_accrual),
                    float(min_payment),
                )
            except Exception as e:
                raise e

# TODO implement a test case to try and create multiple loans with the same name


# Migration notes:
# - Migrated active coverage from old__test_AccountSet__unit_test.py into the newer
#   package-import/direct-class style used by test_Account__unit_test.py.
# - Added current-API fixture helpers that construct Account objects with **kwargs and
#   date billing_start_date values instead of the old positional/string-date API.
# - Restored active coverage for AccountSet constructor valid/invalid inputs,
#   executeTransaction happy paths, createAccount invalid inputs, getAccounts, and __str__.
# - Kept createAccount valid-input coverage out of the active suite because the current
#   checking branch requires primary_checking_ind but reads primary_checking_account_ind.
# - Added a skipped stub for _validate_one_and_only_one_primary_checking_account because
#   the production validator currently raises NotImplementedError.
# - Did not migrate the old ALL_LOANS executeTransaction case because it depends on the
#   unimplemented primary-checking-account validator/name tracking behavior.
# - While restoring transaction coverage, fixed two production NameErrors in AccountSet:
#   bare log_in_color usage and bare ROUNDING_ERROR_TOLERANCE usage.
#
# Recommended next changes:
# - Implement _validate_one_and_only_one_primary_checking_account and primary checking
#   name tracking, then unskip the stub and restore ALL_LOANS transaction coverage.
# - Fix createAccount's checking kwargs mismatch, then add active createAccount valid
#   tests for checking, credit, and loan account creation.
# - Tighten invalid constructor tests to specific exception types once AccountSet
#   validators consistently use ValueError/TypeError instead of assertions.
