"""Ordered collection of conditional scenario transitions."""

from expense_forecast.ConditionalScenarioTransition import (
    ConditionalScenarioTransition,
)


class ConditionalScenarioTransitionSet:
    """Keep transition declaration order and enforce one per milestone."""

    def __init__(self, *transitions):
        if len(transitions) == 1 and isinstance(transitions[0], (list, tuple)):
            transitions = tuple(transitions[0])
        self.transitions = []
        observed_names = set()
        observed_milestones = set()
        for transition in transitions:
            if not isinstance(transition, ConditionalScenarioTransition):
                raise TypeError(
                    "ConditionalScenarioTransitionSet accepts only transitions"
                )
            if transition.name in observed_names:
                raise ValueError(
                    f"Duplicate transition name {transition.name!r}"
                )
            if transition.milestone in observed_milestones:
                raise ValueError(
                    f"Duplicate transition milestone {transition.milestone!r}"
                )
            observed_names.add(transition.name)
            observed_milestones.add(transition.milestone)
            self.transitions.append(transition)

    def __bool__(self):
        return bool(self.transitions)

    def validate(self, milestone_set, line_item_set):
        milestone_names = milestone_set.milestone_names
        for transition in self.transitions:
            if transition.milestone not in milestone_names:
                raise ValueError(
                    f"Unknown transition milestone {transition.milestone!r}"
                )
            for dimension_name, choice_name in transition.changes.items():
                if dimension_name not in line_item_set.scenario_selections:
                    raise ValueError(
                        f"ScenarioDimension {dimension_name!r} has no active choice"
                    )
                known_choices = line_item_set.scenario_dimensions[dimension_name]
                if choice_name not in known_choices:
                    raise ValueError(
                        f"Unknown choice {choice_name!r} for ScenarioDimension "
                        f"{dimension_name!r}"
                    )
