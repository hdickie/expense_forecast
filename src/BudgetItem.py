import pandas as pd
import datetime
import jsonpickle


class BudgetItem:

    @staticmethod
    def _validate_start_and_end_date(start_date, end_date):
        assert isinstance(start_date, datetime.datetime)
        assert isinstance(end_date, datetime.datetime)
        assert start_date <= end_date

    @staticmethod
    def _validate_cadence(cadence, start_date, end_date):
        allowed_cadences = ['once','daily','weekly','semiweekly','monthly','quarterly','yearly']
        assert cadence in allowed_cadences
        if cadence == 'once':
            assert start_date == end_date
        # todo maybe warnings if interval is shorted than cadence?
        # also maybe call cadence interval instead??
        # also maybe allow integer intervals??

    @staticmethod
    def _validate_priority(priority):
        assert priority == int(priority)
        assert priority >= 1

    @staticmethod
    def _validate_amount(amount):
        assert amount == float(amount)
        assert amount >= 0

    @staticmethod
    def _validate_memo(memo):
        assert memo == str(memo)
        assert len(memo.strip()) > 0
        assert ';' not in memo

    def __init__(self, start_date, end_date, priority, cadence, amount, memo, income_flag=False, **kwargs):

        allowed_kwargs = ['deferrable','partial_payment_allowed']
        for key in kwargs:
           if key not in allowed_kwargs:
               raise TypeError(f"Unexpected keyword argument '{key}'")

        self.start_date = start_date
        self.end_date = end_date
        BudgetItem._validate_start_and_end_date(self.start_date, self.end_date)

        self.cadence = cadence
        BudgetItem._validate_cadence(self.cadence, self.start_date, self.end_date)

        self.priority = priority
        BudgetItem._validate_priority(self.priority)

        self.amount = amount
        BudgetItem._validate_amount(self.amount)

        # Validate memo
        self.memo = memo
        BudgetItem._validate_memo(self.memo)

        self.income_flag = income_flag
        assert income_flag == bool(income_flag)

        if 'deferrable' in kwargs:
            self.deferrable = kwargs['deferrable']
            assert self.deferrable == bool(kwargs['deferrable'])

        if 'partial_payment_allowed' in kwargs:
            self.partial_payment_allowed = kwargs['partial_payment_allowed']
            assert self.partial_payment_allowed == bool(kwargs['partial_payment_allowed'])

        # Additional validations
        if income_flag:
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

    def __str__(self):
        return pd.DataFrame(
            {
                "Start_Date": [self.start_date.strftime('%Y%m%d')],
                "End_Date": [self.end_date.strftime('%Y%m%d')],
                "Priority": [self.priority],
                "Cadence": [self.cadence],
                "Amount": [self.amount],
                "Memo": [self.memo],
                "Deferrable": [self.deferrable],
                "Partial_Payment_Allowed": [self.partial_payment_allowed],
            }
        ).to_string()

    def to_json(self):
        return jsonpickle.encode(self, indent=4)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
