"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


#Scenario.py

# Scenario:
#     label: "Nursing school + Weekend CNA"
#     choices: {
#         "School": "Nursing school",
#         "Work": "Weekend CNA"
#     }
#     budget_set: BudgetSet(...)


#TODO DEFER manual review of Scenario docstring
class Scenario:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DEFER manual review of Scenario.__init__ docstring
    def __init__(self, label, choices, budget_set):
        """
        TODO DEFER one-line description of Scenario.__init__.

        TODO DEFER multi-line description of Scenario.__init__.
        TODO DEFER explain how Scenario.__init__ participates in this module.
        TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        label : str
            TODO DEFER one-line description of Scenario.__init__.label.

        choices : object
            TODO DEFER one-line description of Scenario.__init__.choices.

        budget_set : object
            TODO DEFER one-line description of Scenario.__init__.budget_set.

        Returns
        -------
        None

        Contract
        --------
        - #TODO DEFER contract lines for Scenario.__init__.
        - #TODO DEFER document exceptions, mutations, and precision assumptions for Scenario.__init__.

        @interface-report: show
        """
        raise NotImplementedError
