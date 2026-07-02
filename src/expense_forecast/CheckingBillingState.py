

from dataclasses import dataclass
from decimal import Decimal

@dataclass
class CheckingBillingState:
    balance: Decimal
    is_primary: bool
    
    def __init__(self, balance: Decimal, is_primary: bool):
        assert balance >= 0
        self.balance = balance

        assert isinstance(is_primary, bool)
        self.is_primary = is_primary