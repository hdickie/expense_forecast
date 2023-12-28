
#import ForecastHandler, ExpenseForecast
import BudgetSet, AccountSet, MemoRuleSet
#import MilestoneSet, MemoMilestone, AccountMilestone

#import CompositeMilestone
import MilestoneSet
import ExpenseForecast
import pandas as pd
import logging
import datetime

log_format = '%(asctime)s - %(levelname)-8s - %(message)s'
l_formatter = logging.Formatter(log_format)

l_stream = logging.StreamHandler()
l_stream.setFormatter(l_formatter)
l_stream.setLevel(logging.INFO)

l_file = logging.FileHandler('scratch__'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.log')
l_file.setFormatter(l_formatter)
l_file.setLevel(logging.INFO)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
logger.handlers.clear()
logger.addHandler(l_stream)
logger.addHandler(l_file)


def compound_loan_A():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan A",balance=1100,min_balance=0,max_balance=1100,account_type="loan",
                    billing_start_date_YYYYMMDD="20240101",interest_type="compound",apr=0.1,interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1000,accrued_interest=100)
    return A.accounts

def compound_loan_A_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan A",balance=1000,min_balance=0,max_balance=1100,account_type="loan",
                    billing_start_date_YYYYMMDD="20240101",interest_type="compound",apr=0.1,interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1000,accrued_interest=0)
    return A.accounts

def compound_loan_B():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan B", balance=1600, min_balance=0, max_balance=1600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.01,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1500, accrued_interest=100)
    return A.accounts

def compound_loan_B_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan B", balance=1500, min_balance=0, max_balance=1600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.01,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1500, accrued_interest=0)
    return A.accounts

def compound_loan_C():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan C", balance=2600, min_balance=0, max_balance=2600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.05,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=2500, accrued_interest=100)
    return A.accounts

def compound_loan_C_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan C", balance=2500, min_balance=0, max_balance=2600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.05,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=2500, accrued_interest=0)
    return A.accounts

def checking():
    A = AccountSet.AccountSet([])
    A.createAccount("test checking", balance=10000, min_balance=0, max_balance=10000, account_type="checking")
    return A.accounts

def cc(curr_bal,prev_bal,apr,bsd):
    A = AccountSet.AccountSet([])
    A.createAccount('test cc',curr_bal,0,20000,'credit',bsd,'compound',apr,'monthly',40,prev_bal)
    return A.accounts


def one_loan__p_1000__i_100__apr_01():
    return AccountSet.AccountSet(checking()+compound_loan_A())

def two_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001():
    return AccountSet.AccountSet(checking() + compound_loan_A() + compound_loan_B())

def three_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001___p_2500__i_100__apr_005():
    return AccountSet.AccountSet(checking() + compound_loan_A() + compound_loan_B() + compound_loan_C())

# def one_loan__p_1000__i_000__apr_01():
#     return AccountSet.AccountSet(checking()+compound_loan_A_no_interest())
#
# def two_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001():
#     return AccountSet.AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest())

def three_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001___p_2500__i_000__apr_005():
    return AccountSet.AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest() + compound_loan_C_no_interest())

if __name__ == '__main__':
    start_date_YYYYMMDD = '20000101'
    end_date_YYYYMMDD = '20000103'

    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])

    account_set.createAccount(name='Checking',
                              balance=5000,
                              min_balance=0,
                              max_balance=float('Inf'),
                              account_type="checking")

    account_set.createAccount('Loan A',1100,0,9999,'loan','20000102','simple',0.1,'daily',50,None,1000,100)
    account_set.createAccount('Loan B', 1100, 0, 9999, 'loan', '20000102', 'simple', 0.05, 'daily', 50, None, 1000, 100)
    account_set.createAccount('Loan C', 1100, 0, 9999, 'loan', '20000102', 'simple', 0.01, 'daily', 50, None, 1000, 100)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=7,
                             cadence='once', amount=1900, memo='additional loan payment',
                             deferrable=False,
                             partial_payment_allowed=True)

    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to='ALL_LOANS', transaction_priority=7)

    milestone_set = MilestoneSet.MilestoneSet(account_set, budget_set, [], [], [])

    E = ExpenseForecast.ExpenseForecast(account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD,
                                        milestone_set,True)

    E.runForecast()

    print(E.forecast_df.to_string())

    # A4 = AccountSet.AccountSet(checking() + cc(499, 501, 0.05, '20000102') + compound_loan_A_no_interest())
    # A4.to_excel('/Users/hume/Github/expense_forecast/A1.xlsx')

    # account_set = AccountSet.AccountSet([])
    #
    # account_set.addAccount(name='Checking',
    #                        balance=1000,
    #                        min_balance=0,
    #                        max_balance=float('Inf'),
    #                        account_type="checking")
    #
    # budget_set = BudgetSet.BudgetSet([])
    # budget_set.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'Core', deferrable=False, partial_payment_allowed=False)
    #
    # account_milestone__list = []
    # memo_milestone__list = []
    # composite_milestone__list = []
    # milestone_names_for_composite_milestone = ['Account Milestone 1','Memo Milestone 1']
    #
    # account_milestone__list.append(AccountMilestone.AccountMilestone('Account Milestone 1','Checking',0,10000))
    # memo_milestone__list.append(MemoMilestone.MemoMilestone('Memo Milestone 1', '.*'))
    #
    # composite_milestone__list.append( CompositeMilestone.CompositeMilestone('composite milestone name 1',account_milestone__list,memo_milestone__list,milestone_names_for_composite_milestone) )
    #
    #
    #
    # MS = MilestoneSet.MilestoneSet(account_set,budget_set,account_milestone__list,memo_milestone__list,composite_milestone__list)

    # F = ForecastHandler.ForecastHandler()
    #
    # F.initialize_from_excel_file('expense_forecast__milestone_testing__input.ods')
    #
    # F.run_forecasts()

    #print(F.read_results_from_disk())



    # E1 = ExpenseForecast.initialize_from_json_file(path_to_json='Forecast__2023_04_07__14_06_02__031534.json')
    # E1.appendSummaryLines()
    #
    # E2 = ExpenseForecast.initialize_from_json_file(path_to_json='Forecast__2023_04_07__13_27_36__020658.json')
    # E2.appendSummaryLines()

    #print(E1.evaulateMemoMilestone('EMT class'))

    #F.generateCompareTwoForecastsHTMLReport(E1,E2)

    # core_budget_set = [['1']]
    #
    # CoreBudgetSet = BudgetSet.BudgetSet([])
    # CoreBudgetSet.addBudgetItem('20000101','20000101',1,'once','1','Core',deferrable=False,partial_payment_allowed=False)
    #
    # BudgetSetA2 = BudgetSet.BudgetSet([])
    # BudgetSetA2.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'A2', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetB2 = BudgetSet.BudgetSet([])
    # BudgetSetB2.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'B2', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetC3 = BudgetSet.BudgetSet([])
    # BudgetSetC3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'C3', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetD3 = BudgetSet.BudgetSet([])
    # BudgetSetD3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'D3', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetE3 = BudgetSet.BudgetSet([])
    # BudgetSetE3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'E3', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetF4 = BudgetSet.BudgetSet([])
    # BudgetSetF4.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'F4', deferrable=False, partial_payment_allowed=False)
    #
    # list_of_lists_of_budget_sets = [
    #     [ BudgetSetA2, BudgetSetB2 ],
    #     [ BudgetSetC3, BudgetSetD3, BudgetSetE3 ],
    #     [ BudgetSetF4 ]
    # ]
    #
    # F = ForecastHandler.ForecastHandler()
    #
    # account_set = AccountSet.AccountSet([])
    # memo_rule_set = MemoRuleSet.MemoRuleSet([])
    #
    # account_set.addAccount(name='Checking',
    #                        balance=1000,
    #                        min_balance=0,
    #                        max_balance=float('Inf'),
    #                        account_type="checking")
    #
    # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
    #
    # F.calculateMultipleChooseOne(account_set, CoreBudgetSet , memo_rule_set, '20000101', '20000103', list_of_lists_of_budget_sets)
#
# FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_dont_recompute_past_days_for_p2plus_transactions - NotImplementedError
# FAILED test_ForecastHandler.py::TestForecastHandlerMethods::test_ForecastHandler_Constructor - NotImplementedError

# account milestone failed to evaluate, but the account name didnt exist in ExpenseForecast, so this should have been caught in the constructor for ExpenseForecast