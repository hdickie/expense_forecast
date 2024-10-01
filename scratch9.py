import ExpenseForecast
# import ForecastHandler
import BudgetSet
import AccountSet
import MemoRuleSet
import MilestoneSet
# import ForecastSet
# import AccountMilestone
import pandas as pd
# import concurrent.futures
# from time import sleep
# import ForecastRunner
import datetime

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???


# import subprocess
# import pebble

# def task(n_seconds):
#     sleep(n_seconds)
#     return 'Done!'

# from generate_date_sequence import generate_date_sequence

if __name__ == '__main__':

    # 1,2,3
    test_case = 4

    start_date_YYYYMMDD = '20240924'
    num_years = 2
    end_date_YYYYMMDD = (datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d') + datetime.timedelta(days=365*num_years)).strftime('%Y%m%d')

    A = AccountSet.AccountSet([])

    # i did already pay my dad and my cc tho, so adjusting cc acct definition and dad loan items to account for that
    A.createCheckingAccount('Checking', 704.93, 0, 999999999, True)
    A.createCreditCardAccount('Credit', 0, 11147.66, 0, 25000, '20241007', 0.2899, 40)

    # 25 daily food series
    # B.addBudgetItem('20240701', '20240701', 1, 'once', 467, 'pay cc extra 7/1/24', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20240801', '20240801', 1, 'once', 252.21, 'pay cc extra 8/1/24', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20240901', '20240901', 1, 'once', 2026.21, 'pay cc extra 9/1/24', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20241001', '20241001', 1, 'once', 2274.0, 'pay cc extra 10/1/24', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20241101', '20241101', 1, 'once', 3650.3, 'pay cc extra 11/1/24', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20241201', '20241201', 1, 'once', 2361.35, 'pay cc extra 12/1/24', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20250101', '20250101', 1, 'once', 2317.54, 'pay cc extra 1/1/25', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20250201', '20250201', 1, 'once', 1866.81, 'pay cc extra 2/1/25', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20250301', '20250301', 1, 'once', 1100, 'pay cc extra 3/1/25', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20250401', '20250401', 1, 'once', 900, 'pay cc cycle 4/1/25', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20250501', '20250501', 1, 'once', 900, 'pay cc cycle 5/1/25', deferrable=False,
    #                 partial_payment_allowed=False)
    # B.addBudgetItem('20250601', '20250601', 1, 'once', 900, 'pay cc cycle 6/1/25', deferrable=False,
    #                 partial_payment_allowed=False)

    B = BudgetSet.BudgetSet([])

    B.addBudgetItem('20240531', end_date_YYYYMMDD, 1, 'semiweekly', 1600, 'EMT income', deferrable=False, partial_payment_allowed=False)

    #1 shift per week, assumes hired in fed, first paycheck hits in march
    # B.addBudgetItem('20240321', end_date_YYYYMMDD, 1, 'semiweekly', 400, 'ER tech income', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20240531', '20241030', 1, 'semiweekly', 1600, 'EMT income', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241031', end_date_YYYYMMDD, 1, 'semiweekly', 1600 * 1.25, 'ER tech income', deferrable=False,partial_payment_allowed=False)

    B.addBudgetItem('20241101', '20260801', 1, 'monthly', 500, 'repay dad', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 40, 'food', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'semiweekly', 80, 'gas', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241008', end_date_YYYYMMDD, 1, 'monthly', 1800, 'pay cc cycle', deferrable=False, partial_payment_allowed=False)




    # B.addBudgetItem('20241201', end_date_YYYYMMDD, 2, 'monthly', 4000, 'pay cc extra', deferrable=False, partial_payment_allowed=True)


    # 40 daily food series
    # B.addBudgetItem('20240908', '20240908', 1, 'once', 1000, 'pay cc extra 9/8/24', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241008', '20241008', 1, 'once', 2499.49, 'pay cc extra 10/8/24', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241108', '20241108', 1, 'once', 3180.43, 'pay cc extra 11/8/24', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241208', '20241208', 1, 'once', 1622.24, 'pay cc extra 12/8/24', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250108', '20250108', 1, 'once', 1685.51, 'pay cc extra 1/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250208', '20250208', 1, 'once', 1196.3, 'pay cc extra 2/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250308', '20250308', 1, 'once', 1709.14, 'pay cc extra 3/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250408', '20250408', 1, 'once', 1675.08, 'pay cc extra 4/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250508', '20250508', 1, 'once', 1688.95, 'pay cc extra 5/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250608', '20250608', 1, 'once', 2802.86, 'pay cc extra 6/8/25', deferrable=False, partial_payment_allowed=False)
    cycle_amount = 1500
    near_cycle_surplus_amount = 500 # + 800 #dad
    B.addBudgetItem('20240908', '20240908', 1, 'once', cycle_amount + near_cycle_surplus_amount, 'pay cc extra 9/8/24', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20241008', '20241008', 1, 'once', cycle_amount + near_cycle_surplus_amount, 'pay cc extra 10/8/24', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20241108', '20241108', 1, 'once', cycle_amount + near_cycle_surplus_amount, 'pay cc extra 11/8/24', deferrable=False, partial_payment_allowed=False)

    # 2 paychecks the previous month
    B.addBudgetItem('20241208', '20241208', 1, 'once', cycle_amount + near_cycle_surplus_amount + 1600, 'pay cc extra 12/8/24', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20250108', '20250108', 1, 'once', cycle_amount + near_cycle_surplus_amount, 'pay cc extra 1/8/25', deferrable=False, partial_payment_allowed=False)

    # 2/7 is a 3 paycheck period wrt to cc when u include 2/7
    B.addBudgetItem('20250206', '20250206', 1, 'once', cycle_amount + near_cycle_surplus_amount + 1600, 'pay cc extra 2/6/25', deferrable=False, partial_payment_allowed=False)


    asymptote_surplus_amount = 500
    B.addBudgetItem('20250308', '20250730', 1, 'monthly', cycle_amount + asymptote_surplus_amount, 'pay cc cycle + extra', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20250830', end_date_YYYYMMDD, 1, 'monthly', cycle_amount - 100 #bc glitch
         , 'pay cc cycle', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250308', '20250308', 1, 'once', cycle_amount + surplus_amount, 'pay cc extra 3/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250408', '20250408', 1, 'once', 1800 + csp, 'pay cc extra 4/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250508', '20250508', 1, 'once', 1800 + csp, 'pay cc extra 5/8/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250608', '20250608', 1, 'once', 1800 + csp, 'pay cc extra 6/8/25', deferrable=False, partial_payment_allowed=False)


    # There is 6 more months of money for this in my MRA, and I am about to get insurance through norcal which should be cheaper?
    #this is def an overestimate so ill take it out for now
    # B.addBudgetItem('20240403', end_date_YYYYMMDD, 1, 'monthly', 268.88, 'health insurance', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20240420', end_date_YYYYMMDD, 1, 'monthly', 95, 'car insurance', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20240401', end_date_YYYYMMDD, 1, 'monthly', 100, 'storage unit rent', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20240818', end_date_YYYYMMDD, 1, 'monthly', 250, 'phone', deferrable=False, partial_payment_allowed=False)
    if int(end_date_YYYYMMDD) > 20251203:
        B.addBudgetItem('20251203', end_date_YYYYMMDD, 1, 'monthly', 250, 'fake loan payment', deferrable=False, partial_payment_allowed=False)

    # if test_case == 1:
    #     B.addBudgetItem('20240603', '20240603', 2, 'once', 5000, 'pay cc', deferrable=False, partial_payment_allowed=True)
    # elif test_case == 2:
    #     B.addBudgetItem('20240603', '20240703', 2, 'monthly', 5000, 'pay cc', deferrable=False, partial_payment_allowed=True)
    # elif test_case == 3:
    #     B.addBudgetItem('20240603', '20240803', 2, 'monthly', 5000, 'pay cc', deferrable=False, partial_payment_allowed=True)
    # elif test_case == 4:
    #     B.addBudgetItem('20240603', end_date_YYYYMMDD, 2, 'monthly', 5000, 'pay cc', deferrable=False, partial_payment_allowed=True)

    # B.addBudgetItem('20240803', '20240803', 1, 'once', 1000, 'pay cc 8/3', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20240901', '20240901', 1, 'once', 2000, 'pay cc 9/1', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241001', '20241001', 1, 'once', 2295, 'pay cc 10/1', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241101', '20241101', 1, 'once', 2250, 'pay cc 11/1', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20241201', '20241201', 1, 'once', 2175, 'pay cc 12/1', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250103', '20250103', 1, 'once', 2800, 'pay cc 1/3/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250203', '20250203', 1, 'once', 2250, 'pay cc 2/3/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20250303', '20250303', 1, 'once', 1050, 'pay cc 3/3/25', deferrable=False, partial_payment_allowed=False)
    #B.addBudgetItem('20250403', '20250403', 1, 'once', 1000, 'pay cc 4/3/25', deferrable=False, partial_payment_allowed=False)
    # B.addBudgetItem('20260803', '20260803', 1, 'once', 5000, 'pay cc 8/3/26', deferrable=False, partial_payment_allowed=False)


    #B.addBudgetItem('20261003', '20270603', 1, 'monthly', 1000, 'fake extra loan payment', deferrable=False, partial_payment_allowed=False)

    #B.addBudgetItem('20240803', '20240803', 1, 'once', 2345, 'phlebotomy tuition', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20240903', '20240903', 1, 'once', 500, 'sjcc fall tuition', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20250203', '20250203', 1, 'once', 400, 'sjcc spring 2025 tuition', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20250603', '20250603', 1, 'once', 400, 'sjcc summer 2025 tuition', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20250803', '20250803', 1, 'once', 400, 'sjcc fall 2025 tuition', deferrable=False, partial_payment_allowed=False)

    #lets put evergreen at 5k for 2 years. wow :)))))))
    # 4 semesters of 9 units. I think that this will include a summer semester
    # this assumes that if I apply at the end of 2025, I dont start til fall 2026
    # ah i realize this is a quarter system I've never done that
    B.addBudgetItem('20260929', '20260929', 1, 'once', 1250, 'evergreen tuition fall 2026', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20270112', '20270112', 1, 'once', 1250, 'evergreen tuition winter 2026', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20270405', '20270405', 1, 'once', 1250, 'evergreen tuition spring 2027', deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem('20270628', '20270628', 1, 'once', 1250, 'evergreen tuition summer 2027', deferrable=False, partial_payment_allowed=False)
    # Summer 2023: June 30
    # Fall 2023: September 29
    # Winter 2024: January 12
    # Spring 2024: April 5
    # Summer 2024: June 28


    # at this point (7/1/26) i have no more debt and tuition is all paid for
    # My 30th birthday!

    # I don't care about having an apartment unless I want to have a sex life, so I kind of want to take the money I make while
    # I'm in nursing school and save for retirement I'll be left w 60k in those years, which, if I save all that, should put be on track

    # sjcc tuition estimate: 1500
    # 8/1 tuition: 2250
    #things to add: tuition, cert tuition
    #I'm gonna finish sjcc end of next year as well

    ##### (5% inflation makes everything 2x in 15 years, historical data says these costs doubled twice in the last 40 years)
    ### Medicare part A - Hospital Insurance
    # medicare is 65 +
    # HOSPITAL inpatient stay
    # Part A deductible: $1,632 as of 2024
    # Days 1-60: $0 after you pay your Part A deductible.
    # Days 61-90: $408 each day.
    # Days 91-150: $816 each day while using your 60 lifetime reserve days.
    # After day 150 (if use all lifetime reserve days at once, else earlier): You pay all costs.
    #
    # SNF inpatient
    # Days 1-20: $0.
    # Days 21-100: $204 each day.
    # Days 101 and beyond: You pay all costs.
    #
    # Home health-care
    # $0 for covered home health care services.
    # 20% of the Medicare-approved amount for equipement
    #
    # Hospice
    # $0 for covered hospice care services.
    # A copayment of up to $5 for each prescription drug and other similar products for pain relief and symptom control while you're at home.
    # 5% of the Medicare-approved amount for inpatient respite care.
    #
    ### Medicare Part B - Medical Insurance
    # the premium appears to double in 20 years and is also based on income bracket
    # $240 yearly deductible
    # (individual tax return)
    # $174.70 for $103k or less
    # $244.60 for $103,000 up to $129,000
    # $349.40 for $129,000 up to $161,000
    # $454.20 for $161,000 up to $193,000
    # $559.00 for $193,000 and less than $500,000
    #
    # services Usually 20% of the cost for each Medicare-covered service or item
    # labs $0
    # home health care $0 for covered home health care services.
    # 20% of the Medicare-approved amount for durable medical equipment (like wheelchairs, walkers, hospital beds, and other equipment).
    # inpatient hospital 20%
    #
    ### Medicare Part D - Drugs
    # seems like a premium of less than $10 but a deductible of $600

    ### the healthcare marketplace out of pocket maximum can be used to plan
    # Medicare parts A and B do no have OOP, but medicare advantage aka Medicare Part C does
    # Part C is a privately offered replacement for parts A and B
    #
    # Part C has a different coverage network than parts A and B

    ## It seems like the biggest thing to keep track of to avoid medical debt is to know your network
    # avoid chornic illness (lol)
    # Also, there is a difference between not getting care and being forced to downsize
    # So health insurance after 65 i am not really worried about

    # Paying for health insurance through an employer seems like it's almost always going to be cheaper
    # I am paying too much for health insurance atm, but I should be able to claim Premium Tax Credit
    # for sure at least when I was unemployed (aka 2023).
    # For 2024, i am pretty sure my payment is still too high given my income level

    # if i spent 150k just on me every year for 40 years of retirement, thats 6 mil damn
    # if I spent 100k for 30 years, thats 3 mil, maybe doable?

    # Lol if I was an EMT And lived in my care my whole life... what would that look like
    # From Google:
    # Among the elderly age 65 and older, the five most expensive conditions were heart conditions, cancer, arthritis and other non-traumatic joint disorders, trauma-related disorders, and chronic obstructive pulmonary disease (COPD) and asthma.




    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('rent', 'Checking', 'None', 1)
    M.addMemoRule('insurance', 'Checking', 'None', 1)
    M.addMemoRule('phlebotomy tuition', 'Credit', 'None', 1)
    M.addMemoRule('sjcc(.*)tuition', 'Checking', 'None', 1)
    M.addMemoRule('evergreen(.*)tuition', 'Checking', 'None', 1)
    M.addMemoRule('food', 'Credit', 'None', 1)
    M.addMemoRule('gas', 'Credit', 'None', 1)
    M.addMemoRule('loan payment', 'Checking', 'None', 1)
    M.addMemoRule('pay cc', 'Checking', 'Credit', 2)
    M.addMemoRule('pay cc', 'Checking', 'Credit', 1)
    M.addMemoRule('.*income.*', 'None', 'Checking', 1)
    M.addMemoRule('.*repay.*', 'Checking', 'None', 1)
    M.addMemoRule('.*phone.*', 'Checking', 'None', 1)

    MS = MilestoneSet.MilestoneSet([], [], [])

    #E_full = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
    E_A = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)

    #E_full.runForecast(log_level='DEBUG')
    E_A.runForecastApproximate(log_level='DEBUG')
    #E_full.forecast_df.to_csv('full_forecast.csv')
    E_A.forecast_df.to_csv('approx_forecast.csv')

    print(E_A.forecast_df.to_string())



    # if test_case in [1,2,3]:
    #     checking_7_7 = E.forecast_df.loc[E.forecast_df.Date == '20240707', :]['Checking'].iat[0]
    #     checking_8_7 = E.forecast_df.loc[E.forecast_df.Date == '20240807', :]['Checking'].iat[0]
    #     prev_7_7 = E.forecast_df.loc[E.forecast_df.Date == '20240707', :]['Credit: Prev Stmt Bal'].iat[0]
    #     prev_8_7 = E.forecast_df.loc[E.forecast_df.Date == '20240807', :]['Credit: Prev Stmt Bal'].iat[0]
    #     md_7_7 = E.forecast_df.loc[E.forecast_df.Date == '20240707', :]['Memo Directives'].iat[0]
    #     md_8_7 = E.forecast_df.loc[E.forecast_df.Date == '20240807', :]['Memo Directives'].iat[0]
    #
    # # e.g. CC MIN PAYMENT ALREADY MADE (Checking -$0.00) ; CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00) ; CC INTEREST (Credit: Prev Stmt Bal +$18.33)
    #
    #
    # print('test_case:'+str(test_case))
    # if test_case == 1:
    #     interest_7_7 = 0
    #     interest_8_7 = 0
    #
    #     print('prev_7_7:' + str(prev_7_7))
    #     # prev_stmt_bal = 1198.32 => 1198.32*0.2899/12 = 28.95 interest
    #     # prev_stmt_bal = 1198.32 => 1198.32*0.1 = 11.98 pbal
    #     # => min payment = 40.93
    #     ### OG value: 1198.32
    #     ### Observed delta: 738.02 = 750 - 40.93 + 28.95
    #     ### Observed value: 1936.34
    #     assert prev_7_7 == 1936.34
    #
    #     print('checking_7_7:' + str(checking_7_7))
    #     assert checking_7_7 == 2759.07
    #
    #     print('md_7_7:' + str(md_7_7))
    #     assert 'CC INTEREST (Credit: Prev Stmt Bal +$'+str(interest_7_7)+')' in md_7_7
    #
    #     print('checking_8_7:' + str(checking_8_7))
    #     assert checking_8_7 == -1
    #
    #     print('prev_8_7:' + str(prev_8_7))
    #     assert prev_8_7 == -1
    #
    #     print('md_8_7:' + str(md_8_7))
    #     assert 'CC INTEREST (Credit: Prev Stmt Bal +$'+str(interest_8_7)+')' in md_8_7
    # elif test_case == 2:
    #     pass
    # elif test_case == 3:
    #     pass
    #
    #     # prev prev stmt bal * APR / 12
    #     # 1198.32  * 0.2899 / 12 = 28.95
    #     interest_7_7 = 28.95 #satsifice was 51.46, after 1st pay was 28.95 (correct)
    #
    #
    #     # this is 8/7 after 1st opt txn
    #     # 20240806  5159.07      750.0       1936.34
    #     # 20240807  5092.93          0       2691.98            CC MIN PAYMENT (Checking -$66.14);  CC MIN PAYMENT (Credit: Prev Stmt Bal -$66.14); CC INTEREST (Credit: Prev Stmt Bal +$46.78)
    #     # 750 + 75 + 1936.34 + 46.78
    #     interest_8_7 = 18.78 #satisfice was 69.06, after 1st pay was 46.78
    #
    #     assert checking_7_7 == 1600
    #     assert prev_7_7 == 723.32 + 25 + interest_7_7  # 723.32 + 25 + 28.95 = 777.27 #28.95 is it correct interest?
    #     assert 'CC INTEREST (Credit: Prev Stmt Bal +$'+str(interest_7_7)+')' in md_7_7
    #
    #     # assert checking_8_7 == 0
    #     # assert prev_8_7 == 750 + 25 + interest_8_7 # 75 + 25 + 18.78 = 118.78
    #     # assert 'CC INTEREST (Credit: Prev Stmt Bal +$18.33)' in md_8_7  # todo interest should be?
