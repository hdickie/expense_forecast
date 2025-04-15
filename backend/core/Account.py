import datetime
import pandas as pd
from typing import Optional
from models.accountset.params import AccountParams


import logging
logger = logging.getLogger("core.Account")

class Account:

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

    #obsolete
    # @classmethod
    # def _validate_account_type(cls, account_type: str) -> None:
    #     valid_account_types = [
    #         "checking",
    #         "credit prev stmt bal",
    #         "credit curr stmt bal",
    #         "savings",
    #         "principal balance",
    #         "interest",
    #         "credit billing cycle payment bal",
    #         "loan billing cycle payment bal",
    #         "loan end of prev cycle bal",
    #         "credit end of prev cycle bal",
    #     ]
    #     assert account_type == account_type.lower()
    #     if account_type not in valid_account_types:
    #         raise ValueError(
    #             f"Invalid account_type: {account_type}. Must be one of {', '.join(valid_account_types)}"
    #         )

    #obsolete also named wrong
    # @classmethod
    # def _validate_account_name(cls, account_type: str, account_name: str) -> None:
    #     account_types_that_require_colon_in_name = [
    #         "credit curr stmt bal",
    #         "credit prev stmt bal",
    #         "principal balance",
    #         "credit billing cycle payment bal",
    #         "loan billing cycle payment bal",
    #         "loan prev end of cycle balance",
    #         "credit prev end of cycle balance",
    #     ]
    #     if account_type in account_types_that_require_colon_in_name:
    #         if ":" not in account_name:
    #             raise ValueError(
    #                 "Accounts of these types: [" + ', '.join(
    #                     account_types_that_require_colon_in_name) + "] require colon char in the account name. Got: "+account_name
    #             )

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

    # @classmethod
    # def _validate_interest_cadence(cls, account_type: str, interest_cadence: Optional[str]) -> None:
    
    #     account_types_that_require_interest_cadence = [
    #         "credit prev stmt bal",
    #         "principal balance",
    #         "savings",
    #     ]
    #     if account_type in account_types_that_require_interest_cadence and interest_cadence not in ['daily','monthly']: #todo more strict
    #         raise ValueError(
    #             f"Account.interest_cadence should be daily or monthly for account_type '{account_type}'"
    #         )
    #     elif account_type not in account_types_that_require_interest_cadence and interest_cadence is not None:
    #         raise ValueError(
    #             f"Account.interest_cadence should be None for account_type '{account_type}'"
    #         )

    # @classmethod
    # def _validate_interest_type(cls, account_type: str, interest_type: Optional[str]) -> None:
    
    #     if account_type in ["principal balance", "savings"] and interest_type is None:
    #         raise ValueError(
    #             f"Account.interest_type is required for account_type '{account_type}'"
    #         )
    #     elif account_type in ["principal balance", "savings"] and interest_type not in ["simple", "compound"]:
    #         raise ValueError(
    #             f"Account.interest_type should be simple or compound for account_type '{account_type}'"
    #         )
    #     elif account_type not in ["principal balance", "savings"] and interest_type is not None:
    #         raise ValueError(
    #             f"Account.interest_type should be None for account_type '{account_type}'"
    #         )

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

    # @classmethod
    # def _validate_primary_checking_ind(cls, account_type: str, primary_checking_ind: Optional[bool]) -> None:
    #     if account_type != 'checking' and primary_checking_ind is not None:
    #         raise ValueError(
    #             f"Account.primary_checking_ind should be None for account_type '{account_type}'"
    #         )
    #     elif account_type == 'checking' and primary_checking_ind is None:
    #         raise TypeError(
    #             f"Account.primary_checking_ind must be a bool Value was: {primary_checking_ind}"
    #         )
    #     elif account_type == 'checking' and primary_checking_ind is not None:
    #         assert isinstance(primary_checking_ind,bool)

    # e.g. account = Account.from_params(AccountParams(...))
    @classmethod
    def from_params(cls, params: AccountParams, validate: bool = True) -> "Account":
        return cls(
            name=params.name,
            balance=params.balance,
            min_balance=params.min_balance,
            max_balance=params.max_balance,
            account_type=params.account_type,
            billing_start_date=params.billing_start_date,
            interest_type=params.interest_type,
            apr=params.apr,
            interest_cadence=params.interest_cadence,
            minimum_payment=params.minimum_payment,
            primary_checking_ind=params.primary_checking_ind,
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
            # self._validate_account_name(account_type, self.name)
            self._validate_balances(self.min_balance, self.balance, self.max_balance)
            # self._validate_account_type(self.account_type)
            self._validate_billing_start_date(self.account_type, self.billing_start_date)
            # self._validate_interest_type(self.account_type, self.interest_type)
            self._validate_apr(self.account_type, self.apr)
            # self._validate_interest_cadence(self.account_type, self.interest_cadence)
            self._validate_minimum_payment(self.account_type, self.minimum_payment)
            # self._validate_primary_checking_ind(self.account_type, self.primary_checking_ind)

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

