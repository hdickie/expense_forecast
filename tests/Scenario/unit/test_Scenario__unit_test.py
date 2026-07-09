import pytest
from expense_forecast.Scenario import Scenario
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.ScenarioDimension import ScenarioDimension

class TestForecastScenarioUnit:

    # __init__(self, label, choices, budget_set)
    @pytest.mark.skip
    def test_scenario__valid_inputs(self):
         
        S = Scenario('One Specific Forecast',
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     BudgetSet())
        
    @pytest.mark.skip
    def test_scenario__invalid_name(self):
        with pytest.raises(ValueError):
            S = Scenario(None,
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     BudgetSet())
            
        with pytest.raises(ValueError):
            S = Scenario("",
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     BudgetSet())
        
    @pytest.mark.skip
    def test_scenario__empty_budget_set(self):
        with pytest.raises(ValueError):
            S = Scenario("One Specific Forecast",
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     BudgetSet())
            
    @pytest.mark.skip
    def test_scenario__none_budget_set(self):
        with pytest.raises(ValueError):
            S = Scenario("One Specific Forecast",
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     None)
            
    @pytest.mark.skip
    def test_scenario__empty_choice_list(self):
        with pytest.raises(ValueError):
            S = Scenario("One Specific Forecast",
                     [],
                     BudgetSet())
            
    @pytest.mark.skip
    def test_scenario_dimension__valid_inputs(self):

        SD = ScenarioDimension(name="School")

        SD = ScenarioDimension(name="School",
                               choices = {"No school":BudgetSet(),
                                          "Nursing school":BudgetSet()})
    @pytest.mark.skip
    def test_scenario_dimension__invalid_inputs(self):
        #empty string is not valid
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name="",
                               choices = {"No school":BudgetSet(),
                                          "Nursing school":BudgetSet()})

        #None is not valid
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name=None,
                               choices = {"No school":BudgetSet(),
                                          "Nursing school":BudgetSet()})
            
        #None is not valid
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name="Dimension Name",
                               choices = {"No school":None,
                                          "Nursing school":BudgetSet()})
            
        #duplicate choices
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name="Dimension Name",
                               choices = {"No school":BudgetSet(),
                                          "No school":BudgetSet()})
