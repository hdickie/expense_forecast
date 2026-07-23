import pytest
from expense_forecast.Scenario import Scenario
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ScenarioSpace import ScenarioSpace
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.MemoRuleSet import MemoRuleSet

class TestForecastScenarioUnit:

    def test_from_choice_keys_builds_partial_scenario_with_metadata(self):
        food = ScenarioDimension(
            "Food", {"Low": LineItemSet(), "Standard": LineItemSet()}
        )
        housing = ScenarioDimension(
            "Housing", {"Rent": LineItemSet(), "Own": LineItemSet()}
        )
        space = ScenarioSpace(
            LineItemSet(),
            {"Food": food, "Housing": housing},
            MemoRuleSet(),
        )

        scenario = space.from_choice_keys({"Food": "Standard"})

        assert scenario.label == "Food: Standard"
        assert scenario.choices == {"Food": "Standard"}
        assert scenario.line_item_set.scenario_selections == {"Food": "Standard"}
        assert set(scenario.line_item_set.scenario_dimensions) == {"Food"}

    def test_from_choice_keys_uses_dimension_order_for_complete_label(self):
        food = ScenarioDimension("Food", {"Standard": LineItemSet()})
        housing = ScenarioDimension("Housing", {"Rent": LineItemSet()})
        space = ScenarioSpace(
            LineItemSet(),
            {"Food": food, "Housing": housing},
            MemoRuleSet(),
        )

        scenario = space.from_choice_keys(
            {"Housing": "Rent", "Food": "Standard"}
        )

        assert scenario.label == "Food: Standard | Housing: Rent"
        assert scenario.choices == {"Food": "Standard", "Housing": "Rent"}

    def test_from_choice_keys_accepts_empty_mapping(self):
        space = ScenarioSpace(LineItemSet(), {}, MemoRuleSet())

        scenario = space.from_choice_keys({})

        assert scenario.label == "Invariant"
        assert scenario.choices == {}
        assert scenario.line_item_set.scenario_selections == {}

    def test_from_choice_keys_rejects_unknown_dimensions_and_choices(self):
        food = ScenarioDimension("Food", {"Standard": LineItemSet()})
        space = ScenarioSpace(
            LineItemSet(), {"Food": food}, MemoRuleSet()
        )

        with pytest.raises(ValueError, match="Unknown scenario dimension"):
            space.from_choice_keys({"Housing": "Rent"})
        with pytest.raises(ValueError, match="Unknown choice 'Low'"):
            space.from_choice_keys({"Food": "Low"})
        with pytest.raises(TypeError, match="choice_keys must be a mapping"):
            space.from_choice_keys([("Food", "Standard")])

    def test_from_choice_keys_policy_override_and_fluent_replacement_are_isolated(self):
        work = ScenarioDimension(
            "Work", {"RN": LineItemSet(), "Unemployed": LineItemSet()}
        )
        default = ForecastPolicySet(MinimumCheckingBalancePolicy(100, priority=2))
        override = ForecastPolicySet(MinimumCheckingBalancePolicy(500, priority=2))
        replacement = ForecastPolicySet(
            MinimumCheckingBalancePolicy(900, priority=2)
        )
        space = ScenarioSpace(
            LineItemSet(),
            {"Work": work},
            MemoRuleSet(),
            default_policy_set=default,
            policy_overrides=[({"Work": "Unemployed"}, override)],
        )

        selected = space.from_choice_keys({"Work": "Unemployed"})
        configured = selected.with_policy_set(replacement)

        assert selected.policy_set.policies[0].target == 500
        assert configured.policy_set.policies[0].target == 900
        configured.policy_set.policies[0].target = 999
        assert selected.policy_set.policies[0].target == 500
        assert space.scenarios["Unemployed"].policy_set.policies[0].target == 500

    def test_with_policy_set_requires_forecast_policy_set(self):
        scenario = Scenario("Invariant", {}, LineItemSet())

        with pytest.raises(TypeError, match="policy_set must be a ForecastPolicySet"):
            scenario.with_policy_set([])

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
