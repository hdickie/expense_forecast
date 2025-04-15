from dataclasses import dataclass
from typing import Optional
import datetime

from enum import Enum

class BudgetItemCadence(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    SEMIWEEKLY = "semiweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class BudgetItemParams:
    memo: str
    amount: float
    priority: int
    cadence: BudgetItemCadence
    start_date: datetime.datetime
    end_date: datetime.datetime
    deferrable: bool
    partial_payment_allowed: bool
    