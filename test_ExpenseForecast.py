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

        self.assertIsNotNone(ExpenseForecast.ExpenseForecast())

    def test_interest_accrual(self):

        initial_values_dict = {}
        initial_values_dict['Checking'] = 1000
        initial_values_dict['Credit Card Current Statement Balance'] = 2000
        initial_values_dict['Credit Card Previous Statement Balance'] = 3000
        initial_values_dict['Loan A Principal Balance'] = 3359.17
        initial_values_dict['Loan A Interest'] = 0
        initial_values_dict['Credit Card APR'] = 0.2674
        initial_values_dict['Loan APR'] = 0.0466

        expense_forecast_obj = ExpenseForecast.ExpenseForecast()
        account_set = AccountSet.AccountSet()
        budget_set = BudgetSet.BudgetSet()
        memo_rule_set = MemoRuleSet.MemoRuleSet()

        account_set.addAccount(name='Checking', balance=initial_values_dict['Checking'],   min_balance=0,   max_balance=float('inf'),
                               apr=0,   interest_cadence='None',    interest_type='None',   billing_start_date='None',
                               account_type='checking', principal_balance=None, accrued_interest=None)

        account_set.addAccount(name='Credit Card',  balance=initial_values_dict['Credit Card Current Statement Balance'],
                               previous_statement_balance=initial_values_dict['Credit Card Previous Statement Balance'], min_balance=0,
                               max_balance=20000,   apr=initial_values_dict['Credit Card APR'],    interest_cadence='Monthly',  interest_type='Compound',
                               billing_start_date='2021-01-07', account_type='credit',  principal_balance=-1,   accrued_interest=-1,minimum_payment=40)


        account_set.addAccount(name='Loan A',   balance=initial_values_dict['Loan A Principal Balance']+initial_values_dict['Loan A Interest'],
                               min_balance=0,  max_balance=float('inf'),
                               apr=initial_values_dict['Loan APR'],  interest_cadence='daily',   interest_type='Simple', billing_start_date='2023-01-03',
                               account_type='loan', principal_balance=initial_values_dict['Loan A Principal Balance'],
                               accrued_interest=initial_values_dict['Loan A Interest'])

        budget_set.addBudgetItem(start_date='2023-01-01',priority=1,cadence='daily',amount='0',memo='dummy for test')
        memo_rule_set.addMemoRule(memo_regex='dummy for test',account_from='Checking',account_to=None,transaction_priority=1)

        start_date_YYYYMMDD = '20230105'
        start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')

        budget_schedule_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD,num_days=3)
        account_set_df = account_set.getAccounts()
        memo_rules_df = memo_rule_set.getMemoRules()

        #print('account_set_df:')
        #print(account_set_df.to_string())

        forecast_df = expense_forecast_obj.computeForecast(budget_schedule_df, account_set_df, memo_rules_df)[2]

        #print('forecast_df:')
        #print(forecast_df.to_string())

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance
        #   Loan A: Loan Principal Balance      Loan A: Loan Interest       Memo

        new_empty_row_df = pd.DataFrame(
            {'Date': [None], 'Checking': [None], 'Credit Card: Current Statement Balance': [None],
             'Credit Card: Previous Statement Balance': [None], 'Loan A: Principal Balance': [None],
             'Loan A: Interest': [None], 'Memo': [None]
             })

        expected_result_set_df = pd.concat([new_empty_row_df.copy(),
                                              new_empty_row_df.copy(),
                                              new_empty_row_df.copy(),
                                              new_empty_row_df.copy()])

        #Starting values
        expected_result_set_df.iloc[0, 0] = start_date
        expected_result_set_df.iloc[0,new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict['Checking']
        expected_result_set_df.iloc[0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = initial_values_dict['Credit Card Current Statement Balance']
        expected_result_set_df.iloc[0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = initial_values_dict['Credit Card Previous Statement Balance']
        expected_result_set_df.iloc[0, new_empty_row_df.columns.tolist().index('Loan A: Principal Balance')] = initial_values_dict['Loan A Principal Balance']
        expected_result_set_df.iloc[0, new_empty_row_df.columns.tolist().index('Loan A: Interest')] = initial_values_dict['Loan A Interest']

        expected_result_set_df.iloc[1, 0] = start_date + datetime.timedelta(days=1)
        expected_result_set_df.iloc[2, 0] = start_date + datetime.timedelta(days=2)
        expected_result_set_df.iloc[3, 0] = start_date + datetime.timedelta(days=3)

        #Checking doesnt change
        expected_result_set_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict[
            'Checking']
        expected_result_set_df.iloc[2, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict[
            'Checking']
        expected_result_set_df.iloc[3, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict[
            'Checking']

        #Credit should have balance move to previous statement and accrue interest based on previous statement balance
        expected_result_set_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = initial_values_dict['Credit Card Current Statement Balance']
        expected_result_set_df.iloc[2, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = 0
        expected_result_set_df.iloc[3, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = 0

        expected_result_set_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = initial_values_dict['Credit Card Previous Statement Balance']
        expected_result_set_df.iloc[2, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = initial_values_dict['Credit Card Previous Statement Balance'] + initial_values_dict['Credit Card Current Statement Balance'] + initial_values_dict['Credit Card Previous Statement Balance']*initial_values_dict['Credit Card APR']/12
        expected_result_set_df.iloc[3, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = initial_values_dict['Credit Card Previous Statement Balance'] + initial_values_dict['Credit Card Current Statement Balance'] + initial_values_dict['Credit Card Previous Statement Balance']*initial_values_dict['Credit Card APR']/12

        #Loan should accrue interest daily based on the principal balance
        expected_result_set_df.iloc[1, new_empty_row_df.columns.tolist().index('Loan A: Principal Balance')] = initial_values_dict['Loan A Principal Balance']
        expected_result_set_df.iloc[2, new_empty_row_df.columns.tolist().index('Loan A: Principal Balance')] = initial_values_dict['Loan A Principal Balance']
        expected_result_set_df.iloc[3, new_empty_row_df.columns.tolist().index('Loan A: Principal Balance')] = initial_values_dict['Loan A Principal Balance']

        expected_result_set_df.iloc[1, new_empty_row_df.columns.tolist().index('Loan A: Interest')] = initial_values_dict['Loan A Principal Balance']*initial_values_dict['Loan APR']/365.25
        expected_result_set_df.iloc[2, new_empty_row_df.columns.tolist().index('Loan A: Interest')] = 2*initial_values_dict['Loan A Principal Balance']*initial_values_dict['Loan APR']/365.25
        expected_result_set_df.iloc[3, new_empty_row_df.columns.tolist().index('Loan A: Interest')] = 3*initial_values_dict['Loan A Principal Balance']*initial_values_dict['Loan APR']/365.25

        #todo payments should be applied AFTER interest accrual for that day



        #todo check that accounts with 0 APR do not experience interest accrual

        #todo check daily cadence
        ##check amount is correct
        ##check that interest does not accrue before billing start date


        #todo check monthly cadence
        ##check that amount is correct

        try:
            self.account_boundaries_are_violated(account_set_df,forecast_df)
            self.assertTrue(forecast_df.iloc[:,0:expected_result_set_df.shape[1]-1].equals(expected_result_set_df.iloc[:,0:expected_result_set_df.shape[1]-1]))
        except Exception as e:
            print('FAILURE IN test_interest_accrual()')
            print('Expected '.ljust(50,'#'))
            print(expected_result_set_df.iloc[:,0:expected_result_set_df.shape[1]-1].to_string())
            print(''.ljust(50,'#'))
            print('Forecasted '.ljust(50,'#'))
            print(forecast_df.iloc[:,0:expected_result_set_df.shape[1]-1].to_string())
            print('#'.ljust(50,'#'))
            raise e
            
    def test_credit_card_payments(self):

        # note: payments in excess of minimum are priority 2

        # scenarios
        # 1. make cc min payment only. bal is less than $40
        # 2. make cc min payment only. bal is more than $40 and less than $2k
        # 3. make cc min payment only. bal is more than $2k. min payment is 2%
        # 4. make cc min payment. combined current and prev statement balance less than $40, both non 0

        # scenarios: previous statement balance and payment in excess of minimum

        # 5. make cc payment in excess of minimum. current statement more than $40, pay less than total balance.
        # 6. make cc payment in excess of minimum. current statement more than $40, pay less than total balance, when balance is greater than checking
        # 7. make cc payment in excess of minimum. current statement more than $2k, pay more than total balance.

        new_empty_row_df = pd.DataFrame(
            {'Date': [None], 'Checking': [None], 'Credit Card: Current Statement Balance': [None],
             'Credit Card: Previous Statement Balance': [None], 'Memo': [None]
             })

        empty_result_set_df = pd.concat([new_empty_row_df.copy(),
                                         new_empty_row_df.copy(),
                                         new_empty_row_df.copy(),
                                         new_empty_row_df.copy()])

        start_date_YYYYMMDD = '20230105'
        start_date = datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d')

        empty_result_set_df.iloc[0, 0] = start_date
        empty_result_set_df.iloc[1, 0] = start_date + datetime.timedelta(days=1)
        empty_result_set_df.iloc[2, 0] = start_date + datetime.timedelta(days=2)
        empty_result_set_df.iloc[3, 0] = start_date + datetime.timedelta(days=3)

        expense_forecast_obj = ExpenseForecast.ExpenseForecast()

        #scenario 1
        initial_values_dict_1 = {}
        initial_values_dict_1['Checking'] = 10000
        initial_values_dict_1['Credit Card Current Statement Balance'] = 0
        initial_values_dict_1['Credit Card Previous Statement Balance'] = 30
        initial_values_dict_1['Credit Card APR'] = 0.2674

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance  Memo
        expected_result_set_1_df = empty_result_set_df.copy()
        expected_result_set_1_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_1[
            'Checking']
        expected_result_set_1_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
        initial_values_dict_1[
            'Credit Card Current Statement Balance']
        expected_result_set_1_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_1['Credit Card Previous Statement Balance']

        # set expected rows
        expected_result_set_1_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_1['Checking']
        expected_result_set_1_df.iloc[0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = initial_values_dict_1['Credit Card Current Statement Balance']
        expected_result_set_1_df.iloc[0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = initial_values_dict_1['Credit Card Previous Statement Balance']

        expected_result_set_1_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_1['Checking']
        expected_result_set_1_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
        initial_values_dict_1['Credit Card Current Statement Balance']
        expected_result_set_1_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
        initial_values_dict_1['Credit Card Previous Statement Balance']

        expected_result_set_1_df.iloc[2, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_1['Checking'] - initial_values_dict_1['Credit Card Previous Statement Balance']
        expected_result_set_1_df.iloc[2, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = 0
        expected_result_set_1_df.iloc[2, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = 0

        expected_result_set_1_df.iloc[3, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_1['Checking'] - initial_values_dict_1['Credit Card Previous Statement Balance']
        expected_result_set_1_df.iloc[3, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = 0
        expected_result_set_1_df.iloc[3, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = 0



        account_set_1 = AccountSet.AccountSet()
        budget_set_1 = BudgetSet.BudgetSet()
        memo_rule_set_1 = MemoRuleSet.MemoRuleSet()

        account_set_1.addAccount(name='Checking', balance=initial_values_dict_1['Checking'], min_balance=0,
                               max_balance=float('inf'),
                               apr=0, interest_cadence='None', interest_type='None', billing_start_date='None',
                               account_type='checking', principal_balance=None, accrued_interest=None)

        account_set_1.addAccount(name='Credit Card', balance=initial_values_dict_1['Credit Card Current Statement Balance'],
                               previous_statement_balance=initial_values_dict_1['Credit Card Previous Statement Balance'],
                               min_balance=0,
                               max_balance=20000, apr=initial_values_dict_1['Credit Card APR'],
                               interest_cadence='Monthly', interest_type='Compound',
                               billing_start_date='2000-01-07', account_type='credit', principal_balance=-1,
                               accrued_interest=-1,minimum_payment=40)

        budget_set_1.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0', memo='dummy for test')
        memo_rule_set_1.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None, transaction_priority=1)

        budget_schedule_1_df = budget_set_1.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_1_df = account_set_1.getAccounts()
        memo_rules_1_df = memo_rule_set_1.getMemoRules()
        forecast_1_df = expense_forecast_obj.computeForecast(budget_schedule_1_df, account_set_1_df, memo_rules_1_df)[2]

        # scenario 2
        initial_values_dict_2 = {}
        initial_values_dict_2['Checking'] = 10000
        initial_values_dict_2['Credit Card Current Statement Balance'] = 0
        initial_values_dict_2['Credit Card Previous Statement Balance'] = 300
        initial_values_dict_2['Credit Card APR'] = 0.2674

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance  Memo
        expected_result_set_2_df = empty_result_set_df.copy()
        expected_result_set_2_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_2[
            'Checking']
        expected_result_set_2_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_2[
                'Credit Card Current Statement Balance']
        expected_result_set_2_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_2['Credit Card Previous Statement Balance']

        expected_result_set_2_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_2['Checking']
        expected_result_set_2_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_2['Credit Card Current Statement Balance']
        expected_result_set_2_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_2['Credit Card Previous Statement Balance']

        expected_result_set_2_df.iloc[2, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_2['Checking'] - 40
        expected_result_set_2_df.iloc[2, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = 0
        expected_result_set_2_df.iloc[2, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = (initial_values_dict_2['Credit Card Previous Statement Balance'] - 40) + (initial_values_dict_2['Credit Card Previous Statement Balance'] - 40)*initial_values_dict_2['Credit Card APR']/12

        expected_result_set_2_df.iloc[3, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_2['Checking'] - 40
        expected_result_set_2_df.iloc[3, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = 0
        expected_result_set_2_df.iloc[3, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = (initial_values_dict_2['Credit Card Previous Statement Balance'] - 40) + (initial_values_dict_2['Credit Card Previous Statement Balance'] - 40)*initial_values_dict_2['Credit Card APR']/12
        # todo further days


        account_set_2 = AccountSet.AccountSet()
        budget_set_2 = BudgetSet.BudgetSet()
        memo_rule_set_2 = MemoRuleSet.MemoRuleSet()

        account_set_2.addAccount(name='Checking', balance=initial_values_dict_2['Checking'], min_balance=0,
                                 max_balance=float('inf'),
                                 apr=0, interest_cadence='None', interest_type='None', billing_start_date='None',
                                 account_type='checking', principal_balance=None, accrued_interest=None)

        account_set_2.addAccount(name='Credit Card',
                                 balance=initial_values_dict_2['Credit Card Current Statement Balance'],
                                 previous_statement_balance=initial_values_dict_2[
                                     'Credit Card Previous Statement Balance'],
                                 min_balance=0,
                                 max_balance=20000, apr=initial_values_dict_2['Credit Card APR'],
                                 interest_cadence='Monthly', interest_type='Compound',
                                 billing_start_date='2000-01-07', account_type='credit', principal_balance=-1,
                                 accrued_interest=-1, minimum_payment=40)

        budget_set_2.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0',
                                   memo='dummy for test')
        memo_rule_set_2.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None,
                                    transaction_priority=1)

        budget_schedule_2_df = budget_set_2.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_2_df = account_set_2.getAccounts()
        memo_rules_2_df = memo_rule_set_2.getMemoRules()
        forecast_2_df = expense_forecast_obj.computeForecast(budget_schedule_2_df, account_set_2_df, memo_rules_2_df)[2]

        # scenario 3
        initial_values_dict_3 = {}
        initial_values_dict_3['Checking'] = 10000
        initial_values_dict_3['Credit Card Current Statement Balance'] = 0
        initial_values_dict_3['Credit Card Previous Statement Balance'] = 3000
        initial_values_dict_3['Credit Card APR'] = 0.2674

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance  Memo
        expected_result_set_3_df = empty_result_set_df.copy()
        expected_result_set_3_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_3[
            'Checking']
        expected_result_set_3_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_3[
                'Credit Card Current Statement Balance']
        expected_result_set_3_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_3['Credit Card Previous Statement Balance']

        expected_result_set_3_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_3['Checking']
        expected_result_set_3_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_3['Credit Card Current Statement Balance']
        expected_result_set_3_df.iloc[1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_3['Credit Card Previous Statement Balance']
        # todo further days

        account_set_3 = AccountSet.AccountSet()
        budget_set_3 = BudgetSet.BudgetSet()
        memo_rule_set_3 = MemoRuleSet.MemoRuleSet()

        account_set_3.addAccount(name='Checking', balance=initial_values_dict_3['Checking'], min_balance=0,
                                 max_balance=float('inf'),
                                 apr=0, interest_cadence='None', interest_type='None', billing_start_date='None',
                                 account_type='checking', principal_balance=None, accrued_interest=None)

        account_set_3.addAccount(name='Credit Card',
                                 balance=initial_values_dict_3['Credit Card Current Statement Balance'],
                                 previous_statement_balance=initial_values_dict_3[
                                     'Credit Card Previous Statement Balance'],
                                 min_balance=0,
                                 max_balance=20000, apr=initial_values_dict_3['Credit Card APR'],
                                 interest_cadence='Monthly', interest_type='Compound',
                                 billing_start_date='2000-01-07', account_type='credit', principal_balance=-1,
                                 accrued_interest=-1, minimum_payment=40)

        budget_set_3.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0',
                                   memo='dummy for test')
        memo_rule_set_3.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None,
                                    transaction_priority=1)

        budget_schedule_3_df = budget_set_3.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_3_df = account_set_3.getAccounts()
        memo_rules_3_df = memo_rule_set_3.getMemoRules()
        forecast_3_df = expense_forecast_obj.computeForecast(budget_schedule_3_df, account_set_3_df, memo_rules_3_df)[2]

        # scenario 4
        initial_values_dict_4 = {}
        initial_values_dict_4['Checking'] = 1000
        initial_values_dict_4['Credit Card Current Statement Balance'] = 10
        initial_values_dict_4['Credit Card Previous Statement Balance'] = 10
        initial_values_dict_4['Credit Card APR'] = 0.2674

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance  Memo
        expected_result_set_4_df = empty_result_set_df.copy()
        expected_result_set_4_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_4[
            'Checking']
        expected_result_set_4_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_4[
                'Credit Card Current Statement Balance']
        expected_result_set_4_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_4['Credit Card Previous Statement Balance']

        expected_result_set_4_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_4[
            'Checking']
        expected_result_set_4_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_4['Credit Card Current Statement Balance']
        expected_result_set_4_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_4['Credit Card Previous Statement Balance']
        # todo further days

        account_set_4 = AccountSet.AccountSet()
        budget_set_4 = BudgetSet.BudgetSet()
        memo_rule_set_4 = MemoRuleSet.MemoRuleSet()

        account_set_4.addAccount(name='Checking', balance=initial_values_dict_4['Checking'], min_balance=0,
                                 max_balance=float('inf'),
                                 apr=0, interest_cadence='None', interest_type='None', billing_start_date='None',
                                 account_type='checking', principal_balance=None, accrued_interest=None)

        account_set_4.addAccount(name='Credit Card',
                                 balance=initial_values_dict_4['Credit Card Current Statement Balance'],
                                 previous_statement_balance=initial_values_dict_4[
                                     'Credit Card Previous Statement Balance'],
                                 min_balance=0,
                                 max_balance=20000, apr=initial_values_dict_4['Credit Card APR'],
                                 interest_cadence='Monthly', interest_type='Compound',
                                 billing_start_date='2000-01-07', account_type='credit', principal_balance=-1,
                                 accrued_interest=-1, minimum_payment=40)

        budget_set_4.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0',
                                   memo='dummy for test')
        memo_rule_set_4.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None,
                                    transaction_priority=1)

        budget_schedule_4_df = budget_set_4.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_4_df = account_set_4.getAccounts()
        memo_rules_4_df = memo_rule_set_4.getMemoRules()
        forecast_4_df = expense_forecast_obj.computeForecast(budget_schedule_4_df, account_set_4_df, memo_rules_4_df)[2]

        # scenario 5
        initial_values_dict_5 = {}
        initial_values_dict_5['Checking'] = 1000
        initial_values_dict_5['Credit Card Current Statement Balance'] = 60
        initial_values_dict_5['Credit Card Previous Statement Balance'] = 0
        initial_values_dict_5['Credit Card APR'] = 0.2674

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance  Memo
        expected_result_set_5_df = empty_result_set_df.copy()
        expected_result_set_5_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_5[
            'Checking']
        expected_result_set_5_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_5[
                'Credit Card Current Statement Balance']
        expected_result_set_5_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_5['Credit Card Previous Statement Balance']

        expected_result_set_5_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_5[
            'Checking']
        expected_result_set_5_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_5['Credit Card Current Statement Balance']
        expected_result_set_5_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_5['Credit Card Previous Statement Balance']
        # todo further days

        account_set_5 = AccountSet.AccountSet()
        budget_set_5 = BudgetSet.BudgetSet()
        memo_rule_set_5 = MemoRuleSet.MemoRuleSet()

        account_set_5.addAccount(name='Checking', balance=initial_values_dict_5['Checking'], min_balance=0,
                                 max_balance=float('inf'),
                                 apr=0, interest_cadence='None', interest_type='None', billing_start_date='None',
                                 account_type='checking', principal_balance=None, accrued_interest=None)

        account_set_5.addAccount(name='Credit Card',
                                 balance=initial_values_dict_5['Credit Card Current Statement Balance'],
                                 previous_statement_balance=initial_values_dict_5[
                                     'Credit Card Previous Statement Balance'],
                                 min_balance=0,
                                 max_balance=20000, apr=initial_values_dict_5['Credit Card APR'],
                                 interest_cadence='Monthly', interest_type='Compound',
                                 billing_start_date='2000-01-07', account_type='credit', principal_balance=-1,
                                 accrued_interest=-1, minimum_payment=40)

        budget_set_5.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0',
                                   memo='dummy for test')
        memo_rule_set_5.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None,
                                    transaction_priority=1)
        budget_set_5.addBudgetItem(start_date='2023-01-06', priority=2, cadence='once', amount=50,
                                   memo='credit card excess payment')
        memo_rule_set_5.addMemoRule(memo_regex='credit card excess payment', account_from='Checking', account_to='Credit',
                                    transaction_priority=2)

        budget_schedule_5_df = budget_set_5.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_5_df = account_set_5.getAccounts()
        memo_rules_5_df = memo_rule_set_5.getMemoRules()
        forecast_5_df = expense_forecast_obj.computeForecast(budget_schedule_5_df, account_set_5_df, memo_rules_5_df)[2]

        # scenario 6
        initial_values_dict_6 = {}
        initial_values_dict_6['Checking'] = 45
        initial_values_dict_6['Credit Card Current Statement Balance'] = 60
        initial_values_dict_6['Credit Card Previous Statement Balance'] = 0
        initial_values_dict_6['Credit Card APR'] = 0.2674

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance  Memo
        expected_result_set_6_df = empty_result_set_df.copy()
        expected_result_set_6_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_6[
            'Checking']
        expected_result_set_6_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_6[
                'Credit Card Current Statement Balance']
        expected_result_set_6_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_6['Credit Card Previous Statement Balance']

        expected_result_set_6_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_6[
            'Checking']
        expected_result_set_6_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_6['Credit Card Current Statement Balance']
        expected_result_set_6_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_6['Credit Card Previous Statement Balance']
        # todo further days

        account_set_6 = AccountSet.AccountSet()
        budget_set_6 = BudgetSet.BudgetSet()
        memo_rule_set_6 = MemoRuleSet.MemoRuleSet()

        account_set_6.addAccount(name='Checking', balance=initial_values_dict_6['Checking'], min_balance=0,
                                 max_balance=float('inf'),
                                 apr=0, interest_cadence='None', interest_type='None', billing_start_date='None',
                                 account_type='checking', principal_balance=None, accrued_interest=None)

        account_set_6.addAccount(name='Credit Card',
                                 balance=initial_values_dict_6['Credit Card Current Statement Balance'],
                                 previous_statement_balance=initial_values_dict_6[
                                     'Credit Card Previous Statement Balance'],
                                 min_balance=0,
                                 max_balance=20000, apr=initial_values_dict_6['Credit Card APR'],
                                 interest_cadence='Monthly', interest_type='Compound',
                                 billing_start_date='2000-01-07', account_type='credit', principal_balance=-1,
                                 accrued_interest=-1, minimum_payment=40)

        budget_set_6.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0',
                                   memo='dummy for test')
        memo_rule_set_6.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None,
                                    transaction_priority=1)
        budget_set_6.addBudgetItem(start_date='2023-01-06', priority=2, cadence='once', amount=50,
                                   memo='credit card excess payment')
        memo_rule_set_6.addMemoRule(memo_regex='credit card excess payment', account_from='Checking',
                                    account_to='Credit',
                                    transaction_priority=2)

        budget_schedule_6_df = budget_set_6.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_6_df = account_set_6.getAccounts()
        memo_rules_6_df = memo_rule_set_6.getMemoRules()
        forecast_6_df = expense_forecast_obj.computeForecast(budget_schedule_6_df, account_set_6_df, memo_rules_6_df)[2]

        # scenario 7
        initial_values_dict_7 = {}
        initial_values_dict_7['Checking'] = 5000
        initial_values_dict_7['Credit Card Current Statement Balance'] = 3000
        initial_values_dict_7['Credit Card Previous Statement Balance'] = 0
        initial_values_dict_7['Credit Card APR'] = 0.2674

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance  Memo
        expected_result_set_7_df = empty_result_set_df.copy()
        expected_result_set_7_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_7[
            'Checking']
        expected_result_set_7_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_7[
                'Credit Card Current Statement Balance']
        expected_result_set_7_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_7['Credit Card Previous Statement Balance']

        expected_result_set_7_df.iloc[1, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict_7[
            'Checking']
        expected_result_set_7_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = \
            initial_values_dict_7['Credit Card Current Statement Balance']
        expected_result_set_7_df.iloc[
            1, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict_7['Credit Card Previous Statement Balance']
        # todo further days

        account_set_7 = AccountSet.AccountSet()
        budget_set_7 = BudgetSet.BudgetSet()
        memo_rule_set_7 = MemoRuleSet.MemoRuleSet()

        account_set_7.addAccount(name='Checking', balance=initial_values_dict_7['Checking'], min_balance=0,
                                 max_balance=float('inf'),
                                 apr=0, interest_cadence='None', interest_type='None', billing_start_date='None',
                                 account_type='checking', principal_balance=None, accrued_interest=None)

        account_set_7.addAccount(name='Credit Card',
                                 balance=initial_values_dict_7['Credit Card Current Statement Balance'],
                                 previous_statement_balance=initial_values_dict_7[
                                     'Credit Card Previous Statement Balance'],
                                 min_balance=0,
                                 max_balance=20000, apr=initial_values_dict_7['Credit Card APR'],
                                 interest_cadence='Monthly', interest_type='Compound',
                                 billing_start_date='2000-01-07', account_type='credit', principal_balance=-1,
                                 accrued_interest=-1, minimum_payment=40)

        budget_set_7.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0',
                                   memo='dummy for test')
        memo_rule_set_7.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None,
                                    transaction_priority=1)
        budget_set_7.addBudgetItem(start_date='2023-01-06', priority=2, cadence='once', amount=4000,
                                   memo='credit card excess payment')
        memo_rule_set_7.addMemoRule(memo_regex='credit card excess payment', account_from='Checking',
                                    account_to='Credit',
                                    transaction_priority=2)

        budget_schedule_7_df = budget_set_7.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_7_df = account_set_7.getAccounts()
        memo_rules_7_df = memo_rule_set_7.getMemoRules()
        forecast_7_df = expense_forecast_obj.computeForecast(budget_schedule_7_df, account_set_7_df, memo_rules_7_df)[2]

        try:

            error_ind = False

            if self.account_boundaries_are_violated(account_set_1.getAccounts(),forecast_1_df) \
                or not forecast_1_df.iloc[:,0:forecast_1_df.shape[1]-1].equals(expected_result_set_1_df.iloc[:,0:expected_result_set_1_df.shape[1]-1]):
                print('FAILURE IN test_credit_card_payments()')
                print('Expected 1 '.ljust(50, '#'))
                print(expected_result_set_1_df.iloc[:, 0:expected_result_set_1_df.shape[1] - 1].to_string())
                print(''.ljust(50, '#'))
                print('Forecasted 1 '.ljust(50, '#'))
                print(forecast_1_df.iloc[:, 0:forecast_1_df.shape[1] - 1].to_string())
                print('#'.ljust(50, '#'))
                error_ind = True

            if self.account_boundaries_are_violated(account_set_2.getAccounts(), forecast_2_df) \
                    or not forecast_2_df.iloc[:, 0:forecast_2_df.shape[1] - 1].equals(expected_result_set_2_df.iloc[:, 0:expected_result_set_2_df.shape[1] - 1]):
                print('Expected 2 '.ljust(50, '#'))
                print(expected_result_set_2_df.iloc[:, 0:expected_result_set_2_df.shape[1] - 1].to_string())
                print(''.ljust(50, '#'))
                print('Forecasted 2 '.ljust(50, '#'))
                print(forecast_2_df.iloc[:, 0:forecast_2_df.shape[1] - 1].to_string())
                print('#'.ljust(50, '#'))
                error_ind = True

            if self.account_boundaries_are_violated(account_set_3.getAccounts(), forecast_3_df) \
                    or not forecast_3_df.iloc[:, 0:forecast_3_df.shape[1] - 1].equals(
                expected_result_set_3_df.iloc[:, 0:expected_result_set_3_df.shape[1] - 1]):
                print('Expected 3 '.ljust(50, '#'))
                print(expected_result_set_3_df.iloc[:, 0:expected_result_set_3_df.shape[1] - 1].to_string())
                print(''.ljust(50, '#'))
                print('Forecasted 3 '.ljust(50, '#'))
                print(forecast_3_df.iloc[:, 0:forecast_3_df.shape[1] - 1].to_string())
                print('#'.ljust(50, '#'))
                error_ind = True

            if self.account_boundaries_are_violated(account_set_4.getAccounts(), forecast_4_df) \
                    or not forecast_4_df.iloc[:, 0:forecast_4_df.shape[1] - 1].equals(
                expected_result_set_4_df.iloc[:, 0:expected_result_set_4_df.shape[1] - 1]):
                print('Expected 4 '.ljust(50, '#'))
                print(expected_result_set_4_df.iloc[:, 0:expected_result_set_4_df.shape[1] - 1].to_string())
                print(''.ljust(50, '#'))
                print('Forecasted 4 '.ljust(50, '#'))
                print(forecast_4_df.iloc[:, 0:forecast_4_df.shape[1] - 1].to_string())
                print('#'.ljust(50, '#'))
                error_ind = True

            if self.account_boundaries_are_violated(account_set_5.getAccounts(), forecast_5_df) \
                    or not forecast_5_df.iloc[:, 0:forecast_5_df.shape[1] - 1].equals(
                expected_result_set_5_df.iloc[:, 0:expected_result_set_5_df.shape[1] - 1]):
                print('Expected 5 '.ljust(50, '#'))
                print(expected_result_set_5_df.iloc[:, 0:expected_result_set_5_df.shape[1] - 1].to_string())
                print(''.ljust(50, '#'))
                print('Forecasted 5 '.ljust(50, '#'))
                print(forecast_5_df.iloc[:, 0:forecast_5_df.shape[1] - 1].to_string())
                print('#'.ljust(50, '#'))
                error_ind = True

            if self.account_boundaries_are_violated(account_set_6.getAccounts(), forecast_6_df) \
                    or not forecast_6_df.iloc[:, 0:forecast_6_df.shape[1] - 1].equals(
                expected_result_set_6_df.iloc[:, 0:expected_result_set_6_df.shape[1] - 1]):
                print('Expected 6 '.ljust(50, '#'))
                print(expected_result_set_6_df.iloc[:, 0:expected_result_set_6_df.shape[1] - 1].to_string())
                print(''.ljust(50, '#'))
                print('Forecasted 6 '.ljust(50, '#'))
                print(forecast_6_df.iloc[:, 0:forecast_6_df.shape[1] - 1].to_string())
                print('#'.ljust(50, '#'))
                error_ind = True

            if self.account_boundaries_are_violated(account_set_7.getAccounts(), forecast_7_df) \
                    or not forecast_7_df.iloc[:, 0:forecast_7_df.shape[1] - 1].equals(
                expected_result_set_7_df.iloc[:, 0:expected_result_set_7_df.shape[1] - 1]):
                print('Expected 7 '.ljust(50, '#'))
                print(expected_result_set_7_df.iloc[:, 0:expected_result_set_7_df.shape[1] - 1].to_string())
                print(''.ljust(50, '#'))
                print('Forecasted 7 '.ljust(50, '#'))
                print(forecast_7_df.iloc[:, 0:forecast_7_df.shape[1] - 1].to_string())
                print('#'.ljust(50, '#'))
                error_ind = True

            if error_ind:
                raise ValueError

        except Exception as e:
            raise e

    def template_test_method(self):

        initial_values_dict = {}
        initial_values_dict['Checking'] = 1000
        initial_values_dict['Credit Card Current Statement Balance'] = 2000
        initial_values_dict['Credit Card Previous Statement Balance'] = 2000
        initial_values_dict['Loan A Principal Balance'] = 3359.17
        initial_values_dict['Loan A Interest'] = 0
        initial_values_dict['Credit Card APR'] = 0.2674
        initial_values_dict['Loan APR'] = 0.0466

        expense_forecast_obj = ExpenseForecast.ExpenseForecast()
        account_set = AccountSet.AccountSet()
        budget_set = BudgetSet.BudgetSet()
        memo_rule_set = MemoRuleSet.MemoRuleSet()

        # account_set.addAccount(name='Loan A',
        #                        balance=initial_values_dict['Loan A Principal Balance'] + initial_values_dict[
        #                            'Loan A Interest'],
        #                        min_balance=0, max_balance=float('inf'),
        #                        apr=initial_values_dict['Loan APR'], interest_cadence='daily', interest_type='Simple',
        #                        billing_start_date='2023-01-03',
        #                        account_type='loan', principal_balance=initial_values_dict['Loan A Principal Balance'],
        #                        accrued_interest=initial_values_dict['Loan A Interest'])
        #
        # budget_set.addBudgetItem(start_date='2023-01-01', priority=1, cadence='daily', amount='0',
        #                          memo='dummy for test')
        # memo_rule_set.addMemoRule(memo_regex='dummy for test', account_from='Checking', account_to=None,
        #                           transaction_priority=1)

        start_date_YYYYMMDD = '20230105'
        start_date = datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d')

        budget_schedule_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD=start_date_YYYYMMDD, num_days=3)
        account_set_df = account_set.getAccounts()
        memo_rules_df = memo_rule_set.getMemoRules()
        forecast_df = expense_forecast_obj.computeForecast(budget_schedule_df, account_set_df, memo_rules_df)

        # Date  Checking    Credit Card: Credit Card Current Statement Balance  Credit Card: Credit Card Previous Statement Balance
        #   Loan A: Loan Principal Balance      Loan A: Loan Interest       Memo

        new_empty_row_df = pd.DataFrame(
            {'Date': [None], 'Checking': [None], 'Credit Card: Current Statement Balance': [None],
             'Credit Card: Previous Statement Balance': [None], 'Loan A: Principal Balance': [None],
             'Loan A: Interest': [None], 'Memo': [None]
             })

        expected_result_set_df = pd.concat([new_empty_row_df.copy(),
                                            new_empty_row_df.copy(),
                                            new_empty_row_df.copy(),
                                            new_empty_row_df.copy()])

        expected_result_set_df.iloc[0, 0] = start_date
        expected_result_set_df.iloc[0, new_empty_row_df.columns.tolist().index('Checking')] = initial_values_dict[
            'Checking']
        expected_result_set_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = initial_values_dict[
            'Credit Card Current Statement Balance']
        expected_result_set_df.iloc[
            0, new_empty_row_df.columns.tolist().index('Credit Card: Previous Statement Balance')] = \
            initial_values_dict['Credit Card Previous Statement Balance']
        expected_result_set_df.iloc[0, new_empty_row_df.columns.tolist().index('Loan A: Principal Balance')] = \
            initial_values_dict['Loan A Principal Balance']
        expected_result_set_df.iloc[0, new_empty_row_df.columns.tolist().index('Loan A: Interest')] = \
            initial_values_dict['Loan A Interest']

        expected_result_set_df.iloc[1, 0] = start_date + datetime.timedelta(days=1)
        expected_result_set_df.iloc[2, 0] = start_date + datetime.timedelta(days=2)
        expected_result_set_df.iloc[3, 0] = start_date + datetime.timedelta(days=3)

        # set expected rows
        # expected_result_set_df.iloc[2, new_empty_row_df.columns.tolist().index('Credit Card: Current Statement Balance')] = 0

        # check that minimum payment is always the max(statement_balance,40,1% of statement balance)
        # Define test input
        ###

        ###

        try:
            self.account_boundaries_are_violated(account_set_df, forecast_df)
            # self.assertTrue(forecast_df.iloc[:,0:expected_result_set_df.shape[1]-1].equals(expected_result_set_df.iloc[:,0:expected_result_set_df.shape[1]-1]))
        except Exception as e:
            print('FAILURE IN test_credit_card_payments()')
            print('Expected '.ljust(50, '#'))
            # print(expected_result_set_df.iloc[:,0:expected_result_set_df.shape[1]-1].to_string())
            print(''.ljust(50, '#'))
            print(' Forecasted'.ljust(50, '#'))
            # print(forecast_df.iloc[:,0:expected_result_set_df.shape[1]-1].to_string())
            print('#'.ljust(50, '#'))
            raise e

    def test_loan_payments(self):
        # expense_forecast_obj = ExpenseForecast.ExpenseForecast()
        # account_set = AccountSet.AccountSet()
        # budget_set = BudgetSet.BudgetSet()
        # memo_rule_set = MemoRuleSet.MemoRuleSet()
        #
        # #Define test input
        # ###
        #
        # ###
        #
        # budget_schedule_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD='20230101', num_days=10)
        # account_set_df = account_set.getAccounts()
        # memo_rules_df = memo_rule_set.getMemoRules()
        # forecast_df = expense_forecast_obj.computeForecast(budget_schedule_df, account_set_df, memo_rules_df)
        # self.account_boundaries_are_violated(account_set_df,forecast_df)
        pass