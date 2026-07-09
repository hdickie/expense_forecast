"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import datetime
import pandas as pd
import jsonpickle

from .CreditCardBillingState import CreditCardBillingState
from .LoanBillingState import LoanBillingState
from .SavingsBillingState import SavingsBillingState
from .CheckingBillingState import CheckingBillingState

#TODO manual review of Account docstring
class Account:

    # TODO this seems not to use billing_state appropriately
    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of Account._validate_balances docstring
    @staticmethod
    def _validate_balances(min_balance, balance, max_balance, billing_state):
        #validate that billing_state is consistent with balance, min_balance, max_balance ; was this added by an LLM? I don't recognize it and it not being used it worrying to me
        """
        TODO one-line description of Account._validate_balances.

        TODO multi-line description of Account._validate_balances.
        TODO explain how Account._validate_balances participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        min_balance : float
            TODO one-line description of Account._validate_balances.min_balance.

        balance : float
            TODO one-line description of Account._validate_balances.balance.

        max_balance : float
            TODO one-line description of Account._validate_balances.max_balance.

        billing_state : object
            TODO one-line description of Account._validate_balances.billing_state.

        Returns
        -------
        None
            TODO one-line description of return value of Account._validate_balances.

        Contract
        --------
        - #TODO contract lines for Account._validate_balances.
        - #TODO document exceptions, mutations, and precision assumptions for Account._validate_balances.

        @interface-report: show
        """
        if min_balance > balance:
            raise ValueError(
                f"Account.balance ({balance}) cannot be less than min_balance ({min_balance})"
            )

        if max_balance < balance:
            raise ValueError(
                f"Account.balance ({balance}) cannot be greater than max_balance ({max_balance})"
            )

        if max_balance < min_balance:
            raise ValueError(
                f"Account.max_balance ({max_balance}) cannot be less than min_balance ({min_balance})"
            )

    #TODO manual review of Account._validate_account_type docstring
    @staticmethod
    def _validate_account_type(account_type):
        """
        TODO one-line description of Account._validate_account_type.

        TODO multi-line description of Account._validate_account_type.
        TODO explain how Account._validate_account_type participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_type : object
            TODO one-line description of Account._validate_account_type.account_type.

        Returns
        -------
        None
            TODO one-line description of return value of Account._validate_account_type.

        Contract
        --------
        - #TODO contract lines for Account._validate_account_type.
        - #TODO document exceptions, mutations, and precision assumptions for Account._validate_account_type.

        @interface-report: show
        """
        valid_account_types = [
            "checking",
            "credit",
            "savings",
            "loan"
        ]
        assert account_type == account_type.lower()
        if account_type not in valid_account_types:
            raise ValueError(
                f"Invalid account_type: {account_type}. Must be one of {', '.join(valid_account_types)}"
            )

    #TODO manual review of Account._validate_apr docstring
    @staticmethod
    def _validate_apr(account_type, apr):
        """
        TODO one-line description of Account._validate_apr.

        TODO multi-line description of Account._validate_apr.
        TODO explain how Account._validate_apr participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_type : object
            TODO one-line description of Account._validate_apr.account_type.

        apr : float
            TODO one-line description of Account._validate_apr.apr.

        Returns
        -------
        None
            TODO one-line description of return value of Account._validate_apr.

        Contract
        --------
        - #TODO contract lines for Account._validate_apr.
        - #TODO document exceptions, mutations, and precision assumptions for Account._validate_apr.

        @interface-report: show
        """
        account_types_that_require_apr = [
            "credit",
            "loan",
            "savings",
        ]
        if account_type in account_types_that_require_apr and apr is not None:
            assert apr >= 0
        elif account_type in account_types_that_require_apr and apr is None:
            raise ValueError(
                f"Account.apr is required for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_apr and apr is not None:
            raise ValueError(
                f"Account.apr should be None for account_type '{account_type}'"
            )

    #TODO manual review of Account._validate_interest_cadence docstring
    @staticmethod
    def _validate_interest_cadence(account_type, interest_cadence):
        """
        TODO one-line description of Account._validate_interest_cadence.

        TODO multi-line description of Account._validate_interest_cadence.
        TODO explain how Account._validate_interest_cadence participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_type : object
            TODO one-line description of Account._validate_interest_cadence.account_type.

        interest_cadence : object
            TODO one-line description of Account._validate_interest_cadence.interest_cadence.

        Returns
        -------
        None
            TODO one-line description of return value of Account._validate_interest_cadence.

        Contract
        --------
        - #TODO contract lines for Account._validate_interest_cadence.
        - #TODO document exceptions, mutations, and precision assumptions for Account._validate_interest_cadence.

        @interface-report: show
        """
        account_types_that_require_interest_cadence = [
            "credit",
            "loan",
            "savings",
        ]
        if account_type in account_types_that_require_interest_cadence and interest_cadence not in ['daily','monthly']:
            raise ValueError(
                f"Account.interest_cadence should be daily or monthly for account_type '{account_type}'"
            )
        elif account_type not in account_types_that_require_interest_cadence and interest_cadence is not None:
            raise ValueError(
                f"Account.interest_cadence should be None for account_type '{account_type}'"
            )

    #TODO manual review of Account._validate_interest_type docstring
    @staticmethod
    def _validate_interest_type(account_type, interest_type):
        """
        TODO one-line description of Account._validate_interest_type.

        TODO multi-line description of Account._validate_interest_type.
        TODO explain how Account._validate_interest_type participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_type : object
            TODO one-line description of Account._validate_interest_type.account_type.

        interest_type : object
            TODO one-line description of Account._validate_interest_type.interest_type.

        Returns
        -------
        None
            TODO one-line description of return value of Account._validate_interest_type.

        Contract
        --------
        - #TODO contract lines for Account._validate_interest_type.
        - #TODO document exceptions, mutations, and precision assumptions for Account._validate_interest_type.

        @interface-report: show
        """
        if account_type in ["loan", "credit", "savings"] and interest_type is None:
            raise ValueError(
                f"Account.interest_type is required for account_type '{account_type}'"
            )
        elif account_type in ["loan", "credit", "savings"] and interest_type not in ["simple", "compound"]:
            raise ValueError(
                f"Account.interest_type should be simple or compound for account_type '{account_type}'"
            )
        elif account_type in ["checking"] and interest_type is not None:
            raise ValueError(
                f"Account.interest_type should be None for account_type '{account_type}'"
            )


    #TODO manual review of Account._validate_primary_checking_ind docstring
    @staticmethod
    def _validate_primary_checking_ind(account_type, primary_checking_ind):
        """
        TODO one-line description of Account._validate_primary_checking_ind.

        TODO multi-line description of Account._validate_primary_checking_ind.
        TODO explain how Account._validate_primary_checking_ind participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_type : object
            TODO one-line description of Account._validate_primary_checking_ind.account_type.

        primary_checking_ind : object
            TODO one-line description of Account._validate_primary_checking_ind.primary_checking_ind.

        Returns
        -------
        None
            TODO one-line description of return value of Account._validate_primary_checking_ind.

        Contract
        --------
        - #TODO contract lines for Account._validate_primary_checking_ind.
        - #TODO document exceptions, mutations, and precision assumptions for Account._validate_primary_checking_ind.

        @interface-report: show
        """
        if account_type != 'checking' and primary_checking_ind is not None:
            raise ValueError(
                f"Account.primary_checking_ind should be None for account_type '{account_type}'"
            )
        elif account_type == 'checking' and primary_checking_ind is None:
            raise TypeError(
                f"Account.primary_checking_ind must be a bool Value was: {primary_checking_ind}"
            )
        elif account_type == 'checking' and primary_checking_ind is not None:
            assert isinstance(primary_checking_ind,bool)

    #TODO manual review of Account._validate_billing_state docstring
    @staticmethod
    def _validate_billing_state(account_type, billing_state):
        """
        TODO one-line description of Account._validate_billing_state.

        TODO multi-line description of Account._validate_billing_state.
        TODO explain how Account._validate_billing_state participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_type : object
            TODO one-line description of Account._validate_billing_state.account_type.

        billing_state : object
            TODO one-line description of Account._validate_billing_state.billing_state.

        Returns
        -------
        None
            TODO one-line description of return value of Account._validate_billing_state.

        Contract
        --------
        - #TODO contract lines for Account._validate_billing_state.
        - #TODO document exceptions, mutations, and precision assumptions for Account._validate_billing_state.

        @interface-report: show
        """
        if account_type == "credit":
            assert isinstance(billing_state, CreditCardBillingState)
        elif account_type == "loan":
            assert isinstance(billing_state, LoanBillingState)
        elif account_type == "savings":
            assert isinstance(billing_state, SavingsBillingState)
        elif account_type == "checking":
            assert isinstance(billing_state, CheckingBillingState)
        else:
            raise ValueError(
                f"Account.billing_state should not be None"
            )

    #TODO manual review of Account.__init__ docstring
    def __init__(self, name, balance, min_balance, max_balance, account_type, **kwargs):
        # checking, credit, principal balance, interest, investment
        # parameters are expected to be correctly typed. wont cast but will error

        """
        TODO one-line description of Account.__init__.

        TODO multi-line description of Account.__init__.
        TODO explain how Account.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        name : str
            TODO one-line description of Account.__init__.name.

        balance : float
            TODO one-line description of Account.__init__.balance.

        min_balance : float
            TODO one-line description of Account.__init__.min_balance.

        max_balance : float
            TODO one-line description of Account.__init__.max_balance.

        account_type : object
            TODO one-line description of Account.__init__.account_type.

        **kwargs : dict
            TODO one-line description of Account.__init__.kwargs.

        Returns
        -------
        None
            TODO one-line description of return value of Account.__init__.

        Contract
        --------
        - #TODO contract lines for Account.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for Account.__init__.

        @interface-report: show
        """
        allowed_kwargs = ['billing_start_date', 'interest_type',  'interest_cadence', 'apr',
                          'primary_checking_ind', 'billing_state']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        self.name = name
        # self._validate_account_name(account_type, self.name)

        self.balance = balance
        self.min_balance = min_balance
        self.max_balance = max_balance

        self.account_type = account_type
        self._validate_account_type(self.account_type)

        self.billing_state = kwargs.get('billing_state', None)
        self._validate_billing_state(self.account_type, self.billing_state)
        self._validate_balances(self.min_balance, self.balance, self.max_balance, self.billing_state)

        self.billing_start_date = getattr(self.billing_state, "billing_cycle_start_date", None)
        self.interest_type = getattr(self.billing_state, "interest_type", None)
        self.apr = getattr(self.billing_state, "apr", None)
        self.interest_cadence = getattr(self.billing_state, "interest_cadence", None)
        self.minimum_payment = getattr(self.billing_state, "minimum_payment", None)
        self.primary_checking_ind = getattr(self.billing_state, "is_primary", None)

    #TODO manual review of Account.to_json docstring
    def to_json(self):
        """
        TODO one-line description of Account.to_json.

        TODO multi-line description of Account.to_json.
        TODO explain how Account.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that Account.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of Account.to_json.

        Contract
        --------
        - #TODO contract lines for Account.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for Account.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)

    #TODO manual review of Account.__str__ docstring
    def __str__(self):
        """
        TODO one-line description of Account.__str__.

        TODO multi-line description of Account.__str__.
        TODO explain how Account.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that Account.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of Account.__str__.

        Contract
        --------
        - #TODO contract lines for Account.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for Account.__str__.

        @interface-report: show
        """
        return pd.DataFrame(
            {
                "Name": [self.name],
                "Balance": [self.balance],
                "Min_Balance": [self.min_balance],
                "Max_Balance": [self.max_balance],
                "Account_Type": [self.account_type],
                "Billing_Start_Date": [self.billing_start_date],
                "Interest_Type": [self.interest_type],
                "APR": [self.apr],
                "Interest_Cadence": [self.interest_cadence],
                "Minimum_Payment": [self.minimum_payment],
                "Primary_Checking_Ind": [self.primary_checking_ind],
            }
        ).to_string()


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()
