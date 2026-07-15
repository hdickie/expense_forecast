"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


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

import copy
import datetime
import logging

from expense_forecast.LineItemSet import LineItemSet


logger = logging.getLogger(__name__)


#TODO manual review of ScenarioDimension docstring
class ScenarioDimension:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DEFER manual review of ScenarioDimension.__init__ docstring
    def __init__(self, name, choices: dict[str, LineItemSet] = None):

        """
        TODO DEFER one-line description of ScenarioDimension.__init__.

        TODO DEFER multi-line description of ScenarioDimension.__init__.
        TODO DEFER explain how ScenarioDimension.__init__ participates in this module.
        TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        name : str
            TODO DEFER one-line description of ScenarioDimension.__init__.name.

        choices : object
            TODO DEFER one-line description of ScenarioDimension.__init__.choices.

        Returns
        -------
        None

        Contract
        --------
        - #TODO DEFER contract lines for ScenarioDimension.__init__.
        - #TODO DEFER document exceptions, mutations, and precision assumptions for ScenarioDimension.__init__.

        @interface-report: show
        """
        if name is None:
            raise ValueError("Name for ScenarioDimension cannot be None")

        if name.strip() == "":
            raise ValueError("Name for ScenarioDimension cannot be empty string")

        self.name = name.strip()
        self.choices = {}
        if choices is not None:
            for choice_name, choice_budget_set in choices.items():
                if choice_name is None:
                    raise ValueError("choice_name for ScenarioDimension cannot be None")

                if not isinstance(choice_name, str) or choice_name.strip() == "":
                    raise ValueError("choice_name for ScenarioDimension cannot be empty string")
                if not isinstance(choice_budget_set, LineItemSet):
                    raise TypeError(
                        "ScenarioDimension choices must be LineItemSet instances"
                    )
                if choice_budget_set.scenario_selections:
                    raise ValueError(
                        "ScenarioDimension choices cannot contain scenario selections"
                    )
                self.choices[choice_name] = copy.deepcopy(choice_budget_set)

    #TODO manual review of ScenarioDimension.addChoice docstring
    def addChoice(self, label: str, budget_set: LineItemSet):
        """
        TODO one-line description of ScenarioDimension.addChoice.

        TODO multi-line description of ScenarioDimension.addChoice.
        TODO explain how ScenarioDimension.addChoice participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        label : str
            TODO one-line description of ScenarioDimension.addChoice.label.

        budget_set : object
            TODO one-line description of ScenarioDimension.addChoice.budget_set.

        Returns
        -------
        object
            TODO one-line description of return value of ScenarioDimension.addChoice.

        Contract
        --------
        - #TODO contract lines for ScenarioDimension.addChoice.
        - #TODO document exceptions, mutations, and precision assumptions for ScenarioDimension.addChoice.

        @interface-report: show
        """
        if label is None:
            raise ValueError("label for ScenarioDimension::addChoice cannot be None")

        if not isinstance(label, str) or label.strip() == "":
            raise ValueError("label for ScenarioDimensio::addChoice cannot be empty string")
        if not isinstance(budget_set, LineItemSet):
            raise TypeError("budget_set must be a LineItemSet")
        if label in self.choices:
            raise ValueError(f"Duplicate choice {label!r}")
        if budget_set.scenario_selections:
            raise ValueError("ScenarioDimension choices cannot contain scenario selections")
        self.choices[label] = copy.deepcopy(budget_set)

    def select(self, choice_name: str) -> LineItemSet:
        """Return the chosen line items with active scenario metadata."""
        if choice_name not in self.choices:
            raise ValueError(
                f"Unknown choice {choice_name!r} for ScenarioDimension {self.name!r}"
            )
        return LineItemSet(
            copy.deepcopy(self.choices[choice_name].line_items),
            scenario_selections={self.name: choice_name},
            scenario_dimensions={self.name: self.choices},
        )

    def choice_for_date_range(
        self,
        choice_name: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> LineItemSet:
        """Return a choice template scheduled within an inclusive date range.

        Recurring line items receive the requested start and end dates. Fixed
        ``once`` items retain their original date when it is within the range;
        otherwise they are omitted with a warning. The returned set deliberately
        has no active scenario metadata, allowing dated choices from the same
        dimension to be combined. This method assigns dates only and does not
        calculate amounts such as annual raises.
        """
        if choice_name not in self.choices:
            raise ValueError(
                f"Unknown choice {choice_name!r} for ScenarioDimension {self.name!r}"
            )
        if not isinstance(start_date, datetime.date):
            raise TypeError("start_date must be a datetime.date")
        if not isinstance(end_date, datetime.date):
            raise TypeError("end_date must be a datetime.date")
        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date")

        scheduled_items = []
        for line_item in copy.deepcopy(self.choices[choice_name].line_items):
            if line_item.interval == "once":
                if start_date <= line_item.start_date <= end_date:
                    scheduled_items.append(line_item)
                else:
                    logger.warning(
                        "Dropping one-time line item %r dated %s from "
                        "ScenarioDimension %r choice %r because it is outside "
                        "the requested range %s to %s",
                        line_item.memo,
                        line_item.start_date,
                        self.name,
                        choice_name,
                        start_date,
                        end_date,
                    )
                continue

            line_item.start_date = start_date
            line_item.end_date = end_date
            scheduled_items.append(line_item)

        return LineItemSet(scheduled_items)

    # TODO DEFER conceivably I would need dropChoice, but not rn so tabling it for now
