from dataclasses import dataclass
from typing import Optional

@dataclass
class AccountMilestoneParams:
    account_name: str
    min_balance: Optional[float] = None
    max_balance: Optional[float] = None
    