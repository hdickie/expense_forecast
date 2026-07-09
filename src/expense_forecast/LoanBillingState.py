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


#TODO manual review of LoanBillingState docstring
@dataclass
class LoanBillingState:
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
    principal_balance: Decimal
    interest_balance: Decimal
    billing_cycle_payment_balance: Decimal
    minimum_payment: Decimal

    #TODO manual review of LoanBillingState.__init__ docstring
    def __init__(self, billing_cycle_start_date: date,
                  minimum_payment: Decimal,
                  interest_type: str,
                  interest_cadence: str,
                  apr: Decimal,
                  principal_balance: Decimal = None,
                  interest_balance: Decimal = None,
                  billing_cycle_payment_balance: Decimal = Decimal("0"),
                  previous_statement_balance: Decimal = None,
                  current_statement_balance: Decimal = None,
                  ):
        """
        TODO one-line description of LoanBillingState.__init__.

        TODO multi-line description of LoanBillingState.__init__.
        TODO explain how LoanBillingState.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        billing_cycle_start_date : object
            TODO one-line description of LoanBillingState.__init__.billing_cycle_start_date.

        minimum_payment : float
            TODO one-line description of LoanBillingState.__init__.minimum_payment.

        interest_type : object
            TODO one-line description of LoanBillingState.__init__.interest_type.

        interest_cadence : object
            TODO one-line description of LoanBillingState.__init__.interest_cadence.

        apr : float
            TODO one-line description of LoanBillingState.__init__.apr.

        principal_balance : object
            TODO one-line description of LoanBillingState.__init__.principal_balance.

        interest_balance : object
            TODO one-line description of LoanBillingState.__init__.interest_balance.

        billing_cycle_payment_balance : object
            TODO one-line description of LoanBillingState.__init__.billing_cycle_payment_balance.

        previous_statement_balance : object
            TODO one-line description of LoanBillingState.__init__.previous_statement_balance.

        current_statement_balance : object
            TODO one-line description of LoanBillingState.__init__.current_statement_balance.

        Returns
        -------
        None
            TODO one-line description of return value of LoanBillingState.__init__.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.__init__.

        @interface-report: show
        """
        self.billing_cycle_start_date = billing_cycle_start_date

        if principal_balance is None:
            principal_balance = previous_statement_balance
        if interest_balance is None and current_statement_balance is not None:
            interest_balance = current_statement_balance - principal_balance

        assert principal_balance >= 0
        self.principal_balance = principal_balance
        assert interest_balance >= 0
        self.interest_balance = interest_balance
        assert billing_cycle_payment_balance >= 0
        self.billing_cycle_payment_balance = billing_cycle_payment_balance
        assert minimum_payment >= 0
        self.minimum_payment = minimum_payment

        assert interest_type == "simple"
        assert interest_cadence in ["daily", "monthly", "quarterly", "annually"]
        self.interest_type = interest_type
        self.interest_cadence = interest_cadence

        assert apr >= 0
        self.apr = apr

    #TODO manual review of LoanBillingState.balance docstring
    @property
    def balance(self) -> Decimal:
        """
        TODO one-line description of LoanBillingState.balance.

        TODO multi-line description of LoanBillingState.balance.
        TODO explain how LoanBillingState.balance participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LoanBillingState.balance takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.balance.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.balance.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.balance.

        @interface-report: show
        """
        return self.principal_balance + self.interest_balance

    #TODO manual review of LoanBillingState.previous_statement_balance docstring
    @property
    def previous_statement_balance(self) -> Decimal:
        """
        TODO one-line description of LoanBillingState.previous_statement_balance.

        TODO multi-line description of LoanBillingState.previous_statement_balance.
        TODO explain how LoanBillingState.previous_statement_balance participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LoanBillingState.previous_statement_balance takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.previous_statement_balance.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.previous_statement_balance.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.previous_statement_balance.

        @interface-report: show
        """
        return self.principal_balance

    #TODO manual review of LoanBillingState.previous_statement_balance docstring
    @previous_statement_balance.setter
    def previous_statement_balance(self, value: Decimal):
        """
        TODO one-line description of LoanBillingState.previous_statement_balance.

        TODO multi-line description of LoanBillingState.previous_statement_balance.
        TODO explain how LoanBillingState.previous_statement_balance participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            TODO one-line description of LoanBillingState.previous_statement_balance.value.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.previous_statement_balance.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.previous_statement_balance.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.previous_statement_balance.

        @interface-report: show
        """
        assert value >= 0
        self.principal_balance = value

    #TODO manual review of LoanBillingState.current_statement_balance docstring
    @property
    def current_statement_balance(self) -> Decimal:
        """
        TODO one-line description of LoanBillingState.current_statement_balance.

        TODO multi-line description of LoanBillingState.current_statement_balance.
        TODO explain how LoanBillingState.current_statement_balance participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LoanBillingState.current_statement_balance takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.current_statement_balance.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.current_statement_balance.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.current_statement_balance.

        @interface-report: show
        """
        return self.balance

    #TODO manual review of LoanBillingState.current_statement_balance docstring
    @current_statement_balance.setter
    def current_statement_balance(self, value: Decimal):
        """
        TODO one-line description of LoanBillingState.current_statement_balance.

        TODO multi-line description of LoanBillingState.current_statement_balance.
        TODO explain how LoanBillingState.current_statement_balance participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            TODO one-line description of LoanBillingState.current_statement_balance.value.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.current_statement_balance.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.current_statement_balance.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.current_statement_balance.

        @interface-report: show
        """
        assert value >= 0
        self.interest_balance = value - self.principal_balance
        assert self.interest_balance >= 0

    #TODO manual review of LoanBillingState.interest_accrued_for_period docstring
    def interest_accrued_for_period(self) -> Decimal:
        """
        TODO one-line description of LoanBillingState.interest_accrued_for_period.

        TODO multi-line description of LoanBillingState.interest_accrued_for_period.
        TODO explain how LoanBillingState.interest_accrued_for_period participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LoanBillingState.interest_accrued_for_period takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.interest_accrued_for_period.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.interest_accrued_for_period.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.interest_accrued_for_period.

        @interface-report: show
        """
        if self.interest_cadence == "daily":
            return self.principal_balance * self.apr / Decimal("365.25")
        if self.interest_cadence == "monthly":
            return self.principal_balance * self.apr / Decimal("12")
        if self.interest_cadence == "quarterly":
            return self.principal_balance * self.apr / Decimal("4")
        if self.interest_cadence == "annually":
            return self.principal_balance * self.apr
        raise ValueError(f"Unsupported loan interest cadence: {self.interest_cadence}")

    #TODO manual review of LoanBillingState.accrue_interest docstring
    def accrue_interest(self) -> Decimal:
        """
        TODO one-line description of LoanBillingState.accrue_interest.

        TODO multi-line description of LoanBillingState.accrue_interest.
        TODO explain how LoanBillingState.accrue_interest participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LoanBillingState.accrue_interest takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.accrue_interest.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.accrue_interest.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.accrue_interest.

        @interface-report: show
        """
        interest_accrued = self.interest_accrued_for_period()
        self.interest_balance += interest_accrued
        return interest_accrued

    #TODO manual review of LoanBillingState.remaining_minimum_payment_due docstring
    def remaining_minimum_payment_due(self) -> Decimal:
        """
        TODO one-line description of LoanBillingState.remaining_minimum_payment_due.

        TODO multi-line description of LoanBillingState.remaining_minimum_payment_due.
        TODO explain how LoanBillingState.remaining_minimum_payment_due participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LoanBillingState.remaining_minimum_payment_due takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.remaining_minimum_payment_due.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.remaining_minimum_payment_due.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.remaining_minimum_payment_due.

        @interface-report: show
        """
        return max(
            Decimal("0"),
            self.minimum_payment - self.billing_cycle_payment_balance
        )

    #TODO manual review of LoanBillingState.apply_payment docstring
    def apply_payment(self, amount: Decimal) -> tuple[Decimal, Decimal]:
        """
        TODO one-line description of LoanBillingState.apply_payment.

        TODO multi-line description of LoanBillingState.apply_payment.
        TODO explain how LoanBillingState.apply_payment participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        amount : float
            TODO one-line description of LoanBillingState.apply_payment.amount.

        Returns
        -------
        object
            TODO one-line description of return value of LoanBillingState.apply_payment.

        Contract
        --------
        - #TODO contract lines for LoanBillingState.apply_payment.
        - #TODO document exceptions, mutations, and precision assumptions for LoanBillingState.apply_payment.

        @interface-report: show
        """
        payment_remaining = amount

        interest_payment = min(payment_remaining, self.interest_balance)
        self.interest_balance -= interest_payment
        payment_remaining -= interest_payment

        principal_payment = min(payment_remaining, self.principal_balance)
        self.principal_balance -= principal_payment
        payment_remaining -= principal_payment

        return interest_payment, principal_payment
