import pytest

from expense_forecast.ConditionalScenarioTransition import ConditionalScenarioTransition
from expense_forecast.ConditionalScenarioTransitionSet import ConditionalScenarioTransitionSet


def test_transition_set_rejects_duplicate_milestone_names():
    first = ConditionalScenarioTransition("First", "RN job", {"Food": "Average"})
    second = ConditionalScenarioTransition("Second", "RN job", {"Food": "Low"})

    with pytest.raises(ValueError, match="Duplicate transition milestone"):
        ConditionalScenarioTransitionSet(first, second)


def test_transition_set_rejects_duplicate_transition_names():
    first = ConditionalScenarioTransition("RN change", "RN job", {"Food": "Average"})
    second = ConditionalScenarioTransition("RN change", "Promotion", {"Food": "Low"})

    with pytest.raises(ValueError, match="Duplicate transition name"):
        ConditionalScenarioTransitionSet(first, second)


def test_transition_accepts_dimension_names_and_normalizes_whitespace():
    transition = ConditionalScenarioTransition("RN transition", "RN job", {" Food ": " Average "})

    assert transition.changes == {"Food": "Average"}
    assert transition.name == "RN transition"


@pytest.mark.parametrize("changes", [{None: "Average"}, {"": "Average"}])
def test_transition_rejects_invalid_dimension_names(changes):
    with pytest.raises(ValueError, match="keys must be non-empty strings"):
        ConditionalScenarioTransition("RN transition", "RN job", changes)


@pytest.mark.parametrize("changes", [{"Food": None}, {"Food": ""}])
def test_transition_rejects_invalid_choice_names(changes):
    with pytest.raises(ValueError, match="choice names must be non-empty strings"):
        ConditionalScenarioTransition("RN transition", "RN job", changes)


def test_transition_rejects_duplicate_normalized_dimension_names():
    with pytest.raises(ValueError, match="Duplicate ScenarioDimension name"):
        ConditionalScenarioTransition(
            "RN transition", "RN job", {"Food": "Average", " Food ": "Low"}
        )
