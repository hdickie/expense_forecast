from .Account import Account
from .CheckingBillingState import CheckingBillingState
from .CreditCardBillingState import CreditCardBillingState
from .LoanBillingState import LoanBillingState
from datetime import date, datetime, timedelta
from decimal import Decimal
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
        if len(primary_checking_accounts_df) != 1:
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
                          'interest_balance', 'end_of_previous_cycle_balance', 'primary_checking_ind']
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
                          'interest_balance', 'end_of_previous_cycle_balance']

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
                                   end_of_previous_cycle_balance=kwargs['end_of_previous_cycle_balance'])

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
                    "loan end of prev cycle bal",
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
                          apr, minimum_payment, end_of_previous_cycle_balance,):

        principal_balance = self._money(principal_balance)
        interest_balance = self._money(interest_balance)
        minimum_payment = self._money(minimum_payment)
        apr = self._money(apr)
        end_of_previous_cycle_balance = self._money(end_of_previous_cycle_balance)

        billing_cycle_payment_balance = end_of_previous_cycle_balance - principal_balance
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
        if not account.min_balance <= proposed_balance <= account.max_balance:
            raise AccountBoundaryError(
                f"transaction violated {role} boundaries:\n"
                f"{role}:\n{account}\n"
                f"Proposed balance: {proposed_balance}"
            )

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

        if payment_remaining > Decimal(str(ROUNDING_ERROR_TOLERANCE)):
            raise ValueError(
                f"Payment amount {amount} exceeds credit balance for '{account.name}'"
            )

        if not minimum_payment_flag:
            account.billing_state.billing_cycle_payment_balance += amount
        AccountSet._sync_debt_account_from_billing_state(account)

    @staticmethod
    def _decrease_loan_balance(account, amount, minimum_payment_flag):
        amount = AccountSet._money(amount)
        starting_balance = account.billing_state.balance
        interest_payment, principal_payment = account.billing_state.apply_payment(amount)
        payment_remaining = amount - interest_payment - principal_payment

        if payment_remaining > ROUNDING_ERROR_TOLERANCE:
            raise ValueError(
                f"Payment amount {amount} exceeds loan balance for '{account.name}'"
            )

        if not minimum_payment_flag:
            account.billing_state.billing_cycle_payment_balance += amount
        AccountSet._sync_debt_account_from_billing_state(account)
        assert starting_balance - account.billing_state.balance == amount

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
            columns[f"{account.name}: Loan End of Prev Cycle Bal"] = AccountSet._forecast_value(
                billing_state.principal_balance
            )

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
            for single_account_loan_payment in self.allocate_additional_loan_payments(Amount):
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
                if isinstance(amount, Decimal):
                    proposed_balance = self._money(account_from.balance) - amount
                else:
                    proposed_balance = account_from.balance - amount
                self._validate_account_balance_bounds(
                    account_from, proposed_balance, "Account_From"
                )
                account_from.balance = proposed_balance
            elif account_from.account_type in ["credit", "loan"]:
                proposed_balance = (
                    self._money(account_from.balance) + self._money(amount)
                )
                self._validate_account_balance_bounds(
                    account_from, proposed_balance, "Account_From"
                )
                self._increase_debt_balance(account_from, amount)
            else:
                raise NotImplementedError(
                    "account type was: " + str(account_from.account_type)
                )

        if account_to is not None:
            if account_to.account_type == "checking":
                if isinstance(amount, Decimal):
                    proposed_balance = self._money(account_to.balance) + amount
                else:
                    proposed_balance = account_to.balance + amount
                self._validate_account_balance_bounds(
                    account_to, proposed_balance, "Account_To"
                )
                account_to.balance = proposed_balance
            elif account_to.account_type in ["credit", "loan"]:
                proposed_balance = (
                    self._money(account_to.balance) - self._money(amount)
                )
                self._validate_account_balance_bounds(
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

    #TODO come back to this when unit tests are fixed
    def allocate_additional_loan_payments(self, amount):
        # print('ENTER allocate_additional_loan_payments: '+str(amount))

        og_amount = amount

        check_sel_vec = [x for x in (self.getAccounts().Account_Type == "checking")]
        # checking_acct_name = self.getAccounts()[row_sel_vec].Name[0] #we use this waaay later during executeTransaction
        checking_acct_name = self.getPrimaryCheckingAccountName()
        if self.getAccounts()[check_sel_vec].Balance.iat[0] < amount:
            log_in_color(
                logger,
                "green",
                "debug",
                "input amount is greater than available balance. Reducing amount.",
            )
            amount = self.getAccounts().loc[check_sel_vec, :].Balance.iat[0]

        date_string_YYYYMMDD = "20000101"  # this method needs to be refactored

        account_set = copy.deepcopy(self)

        A = account_set.getAccounts()
        principal_accts_df = A[A.Account_Type == "principal balance"]

        principal_accts_df["Marginal Interest Amount"] = (
            principal_accts_df.Balance * principal_accts_df.APR
        )
        principal_accts_df["Marginal Interest Rank"] = principal_accts_df[
            "Marginal Interest Amount"
        ].rank(method="dense", ascending=False)

        number_of_phase_space_regions = max(
            principal_accts_df["Marginal Interest Rank"]
        )
        # log_in_color(logger,'yellow', 'debug','Explanation of the loan payment algorithm:')
        # log_in_color(logger,'yellow', 'debug', 'FACT 1: The optimal loan payment pays the loan with the highest marginal interest first.')
        # log_in_color(logger,'yellow', 'debug','FACT 2: If two loans have different balances and APRs, but will accrue the same amount of additional interest the next day, then it is at this point that we begin to split our next dollar between the two loans in proportion to the APR.')
        # log_in_color(logger,'yellow', 'debug','We would know that our allocation is optimal when the marginal interest for both loans stays the same.')
        # log_in_color(logger,'yellow', 'debug','Then we will reach a point where we are splitting our next dollar between two loans, then three... (assuming there are this many loans)')
        # log_in_color(logger,'yellow', 'debug','This algorithm finds these points to allocate payment.')
        # log_in_color(logger,'yellow', 'debug', 'If you plot this on a graph, the behavior changes when a new loan joins the group that is being paid proportionally. The space between these points is referred to as a phase space region.')
        # log_in_color(logger,'yellow', 'debug',
        #              'The following table shows the order in which loans will be paid. Marginal Interest Rank 1 will be paid until the Marginal Interest Amount is equal to the account with Marginal Interest Rank 2, etc.')
        # print(principal_accts_df.loc[:,('Name','Balance','Marginal Interest Amount','Marginal Interest Rank')].to_string())

        # log_in_color(logger,'yellow', 'debug', 'number_of_phase_space_regions:'+str(number_of_phase_space_regions))
        # print('number_of_phase_space_regions:'+str(number_of_phase_space_regions))

        all_account_names__1 = [x.split(":") for x in principal_accts_df.Name]
        all_account_names__2 = [
            name for sublist in all_account_names__1 for name in sublist
        ]
        all_account_names = set(all_account_names__2) - set([" Principal Balance"])

        payment_amounts__BudgetSet = BudgetSet([])
        payment_amount_tuple_list = []

        # print('number_of_phase_space_regions:'+str(number_of_phase_space_regions))
        for i in range(0, int(number_of_phase_space_regions)):
            # print('Phase space region index........: ' + str(i))
            # print('remaining amount to be allocated: '+str(amount))

            if amount == 0:
                break

            log_in_color(
                logger, "yellow", "debug", "Phase space region index: " + str(i)
            )

            A = account_set.getAccounts()
            # print('A:\n')
            # print(A.to_string())

            principal_accts_df = A[A.Account_Type == "principal balance"]
            interest_accts_df = A[A.Account_Type == "interest"]

            total_amount_per_loan = {}
            for acct_name in all_account_names:
                principal_amt = principal_accts_df.iloc[
                    [acct_name in pa_element for pa_element in principal_accts_df.Name],
                    :,
                ].Balance.iloc[0]
                interest_amt = interest_accts_df.iloc[
                    [acct_name in pa_element for pa_element in interest_accts_df.Name],
                    :,
                ].Balance.iloc[0]

                total_amount_per_loan[acct_name] = principal_amt + interest_amt

            # print('total_amount_per_loan:'+str(total_amount_per_loan))
            # Let P0 be initial principal
            # Let M0 be initial marginal_interest
            # Let R be vector of APRs
            # then, P0 * R = M0

            # Assume the case where there are 2 loans
            # The principal balances at the beginning of the next phase space region corresponds to
            # P1 * R = M1
            # where both entries in M1 are the same, and correspond to the lower of the two marginal interest amounts
            # therefore, we calculate the maximum amount we are able to pay until the payment strategy must change as
            # P1 = M1 * R^-1
            # this is equivalent to taking the next desired state of marginal interest amounts and right multiplying by a vector of the reciprocal rates

            # P = np.matrix(principal_accts_df.Balance)
            P = np.array(principal_accts_df.Balance)
            P = P[:, None]

            # r = np.matrix(principal_accts_df.APR)
            r = np.array(principal_accts_df.APR)
            r = r[:, None]

            # reciprocal_rates = []
            # for i in range(0, P.shape[1]):
            #    reciprocal_rates.append(1 / r[0, i])
            # reciprocal_rates = np.matrix(reciprocal_rates)\

            # print('P_dot_r:')
            # print(np.matrix(P_dot_r))

            marginal_interest_amounts = np.diag(
                P.dot(r.T)
            )  # this represents marginal interest
            # marginal_interest_amounts__list = []
            # for i in range(0, P.shape[1]):
            #    marginal_interest_amounts__list.append(round(P_dot_r[i, i], 2))
            # print(marginal_interest_amounts__list)
            # marginal_interest_amounts__matrix = np.matrix(marginal_interest_amounts__list)
            # print('marginal_interest_amounts__matrix:')
            # print(marginal_interest_amounts__matrix)

            marginal_interest_amounts_df = pd.DataFrame(marginal_interest_amounts)
            marginal_interest_amounts_df.columns = ["Marginal Interest Amount"]
            marginal_interest_amounts_df["Marginal Interest Rank"] = (
                marginal_interest_amounts_df["Marginal Interest Amount"].rank(
                    method="dense", ascending=False
                )
            )
            # print('marginal_interest_amounts_df:')
            # print(marginal_interest_amounts_df)

            try:
                next_lowest_marginal_interest_amount = marginal_interest_amounts_df[
                    marginal_interest_amounts_df["Marginal Interest Rank"] == 2
                ].iloc[0, 0]
            except Exception as e:
                next_lowest_marginal_interest_amount = 0
            # print('next_lowest_marginal_interest_amount:')
            # print(next_lowest_marginal_interest_amount)
            marginal_interest_amounts_df__c = pd.DataFrame(
                marginal_interest_amounts_df, copy=True
            )

            # print('marginal_interest_amounts_df__c[marginal_interest_amounts_df__c[Marginal Interest Rank] == 1]')
            # print(marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1)
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1])
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1]['Marginal Interest Amount'])

            marginal_interest_amounts_df__c.loc[
                marginal_interest_amounts_df__c["Marginal Interest Rank"] == 1,
                marginal_interest_amounts_df__c.columns == "Marginal Interest Amount",
            ] = next_lowest_marginal_interest_amount
            next_step_marginal_interest_vector = np.array(
                marginal_interest_amounts_df__c["Marginal Interest Amount"]
            )  # this corresponds to the M1 vector
            next_step_marginal_interest_vector = next_step_marginal_interest_vector[
                :, None
            ]
            # print('next_step_marginal_interest_vector:\n')
            # print(next_step_marginal_interest_vector)

            current_principal_balance_state = P
            # print('current_state:' + str(current_state))
            # print('total_amount_per_loan:'+str(total_amount_per_loan))

            # print('current_state:\n'+str(current_state))

            # print('next_step_marginal_interest_vector:')
            # rint(next_step_marginal_interest_vector)

            reciprocal_rates = 1 / r

            # print('reciprocal_rates:')
            # print(reciprocal_rates)

            next_principal_balance_state = np.diag(
                next_step_marginal_interest_vector.dot(reciprocal_rates.T)
            )  # this corresponds to the P1 vector, and tells us how much we can pay before our strategy must change

            # print('current_principal_balance_state:\n' + str(current_principal_balance_state))
            # print('next_principal_balance_state:\n' + str(next_principal_balance_state))

            principal_balance_delta = (
                current_principal_balance_state.T - next_principal_balance_state
            ).T
            # print('principal_balance_delta:')
            # print(principal_balance_delta)

            # log_in_color(logger, 'blue', 'debug', 'principal_balance_delta:')
            # log_in_color(logger, 'blue', 'debug', str(principal_balance_delta))

            payment_amounts = []
            for i in range(0, principal_balance_delta.shape[0]):

                # if we pay at all, then we add the interest as well.
                current_loan_interest = np.array(
                    interest_accts_df.iloc[i, :].Balance
                )  # this is a 1 x 1 array

                proposed_payment_on_principal = principal_balance_delta

                # todo, currently, if the final payment includes interest, then the total gets distributed across multiple loans and does not go to interest first # https://github.com/hdickie/expense_forecast/issues/14
                if proposed_payment_on_principal[i][0] > 0:
                    loop__amount = (
                        proposed_payment_on_principal[i][0] + current_loan_interest
                    )
                else:
                    loop__amount = 0
                payment_amounts.append(loop__amount)
            # print('payment_amounts:'+str(payment_amounts))

            total_interest_on_loans_w_non_0_payment = 0
            for i in range(0, len(payment_amounts)):
                if principal_balance_delta[i] > 0:
                    total_interest_on_loans_w_non_0_payment += interest_accts_df.iloc[
                        i, :
                    ].Balance
            # print('total_interest_on_loans_w_non_0_payment:'+str(total_interest_on_loans_w_non_0_payment))

            if amount <= sum(payment_amounts):
                payment_amounts = [
                    a * (amount) / sum(payment_amounts) for a in payment_amounts
                ]
            # print('payment_amounts:' + str(payment_amounts))
            # print('amount -> remaining_amount:')
            # print(str(amount) + ' -> ' + str(amount - sum(payment_amounts)))
            amount = amount - sum(payment_amounts)

            for i in range(0, principal_balance_delta.shape[0]):
                loop__to_name = principal_accts_df.Name.iloc[i].split(":")[0]
                loop__amount = payment_amounts[i]

                # print( str( loop__amount ) + ' ' + loop__to_name )

                if loop__amount == 0:
                    continue

                account_set.executeTransaction(
                    Account_From=checking_acct_name,
                    Account_To=loop__to_name,
                    Amount=loop__amount,
                )
                # payment_amounts__BudgetSet.addBudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once', round(loop__amount,2), loop__to_name,False,partial_payment_allowed=False)
                payment_amount_tuple_list.append((loop__to_name, loop__amount))
        # print('payment_amount_tuple_list:'+str(payment_amount_tuple_list))

        unique_payment_amount_tuple_dict = {}
        for tp in payment_amount_tuple_list:
            if tp[0] not in unique_payment_amount_tuple_dict:
                unique_payment_amount_tuple_dict[tp[0]] = tp[1]
            else:
                unique_payment_amount_tuple_dict[tp[0]] += tp[1]
        # print('unique_payment_amount_tuple_dict:' + str(unique_payment_amount_tuple_dict))

        for key, value in unique_payment_amount_tuple_dict.items():
            payment_amounts__BudgetSet.addBudgetItem(
                date_string_YYYYMMDD,
                date_string_YYYYMMDD,
                7,
                "once",
                value,
                key,
                False,
                partial_payment_allowed=False,
            )

        # consolidate payments
        B = payment_amounts__BudgetSet.getBudgetItems()
        # print('B:')
        # print(B.to_string())
        payment_dict = {}
        for index, row in B.iterrows():
            # print('row:')
            # print(row)

            if row.Memo in payment_dict.keys():
                payment_dict[row.Memo] = payment_dict[row.Memo] + row.Amount
            else:
                payment_dict[row.Memo] = row.Amount
        # print('payment_dict:'+str(payment_dict))

        final_txns = []
        for key in payment_dict.keys():
            final_txns.append([checking_acct_name, key, payment_dict[key]])
            # final_budget_items.append(BudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once', payment_dict[key], False, key, ))
        # print('final_txns:'+str(final_txns))

        running_total = 0
        for t in final_txns:
            running_total += t[2]
        # print(str(running_total)+' ?= '+str(og_amount))
        assert running_total == og_amount

        # log_in_color(logger,'green', 'debug', 'final_txns:')
        # log_in_color(logger,'green', 'debug', final_txns)
        # log_in_color(logger,'blue', 'debug', 'EXIT allocate_additional_loan_payments(amount='+str(amount)+')')
        # print(final_txns)
        # print('EXIT allocate_additional_loan_payments')
        return final_txns

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
                        "End_Of_Previous_Cycle_Balance": self._dict_value(
                            billing_state.principal_balance
                            + billing_state.billing_cycle_payment_balance
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
