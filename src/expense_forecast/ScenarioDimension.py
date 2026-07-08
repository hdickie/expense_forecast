#ScenarioDimension.py

# ForecastSet(
#     baseline=base_forecast_definition,
#     dimensions=[
#         ScenarioDimension("School", [...]),
#         ScenarioDimension("Work", [...]),
#         ScenarioDimension("Housing", [...]),
#     ],
# )
#
# ForecastSet:
#     baseline: ForecastDefinition
#     scenarios: list[Scenario]

from expense_forecast.BudgetSet import BudgetSet


class ScenarioDimension:
    
    def __init__(self, name, choices: dict[str, BudgetSet]):
        
        if name is None:
            raise ValueError("Name for ScenarioDimension cannot be None")
        
        if name.strip() == "":
            raise ValueError("Name for ScenarioDimension cannot be empty string")
        
        self.choices = {}
        if choices is not None:
            for choice_name, choice_budget_set in choices.items():
                if choice_name is None:
                    raise ValueError("choice_name for ScenarioDimension cannot be None")
                
                if choice_name == "":
                    raise ValueError("choice_name for ScenarioDimension cannot be empty string")
                
                # TOOD enforce something about budgetSet
                # TODO add to self.choices

    def addChoice(self, label: str, budget_set: BudgetSet):
        if label is None:
            raise ValueError("label for ScenarioDimension::addChoice cannot be None")
        
        if label != "":
            raise ValueError("label for ScenarioDimensio::addChoice cannot be empty string")
        
        # TOOD enforce something about budgetSet
        self.choices[label] = budget_set

    # TODO conceivably I would need dropChoice, but not rn so tabling it for now