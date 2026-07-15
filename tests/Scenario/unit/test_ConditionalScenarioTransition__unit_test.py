import pytest

from expense_forecast.ConditionalScenarioTransition import ConditionalScenarioTransition
from expense_forecast.ConditionalScenarioTransitionSet import ConditionalScenarioTransitionSet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.ScenarioDimension import ScenarioDimension


def test_transition_set_rejects_duplicate_milestone_names():
    food = ScenarioDimension("Food", {"Low": LineItemSet(), "Average": LineItemSet()})
    first = ConditionalScenarioTransition("RN job", {food: "Average"})
    second = ConditionalScenarioTransition("RN job", {food: "Low"})

    with pytest.raises(ValueError, match="Duplicate transition milestone"):
        ConditionalScenarioTransitionSet(first, second)

