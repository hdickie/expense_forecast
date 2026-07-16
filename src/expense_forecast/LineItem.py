import pandas as pd
import datetime
import json

#TODO DOC manual review of LineItem docstring
class LineItem:
    """
    Represents a single financial event within a forecast.

    A LineItem describes one transaction or adjustment that may affect the
    financial state of a forecast. Examples include one-time or recurring
    transactions, not including transactions which occur due to account 
    rules alone such as credit card or loan interest.

    A LineItem defines what financial event is intended to occur and the
    information required to evaluate, schedule, and apply that event during
    forecast execution. Collections of LineItems are organized and managed
    by higher-level components such as BudgetSets and MemoRuleSets.

    Responsibilities
    ----------------
    - Describe a single financial event.
    - Store the data required to evaluate and apply the event.
    - Support serialization and deserialization.
    - Participate in forecast execution and scenario evaluation.

    Invariants
    ----------
    - A LineItem represents exactly one (potentially recurring) 
      financial event.
    - The represented event is internally consistent and valid.
    - Serialization preserves the semantic meaning of the event.
    - Equivalent LineItems compare as equal regardless of incidental
      implementation details.

    Notes
    -----
    LineItem is a domain object. It describes *what* financial event should
    occur. By specificying priority = 1, the *when* it will ultimately be 
    applied may be enforced. For priority > 1, the *whether* a transaction
    occurred may be manipulated using the partial_payment_allowed and 
    deferrable flags. Beyond that, scheduling, prioritization, optimization, 
    and execution are the responsibility of higher-level forecasting 
    components.
    """
    @staticmethod
    def _validate_start_and_end_date(start_date, end_date):

        # TODO DEFER change from AssertionError to ValueError with error message including the illegal values
        assert isinstance(start_date, datetime.date)
        assert isinstance(end_date, datetime.date)
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be before end_date ({end_date})")
        assert start_date <= end_date

    @staticmethod
    def _validate_interval(interval, start_date, end_date):
        
        allowed_intervals = ['once','daily','weekly','semiweekly','monthly','quarterly','anually']
        if not interval in allowed_intervals:
            raise ValueError(
                f"Invalid interval: {interval!r}. "
                f"Allowed values are: {sorted(allowed_intervals)}"
            )
        
        # TODO DEFER change from AssertionError to ValueError with error message including the illegal values
        if interval == 'once':
            assert start_date == end_date
        # TODO add warnings if interval is shorter than interval and create test

    @staticmethod
    def _validate_priority(priority):
        # TODO DEFER change from AssertionError to ValueError with error message including the illegal values
        assert priority == int(priority)
        assert priority >= 1

    @staticmethod
    def _validate_amount(amount):
        # TODO DEFER change from AssertionError to ValueError with error message including the illegal values
        assert amount == float(amount)
        assert amount >= 0

    @staticmethod
    def _validate_memo(memo):

        # TODO DEFER change from AssertionError to ValueError with error message including the illegal values
        assert memo == str(memo)
        assert len(memo.strip()) > 0
        assert ';' not in memo

    #TODO DOC manual review of LineItem.__init__ docstring
    def __init__(self, start_date, end_date, priority, interval, amount, memo, **kwargs):

        """
        #TODO DOC one-line description of LineItem.__init__.

        #TODO DOC multi-line description of LineItem.__init__.
        #TODO DOC explain how LineItem.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of LineItem.__init__.start_date.

        end_date : date
            #TODO DOC one-line description of LineItem.__init__.end_date.

        priority : int
            #TODO DOC one-line description of LineItem.__init__.priority.

        interval : str
            #TODO DOC one-line description of LineItem.__init__.interval.

        amount : float
            #TODO DOC one-line description of LineItem.__init__.amount.

        memo : str
            #TODO DOC one-line description of LineItem.__init__.memo.

        **kwargs : dict
            #TODO DOC one-line description of LineItem.__init__.kwargs.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of LineItem.__init__.

        Contract
        --------
        - #TODO DOC contract lines for LineItem.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LineItem.__init__.

        @interface-report: show
        """
        allowed_kwargs = ['deferrable','partial_payment_allowed', 'income_flag']
        for key in kwargs:
           if key not in allowed_kwargs:
               raise TypeError(f"Unexpected keyword argument '{key}'")

        self.start_date = start_date
        self.end_date = end_date
        LineItem._validate_start_and_end_date(self.start_date, self.end_date)

        self.interval = interval
        LineItem._validate_interval(self.interval, self.start_date, self.end_date)

        self.priority = priority
        LineItem._validate_priority(self.priority)

        self.amount = amount
        LineItem._validate_amount(self.amount)

        # Validate memo
        self.memo = memo
        LineItem._validate_memo(self.memo)

        # todo this may not be best practice bc this behaves like an optional parameters
        # but it is not obvious from looking at the method signature? Genuinely don't know
        self.income_flag = kwargs.get('income_flag',False)
        assert self.income_flag == bool(self.income_flag)

        if 'deferrable' in kwargs:
            if kwargs['deferrable']:
                if kwargs['deferrable'] != bool(kwargs['deferrable']):
                    raise ValueError('Deferrable field not castable to bool: '+str(kwargs['deferrable']))
        self.deferrable = kwargs.get('deferrable', False)


        if 'partial_payment_allowed' in kwargs:
            if kwargs['partial_payment_allowed']:
                if kwargs['partial_payment_allowed'] != bool(kwargs['partial_payment_allowed']):
                    raise ValueError('partial_payment_allowed field not castable to bool: '+str(kwargs['partial_payment_allowed']))
        self.partial_payment_allowed = kwargs.get('partial_payment_allowed',False)


        # TODO DEFER change from AssertionError to ValueError with error message including the illegal values
        # Additional validations
        if 'income_flag' in kwargs:
            if kwargs['income_flag']:
                assert self.priority == 1
                assert not self.deferrable
                assert not self.partial_payment_allowed

        if self.priority == 1:
            assert not self.deferrable
            assert not self.partial_payment_allowed

        if self.deferrable:
            assert not self.priority == 1

        if self.partial_payment_allowed:
            assert not self.priority == 1

    def to_dict(self):
        return {
            "Start_Date": self.start_date.strftime("%Y%m%d"),
            "End_Date": self.end_date.strftime("%Y%m%d"),
            "Priority": self.priority,
            "interval": self.interval,
            "Amount": self.amount,
            "Memo": self.memo,
            "Deferrable": self.deferrable,
            "Partial_Payment_Allowed": self.partial_payment_allowed,
        }

    def to_dataframe(self):
        """
        @interface-report: show
        """
        return pd.DataFrame([self.to_dict()])

    def to_json(self):
        """
        @interface-report: show
        """
        return json.dumps(self.to_dict(), indent=4)

    def __str__(self):
        """
        @interface-report: show
        """
        return self.to_dataframe().to_string(index=False)
