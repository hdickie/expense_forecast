from typing import Optional
from pydantic import BaseModel, Field
from typing import List, Literal



class ParameterRow(BaseModel):
    start_date: str
    end_date: str
    forecast_name: str
    approximate: Optional[bool] = False

class AccountRow(BaseModel):
    account_name: str
    account_type: Literal["checking", "credit", "loan", "investment"]
    interest_type: Optional[Literal["simple", "compound"]]
    interest_cadence: Optional[Literal["daily", "monthly"]]
    balance: float
    min_balance: Optional[float]
    max_balance: Optional[float]
    billing_start_date: Optional[str]
    interest_type: Optional[str]
    apr: Optional[float]
    minimum_payment: Optional[float]
    primary_checking: Optional[bool] = False
    prev_cycle_balance: Optional[float]

class LineItemRow(BaseModel):
    name: str
    amount: float
    priority: int
    cadence: Literal["once", "daily", "weekly", "semiweekly", "monthly", "quarterly", "yearly"]
    start_date: Optional[str]
    end_date: Optional[str]
    deferrable: bool
    partial_payment_allowed: bool

class DecisionRuleRow(BaseModel):
    memo_regex: str
    priority: int
    account_from: str
    account_to: str

class MilestoneRow(BaseModel):
    milestone_name: str
    account_name: str
    min_balance: Optional[float]
    max_balance: Optional[float]
    memo_regex: Optional[str]
    account_milestone_names: Optional[str]
    memo_milestone_name: Optional[str]

class DraftSubmission(BaseModel):
    parameters: List[ParameterRow]
    accounts: List[AccountRow]
    line_items: List[LineItemRow]
    decision_rules: List[DecisionRuleRow]
    milestones: List[MilestoneRow]


class SessionData(BaseModel):
    user_id: str
    forecast_id: Optional[str] = None

class User(BaseModel):
    username: str
    # role: str
    # isAdmin: str
    # add whatever fields you want to collect from the client


class ForecastSelect(BaseModel):
    forecast_name: str