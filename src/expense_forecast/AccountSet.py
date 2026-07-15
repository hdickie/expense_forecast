from .Account import Account
from .CheckingBillingState import CheckingBillingState
from .CreditCardBillingState import CreditCardBillingState
from .LoanBillingState import LoanBillingState
from .InvestmentBillingState import InvestmentBillingState

from datetime import date, datetime, timedelta
from decimal import Decimal
import math
import pandas as pd
import copy
from expense_forecast.log_methods import setup_logger
from .log_methods import log_in_color
import logging
import numpy as np
from .LineItemSet import LineItemSet  # this could be refactored out, and should be in terms of independent dependencies and clear organization, but it works
import jsonpickle
from .generate_date_sequence import generate_date_sequence

# logger = setup_logger('AccountSet','./log/AccountSet.log',logging.INFO)
logger = logging.getLogger(__name__)

ROUNDING_ERROR_TOLERANCE = 0.0000000001
MONEY_BOUNDARY_TOLERANCE = Decimal("0.005")


class AccountBoundaryError(ValueError):
    pass


class AccountSet:
    """
    Represents the complete financial state of a forecast at a single
    point in simulated time.

    An AccountSet is the primary state object manipulated by the forecast
    engine. It contains every account that participates in a scenario,
    including cash accounts, credit card debt, loan debt and
    (planned for future release) investments.

    Rather than reasoning about individual balances in isolation, most
    forecasting operations transform one AccountSet into another. This
    allows forecast execution to be viewed as a sequence of state
    transitions.

    Responsibilities
    ----------------
    - Store all accounts participating in the forecast.
    - Provide efficient lookup and iteration.
    - Support serialization and deserialization.
    - Define equality and hashing semantics.
    - Support semantic arithmetic where appropriate.
    - Preserve invariants required by the forecast engine.

    Invariants
    ----------
    - Every account identifier is unique.
    - Every contained account is valid.
    - Account ordering has no semantic meaning.
    - Equivalent financial states compare as equal based on balances 
    alone.

    Relationships
    -------------
    AccountSet serves as the shared state exchanged between many major
    components of the system, including ForecastHandler, BudgetSet,
    MemoRuleSet, scenario planning, optimization, milestone execution,
    and reporting.

    Notes
    -----
    This class models domain concepts rather than persistence concerns.
    JSON serialization, database storage, and UI rendering are supported
    by the class but are not its primary purpose. 
    TODO DEFER i think IO / should probably be pulled out into another 
    class
    """

    ROUNDING_ERROR_TOLERANCE = 0.0000000001

    @staticmethod
    def _money(value):
        """
        TODO DEFER one-line description of _money. #Codex-write-doctstring-OK

        @interface-report: ignore
        """
        return Decimal(str(value))

    @staticmethod
    def _dict_value(value):
        """
        TODO DEFER one-line description of _dict_value. #Codex-write-doctstring-OK

        @interface-report: ignore
        """
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    @staticmethod
    def _forecast_value(value):
        """
        TODO DEFER one-line description of _forecast_value. #Codex-write-doctstring-OK

        @interface-report: ignore
        """
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _normalize_billing_start_date(value):
        """
        @interface-report: ignore
        """
        if pd.isnull(value):
            return None
        if isinstance(value, pd.Timestamp):
            return value.date()
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return value

    #TODO DEFER this doesn't seem like it should take a df as input
    @staticmethod
    def _validate_one_and_only_one_primary_checking_account(accounts_df):
        """
        @interface-report: ignore
        """
        checking_accounts_df = accounts_df[accounts_df.Account_Type == "checking"]
        primary_checking_accounts_df = checking_accounts_df[
            checking_accounts_df.Primary_Checking_Ind == True
        ]
        print(checking_accounts_df.to_string())
        if primary_checking_accounts_df.shape[0] != 1:
            raise ValueError("AccountSet must have one and only one primary checking account")

    #TODO DEFER this doesn't seem like it should take a df as input
    @staticmethod
    def _validate_unique_names(accounts_df):
        """
        @interface-report: ignore
        """
        if len(accounts_df.Name) != len(set(accounts_df.Name)):
            # TODO DEFER identify duplicated account name and include it in error message
            raise ValueError("Account names must be unique within AccountSet")

    def __init__(self, accounts_list=None):
        """
        Initialize an AccountSet, optionally accepting a list of Account objects
        to initialize as non-empty.

        Parameters
        ----------
        accounts_list : list[Account] | None

        Returns
        -------
        None

        @interface-report: show
        """

        self.primary_checking_account_name = None

        if accounts_list is None:
            accounts_list = []

        self.accounts = accounts_list

        if not self.accounts:
            return

        accounts_df = self.getAccounts()
        #TODO set primary_checking_account_name when creating AccountSet from a list of accounts
        AccountSet._validate_unique_names(accounts_df)

    def __str__(self):
        """
        TODO DEFER one-line description of __str__. #Codex-write-doctstring-OK

        @interface-report: show
        """
        return self.getAccounts().to_string()

    def createAccount(
        self,
        name,
        balance,
        min_balance,
        max_balance,
        account_type,
            **kwargs
    ):
        """
        Create a new Account and add it to this AccountSet.

        This method centralizes account creation so that AccountSet can enforce 
        account uniqueness. Callers should prefer this method over manually 
        constructing and inserting Account instances, though that is permitted.

        The created Account is validated before being incorporated into the
        AccountSet.

        These are the valid combinations of kwargs:
        checking - primary_checking_ind
        credit - billing_start_date, minimum_payment, 
                previous_statement_balance = 0, 
                current_statement_balance = 0, 
                billing_cycle_payment_balance = 0, 
                end_of_previous_cycle_balance = 0
        loan -  billing_start_date, interest_type, 
                interest_interval, minimum_payment, 
                principal_balance = 0,
                interest_balance = 0, 
                billing_cycle_payment_balance = 0

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

        **kwargs : dict
            Additional keyword arguments.

            billing_start_date : date
                First date of billing cycles and interest accruals.

            interest_type : str
                One of 'simple', 'compound'. Either for loans, credit must be 'compound'.

            apr : Decimal

            interest_interval : str
                One of 'daily', 'monthly'.

            minimum_payment : Decimal

            previous_statement_balance : Decimal
                For credit cards, represents the interest-accruing balance.

            current_statement_balance : Decimal
                For credit cards, represents spend within the current 
                cycle that is not yet accruing interest. Each billing
                cycle, current_statement_balance is rolled into 
                previous_statement_balance.

            principal_balance : Decimal
                For loans, represents the interest-accruing balance.

            interest_balance : Decimal
                For loans, represents the interest, which is paid first
                before payments are applied to the princiapal.
                
            billing_cycle_payment_balance : Decimal
                For accounts with billing cycles, payments made before
                the due date count as advance payment.

            end_of_previous_cycle_balance : Decimal
                For credit cards, if a credit card is paid off, interest
                is still due on previous_statement_balance at the end
                of the payment cycle, which is calculated using this.

            primary_checking_ind : bool
                For checking accounts, indicates if this account is the
                primary liquid account.     

        @interface-report: show
        """

        allowed_kwargs = ['billing_start_date', 'interest_type', 'apr', 'interest_interval', 'minimum_payment',
                          'previous_statement_balance', 'current_statement_balance', 'principal_balance',
                          'interest_balance', 'billing_cycle_payment_balance',
                          'end_of_previous_cycle_balance', 'primary_checking_ind']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        allowed_account_types = ['checking', 'credit', 'loan', 'investment']
        if not account_type in allowed_account_types:
            raise ValueError(f"Unexpected account type: ({account_type})")

        #assert groups are all present
        checking_required_kwargs = ['primary_checking_ind']
        credit_required_kwargs = ['billing_start_date', 'apr', 'interest_interval', 'minimum_payment', 'previous_statement_balance', 'current_statement_balance', 'end_of_previous_cycle_balance']
        loan_required_kwargs = ['billing_start_date', 'apr', 'interest_interval', 'minimum_payment', 'principal_balance',
                          'interest_balance', 'billing_cycle_payment_balance']

        # TODO DEFER implement required kwargs in createAccount for investment case
        investment_required_kwargs = ['billing_start_date', 'apr']


        if min_balance > balance:
            raise ValueError(
                f"min_balance ({min_balance}) must be less than or equal to balance ({balance})."
            )

        if balance > max_balance:
            raise ValueError(
                f"balance ({balance}) must be less than or equal to max_balance ({max_balance})."
            )

        if min_balance > max_balance:
            raise ValueError(
                f"min_balance ({min_balance}) must be less than or equal to max_balance ({max_balance})."
            )

        if account_type == 'checking':
            for checking_required_kwarg in checking_required_kwargs:
                assert checking_required_kwarg in kwargs #primary_checking_ind is missing
            self.createCheckingAccount(name, balance, min_balance, max_balance, kwargs['primary_checking_ind'])
        elif account_type == 'credit':
            missing = [
                kwarg for kwarg in credit_required_kwargs
                if kwarg not in kwargs
            ]

            if missing:
                raise ValueError(f"Missing required kwargs: {', '.join(missing)}")
            if balance != kwargs['current_statement_balance'] + kwargs['previous_statement_balance']:
                raise ValueError(f"balance != ({kwargs['current_statement_balance']}) + ({kwargs['previous_statement_balance']})")
            self.createCreditCardAccount(name,
                                         current_statement_balance=kwargs['current_statement_balance'],
                                         previous_statement_balance=kwargs['previous_statement_balance'],
                                         min_balance=min_balance,
                                         max_balance=max_balance,
                                         billing_start_date=kwargs['billing_start_date'],
                                         apr=kwargs['apr'],
                                         minimum_payment=kwargs['minimum_payment'],
                                         end_of_previous_cycle_balance=kwargs['end_of_previous_cycle_balance'])
        elif account_type == 'loan':
            for loan_required_kwarg in loan_required_kwargs:
                if not loan_required_kwarg in kwargs:
                    raise ValueError("Missing kwarg creating loan account:{loan_required_kwarg}")

            if balance != kwargs['principal_balance'] + kwargs['interest_balance']:
                raise ValueError(f"balance != ({kwargs['principal_balance']}) + ({kwargs['interest_balance']})")
            self.createLoanAccount(name,
                                   principal_balance=kwargs['principal_balance'],
                                   interest_balance=kwargs['interest_balance'],
                                   min_balance=min_balance,
                                   max_balance=max_balance,
                                   billing_start_date=kwargs['billing_start_date'],
                                   apr=kwargs['apr'],
                                   minimum_payment=kwargs['minimum_payment'],
                                   billing_cycle_payment_balance=kwargs['billing_cycle_payment_balance'])
        elif account_type == 'investment':
            missing = [
                kwarg for kwarg in investment_required_kwargs
                if kwarg not in kwargs
            ]
            if missing:
                raise ValueError(f"Missing required kwargs: {', '.join(missing)}")
            self.createInvestmentAccount(name,
                                         balance=balance,
                                         billing_start_date=kwargs['billing_start_date'],
                                         apr=kwargs['apr'])

        accounts_df = self.getAccounts()
        # loan_account_rows_df = accounts_df[
        #     accounts_df.Account_Type.isin(
        #         [
        #             "principal balance",
        #             "interest",
        #             "loan billing cycle payment bal",
        #         ]
        #     )
        # ]
        # credit_account_rows_df = accounts_df[
        #     accounts_df.Account_Type.isin(
        #         [
        #             "credit prev stmt bal",
        #             "credit curr stmt bal",
        #             "credit billing cycle payment bal",
        #             "credit end of prev cycle bal",
        #         ]
        #     )
        # ]

        AccountSet._validate_unique_names(accounts_df)

    def createCheckingAccount(self, name, balance, min_balance, max_balance, primary_checking_ind):
        """
        @interface-report: ignore
        """
        billing_state = CheckingBillingState(
            balance=balance,
            is_primary=primary_checking_ind,
        )

        account = Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="checking",
            billing_state=billing_state,
        )
        self.accounts.append(account)

        if primary_checking_ind:
            accounts_df = self.getAccounts()
            AccountSet._validate_one_and_only_one_primary_checking_account(accounts_df)
            self.primary_checking_account_name = name


    def createLoanAccount(self, name, principal_balance, interest_balance, min_balance, max_balance, billing_start_date,
                          apr, minimum_payment, billing_cycle_payment_balance=0,):
        """
        @interface-report: show
        """

        principal_balance = self._money(principal_balance)
        interest_balance = self._money(interest_balance)
        minimum_payment = self._money(minimum_payment)
        apr = self._money(apr)
        billing_cycle_payment_balance = self._money(billing_cycle_payment_balance)
        assert billing_cycle_payment_balance >= 0

        balance = principal_balance + interest_balance
        billing_state = LoanBillingState(
            billing_cycle_start_date=billing_start_date,
            principal_balance=principal_balance,
            interest_balance=interest_balance,
            billing_cycle_payment_balance=billing_cycle_payment_balance,
            minimum_payment=minimum_payment,
            interest_type="simple",
            interest_interval="daily",
            apr=apr,
        )

        account = Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="loan",
            billing_state=billing_state,
        )
        self.accounts.append(account)

    def createCreditCardAccount(self, name, current_statement_balance, previous_statement_balance, min_balance, max_balance,
                                billing_start_date, apr, minimum_payment, end_of_previous_cycle_balance):
        """
        @interface-report: show
        """

        billing_cycle_payment_balance = end_of_previous_cycle_balance - previous_statement_balance
        assert billing_cycle_payment_balance >= 0

        balance = current_statement_balance + previous_statement_balance
        billing_state = CreditCardBillingState(
            billing_cycle_start_date=billing_start_date,
            previous_statement_balance=previous_statement_balance,
            current_statement_balance=current_statement_balance,
            billing_cycle_payment_balance=billing_cycle_payment_balance,
            minimum_payment=minimum_payment,
            interest_type="compound",
            interest_interval="monthly",
            apr=apr,
            end_of_previous_cycle_balance=end_of_previous_cycle_balance,
        )

        account = Account(
            name=name,
            balance=balance,
            min_balance=min_balance,
            max_balance=max_balance,
            account_type="credit",
            billing_state=billing_state,
        )
        self.accounts.append(account)

    def createInvestmentAccount(self, name, balance, billing_start_date, apr):

        billing_state = InvestmentBillingState(
            balance = balance,
            billing_start_date = billing_start_date,
            expected_apr = apr
        )

        account = Account(
            min_balance=0,
            max_balance=float('Inf'),
            name=name,
            balance=balance,
            account_type="investment",
            billing_state=billing_state
        )
        self.accounts.append(account)


    #Codex-write-doctstring-OK
    def getBalances(self):
        """
        @interface-report: show
        """
        balances_dict = {account.name: account.balance for account in self.accounts}
        return balances_dict

    #Codex-write-doctstring-OK
    def _get_account_by_name(self, account_name):
        """
        @interface-report: ignore
        """
        if str(account_name).startswith("CHECKING_ABOVE:"):
            return self._get_account_by_name(self.primary_checking_account_name)
        if str(account_name).startswith("CURRENT_STATEMENT_BALANCE:"):
            return self._get_account_by_name(str(account_name).split(":", 1)[1])
        if account_name in [None, "", "None"] or str(account_name).startswith("ALL_"):
            return None

        matching_accounts = [
            account for account in self.accounts if account.name == account_name
        ]
        if len(matching_accounts) != 1:
            raise ValueError(
                f"Expected exactly one account named '{account_name}', found {len(matching_accounts)}"
            )
        return matching_accounts[0]

    #Codex-write-doctstring-OK
    @staticmethod
    def _validate_account_balance_bounds(account, proposed_balance, role):
        """
        @interface-report: show
        """
        proposed_balance_decimal = Decimal(str(proposed_balance))
        min_balance_decimal = Decimal(str(account.min_balance))
        max_balance_is_infinite = math.isinf(float(account.max_balance))
        max_balance_decimal = (
            None
            if max_balance_is_infinite
            else Decimal(str(account.max_balance))
        )

        if proposed_balance_decimal < min_balance_decimal:
            if min_balance_decimal - proposed_balance_decimal <= MONEY_BOUNDARY_TOLERANCE:
                return (
                    min_balance_decimal
                    if isinstance(proposed_balance, Decimal)
                    else float(min_balance_decimal)
                )
            error = AccountBoundaryError(
                f"transaction violated {role} boundaries:\n"
                f"{role}:\n{account}\n"
                f"Proposed balance: {proposed_balance}"
            )
            error.boundary_shortfall = min_balance_decimal - proposed_balance_decimal
            error.account_name = account.name
            error.role = role
            raise error
        if (
            max_balance_decimal is not None
            and proposed_balance_decimal > max_balance_decimal
        ):
            if proposed_balance_decimal - max_balance_decimal <= MONEY_BOUNDARY_TOLERANCE:
                return (
                    max_balance_decimal
                    if isinstance(proposed_balance, Decimal)
                    else float(max_balance_decimal)
                )
            error = AccountBoundaryError(
                f"transaction violated {role} boundaries:\n"
                f"{role}:\n{account}\n"
                f"Proposed balance: {proposed_balance}"
            )
            error.boundary_shortfall = proposed_balance_decimal - max_balance_decimal
            error.account_name = account.name
            error.role = role
            raise error

        return proposed_balance

    #Codex-write-doctstring-OK
    @staticmethod
    def _sync_debt_account_from_billing_state(account):
        """
        @interface-report: show
        """
        if account.account_type not in ["credit", "loan"]:
            return

        if account.account_type == "credit":
            account.balance = (
                account.billing_state.previous_statement_balance
                + account.billing_state.current_statement_balance
            )
        elif account.account_type == "loan":
            account.balance = account.billing_state.balance

    #Codex-write-doctstring-OK
    @staticmethod
    def _increase_debt_balance(account, amount):
        """
        @interface-report: show
        """
        amount = AccountSet._money(amount)
        if account.account_type == "credit":
            account.billing_state.current_statement_balance += amount
        elif account.account_type == "loan":
            account.billing_state.principal_balance += amount
        else:
            raise ValueError(f"Account '{account.name}' is not a debt account")
        AccountSet._sync_debt_account_from_billing_state(account)

    #Codex-write-doctstring-OK
    @staticmethod
    def _decrease_credit_balance(account, amount, minimum_payment_flag):
        """
        @interface-report: show
        """
        amount = AccountSet._money(amount)
        payment_remaining = amount
        previous_statement_payment = min(
            payment_remaining,
            account.billing_state.previous_statement_balance,
        )
        account.billing_state.previous_statement_balance -= previous_statement_payment
        payment_remaining -= previous_statement_payment

        current_statement_payment = min(
            payment_remaining,
            account.billing_state.current_statement_balance,
        )
        account.billing_state.current_statement_balance -= current_statement_payment
        payment_remaining -= current_statement_payment

        if payment_remaining > MONEY_BOUNDARY_TOLERANCE:
            error = AccountBoundaryError(
                f"Payment amount {amount} exceeds credit balance for '{account.name}'"
            )
            error.boundary_shortfall = payment_remaining
            error.account_name = account.name
            error.role = "account_to"
            raise error
        payment_remaining = Decimal("0")

        if not minimum_payment_flag:
            account.billing_state.billing_cycle_payment_balance += amount
        AccountSet._sync_debt_account_from_billing_state(account)

    #Codex-write-doctstring-OK
    @staticmethod
    def _decrease_loan_balance(account, amount, minimum_payment_flag):
        """
        @interface-report: show
        """
        amount = AccountSet._money(amount)
        starting_balance = account.billing_state.balance
        interest_payment, principal_payment = account.billing_state.apply_payment(amount)
        payment_remaining = amount - interest_payment - principal_payment

        if payment_remaining > MONEY_BOUNDARY_TOLERANCE:
            error = AccountBoundaryError(
                f"Payment amount {amount} exceeds loan balance for '{account.name}'"
            )
            error.boundary_shortfall = payment_remaining
            error.account_name = account.name
            error.role = "account_to"
            raise error
        payment_remaining = Decimal("0")

        if not minimum_payment_flag:
            account.billing_state.billing_cycle_payment_balance += amount
        if account.billing_state.balance <= MONEY_BOUNDARY_TOLERANCE:
            account.billing_state.principal_balance = Decimal("0")
            account.billing_state.interest_balance = Decimal("0")
            account.billing_state.billing_cycle_payment_balance = Decimal("0")
        AccountSet._sync_debt_account_from_billing_state(account)
        assert (
            abs(starting_balance - account.billing_state.balance - amount)
            <= MONEY_BOUNDARY_TOLERANCE
        )

    #Codex-write-doctstring-OK
    @staticmethod
    def is_billing_date(account, current_date):
        """
        @interface-report: show
        """
        billing_start_date = account.billing_state.billing_cycle_start_date
        if isinstance(current_date, datetime):
            current_date = current_date.date()
        if isinstance(billing_start_date, datetime):
            billing_start_date = billing_start_date.date()

        num_days = (current_date - billing_start_date).days
        if num_days < 0:
            return False
        billing_days = set(
            generate_date_sequence(
                start_date=billing_start_date,
                num_days=num_days,
                interval="monthly",
            )
        )
        billing_days.add(billing_start_date)
        return current_date in billing_days

    #TODO manual review of AccountSet.processCreditCardBillingDay docstring
    def processCreditCardBillingDay(self, current_date):
        """
        TODO one-line description of processCreditCardBillingDay.

        TODO multi-line description of processCreditCardBillingDay.
        TODO explain how AccountSet.processCreditCardBillingDay participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        current_date : date
            TODO one-line description of processCreditCardBillingDay.current_date.

        Returns
        -------
        list[str]
            TODO one-line description of return value of processCreditCardBillingDay.

        Contract
        --------
        - #TODO contract lines for processCreditCardBillingDay.
        - #TODO document exceptions, mutations, and precision assumptions for processCreditCardBillingDay.

        @interface-report: show
        """
        interest_directives = []

        for account in self.accounts:
            if account.account_type != "credit":
                continue
            if not self.is_billing_date(account, current_date):
                continue

            previous_statement_name = f"{account.name}: Prev Stmt Bal"
            interest_accrued = account.billing_state.interest_accrued_this_cycle()
            if interest_accrued > 0:
                interest_directives.append(
                    f"CC INTEREST ({previous_statement_name} +${interest_accrued})"
                )

            account.billing_state = account.billing_state.roll_cycle(current_date)
            account.billing_start_date = account.billing_state.billing_cycle_start_date
            account.minimum_payment = account.billing_state.minimum_payment
            self._sync_debt_account_from_billing_state(account)

        return interest_directives

    #Codex-write-doctstring-OK
    def updateCreditCardEndOfPreviousCycleBalances(self, current_date):
        """
        @interface-report: show
        """
        for account in self.accounts:
            if account.account_type != "credit":
                continue

            billing_start_date = account.billing_state.billing_cycle_start_date
            if isinstance(current_date, datetime):
                current_date = current_date.date()
            if isinstance(billing_start_date, datetime):
                billing_start_date = billing_start_date.date()

            if current_date == billing_start_date + timedelta(days=1):
                account.billing_state.end_of_previous_cycle_balance = (
                    account.billing_state.previous_statement_balance
                    + account.billing_state.billing_cycle_payment_balance
                )

    #TODO manual review of AccountSet.getForecastColumnsForAccount docstring
    @staticmethod
    def getForecastColumnsForAccount(account):
        """
        TODO one-line description of getForecastColumnsForAccount.

        TODO multi-line description of getForecastColumnsForAccount.
        TODO explain how AccountSet.getForecastColumnsForAccount participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of getForecastColumnsForAccount.account.

        Returns
        -------
        dict
            TODO one-line description of return value of getForecastColumnsForAccount.

        Contract
        --------
        - #TODO contract lines for getForecastColumnsForAccount.
        - #TODO document exceptions, mutations, and precision assumptions for getForecastColumnsForAccount.

        @interface-report: show
        """
        columns = {account.name: AccountSet._forecast_value(account.balance)}
        billing_state = getattr(account, "billing_state", None)
        if billing_state is None:
            return columns

        if account.account_type == "credit":
            columns[f"{account.name}: Curr Stmt Bal"] = AccountSet._forecast_value(
                billing_state.current_statement_balance
            )
            columns[f"{account.name}: Prev Stmt Bal"] = AccountSet._forecast_value(
                billing_state.previous_statement_balance
            )
            columns[
                f"{account.name}: Credit Billing Cycle Payment Bal"
            ] = AccountSet._forecast_value(billing_state.billing_cycle_payment_balance)
            columns[
                f"{account.name}: Credit End of Prev Cycle Bal"
            ] = AccountSet._forecast_value(billing_state.end_of_previous_cycle_balance)
        elif account.account_type == "loan":
            columns[f"{account.name}: Principal Balance"] = AccountSet._forecast_value(
                billing_state.principal_balance
            )
            columns[f"{account.name}: Interest"] = AccountSet._forecast_value(
                billing_state.interest_balance
            )
            columns[
                f"{account.name}: Loan Billing Cycle Payment Bal"
            ] = AccountSet._forecast_value(billing_state.billing_cycle_payment_balance)

        return columns

    #Codex-write-doctstring-OK
    def getForecastAccountBalances(self, include_debug_columns=False):
        """
        @interface-report: show
        """
        balances = {}
        for account in self.accounts:
            balances[account.name] = self._forecast_value(account.balance)
            if include_debug_columns:
                balances.update(self.getForecastColumnsForAccount(account))
        return balances

    #Codex-write-doctstring-OK
    @staticmethod
    def _decrease_debt_balance(account, amount, minimum_payment_flag):
        """
        @interface-report: show
        """
        if account.account_type == "credit":
            AccountSet._decrease_credit_balance(account, amount, minimum_payment_flag)
        elif account.account_type == "loan":
            AccountSet._decrease_loan_balance(account, amount, minimum_payment_flag)
        else:
            raise ValueError(f"Account '{account.name}' is not a debt account")

    #TODO manual review of AccountSet.executeTransaction docstring
    def executeTransaction(
        self,
        Account_From,
        Account_To,
        Amount,
        income_flag=False,
        minimum_payment_flag=False,
        allocation_strategy="avalanche",
    ):
        """
        TODO one-line description of executeTransaction.

        TODO multi-line description of executeTransaction.
        TODO explain how AccountSet.executeTransaction participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        Account_From : str | None
            TODO one-line description of executeTransaction.Account_From.

        Account_To : str | None
            TODO one-line description of executeTransaction.Account_To.

        Amount : float
            TODO one-line description of executeTransaction.Amount.

        income_flag : bool
            TODO one-line description of executeTransaction.income_flag.

        minimum_payment_flag : bool
            TODO one-line description of executeTransaction.minimum_payment_flag.

        Returns
        -------
        None
            TODO one-line description of return value of executeTransaction.

        Contract
        --------
        - #TODO contract lines for executeTransaction.
        - #TODO document exceptions, mutations, and precision assumptions for executeTransaction.

        @interface-report: show
        """
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER executeTransaction("
            + str(Account_From)
            + ","
            + str(Account_To)
            + ","
            + str(Amount)
            + ", minimum_payment_flag="
            + str(minimum_payment_flag)
            + ")",
        )
        if Amount == 0:
            log_in_color(
                logger,
                "white",
                "debug",
                "EXIT executeTransaction("
                + str(Account_From)
                + ","
                + str(Account_To)
                + ","
                + str(Amount)
                + ")",
            )
            return

        if str(Account_From).startswith("CHECKING_ABOVE:"):
            threshold = self._money(str(Account_From).split(":", 1)[1])
            checking = self._get_account_by_name(self.primary_checking_account_name)
            Amount = min(
                self._money(abs(Amount)),
                max(Decimal("0"), self._money(checking.balance) - threshold),
            )
            Account_From = checking.name
            if Amount <= MONEY_BOUNDARY_TOLERANCE:
                return Decimal("0")

        if str(Account_To).startswith("CURRENT_STATEMENT_BALANCE:"):
            card_name = str(Account_To).split(":", 1)[1]
            card = self._get_account_by_name(card_name)
            if card is None or card.account_type != "credit":
                raise ValueError(
                    f"Current-statement payment requires credit card {card_name!r}"
                )
            checking = self._get_account_by_name(Account_From)
            available_cash = (
                self._money(checking.balance) - self._money(checking.min_balance)
                if checking is not None and checking.account_type == "checking"
                else self._money(abs(Amount))
            )
            Amount = min(
                self._money(abs(Amount)),
                self._money(card.billing_state.current_statement_balance),
                max(Decimal("0"), available_cash),
            )
            Account_To = card_name
            if Amount <= MONEY_BOUNDARY_TOLERANCE:
                return Decimal("0")

        if Account_To in {"ALL_LOANS", "ALL_LOANS_SNOWBALL"}:
            if Account_To.endswith("SNOWBALL"):
                allocation_strategy = "snowball"
            allocated_payments = self.allocate_additional_loan_payments(
                Amount, account_from=Account_From, strategy=allocation_strategy
            )
            for single_account_loan_payment in allocated_payments:
                self.executeTransaction(
                    single_account_loan_payment[0],
                    single_account_loan_payment[1],
                    single_account_loan_payment[2],
                    income_flag=False,
                )
            return sum(
                (self._money(payment[2]) for payment in allocated_payments),
                Decimal("0"),
            )

        if Account_To in {"ALL_CREDIT_CARDS", "ALL_CREDIT_CARDS_SNOWBALL"}:
            if Account_To.endswith("SNOWBALL"):
                allocation_strategy = "snowball"
            allocated_payments = self.allocate_additional_credit_card_payments(
                Amount, account_from=Account_From, strategy=allocation_strategy
            )
            for source, destination, payment_amount in allocated_payments:
                self.executeTransaction(source, destination, payment_amount)
            return sum(
                (self._money(payment[2]) for payment in allocated_payments),
                Decimal("0"),
            )

        amount = abs(Amount)
        account_from = self._get_account_by_name(Account_From)
        account_to = self._get_account_by_name(Account_To)

        if account_from is None and account_to is None:
            raise ValueError("At least one side of a transaction must be an account")

        if income_flag and (
            account_from is not None
            or account_to is None
            or account_to.account_type != "checking"
        ):
            raise ValueError(
                "income_flag was True but did not refer to a checking account or "
                f"referred to multiple accounts (from={Account_From!r}, "
                f"to={Account_To!r}, to_type={getattr(account_to, 'account_type', None)!r})"
            )

        if account_from is not None:
            if account_from.account_type in ["checking", "investment"]:
                proposed_balance = self._money(account_from.balance) - self._money(
                    amount
                )
                proposed_balance = self._validate_account_balance_bounds(
                    account_from, proposed_balance, "Account_From"
                )
                account_from.balance = proposed_balance
                account_from.billing_state.balance = proposed_balance
            elif account_from.account_type in ["credit", "loan"]:
                proposed_balance = (
                    self._money(account_from.balance) + self._money(amount)
                )
                proposed_balance = self._validate_account_balance_bounds(
                    account_from, proposed_balance, "Account_From"
                )
                self._increase_debt_balance(account_from, amount)
            else:
                raise NotImplementedError(
                    "account type was: " + str(account_from.account_type)
                )

        if account_to is not None:
            if account_to.account_type in ["checking", "investment"]:
                proposed_balance = self._money(account_to.balance) + self._money(
                    amount
                )
                proposed_balance = self._validate_account_balance_bounds(
                    account_to, proposed_balance, "Account_To"
                )
                account_to.balance = proposed_balance
                account_to.billing_state.balance = proposed_balance
            elif account_to.account_type in ["credit", "loan"]:
                proposed_balance = (
                    self._money(account_to.balance) - self._money(amount)
                )
                proposed_balance = self._validate_account_balance_bounds(
                    account_to, proposed_balance, "Account_To"
                )
                self._decrease_debt_balance(account_to, amount, minimum_payment_flag)
            else:
                raise NotImplementedError(
                    "account type was: " + str(account_to.account_type)
                )

        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT executeTransaction("
            + str(Account_From)
            + ","
            + str(Account_To)
            + ","
            + str(Amount)
            + ")",
        )
        return self._money(amount)

    #Codex-write-doctstring-OK
    def _allocate_additional_debt_payments(
        self, amount, debt_type, account_from=None, strategy="avalanche"
    ):
        if strategy not in {"avalanche", "snowball"}:
            raise ValueError("strategy must be 'avalanche' or 'snowball'")
        amount = self._money(abs(amount))
        if amount == 0:
            return []
        checking_name = account_from or self.primary_checking_account_name
        checking = self._get_account_by_name(checking_name)
        if checking is None or checking.account_type != "checking":
            raise ValueError("aggregate debt payments require a checking source account")
        amount = min(
            amount,
            self._money(checking.balance) - self._money(checking.min_balance),
        )
        def outstanding_balance(account):
            # Preserve the loan allocator's billing-state semantics. Credit
            # cards split debt across current/previous-cycle fields and have no
            # billing_state.balance, so their synchronized Account.balance is
            # the corresponding aggregate.
            if account.account_type == "loan":
                return self._money(account.billing_state.balance)
            return self._money(account.balance)

        debts = [
            account for account in self.accounts
            if account.account_type == debt_type
            and outstanding_balance(account) > MONEY_BOUNDARY_TOLERANCE
        ]
        declaration_order = {id(account): index for index, account in enumerate(self.accounts)}
        if strategy == "avalanche":
            debts.sort(key=lambda account: (-account.apr, declaration_order[id(account)]))
        else:
            debts.sort(
                key=lambda account: (
                    outstanding_balance(account),
                    declaration_order[id(account)],
                )
            )
        payments = []
        for debt in debts:
            if amount <= MONEY_BOUNDARY_TOLERANCE:
                break
            payment = min(amount, outstanding_balance(debt))
            if payment > MONEY_BOUNDARY_TOLERANCE:
                payments.append([checking_name, debt.name, payment])
                amount -= payment
        return payments

    def allocate_additional_loan_payments(
        self, amount, account_from=None, strategy="avalanche"
    ):
        """
        @interface-report: show
        """
        return self._allocate_additional_debt_payments(
            amount, "loan", account_from, strategy
        )

    def allocate_additional_credit_card_payments(
        self, amount, account_from=None, strategy="avalanche"
    ):
        return self._allocate_additional_debt_payments(
            amount, "credit", account_from, strategy
        )

    #TODO manual review of AccountSet.getAccounts docstring
    def getAccounts(self):
        """
        TODO one-line description of getAccounts.

        TODO multi-line description of getAccounts.
        TODO explain how AccountSet.getAccounts participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        None
            TODO confirm that getAccounts takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of getAccounts.

        Contract
        --------
        - #TODO contract lines for getAccounts.
        - #TODO document exceptions, mutations, and precision assumptions for getAccounts.

        @interface-report: show
        """
        columns = [
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
        account_rows = []
        for account in self.accounts:
            account_rows.append(
                {
                    "Name": account.name,
                    "Balance": account.balance,
                    "Min_Balance": account.min_balance,
                    "Max_Balance": account.max_balance,
                    "Account_Type": account.account_type,
                    "Billing_Start_Date": self._normalize_billing_start_date(
                        account.billing_start_date
                    ),
                    "Interest_Type": account.interest_type,
                    "APR": account.apr,
                    "Interest_interval": account.interest_interval,
                    "Minimum_Payment": account.minimum_payment,
                    "Primary_Checking_Ind": account.primary_checking_ind,
                }
            )

        return pd.DataFrame(account_rows, columns=columns)

    def to_dict(self):
        """
        @interface-report: show
        """
        account_rows = []
        for account in self.accounts:
            account_row = {
                    "Name": account.name,
                    "Balance": self._dict_value(account.balance),
                    "Min_Balance": self._dict_value(account.min_balance),
                    "Max_Balance": self._dict_value(account.max_balance),
                    "Account_Type": account.account_type,
                    "Billing_Start_Date": self._dict_value(
                        self._normalize_billing_start_date(account.billing_start_date)
                    ),
                    "Interest_Type": account.interest_type,
                    "APR": self._dict_value(account.apr),
                    "Interest_interval": account.interest_interval,
                    "Minimum_Payment": self._dict_value(account.minimum_payment),
                    "Primary_Checking_Ind": account.primary_checking_ind,
            }

            billing_state = account.billing_state
            if account.account_type == "credit":
                account_row.update(
                    {
                        "Current_Statement_Balance": self._dict_value(
                            billing_state.current_statement_balance
                        ),
                        "Previous_Statement_Balance": self._dict_value(
                            billing_state.previous_statement_balance
                        ),
                        "Billing_Cycle_Payment_Balance": self._dict_value(
                            billing_state.billing_cycle_payment_balance
                        ),
                        "End_Of_Previous_Cycle_Balance": self._dict_value(
                            billing_state.end_of_previous_cycle_balance
                        ),
                        "Minimum_Payment_Floor": self._dict_value(
                            billing_state.minimum_payment_floor
                        ),
                        "Minimum_Payment_Credit_Balance": self._dict_value(
                            billing_state.minimum_payment_credit_balance
                        ),
                    }
                )
            elif account.account_type == "loan":
                account_row.update(
                    {
                        "Principal_Balance": self._dict_value(
                            billing_state.principal_balance
                        ),
                        "Interest_Balance": self._dict_value(
                            billing_state.interest_balance
                        ),
                        "Billing_Cycle_Payment_Balance": self._dict_value(
                            billing_state.billing_cycle_payment_balance
                        ),
                    }
                )

            account_rows.append(account_row)

        return {"accounts": account_rows}

    def to_json(self):
        """
        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)
