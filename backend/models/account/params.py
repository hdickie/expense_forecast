from dataclasses import dataclass, field
from typing import Optional
import datetime

from enum import Enum

class AccountType(Enum):
    CHECKING = "checking"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    CREDIT_PREV_STMT_BAL = "credit prev stmt bal"
    CREDIT_CURR_STMT_BAL = "credit curr stmt bal"
    CREDIT_BILLLING_CYCLE_PAYMENT_BAL = "credit billing cycle payment bal"
    CREDIT_END_OF_PREV_CYCLE_BAL = "credit end of prev cycle bal"
    LOAN_PRINCIPAL_BALANCE = "loan principal balance"
    LOAN_INTEREST = "loan interest"
    LOAN_BILLLING_CYCLE_PAYMENT_BAL = "loan billing cycle payment bal"
    LOAN_END_OF_PREV_CYCLE_BAL = "loan end of prev cycle bal"
    SAVINGS = "savings"

class InterestType(Enum):
    SIMPLE="simple"
    COMPOUND="compound"

class InterestCadence(Enum):
    DAILY="daily"
    MONTHLY="monthly"

@dataclass
class AccountParams:
    name: str
    balance: float
    min_balance: float
    max_balance: float
    

@dataclass
class CheckingAccountParams(AccountParams):
    account_type: AccountType = field(default=AccountType.CHECKING, init=False)
    primary_checking_ind: bool

@dataclass
class CreditCardAccountParams(AccountParams):
    account_type: AccountType = field(default=AccountType.CREDIT, init=False)
    billing_start_date: datetime.datetime
    interest_type: InterestType = field(default=InterestType.COMPOUND, init=False)
    apr: float
    interest_cadence: InterestCadence = field(default=InterestCadence.MONTHLY, init=False)
    minimum_payment: float
    current_statement_balance: float
    previous_statement_balance: float
    billing_cycle_payment_balance: Optional[float] = None

@dataclass
class LoanAccountParams(AccountParams):
    account_type: AccountType = field(default=AccountType.LOAN, init=False)
    billing_start_date: datetime.datetime
    interest_type: InterestType
    apr: float
    interest_cadence: InterestCadence
    minimum_payment: float
    end_of_previous_cycle_balance: Optional[float] = None

@dataclass
class InvestmentAccountParams(AccountParams):
    account_type: AccountType = field(default=AccountType.INVESTMENT, init=False)
    billing_start_date: Optional[datetime.datetime] = None
    interest_type: Optional[InterestType] = None
    apr: Optional[float] = None
    interest_cadence: Optional[InterestCadence] = None
    end_of_previous_cycle_balance: Optional[float] = None
