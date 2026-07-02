import datetime

import pandas as pd
import pytest

from expense_forecast.Account import Account


def dt(date_string):
    return datetime.datetime.strptime(date_string, "%Y%m%d")


class TestAccount:

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "name,balance,min_balance,max_balance,account_type,kwargs",
        [
            (
                "checking",
                0,
                0,
                0,
                "checking",
                {"primary_checking_ind": True},
            ),
            (
                "cc: prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": dt("20000101"),
                    "apr": 0.25,
                    "interest_cadence": "monthly",
                    "minimum_payment": 50,
                },
            ),
            (
                "cc: curr stmt bal",
                0,
                0,
                0,
                "credit curr stmt bal",
                {},
            ),
            (
                "loan: principal balance",
                0,
                0,
                0,
                "principal balance",
                {
                    "billing_start_date": dt("20000101"),
                    "interest_type": "simple",
                    "apr": 0.25,
                    "interest_cadence": "daily",
                    "minimum_payment": 50,
                },
            ),
            (
                "loan: principal balance",
                0,
                0,
                0,
                "principal balance",
                {
                    "billing_start_date": dt("20000101"),
                    "interest_type": "compound",
                    "apr": 0.25,
                    "interest_cadence": "monthly",
                    "minimum_payment": 50,
                },
            ),
            (
                "loan: interest",
                0,
                0,
                0,
                "interest",
                {},
            ),
        ],
    )
    def test_Account_constructor_valid_inputs(
        self, name, balance, min_balance, max_balance, account_type, kwargs
    ):
        account = Account(
            name,
            balance,
            min_balance,
            max_balance,
            account_type,
            **kwargs,
        )

        assert account.name == name
        assert account.balance == balance
        assert account.min_balance == min_balance
        assert account.max_balance == max_balance
        assert account.account_type == account_type

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "name,balance,min_balance,max_balance,account_type,kwargs",
        [
            ("typo- invalid account type", 0, 0, 0, "shmecking", {}),
            ("NoneType- no account type", 0, 0, 0, None, {}),
            ("context warning for account type- used credit type", 0, 0, 0, "credit", {}),
            ("context warning for account type- used loan type", 0, 0, 0, "loan", {}),
            (
                "name missing colon- prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": dt("20000101"),
                    "apr": 0,
                    "interest_cadence": "monthly",
                    "minimum_payment": 0,
                },
            ),
            (
                "name missing colon- principal balance",
                0,
                0,
                0,
                "principal balance",
                {
                    "billing_start_date": dt("20000101"),
                    "interest_type": "simple",
                    "apr": 0,
                    "interest_cadence": "daily",
                    "minimum_payment": 0,
                },
            ),
            ("checking- bal not comparable (None)", None, 0, 0, "checking", {"primary_checking_ind": True}),
            ("checking- bal not comparable (pd.NA)", pd.NA, 0, 0, "checking", {"primary_checking_ind": True}),
            ("checking- bal not comparable (string)", "X", 0, 0, "checking", {"primary_checking_ind": True}),
            ("checking- min bal not comparable (None)", 0, None, 0, "checking", {"primary_checking_ind": True}),
            ("checking- min bal not comparable (pd.NA)", 0, pd.NA, 0, "checking", {"primary_checking_ind": True}),
            ("checking- min bal not comparable (string)", 0, "X", 0, "checking", {"primary_checking_ind": True}),
            ("checking- max bal not comparable (None)", 0, 0, None, "checking", {"primary_checking_ind": True}),
            ("checking- max bal not comparable (pd.NA)", 0, 0, pd.NA, "checking", {"primary_checking_ind": True}),
            ("checking- max bal not comparable (string)", 0, 0, "X", "checking", {"primary_checking_ind": True}),
            ("checking- min gt balance", 0, 10, 20, "checking", {"primary_checking_ind": True}),
            ("checking- balance gt max", 10, 0, 5, "checking", {"primary_checking_ind": True}),
            ("checking- max lt min", 0, -100, -10, "checking", {"primary_checking_ind": True}),
            (
                "checking- billing_start_dt is not None",
                0,
                0,
                0,
                "checking",
                {"billing_start_date": dt("20000101"), "primary_checking_ind": True},
            ),
            (
                "checking- interest_type is not None",
                0,
                0,
                0,
                "checking",
                {"interest_type": "simple", "primary_checking_ind": True},
            ),
            (
                "checking- apr is not None",
                0,
                0,
                0,
                "checking",
                {"apr": 0, "primary_checking_ind": True},
            ),
            (
                "checking- interest_cadence is not None",
                0,
                0,
                0,
                "checking",
                {"interest_cadence": "daily", "primary_checking_ind": True},
            ),
            (
                "checking- min_payment is not None",
                0,
                0,
                0,
                "checking",
                {"minimum_payment": 0, "primary_checking_ind": True},
            ),
            (
                "cc- billing_start_dt not datetime: prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": "1234",
                    "apr": 0.25,
                    "interest_cadence": "monthly",
                    "minimum_payment": 50,
                },
            ),
            (
                "cc- apr missing: prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": dt("20000101"),
                    "interest_cadence": "monthly",
                    "minimum_payment": 50,
                },
            ),
            (
                "cc- apr is negative: prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": dt("20000101"),
                    "apr": -0.25,
                    "interest_cadence": "monthly",
                    "minimum_payment": 50,
                },
            ),
            (
                "cc- interest_cadence invalid: prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": dt("20000101"),
                    "apr": 0.25,
                    "interest_cadence": "weekly",
                    "minimum_payment": 50,
                },
            ),
            (
                "cc- min_payment missing: prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": dt("20000101"),
                    "apr": 0.25,
                    "interest_cadence": "monthly",
                },
            ),
            (
                "cc- min_payment negative: prev stmt bal",
                0,
                0,
                0,
                "credit prev stmt bal",
                {
                    "billing_start_date": dt("20000101"),
                    "apr": 0.25,
                    "interest_cadence": "monthly",
                    "minimum_payment": -50,
                },
            ),
            (
                "loan- interest_type invalid: principal balance",
                0,
                0,
                0,
                "principal balance",
                {
                    "billing_start_date": dt("20000101"),
                    "interest_type": "shmimple",
                    "apr": 0.25,
                    "interest_cadence": "monthly",
                    "minimum_payment": 50,
                },
            ),
            (
                "interest- loan fields should be None",
                0,
                0,
                0,
                "interest",
                {
                    "billing_start_date": dt("20000101"),
                    "interest_type": "compound",
                    "apr": 0.25,
                    "interest_cadence": "monthly",
                    "minimum_payment": 50,
                },
            ),
            ("unexpected kwarg", 0, 0, 0, "checking", {"primary_checking_ind": True, "unknown": True}),
        ],
    )
    def test_Account_constructor_invalid_inputs(
        self, name, balance, min_balance, max_balance, account_type, kwargs
    ):
        with pytest.raises(Exception):
            Account(
                name,
                balance,
                min_balance,
                max_balance,
                account_type,
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
        Account._validate_balances(min_balance, balance, max_balance)

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
            Account._validate_balances(min_balance, balance, max_balance)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type",
        [
            "checking",
            "credit prev stmt bal",
            "credit curr stmt bal",
            "savings",
            "principal balance",
            "interest",
            "credit billing cycle payment bal",
            "loan billing cycle payment bal",
            "loan end of prev cycle bal",
            "credit end of prev cycle bal",
        ],
    )
    def test_validate_account_type__expect_success(self, account_type):
        Account._validate_account_type(account_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type",
        ["Checking", "credit", "loan", "shmecking", None],
    )
    def test_validate_account_type__expect_fail(self, account_type):
        with pytest.raises(Exception):
            Account._validate_account_type(account_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,account_name",
        [
            ("checking", "checking"),
            ("savings", "savings"),
            ("interest", "loan interest"),
            ("credit prev stmt bal", "credit card: prev stmt bal"),
            ("credit curr stmt bal", "credit card: curr stmt bal"),
            ("principal balance", "loan: principal balance"),
        ],
    )
    def test_validate_account_name__expect_success(self, account_type, account_name):
        Account._validate_account_name(account_type, account_name)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,account_name",
        [
            ("credit prev stmt bal", "credit prev stmt bal"),
            ("credit curr stmt bal", "credit curr stmt bal"),
            ("principal balance", "principal balance"),
        ],
    )
    def test_validate_account_name__expect_fail(self, account_type, account_name):
        with pytest.raises(Exception):
            Account._validate_account_name(account_type, account_name)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,apr",
        [
            ("credit prev stmt bal", 0),
            ("credit prev stmt bal", 0.25),
            ("principal balance", 0.25),
            ("savings", 0.01),
            ("checking", None),
            ("credit curr stmt bal", None),
            ("interest", None),
        ],
    )
    def test_validate_apr__expect_success(self, account_type, apr):
        Account._validate_apr(account_type, apr)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,apr",
        [
            ("credit prev stmt bal", None),
            ("principal balance", None),
            ("savings", None),
            ("credit prev stmt bal", -0.25),
            ("principal balance", -0.25),
            ("credit prev stmt bal", "X"),
            ("credit prev stmt bal", pd.NA),
            ("checking", 0),
            ("credit curr stmt bal", 0.25),
            ("interest", 0.25),
        ],
    )
    def test_validate_apr__expect_fail(self, account_type, apr):
        with pytest.raises(Exception):
            Account._validate_apr(account_type, apr)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_cadence",
        [
            ("credit prev stmt bal", "monthly"),
            ("credit prev stmt bal", "daily"),
            ("principal balance", "daily"),
            ("principal balance", "monthly"),
            ("savings", "daily"),
            ("checking", None),
            ("credit curr stmt bal", None),
            ("interest", None),
        ],
    )
    def test_validate_interest_cadence__expect_success(self, account_type, interest_cadence):
        Account._validate_interest_cadence(account_type, interest_cadence)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_cadence",
        [
            ("credit prev stmt bal", None),
            ("credit prev stmt bal", "weekly"),
            ("principal balance", None),
            ("principal balance", "yearly"),
            ("checking", "daily"),
            ("credit curr stmt bal", "monthly"),
            ("interest", "monthly"),
        ],
    )
    def test_validate_interest_cadence__expect_fail(self, account_type, interest_cadence):
        with pytest.raises(Exception):
            Account._validate_interest_cadence(account_type, interest_cadence)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_type",
        [
            ("principal balance", "simple"),
            ("principal balance", "compound"),
            ("savings", "simple"),
            ("savings", "compound"),
            ("checking", None),
            ("credit prev stmt bal", None),
            ("credit curr stmt bal", None),
            ("interest", None),
        ],
    )
    def test_validate_interest_type__expect_success(self, account_type, interest_type):
        Account._validate_interest_type(account_type, interest_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,interest_type",
        [
            ("principal balance", None),
            ("principal balance", "shmimple"),
            ("savings", None),
            ("savings", "shmimple"),
            ("checking", "simple"),
            ("credit prev stmt bal", "compound"),
            ("credit curr stmt bal", "compound"),
            ("interest", "compound"),
        ],
    )
    def test_validate_interest_type__expect_fail(self, account_type, interest_type):
        with pytest.raises(Exception):
            Account._validate_interest_type(account_type, interest_type)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,billing_start_date",
        [
            ("credit prev stmt bal", dt("20000101")),
            ("principal balance", dt("20000101")),
            ("savings", dt("20000101")),
            ("credit billing cycle payment bal", dt("20000101")),
            ("loan billing cycle payment bal", dt("20000101")),
            ("loan end of prev cycle bal", dt("20000101")),
            ("credit end of prev cycle bal", dt("20000101")),
            ("checking", None),
            ("credit curr stmt bal", None),
            ("interest", None),
        ],
    )
    def test_validate_billing_start_date__expect_success(
        self, account_type, billing_start_date
    ):
        Account._validate_billing_start_date(account_type, billing_start_date)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,billing_start_date",
        [
            ("credit prev stmt bal", None),
            ("credit prev stmt bal", "20000101"),
            ("principal balance", None),
            ("principal balance", "20000101"),
            ("savings", None),
            ("checking", dt("20000101")),
            ("credit curr stmt bal", dt("20000101")),
            ("interest", dt("20000101")),
        ],
    )
    def test_validate_billing_start_date__expect_fail(
        self, account_type, billing_start_date
    ):
        with pytest.raises(Exception):
            Account._validate_billing_start_date(account_type, billing_start_date)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,minimum_payment",
        [
            ("credit prev stmt bal", 0),
            ("credit prev stmt bal", 50),
            ("principal balance", 0),
            ("principal balance", 50),
            ("checking", None),
            ("credit curr stmt bal", None),
            ("interest", None),
        ],
    )
    def test_validate_minimum_payment__expect_success(
        self, account_type, minimum_payment
    ):
        Account._validate_minimum_payment(account_type, minimum_payment)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,minimum_payment",
        [
            ("credit prev stmt bal", None),
            ("credit prev stmt bal", -1),
            ("credit prev stmt bal", "X"),
            ("credit prev stmt bal", pd.NA),
            ("principal balance", None),
            ("principal balance", -50),
            ("checking", 0),
            ("credit curr stmt bal", 50),
            ("interest", 50),
        ],
    )
    def test_validate_minimum_payment__expect_fail(
        self, account_type, minimum_payment
    ):
        with pytest.raises(Exception):
            Account._validate_minimum_payment(account_type, minimum_payment)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "account_type,primary_checking_ind",
        [
            ("checking", True),
            ("checking", False),
            ("credit prev stmt bal", None),
            ("credit curr stmt bal", None),
            ("principal balance", None),
            ("interest", None),
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
            ("credit prev stmt bal", False),
            ("credit curr stmt bal", False),
            ("principal balance", False),
            ("interest", False),
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
            primary_checking_ind=True,
        )

        assert "test checking" in str(test_account)


# Migration notes:
# - Migrated coverage from old__test_Account__unit_test.py into the newer test shape:
#   package import, direct Account(...) calls, constructor **kwargs, and active
#   private/static validator tests.
# - Removed placeholder skips once each validator test had concrete success/failure cases.
# - Kept cases conservative: old cases that depended on the former positional constructor
#   were translated only when the current Account API made the equivalent behavior clear.
# - Updated old date-string constructor inputs to datetime objects because the current
#   _validate_billing_start_date API explicitly requires datetime.datetime.
# - Lowercased valid account types because the current _validate_account_type asserts
#   that account_type is already lower-case.
#
# Recommended next changes:
# - Decide whether validators should raise ValueError/TypeError consistently instead of
#   a mix of ValueError, TypeError, and AssertionError; then tighten these tests to the
#   exact exception types.
# - Revisit the "not comparable" cases from the old file after the Account validators
#   either formally support or reject type casting.
# - Consider extracting the valid account fixtures here for reuse by AccountSet tests.
