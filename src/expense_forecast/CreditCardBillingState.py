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


#TODO DOC manual review of CreditCardBillingState docstring
@dataclass
class CreditCardBillingState:
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
    end_of_previous_cycle_balance: Decimal
    minimum_payment: Decimal
    minimum_payment_floor: Decimal
    minimum_payment_credit_balance: Decimal

    #TODO DOC manual review of CreditCardBillingState.__init__ docstring
    def __init__(self, billing_cycle_start_date: date, previous_statement_balance: Decimal,
                  current_statement_balance: Decimal, billing_cycle_payment_balance: Decimal,
                  minimum_payment: Decimal,
                  interest_type: str,
                  interest_interval: str,
                  apr: Decimal,
                  end_of_previous_cycle_balance: Decimal = None,
                  minimum_payment_floor: Decimal = None,
                  minimum_payment_credit_balance: Decimal = Decimal("0"),
                  ):
        """
        #TODO DOC one-line description of CreditCardBillingState.__init__.

        #TODO DOC multi-line description of CreditCardBillingState.__init__.
        #TODO DOC explain how CreditCardBillingState.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        billing_cycle_start_date : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.billing_cycle_start_date.

        previous_statement_balance : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.previous_statement_balance.

        current_statement_balance : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.current_statement_balance.

        billing_cycle_payment_balance : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.billing_cycle_payment_balance.

        minimum_payment : float
            #TODO DOC one-line description of CreditCardBillingState.__init__.minimum_payment.

        interest_type : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.interest_type.

        interest_interval : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.interest_interval.

        apr : float
            #TODO DOC one-line description of CreditCardBillingState.__init__.apr.

        end_of_previous_cycle_balance : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.end_of_previous_cycle_balance.

        minimum_payment_floor : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.minimum_payment_floor.

        minimum_payment_credit_balance : object
            #TODO DOC one-line description of CreditCardBillingState.__init__.minimum_payment_credit_balance.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of CreditCardBillingState.__init__.

        Contract
        --------
        - #TODO DOC contract lines for CreditCardBillingState.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for CreditCardBillingState.__init__.

        @interface-report: show
        """
        self.billing_cycle_start_date = billing_cycle_start_date
        previous_statement_balance = Decimal(str(previous_statement_balance))
        current_statement_balance = Decimal(str(current_statement_balance))
        billing_cycle_payment_balance = Decimal(str(billing_cycle_payment_balance))
        minimum_payment = Decimal(str(minimum_payment))
        if minimum_payment_floor is None:
            minimum_payment_floor = minimum_payment
        minimum_payment_floor = Decimal(str(minimum_payment_floor))
        minimum_payment_credit_balance = Decimal(str(minimum_payment_credit_balance))
        apr = Decimal(str(apr))
        if end_of_previous_cycle_balance is None:
            end_of_previous_cycle_balance = (
                previous_statement_balance + billing_cycle_payment_balance
            )
        end_of_previous_cycle_balance = Decimal(str(end_of_previous_cycle_balance))

        assert previous_statement_balance >= 0
        self.previous_statement_balance = previous_statement_balance
        assert current_statement_balance >= 0
        self.current_statement_balance = current_statement_balance
        assert billing_cycle_payment_balance >= 0
        self.billing_cycle_payment_balance = billing_cycle_payment_balance
        assert end_of_previous_cycle_balance >= 0
        self.end_of_previous_cycle_balance = end_of_previous_cycle_balance
        assert minimum_payment >= 0
        self.minimum_payment = minimum_payment
        assert minimum_payment_floor >= 0
        self.minimum_payment_floor = minimum_payment_floor
        assert minimum_payment_credit_balance >= 0
        self.minimum_payment_credit_balance = minimum_payment_credit_balance

        assert interest_type in ["simple", "compound"]
        assert interest_interval in ["daily", "monthly", "quarterly", "annually"]
        self.interest_type = interest_type
        self.interest_interval = interest_interval

        assert apr >= 0
        self.apr = apr

    #TODO DOC manual review of CreditCardBillingState.calculate_next_minimum_payment docstring
    def calculate_next_minimum_payment(self) -> Decimal:
        """
        #TODO DOC one-line description of CreditCardBillingState.calculate_next_minimum_payment.

        #TODO DOC multi-line description of CreditCardBillingState.calculate_next_minimum_payment.
        #TODO DOC explain how CreditCardBillingState.calculate_next_minimum_payment participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that CreditCardBillingState.calculate_next_minimum_payment takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of CreditCardBillingState.calculate_next_minimum_payment.

        Contract
        --------
        - #TODO DOC contract lines for CreditCardBillingState.calculate_next_minimum_payment.
        - #TODO DOC document exceptions, mutations, and precision assumptions for CreditCardBillingState.calculate_next_minimum_payment.

        @interface-report: show
        """
        interest_accrued_this_cycle = self.interest_accrued_this_cycle()
        principal_due_this_cycle = self.previous_statement_balance * Decimal("0.01")
        total_balance = (
            self.previous_statement_balance
            + self.current_statement_balance
            + interest_accrued_this_cycle
        )

        if interest_accrued_this_cycle + principal_due_this_cycle == 0:
            return Decimal("0")

        return min(
            total_balance,
            max(
                self.minimum_payment_floor,
                interest_accrued_this_cycle + principal_due_this_cycle,
            ),
        )

    #TODO DOC manual review of CreditCardBillingState.interest_accrued_this_cycle docstring
    def interest_accrued_this_cycle(self) -> Decimal:
        """
        #TODO DOC one-line description of CreditCardBillingState.interest_accrued_this_cycle.

        #TODO DOC multi-line description of CreditCardBillingState.interest_accrued_this_cycle.
        #TODO DOC explain how CreditCardBillingState.interest_accrued_this_cycle participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that CreditCardBillingState.interest_accrued_this_cycle takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of CreditCardBillingState.interest_accrued_this_cycle.

        Contract
        --------
        - #TODO DOC contract lines for CreditCardBillingState.interest_accrued_this_cycle.
        - #TODO DOC document exceptions, mutations, and precision assumptions for CreditCardBillingState.interest_accrued_this_cycle.

        @interface-report: show
        """
        if self.interest_interval != "monthly":
            raise NotImplementedError(
                f"Credit card interest interval '{self.interest_interval}' is not implemented."
            )
        if self.interest_type != "compound":
            raise NotImplementedError(
                f"Credit card interest type '{self.interest_type}' is not implemented."
            )
        return self.previous_statement_balance * (self.apr / Decimal("12"))

    #TODO DOC manual review of CreditCardBillingState.remaining_minimum_payment_due docstring
    def remaining_minimum_payment_due(self) -> Decimal:
        """
        #TODO DOC one-line description of CreditCardBillingState.remaining_minimum_payment_due.

        #TODO DOC multi-line description of CreditCardBillingState.remaining_minimum_payment_due.
        #TODO DOC explain how CreditCardBillingState.remaining_minimum_payment_due participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that CreditCardBillingState.remaining_minimum_payment_due takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of CreditCardBillingState.remaining_minimum_payment_due.

        Contract
        --------
        - #TODO DOC contract lines for CreditCardBillingState.remaining_minimum_payment_due.
        - #TODO DOC document exceptions, mutations, and precision assumptions for CreditCardBillingState.remaining_minimum_payment_due.

        @interface-report: show
        """
        return max(
            Decimal("0"),
            self.minimum_payment - self.minimum_payment_credit_balance
        )

    #TODO DOC manual review of CreditCardBillingState.remaining_statement_balance docstring
    def remaining_statement_balance(self) -> Decimal:
        """
        #TODO DOC one-line description of CreditCardBillingState.remaining_statement_balance.

        #TODO DOC multi-line description of CreditCardBillingState.remaining_statement_balance.
        #TODO DOC explain how CreditCardBillingState.remaining_statement_balance participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that CreditCardBillingState.remaining_statement_balance takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of CreditCardBillingState.remaining_statement_balance.

        Contract
        --------
        - #TODO DOC contract lines for CreditCardBillingState.remaining_statement_balance.
        - #TODO DOC document exceptions, mutations, and precision assumptions for CreditCardBillingState.remaining_statement_balance.

        @interface-report: show
        """
        return max(
            Decimal("0"),
            self.previous_statement_balance - self.billing_cycle_payment_balance
        )

    #TODO DOC manual review of CreditCardBillingState.roll_cycle docstring
    def roll_cycle(self, new_cycle_start_date: date) -> "CreditCardBillingState":
        """
        #TODO DOC one-line description of CreditCardBillingState.roll_cycle.

        #TODO DOC multi-line description of CreditCardBillingState.roll_cycle.
        #TODO DOC explain how CreditCardBillingState.roll_cycle participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        new_cycle_start_date : object
            #TODO DOC one-line description of CreditCardBillingState.roll_cycle.new_cycle_start_date.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of CreditCardBillingState.roll_cycle.

        Contract
        --------
        - #TODO DOC contract lines for CreditCardBillingState.roll_cycle.
        - #TODO DOC document exceptions, mutations, and precision assumptions for CreditCardBillingState.roll_cycle.

        @interface-report: show
        """
        interest_accrued_this_cycle = self.interest_accrued_this_cycle()
        end_of_previous_cycle_balance = (
            self.previous_statement_balance
            + self.billing_cycle_payment_balance
        )
        next_statement_balance = (
            self.previous_statement_balance
            + self.current_statement_balance
            + interest_accrued_this_cycle
        )
        next_minimum_payment = self.calculate_next_minimum_payment()
        advance_payment_credit = min(
            self.billing_cycle_payment_balance,
            next_minimum_payment,
        )

        return CreditCardBillingState(
            billing_cycle_start_date=new_cycle_start_date,
            previous_statement_balance=next_statement_balance,
            current_statement_balance=Decimal("0"),
            billing_cycle_payment_balance=Decimal("0"),
            end_of_previous_cycle_balance=end_of_previous_cycle_balance,
            minimum_payment=next_minimum_payment,
            interest_type=self.interest_type,
            interest_interval=self.interest_interval,
            apr=self.apr,
            minimum_payment_floor=self.minimum_payment_floor,
            minimum_payment_credit_balance=advance_payment_credit,
        )
