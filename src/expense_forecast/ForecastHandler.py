from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.ForecastSet import ForecastSet
from expense_forecast.MemoRuleSet import MemoRuleSet 
from expense_forecast.MilestoneSet import MilestoneSet 


class ForecastHandler:
    def __init__(self):
        self.forecast_set = None
        self.account_set = None
        self.budget_set = None
        self.memo_rule_set = None
        self.milestone_set = None

    def load_forecast_set(self, forecast_set: ForecastSet):
        self.forecast_set = forecast_set

    def load_account_set(self, account_set: AccountSet):
        self.account_set = account_set

    def load_budget_set(self, budget_set: BudgetSet):
        self.budget_set = budget_set

    def load_memo_rule_set(self, memo_rule_set: MemoRuleSet):
        self.memo_rule_set = memo_rule_set

    def load_milestone_set(self, milestone_set: MilestoneSet):
        self.milestone_set = milestone_set