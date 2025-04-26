import pandas as pd
import datetime
import jsonpickle
from typing import Literal
from models.lineitem.params import LineItemParams

class LineItem:

    @staticmethod
    def _validate_start_and_end_date(start_date, end_date):
        assert isinstance(start_date, datetime.datetime)
        assert isinstance(end_date, datetime.datetime)
        assert start_date <= end_date

    @staticmethod
    def _validate_cadence(cadence, start_date, end_date):
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

    @classmethod
    def from_params(cls, params: LineItemParams, validate: bool = True) -> "LineItem":
        return cls(
            start_date=params.start_date,
            end_date=params.end_date,
            priority=params.priority,
            cadence=params.cadence,
            amount=params.amount,
            deferrable=params.deferrable,
            partial_payment_allowed=params.partial_payment_allowed,
            income_flag=params.income_flag,
            validate=validate
        )


    def __init__(
        self,
        *,
        start_date: datetime.date,
        end_date: datetime.date,
        priority: int,
        cadence: Literal["daily", "weekly", "monthly"],
        amount: float,
        memo: str,
        deferrable: bool = False,
        partial_payment_allowed: bool = False,
        income_flag: bool = False,
        validate: bool = True
    ) -> None:
        
        self.start_date = start_date
        self.end_date = end_date
        self.cadence = cadence
        self.priority = priority
        self.amount = amount
        self.memo = memo
        self.deferrable = deferrable
        self.partial_payment_allowed = partial_payment_allowed
        self.income_flag = income_flag

        if validate:
            LineItem._validate_start_and_end_date(self.start_date, self.end_date)
            LineItem._validate_cadence(self.cadence, self.start_date, self.end_date)
            LineItem._validate_priority(self.priority)
            LineItem._validate_amount(self.amount)
            LineItem._validate_memo(self.memo)

            # Additional validations
            if self.income_flag:
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
                "Start_Date": [self.start_date],
                "End_Date": [self.end_date],
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