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
from expense_forecast.ScenarioChoice import ScenarioChoice


logger = logging.getLogger(__name__)


#TODO DOC manual review of ScenarioDimension docstring
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
    def __init__(self, name, choices=None):

        """
        #TODO DEFER one-line description of ScenarioDimension.__init__.

        #TODO DEFER multi-line description of ScenarioDimension.__init__.
        #TODO DEFER explain how ScenarioDimension.__init__ participates in this module.
        #TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        name : str
            #TODO DEFER one-line description of ScenarioDimension.__init__.name.

        choices : object
            #TODO DEFER one-line description of ScenarioDimension.__init__.choices.

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
        # Authored choice changes live on the dimension. Materializing the
        # dimension copies this metadata into a LineItemSet; it never mutates
        # the choice templates themselves.
        self.scenario_timelines = []
        if choices is not None:
            for choice_name, choice_value in choices.items():
                if choice_name is None:
                    raise ValueError("choice_name for ScenarioDimension cannot be None")

                if not isinstance(choice_name, str) or choice_name.strip() == "":
                    raise ValueError("choice_name for ScenarioDimension cannot be empty string")
                self.choices[choice_name] = ScenarioChoice.normalize(
                    choice_value
                )

    def _validate_timeline_choice(self, choice_name: str) -> None:
        if choice_name not in self.choices:
            raise ValueError(
                f"Unknown choice {choice_name!r} for "
                f"ScenarioDimension {self.name!r}"
            )

    @staticmethod
    def _validate_timeline_date(value, parameter_name: str) -> None:
        if not isinstance(value, datetime.date):
            raise TypeError(
                f"{parameter_name} must be a datetime.date"
            )

    def set_default(
        self,
        effective_date: datetime.date,
        choice_name: str,
    ) -> "ScenarioDimension":
        """Set the first dated choice without changing its line-item template."""
        self._validate_timeline_date(effective_date, "effective_date")
        self._validate_timeline_choice(choice_name)
        if self.scenario_timelines:
            raise ValueError(
                f"ScenarioDimension {self.name!r} already has a default choice"
            )

        self.scenario_timelines.append({
            "choice": choice_name,
            "effective_date": effective_date,
            "end_date": None,
        })
        return self

    def change_choice_on_date(
        self,
        effective_date: datetime.date,
        choice_name: str,
    ) -> "ScenarioDimension":
        """Activate a different choice at the start of ``effective_date``."""
        self._validate_timeline_date(effective_date, "effective_date")
        self._validate_timeline_choice(choice_name)
        if not self.scenario_timelines:
            raise ValueError(
                "set_default must be called before change_choice_on_date"
            )

        previous = self.scenario_timelines[-1]
        if effective_date <= previous["effective_date"]:
            raise ValueError(
                "choice-change dates must be strictly increasing"
            )
        if choice_name == previous["choice"]:
            raise ValueError(
                f"Choice {choice_name!r} is already active"
            )

        previous["end_date"] = (
            effective_date - datetime.timedelta(days=1)
        )
        self.scenario_timelines.append({
            "choice": choice_name,
            "effective_date": effective_date,
            "end_date": None,
        })
        return self

    def to_line_item_set(
        self,
        end_date: datetime.date,
    ) -> LineItemSet:
        """Materialize the authored timeline through an inclusive end date."""
        self._validate_timeline_date(end_date, "end_date")
        if not self.scenario_timelines:
            raise ValueError(
                "set_default must be called before to_line_item_set"
            )
        if end_date < self.scenario_timelines[0]["effective_date"]:
            raise ValueError(
                "end_date must be on or after the default effective date"
            )

        materialized = None
        for index, entry in enumerate(self.scenario_timelines):
            segment_start = entry["effective_date"]
            if segment_start > end_date:
                break

            next_start = (
                self.scenario_timelines[index + 1]["effective_date"]
                if index + 1 < len(self.scenario_timelines)
                else None
            )
            segment_end = (
                min(end_date, next_start - datetime.timedelta(days=1))
                if next_start is not None
                else end_date
            )
            segment = self.choice_for_date_range(
                entry["choice"], segment_start, segment_end
            )
            materialized = (
                segment if materialized is None else materialized + segment
            )

        # At least the default entry is active because the range check above
        # excludes an end date before it.
        return materialized

    #TODO DOC manual review of ScenarioDimension.addChoice docstring
    def addChoice(self, label: str, choice):
        """
        #TODO DOC one-line description of ScenarioDimension.addChoice.

        #TODO DOC multi-line description of ScenarioDimension.addChoice.
        #TODO DOC explain how ScenarioDimension.addChoice participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        label : str
            #TODO DOC one-line description of ScenarioDimension.addChoice.label.

        line_item_set : object
            #TODO DOC one-line description of ScenarioDimension.addChoice.line_item_set.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ScenarioDimension.addChoice.

        Contract
        --------
        - #TODO DOC contract lines for ScenarioDimension.addChoice.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ScenarioDimension.addChoice.

        @interface-report: show
        """
        if label is None:
            raise ValueError("label for ScenarioDimension::addChoice cannot be None")

        if not isinstance(label, str) or label.strip() == "":
            raise ValueError("label for ScenarioDimensio::addChoice cannot be empty string")
        if label in self.choices:
            raise ValueError(f"Duplicate choice {label!r}")
        self.choices[label] = ScenarioChoice.normalize(choice)

    def select(
        self, choice_name: str, effective_date: datetime.date = None
    ) -> LineItemSet:
        """Return the chosen line items with active scenario metadata."""
        if choice_name not in self.choices:
            raise ValueError(
                f"Unknown choice {choice_name!r} for ScenarioDimension {self.name!r}"
            )
        if effective_date is not None and not isinstance(effective_date, datetime.date):
            raise TypeError("effective_date must be a datetime.date or None")
        items = copy.deepcopy(
            self.choices[choice_name].line_item_set.line_items
        )
        if effective_date is not None:
            for item in items:
                if item.interval != "once":
                    item.start_date = effective_date
                    item.recurrence_anchor = effective_date
        return LineItemSet(
            items,
            scenario_selections=(
                {self.name: choice_name} if effective_date is None else {}
            ),
            scenario_dimensions={self.name: copy.deepcopy(self.choices)},
            scenario_timelines=(
                {self.name: [{
                    "choice": choice_name,
                    "effective_date": effective_date,
                    "end_date": None,
                }]}
                if effective_date is not None else {}
            ),
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
        for line_item in copy.deepcopy(
            self.choices[choice_name].line_item_set.line_items
        ):
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

        for line_item in scheduled_items:
            if line_item.interval != "once":
                line_item.recurrence_anchor = start_date
        return LineItemSet(
            scheduled_items,
            scenario_dimensions={self.name: copy.deepcopy(self.choices)},
            scenario_timelines={self.name: [{
                "choice": choice_name,
                "effective_date": start_date,
                "end_date": end_date,
                "recurrence_keys": [
                    item.recurrence_key for item in scheduled_items
                    if item.interval != "once"
                ],
            }]},
        )

    # TODO DEFER conceivably I would need dropChoice, but not rn so tabling it for now
