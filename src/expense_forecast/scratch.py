#scratch.py

from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet

from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.MilestoneSet import MilestoneSet

from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ScenarioSpace import ScenarioSpace

import datetime
from datetime import date

def get_B_invariant():
    B_invariant = BudgetSet()

    B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='daily',amount=10,memo='food expense',income_flag=False, 
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

# same as before, but food and gas are probably different
def get_B_invariant_post_RN_life():
    B_invariant = BudgetSet()

    # B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
    #                 cadence='daily',amount=10,memo='food expense',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    # B_invariant.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
    #                 cadence='semiweekly',amount=80,memo='gas expense',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
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
                        minimum_payment=10, #TODO not sure
                        end_of_previous_cycle_balance=3484.34 + 124.33,
                        apr=0.0466) #TODO end_of_previous_cycle_balance shouldn't exist...
    A.createLoanAccount(name="Loan B", 
                        principal_balance=4519.90, 
                        interest_balance=67.01, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2026,6,3),
                        minimum_payment=10, #TODO not sure
                        end_of_previous_cycle_balance=4519.90 + 67.01,
                        apr=0.0429) #TODO end_of_previous_cycle_balance shouldn't exist...  
    A.createLoanAccount(name="Loan C", 
                            principal_balance=1969.58, 
                            interest_balance=63.28, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=10, #TODO not sure
                            end_of_previous_cycle_balance=1969.58 + 63.28,
                            apr=0.0429) #TODO end_of_previous_cycle_balance shouldn't exist...
    A.createLoanAccount(name="Loan D", 
                            principal_balance=4506.0, 
                            interest_balance=52.79, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=10, #TODO not sure
                            end_of_previous_cycle_balance=4506.0 + 52.79,
                            apr=0.0376) #TODO end_of_previous_cycle_balance shouldn't exist...
    A.createLoanAccount(name="Loan E", 
                            principal_balance=1855.69, 
                            interest_balance=50.18, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=10, #TODO not sure
                            end_of_previous_cycle_balance=1855.69 + 50.18,
                            apr=0.0376) #TODO end_of_previous_cycle_balance shouldn't exist...
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
    M.addMemoRule(memo_regex='CNA Income',
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
    return M

def getHardCodedCreditCardPayments():

    B_keep_cc_payed_off = BudgetSet()

    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,9,1), end_date=date(2026,9,1), priority=1,
                    cadence='once',amount=6621.33,memo='extra cc payment 1',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,10,1), end_date=date(2026,10,1), priority=1,
                    cadence='once',amount=2377.50,memo='extra cc payment 2',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    # B.addBudgetItem(start_date=date(2026,11,1), end_date=date(2026,11,1), priority=1,
    #                 cadence='once',amount=2709.27,memo='citi payment 1',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    
    # B.addBudgetItem(start_date=date(2026,11,15), end_date=date(2026,11,15), priority=1,
    #                 cadence='once',amount=1010.0,memo='citi payment 2',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)
    
    # 1010.14 11/13
    
    B_keep_cc_payed_off.addBudgetItem(start_date=date(2026,11,1), end_date=date(2026,11,1), priority=1,
                    cadence='monthly',amount=1533.47,memo='extra cc payment 3',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    # B.addBudgetItem(start_date=date(2026,12,1), end_date=end_date, priority=1,
    #                 cadence='monthly',amount=1150,memo='extra cc payment cyclical',income_flag=False, 
    #                 deferrable=False, partial_payment_allowed=False)

    # approx cc cycle balance 1170

    # 9/1 ADDTL CC PAYMENT (Chase -$6621.33)
    # 10/1 payment $2377.50
    # 11/1 1533.47

    B_keep_cc_payed_off.addBudgetItem(start_date=income_start_date, end_date=start_nursing_school_stop_working_full_time_date, priority=1,
                    cadence='semiweekly',amount=CNA_paycheck_amount,memo='CNA Income',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)
    
    return B_keep_cc_payed_off
    
def getUserVars():
    user_vars = {}

    user_vars["CNA_first_paycheck_date"] = date(2026,8,22)
    user_vars["CNA_paycheck_amount"] = 22.77 * 80 * 0.75 # assume 25% tax at a minimum
    user_vars["start_nursing_school_stop_working_full_time_date"] = date(2028,2,1)
    user_vars["nursing_school_end_date"] = date(2029,12,15)
    user_vars["begin_rn_job_date"] = date(2030,2,1)
    # user_kwargs[""] = 

    return user_vars

def before_RN_life():
    start_date = date(2026,7,4)
    end_date = start_date + datetime.timedelta(days=180)

    A = get_IRL_current_A() #TODO this could take kwargs
    B_invariant = get_B_invariant()
    M = getComprehensiveMemoRules() 

    user_vars = getUserVars()

    ### Dimensions
    # CC Payments
    B_keep_cc_payed_off = getHardCodedCreditCardPayments()

    # Housing
    B_live_in_car = BudgetSet() #TODO maybe increase cost of gas ?

    # Work
    B_1_12_hour_CNA_shift_per_weekend = BudgetSet() #TODO

    F = ForecastHandler()
    
    
        # invariant_transactions: BudgetSet,
        #          scenario_dimensions: dict[str, ScenarioDimension],
        #          memo_rule_set: MemoRuleSet):
    S = ScenarioSpace()
    
    MS = MilestoneSet()
    
    IO = ExpenseForecastInitialConditions(start_date, end_date, A,B,M)

    R = F.runForecast(IO, MS, include_debug_columns=True)

    R.writeToJSONFile(str(R.unique_id)+'.json')
    F.generateHTMLReport(R)
    print(R.forecast_df.to_string())

def get_hypothetical_A_at_start_of_RN_life():
    A = AccountSet()
    raise NotImplementedError
    return A

if __name__ == '__main__':

    # start of RN life

    start_date = date(2030,2,1)
    end_date = start_date + datetime.timedelta(days=180)

    A = get_hypothetical_A_at_start_of_RN_life()
    B_invariant = get_B_invariant_post_RN_life()
    M = getComprehensiveMemoRules() 

    IO = ExpenseForecastInitialConditions(start_date, end_date, A, B_invariant, M)

    user_vars = getUserVars()

    ### def __init__(self, name, choices=dict[str, BudgetSet])

    ### Dimensions
    # CC Payments
    # this could be invariant just partial payment allowed

    # Housing
    B_live_in_car = BudgetSet() #TODO maybe increase cost of gas ?
    B_1500_rent = BudgetSet() #TODO 
    B_2200_rent = BudgetSet() #TODO 
    # ...
    # live in boat!!! #TODO
    # move to spain in 3 years #TODO
    # move to spain in 4 years #TODO
    # move to spain in 5 years #TODO
    housing = ScenarioDimension("Housing", {
        "Live in Car":B_live_in_car,
        "Rent 1500":B_1500_rent,
        "Rent 2200":B_2200_rent,
    })

    # Work
    RN_employment_not_travel = BudgetSet() #TODO
    RN_employment_travel_after_1_year = BudgetSet() #TODO
    RN_employment_travel_after_2_years = BudgetSet() #TODO
    RN_employment_travel_after_3_years = BudgetSet() #TODO
    RN_employment_travel_after_4_years = BudgetSet() #TODO
    # work in spain #TODO
    work = ScenarioDimension("Work", {
        "Staff Nurse for 5 Years":RN_employment_not_travel,
        "Travel RN in 1 Year":RN_employment_travel_after_1_year,
        "Travel RN in 2 Years":RN_employment_travel_after_2_years,
        "Travel RN in 3 Years":RN_employment_travel_after_3_years,
        "Travel RN in 4 Years":RN_employment_travel_after_4_years,
    })

    scenario_dimensions = {}
    scenario_dimensions["Housing"] = housing
    scenario_dimensions["Work"] = work
    
    S = ScenarioSpace(B_invariant,
                      scenario_dimensions,
                      M)
    
    MS = MilestoneSet()
    
    FS = ForecastSetInitialConditions(IO, S, "The Next 5 Years")

    F = ForecastHandler()

    # describe what will be run before I decide to press start
    F.show_plan(FS)
    
