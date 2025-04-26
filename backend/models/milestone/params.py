from dataclasses import dataclass
from typing import Optional

@dataclass
class AccountMilestoneParams:
    milestone_name: str
    account_name: str
    min_balance: Optional[float] = None
    max_balance: Optional[float] = None
    
@dataclass
class MemoMilestoneParams:
    milestone_name: str
    memo_regex: str

@dataclass
class CompositeMilestoneParams:
    composite_milestone_name: str
    list_of_account_milestone_names: Optional[str] = None
    list_of_account_memo_names: Optional[str] = None