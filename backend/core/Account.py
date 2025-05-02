import datetime
import pandas as pd
from typing import Optional
from models.account.params import AccountParams
import sys
import hashlib
import logging
logger = logging.getLogger("core.Account")
logger.setLevel(logging.INFO)  # Or DEBUG if you want more noise

# Create console handler
handler = logging.StreamHandler(sys.stdout)  # Important! stdout not stderr
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

# Avoid duplicate handlers if code reloads
if not logger.handlers:
    logger.addHandler(handler)

class Account:

    def get_stable_id(self):
        m = hashlib.sha256()
        m.update(str(self).encode())
        self.stable_id = m.hexdigest()
        return self.stable_id

    @classmethod
    def _validate_balances(cls, min_balance: float, balance: float, max_balance: float) -> None:
        if min_balance > balance:
            raise ValueError(
                f"Account.balance ({balance}) cannot be less than min_balance ({min_balance})"
            )

        if max_balance < balance:
            raise ValueError(
                f"Account.balance ({balance}) cannot be greater than max_balance ({max_balance})"
            )

        if max_balance < min_balance:
            raise ValueError(
                f"Account.max_balance ({max_balance}) cannot be less than min_balance ({min_balance})"
            )

    @classmethod
    def _validate_apr(cls, account_type: str, apr: Optional[float]) -> None:
        account_types_that_require_apr = [
            "credit prev stmt bal",
            "principal balance",
            "savings",
        ]
        if account_type in account_types_that_require_apr and apr is not None:
            assert apr >= 0
        elif account_type in account_types_that_require_apr and apr is None:
            raise ValueError(
                f"Account.apr is required for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_apr and apr is not None:
            raise ValueError(
                f"Account.apr should be None for account_type '{account_type}'"
            )

    @classmethod
    def _validate_billing_start_date(cls, account_type: str, billing_start_date: Optional[datetime.datetime]) -> None:
        account_types_that_require_billing_start_date = [
            "credit billing cycle payment bal",
            "loan billing cycle payment bal",
            "credit prev stmt bal",
            "principal balance",
            "savings",
            "loan end of prev cycle bal",
            "credit end of prev cycle bal",
        ]

        if account_type in account_types_that_require_billing_start_date and billing_start_date is not None:
            assert isinstance(billing_start_date, datetime.datetime)
        elif account_type in account_types_that_require_billing_start_date and billing_start_date is None:
            raise ValueError(
                f"Account.billing_start_date is required for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_billing_start_date and billing_start_date is not None:
            raise ValueError(
                f"Account.billing_start_date should be None for account_type '{account_type}'"
            )

    @classmethod
    def _validate_minimum_payment(cls, account_type: str, minimum_payment: Optional[float]) -> None:
        account_types_that_require_minimum_payment = ["credit prev stmt bal", "principal balance"]
        if account_type in account_types_that_require_minimum_payment and minimum_payment is not None:
            assert minimum_payment >= 0
        elif account_type in account_types_that_require_minimum_payment and minimum_payment is None:
            raise ValueError(
                f"Account.minimum_payment is required for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_minimum_payment and minimum_payment is not None:
            raise ValueError(
                f"Account.minimum_payment should be None for account_type '{account_type}'"
            )

    # e.g. account = Account.from_params(AccountParams(...))
    @classmethod
    def from_params(cls, params: AccountParams, validate: bool = True) -> "Account":
        logger.debug('ENTER/EXIT Account.from_params')
        return cls(
            name=params.name,
            balance=params.balance,
            min_balance=params.min_balance,
            max_balance=params.max_balance,
            account_type=params.account_type,
            billing_start_date=getattr(params, "billing_start_date", None),
            interest_type=getattr(params, "interest_type", None),
            apr=getattr(params, "apr", None),
            interest_cadence=getattr(params, "interest_cadence", None),
            minimum_payment=getattr(params, "minimum_payment", None),
            primary_checking_ind=getattr(params, "primary_checking_ind", False),
            validate=validate
        )

    def __init__(
        self,
        name: str,
        balance: float,
        min_balance: float,
        max_balance: float,
        account_type: str,
        *,
        billing_start_date: Optional[datetime.datetime] = None,
        interest_type: Optional[str] = None,
        apr: Optional[float] = None,
        interest_cadence: Optional[str] = None,
        minimum_payment: Optional[float] = None,
        primary_checking_ind: Optional[bool] = None,
        validate: bool = True
    ) -> None:
        logger.debug('ENTER Account()')

        self.name = name
        self.balance = balance
        self.min_balance = min_balance
        self.max_balance = max_balance
        self.account_type = account_type
        self.billing_start_date = billing_start_date
        self.interest_type = interest_type
        self.apr = apr
        self.interest_cadence = interest_cadence
        self.minimum_payment = minimum_payment
        self.primary_checking_ind = primary_checking_ind

        if validate:
            self._validate_balances(self.min_balance, self.balance, self.max_balance)
            self._validate_billing_start_date(self.account_type, self.billing_start_date)
            self._validate_apr(self.account_type, self.apr)
            self._validate_minimum_payment(self.account_type, self.minimum_payment)

        logger.debug('EXIT Account()')

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "balance": self.balance,
            "min_balance": self.min_balance,
            "max_balance": self.max_balance,
            "account_type": self.account_type,
            "billing_start_date": self.billing_start_date.strftime("%Y-%m-%d") if self.billing_start_date else None,
            "interest_type": self.interest_type,
            "apr": self.apr,
            "interest_cadence": self.interest_cadence,
            "minimum_payment": self.minimum_payment,
            "primary_checking_ind": self.primary_checking_ind,
        }

    ### this could contain None which apparently are not hashable
    def __str__(self) -> str:
        bsd = [ bsd.strftime('%Y%m%d') for bsd in [self.billing_start_date] if self.billing_start_date ]

        return pd.DataFrame(
            {
                "Name": [self.name],
                "Balance": [self.balance],
                "Min_Balance": [self.min_balance],
                "Max_Balance": [self.max_balance],
                "Account_Type": [self.account_type],
                "Billing_Start_Date": [bsd],
                "Interest_Type": [self.interest_type],
                "APR": [self.apr],
                "Interest_Cadence": [self.interest_cadence],
                "Minimum_Payment": [self.minimum_payment],
                "Primary_Checking_Ind": [self.primary_checking_ind],
            }
        ).to_string()

    ### I do like this better but it didn't fix the problem I was trying to solve, so let's return to this later
    # def __str__(self) -> str:
    #     return "|".join([
    #         str(self.name),
    #         str(self.balance),
    #         str(self.min_balance),
    #         str(self.max_balance),
    #         str(self.account_type),
    #         self.billing_start_date.strftime('%Y%m%d') if self.billing_start_date else "",
    #         str(self.interest_type),
    #         str(self.apr),
    #         str(self.interest_cadence),
    #         str(self.minimum_payment),
    #         str(self.primary_checking_ind),
    #     ])

