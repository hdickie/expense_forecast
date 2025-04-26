from dataclasses import dataclass
from typing import Optional
import datetime

from enum import Enum

class LineItemCadence(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    SEMIWEEKLY = "semiweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class LineItemParams:
    memo: str
    amount: float
    priority: int
    cadence: LineItemCadence
    start_date: datetime.datetime
    end_date: datetime.datetime
    deferrable: bool
    partial_payment_allowed: bool
    income_flag: bool
    