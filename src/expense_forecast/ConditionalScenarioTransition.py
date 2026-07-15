"""Milestone-triggered scenario choice changes."""

from expense_forecast.ScenarioDimension import ScenarioDimension


class ConditionalScenarioTransition:
    """Describe scenario choices activated when a milestone is achieved."""

    def __init__(self, milestone: str, changes: dict):
        if not isinstance(milestone, str) or not milestone.strip():
            raise ValueError("milestone must be a non-empty string")
        if not isinstance(changes, dict) or not changes:
            raise ValueError("changes must be a non-empty mapping")

        normalized_changes = {}
        dimensions = {}
        for dimension, choice_name in changes.items():
            if not isinstance(dimension, ScenarioDimension):
                raise TypeError("transition change keys must be ScenarioDimension objects")
            if choice_name not in dimension.choices:
                raise ValueError(
                    f"Unknown choice {choice_name!r} for ScenarioDimension "
                    f"{dimension.name!r}"
                )
            if dimension.name in normalized_changes:
                raise ValueError(
                    f"Duplicate ScenarioDimension name {dimension.name!r} in changes"
                )
            normalized_changes[dimension.name] = choice_name
            dimensions[dimension.name] = dimension

        self.milestone = milestone
        self.changes = normalized_changes
        self.dimensions = dimensions

