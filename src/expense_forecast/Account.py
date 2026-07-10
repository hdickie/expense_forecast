import datetime
import pandas as pd
import jsonpickle

from .CreditCardBillingState import CreditCardBillingState
from .LoanBillingState import LoanBillingState
from .SavingsBillingState import SavingsBillingState
from .CheckingBillingState import CheckingBillingState

class Account:
    """
    Represents a single financial account.

    An Account models the current state of a single financial instrument,
    asset, or liability. Examples include checking accounts, savings
    accounts, credit cards, loans, investment accounts.

    An Account encapsulates the data and behavior specific to one financial
    entity. Collections of Accounts are managed by AccountSet, which
    represents the complete financial state of a forecast.

    Responsibilities
    ----------------
    - Store the state of a single financial account.
    - Provide account-specific calculations and behaviors.
    - Support serialization and deserialization.
    - Define equality and arithmetic semantics where appropriate.
    - Maintain invariants required by the forecasting engine.

    Invariants
    ----------
    - The account identifier uniquely identifies the account within an
      AccountSet.
    - The account's state is internally consistent.
    - Operations preserve the validity of the account.

    Notes
    -----
    Account represents domain state rather than presentation or persistence.
    It may be serialized to support storage and interchange, but its primary
    purpose is to model a financial account and participate in forecast
    calculations.
    """
    
    @staticmethod
    def _validate_balances(min_balance, balance, max_balance, billing_state):
        """
        Validate that billing_state is consistent with balance, min_balance, 
        max_balance, and that balances bounds are consistent with each other.

        Parameters
        ----------
        min_balance : float

        balance : float

        max_balance : float

        billing_state : object
            One of: CheckingBillingState, CreditCardBillingState, LoanBillingState.

        @interface-report: show
        """
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

        # TODO DEFER validate sync with billing_state

    @staticmethod
    def _validate_account_type(account_type):
        valid_account_types = [
            "checking",
            "credit",
            "savings",
            "loan"
        ]
        assert account_type == account_type.lower()
        if account_type not in valid_account_types:
            raise ValueError(
                f"Invalid account_type: {account_type}. Must be one of {', '.join(valid_account_types)}"
            )

    @staticmethod
    def _validate_apr(account_type, apr):
        
        account_types_that_require_apr = [
            "credit",
            "loan",
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

    @staticmethod
    def _validate_interest_interval(account_type, interest_interval):
        account_types_that_require_interest_interval = [
            "credit",
            "loan",
            "savings",
        ]
        if account_type in account_types_that_require_interest_interval and interest_interval not in ['daily','monthly']:
            raise ValueError(
                f"Account.interest_interval should be daily or monthly for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_interest_interval and interest_interval is not None:
            raise ValueError(
                f"Account.interest_interval should be None for account_type '{account_type}'"
            )

    @staticmethod
    def _validate_interest_type(account_type, interest_type):
        if account_type in ["loan", "credit", "savings"] and interest_type is None:
            raise ValueError(
                f"Account.interest_type is required for account_type '{account_type}'"
            )
        elif account_type in ["loan", "credit", "savings"] and interest_type not in ["simple", "compound"]:
            raise ValueError(
                f"Account.interest_type should be simple or compound for account_type '{account_type}'"
            )
        elif account_type in ["checking"] and interest_type is not None:
            raise ValueError(
                f"Account.interest_type should be None for account_type '{account_type}'"
            )

    @staticmethod
    def _validate_primary_checking_ind(account_type, primary_checking_ind):
        if account_type != 'checking' and primary_checking_ind is not None:
            raise ValueError(
                f"Account.primary_checking_ind should be None for account_type '{account_type}'"
            )
        elif account_type == 'checking' and primary_checking_ind is None:
            raise TypeError(
                f"Account.primary_checking_ind must be a bool Value was: {primary_checking_ind}"
            )
        elif account_type == 'checking' and primary_checking_ind is not None:
            assert isinstance(primary_checking_ind,bool)

    @staticmethod
    def _validate_billing_state(account_type, billing_state):
        if account_type == "credit":
            assert isinstance(billing_state, CreditCardBillingState)
        elif account_type == "loan":
            assert isinstance(billing_state, LoanBillingState)
        elif account_type == "savings":
            assert isinstance(billing_state, SavingsBillingState)
        elif account_type == "checking":
            assert isinstance(billing_state, CheckingBillingState)
        else:
            raise ValueError(
                f"Account.billing_state should not be None"
            )

    @staticmethod
    def _validate_account_name(account_name):
        assert ';' not in account_name
        # TODO DEFER enforce max length

    def __init__(self, 
                 name: str, 
                 balance: float, 
                 min_balance: float, 
                 max_balance: float, 
                 account_type: str, 
                 billing_state: CheckingBillingState | CreditCardBillingState | LoanBillingState):
        # checking, credit, principal balance, interest, investment
        # parameters are expected to be correctly typed. wont cast but will error

        """
        Initialize an Account.

        Create a new Account from its identifying information and current state.
        The constructor establishes the immutable characteristics of the account
        (e.g., identifier, account type, and configuration) together with the
        mutable state required for forecasting.

        Billing-related state is provided through the BillingState abstraction
        rather than individual billing parameters. This ensures there is a single
        authoritative representation of the account's billing status and avoids
        ambiguous construction semantics.

        The constructor performs any validation necessary to establish the class
        invariants. Once successfully constructed, the Account should represent a
        self-consistent financial entity that can participate in forecast
        execution, serialization, comparison, and state transitions.

        Parameters
        ----------
        name : str
            Name of account.

        balance : float
            Balance of account. Credit and Loan types use non-negative numbers.

        min_balance : float
            Minimum legal balance of account. Infinity not allowed.

        max_balance : float
            Maximum legal balance of account. Infinity is allowed.

        account_type : str
            One of: checking, credit, loan. Case-insensitive.

        billing_state: CheckingBillingState | CreditCardBillingState | LoanBillingState 
            A billing state object appropriate for the type of account.

        Returns
        -------
        None

        @interface-report: show
        """

        self.name = name
        self._validate_account_name(self.name) 

        self.balance = balance
        self.min_balance = min_balance
        self.max_balance = max_balance

        self.account_type = account_type
        self._validate_account_type(self.account_type)

        self.billing_state = billing_state
        self._validate_billing_state(self.account_type, self.billing_state)
        self._validate_balances(self.min_balance, self.balance, self.max_balance, self.billing_state)

        self.billing_start_date = getattr(self.billing_state, "billing_cycle_start_date", None)
        self.interest_type = getattr(self.billing_state, "interest_type", None)
        self.apr = getattr(self.billing_state, "apr", None)
        self.interest_interval = getattr(self.billing_state, "interest_interval", None)
        self.minimum_payment = getattr(self.billing_state, "minimum_payment", None)
        self.primary_checking_ind = getattr(self.billing_state, "is_primary", None)


    def to_json(self):
        """
        Returns json string.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)

    def __str__(self):
        """
        Returns human-readable string represensation of Account.

        @interface-report: show
        """
        return pd.DataFrame(
            {
                "Name": [self.name],
                "Balance": [self.balance],
                "Min_Balance": [self.min_balance],
                "Max_Balance": [self.max_balance],
                "Account_Type": [self.account_type],
                "Billing_Start_Date": [self.billing_start_date],
                "Interest_Type": [self.interest_type],
                "APR": [self.apr],
                "Interest_interval": [self.interest_interval],
                "Minimum_Payment": [self.minimum_payment],
                "Primary_Checking_Ind": [self.primary_checking_ind],
            }
        ).to_string()
