import pytest
import BudgetItem

class TestBudgetItemMethods:

    @pytest.mark.parametrize('start_date_YYYYMMDD,end_date_YYYYMMDD,priority,cadence,amount,memo,deferrable,partial_payment_allowed',
                 # (start_date_YYYYMMDD,
                 # end_date_YYYYMMDD,
                 # priority,
                 # cadence,
                 # amount,
                 # memo,
                 # deferrable,
                 # partial_payment_allowed),
                [('20000101',
                 '20000101',
                 1,
                 'daily',
                 10,
                 'test memo',
                 False,
                 False),
                  ])
    def test_BudgetItem_Constructor__valid_inputs(self,start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            priority,
                                            cadence,
                                            amount,
                                            memo,
                                            deferrable,
                                            partial_payment_allowed):
        BudgetItem.BudgetItem(start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            priority,
                                            cadence,
                                            amount,
                                            memo,
                                            deferrable,
                                            partial_payment_allowed)

    @pytest.mark.parametrize('start_date_YYYYMMDD,end_date_YYYYMMDD,priority,cadence,amount,memo,deferrable,partial_payment_allowed,expected_exception',
        # (start_date_YYYYMMDD,
        # end_date_YYYYMMDD,
        # priority,
        # cadence,
        # amount,
        # memo,
        # deferrable,
        # partial_payment_allowed),
        [('X',
         '20000101',
         1,
         'daily',
         10,
         'test memo',
         False,
         False,
         ValueError),  #malformed start date string

         ('20000101',
          'X',
          1,
          'daily',
          10,
          'test memo',
          False,
          False,
          ValueError),  # malformed end date string

         ('20000101',
          '20000101',
          'X',
          'daily',
          10,
          'test memo',
          False,
          False,
          TypeError),  # priority is not an int

         ('20000101',
          '20000101',
          1,
          'daily',
          'X',
          'test memo',
          False,
          False,
          TypeError),  # amount is not a float

         ('20000101',
          '20000101',
          0,
          'daily',
          10,
          'test memo',
          False,
          False,
          ValueError),  # priority is less than 1

         ('20000101',
          '20000101',
          1,
          'shmaily',
          10,
          'test memo',
          False,
          False,
          ValueError),  # illegal cadence value

         ('20000101',
          '20000101',
          2,
          'daily',
          10,
          'income',
          False,
          False,
          ValueError),  # priority not 1 for income

         ('20000101',
          '20000101',
          1,
          'daily',
          10,
          'test',
          True,
          False,
          ValueError),  # deferrable must be false for p1

         ('20000101',
          '20000101',
          1,
          'daily',
          10,
          'test',
          False,
          True,
          ValueError),  # partial_payment_allowed must be false for p1

         ])
    def test_BudgetItem_Constructor__invalid_inputs(self,start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            priority,
                                            cadence,
                                            amount,
                                            memo,
                                            deferrable,
                                            partial_payment_allowed,expected_exception):
        with pytest.raises(expected_exception):
            BudgetItem.BudgetItem(start_date_YYYYMMDD,
                                  end_date_YYYYMMDD,
                                  priority,
                                  cadence,
                                  amount,
                                  memo,
                                  deferrable,
                                  partial_payment_allowed)


    def test_to_str(self):
        B = BudgetItem.BudgetItem('20000101',
                                  '20000101',
                                  1,
                                  'daily',
                                  10,
                                  'test',
                                  False,
                                  False)
        str(B)
