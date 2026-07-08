#scratch.py

from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet

from expense_forecast.MilestoneTriggeredForecastTransition import MilestoneTriggeredForecastTransition

from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.MilestoneSet import MilestoneSet

from expense_forecast.AccountMilestone import AccountMilestone
from expense_forecast.CompositeMilestone import CompositeMilestone

from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ScenarioSpace import ScenarioSpace

import datetime
from datetime import date

def get_B_invariant(food_daily_amount, gas_semiweekly_amount):
    B_invariant = BudgetSet()

    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='daily',amount=food_daily_amount,memo='food expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='semiweekly',amount=gas_semiweekly_amount,memo='gas expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=287.68,memo='phone expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=10,memo='hulu expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,7,2), end_date=end_date, priority=1,
                    cadence='monthly',amount=14,memo='paramount plus expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,6,26), end_date=end_date, priority=1,
                    cadence='monthly',amount=9,memo='netflix expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=100,memo='car insurance expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,7,3), end_date=end_date, priority=1,
                    cadence='monthly',amount=149,memo='storage expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,6,6), end_date=end_date, priority=1,
                    cadence='monthly',amount=129,memo='joyous expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    return B_invariant

# same as before, but food and gas are probably different
def get_B_invariant_post_RN_life():
    B_invariant = BudgetSet()

    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='daily',amount=20,memo='food expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='semiweekly',amount=80,memo='gas expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=287.68,memo='phone expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=10,memo='hulu expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,7,2), end_date=end_date, priority=1,
                    cadence='monthly',amount=14,memo='paramount plus expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,6,26), end_date=end_date, priority=1,
                    cadence='monthly',amount=9,memo='netflix expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=100,memo='car insurance expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,7,3), end_date=end_date, priority=1,
                    cadence='monthly',amount=149,memo='storage expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B_invariant.addBudgetItem(start_date=date(2026,6,6), end_date=end_date, priority=1,
                    cadence='monthly',amount=129,memo='joyous expense',income_flag=False, 
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
                                max_balance=25_000,
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
                        minimum_payment=40, #TODO not sure
                        billing_cycle_payment_balance=0,
                        apr=0.0466)
    A.createLoanAccount(name="Loan B", 
                        principal_balance=4519.90, 
                        interest_balance=67.01, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2026,6,3),
                        minimum_payment=40, #TODO not sure
                        billing_cycle_payment_balance=0,
                        apr=0.0429)
    A.createLoanAccount(name="Loan C", 
                            principal_balance=1969.58, 
                            interest_balance=63.28, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=40, #TODO not sure
                            billing_cycle_payment_balance=0,
                            apr=0.0429)
    A.createLoanAccount(name="Loan D", 
                            principal_balance=4506.0, 
                            interest_balance=52.79, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=40, #TODO not sure
                            billing_cycle_payment_balance=0,
                            apr=0.0376)
    A.createLoanAccount(name="Loan E", 
                            principal_balance=1855.69, 
                            interest_balance=50.18, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=40, #TODO not sure
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

    B_keep_cc_payed_off = BudgetSet()

    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,9,1), end_date=date(2026,9,1), priority=1,
                    cadence='once',amount=5000.0,memo='extra cc payment 1',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,10,1), end_date=date(2026,10,1), priority=1,
                    cadence='once',amount=3000.0,memo='extra cc payment 2',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    # 11/1 2588.23 	
    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,11,1), end_date=date(2026,11,1), priority=1,
                    cadence='once',amount=3450.00,memo='extra cc payment 3',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,12,1), end_date=date(2026,12,1), priority=1,
                    cadence='once',amount=1500.0,memo='citi payment 1',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2027,1,1), end_date=date(2027,1,1), priority=1,
                    cadence='once',amount=1400.0,memo='citi payment 2',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2027,2,1), end_date=date(2027,2,1), priority=1,
                    cadence='once',amount=730.0,memo='citi payment 3',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    # B.addBudgetItem(start_date=date(2026,11,15), end_date=date(2026,11,15), priority=1,
    #                 cadence='once',amount=1010.0,memo='citi payment 2',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    
    # 1010.14 11/13
    
    # B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,11,1), end_date=date(2026,11,1), priority=1,
    #                 cadence='monthly',amount=1533.47,memo='extra cc payment 3',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    
    
    
    # B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,12,1), end_date=end_date, priority=1,
    #                 cadence='monthly',amount=1500,memo='extra cc payment cyclical',income_flag=False, 
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

if __name__ == '__main__':

    # action = 'near term'
    # action = 'start of RN life'
    action = 'net worth 0 after 18 months of RN car life'

    if action == 'near term':

        start_date = date(2026,7,4)
        end_date = start_date + datetime.timedelta(days=365*2)

        A = get_IRL_current_A() #TODO this could take kwargs
        B_invariant = get_B_invariant()
        M = getComprehensiveMemoRules() 

        user_vars = getUserVars()

        ### Dimensions
        # CC Payments
        B_keep_cc_payed_off = getHardCodedCreditCardPayments(user_vars)

        # Housing
        B_live_in_car = BudgetSet() #TODO maybe increase cost of gas ?

        # Work
        B_CNA = BudgetSet()
        B_CNA.addBudgetItem(start_date=user_vars["CNA_first_paycheck_date"], 
                                      end_date=user_vars["start_nursing_school_stop_working_full_time_date"], 
                                      priority=1,
                    cadence='semiweekly',amount=user_vars["CNA_paycheck_amount"],
                    memo='CNA Income Eugene',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)
        
        #assume a 30 day gap i nemployment at least
        B_CNA.addBudgetItem(start_date=user_vars["start_nursing_school_stop_working_full_time_date"] + datetime.timedelta(days=30), 
                                      end_date=user_vars["nursing_school_end_date"], 
                                      priority=1,
                    cadence='semiweekly',
                    amount=user_vars["CNA_paycheck_one_shift_amount"] ,
                    memo='CNA Income Los Angeles',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)

        B = B_invariant + B_keep_cc_payed_off + B_live_in_car + B_CNA

        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        MS = MilestoneSet()

        F = ForecastHandler()
        R = F.runForecast(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        F.generateHTMLReport(R)
        
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

    elif action == 'start of RN life':
        pass

        start_date = date(2030,1,1)
        end_date = start_date + datetime.timedelta(days=365 * 2)

        A = get_hypothetical_A_at_start_of_RN_life()
        B_invariant = get_B_invariant_post_RN_life()
        M = getComprehensiveMemoRules() 
        
        RN_income = BudgetSet()
        RN_income.addBudgetItem( start_date + datetime.timedelta(days=30), 
                                start_date + datetime.timedelta(days=30 + 365), #end date
                                1, 'semiweekly', 2900, 'RN income 1st Year', True)
        # 5% raise after first year
        RN_income.addBudgetItem( start_date + datetime.timedelta(days=30 + 365), 
                                start_date + datetime.timedelta(days=30 + 365*2), #end date
                                1, 'semiweekly', 2900*1.05, 'RN income 2nd Year', True)

        B_keep_cc_payed_off = BudgetSet()
        B_keep_cc_payed_off.addBudgetItem(start_date=date(2030,2,1), end_date=end_date, priority=1,
                    cadence='monthly',amount=1400,memo='extra cc payment cyclical',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
        
        B_loan_payments = BudgetSet()
        B_loan_payments.addBudgetItem(start_date=start_date + datetime.timedelta(days=90), 
                                      end_date=end_date, 
                                      priority=1, cadence="monthly", amount=4_200,
                                      memo='all loan payment')

        B = B_invariant + RN_income + B_keep_cc_payed_off + B_loan_payments
        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        #TODO this is a good next test
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
        R = F.runForecast(IO, MS, include_debug_columns=True)
        R.writeToJSONFile(str(R.unique_id)+'.json')
        F.generateHTMLReport(R)

        user_vars = getUserVars()

        ### 5/9/31 net worth 0

        ### def __init__(self, name, choices=dict[str, BudgetSet])

        ### Dimensions
        # CC Payments
        # this could be invariant just partial payment allowed

        # Housing
        # B_live_in_car = BudgetSet() #TODO maybe increase cost of gas ?
        # B_1500_rent = BudgetSet() #TODO 
        # B_2200_rent = BudgetSet() #TODO 
        # # ...
        # # live in boat!!! #TODO
        # # move to spain in 3 years #TODO
        # # move to spain in 4 years #TODO
        # # move to spain in 5 years #TODO
        # housing = ScenarioDimension("Housing", {
        #     "Live in Car":B_live_in_car,
        #     "Rent 1500":B_1500_rent,
        #     "Rent 2200":B_2200_rent,
        # })

        # # Work
        # RN_employment_not_travel = BudgetSet() #TODO
        # RN_employment_travel_after_1_year = BudgetSet() #TODO
        # RN_employment_travel_after_2_years = BudgetSet() #TODO
        # RN_employment_travel_after_3_years = BudgetSet() #TODO
        # RN_employment_travel_after_4_years = BudgetSet() #TODO
        # # work in spain #TODO

        # work = ScenarioDimension("Work", {
        #     "Staff Nurse for 5 Years":RN_employment_not_travel,
        #     "Travel RN in 1 Year":RN_employment_travel_after_1_year,
        #     "Travel RN in 2 Years":RN_employment_travel_after_2_years,
        #     "Travel RN in 3 Years":RN_employment_travel_after_3_years,
        #     "Travel RN in 4 Years":RN_employment_travel_after_4_years,
        # })

        # scenario_dimensions = {}
        # scenario_dimensions["Housing"] = housing
        # scenario_dimensions["Work"] = work
        
        # S = ScenarioSpace(B_invariant,
        #                 scenario_dimensions,
        #                 M)
        
        # MS = MilestoneSet()
        
        # FS = ForecastSetInitialConditions(IO, S, "The Next 5 Years")

        # F = ForecastHandler()

        # # describe what will be run before I decide to press start
        # F.show_plan(FS)
        
    elif action == 'net worth 0 after 18 months of RN car life':
        pass

        #pushed it out 6 months
        start_date = date(2032, 1, 1)
        end_date = start_date + datetime.timedelta(days=365)

        A = get_hypothetical_A_at_start_of_net_0_life()
        
        B_base = get_B_invariant(20, 80)
        B_retirement_saving = BudgetSet() # TODO

        B_income = BudgetSet()
        B_income.addBudgetItem( start_date, 
                                end_date,
                                1, 'semiweekly', 2900*(1.05**2), 'RN income 3rd Year', True)
        
        B_keep_cc_payed_off = BudgetSet()
        B_keep_cc_payed_off.addBudgetItem(start_date=date(2030,2,1), end_date=end_date, priority=1,
                    cadence='monthly',amount=1400,memo='extra cc payment cyclical',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)

        B = B_base + B_retirement_saving + B_income + B_keep_cc_payed_off

        # M = get_post_net_worth_0_M()
        M = getComprehensiveMemoRules()

        MS = MilestoneSet()

        IO = ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

        F = ForecastHandler()

        milestone_name_to_budget_swap_set = {} #TODO

        fork_set = MilestoneTriggeredForecastTransition(milestone_name_to_budget_swap_set)
        R = F.runForecastWithForks(IO, MS, fork_set, include_debug_columns=True)
        # R = F.runForecast(IO, MS, include_debug_columns=True)
        # R.writeToJSONFile(str(R.unique_id)+'.json')
        # F.generateHTMLReport(R)


        ### Lifestyle Options
        # 1. Stay in Los Angeles in Current Car
        # 2. Get room in Los Angeles 1500
        # 3. Get room in Los Angeles 2200
        ScenarioDimension(name='Lifestyle', choices={
            'Stay in Los Angeles in Current Car': BudgetSet(),
            'Get room in Los Angeles 1500': BudgetSet(),
            'Get room in Los Angeles 2200': BudgetSet(),
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

        raise NotImplementedError