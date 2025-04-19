from core.AccountSet import AccountSet
from core.LineItemSet import LineItemSet
from core.DecisionRuleSet import DecisionRuleSet
from core.MilestoneSet import MilestoneSet

from dataclasses import dataclass, field
from typing import Optional
import datetime


@dataclass
class ExpenseForecastParams:
    account_set: AccountSet
    lineitem_set: LineItemSet
    decisionrule_set: DecisionRuleSet
    start_date: datetime.datetime
    end_date: datetime.datetime
    milestone_set: MilestoneSet
    approximate_flag: bool = False
    forecast_set_name: str = ""
    forecast_name: str = ""
    validate: bool = True