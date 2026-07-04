from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from expense_forecast.Account import Account
from expense_forecast.CheckingBillingState import CheckingBillingState
from expense_forecast.CreditCardBillingState import CreditCardBillingState
from expense_forecast.LoanBillingState import LoanBillingState
from expense_forecast.SavingsBillingState import SavingsBillingState


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
    interest_cadence="monthly",
    apr=0.25,
):
    return CreditCardBillingState(
        billing_cycle_start_date=billing_cycle_start_date,
        previous_statement_balance=Decimal(str(previous_statement_balance)),
        current_statement_balance=Decimal(str(current_statement_balance)),
        billing_cycle_payment_balance=Decimal(str(billing_cycle_payment_balance)),
        minimum_payment=Decimal(str(minimum_payment)),
        interest_type=interest_type,
        interest_cadence=interest_cadence,
        apr=Decimal(str(apr)),
    )


def loan_billing_state(
    previous_statement_balance=0,
    current_statement_balance=0,
    billing_cycle_payment_balance=0,
    minimum_payment=50,
    billing_cycle_start_date=date(2000, 1, 1),
    interest_type="simple",
    interest_cadence="daily",
    apr=0.25,
):
    return LoanBillingState(
        billing_cycle_start_date=billing_cycle_start_date,
        previous_statement_balance=Decimal(str(previous_statement_balance)),
        current_statement_balance=Decimal(str(current_statement_balance)),
        billing_cycle_payment_balance=Decimal(str(billing_cycle_payment_balance)),
        minimum_payment=Decimal(str(minimum_payment)),
        interest_type=interest_type,
        interest_cadence=interest_cadence,
        apr=Decimal(str(apr)),
    )


def savings_billing_state(
    previous_statement_balance=0,
    current_statement_balance=0,
    billing_cycle_payment_balance=0,
    minimum_payment=0,
    billing_cycle_start_date=date(2000, 1, 1),
    interest_type="compound",
    interest_cadence="daily",
    apr=0.01,
):
    return SavingsBillingState(
        billing_cycle_start_date=billing_cycle_start_date,
        previous_statement_balance=Decimal(str(previous_statement_balance)),
        current_statement_balance=Decimal(str(current_statement_balance)),
        billing_cycle_payment_balance=Decimal(str(billing_cycle_payment_balance)),
        minimum_payment=Decimal(str(minimum_payment)),
        interest_type=interest_type,
        interest_cadence=interest_cadence,
        apr=Decimal(str(apr)),
    )


class TestAccount:

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "name,balance,min_balance,max_balance,account_type,billing_state",
        [
            ("checking", 0, 0, 100, "checking", checking_billing_state()),
            ("credit", 500, 0, 5000, "credit", credit_billing_state(200, 300)),
            ("loan", 900, 0, 5000, "loan", loan_billing_state(800, 900)),
            ("savings", 100, 0, 5000, "savings", savings_billing_state(100, 100)),
        ],
    )
    def test_Account_constructor_valid_inputs(
        self, name, balance, min_balance, max_balance, account_type, billing_state
    ):
        account = Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type=account_type,
            billing_state=billing_state,
        )

        assert account.name == name
        assert account.balance == balance
        assert account.min_balance == min_balance
        assert account.max_balance == max_balance
        assert account.account_type == account_type
        assert account.billing_state == billing_state

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "name,balance,min_balance,max_balance,account_type,kwargs",
        [
            ("invalid account type", 0, 0, 100, "shmecking", {}),
            ("missing billing state", 0, 0, 100, "checking", {}),
            (
                "wrong billing state",
                0,
                0,
                100,
                "checking",
                {"billing_state": credit_billing_state()},
            ),
            (
                "unexpected kwarg",
                0,
                0,
                100,
                "checking",
                {"billing_state": checking_billing_state(), "unknown": True},
            ),
            (
                "balance below min",
                0,
                10,
                100,
                "checking",
                {"billing_state": checking_billing_state()},
            ),
            (
                "balance above max",
                101,
                0,
                100,
                "checking",
                {"billing_state": checking_billing_state()},
            ),
        ],
    )
    def test_Account_constructor_invalid_inputs(
        self, name, balance, min_balance, max_balance, account_type, kwargs
    ):
        with pytest.raises(Exception):
            Account(
                name=name,
                balance=balance,
                min_balance=min_balance,
                max_balance=max_balance,
                account_type=account_type,
                **kwargs,
            )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "min_balance,balance,max_balance",
        [
            (0, 0, 0),
            (0, 5, 10),
            (-100, 0, 100),
        ],
    )
    def test_validate_balances__expect_success(self, min_balance, balance, max_balance):
        Account._validate_balances(min_balance, balance, max_balance, None)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "min_balance,balance,max_balance",
        [
            (10, 0, 20),
            (0, 10, 5),
            (10, 10, 0),
            (None, 0, 0),
            (0, None, 0),
            (0, 0, None),
            ("X", 0, 0),
            (0, "X", 0),
            (0, 0, "X"),
            (pd.NA, 0, 0),
            (0, pd.NA, 0),
            (0, 0, pd.NA),
        ],
    )
    def test_validate_balances__expect_fail(self, min_balance, balance, max_balance):
        with pytest.raises(Exception):
            Account._validate_balances(min_balance, balance, max_balance, None)

    @pytest.mark.unit
    @pytest.mark.parametrize("account_type", ["checking", "credit", "loan", "savings"])
    def test_validate_account_type__expect_success(self, account_type):
        Account._validate_account_type(account_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type",
        ["Checking", "credit prev stmt bal", "principal balance", "interest", None],
    )
    def test_validate_account_type__expect_fail(self, account_type):
        with pytest.raises(Exception):
            Account._validate_account_type(account_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,apr",
        [
            ("credit", 0),
            ("credit", 0.25),
            ("loan", 0.25),
            ("savings", 0.01),
            ("checking", None),
        ],
    )
    def test_validate_apr__expect_success(self, account_type, apr):
        Account._validate_apr(account_type, apr)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,apr",
        [
            ("credit", None),
            ("loan", None),
            ("savings", None),
            ("credit", -0.25),
            ("loan", -0.25),
            ("credit", "X"),
            ("credit", pd.NA),
            ("checking", 0),
        ],
    )
    def test_validate_apr__expect_fail(self, account_type, apr):
        with pytest.raises(Exception):
            Account._validate_apr(account_type, apr)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_cadence",
        [
            ("credit", "monthly"),
            ("credit", "daily"),
            ("loan", "daily"),
            ("loan", "monthly"),
            ("savings", "daily"),
            ("checking", None),
        ],
    )
    def test_validate_interest_cadence__expect_success(self, account_type, interest_cadence):
        Account._validate_interest_cadence(account_type, interest_cadence)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_cadence",
        [
            ("credit", None),
            ("credit", "weekly"),
            ("loan", None),
            ("loan", "yearly"),
            ("checking", "daily"),
        ],
    )
    def test_validate_interest_cadence__expect_fail(self, account_type, interest_cadence):
        with pytest.raises(Exception):
            Account._validate_interest_cadence(account_type, interest_cadence)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_type",
        [
            ("credit", "compound"),
            ("loan", "simple"),
            ("loan", "compound"),
            ("savings", "simple"),
            ("savings", "compound"),
            ("checking", None),
        ],
    )
    def test_validate_interest_type__expect_success(self, account_type, interest_type):
        Account._validate_interest_type(account_type, interest_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_type",
        [
            ("credit", None),
            ("loan", None),
            ("loan", "shmimple"),
            ("savings", None),
            ("savings", "shmimple"),
            ("checking", "simple"),
        ],
    )
    def test_validate_interest_type__expect_fail(self, account_type, interest_type):
        with pytest.raises(Exception):
            Account._validate_interest_type(account_type, interest_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,billing_state",
        [
            ("checking", checking_billing_state()),
            ("credit", credit_billing_state()),
            ("loan", loan_billing_state()),
            ("savings", savings_billing_state()),
        ],
    )
    def test_validate_billing_state__expect_success(self, account_type, billing_state):
        Account._validate_billing_state(account_type, billing_state)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,billing_state",
        [
            ("checking", None),
            ("checking", credit_billing_state()),
            ("credit", checking_billing_state()),
            ("loan", credit_billing_state()),
            ("savings", loan_billing_state()),
        ],
    )
    def test_validate_billing_state__expect_fail(self, account_type, billing_state):
        with pytest.raises(Exception):
            Account._validate_billing_state(account_type, billing_state)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,primary_checking_ind",
        [
            ("checking", True),
            ("checking", False),
            ("credit", None),
            ("loan", None),
            ("savings", None),
        ],
    )
    def test_validate_primary_checking_ind__expect_success(
        self, account_type, primary_checking_ind
    ):
        Account._validate_primary_checking_ind(account_type, primary_checking_ind)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,primary_checking_ind",
        [
            ("checking", None),
            ("checking", "True"),
            ("credit", False),
            ("loan", False),
            ("savings", False),
        ],
    )
    def test_validate_primary_checking_ind__expect_fail(
        self, account_type, primary_checking_ind
    ):
        with pytest.raises(Exception):
            Account._validate_primary_checking_ind(account_type, primary_checking_ind)

    @pytest.mark.unit
    def test_str(self):
        test_account = Account(
            name="test checking",
            balance=0,
            min_balance=0,
            max_balance=0,
            account_type="checking",
            billing_state=checking_billing_state(balance=0, is_primary=True),
        )

        assert "test checking" in str(test_account)


# Migration notes:
# - Replaced pre-billing-state account-type cases with the current Account API:
#   checking, credit, loan, and savings accounts now receive explicit billing_state objects.
# - Kept validator coverage focused on current private/static validators and conservative
#   equivalents of the old tests where behavior was clear.
# - Recommendation: once the billing-state classes settle, tighten broad exception checks
#   to exact ValueError/TypeError expectations.
