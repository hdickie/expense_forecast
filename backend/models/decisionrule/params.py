from dataclasses import dataclass
from typing import Optional

@dataclass
class DecisionRuleParams:
    memo_regex: str
    transaction_priority: int
    account_from: Optional[str] = None
    account_to: Optional[str] = None
    