from .Account import Account
from .CheckingBillingState import CheckingBillingState
from .CreditCardBillingState import CreditCardBillingState
from .LoanBillingState import LoanBillingState
from datetime import date, datetime, timedelta
from decimal import Decimal
import math
import pandas as pd
import copy
from expense_forecast.log_methods import setup_logger
from .log_methods import log_in_color
import logging
import numpy as np
from .LineItemSet import BudgetSet  # this could be refactored out, and should be in terms of independent dependencies and clear organization, but it works
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

    @staticmethod
    def _money(value):
        """
        TODO one-line description of _money. #Codex-write-doctstring-OK

        @interface-report: ignore
        """
        return Decimal(str(value))

    @staticmethod
    def _dict_value(value):
        """
        TODO one-line description of _dict_value. #Codex-write-doctstring-OK

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
        TODO one-line description of _forecast_value. #Codex-write-doctstring-OK

        @interface-report: ignore
        """
        if isinstance(value, Decimal):
            return float(value)
        return value


    ROUNDING_ERROR_TOLERANCE = 0.0000000001

    @staticmethod
    def _normalize_billing_start_date(value):
        """
        TODO one-line description of _normalize_billing_start_date. #Codex-write-doctstring-OK

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

    #TODO manual review of AccountSet.determineMinPaymentAmount docstring
    @staticmethod
    def determineMinPaymentAmount(
            advance_payment_amount,
            interest_accrued_this_cycle,
            principal_due_this_cycle,
            total_balance,
            min_payment,
    ):
        """
        TODO one-line description of determineMinPaymentAmount.

        TODO multi-line description of determineMinPaymentAmount.
        TODO explain how AccountSet.determineMinPaymentAmount participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        advance_payment_amount : float
            TODO one-line description of determineMinPaymentAmount.advance_payment_amount.

        interest_accrued_this_cycle : float
            TODO one-line description of determineMinPaymentAmount.interest_accrued_this_cycle.

        principal_due_this_cycle : float
            TODO one-line description of determineMinPaymentAmount.principal_due_this_cycle.

        total_balance : float
            TODO one-line description of determineMinPaymentAmount.total_balance.

        min_payment : float
            TODO one-line description of determineMinPaymentAmount.min_payment.

        Returns
        -------
        float
            TODO one-line description of return value of determineMinPaymentAmount.

        Contract
        --------
        - #TODO contract lines for determineMinPaymentAmount.
        - #TODO document exceptions, mutations, and precision assumptions for determineMinPaymentAmount.

        @interface-report: show
        """
        # log_in_color(logger, 'white', 'debug', 'ENTER determineMinPaymentAmount', self.log_stack_depth)
        # self.log_stack_depth += 1
        # print(f"determineMinPaymentAmount({advance_payment_amount}, {interest_accrued_this_cycle}, {principal_due_this_cycle}, {total_balance}, {min_payment})")

        Advance = advance_payment_amount
        Interest = interest_accrued_this_cycle
        Principal = principal_due_this_cycle
        Total = total_balance
        Minimum = min_payment

        amount_due = 0 #setting this 0 instead of None to make type checker happy

        if Advance > Total:
            Advance = Total

        M_prime = max(0, Minimum - Advance)
        P_prime = max(0, Principal - Advance)
        T_prime = Total - Advance

        Sum_1 = P_prime + Interest

        if Interest + Principal == 0:
            return 0

        if Sum_1 >= M_prime:
            return Sum_1

        if Sum_1 < M_prime and Total >= M_prime:
            return M_prime

        if Sum_1 < M_prime and T_prime < M_prime:
            return T_prime

        # print('FINAL ANSWER: '+str(amount_due))
        return amount_due

    ### I think this never got used
    # def isSufficientToBeginForecast(self):
    #     accounts_df = self.getAccounts()
    #     AccountSet._validate_one_and_only_one_primary_checking_account(accounts_df)

    #TODO manual review of AccountSet._validate_one_and_only_one_primary_checking_account docstring
    @staticmethod
    def _validate_one_and_only_one_primary_checking_account(accounts_df):
        """
        TODO one-line description of _validate_one_and_only_one_primary_checking_account.

        TODO multi-line description of _validate_one_and_only_one_primary_checking_account.
        TODO explain how AccountSet._validate_one_and_only_one_primary_checking_account participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        accounts_df : pd.DataFrame
            TODO one-line description of _validate_one_and_only_one_primary_checking_account.accounts_df.

        Returns
        -------
        None
            TODO one-line description of return value of _validate_one_and_only_one_primary_checking_account.

        Contract
        --------
        - #TODO contract lines for _validate_one_and_only_one_primary_checking_account.
        - #TODO document exceptions, mutations, and precision assumptions for _validate_one_and_only_one_primary_checking_account.

        @interface-report: show
        """
        checking_accounts_df = accounts_df[accounts_df.Account_Type == "checking"]
        primary_checking_accounts_df = checking_accounts_df[
            checking_accounts_df.Primary_Checking_Ind == True
        ]
        print(checking_accounts_df.to_string())
        if primary_checking_accounts_df.shape[0] != 1:
            raise ValueError("AccountSet must have one and only one primary checking account")

    @staticmethod
    def _validate_unique_names(accounts_df):
        """
        TODO one-line description of _validate_unique_names. #Codex-write-doctstring-OK

        @interface-report: ignore
        """
        # TODO write a descriptive value error instead of assertion error
        assert len(accounts_df.Name) == len(set(accounts_df.Name)) #Account Names must be unique

    #TODO manual review of AccountSet.__init__ docstring
    def __init__(self, accounts_list=None):
        """
        TODO one-line description of __init__.

        TODO multi-line description of __init__.
        TODO explain how AccountSet.__init__ participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        accounts_list : list[Account] | None
            TODO one-line description of __init__.accounts_list.

        Returns
        -------
        None
            TODO one-line description of return value of __init__.

        Contract
        --------
        - #TODO contract lines for __init__.
        - #TODO document exceptions, mutations, and precision assumptions for __init__.

        @interface-report: show
        """

        self.primary_checking_account_name = None

        if accounts_list is None:
            accounts_list = []

        self.accounts = accounts_list

        if not self.accounts:
            return

        accounts_df = self.getAccounts()
        #TODO set primary_checking_account_name ; unclear if this is still being used after Codex-powered refactors
        AccountSet._validate_unique_names(accounts_df)

    def __str__(self):
        """
        TODO one-line description of __str__. #Codex-write-doctstring-OK

        @interface-report: show
        """
        return self.getAccounts().to_string()

    #TODO manual review of AccountSet.getPrimaryCheckingAccountName docstring
    def getPrimaryCheckingAccountName(self):
        """
        TODO one-line description of getPrimaryCheckingAccountName.

        TODO multi-line description of getPrimaryCheckingAccountName.
        TODO explain how AccountSet.getPrimaryCheckingAccountName participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        None
            TODO confirm that getPrimaryCheckingAccountName takes no parameters beyond self/cls.

        Returns
        -------
        str | None
            TODO one-line description of return value of getPrimaryCheckingAccountName.

        Contract
        --------
        - #TODO contract lines for getPrimaryCheckingAccountName.
        - #TODO document exceptions, mutations, and precision assumptions for getPrimaryCheckingAccountName.

        @interface-report: show
        """
        if self.primary_checking_account_name is None:
            primary_checking_accounts = [
                account.name
                for account in self.accounts
                if account.account_type == "checking"
                and account.primary_checking_ind is True
            ]
            if len(primary_checking_accounts) == 1:
                self.primary_checking_account_name = primary_checking_accounts[0]
        return self.primary_checking_account_name



    #TODO manual review of AccountSet.createAccount docstring
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
        TODO one-line description of createAccount.

        TODO multi-line description of createAccount.
        TODO explain how AccountSet.createAccount participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        name : str
            TODO one-line description of createAccount.name.

        balance : float
            TODO one-line description of createAccount.balance.

        min_balance : float
            TODO one-line description of createAccount.min_balance.

        max_balance : float
            TODO one-line description of createAccount.max_balance.

        account_type : str
            TODO one-line description of createAccount.account_type.

        **kwargs : dict
            TODO one-line description of createAccount.kwargs.

        Returns
        -------
        None
            TODO one-line description of return value of createAccount.

        Contract
        --------
        - #TODO contract lines for createAccount.
        - #TODO document exceptions, mutations, and precision assumptions for createAccount.

        @interface-report: show
        """

        allowed_kwargs = ['billing_start_date', 'interest_type', 'apr', 'interest_interval', 'minimum_payment',
                          'previous_statement_balance', 'current_statement_balance', 'principal_balance',
                          'interest_balance', 'billing_cycle_payment_balance',
                          'end_of_previous_cycle_balance', 'primary_checking_ind']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        allowed_account_types = ['checking', 'credit', 'loan', 'savings']
        if not account_type in allowed_account_types:
            raise ValueError(f"Unexpected account type: ({account_type})")

        #assert groups are all present
        checking_required_kwargs = ['primary_checking_ind']
        credit_required_kwargs = ['billing_start_date', 'apr', 'interest_interval', 'minimum_payment', 'previous_statement_balance', 'current_statement_balance', 'end_of_previous_cycle_balance']
        loan_required_kwargs = ['billing_start_date', 'apr', 'interest_interval', 'minimum_payment', 'principal_balance',
                          'interest_balance', 'billing_cycle_payment_balance']

        # TODO DEFER implement required kwargs in createAccount for investment case
        # investment_required_kwargs = ['billing_start_date', 'interest_type', 'apr', 'interest_interval', 'minimum_payment',
        #                   'previous_statement_balance', 'current_statement_balance', 'principal_balance',
        #                   'interest_balance', 'end_of_previous_cycle_balance']


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

        # TODO DEFER implement createAccount branch for investment case
        # elif account_type == 'investment':
        #     assert balance == kwargs['current_statement_balance'] + kwargs['previous_statement_balance']
        #     self.createInvestmentAccount(name,
        #                                  current_statement_balance=kwargs['current_statement_balance'],
        #                                  previous_statement_balance=kwargs['previous_statement_balance'],
        #                                  billing_start_date=kwargs['billing_start_date'],
        #                                  apr=kwargs['apr'],
        #                                  end_of_previous_cycle_balance=kwargs['end_of_previous_cycle_balance'])

        accounts_df = self.getAccounts()
        loan_account_rows_df = accounts_df[
            accounts_df.Account_Type.isin(
                [
                    "principal balance",
                    "interest",
                    "loan billing cycle payment bal",
                ]
            )
        ]
        credit_account_rows_df = accounts_df[
            accounts_df.Account_Type.isin(
                [
                    "credit prev stmt bal",
                    "credit curr stmt bal",
                    "credit billing cycle payment bal",
                    "credit end of prev cycle bal",
                ]
            )
        ]

        AccountSet._validate_unique_names(accounts_df)


    #TODO manual review of AccountSet.createCheckingAccount docstring
    def createCheckingAccount(self, name, balance, min_balance, max_balance, primary_checking_ind):
        """
        TODO one-line description of createCheckingAccount.

        TODO multi-line description of createCheckingAccount.
        TODO explain how AccountSet.createCheckingAccount participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        name : str
            TODO one-line description of createCheckingAccount.name.

        balance : float
            TODO one-line description of createCheckingAccount.balance.

        min_balance : float
            TODO one-line description of createCheckingAccount.min_balance.

        max_balance : float
            TODO one-line description of createCheckingAccount.max_balance.

        primary_checking_ind : bool
            TODO one-line description of createCheckingAccount.primary_checking_ind.

        Returns
        -------
        None
            TODO one-line description of return value of createCheckingAccount.

        Contract
        --------
        - #TODO contract lines for createCheckingAccount.
        - #TODO document exceptions, mutations, and precision assumptions for createCheckingAccount.

        @interface-report: show
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

    #TODO manual review of AccountSet.createLoanAccount docstring
    def createLoanAccount(self, name, principal_balance, interest_balance, min_balance, max_balance, billing_start_date,
                          apr, minimum_payment, billing_cycle_payment_balance=0,):
        """
        TODO one-line description of createLoanAccount.

        TODO multi-line description of createLoanAccount.
        TODO explain how AccountSet.createLoanAccount participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        name : str
            TODO one-line description of createLoanAccount.name.

        principal_balance : float
            TODO one-line description of createLoanAccount.principal_balance.

        interest_balance : float
            TODO one-line description of createLoanAccount.interest_balance.

        min_balance : float
            TODO one-line description of createLoanAccount.min_balance.

        max_balance : float
            TODO one-line description of createLoanAccount.max_balance.

        billing_start_date : date
            TODO one-line description of createLoanAccount.billing_start_date.

        apr : float
            TODO one-line description of createLoanAccount.apr.

        minimum_payment : float
            TODO one-line description of createLoanAccount.minimum_payment.

        billing_cycle_payment_balance : float
            TODO one-line description of createLoanAccount.billing_cycle_payment_balance.

        Returns
        -------
        None
            TODO one-line description of return value of createLoanAccount.

        Contract
        --------
        - #TODO contract lines for createLoanAccount.
        - #TODO document exceptions, mutations, and precision assumptions for createLoanAccount.

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

    #TODO manual review of AccountSet.createCreditCardAccount docstring
    def createCreditCardAccount(self, name, current_statement_balance, previous_statement_balance, min_balance, max_balance,
                                billing_start_date, apr, minimum_payment, end_of_previous_cycle_balance):
        """
        TODO one-line description of createCreditCardAccount.

        TODO multi-line description of createCreditCardAccount.
        TODO explain how AccountSet.createCreditCardAccount participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        name : str
            TODO one-line description of createCreditCardAccount.name.

        current_statement_balance : float
            TODO one-line description of createCreditCardAccount.current_statement_balance.

        previous_statement_balance : float
            TODO one-line description of createCreditCardAccount.previous_statement_balance.

        min_balance : float
            TODO one-line description of createCreditCardAccount.min_balance.

        max_balance : float
            TODO one-line description of createCreditCardAccount.max_balance.

        billing_start_date : date
            TODO one-line description of createCreditCardAccount.billing_start_date.

        apr : float
            TODO one-line description of createCreditCardAccount.apr.

        minimum_payment : float
            TODO one-line description of createCreditCardAccount.minimum_payment.

        end_of_previous_cycle_balance : float
            TODO one-line description of createCreditCardAccount.end_of_previous_cycle_balance.

        Returns
        -------
        None
            TODO one-line description of return value of createCreditCardAccount.

        Contract
        --------
        - #TODO contract lines for createCreditCardAccount.
        - #TODO document exceptions, mutations, and precision assumptions for createCreditCardAccount.

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

    # TODO DEFER implement createInvestmentAccount
    # def createInvestmentAccount(self, name, balance, apr):
    #     account = Account(
    #         name=name,
    #         balance=balance,
    #         account_type="investment",
    #         apr=apr,
    #     )
    #     self.accounts.append(account)


    #TODO manual review of AccountSet.getBalances docstring
    def getBalances(self):
        """
        TODO one-line description of getBalances.

        TODO multi-line description of getBalances.
        TODO explain how AccountSet.getBalances participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        None
            TODO confirm that getBalances takes no parameters beyond self/cls.

        Returns
        -------
        dict
            TODO one-line description of return value of getBalances.

        Contract
        --------
        - #TODO contract lines for getBalances.
        - #TODO document exceptions, mutations, and precision assumptions for getBalances.

        @interface-report: show
        """
        balances_dict = {account.name: account.balance for account in self.accounts}
        return balances_dict

    #TODO manual review of AccountSet._get_account_by_name docstring
    def _get_account_by_name(self, account_name):
        """
        TODO one-line description of _get_account_by_name.

        TODO multi-line description of _get_account_by_name.
        TODO explain how AccountSet._get_account_by_name participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account_name : str | None
            TODO one-line description of _get_account_by_name.account_name.

        Returns
        -------
        Account | None
            TODO one-line description of return value of _get_account_by_name.

        Contract
        --------
        - #TODO contract lines for _get_account_by_name.
        - #TODO document exceptions, mutations, and precision assumptions for _get_account_by_name.

        @interface-report: show
        """
        if account_name in [None, "", "None"]:
            return None

        matching_accounts = [
            account for account in self.accounts if account.name == account_name
        ]
        if len(matching_accounts) != 1:
            raise ValueError(
                f"Expected exactly one account named '{account_name}', found {len(matching_accounts)}"
            )
        return matching_accounts[0]

    #TODO manual review of AccountSet._validate_account_balance_bounds docstring
    @staticmethod
    def _validate_account_balance_bounds(account, proposed_balance, role):
        """
        TODO one-line description of _validate_account_balance_bounds.

        TODO multi-line description of _validate_account_balance_bounds.
        TODO explain how AccountSet._validate_account_balance_bounds participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of _validate_account_balance_bounds.account.

        proposed_balance : float
            TODO one-line description of _validate_account_balance_bounds.proposed_balance.

        role : str
            TODO one-line description of _validate_account_balance_bounds.role.

        Returns
        -------
        Decimal | float
            TODO one-line description of return value of _validate_account_balance_bounds.

        Contract
        --------
        - #TODO contract lines for _validate_account_balance_bounds.
        - #TODO document exceptions, mutations, and precision assumptions for _validate_account_balance_bounds.

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
            raise AccountBoundaryError(
                f"transaction violated {role} boundaries:\n"
                f"{role}:\n{account}\n"
                f"Proposed balance: {proposed_balance}"
            )
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
            raise AccountBoundaryError(
                f"transaction violated {role} boundaries:\n"
                f"{role}:\n{account}\n"
                f"Proposed balance: {proposed_balance}"
            )

        return proposed_balance

    #TODO manual review of AccountSet._sync_debt_account_from_billing_state docstring
    @staticmethod
    def _sync_debt_account_from_billing_state(account):
        """
        TODO one-line description of _sync_debt_account_from_billing_state.

        TODO multi-line description of _sync_debt_account_from_billing_state.
        TODO explain how AccountSet._sync_debt_account_from_billing_state participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of _sync_debt_account_from_billing_state.account.

        Returns
        -------
        None
            TODO one-line description of return value of _sync_debt_account_from_billing_state.

        Contract
        --------
        - #TODO contract lines for _sync_debt_account_from_billing_state.
        - #TODO document exceptions, mutations, and precision assumptions for _sync_debt_account_from_billing_state.

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

    #TODO manual review of AccountSet._increase_debt_balance docstring
    @staticmethod
    def _increase_debt_balance(account, amount):
        """
        TODO one-line description of _increase_debt_balance.

        TODO multi-line description of _increase_debt_balance.
        TODO explain how AccountSet._increase_debt_balance participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of _increase_debt_balance.account.

        amount : float
            TODO one-line description of _increase_debt_balance.amount.

        Returns
        -------
        None
            TODO one-line description of return value of _increase_debt_balance.

        Contract
        --------
        - #TODO contract lines for _increase_debt_balance.
        - #TODO document exceptions, mutations, and precision assumptions for _increase_debt_balance.

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

    #TODO manual review of AccountSet._decrease_credit_balance docstring
    @staticmethod
    def _decrease_credit_balance(account, amount, minimum_payment_flag):
        """
        TODO one-line description of _decrease_credit_balance.

        TODO multi-line description of _decrease_credit_balance.
        TODO explain how AccountSet._decrease_credit_balance participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of _decrease_credit_balance.account.

        amount : float
            TODO one-line description of _decrease_credit_balance.amount.

        minimum_payment_flag : bool
            TODO one-line description of _decrease_credit_balance.minimum_payment_flag.

        Returns
        -------
        None
            TODO one-line description of return value of _decrease_credit_balance.

        Contract
        --------
        - #TODO contract lines for _decrease_credit_balance.
        - #TODO document exceptions, mutations, and precision assumptions for _decrease_credit_balance.

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
            raise ValueError(
                f"Payment amount {amount} exceeds credit balance for '{account.name}'"
            )
        payment_remaining = Decimal("0")

        if not minimum_payment_flag:
            account.billing_state.billing_cycle_payment_balance += amount
        AccountSet._sync_debt_account_from_billing_state(account)

    #TODO manual review of AccountSet._decrease_loan_balance docstring
    @staticmethod
    def _decrease_loan_balance(account, amount, minimum_payment_flag):
        """
        TODO one-line description of _decrease_loan_balance.

        TODO multi-line description of _decrease_loan_balance.
        TODO explain how AccountSet._decrease_loan_balance participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of _decrease_loan_balance.account.

        amount : float
            TODO one-line description of _decrease_loan_balance.amount.

        minimum_payment_flag : bool
            TODO one-line description of _decrease_loan_balance.minimum_payment_flag.

        Returns
        -------
        None
            TODO one-line description of return value of _decrease_loan_balance.

        Contract
        --------
        - #TODO contract lines for _decrease_loan_balance.
        - #TODO document exceptions, mutations, and precision assumptions for _decrease_loan_balance.

        @interface-report: show
        """
        amount = AccountSet._money(amount)
        starting_balance = account.billing_state.balance
        interest_payment, principal_payment = account.billing_state.apply_payment(amount)
        payment_remaining = amount - interest_payment - principal_payment

        if payment_remaining > MONEY_BOUNDARY_TOLERANCE:
            raise ValueError(
                f"Payment amount {amount} exceeds loan balance for '{account.name}'"
            )
        payment_remaining = Decimal("0")

        if not minimum_payment_flag:
            account.billing_state.billing_cycle_payment_balance += amount
        AccountSet._sync_debt_account_from_billing_state(account)
        assert (
            abs(starting_balance - account.billing_state.balance - amount)
            <= MONEY_BOUNDARY_TOLERANCE
        )

    #TODO manual review of AccountSet.is_billing_date docstring
    @staticmethod
    def is_billing_date(account, current_date):
        """
        TODO one-line description of is_billing_date.

        TODO multi-line description of is_billing_date.
        TODO explain how AccountSet.is_billing_date participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of is_billing_date.account.

        current_date : date
            TODO one-line description of is_billing_date.current_date.

        Returns
        -------
        bool
            TODO one-line description of return value of is_billing_date.

        Contract
        --------
        - #TODO contract lines for is_billing_date.
        - #TODO document exceptions, mutations, and precision assumptions for is_billing_date.

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

    #TODO manual review of AccountSet.updateCreditCardEndOfPreviousCycleBalances docstring
    def updateCreditCardEndOfPreviousCycleBalances(self, current_date):
        """
        TODO one-line description of updateCreditCardEndOfPreviousCycleBalances.

        TODO multi-line description of updateCreditCardEndOfPreviousCycleBalances.
        TODO explain how AccountSet.updateCreditCardEndOfPreviousCycleBalances participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        current_date : date
            TODO one-line description of updateCreditCardEndOfPreviousCycleBalances.current_date.

        Returns
        -------
        None
            TODO one-line description of return value of updateCreditCardEndOfPreviousCycleBalances.

        Contract
        --------
        - #TODO contract lines for updateCreditCardEndOfPreviousCycleBalances.
        - #TODO document exceptions, mutations, and precision assumptions for updateCreditCardEndOfPreviousCycleBalances.

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

    #TODO manual review of AccountSet.getForecastAccountBalances docstring
    def getForecastAccountBalances(self, include_debug_columns=False):
        """
        TODO one-line description of getForecastAccountBalances.

        TODO multi-line description of getForecastAccountBalances.
        TODO explain how AccountSet.getForecastAccountBalances participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        include_debug_columns : bool
            TODO one-line description of getForecastAccountBalances.include_debug_columns.

        Returns
        -------
        dict
            TODO one-line description of return value of getForecastAccountBalances.

        Contract
        --------
        - #TODO contract lines for getForecastAccountBalances.
        - #TODO document exceptions, mutations, and precision assumptions for getForecastAccountBalances.

        @interface-report: show
        """
        balances = {}
        for account in self.accounts:
            balances[account.name] = self._forecast_value(account.balance)
            if include_debug_columns:
                balances.update(self.getForecastColumnsForAccount(account))
        return balances

    #TODO manual review of AccountSet._decrease_debt_balance docstring
    @staticmethod
    def _decrease_debt_balance(account, amount, minimum_payment_flag):
        """
        TODO one-line description of _decrease_debt_balance.

        TODO multi-line description of _decrease_debt_balance.
        TODO explain how AccountSet._decrease_debt_balance participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        account : Account
            TODO one-line description of _decrease_debt_balance.account.

        amount : float
            TODO one-line description of _decrease_debt_balance.amount.

        minimum_payment_flag : bool
            TODO one-line description of _decrease_debt_balance.minimum_payment_flag.

        Returns
        -------
        None
            TODO one-line description of return value of _decrease_debt_balance.

        Contract
        --------
        - #TODO contract lines for _decrease_debt_balance.
        - #TODO document exceptions, mutations, and precision assumptions for _decrease_debt_balance.

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

        if Account_To == "ALL_LOANS":
            for single_account_loan_payment in self.allocate_additional_loan_payments(
                Amount, account_from=Account_From
            ):
                self.executeTransaction(
                    single_account_loan_payment[0],
                    single_account_loan_payment[1],
                    single_account_loan_payment[2],
                    income_flag=False,
                )
            return

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
                "income_flag was True but did not refer to a checking account or referred to multiple accounts"
            )

        if account_from is not None:
            if account_from.account_type == "checking":
                proposed_balance = self._money(account_from.balance) - self._money(
                    amount
                )
                proposed_balance = self._validate_account_balance_bounds(
                    account_from, proposed_balance, "Account_From"
                )
                account_from.balance = proposed_balance
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
            if account_to.account_type == "checking":
                proposed_balance = self._money(account_to.balance) + self._money(
                    amount
                )
                proposed_balance = self._validate_account_balance_bounds(
                    account_to, proposed_balance, "Account_To"
                )
                account_to.balance = proposed_balance
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

    #TODO manual review of AccountSet.allocate_additional_loan_payments docstring
    def allocate_additional_loan_payments(self, amount, account_from=None):
        """
        TODO one-line description of allocate_additional_loan_payments.

        TODO multi-line description of allocate_additional_loan_payments.
        TODO explain how AccountSet.allocate_additional_loan_payments participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        amount : float
            TODO one-line description of allocate_additional_loan_payments.amount.

        account_from : str | None
            TODO one-line description of allocate_additional_loan_payments.account_from.

        Returns
        -------
        list[list]
            TODO one-line description of return value of allocate_additional_loan_payments.

        Contract
        --------
        - #TODO contract lines for allocate_additional_loan_payments.
        - #TODO document exceptions, mutations, and precision assumptions for allocate_additional_loan_payments.

        @interface-report: show
        """
        amount = self._money(abs(amount))
        if amount == 0:
            return []

        checking_acct_name = account_from or self.getPrimaryCheckingAccountName()
        checking_account = self._get_account_by_name(checking_acct_name)
        if checking_account is None or checking_account.account_type != "checking":
            raise ValueError("ALL_LOANS payments require a checking source account")

        amount = min(amount, self._money(checking_account.balance))
        if amount == 0:
            return []

        account_set = copy.deepcopy(self)
        payment_dict = {}

        while amount > MONEY_BOUNDARY_TOLERANCE:
            loan_accounts = [
                account
                for account in account_set.accounts
                if account.account_type == "loan"
                and account.billing_state.balance > MONEY_BOUNDARY_TOLERANCE
            ]
            if not loan_accounts:
                break

            marginal_interest_amounts = [
                loan.billing_state.principal_balance * loan.apr
                for loan in loan_accounts
            ]
            highest_marginal_interest = max(marginal_interest_amounts)

            if highest_marginal_interest <= MONEY_BOUNDARY_TOLERANCE:
                target_loans = loan_accounts
                proposed_payment_by_name = {
                    loan.name: min(loan.billing_state.balance, amount)
                    for loan in target_loans
                }
            else:
                lower_marginal_interest_amounts = [
                    marginal_interest_amount
                    for marginal_interest_amount in marginal_interest_amounts
                    if highest_marginal_interest - marginal_interest_amount
                    > MONEY_BOUNDARY_TOLERANCE
                ]
                next_marginal_interest = (
                    max(lower_marginal_interest_amounts)
                    if lower_marginal_interest_amounts
                    else Decimal("0")
                )

                proposed_payment_by_name = {}
                for loan, marginal_interest_amount in zip(
                    loan_accounts, marginal_interest_amounts
                ):
                    if (
                        highest_marginal_interest - marginal_interest_amount
                        > MONEY_BOUNDARY_TOLERANCE
                    ):
                        proposed_payment_by_name[loan.name] = Decimal("0")
                        continue

                    target_principal_balance = next_marginal_interest / loan.apr
                    principal_payment = (
                        loan.billing_state.principal_balance
                        - target_principal_balance
                    )
                    principal_payment = max(Decimal("0"), principal_payment)
                    proposed_payment_by_name[loan.name] = min(
                        loan.billing_state.balance,
                        loan.billing_state.interest_balance + principal_payment,
                    )

            total_proposed_payment = sum(proposed_payment_by_name.values(), Decimal("0"))
            if total_proposed_payment <= MONEY_BOUNDARY_TOLERANCE:
                break

            if amount < total_proposed_payment:
                proposed_payment_by_name = {
                    loan_name: proposed_payment * amount / total_proposed_payment
                    for loan_name, proposed_payment in proposed_payment_by_name.items()
                }
                total_proposed_payment = amount

            for loan_name, proposed_payment in proposed_payment_by_name.items():
                if proposed_payment <= MONEY_BOUNDARY_TOLERANCE:
                    continue
                account_set.executeTransaction(
                    Account_From=checking_acct_name,
                    Account_To=loan_name,
                    Amount=proposed_payment,
                )
                payment_dict[loan_name] = (
                    payment_dict.get(loan_name, Decimal("0")) + proposed_payment
                )

            amount -= total_proposed_payment

        return [
            [checking_acct_name, loan_name, payment_amount]
            for loan_name, payment_amount in payment_dict.items()
            if payment_amount > MONEY_BOUNDARY_TOLERANCE
        ]

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

    #TODO manual review of AccountSet.to_dict docstring
    def to_dict(self):
        """
        TODO one-line description of to_dict.

        TODO multi-line description of to_dict.
        TODO explain how AccountSet.to_dict participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        None
            TODO confirm that to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            TODO one-line description of return value of to_dict.

        Contract
        --------
        - #TODO contract lines for to_dict.
        - #TODO document exceptions, mutations, and precision assumptions for to_dict.

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

    #TODO manual review of AccountSet.to_json docstring
    def to_json(self):
        """
        TODO one-line description of to_json.

        TODO multi-line description of to_json.
        TODO explain how AccountSet.to_json participates in account
        TODO state management, forecasting, validation, or serialization.

        Parameters
        ----------
        None
            TODO confirm that to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of to_json.

        Contract
        --------
        - #TODO contract lines for to_json.
        - #TODO document exceptions, mutations, and precision assumptions for to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()
