"""Shared forecast-policy contracts."""

import math
from decimal import Decimal
from numbers import Real


class ForecastPolicyError(RuntimeError):
    """Raised when a policy configured with ``on_unmet='fail'`` is unmet."""


class ForecastPolicy:
    """Base validation and identity for prioritized forecast policies."""

    policy_name = "forecast_policy"

    def __init__(self, priority, on_unmet="warn"):
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
            raise ValueError("policy priority must be an integer greater than or equal to 1")
        if on_unmet not in {"warn", "fail"}:
            raise ValueError("on_unmet must be 'warn' or 'fail'")
        self.priority = priority
        self.on_unmet = on_unmet

    @property
    def policy_key(self):
        return self.policy_name

    @staticmethod
    def validate_amount(value, name):
        if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
            raise TypeError(f"{name} must be a finite, non-negative number")
        if not math.isfinite(float(value)) or value < 0:
            raise ValueError(f"{name} must be a finite, non-negative number")

