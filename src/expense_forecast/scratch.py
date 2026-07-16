#scratch.py

from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
# from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.AccountSet import AccountSet
from expense_forecast.LineItemSet import LineItemSet


from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.ConditionalScenarioTransition import ConditionalScenarioTransition
from expense_forecast.ConditionalScenarioTransitionSet import ConditionalScenarioTransitionSet

from expense_forecast.AccountMilestone import AccountMilestone
from expense_forecast.CompositeMilestone import CompositeMilestone

from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ScenarioSpace import ScenarioSpace
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.SurplusSavingPolicy import SurplusSavingPolicy
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)
from expense_forecast.FixedMonthlyInvestmentPolicy import FixedMonthlyInvestmentPolicy
from expense_forecast.IncomePercentageInvestmentPolicy import IncomePercentageInvestmentPolicy
from expense_forecast.SurplusInvestmentPolicy import SurplusInvestmentPolicy
from expense_forecast.PeriodicInvestmentContributionCapPolicy import PeriodicInvestmentContributionCapPolicy

import datetime
from datetime import date

import inspect

import numpy as np

def get_B_invariant(start_date, end_date):
    B_invariant = LineItemSet()

    # B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
    #                 interval='daily',amount=food_daily_amount,memo='food expense',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='semiweekly',amount=60,memo='gas expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=287.68,memo='phone expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=10,memo='hulu expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=14,memo='paramount plus expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=9,memo='netflix expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=100,memo='car insurance expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=149,memo='storage expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=129,memo='joyous expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    return B_invariant

# same as before, but food and gas are probably different
def get_B_invariant_post_RN_life():
    B_invariant = LineItemSet()

    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='daily',amount=20,memo='food expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='semiweekly',amount=80,memo='gas expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=287.68,memo='phone expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=10,memo='hulu expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=date(2026,7,2), end_date=end_date, priority=1,
                    interval='monthly',amount=14,memo='paramount plus expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=date(2026,6,26), end_date=end_date, priority=1,
                    interval='monthly',amount=9,memo='netflix expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=start_date, end_date=end_date, priority=1,
                    interval='monthly',amount=100,memo='car insurance expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=date(2026,7,3), end_date=end_date, priority=1,
                    interval='monthly',amount=149,memo='storage expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addLineItem(start_date=date(2026,6,6), end_date=end_date, priority=1,
                    interval='monthly',amount=129,memo='joyous expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    return B_invariant

def get_IRL_current_A():
    A = AccountSet()
    A.createAccount(name='Checking',balance=5897.80,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=True)
    A.createAccount(name='Savings',balance=274.69 + 50.52,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=False)
    A.createCreditCardAccount(name='Citi',
                                current_statement_balance=0,
                                previous_statement_balance=3871.98,
                                billing_start_date=date(2026,6,14),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=3871.98,
                                min_balance=0,
                                max_balance=4_000,
                                apr=0.2149)
    A.createCreditCardAccount(name='Chase',
                                current_statement_balance=0,
                                previous_statement_balance=6566.49,
                                billing_start_date=date(2026,6,6),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=6566.49,
                                min_balance=0,
                                max_balance=25_000,
                                apr=0.2724)
    A.createLoanAccount(name="Loan A", 
                        principal_balance=3484.34, 
                        interest_balance=124.33, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2026,6,3),
                        minimum_payment=40,
                        billing_cycle_payment_balance=0,
                        apr=0.0466)
    A.createLoanAccount(name="Loan B", 
                        principal_balance=4519.90, 
                        interest_balance=67.01, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2026,6,3),
                        minimum_payment=40, 
                        billing_cycle_payment_balance=0,
                        apr=0.0429)
    A.createLoanAccount(name="Loan C", 
                            principal_balance=1969.58, 
                            interest_balance=63.28, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=40, 
                            billing_cycle_payment_balance=0,
                            apr=0.0429)
    A.createLoanAccount(name="Loan D", 
                            principal_balance=4506.0, 
                            interest_balance=52.79, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=40, 
                            billing_cycle_payment_balance=0,
                            apr=0.0376)
    A.createLoanAccount(name="Loan E", 
                            principal_balance=1855.69, 
                            interest_balance=50.18, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=40, 
                            billing_cycle_payment_balance=0,
                            apr=0.0376)
    return A
    
def getComprehensiveMemoRules():
    M = MemoRuleSet()

    M.addMemoRule(memo_regex='.*expense.*',
                  account_from='Chase',
                  account_to=None,
                  transaction_priority=1)
    M.addMemoRule(memo_regex='.*cc payment.*',
                  account_from='Checking',
                  account_to='Chase',
                  transaction_priority=1)
    M.addMemoRule(memo_regex='.*income.*',
                  account_from=None,
                  account_to='Checking',
                  transaction_priority=1)
    M.addMemoRule(memo_regex='extra cc payment',
                  account_from='Checking',
                  account_to='Chase',
                  transaction_priority=2)
    M.addMemoRule(memo_regex='citi payment',
                  account_from='Checking',
                  account_to='Citi',
                  transaction_priority=1)
    M.addMemoRule(memo_regex='all loan payment',account_from='Checking',account_to='ALL_LOANS',transaction_priority=1)
    return M

def getHardCodedCreditCardPayments(user_vars):

    B_keep_cc_payed_off = LineItemSet()

    
    B_keep_cc_payed_off.addLineItem(start_date=date(2026,9,1), end_date=date(2026,9,1), priority=1,
                    interval='once',amount=5000.0,memo='extra cc payment 1',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addLineItem(start_date=date(2026,10,1), end_date=date(2026,10,1), priority=1,
                    interval='once',amount=3000.0,memo='extra cc payment 2',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    # 11/1 2588.23 	
    
    B_keep_cc_payed_off.addLineItem(start_date=date(2026,11,1), end_date=date(2026,11,1), priority=1,
                    interval='once',amount=3450.00,memo='extra cc payment 3',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addLineItem(start_date=date(2026,12,1), end_date=date(2026,12,1), priority=1,
                    interval='once',amount=1500.0,memo='citi payment 1',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addLineItem(start_date=date(2027,1,1), end_date=date(2027,1,1), priority=1,
                    interval='once',amount=1400.0,memo='citi payment 2',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addLineItem(start_date=date(2027,2,1), end_date=date(2027,2,1), priority=1,
                    interval='once',amount=730.0,memo='citi payment 3',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    # B.addLineItem(start_date=date(2026,11,15), end_date=date(2026,11,15), priority=1,
    #                 interval='once',amount=1010.0,memo='citi payment 2',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    
    # 1010.14 11/13
    
    # B_keep_cc_payed_off.addLineItem(start_date=date(2026,11,1), end_date=date(2026,11,1), priority=1,
    #                 interval='monthly',amount=1533.47,memo='extra cc payment 3',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    
    
    
    # B_keep_cc_payed_off.addLineItem(start_date=date(2026,12,1), end_date=end_date, priority=1,
    #                 interval='monthly',amount=1500,memo='extra cc payment cyclical',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)

    # approx cc cycle balance 1170

    # 9/1 ADDTL CC PAYMENT (Chase -$6621.33)
    # 10/1 payment $2377.50
    # 11/1 1533.47
    # Citi 11/14  - 3682.21

    return B_keep_cc_payed_off
    
def getUserVars():
    user_vars = {}

    user_vars["CNA_first_paycheck_date"] = date(2026,8,22)
    user_vars["CNA_paycheck_amount"] = 22.77 * 80 * 0.75 # assume 25% tax at a minimum
    user_vars["CNA_paycheck_one_shift_amount"] = 20 * 24 * 0.75 #lower wages in LA, 1 12hr shift per week
    user_vars["start_nursing_school_stop_working_full_time_date"] = date(2027,2,1)
    user_vars["nursing_school_end_date"] = date(2029,12,15)
    user_vars["begin_rn_job_date"] = date(2030,2,1)
    # user_kwargs[""] = 

    return user_vars

# based on vibes
def get_hypothetical_A_at_start_of_RN_life():
    A = AccountSet()
    A.createAccount(name='Checking',balance=5000.0,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=True)
    A.createAccount(name='Savings',balance=500.0,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=False)
    A.createCreditCardAccount(name='Citi',
                                current_statement_balance=0,
                                previous_statement_balance=0,
                                billing_start_date=date(2026,6,14),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=0,
                                min_balance=0,
                                max_balance=25_000,
                                apr=0.2149)
    A.createCreditCardAccount(name='Chase',
                                current_statement_balance=0,
                                previous_statement_balance=0,
                                billing_start_date=date(2026,6,6),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=0,
                                min_balance=0,
                                max_balance=25_000,
                                apr=0.2724)

## Based on Forecast
 #2027-02-01 	3462.75 	3449.99 	12.76 	0.0 	
 #              4458.89 	4443.75 	15.14 	0.0 	
 #              1840.69 	1834.44 	6.25 	0.0 	
 #              4416.34 	4403.19 	13.15 	0.0 	
 #              1705.03 	1699.95 	5.07 	0.0

    length_of_deferral_in_days = (date(2030,1,1) - date(2028,2,1)).days

    # we will add interest ahead of time because deferral is not a feature of this code
    A.createLoanAccount(name="Loan A", 
                        principal_balance=3449.99, 
                        interest_balance=12.76 + 3449.99*(length_of_deferral_in_days/365.25)*0.0466, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2030,1,1),
                        minimum_payment=40, #TODO not sure
                        billing_cycle_payment_balance=0,
                        apr=0.0466)
    A.createLoanAccount(name="Loan B", 
                        principal_balance=4443.75, 
                        interest_balance=15.14 + 4443.75*(length_of_deferral_in_days/365.25)*0.0429, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2030,1,1),
                        minimum_payment=40, #TODO not sure
                        billing_cycle_payment_balance=0,
                        apr=0.0429)
    A.createLoanAccount(name="Loan C", 
                            principal_balance=1834.44, 
                            interest_balance=6.25 + 1834.75*(length_of_deferral_in_days/365.25)*0.0429, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40, #TODO not sure
                            billing_cycle_payment_balance=0,
                            apr=0.0429)
    A.createLoanAccount(name="Loan D", 
                            principal_balance=4403.19, 
                            interest_balance=13.15 + 4403.75*(length_of_deferral_in_days/365.25)*0.0376, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40, #TODO not sure
                            billing_cycle_payment_balance=0,
                            apr=0.0376)
    A.createLoanAccount(name="Loan E", 
                            principal_balance=1699.95, 
                            interest_balance=5.07 + 4403.95*(length_of_deferral_in_days/365.25)*0.0376, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40, #TODO not sure
                            billing_cycle_payment_balance=0,
                            apr=0.0376)
    
    unoptimistic_but_reasonable_apr = 0.1

    disbursement_date_1 = date(2028, 1, 1)
    disbursement_date_2 = date(2028, 9, 1)
    disbursement_date_3 = date(2029, 1, 1)
    disbursement_date_4 = date(2028, 9, 1)

    A.createLoanAccount(name="Subsidized FAFSA Disbursement 1", 
                            principal_balance=9500 / 2, 
                            interest_balance=0, #bc subsidixed
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Subsidized FAFSA Disbursement 2", 
                            principal_balance=9500 / 2, 
                            interest_balance=0, #bc subsidixed
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Subsidized FAFSA Disbursement 3", 
                            principal_balance=10_500 / 2, 
                            interest_balance=0, #bc subsidixed
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Subsidized FAFSA Disbursement 4", 
                            principal_balance=10_500 / 2, 
                            interest_balance=0, #bc subsidixed
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)

    A.createLoanAccount(name="Unsubsidized FAFSA Disbursement 1", 
                            principal_balance=9500 / 2, 
                            interest_balance= (9500 / 2) * ((date(2030,1,1) - disbursement_date_1).days/365.25) * unoptimistic_but_reasonable_apr, 
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Unsubsidized FAFSA Disbursement 2", 
                            principal_balance=9500 / 2, 
                            interest_balance= (9500 / 2) * ((date(2030,1,1) - disbursement_date_2).days/365.25) * unoptimistic_but_reasonable_apr,
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Unsubsidized FAFSA Disbursement 3", 
                            principal_balance=10_500 / 2, 
                            interest_balance=(10_500 / 2) * ((date(2030,1,1) - disbursement_date_3).days/365.25) * unoptimistic_but_reasonable_apr,
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Unsubsidized FAFSA Disbursement 4", 
                            principal_balance=10_500 / 2, 
                            interest_balance=(10_500 / 2) * ((date(2030,1,1) - disbursement_date_4).days/365.25) * unoptimistic_but_reasonable_apr, #bc subsidixed
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)

    A.createLoanAccount(name="Private Disbursement 1", 
                            principal_balance=7000 / 2, 
                            interest_balance= (7000 / 2) * ((date(2030,1,1) - disbursement_date_1).days/365.25) * unoptimistic_but_reasonable_apr, 
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Private Disbursement 2", 
                            principal_balance=7000 / 2, 
                            interest_balance= (7000 / 2) * ((date(2030,1,1) - disbursement_date_2).days/365.25) * unoptimistic_but_reasonable_apr,
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Private Disbursement 3", 
                            principal_balance=7000 / 2, 
                            interest_balance=(7000 / 2) * ((date(2030,1,1) - disbursement_date_3).days/365.25) * unoptimistic_but_reasonable_apr,
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)
    
    A.createLoanAccount(name="Private Disbursement 4", 
                            principal_balance=7000 / 2, 
                            interest_balance=(7000 / 2) * ((date(2030,1,1) - disbursement_date_4).days/365.25) * unoptimistic_but_reasonable_apr, #bc subsidixed
                            min_balance=0,
                            max_balance=float('Inf'),
                            billing_start_date=date(2030,1,1),
                            minimum_payment=40,
                            billing_cycle_payment_balance=0,
                            apr=unoptimistic_but_reasonable_apr)

    return A

def get_hypothetical_A_at_start_of_net_0_life():
    A = AccountSet()
    A.createAccount(name='Checking',balance=0,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=True)
    A.createAccount(name='Savings',balance=500.0,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=False)
    A.createCreditCardAccount(name='Citi',
                                current_statement_balance=0,
                                previous_statement_balance=0,
                                billing_start_date=date(2026,6,14),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=0,
                                min_balance=0,
                                max_balance=25_000,
                                apr=0.2149)
    A.createCreditCardAccount(name='Chase',
                                current_statement_balance=0,
                                previous_statement_balance=0,
                                billing_start_date=date(2026,6,6),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=0,
                                min_balance=0,
                                max_balance=25_000,
                                apr=0.2724)
    return A

def get_post_net_worth_0_M():
    
    M = MemoRuleSet()

    return M

def fuck_off_to_spain(start_date : date, end_date : date) -> LineItemSet:

    L = LineItemSet()

    return L

if __name__ == '__main__':

    # action = 'near term'
    # action = 'start of RN life'
    action = 'second year of RN life'
    # action = 'net worth 0 after 18 months of RN car life'
    # action = 'test approximate case'
    # action = 'test milestone conditional swaps'
    # action = 'dated scenarios and policies'
    # action = 'prioritized policies'
    # action = 'inspect'

    # action = 'I just won the lottery'

    # action = 'example single forecast report'

    if action == 'near term':

        start_date = date(2026,7,14)
        end_date = start_date + datetime.timedelta(days=180)

        A = get_IRL_current_A() #TODO this could take kwargs
        B_invariant = get_B_invariant(15, 80)
        M = getComprehensiveMemoRules() 

        user_vars = getUserVars()

        ### Dimensions
        # CC Payments
        # B_keep_cc_payed_off = getHardCodedCreditCardPayments(user_vars)
        B_keep_cc_payed_off = LineItemSet()
        B_keep_cc_payed_off.addLineItem(start_date=date(2026,9,1), end_date=end_date, priority=2,
                    interval='monthly',amount=5000.0,memo='extra cc payment',income_flag=False, 
                    deferrable=False, partial_payment_allowed=True)

        # Housing
        B_live_in_car = LineItemSet() #TODO maybe increase cost of gas ?

        # Work
        B_CNA = LineItemSet()
        B_CNA.addLineItem(start_date=user_vars["CNA_first_paycheck_date"], 
                                      end_date=user_vars["start_nursing_school_stop_working_full_time_date"], 
                                      priority=1,
                    interval='semiweekly',amount=user_vars["CNA_paycheck_amount"],
                    memo='CNA income Eugene',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)
        
        #assume a 30 day gap i nemployment at least
        B_CNA.addLineItem(start_date=user_vars["start_nursing_school_stop_working_full_time_date"] + datetime.timedelta(days=30), 
                                      end_date=user_vars["nursing_school_end_date"], 
                                      priority=1,
                    interval='semiweekly',
                    amount=user_vars["CNA_paycheck_one_shift_amount"] ,
                    memo='CNA income Los Angeles',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)

        B = B_invariant + B_keep_cc_payed_off + B_live_in_car + B_CNA

        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M, forecast_name='Current State')

        MS = MilestoneSet()

        F = ForecastHandler()
        R = F.runForecastApproximate(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        html_report = F.generateHTMLReport(R, write_file=False)

        with open('test_report.html', "w") as f:
            f.write(html_report)

        
        # S = ScenarioSpace()
        # IO = ExpenseForecastInitialConditions(start_date, end_date, A,B,M)
        # R = F.runForecast(IO, MS, include_debug_columns=True)
        # R.writeToJSONFile(str(R.unique_id)+'.json')
        # F.generateHTMLReport(R)
        # print(R.forecast_df.to_string())


        ### i will et 20k from fafsa over 2 years, I will need 30k to cover the gap, thats living in my car and working 
        # 1 12 hour shift per week (on top of school)
        # if i can make $312.50 per week that makes the difference 
        # my student loans will go into deferrment actually, so thats $200/month i dont need to pay
        # so i will actually need $25k in private loans

    elif action == 'dated scenarios and policies':
        # Demonstrates three related features:
        #   1. dated choices preserve a recurring transaction's cadence;
        #   2. ScenarioSpace values are Scenario objects containing line items
        #      and policies; and
        #   3. a complete choice combination can override the default policies.
        start_date = date(2026, 1, 1)
        transition_date = start_date + datetime.timedelta(days=365)
        end_date = start_date + datetime.timedelta(days=365 * 2)

        accounts = AccountSet()
        accounts.createCheckingAccount(
            'Checking', 5_000, 1_000, float('inf'), True
        )
        accounts.createCheckingAccount(
            'Savings', 0, 0, float('inf'), False
        )

        rn_year_1 = LineItemSet()
        rn_year_1.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2_900,
            memo='RN Year 1 income',
            income_flag=True,
            recurrence_key='RN paycheck',
        )
        rn_year_2 = LineItemSet()
        rn_year_2.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2_900 * 1.05,
            memo='RN Year 2 income',
            income_flag=True,
            recurrence_key='RN paycheck',
        )
        income = ScenarioDimension(
            'Income',
            {'RN Year 1': rn_year_1, 'RN Year 2': rn_year_2},
        )
        dated_income = income.choice_for_date_range(
            'RN Year 1', start_date, transition_date
        ) + income.choice_for_date_range(
            'RN Year 2', transition_date, end_date
        )

        low_food = LineItemSet()
        low_food.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=2,
            interval='daily',
            amount=15,
            memo='food expense',
            partial_payment_allowed=True,
        )
        standard_food = LineItemSet()
        standard_food.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=2,
            interval='daily',
            amount=25,
            memo='food expense',
            partial_payment_allowed=True,
        )
        food = ScenarioDimension(
            'Food', {'Low': low_food, 'Standard': standard_food}
        )

        memo_rules = MemoRuleSet()
        memo_rules.addMemoRule(r'RN Year [12] income', None, 'Checking', 1)
        memo_rules.addMemoRule('food expense', 'Checking', None, 2)

        scenario_space = ScenarioSpace(
            invariant_transactions=dated_income,
            scenario_dimensions={'Food': food},
            memo_rule_set=memo_rules,
            default_policy_set=ForecastPolicySet(
                MinimumCheckingBalancePolicy(
                    account_name='Checking', target=2_000,
                    priority=3, on_unmet='warn',
                )
            ),
            policy_overrides=[
                (
                    {'Food': 'Standard'},
                    ForecastPolicySet(
                        SurplusSavingPolicy(
                            account_name='Savings',
                            saved_minimum_threshold=10_000,
                            priority=3,
                            on_unmet='warn',
                        )
                    ),
                )
            ],
        )

        scenario = scenario_space.scenarios['Standard']
        IO = scenario.to_initial_conditions(
            start_date, end_date, accounts, memo_rules,
            forecast_name='Dated scenario and policy demo',
        )
        R = ForecastHandler.runForecastApproximate(IO)

        paycheck_dates = scenario.line_item_set.getLineItemSchedule().loc[
            lambda schedule: schedule['Memo'].str.contains('RN Year'), 'Date'
        ].tolist()
        transition_window = [
            scheduled_date for scheduled_date in paycheck_dates
            if abs((scheduled_date - transition_date).days) <= 21
        ]
        print('Scenario choices:', scenario.choices)
        print('Scenario policies:', [
            policy.policy_key for policy in scenario.policy_set.policies
        ])
        print('Paychecks around transition:', transition_window)
        print('Paycheck day gaps:', [
            (right - left).days
            for left, right in zip(transition_window, transition_window[1:])
        ])
        print('Safety resolution counts:', {
            method: sum(
                decision['resolution_method'] == method
                for decision in R.safety_decisions
            )
            for method in {'constraint', 'recursive'}
        })
        print('Executed safety decisions:', [
            decision for decision in R.safety_decisions
            if decision['executed'] > 0
        ])

    elif action == 'second year of RN life':

        A = AccountSet.from_dict({'accounts': [{'Name': 'Checking',
               'Balance': 2000.0,
               'Min_Balance': 0,
               'Max_Balance': float('inf'),
               'Account_Type': 'checking',
               'Billing_Start_Date': None,
               'Interest_Type': None,
               'APR': None,
               'Interest_interval': None,
               'Minimum_Payment': None,
               'Primary_Checking_Ind': True},
              {'Name': 'Savings',
               'Balance': 20000.0,
               'Min_Balance': 0,
               'Max_Balance': float('inf'),
               'Account_Type': 'checking',
               'Billing_Start_Date': None,
               'Interest_Type': None,
               'APR': None,
               'Interest_interval': None,
               'Minimum_Payment': None,
               'Primary_Checking_Ind': False},
              {'Name': 'Citi',
               'Balance': 0.0,
               'Min_Balance': 0,
               'Max_Balance': 4000,
               'Account_Type': 'credit',
               'Billing_Start_Date': '2026-06-14',
               'Interest_Type': 'compound',
               'APR': 0.2149,
               'Interest_interval': 'monthly',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Current_Statement_Balance': 0.0,
               'Previous_Statement_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 0.0,
               'End_Of_Previous_Cycle_Balance': 0.0,
               'Minimum_Payment_Floor': 40.0,
               'Minimum_Payment_Credit_Balance': 0.0},
              {'Name': 'Chase',
               'Balance': 0.0,
               'Min_Balance': 0,
               'Max_Balance': 25000,
               'Account_Type': 'credit',
               'Billing_Start_Date': '2026-06-06',
               'Interest_Type': 'compound',
               'APR': 0.2724,
               'Interest_interval': 'monthly',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Current_Statement_Balance': 0.0,
               'Previous_Statement_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 1235.68,
               'End_Of_Previous_Cycle_Balance': 1458.68,
               'Minimum_Payment_Floor': 40.0,
               'Minimum_Payment_Credit_Balance': 0.0},
              {'Name': 'Brokerage',
               'Balance': 19427.08,
               'Min_Balance': 0,
               'Max_Balance': float('inf'),
               'Account_Type': 'investment',
               'Billing_Start_Date': '2030-01-01',
               'Interest_Type': None,
               'APR': 0.07,
               'Interest_interval': None,
               'Minimum_Payment': None,
               'Primary_Checking_Ind': None}]})

        start_date = date(2031,1,1)
        end_date = start_date + datetime.timedelta(days=365 * 1)

        L_invariant = get_B_invariant_post_RN_life()
        M = getComprehensiveMemoRules() 

        unemployed = LineItemSet()
        rn_income_y1 = LineItemSet()
        rn_income_y1.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900,
            memo='RN Year 1 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y2 = LineItemSet()
        rn_income_y2.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*1.05,
            memo='RN Year 2 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y3 = LineItemSet()
        rn_income_y3.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**2),
            memo='RN Year 3 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y4 = LineItemSet()
        rn_income_y4.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**3),
            memo='RN Year 4 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        income = ScenarioDimension(
            name='Income',
            choices={
                'Unemployed': unemployed,
                'RN Year 1': rn_income_y1,
                'RN Year 2': rn_income_y2,
                'RN Year 3': rn_income_y3,
                'RN Year 4': rn_income_y4,
            },
        )
        
        L_income = income.choice_for_date_range(
            "RN Year 2",
            start_date,
            end_date
        )


        L = L_invariant + L_income

        policies = ForecastPolicySet(
            CurrentStatementBalancePaymentPolicy(
                account_name='Chase', priority=1, on_unmet='warn'
            ),
            SurplusDebtPaymentPolicy(
                debt_type='credit', strategy='avalanche',
                priority=2, on_unmet='warn',
            ),

            SurplusInvestmentPolicy(
                account_name='Brokerage', 
                checking_threshold=2_000,
                priority=3, on_unmet='warn',
            ),
            # PeriodicInvestmentContributionCapPolicy(
            #     account_name='Brokerage', limit=1_000,
            #     period='month', priority=3, on_unmet='warn',
            # ),
            # FixedMonthlyInvestmentPolicy(
            #     account_name='Brokerage', amount=300, day=15,
            #     priority=4, on_unmet='warn',
            # ),
            # IncomePercentageInvestmentPolicy(
            #     account_name='Brokerage', percentage=0.10,
            #     priority=5, on_unmet='warn',
            # ),
            
        )

        IO = ExpenseForecastInitialConditions(start_date, end_date, 
                                              A, L, M, 
                                              policy_set = policies, 
                                              forecast_name = 'Second Year of RN Life Still in My Car')

        MS = MilestoneSet()

        F = ForecastHandler()
        R = F.runForecastApproximate(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        # F.generateHTMLReport(R)

        html_report = F.generateHTMLReport(R, write_file=False)

        with open('test_report.html', "w") as f:
            f.write(html_report)

        user_vars = getUserVars()

    elif action == 'start of RN life':
        pass

        start_date = date(2030,1,1)
        end_date = start_date + datetime.timedelta(days=365 * 1)

        A = AccountSet.from_dict({'accounts': [{'Name': 'Checking',
               'Balance': np.float64(2000.0),
               'Min_Balance': 0,
               'Max_Balance': float('inf'),
               'Account_Type': 'checking',
               'Billing_Start_Date': None,
               'Interest_Type': None,
               'APR': None,
               'Interest_interval': None,
               'Minimum_Payment': None,
               'Primary_Checking_Ind': True},
              {'Name': 'Savings',
               'Balance': np.float64(325.21),
               'Min_Balance': 0,
               'Max_Balance': float('inf'),
               'Account_Type': 'checking',
               'Billing_Start_Date': None,
               'Interest_Type': None,
               'APR': None,
               'Interest_interval': None,
               'Minimum_Payment': None,
               'Primary_Checking_Ind': False},
              {'Name': 'Citi',
               'Balance': np.float64(0.0),
               'Min_Balance': 0,
               'Max_Balance': 4000,
               'Account_Type': 'credit',
               'Billing_Start_Date': '2026-06-14',
               'Interest_Type': 'compound',
               'APR': 0.2149,
               'Interest_interval': 'monthly',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Current_Statement_Balance': 0.0,
               'Previous_Statement_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 0.0,
               'End_Of_Previous_Cycle_Balance': 0.0,
               'Minimum_Payment_Floor': 40.0,
               'Minimum_Payment_Credit_Balance': 0.0},
              {'Name': 'Chase',
               'Balance': np.float64(2001.52),
               'Min_Balance': 0,
               'Max_Balance': 25000,
               'Account_Type': 'credit',
               'Billing_Start_Date': '2026-06-06',
               'Interest_Type': 'compound',
               'APR': 0.2724,
               'Interest_interval': 'monthly',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Current_Statement_Balance': 0.0,
               'Previous_Statement_Balance': 2001.52,
               'Billing_Cycle_Payment_Balance': 0.0,
               'End_Of_Previous_Cycle_Balance': 2001.52,
               'Minimum_Payment_Floor': 40.0,
               'Minimum_Payment_Credit_Balance': 0.0},
              {'Name': 'Loan A',
               'Balance': 3588.31,
               'Min_Balance': 0,
               'Max_Balance': 20000,
               'Account_Type': 'loan',
               'Billing_Start_Date': '2026-06-03',
               'Interest_Type': 'simple',
               'APR': 0.0466,
               'Interest_interval': 'daily',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Principal_Balance': 3588.31,
               'Interest_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 0.0},
              {'Name': 'Loan B',
               'Balance': 4663.83,
               'Min_Balance': 0,
               'Max_Balance': 20000,
               'Account_Type': 'loan',
               'Billing_Start_Date': '2026-06-03',
               'Interest_Type': 'simple',
               'APR': 0.0429,
               'Interest_interval': 'daily',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Principal_Balance': 4663.83,
               'Interest_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 0.0},
              {'Name': 'Loan C',
               'Balance': 1880.52,
               'Min_Balance': 0,
               'Max_Balance': 20000,
               'Account_Type': 'loan',
               'Billing_Start_Date': '2026-06-03',
               'Interest_Type': 'simple',
               'APR': 0.0429,
               'Interest_interval': 'daily',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Principal_Balance': 1880.52,
               'Interest_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 0.0},
              {'Name': 'Loan D',
               'Balance': 4634.93,
               'Min_Balance': 0,
               'Max_Balance': 20000,
               'Account_Type': 'loan',
               'Billing_Start_Date': '2026-06-03',
               'Interest_Type': 'simple',
               'APR': 0.0376,
               'Interest_interval': 'daily',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Principal_Balance': 4634.93,
               'Interest_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 0.0},
              {'Name': 'Loan E',
               'Balance': 1744.23,
               'Min_Balance': 0,
               'Max_Balance': 20000,
               'Account_Type': 'loan',
               'Billing_Start_Date': '2026-06-03',
               'Interest_Type': 'simple',
               'APR': 0.0376,
               'Interest_interval': 'daily',
               'Minimum_Payment': 40.0,
               'Primary_Checking_Ind': None,
               'Principal_Balance': 1744.23,
               'Interest_Balance': 0.0,
               'Billing_Cycle_Payment_Balance': 0.0}]})
        A.createInvestmentAccount('Brokerage',0,start_date,apr=0.07)

        L_invariant = get_B_invariant_post_RN_life()
        M = getComprehensiveMemoRules() 

        unemployed = LineItemSet()
        rn_income_y1 = LineItemSet()
        rn_income_y1.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900,
            memo='RN Year 1 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y2 = LineItemSet()
        rn_income_y2.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*1.05,
            memo='RN Year 2 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y3 = LineItemSet()
        rn_income_y3.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**2),
            memo='RN Year 3 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y4 = LineItemSet()
        rn_income_y4.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**3),
            memo='RN Year 4 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        income = ScenarioDimension(
            name='Income',
            choices={
                'Unemployed': unemployed,
                'RN Year 1': rn_income_y1,
                'RN Year 2': rn_income_y2,
                'RN Year 3': rn_income_y3,
                'RN Year 4': rn_income_y4,
            },
        )
        
        L_income = income.choice_for_date_range(
            "RN Year 1",
            start_date,
            start_date + datetime.timedelta(days=365)
        ) + income.choice_for_date_range(
            "RN Year 2",
            start_date + datetime.timedelta(days=365 + 14),
            start_date + datetime.timedelta(days=365*2)
        ) + income.choice_for_date_range(
            "RN Year 3",
            start_date + datetime.timedelta(days=365*2 + 14),
            start_date + datetime.timedelta(days=365*3)
        ) + income.choice_for_date_range(
            "RN Year 4",
            start_date + datetime.timedelta(days=365*3 + 14),
            start_date + datetime.timedelta(days=365*4)
        )

        #in this case is achieved by 10/1 so let's skip the checks and hard code
        # L_emergency_fund = LineItemSet()
        # L_emergency_fund.addLineItem(
        #     start_date=date(2030,10,1),
        #     end_date=date(2030,10,1),
        #     priority=1,
        #     interval='once',
        #     amount=20_000,
        #     memo='save',
        #     income_flag=False,
        #     deferrable=False,
        #     partial_payment_allowed=False,
        # )
        # M.addMemoRule('save','Checking','Savings',1)

        L = L_invariant + L_income #+ L_emergency_fund

        policies = ForecastPolicySet(
            CurrentStatementBalancePaymentPolicy(
                account_name='Chase', priority=1, on_unmet='warn'
            ),
            MinimumCheckingBalancePolicy(
                target=2_000, priority=2, on_unmet='warn'
            ),
            SurplusDebtPaymentPolicy(
                debt_type='credit', strategy='avalanche',
                priority=3, on_unmet='warn',
            ),
            SurplusDebtPaymentPolicy(
                debt_type='loan', strategy='avalanche',
                priority=4, on_unmet='warn',
            ),

            SurplusSavingPolicy(
                account_name="Savings",
                saved_minimum_threshold=20_000,
                priority=5,
                on_unmet="warn",
            ), 

            SurplusInvestmentPolicy(
                account_name='Brokerage', 
                checking_threshold=2_000,
                priority=6, on_unmet='warn',
            ),
            # PeriodicInvestmentContributionCapPolicy(
            #     account_name='Brokerage', limit=1_000,
            #     period='month', priority=3, on_unmet='warn',
            # ),
            # FixedMonthlyInvestmentPolicy(
            #     account_name='Brokerage', amount=300, day=15,
            #     priority=4, on_unmet='warn',
            # ),
            # IncomePercentageInvestmentPolicy(
            #     account_name='Brokerage', percentage=0.10,
            #     priority=5, on_unmet='warn',
            # ),
            
        )

        IO = ExpenseForecastInitialConditions(start_date, end_date, 
                                              A, L, M, 
                                              policy_set = policies, 
                                              forecast_name = 'First Year of RN Life Still in My Car')

        composite_milestone = CompositeMilestone('All OG Loans Paid Off',
                                [
                                    AccountMilestone('Loan A Paid Off','Loan A', 0, 0),
                                    AccountMilestone('Loan B Paid Off','Loan B', 0, 0),
                                    AccountMilestone('Loan C Paid Off','Loan C', 0, 0),
                                    AccountMilestone('Loan D Paid Off','Loan D', 0, 0),
                                    AccountMilestone('Loan E Paid Off','Loan E', 0, 0),
                                 ],
                                None)

        MS = MilestoneSet(account_milestones=[
                            AccountMilestone('All Loans Paid Off','Loan Total',0,0),
                            AccountMilestone('Loan A Paid Off','Loan A', 0, 0),
                            AccountMilestone('Loan B Paid Off','Loan B', 0, 0),
                            AccountMilestone('Loan C Paid Off','Loan C', 0, 0),
                            AccountMilestone('Loan D Paid Off','Loan D', 0, 0),
                            AccountMilestone('Loan E Paid Off','Loan E', 0, 0),

                            
                            ],
                          composite_milestones=[composite_milestone])

        F = ForecastHandler()
        R = F.runForecastApproximate(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        # F.generateHTMLReport(R)

        html_report = F.generateHTMLReport(R, write_file=False)

        with open('test_report.html', "w") as f:
            f.write(html_report)

        user_vars = getUserVars()

        
    elif action == 'net worth 0 after 18 months of RN car life':
        pass

        #pushed it out 6 months
        start_date = date(2032, 1, 1)
        end_date = start_date + datetime.timedelta(days=365)

        A = get_hypothetical_A_at_start_of_net_0_life()
        
        B_base = get_B_invariant(20, 80)
        B_retirement_saving = LineItemSet() # TODO

        B_income = LineItemSet()
        B_income.addLineItem( start_date, 
                                end_date,
                                1, 'semiweekly', 2900*(1.05**2), 'RN income 3rd Year', True)
        
        B_keep_cc_payed_off = LineItemSet()
        B_keep_cc_payed_off.addLineItem(start_date=date(2030,2,1), end_date=end_date, priority=1,
                    interval='monthly',amount=1400,memo='extra cc payment cyclical',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)

        B = B_base + B_retirement_saving + B_income + B_keep_cc_payed_off

        # M = get_post_net_worth_0_M()
        M = getComprehensiveMemoRules()

        MS = MilestoneSet()

        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        F = ForecastHandler()

        milestone_name_to_budget_swap_set = {} #TODO

        # fork_set = MilestoneTriggeredLineItemSetSwapSet(milestone_name_to_budget_swap_set)

        # TODO this method is just for development, eventually runForecast will implement this
        R = F.runForecastWithMilestoneConditionalSwaps(IO, MS, 
                                                       include_debug_columns=True)
        # R = F.runForecast(IO, MS, include_debug_columns=True)
        # R.writeToJSONFile(str(R.unique_id)+'.json')
        # F.generateHTMLReport(R)


        ### Lifestyle Options
        # 1. Stay in Los Angeles in Current Car
        # 2. Get room in Los Angeles 1500
        # 3. Get room in Los Angeles 2200
        ScenarioDimension(name='Lifestyle', choices={
            'Stay in Los Angeles in Current Car': LineItemSet(),
            'Get room in Los Angeles 1500': LineItemSet(),
            'Get room in Los Angeles 2200': LineItemSet(),
        })

        ### Dimensions
        # Personal trainer or not ; lets call it $1000 / mo bc lazy
        # Save for retirements or not 

        ### Goal Options
        # Save up for escalade and live in that
        # Save up for sailboat, then move to Seattle area for a year (staff nurse)
        # Save up to sojourn to spain, become travel nurse, sojourn a few times and then move to spain for a year
        # Put all my extra money into retirement
        
        # TODO in order to do these, I need to be able to stop mid way at a milestone and start a new forecsast
        # starting from there, with A, B, M

        # TODO MS


        # TODO ForecastStateSnapshot
        # TODO MilestoneTriggeredForecastTransition

    elif action == 'test approximate case':


        start_date = date(2030,1,1)
        # end_date = date(2031,10,1)
        end_date = date(2038,5,1)
        # end_date = start_date + datetime.timedelta(days=365 * 10)

        A = get_hypothetical_A_at_start_of_RN_life()
        A.createInvestmentAccount(name='Generic Investment',
                                  balance=0,
                                  billing_start_date=start_date, 
                                  apr=0.07)
        B_invariant = get_B_invariant_post_RN_life()
        M = getComprehensiveMemoRules() 
        M.addMemoRule('Invest','Checking','Generic Investment',1)
        
        RN_income = LineItemSet()
        RN_income.addLineItem( start_date + datetime.timedelta(days=30), 
                                start_date + datetime.timedelta(days=30 + 365), #end date
                                1, 'semiweekly', 2900, 'RN income 1st Year', True)
        # 5% raise after first year
        RN_income.addLineItem( start_date + datetime.timedelta(days=30 + 365), 
                                end_date, #end date
                                1, 'semiweekly', 2900*1.05, 'RN income 2nd Year', True)

        B_keep_cc_payed_off = LineItemSet()
        B_keep_cc_payed_off.addLineItem(start_date=date(2030,2,1), end_date=end_date, priority=1,
                    interval='monthly',amount=1469,memo='extra cc payment cyclical',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
        
        B_loan_payments = LineItemSet()
        B_loan_payments.addLineItem(start_date=start_date + datetime.timedelta(days=90), 
                                      end_date=end_date, 
                                      priority=1, interval="monthly", amount=4_200,
                                      memo='all loan payment')

        B_investment = LineItemSet()
        B_investment.addLineItem(start_date=start_date + datetime.timedelta(days=365*2), 
                                      end_date=end_date, 
                                      priority=1, interval="monthly", amount=4_200,
                                      memo='Invest')
        B = B_invariant + RN_income + B_keep_cc_payed_off + B_loan_payments + B_investment
        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        composite_milestone = CompositeMilestone('All OG Loans Paid Off',
                                [
                                    AccountMilestone('Loan A Paid Off','Loan A', 0, 0),
                                    AccountMilestone('Loan B Paid Off','Loan B', 0, 0),
                                    AccountMilestone('Loan C Paid Off','Loan C', 0, 0),
                                    AccountMilestone('Loan D Paid Off','Loan D', 0, 0),
                                    AccountMilestone('Loan E Paid Off','Loan E', 0, 0),
                                 ],
                                None)

        MS = MilestoneSet(account_milestones=[
                            AccountMilestone('All Loans Paid Off','Loan Total',0,0),
                            AccountMilestone('Loan A Paid Off','Loan A', 0, 0),
                            AccountMilestone('Loan B Paid Off','Loan B', 0, 0),
                            AccountMilestone('Loan C Paid Off','Loan C', 0, 0),
                            AccountMilestone('Loan D Paid Off','Loan D', 0, 0),
                            AccountMilestone('Loan E Paid Off','Loan E', 0, 0),

                            AccountMilestone('Subsidized FAFSA Disbursement 1 Paid Off',
                                             'Subsidized FAFSA Disbursement 1', 0, 0),
                            AccountMilestone('Subsidized FAFSA Disbursement 2 Paid Off',
                                             'Subsidized FAFSA Disbursement 2', 0, 0),
                            AccountMilestone('Subsidized FAFSA Disbursement 3 Paid Off',
                                             'Subsidized FAFSA Disbursement 3', 0, 0),
                            AccountMilestone('Subsidized FAFSA Disbursement 4 Paid Off',
                                             'Subsidized FAFSA Disbursement 4', 0, 0),

                            AccountMilestone('Unsubsidized FAFSA Disbursement 1 Paid Off',
                                             'Unsubsidized FAFSA Disbursement 1', 0, 0),
                            AccountMilestone('Unsubsidized FAFSA Disbursement 2 Paid Off',
                                             'Unsubsidized FAFSA Disbursement 2', 0, 0),
                            AccountMilestone('Unsubsidized FAFSA Disbursement 3 Paid Off',
                                             'Unsubsidized FAFSA Disbursement 3', 0, 0),
                            AccountMilestone('Unsubsidized FAFSA Disbursement 4 Paid Off',
                                             'Unsubsidized FAFSA Disbursement 4', 0, 0),

                            AccountMilestone('Private Disbursement 1 Paid Off',
                                             'Private Disbursement 1', 0, 0),
                            AccountMilestone('Private Disbursement 2 Paid Off',
                                             'Private Disbursement 2', 0, 0),
                            AccountMilestone('Private Disbursement 3 Paid Off',
                                             'Private Disbursement 3', 0, 0),
                            AccountMilestone('Private Disbursement 4 Paid Off',
                                             'Private Disbursement 4', 0, 0),
                            
                            ],
                          composite_milestones=[composite_milestone])

        F = ForecastHandler()
        R = F.runForecastApproximate(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        
        R.writeToJSONFile(str(R.unique_id)+'.json')
        html_report = F.generateHTMLReport(R, write_file=False)

        with open('test_report.html', "w") as f:
            f.write(html_report)
    
    elif action == 'inspect':
        pass
        # TODO list the classes
        # for name, member in inspect.getmembers(Account, inspect.isfunction):
        #     print(name)

    elif action == 'test milestone conditional swaps':
        start_date = date(2026, 7, 1)
        end_date = date(2027, 2, 1)

        accounts = get_IRL_current_A() #TODO this could take kwargs

        memo_rules = getComprehensiveMemoRules() 

        food_very_low = LineItemSet()
        food_very_low.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='daily',
            amount=10,
            memo='very low food expense',
            deferrable=False,
            partial_payment_allowed=False,
        )
        food_average = LineItemSet()
        food_average.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='daily',
            amount=20,
            memo='average food expense',
            deferrable=False,
            partial_payment_allowed=False,
        )
        food = ScenarioDimension(
            name='Food',
            choices={
                'Very Low': food_very_low, #10
                'Average': food_average, #20
            },
        )

        #TODO i assumed y3 and y4 are just 5% raises from prev
        unemployed = LineItemSet()
        cna_income = LineItemSet()
        cna_income.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=22.77 * 80 * 0.75, # assume 25% tax at a minimum
            memo='CNA income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y1 = LineItemSet()
        rn_income_y1.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900,
            memo='RN Year 1 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y2 = LineItemSet()
        rn_income_y2.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*1.05,
            memo='RN Year 2 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y3 = LineItemSet()
        rn_income_y3.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**2),
            memo='RN Year 3 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y4 = LineItemSet()
        rn_income_y4.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**3),
            memo='RN Year 4 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        income = ScenarioDimension(
            name='Income',
            choices={
                'Unemployed': unemployed,
                'CNA': cna_income,
                'RN Year 1': rn_income_y1,
                'RN Year 2': rn_income_y2,
                'RN Year 3': rn_income_y3,
                'RN Year 4': rn_income_y4,
            },
        )

        # The composed LineItemSet remembers both active dimension choices.
        lifestyle = food.select('Very Low') + income.choice_for_date_range(
            "Unemployed",
            start_date,
            date(2026, 8, 22),
        ) + income.choice_for_date_range(
            "CNA",
            date(2026, 8, 22),
            end_date,
        )

        milestones = MilestoneSet({
            'Get job as RN': MemoMilestone(memo_regex=r'RN Year 1 income'),
        })
        transitions = ConditionalScenarioTransitionSet(
            ConditionalScenarioTransition(
                milestone='Get job as RN',
                changes={
                    'Food': 'Average',
                },
            )
        )

        initial_conditions = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=accounts,
            budget_set=lifestyle,
            memo_rule_set=memo_rules,
            milestone_set=milestones,
            transitions=transitions,
        )

        R = ForecastHandler.runForecastApproximate(initial_conditions)
        print('Initial selections:', lifestyle.scenario_selections)
        print('Milestones:', R.milestone_results)
        print(R.forecast_df[['Date', 'Checking', 'Memo']].to_string(index=False))
        # print('Confirmed transactions:')
        # print(result.confirmed_df[['Date', 'Amount', 'Memo']].to_string(index=False))

        R.writeToJSONFile(str(R.unique_id)+'.json')
        
        html_report = ForecastHandler.generateHTMLReport(R, write_file=False)

        with open('test_report.html', "w") as f:
            f.write(html_report)

    elif action == 'prioritized policies':
        # Policies and LineItems share one priority sequence. Policy priorities
        # must be unique and cannot collide with a reachable LineItem priority.
        start_date = date(2026, 8, 1)
        # end_date = start_date + datetime.timedelta(days=180)
        nursing_school_start_date = date(2027, 2, 1)


        start_summer_break_1 = date(2027,5,13)
        end_summer_break_1 = date(2027,7,9)
        start_winter_break_1 = date(2027,12,16)
        end_winter_break_1 = date(2028,1,7)
        start_summer_break_2 = date(2028,5,5)
        end_summer_break_2 = date(2028,6,30)

        graduation = date(2028,12,1)

        # end_date = date(2027,6,1)
        end_date = graduation

        accounts = get_IRL_current_A()
        food_very_low = LineItemSet()
        food_very_low.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='daily',
            amount=10,
            memo='very low food expense',
            deferrable=False,
            partial_payment_allowed=False,
        )
        food_average = LineItemSet()
        food_average.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='daily',
            amount=20,
            memo='average food expense',
            deferrable=False,
            partial_payment_allowed=False,
        )
        food = ScenarioDimension(
            name='Food',
            choices={
                'Very Low': food_very_low, #10
                'Average': food_average, #20
            },
        )

        #TODO i assumed y3 and y4 are just 5% raises from prev
        unemployed = LineItemSet()
        full_time_cna_eugene_income = LineItemSet()
        full_time_cna_eugene_income.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=22.77 * 80 * 0.75, # assume 25% tax at a minimum
            memo='Ful-Time CNA income Eugene',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        part_time_cna_los_angeles_income = LineItemSet()
        part_time_cna_los_angeles_income.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=20 * 24 * 0.75, #lower wages in LA, 1 12hr shift per week
            memo='Part-Time CNA income Los Angeles',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        full_time_cna_los_angeles_income = LineItemSet()
        full_time_cna_los_angeles_income.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=80 * 24 * 0.75, #lower wages in LA, 1 12hr shift per week
            memo='Full-Time CNA income Los Angeles',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y1 = LineItemSet()
        rn_income_y1.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900,
            memo='RN Year 1 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y2 = LineItemSet()
        rn_income_y2.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*1.05,
            memo='RN Year 2 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y3 = LineItemSet()
        rn_income_y3.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**2),
            memo='RN Year 3 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        rn_income_y4 = LineItemSet()
        rn_income_y4.addLineItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            interval='semiweekly',
            amount=2900*(1.05**3),
            memo='RN Year 4 income',
            income_flag=True,
            deferrable=False,
            partial_payment_allowed=False,
        )
        income = ScenarioDimension(
            name='Income',
            choices={
                'Unemployed': unemployed,
                'Part Time CNA Los Angeles': part_time_cna_los_angeles_income,
                'Full Time CNA Los Angeles': full_time_cna_los_angeles_income,
                'Full Time CNA Eugene': full_time_cna_eugene_income,
                'RN Year 1': rn_income_y1,
                'RN Year 2': rn_income_y2,
                'RN Year 3': rn_income_y3,
                'RN Year 4': rn_income_y4,
            },
        )

        # Spring 2028	            Jan 18 to May 12
        # Summer break (8 weeks)	May 13 to July 9
        # Fall 2028	                July 10 to Dec 15
        # Winter break (3 weeks)	Dec 16 to Jan 7
        # Spring 2029	            Jan 8 to May 4
        # Summer break (8 weeks)	May 5 to June 30
        # Fall 2029	                July 1 to Dec 7
        # Graduation	            December 2029


        # The composed LineItemSet remembers both active dimension choices.
        lifestyle = food.select('Average') + income.choice_for_date_range(
            "Unemployed",
            start_date,
            date(2026, 8, 22),
        ) + income.choice_for_date_range(
            "Full Time CNA Eugene",
            date(2026, 8, 22),
            nursing_school_start_date,
        ) + income.choice_for_date_range(
            "Part Time CNA Los Angeles",
            nursing_school_start_date + datetime.timedelta(days=14),
            start_summer_break_1,
        ) + income.choice_for_date_range( #these dont have +2 weeks bc i want to bias conversative
            "Full Time CNA Los Angeles",
            start_summer_break_1,
            end_summer_break_1,
        ) + income.choice_for_date_range(
            "Part Time CNA Los Angeles",
            end_summer_break_1 + datetime.timedelta(days=14),
            start_winter_break_1,
        ) + income.choice_for_date_range(
            "Full Time CNA Los Angeles",
            start_winter_break_1,
            end_winter_break_1,
        ) + income.choice_for_date_range(
            "Part Time CNA Los Angeles",
            end_winter_break_1 + datetime.timedelta(days=14),
            start_summer_break_2,
        ) + income.choice_for_date_range(
            "Full Time CNA Los Angeles",
            start_summer_break_2,
            end_summer_break_2,
        ) + income.choice_for_date_range(
            "Part Time CNA Los Angeles",
            end_summer_break_2 + datetime.timedelta(days=14),
            graduation,
        ) + income.choice_for_date_range(
            "RN Year 1",
            graduation + datetime.timedelta(days=90),
            graduation + datetime.timedelta(days=90 + 365)
        ) + income.choice_for_date_range(
            "RN Year 2",
            graduation + datetime.timedelta(days=90 + 365 + 14),
            graduation + datetime.timedelta(days=90 + 365*2)
        ) + income.choice_for_date_range(
            "RN Year 3",
            graduation + datetime.timedelta(days=90 + 365*2 + 14),
            graduation + datetime.timedelta(days=90 + 365*3)
        ) + income.choice_for_date_range(
            "RN Year 4",
            graduation + datetime.timedelta(days=90 + 365*3 + 14),
            graduation + datetime.timedelta(days=90 + 365*4)
        )


        lifestyle = lifestyle + get_B_invariant(start_date, end_date)
        memo_rules = getComprehensiveMemoRules()
        # memo_rules = MemoRuleSet()
        # memo_rules.addMemoRule(
        #     memo_regex='policy demo income',
        #     account_from=None,
        #     account_to='Checking',
        #     transaction_priority=1,
        # )
        # memo_rules.addMemoRule(
        #     memo_regex='policy demo essential expense',
        #     account_from='Checking',
        #     account_to=None,
        #     transaction_priority=1,
        # )

        policies = ForecastPolicySet(
            CurrentStatementBalancePaymentPolicy(
                account_name='Chase', priority=1, on_unmet='warn'
            ),
            MinimumCheckingBalancePolicy(
                target=2_000, priority=2, on_unmet='warn'
            ),
            # PeriodicInvestmentContributionCapPolicy(
            #     account_name='Brokerage', limit=1_000,
            #     period='month', priority=3, on_unmet='warn',
            # ),
            # FixedMonthlyInvestmentPolicy(
            #     account_name='Brokerage', amount=300, day=15,
            #     priority=4, on_unmet='warn',
            # ),
            # IncomePercentageInvestmentPolicy(
            #     account_name='Brokerage', percentage=0.10,
            #     priority=5, on_unmet='warn',
            # ),
            # SurplusInvestmentPolicy(
            #     account_name='Brokerage', checking_threshold=3_000,
            #     priority=3, on_unmet='warn',
            # ),
            SurplusDebtPaymentPolicy(
                debt_type='credit', strategy='avalanche',
                priority=4, on_unmet='warn',
            ),
            # SurplusDebtPaymentPolicy(
            #     debt_type='loan', strategy='avalanche',
            #     priority=5, on_unmet='warn',
            # ),
        )

        initial_conditions = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=accounts,
            budget_set=lifestyle,
            memo_rule_set=memo_rules,
            policy_set=policies,
            forecast_name='I can pay for Nursing School working part-time during school and full-time during breaks!'
        )
        result = ForecastHandler.runForecastApproximate(initial_conditions)

        # print('Policy results:')
        # for policy_key, policy_result in result.policy_results.items():
        #     print(f'  {policy_key}: {policy_result}')
        # print(result.forecast_df[
        #     ['Date', 'Checking', 'Brokerage', 'Loan Total', 'Memo']
        # ].to_string(index=False))

        result.writeToJSONFile(f'{result.unique_id}.json')
        ForecastHandler.generateHTMLReport(
            result, f'Forecast_{result.unique_id}.html'
        )

    elif action == 'retirement':
        pass

        # retirement at 55
        # retirement at 57
        # retirement at 60
        # semi-retirement at 50
        # Coast FIRE (working part time)
        # retiring in California
        # retiring in Portugal
        # retiring in Spain ; how often can I fly home ???
        # retiring with one paid-off home
        # retiring with rental income
        # delaying Social Security versus claiming early

    elif action == 'I just won the lottery':

        start_date = date(2026,7,4)
        end_date = start_date + datetime.timedelta(days=365*1)


        # I just won 2.5 million dollars

        A = AccountSet()
        A.createAccount(name='Checking',balance=2_500_000 - 3871.98 - 6566.49 - 20_000, #overestimate loans bc i won the lottery who cares
                        min_balance=0,max_balance=float('Inf'),
                        account_type='checking',
                        primary_checking_ind=True)
        
        B_invariant = get_B_invariant(food_daily_amount=50, gas_semiweekly_amount=80)
        M = MemoRuleSet() 
        M.addMemoRule(memo_regex='.*',
                account_from='Checking',
                account_to=None,
                transaction_priority=1)

        # Transactions
        # Take my car to the mechanic and have them fix the doors, come back for it in a week
        
        # implement multiply for LineItemSets ?
        B_all_of_us_fuck_off_to_spain_for_a_week = fuck_off_to_spain()

        

        # Housing
        # Rent 3 bed / 1 ba sf apartment haight ashbury $6k/month
        #     bedroom / gym / office / sewing room
        # use a milestone triggered budget set swap to stop paying for storage, and start paying this rent

        # Work
        # Not working!!!

        B = B_invariant

        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        MS = MilestoneSet()

        F = ForecastHandler()
        R = F.runForecastApproximate(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        F.generateHTMLReport(R)

 

        start_date = date(2026,7,4)
        end_date = start_date + datetime.timedelta(days=365*1)


        # I just won 2.5 million dollars

        A = AccountSet()
        A.createAccount(name='Chase',balance=2_500_000 - 3871.98 - 6566.49 - 20_000, #overestimate loans bc i won the lottery who cares
                        min_balance=0,max_balance=float('Inf'),
                        account_type='checking',
                        primary_checking_ind=True)
        A.createAccount(name='Savings',balance=274.69 + 50.52,
                        min_balance=0,max_balance=float('Inf'),
                        account_type='checking',
                        primary_checking_ind=False)
        
        B_invariant = get_B_invariant(food_daily_amount=50, gas_semiweekly_amount=100)
        M = MemoRuleSet() 
        M.addMemoRule(memo_regex='.*',
                account_from='Chase',
                account_to=None,
                transaction_priority=1)

        # Housing

        # Work

        B = B_invariant

        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        MS = MilestoneSet()

        F = ForecastHandler()
        R = F.runForecastApproximate(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        html_report = F.generateHTMLReport(R, write_file=False)

        with open('test_report.html', "w") as f:
            f.write(html_report)

    elif action == 'example single forecast report':
        
        start_date = date(2026,7,4)
        end_date = start_date + datetime.timedelta(days=90)

        A = get_IRL_current_A() #TODO this could take kwargs
        B_invariant = get_B_invariant()
        M = getComprehensiveMemoRules() 

        user_vars = getUserVars()

        ### Dimensions
        # CC Payments
        B_keep_cc_payed_off = getHardCodedCreditCardPayments(user_vars)

        # Housing
        B_live_in_car = LineItemSet() #TODO maybe increase cost of gas ?

        # Work
        B_CNA = LineItemSet()
        B_CNA.addLineItem(start_date=user_vars["CNA_first_paycheck_date"], 
                                      end_date=user_vars["start_nursing_school_stop_working_full_time_date"], 
                                      priority=1,
                    interval='semiweekly',amount=user_vars["CNA_paycheck_amount"],
                    memo='CNA income Eugene',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)
        
        #assume a 30 day gap i nemployment at least
        B_CNA.addLineItem(start_date=user_vars["start_nursing_school_stop_working_full_time_date"] + datetime.timedelta(days=30), 
                                      end_date=user_vars["nursing_school_end_date"], 
                                      priority=1,
                    interval='semiweekly',
                    amount=user_vars["CNA_paycheck_one_shift_amount"] ,
                    memo='CNA income Los Angeles',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)

        B = B_invariant + B_keep_cc_payed_off + B_live_in_car + B_CNA

        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        MS = MilestoneSet()

        F = ForecastHandler()
        R = F.runForecast(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        
        html_report = F.generateHTMLReport(R, write_file=False)

        with open('test_report.html', "w") as f:
            f.write(html_report)
