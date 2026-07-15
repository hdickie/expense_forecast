"""Milestone-triggered scenario choice changes."""


class ConditionalScenarioTransition:
    """Describe scenario choices activated when a milestone is achieved."""

    def __init__(self, milestone: str, changes: dict):
        if not isinstance(milestone, str) or not milestone.strip():
            raise ValueError("milestone must be a non-empty string")
        if not isinstance(changes, dict) or not changes:
            raise ValueError("changes must be a non-empty mapping")

        normalized_changes = {}
        for dimension_name, choice_name in changes.items():
            if not isinstance(dimension_name, str) or not dimension_name.strip():
                raise ValueError("transition change keys must be non-empty strings")
            if not isinstance(choice_name, str) or not choice_name.strip():
                raise ValueError("transition choice names must be non-empty strings")
            dimension_name = dimension_name.strip()
            if dimension_name in normalized_changes:
                raise ValueError(
                    f"Duplicate ScenarioDimension name {dimension_name!r} in changes"
                )
            normalized_changes[dimension_name] = choice_name.strip()

        self.milestone = milestone
        self.changes = normalized_changes
