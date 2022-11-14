import unittest
import Account,AccountSet,BudgetItem,BudgetSet,MemoRule,MemoRuleSet,ExpenseForecast
import pandas as pd
import datetime
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

class TestExpenseForecastMethods(unittest.TestCase):

    def account_boundaries_are_violated(self,accounts_df,forecast_df):

        for col_name in forecast_df.columns.tolist():
            if col_name == 'Date' or col_name == 'Memo':
                continue

            acct_boundary__min = accounts_df.loc[accounts_df.Name == col_name,'Min_Balance']
            acct_boundary__max = accounts_df.loc[accounts_df.Name == col_name, 'Max_Balance']

            min_in_forecast_for_acct = min(forecast_df[col_name])
            max_in_forecast_for_acct = max(forecast_df[col_name])

            try:
                # print('min_in_forecast_for_acct:'+str(min_in_forecast_for_acct))
                # print('max_in_forecast_for_acct:' + str(max_in_forecast_for_acct))
                # print('acct_boundary__min:' + str(acct_boundary__min))
                # print('acct_boundary__max:' + str(acct_boundary__max))

                assert float(min_in_forecast_for_acct) >= float(acct_boundary__min)
                assert float(max_in_forecast_for_acct) <= float(acct_boundary__max)
            except Exception as e:
                print('Account Boundary Violation for '+str(col_name)+' in ExpenseForecast.account_boundaries_are_violated()')
                return True
        return False

    def test_ExpenseForecast_Constructor(self):
        """
        |
        | Test Cases
        | Expected Successes
        | S1: Base case. More complex tests will go in other methods.
        |
        | Expected Fails
        | F1: start date is after end date
        | F2: Pass in empty AccountSet, BudgetSet, MemoRuleSet objects
        | F3: A budget memo x priority element does not have a matching regex in memo rule set
        | F4: A memo rule has an account that does not exist in AccountSet
        """

        account_set = AccountSet.AccountSet()
        budget_set = BudgetSet.BudgetSet()
        memo_rule_set = MemoRuleSet.MemoRuleSet()
        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000102'

        with self.assertRaises(ValueError): #F1
            #switch started and end date to provoke error
            ExpenseForecast.ExpenseForecast(account_set, budget_set, memo_rule_set,end_date_YYYYMMDD, start_date_YYYYMMDD)

        with self.assertRaises(ValueError): #F2
            ExpenseForecast.ExpenseForecast(account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD)

        account_set.addAccount(name='checking', balance=0, min_balance=0, max_balance=0, account_type="checking" )

        with self.assertRaises(ValueError): #F3
            budget_set.addBudgetItem(start_date_YYYYMMDD='20000101',
                                     priority=1,
                                     cadence='once',
                                     amount=10,
                                     deferrable=False,
                                     memo='test',
                                     print_debug_messages=False)

            #Since there are no memo rules, this will cause the intended error
            ExpenseForecast.ExpenseForecast(account_set,
                                            budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                     print_debug_messages=False)

        with self.assertRaises(ValueError):  # F4
            budget_set = BudgetSet.BudgetSet()
            memo_rule_set.addMemoRule(memo_regex='.*',account_from='doesnt exist',account_to=None,transaction_priority=1)
            ExpenseForecast.ExpenseForecast(account_set,
                                            budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                     print_debug_messages=False)

        ### Debug Message Tests

    # Interest accruals are calculated before any payments for that day
    #
    # scenarios:
    # 1. daily accrual simple ( 0 APR )
    # 2. daily accrual simple
    # 3. monthly accrual simple
    # 4. daily accrual compound
    # 5. monthly accrual compound
    # 6. daily accrual simple (make a payment)
    # 7. monthly accrual compound (make a payment)
    #
    # each test case can have success defined by a 3 x n matrix
    def test_interest_accrual(self):
        pass

    # note: payments in excess of minimum are priority 2
    #
    # scenarios: min payments only. we do not consider the case of insufficient funds because this is priority 1
    # 1. make cc min payment only. prev statement bal is less than $40
    # 2. make cc min payment only. prev statement bal is more than $40 and less than $2k
    # 3. make cc min payment only. prev bal is more than $2k. min payment is 2%
    #
    # scenarios: hard-coded payment in excess of minimum
    # 5. prev less than 40, total debt more than 40, pay less than total balance.
    # 6. prev less than 40, total debt more than 40, pay more than total balance.
    # 7. prev less than 40, total debt more than 40, pay less than total balance when insufficient funds
    # 8. prev less than 40, total debt more than 40, pay more than total balance when insufficient funds
    # 9. prev more than 40 and less than 2k. pay less than total balance
    # 10. prev more than 40 and less than 2k. pay more than total balance
    # 11. prev more than 40 and less than 2k. pay less than total balance when insufficient funds
    # 12. prev more than 40 and less than 2k. pay more than total balance when insufficient funds
    # 13. prev more than 2k. pay less than total balance
    # 14. prev more than 2k. pay more than total balance
    # 15. prev more than 2k. pay less than total balance when insufficient funds
    # 16. prev more than 2k. pay more than total balance when insufficient funds
    #
    # scenarios: amount = "*"
    # 17. prv less than 40, current is non 0
    # 18. prv bw 40 and 2k, current is non 0
    # 19. prv more than 2k, current is non 0
    def test_credit_card_payments(self):
        pass




    # scenarios: min payments only
    # 1. minimum payments only
    #
    # scenarios: hard coded payments in excess of minimum
    # 2. extra payment: 1 loan, less than total balance
    # 3. extra payment: 1 loan, more than total balance
    # 4. extra payment: 1 loan, less than total balance when insufficient funds
    # 5. extra payment: 1 loan, more than total balance when insufficient funds

    # 6. extra payment: 2 loans, same interest rate diff balances, less than total balance
    # 7. extra payment: 2 loans, same interest rate diff balances, more than total balance
    # 8. extra payment: 2 loans, same interest rate diff balances, less than total balance when insufficient funds
    # 9. extra payment: 2 loans, same interest rate diff balances, more than total balance when insufficient funds

    # 10. extra payment: 2 loans, diff interest rate diff balances, less than total balance
    # 11. extra payment: 2 loans, diff interest rate diff balances, more than total balance
    # 12. extra payment: 2 loans, diff interest rate diff balances, less than total balance when insufficient funds
    # 13. extra payment: 2 loans, diff interest rate diff balances, more than total balance when insufficient funds

    # 14. extra payment: 5 loans, diff interest rate diff balances, less than total balance
    # 15. extra payment: 5 loans, diff interest rate diff balances, more than total balance
    # 16. extra payment: 5 loans, diff interest rate diff balances, less than total balance when insufficient funds
    # 17. extra payment: 5 loans, diff interest rate diff balances, more than total balance when insufficient funds
    #
    # scenarios: amount = "*"
    # 18. extra payment: 5 loans, diff interest rate diff balances,
    def test_loan_payments(self):
        raise NotImplementedError

    def test_satisfice(self):
        raise NotImplementedError

    def test_toJSON(self):
        raise NotImplementedError