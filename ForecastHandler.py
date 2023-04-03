


class ForecastHandler:

    def __init__(self):
        pass
        raise NotImplementedError

    def outputHTMLreport(self,E):
        pass
        raise NotImplementedError

    def satisfice(self,AccountSet,BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD):
        raise NotImplementedError

    def calculateImpactOfAddingItemSet(self,AccountSet,Core_BudgetSet, Additional_BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD):
        raise NotImplementedError

    def getRuntimeEstimate(self,AccountSet,BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD):
        raise NotImplementedError

    def calculateCorePlusChooseOne(self,AccountSet,Core_BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD, list_of_budget_sets):
        raise NotImplementedError