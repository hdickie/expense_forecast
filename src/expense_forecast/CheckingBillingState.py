"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""




from dataclasses import dataclass
from decimal import Decimal

#TODO manual review of CheckingBillingState docstring
@dataclass
class CheckingBillingState:
    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    balance: Decimal
    is_primary: bool

    #TODO manual review of CheckingBillingState.__init__ docstring
    def __init__(self, balance: Decimal, is_primary: bool):
        """
        TODO one-line description of CheckingBillingState.__init__.

        TODO multi-line description of CheckingBillingState.__init__.
        TODO explain how CheckingBillingState.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        balance : float
            TODO one-line description of CheckingBillingState.__init__.balance.

        is_primary : object
            TODO one-line description of CheckingBillingState.__init__.is_primary.

        Returns
        -------
        None
            TODO one-line description of return value of CheckingBillingState.__init__.

        Contract
        --------
        - #TODO contract lines for CheckingBillingState.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for CheckingBillingState.__init__.

        @interface-report: show
        """
        assert balance >= 0
        self.balance = balance

        assert isinstance(is_primary, bool)
        self.is_primary = is_primary
