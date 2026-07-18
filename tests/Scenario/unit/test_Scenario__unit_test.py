import pytest
from expense_forecast.Scenario import Scenario
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ScenarioSpace import ScenarioSpace
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.MemoRuleSet import MemoRuleSet

class TestForecastScenarioUnit:

    def test_scenario_space_resolves_default_and_exact_policy_overrides(self):
        work = ScenarioDimension(
            "Work", {"RN": LineItemSet(), "Unemployed": LineItemSet()}
        )
        default = ForecastPolicySet(MinimumCheckingBalancePolicy(100, priority=2))
        override = ForecastPolicySet(MinimumCheckingBalancePolicy(500, priority=2))

        space = ScenarioSpace(
            LineItemSet(),
            {"Work": work},
            MemoRuleSet(),
            default_policy_set=default,
            policy_overrides=[({"Work": "Unemployed"}, override)],
        )

        assert isinstance(space.scenarios["RN"], Scenario)
        assert space.scenarios["RN"].policy_set.policies[0].target == 100
        assert space.scenarios["Unemployed"].policy_set.policies[0].target == 500
        space.scenarios["RN"].policy_set.policies[0].target = 999
        assert space.scenarios["Unemployed"].policy_set.policies[0].target == 500

    # __init__(self, label, choices, line_item_set)
    @pytest.mark.skip
    def test_scenario__valid_inputs(self):
         
        S = Scenario('One Specific Forecast',
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     LineItemSet())
        
    @pytest.mark.skip
    def test_scenario__invalid_name(self):
        with pytest.raises(ValueError):
            S = Scenario(None,
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     LineItemSet())
            
        with pytest.raises(ValueError):
            S = Scenario("",
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     LineItemSet())
        
    @pytest.mark.skip
    def test_scenario__empty_line_item_set(self):
        with pytest.raises(ValueError):
            S = Scenario("One Specific Forecast",
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     LineItemSet())
            
    @pytest.mark.skip
    def test_scenario__none_line_item_set(self):
        with pytest.raises(ValueError):
            S = Scenario("One Specific Forecast",
                     ['Choice 1A','Choice 2B','Choice 3C'],
                     None)
            
    @pytest.mark.skip
    def test_scenario__empty_choice_list(self):
        with pytest.raises(ValueError):
            S = Scenario("One Specific Forecast",
                     [],
                     LineItemSet())
            
    @pytest.mark.skip
    def test_scenario_dimension__valid_inputs(self):

        SD = ScenarioDimension(name="School")

        SD = ScenarioDimension(name="School",
                               choices = {"No school":LineItemSet(),
                                          "Nursing school":LineItemSet()})
    @pytest.mark.skip
    def test_scenario_dimension__invalid_inputs(self):
        #empty string is not valid
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name="",
                               choices = {"No school":LineItemSet(),
                                          "Nursing school":LineItemSet()})

        #None is not valid
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name=None,
                               choices = {"No school":LineItemSet(),
                                          "Nursing school":LineItemSet()})
            
        #None is not valid
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name="Dimension Name",
                               choices = {"No school":None,
                                          "Nursing school":LineItemSet()})
            
        #duplicate choices
        with pytest.raises(ValueError):
            SD = ScenarioDimension(name="Dimension Name",
                               choices = {"No school":LineItemSet(),
                                          "No school":LineItemSet()})
