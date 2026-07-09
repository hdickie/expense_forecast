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

from expense_forecast.BudgetSet import BudgetSet


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
    #TODO manual review of ScenarioDimension.__init__ docstring
    def __init__(self, name, choices: dict[str, BudgetSet]):

        """
        TODO one-line description of ScenarioDimension.__init__.

        TODO multi-line description of ScenarioDimension.__init__.
        TODO explain how ScenarioDimension.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        name : str
            TODO one-line description of ScenarioDimension.__init__.name.

        choices : object
            TODO one-line description of ScenarioDimension.__init__.choices.

        Returns
        -------
        None
            TODO one-line description of return value of ScenarioDimension.__init__.

        Contract
        --------
        - #TODO contract lines for ScenarioDimension.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for ScenarioDimension.__init__.

        @interface-report: show
        """
        if name is None:
            raise ValueError("Name for ScenarioDimension cannot be None")

        if name.strip() == "":
            raise ValueError("Name for ScenarioDimension cannot be empty string")

        self.choices = {}
        if choices is not None:
            for choice_name, choice_budget_set in choices.items():
                if choice_name is None:
                    raise ValueError("choice_name for ScenarioDimension cannot be None")

                if choice_name == "":
                    raise ValueError("choice_name for ScenarioDimension cannot be empty string")

                # TOOD enforce something about budgetSet
                # TODO add to self.choices

    #TODO manual review of ScenarioDimension.addChoice docstring
    def addChoice(self, label: str, budget_set: BudgetSet):
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

        if label != "":
            raise ValueError("label for ScenarioDimensio::addChoice cannot be empty string")

        # TOOD enforce something about budgetSet
        self.choices[label] = budget_set

    # TODO conceivably I would need dropChoice, but not rn so tabling it for now
