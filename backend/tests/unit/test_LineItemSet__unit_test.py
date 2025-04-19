import pytest
from backend.core import LineItem
from backend.core import LineItemSet
import datetime

def example_line_item():
    return LineItem.LineItem(
        start_date=datetime.datetime.strptime("20000101",'%Y%m%d'),
        end_date=datetime.datetime.strptime("20000101",'%Y%m%d'),
        priority=1,
        cadence="once",
        amount=10,
        deferrable=False,
        memo="test",
    )


class TestLineItemSetMethods:

    @pytest.mark.parametrize(
        "line_items__list",
        [
            ([example_line_item()]),
        ],
    )
    def test_LineItemSet_Constructor(self, line_items__list):
        LineItemSet.LineItemSet(line_items__list)

    @pytest.mark.parametrize(
        "start_date,end_date,priority,cadence,amount,memo,deferrable,partial_payment_allowed",
        [
            ([datetime.datetime.strptime("20000101",'%Y%m%d'), datetime.datetime.strptime("20000101",'%Y%m%d'), 1, "daily", 10, "test memo", False, False]),
        ],
    )
    def test_addLineItem(self,
                         start_date,
                         end_date,
                         priority,
                         cadence,
                         amount,
                         memo,
                         deferrable,
                         partial_payment_allowed):
        test_lineitem_set = LineItemSet.LineItemSet([])
        test_lineitem_set.addLineItem(
            start_date=datetime.datetime.strptime("20000101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20000101",'%Y%m%d'),
            priority=1,
            cadence="once",
            amount=10,
            deferrable=False,
            memo="test 2",
            partial_payment_allowed=False,
        )

    def test_getLineItems(self):
        test_lineitem_set = LineItemSet.LineItemSet([])

        test_lineitem_set.addLineItem(
            start_date=datetime.datetime.strptime("20000101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20000101",'%Y%m%d'),
            priority=1,
            cadence="once",
            amount=10,
            deferrable=False,
            memo="test",
            partial_payment_allowed=False,
        )
        test_df = test_lineitem_set.getBudgetItems()
        assert test_df is not None

    def test_getLineItemSchedule(self):
        test_budget_set = LineItemSet.LineItemSet([])
        test_budget_set.addLineItem(
            start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            priority=1,
            cadence="daily",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 0",
        )
        test_budget_set.addLineItem(
            start_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            priority=1,
            cadence="once",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 1",
        )
        test_budget_set.addLineItem(
            start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            priority=1,
            cadence="weekly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 2",
        )
        test_budget_set.addLineItem(
            start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            priority=1,
            cadence="semiweekly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 3",
        )
        test_budget_set.addLineItem(
            start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            priority=1,
            cadence="monthly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 4",
        )
        test_budget_set.addLineItem(
            start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            priority=1,
            cadence="quarterly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 5",
        )
        test_budget_set.addLineItem(
            start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
            end_date=datetime.datetime.strptime("20230101",'%Y%m%d'),
            priority=1,
            cadence="yearly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 6",
        )
        test_df = test_budget_set.getBudgetSchedule()

    def test_str(self):
        test_lineitem_set = LineItemSet.LineItemSet([])
        lineitemset_str = str(test_lineitem_set)
        assert lineitemset_str is not None

        test_lineitem_set.addLineItem(
            start_date_YYYYMMDD="20220101",
            end_date_YYYYMMDD="20220101",
            priority=1,
            cadence="daily",
            amount=0,
            deferrable=False,
            memo="test",
            partial_payment_allowed=False,
            # ,throw_exceptions=False
        )
        budgetset_str = str(test_lineitem_set)
        assert budgetset_str is not None

    def test_duplicate_line_items_not_allowed(self):
        test_lineitem_set = LineItemSet.BudgetSet([])
        with pytest.raises(ValueError):
            test_lineitem_set.addLineItem(
                start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
                end_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
                priority=1,
                cadence="daily",
                amount=10,
                deferrable=False,
                memo="test",
                partial_payment_allowed=False,
                # ,throw_exceptions=False
            )
            test_lineitem_set.addLineItem(
                start_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
                end_date=datetime.datetime.strptime("20220101",'%Y%m%d'),
                priority=1,
                cadence="daily",
                amount=10,
                deferrable=False,
                memo="test",
                partial_payment_allowed=False,
                # ,throw_exceptions=False
            )

    # this test is here for coverage, bc input validation would have stopped this branch of logic first
    def test_illegal_cadence_in__generate_date_sequence__internal_method(self):
        with pytest.raises(ValueError):
            LineItemSet.generate_date_sequence("20000101", 10, "shmaily")
