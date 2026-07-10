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
from datetime import date
from decimal import Decimal


#TODO manual review of SavingsBillingState docstring
@dataclass
class SavingsBillingState:
    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    billing_cycle_start_date: date
    previous_statement_balance: Decimal
    current_statement_balance: Decimal
    billing_cycle_payment_balance: Decimal
    minimum_payment: Decimal
    apr: Decimal

    #TODO manual review of SavingsBillingState.__init__ docstring
    def __init__(self, billing_cycle_start_date: date, previous_statement_balance: Decimal,
                  current_statement_balance: Decimal, billing_cycle_payment_balance: Decimal,
                  minimum_payment: Decimal,
                  interest_type: str,
                  interest_interval: str,
                  apr: Decimal
                  ):
        """
        TODO one-line description of SavingsBillingState.__init__.

        TODO multi-line description of SavingsBillingState.__init__.
        TODO explain how SavingsBillingState.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        billing_cycle_start_date : object
            TODO one-line description of SavingsBillingState.__init__.billing_cycle_start_date.

        previous_statement_balance : object
            TODO one-line description of SavingsBillingState.__init__.previous_statement_balance.

        current_statement_balance : object
            TODO one-line description of SavingsBillingState.__init__.current_statement_balance.

        billing_cycle_payment_balance : object
            TODO one-line description of SavingsBillingState.__init__.billing_cycle_payment_balance.

        minimum_payment : float
            TODO one-line description of SavingsBillingState.__init__.minimum_payment.

        interest_type : object
            TODO one-line description of SavingsBillingState.__init__.interest_type.

        interest_interval : object
            TODO one-line description of SavingsBillingState.__init__.interest_interval.

        apr : float
            TODO one-line description of SavingsBillingState.__init__.apr.

        Returns
        -------
        None
            TODO one-line description of return value of SavingsBillingState.__init__.

        Contract
        --------
        - #TODO contract lines for SavingsBillingState.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for SavingsBillingState.__init__.

        @interface-report: show
        """
        self.billing_cycle_start_date = billing_cycle_start_date
        assert previous_statement_balance >= 0
        self.previous_statement_balance = previous_statement_balance
        assert current_statement_balance >= 0
        self.current_statement_balance = current_statement_balance
        assert billing_cycle_payment_balance >= 0
        self.billing_cycle_payment_balance = billing_cycle_payment_balance
        assert minimum_payment >= 0
        self.minimum_payment = minimum_payment

        assert interest_type in ["simple", "compound"]
        assert interest_interval in ["daily", "monthly", "quarterly", "annually"]
        self.interest_type = interest_type
        self.interest_interval = interest_interval

        assert apr >= 0
        self.apr = apr

    #TODO manual review of SavingsBillingState.calculate_next_minimum_payment docstring
    def calculate_next_minimum_payment(self) -> Decimal:
        """
        TODO one-line description of SavingsBillingState.calculate_next_minimum_payment.

        TODO multi-line description of SavingsBillingState.calculate_next_minimum_payment.
        TODO explain how SavingsBillingState.calculate_next_minimum_payment participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that SavingsBillingState.calculate_next_minimum_payment takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of SavingsBillingState.calculate_next_minimum_payment.

        Contract
        --------
        - #TODO contract lines for SavingsBillingState.calculate_next_minimum_payment.
        - #TODO document exceptions, mutations, and precision assumptions for SavingsBillingState.calculate_next_minimum_payment.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO manual review of SavingsBillingState.remaining_minimum_payment_due docstring
    def remaining_minimum_payment_due(self) -> Decimal:
        """
        TODO one-line description of SavingsBillingState.remaining_minimum_payment_due.

        TODO multi-line description of SavingsBillingState.remaining_minimum_payment_due.
        TODO explain how SavingsBillingState.remaining_minimum_payment_due participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that SavingsBillingState.remaining_minimum_payment_due takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of SavingsBillingState.remaining_minimum_payment_due.

        Contract
        --------
        - #TODO contract lines for SavingsBillingState.remaining_minimum_payment_due.
        - #TODO document exceptions, mutations, and precision assumptions for SavingsBillingState.remaining_minimum_payment_due.

        @interface-report: show
        """
        return max(
            Decimal("0"),
            self.minimum_payment - self.billing_cycle_payment_balance
        )

    #TODO manual review of SavingsBillingState.remaining_statement_balance docstring
    def remaining_statement_balance(self) -> Decimal:
        """
        TODO one-line description of SavingsBillingState.remaining_statement_balance.

        TODO multi-line description of SavingsBillingState.remaining_statement_balance.
        TODO explain how SavingsBillingState.remaining_statement_balance participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that SavingsBillingState.remaining_statement_balance takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of SavingsBillingState.remaining_statement_balance.

        Contract
        --------
        - #TODO contract lines for SavingsBillingState.remaining_statement_balance.
        - #TODO document exceptions, mutations, and precision assumptions for SavingsBillingState.remaining_statement_balance.

        @interface-report: show
        """
        return max(
            Decimal("0"),
            self.previous_statement_balance - self.billing_cycle_payment_balance
        )

    #TODO manual review of SavingsBillingState.roll_cycle docstring
    def roll_cycle(self, new_cycle_start_date: date) -> "SavingsBillingState":
        """
        TODO one-line description of SavingsBillingState.roll_cycle.

        TODO multi-line description of SavingsBillingState.roll_cycle.
        TODO explain how SavingsBillingState.roll_cycle participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        new_cycle_start_date : object
            TODO one-line description of SavingsBillingState.roll_cycle.new_cycle_start_date.

        Returns
        -------
        object
            TODO one-line description of return value of SavingsBillingState.roll_cycle.

        Contract
        --------
        - #TODO contract lines for SavingsBillingState.roll_cycle.
        - #TODO document exceptions, mutations, and precision assumptions for SavingsBillingState.roll_cycle.

        @interface-report: show
        """
        return SavingsBillingState(
            billing_cycle_start_date=new_cycle_start_date,
            previous_statement_balance=self.current_statement_balance,
            current_statement_balance=self.current_statement_balance,
            billing_cycle_payment_balance=Decimal("0"),
            minimum_payment=self.calculate_next_minimum_payment(),
            interest_type=self.interest_type,
            interest_interval=self.interest_interval,
            apr=self.apr
        )
