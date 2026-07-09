"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import pandas as pd
import jsonpickle


#TODO manual review of AccountMilestone docstring
class AccountMilestone:
    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of AccountMilestone.__init__ docstring
    def __init__(self, Milestone_Name, Account_Name, Min_Balance, Max_Balance):
        """
        TODO one-line description of AccountMilestone.__init__.

        TODO multi-line description of AccountMilestone.__init__.
        TODO explain how AccountMilestone.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        Milestone_Name : object
            TODO one-line description of AccountMilestone.__init__.Milestone_Name.

        Account_Name : object
            TODO one-line description of AccountMilestone.__init__.Account_Name.

        Min_Balance : object
            TODO one-line description of AccountMilestone.__init__.Min_Balance.

        Max_Balance : object
            TODO one-line description of AccountMilestone.__init__.Max_Balance.

        Returns
        -------
        None
            TODO one-line description of return value of AccountMilestone.__init__.

        Contract
        --------
        - #TODO contract lines for AccountMilestone.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for AccountMilestone.__init__.

        @interface-report: show
        """
        self.milestone_name = Milestone_Name
        assert self.milestone_name is not None

        self.account_name = Account_Name
        assert self.account_name is not None
        assert ';' not in self.account_name

        self.min_balance = float(Min_Balance)
        self.max_balance = float(Max_Balance)

        assert Min_Balance <= Max_Balance

    #TODO manual review of AccountMilestone.__str__ docstring
    def __str__(self):
        """
        TODO one-line description of AccountMilestone.__str__.

        TODO multi-line description of AccountMilestone.__str__.
        TODO explain how AccountMilestone.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that AccountMilestone.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of AccountMilestone.__str__.

        Contract
        --------
        - #TODO contract lines for AccountMilestone.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for AccountMilestone.__str__.

        @interface-report: show
        """
        return pd.DataFrame(
            {
                "Milestone_Name": [self.milestone_name],
                "Account_Name": [self.account_name],
                "Min_Balance": [self.min_balance],
                "Max_Balance": [self.max_balance],
            }
        ).to_string()

    #TODO manual review of AccountMilestone.to_json docstring
    def to_json(self):
        """
        TODO one-line description of AccountMilestone.to_json.

        TODO multi-line description of AccountMilestone.to_json.
        TODO explain how AccountMilestone.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that AccountMilestone.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of AccountMilestone.to_json.

        Contract
        --------
        - #TODO contract lines for AccountMilestone.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for AccountMilestone.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)
