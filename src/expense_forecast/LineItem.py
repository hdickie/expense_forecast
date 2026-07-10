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
import datetime
import jsonpickle
import json

#TODO manual review of LineItem docstring
class LineItem:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of LineItem._validate_start_and_end_date docstring
    @staticmethod
    def _validate_start_and_end_date(start_date, end_date):
        """
        TODO one-line description of LineItem._validate_start_and_end_date.

        TODO multi-line description of LineItem._validate_start_and_end_date.
        TODO explain how LineItem._validate_start_and_end_date participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            TODO one-line description of LineItem._validate_start_and_end_date.start_date.

        end_date : date
            TODO one-line description of LineItem._validate_start_and_end_date.end_date.

        Returns
        -------
        None
            TODO one-line description of return value of LineItem._validate_start_and_end_date.

        Contract
        --------
        - #TODO contract lines for LineItem._validate_start_and_end_date.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem._validate_start_and_end_date.

        @interface-report: show
        """
        assert isinstance(start_date, datetime.date)
        assert isinstance(end_date, datetime.date)
        assert start_date <= end_date

    #TODO manual review of LineItem._validate_interval docstring
    @staticmethod
    def _validate_interval(interval, start_date, end_date):
        """
        TODO one-line description of LineItem._validate_interval.

        TODO multi-line description of LineItem._validate_interval.
        TODO explain how LineItem._validate_interval participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        interval : str
            TODO one-line description of LineItem._validate_interval.interval.

        start_date : date
            TODO one-line description of LineItem._validate_interval.start_date.

        end_date : date
            TODO one-line description of LineItem._validate_interval.end_date.

        Returns
        -------
        None
            TODO one-line description of return value of LineItem._validate_interval.

        Contract
        --------
        - #TODO contract lines for LineItem._validate_interval.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem._validate_interval.

        @interface-report: show
        """
        allowed_intervals = ['once','daily','weekly','semiweekly','monthly','quarterly','anually']
        if not interval in allowed_intervals:
            raise ValueError(
                f"Invalid interval: {interval!r}. "
                f"Allowed values are: {sorted(allowed_intervals)}"
            )
        if interval == 'once':
            assert start_date == end_date
        # TODO add warnings if interval is shorter than interval and create test

    #TODO manual review of LineItem._validate_priority docstring
    @staticmethod
    def _validate_priority(priority):
        """
        TODO one-line description of LineItem._validate_priority.

        TODO multi-line description of LineItem._validate_priority.
        TODO explain how LineItem._validate_priority participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        priority : int
            TODO one-line description of LineItem._validate_priority.priority.

        Returns
        -------
        None
            TODO one-line description of return value of LineItem._validate_priority.

        Contract
        --------
        - #TODO contract lines for LineItem._validate_priority.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem._validate_priority.

        @interface-report: show
        """
        assert priority == int(priority)
        assert priority >= 1

    #TODO manual review of LineItem._validate_amount docstring
    @staticmethod
    def _validate_amount(amount):
        """
        TODO one-line description of LineItem._validate_amount.

        TODO multi-line description of LineItem._validate_amount.
        TODO explain how LineItem._validate_amount participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        amount : float
            TODO one-line description of LineItem._validate_amount.amount.

        Returns
        -------
        None
            TODO one-line description of return value of LineItem._validate_amount.

        Contract
        --------
        - #TODO contract lines for LineItem._validate_amount.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem._validate_amount.

        @interface-report: show
        """
        assert amount == float(amount)
        assert amount >= 0

    #TODO manual review of LineItem._validate_memo docstring
    @staticmethod
    def _validate_memo(memo):
        """
        TODO one-line description of LineItem._validate_memo.

        TODO multi-line description of LineItem._validate_memo.
        TODO explain how LineItem._validate_memo participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo : str
            TODO one-line description of LineItem._validate_memo.memo.

        Returns
        -------
        None
            TODO one-line description of return value of LineItem._validate_memo.

        Contract
        --------
        - #TODO contract lines for LineItem._validate_memo.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem._validate_memo.

        @interface-report: show
        """
        assert memo == str(memo)
        assert len(memo.strip()) > 0
        assert ';' not in memo

    #TODO manual review of LineItem.__init__ docstring
    def __init__(self, start_date, end_date, priority, interval, amount, memo, **kwargs):

        """
        TODO one-line description of LineItem.__init__.

        TODO multi-line description of LineItem.__init__.
        TODO explain how LineItem.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            TODO one-line description of LineItem.__init__.start_date.

        end_date : date
            TODO one-line description of LineItem.__init__.end_date.

        priority : int
            TODO one-line description of LineItem.__init__.priority.

        interval : str
            TODO one-line description of LineItem.__init__.interval.

        amount : float
            TODO one-line description of LineItem.__init__.amount.

        memo : str
            TODO one-line description of LineItem.__init__.memo.

        **kwargs : dict
            TODO one-line description of LineItem.__init__.kwargs.

        Returns
        -------
        None
            TODO one-line description of return value of LineItem.__init__.

        Contract
        --------
        - #TODO contract lines for LineItem.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem.__init__.

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

    #TODO manual review of LineItem.to_dict docstring
    def to_dict(self):
        """
        TODO one-line description of LineItem.to_dict.

        TODO multi-line description of LineItem.to_dict.
        TODO explain how LineItem.to_dict participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LineItem.to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            TODO one-line description of return value of LineItem.to_dict.

        Contract
        --------
        - #TODO contract lines for LineItem.to_dict.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem.to_dict.

        @interface-report: show
        """
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

    #TODO manual review of LineItem.to_dataframe docstring
    def to_dataframe(self):
        """
        TODO one-line description of LineItem.to_dataframe.

        TODO multi-line description of LineItem.to_dataframe.
        TODO explain how LineItem.to_dataframe participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LineItem.to_dataframe takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of LineItem.to_dataframe.

        Contract
        --------
        - #TODO contract lines for LineItem.to_dataframe.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem.to_dataframe.

        @interface-report: show
        """
        return pd.DataFrame([self.to_dict()])

    #TODO manual review of LineItem.to_json docstring
    def to_json(self):
        """
        TODO one-line description of LineItem.to_json.

        TODO multi-line description of LineItem.to_json.
        TODO explain how LineItem.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LineItem.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of LineItem.to_json.

        Contract
        --------
        - #TODO contract lines for LineItem.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem.to_json.

        @interface-report: show
        """
        return json.dumps(self.to_dict(), indent=4)

    #TODO manual review of LineItem.__str__ docstring
    def __str__(self):
        """
        TODO one-line description of LineItem.__str__.

        TODO multi-line description of LineItem.__str__.
        TODO explain how LineItem.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LineItem.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of LineItem.__str__.

        Contract
        --------
        - #TODO contract lines for LineItem.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for LineItem.__str__.

        @interface-report: show
        """
        return self.to_dataframe().to_string(index=False)


BudgetItem = LineItem


if __name__ == "__main__":
    import doctest

    doctest.testmod()
