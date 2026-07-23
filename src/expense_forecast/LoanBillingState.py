

from dataclasses import dataclass
from datetime import date


#TODO DOC manual review of LoanBillingState docstring
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
    principal_balance: float
    interest_balance: float
    billing_cycle_payment_balance: float
    minimum_payment: float

    #TODO DOC manual review of LoanBillingState.__init__ docstring
    def __init__(self, billing_cycle_start_date: date,
                  minimum_payment: float,
                  interest_type: str,
                  interest_interval: str,
                  apr: float,
                  principal_balance: float = None,
                  interest_balance: float = None,
                  billing_cycle_payment_balance: float = float("0"),
                  previous_statement_balance: float = None,
                  current_statement_balance: float = None,
                  ):
        """
        #TODO DOC one-line description of LoanBillingState.__init__.

        #TODO DOC multi-line description of LoanBillingState.__init__.
        #TODO DOC explain how LoanBillingState.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        billing_cycle_start_date : object
            #TODO DOC one-line description of LoanBillingState.__init__.billing_cycle_start_date.

        minimum_payment : float
            #TODO DOC one-line description of LoanBillingState.__init__.minimum_payment.

        interest_type : object
            #TODO DOC one-line description of LoanBillingState.__init__.interest_type.

        interest_interval : object
            #TODO DOC one-line description of LoanBillingState.__init__.interest_interval.

        apr : float
            #TODO DOC one-line description of LoanBillingState.__init__.apr.

        principal_balance : object
            #TODO DOC one-line description of LoanBillingState.__init__.principal_balance.

        interest_balance : object
            #TODO DOC one-line description of LoanBillingState.__init__.interest_balance.

        billing_cycle_payment_balance : object
            #TODO DOC one-line description of LoanBillingState.__init__.billing_cycle_payment_balance.

        previous_statement_balance : object
            #TODO DOC one-line description of LoanBillingState.__init__.previous_statement_balance.

        current_statement_balance : object
            #TODO DOC one-line description of LoanBillingState.__init__.current_statement_balance.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of LoanBillingState.__init__.

        Contract
        --------
        - #TODO DOC contract lines for LoanBillingState.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LoanBillingState.__init__.

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
        assert interest_interval in ["daily", "monthly", "quarterly", "annually"]
        self.interest_type = interest_type
        self.interest_interval = interest_interval

        assert apr >= 0
        self.apr = apr

    #TODO this should be loan_balance
    @property
    def balance(self) -> float:
        """
        @interface-report: show
        """
        return self.principal_balance + self.interest_balance

    @property
    def previous_statement_balance(self) -> float:
        """
        Return the loan principal balance from the previous statement.

        This property is an alias for ``principal_balance`` kept for callers
        that initialize or report loan billing state in statement-balance
        terms.

        Returns
        -------
        float
            Current principal balance.

        @interface-report: show
        """
        return self.principal_balance

    @previous_statement_balance.setter
    def previous_statement_balance(self, value: float):
        """
        Set the loan principal balance from a previous statement balance.

        Assigning this property updates ``principal_balance`` directly. The
        value must be nonnegative, matching the validation applied during
        construction.

        Parameters
        ----------
        value : float
            Nonnegative statement principal balance.

        Contract
        --------
        - Mutates ``principal_balance``.
        - Raises ``AssertionError`` when ``value`` is negative.

        @interface-report: show
        """
        assert value >= 0
        self.principal_balance = value

    #TODO DOC manual review of LoanBillingState.current_statement_balance docstring
    @property
    def current_statement_balance(self) -> float:
        """
        #TODO DOC one-line description of LoanBillingState.current_statement_balance.

        #TODO DOC multi-line description of LoanBillingState.current_statement_balance.
        #TODO DOC explain how LoanBillingState.current_statement_balance participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that LoanBillingState.current_statement_balance takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of LoanBillingState.current_statement_balance.

        Contract
        --------
        - #TODO DOC contract lines for LoanBillingState.current_statement_balance.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LoanBillingState.current_statement_balance.

        @interface-report: show
        """
        return self.balance

    #TODO DOC manual review of LoanBillingState.current_statement_balance docstring
    @current_statement_balance.setter
    def current_statement_balance(self, value: float):
        """
        #TODO DOC one-line description of LoanBillingState.current_statement_balance.

        #TODO DOC multi-line description of LoanBillingState.current_statement_balance.
        #TODO DOC explain how LoanBillingState.current_statement_balance participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            #TODO DOC one-line description of LoanBillingState.current_statement_balance.value.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of LoanBillingState.current_statement_balance.

        Contract
        --------
        - #TODO DOC contract lines for LoanBillingState.current_statement_balance.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LoanBillingState.current_statement_balance.

        @interface-report: show
        """
        assert value >= 0
        self.interest_balance = value - self.principal_balance
        assert self.interest_balance >= 0

    #TODO DOC manual review of LoanBillingState.interest_accrued_for_period docstring
    def interest_accrued_for_period(self) -> float:
        """
        #TODO DOC one-line description of LoanBillingState.interest_accrued_for_period.

        #TODO DOC multi-line description of LoanBillingState.interest_accrued_for_period.
        #TODO DOC explain how LoanBillingState.interest_accrued_for_period participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that LoanBillingState.interest_accrued_for_period takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of LoanBillingState.interest_accrued_for_period.

        Contract
        --------
        - #TODO DOC contract lines for LoanBillingState.interest_accrued_for_period.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LoanBillingState.interest_accrued_for_period.

        @interface-report: show
        """
        if self.interest_interval == "daily":
            return self.principal_balance * self.apr / float("365.25")
        if self.interest_interval == "monthly":
            return self.principal_balance * self.apr / float("12")
        if self.interest_interval == "quarterly":
            return self.principal_balance * self.apr / float("4")
        if self.interest_interval == "annually":
            return self.principal_balance * self.apr
        raise ValueError(f"Unsupported loan interest interval: {self.interest_interval}")

    #TODO DOC manual review of LoanBillingState.accrue_interest docstring
    def accrue_interest(self) -> float:
        """
        #TODO DOC one-line description of LoanBillingState.accrue_interest.

        #TODO DOC multi-line description of LoanBillingState.accrue_interest.
        #TODO DOC explain how LoanBillingState.accrue_interest participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that LoanBillingState.accrue_interest takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of LoanBillingState.accrue_interest.

        Contract
        --------
        - #TODO DOC contract lines for LoanBillingState.accrue_interest.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LoanBillingState.accrue_interest.

        @interface-report: show
        """
        interest_accrued = self.interest_accrued_for_period()
        self.interest_balance += interest_accrued
        return interest_accrued

    #TODO DOC manual review of LoanBillingState.remaining_minimum_payment_due docstring
    def remaining_minimum_payment_due(self) -> float:
        """
        #TODO DOC one-line description of LoanBillingState.remaining_minimum_payment_due.

        #TODO DOC multi-line description of LoanBillingState.remaining_minimum_payment_due.
        #TODO DOC explain how LoanBillingState.remaining_minimum_payment_due participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that LoanBillingState.remaining_minimum_payment_due takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of LoanBillingState.remaining_minimum_payment_due.

        Contract
        --------
        - #TODO DOC contract lines for LoanBillingState.remaining_minimum_payment_due.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LoanBillingState.remaining_minimum_payment_due.

        @interface-report: show
        """
        return max(
            float("0"),
            self.minimum_payment - self.billing_cycle_payment_balance
        )

    #TODO DOC manual review of LoanBillingState.apply_payment docstring
    def apply_payment(self, amount: float) -> tuple[float, float]:
        """
        #TODO DOC one-line description of LoanBillingState.apply_payment.

        #TODO DOC multi-line description of LoanBillingState.apply_payment.
        #TODO DOC explain how LoanBillingState.apply_payment participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        amount : float
            #TODO DOC one-line description of LoanBillingState.apply_payment.amount.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of LoanBillingState.apply_payment.

        Contract
        --------
        - #TODO DOC contract lines for LoanBillingState.apply_payment.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LoanBillingState.apply_payment.

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
