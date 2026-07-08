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
from .BudgetSet import BudgetSet  # this could be refactored out, and should be in terms of independent dependencies and clear organization, but it works
import jsonpickle
from .generate_date_sequence import generate_date_sequence

# logger = setup_logger('AccountSet','./log/AccountSet.log',logging.INFO)
logger = logging.getLogger(__name__)

ROUNDING_ERROR_TOLERANCE = 0.0000000001
MONEY_BOUNDARY_TOLERANCE = Decimal("0.005")


class AccountBoundaryError(ValueError):
    pass


class AccountSet:
    @staticmethod
    def _money(value):
        return Decimal(str(value))

    @staticmethod
    def _dict_value(value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    @staticmethod
    def _forecast_value(value):
        if isinstance(value, Decimal):
            return float(value)
        return value


    ROUNDING_ERROR_TOLERANCE = 0.0000000001

    @staticmethod
    def _normalize_billing_start_date(value):
        if pd.isnull(value):
            return None
        if isinstance(value, pd.Timestamp):
            return value.date()
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return value

    # TODO I am not sure if I need this
    # @staticmethod
    # def initialize_from_dataframe(accounts_df):
    #     # print('ENTER AccountSet initialize_from_dataframe')
    #     A = AccountSet([])
    #     try:
    #         expect_curr_stmt_bal = False
    #         expect_prev_stmt_bal = False
    #         expect_principal_bal = False
    #         expect_interest_bal = False
    #         for index, row in accounts_df.iterrows():
    #             row = pd.DataFrame(row).T
    #
    #             accountname = row.account_name.iat[0].split(":")[0]
    #             balance = row.balance.iat[0]
    #             min_balance = row.min_balance.iat[0]
    #             max_balance = row.max_balance.iat[0]
    #             primary_checking_ind = row.primary_checking_ind.iat[0]
    #
    #             account_type = row.account_type.iat[0]
    #             if account_type == "curr stmt bal" and not expect_prev_stmt_bal:
    #                 current_statement_balance = row.balance.iat[0]
    #                 expect_prev_stmt_bal = True
    #             elif account_type == "prev stmt bal" and not expect_curr_stmt_bal:
    #                 previous_statement_balance = row.balance.iat[0]
    #                 billing_start_date_yyyymmdd = row.billing_start_date_yyyymmdd.iat[0]
    #                 apr = row.apr.iat[0]
    #                 minimum_payment = row.minimum_payment.iat[0]
    #                 expect_curr_stmt_bal = True
    #             elif account_type == "principal balance" and not expect_interest_bal:
    #                 billing_start_date_yyyymmdd = row.billing_start_date_yyyymmdd.iat[0]
    #                 apr = row.apr.iat[0]
    #                 minimum_payment = row.minimum_payment.iat[0]
    #                 principal_balance = row.balance.iat[0]
    #                 expect_interest_bal = True
    #             elif account_type == "interest" and not expect_principal_bal:
    #                 interest_balance = row.balance.iat[0]
    #                 expect_principal_bal = True
    #
    #             if account_type == "curr stmt bal" and expect_curr_stmt_bal:
    #                 current_statement_balance = row.balance.iat[0]
    #                 A.createCreditCardAccount(
    #                     accountname,
    #                     current_statement_balance,
    #                     previous_statement_balance,
    #                     min_balance,
    #                     max_balance,
    #                     billing_start_date_yyyymmdd,
    #                     apr,
    #                     minimum_payment,
    #                 )
    #                 expect_prev_stmt_bal = False
    #             elif account_type == "prev stmt bal" and expect_prev_stmt_bal:
    #                 A.createCreditCardAccount(
    #                     accountname,
    #                     current_statement_balance,
    #                     previous_statement_balance,
    #                     min_balance,
    #                     max_balance,
    #                     billing_start_date_yyyymmdd,
    #                     apr,
    #                     minimum_payment,
    #                 )
    #                 expect_curr_stmt_bal = False
    #             elif account_type == "principal balance" and expect_principal_bal:
    #                 principal_balance = row.balance.iat[0]
    #                 A.createLoanAccount(
    #                     accountname,
    #                     principal_balance,
    #                     interest_balance,
    #                     min_balance,
    #                     max_balance,
    #                     billing_start_date_yyyymmdd,
    #                     apr,
    #                     minimum_payment,
    #                 )
    #                 expect_interest_bal = False
    #             elif account_type == "interest" and expect_interest_bal:
    #                 A.createLoanAccount(
    #                     accountname,
    #                     principal_balance,
    #                     interest_balance,
    #                     min_balance,
    #                     max_balance,
    #                     billing_start_date_yyyymmdd,
    #                     apr,
    #                     minimum_payment,
    #                 )
    #                 expect_principal_bal = False
    #
    #             if account_type.lower() == "checking":
    #                 A.createCheckingAccount(
    #                     accountname, balance, min_balance, max_balance, primary_checking_ind
    #                 )
    #             elif account_type.lower() == "investment":
    #                 A.createInvestmentAccount(
    #                     accountname, row.balance, row.min_balance, row.max_balance, row.apr
    #                 )
    #     except Exception as e:
    #         print(e.args)
    #         raise e
    #     # print(A.getAccounts().to_string())
    #     # print('EXIT AccountSet initialize_from_dataframe')
    #     return A

    # TODO this might belong somewhere else, not sure
    @staticmethod
    def determineMinPaymentAmount(
            advance_payment_amount,
            interest_accrued_this_cycle,
            principal_due_this_cycle,
            total_balance,
            min_payment,
    ):
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

    def isSufficientToBeginForecast(self):
        accounts_df = self.getAccounts()
        AccountSet._validate_one_and_only_one_primary_checking_account(accounts_df)
        raise NotImplementedError # todo more strict checking #https://github.com/hdickie/expense_forecast/issues/18

    @staticmethod
    def _validate_one_and_only_one_primary_checking_account(accounts_df):
        checking_accounts_df = accounts_df[accounts_df.Account_Type == "checking"]
        primary_checking_accounts_df = checking_accounts_df[
            checking_accounts_df.Primary_Checking_Ind == True
        ]
        print(checking_accounts_df.to_string())
        if primary_checking_accounts_df.shape[0] != 1:
            raise ValueError("AccountSet must have one and only one primary checking account")

    @staticmethod
    def _validate_unique_names(accounts_df):
        assert len(accounts_df.Name) == len(set(accounts_df.Name)) #Account Names must be unique

    def __init__(self, accounts_list=None):

        self.primary_checking_account_name = None

        if accounts_list is None:
            accounts_list = []

        self.accounts = accounts_list

        if not self.accounts:
            return
        
        accounts_df = self.getAccounts()
        #TODO set primary_checking_account_name
        AccountSet._validate_unique_names(accounts_df)

    def __str__(self):
        return self.getAccounts().to_string()

    def getPrimaryCheckingAccountName(self):
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



    def createAccount(
        self,
        name,
        balance,
        min_balance,
        max_balance,
        account_type,
            **kwargs
    ):

        allowed_kwargs = ['billing_start_date', 'interest_type', 'apr', 'interest_cadence', 'minimum_payment',
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
        credit_required_kwargs = ['billing_start_date', 'apr', 'interest_cadence', 'minimum_payment', 'previous_statement_balance', 'current_statement_balance', 'end_of_previous_cycle_balance']
        loan_required_kwargs = ['billing_start_date', 'apr', 'interest_cadence', 'minimum_payment', 'principal_balance',
                          'interest_balance', 'billing_cycle_payment_balance']

        # todo i don't know what I want for this
        # investment_required_kwargs = ['billing_start_date', 'interest_type', 'apr', 'interest_cadence', 'minimum_payment',
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

        # todo I don't know what I want for this
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


    def createCheckingAccount(self, name, balance, min_balance, max_balance, primary_checking_ind):
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
            interest_cadence="daily",
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
            interest_cadence="monthly",
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

    # def createInvestmentAccount(self, name, balance, apr):
    #     #todo
    #     account = Account(
    #         name=name,
    #         balance=balance,
    #         account_type="investment",
    #         apr=apr,
    #     )
    #     self.accounts.append(account)


    def getBalances(self):
        balances_dict = {account.name: account.balance for account in self.accounts}
        return balances_dict

    def _get_account_by_name(self, account_name):
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

    @staticmethod
    def _validate_account_balance_bounds(account, proposed_balance, role):
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

    @staticmethod
    def _sync_debt_account_from_billing_state(account):
        if account.account_type not in ["credit", "loan"]:
            return

        if account.account_type == "credit":
            account.balance = (
                account.billing_state.previous_statement_balance
                + account.billing_state.current_statement_balance
            )
        elif account.account_type == "loan":
            account.balance = account.billing_state.balance

    @staticmethod
    def _increase_debt_balance(account, amount):
        amount = AccountSet._money(amount)
        if account.account_type == "credit":
            account.billing_state.current_statement_balance += amount
        elif account.account_type == "loan":
            account.billing_state.principal_balance += amount
        else:
            raise ValueError(f"Account '{account.name}' is not a debt account")
        AccountSet._sync_debt_account_from_billing_state(account)

    @staticmethod
    def _decrease_credit_balance(account, amount, minimum_payment_flag):
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

    @staticmethod
    def _decrease_loan_balance(account, amount, minimum_payment_flag):
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

    @staticmethod
    def is_billing_date(account, current_date):
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
                cadence="monthly",
            )
        )
        billing_days.add(billing_start_date)
        return current_date in billing_days

    def processCreditCardBillingDay(self, current_date):
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

    def updateCreditCardEndOfPreviousCycleBalances(self, current_date):
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

    @staticmethod
    def getForecastColumnsForAccount(account):
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

    def getForecastAccountBalances(self, include_debug_columns=False):
        balances = {}
        for account in self.accounts:
            balances[account.name] = self._forecast_value(account.balance)
            if include_debug_columns:
                balances.update(self.getForecastColumnsForAccount(account))
        return balances

    @staticmethod
    def _decrease_debt_balance(account, amount, minimum_payment_flag):
        if account.account_type == "credit":
            AccountSet._decrease_credit_balance(account, amount, minimum_payment_flag)
        elif account.account_type == "loan":
            AccountSet._decrease_loan_balance(account, amount, minimum_payment_flag)
        else:
            raise ValueError(f"Account '{account.name}' is not a debt account")

    def executeTransaction(
        self,
        Account_From,
        Account_To,
        Amount,
        income_flag=False,
        minimum_payment_flag=False,
    ):
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

    def allocate_additional_loan_payments(self, amount, account_from=None):
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

    # TODO include_debug_columns is not a needed parameter here
    def getAccounts(self, include_debug_columns=False):
        columns = [
            "Name",
            "Balance",
            "Min_Balance",
            "Max_Balance",
            "Account_Type",
            "Billing_Start_Date",
            "Interest_Type",
            "APR",
            "Interest_Cadence",
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
                    "Interest_Cadence": account.interest_cadence,
                    "Minimum_Payment": account.minimum_payment,
                    "Primary_Checking_Ind": account.primary_checking_ind,
                }
            )

        return pd.DataFrame(account_rows, columns=columns)

    def to_dict(self):
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
                    "Interest_Cadence": account.interest_cadence,
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
        Get a JSON <string> representation of the <AccountSet> object.

        """
        return jsonpickle.encode(self, indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()

# todo known bug- i was able to create multiple loan accounts with the same name #https://github.com/hdickie/expense_forecast/issues/15
