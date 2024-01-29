import AccountMilestone
import AccountSet
import CompositeMilestone
import ForecastHandler
import ExpenseForecast
import BudgetSet
import MemoMilestone
import MemoRuleSet
import MilestoneSet
import ForecastSet

if __name__ == '__main__':

    rerun = True

    F = ForecastHandler.ForecastHandler()

    if rerun:

        start_date_YYYYMMDD = '20240123'
        end_date_YYYYMMDD = '20240301'

        loan_A_pbal = 1000
        loan_A_interest = 100
        loan_A_APR = 0.24
        loan_A_min_payment = 40

        A = AccountSet.AccountSet([])
        A.createAccount('Checking', 4000, 0, 99999, 'checking')
        A.createAccount('Loan A', loan_A_pbal + loan_A_interest, 0, 25000, 'loan', '20240127', 'simple', loan_A_APR,
                        'daily', loan_A_min_payment, None, loan_A_pbal, loan_A_interest)

        core_budget_set = BudgetSet.BudgetSet([])
        core_budget_set.addBudgetItem('20000101', '20000101', 1, 'daily', 10, 'core txn', False, False)

        option_budget_set = BudgetSet.BudgetSet([])
        option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 10, 'txn 1A', False, False)
        option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 20, 'txn 1B', False, False)
        option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 30, 'txn 2A', False, False)
        option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 40, 'txn 2B', False, False)

        option_budget_set.addBudgetItem('20240201', '20240201', 1, 'once', 1000, 'txn 1C', False, False)  # 2/1 2k
        option_budget_set.addBudgetItem('20240222', '20240222', 1, 'once', 1000, 'txn 1D', False, False)  # 2/22 2k
        option_budget_set.addBudgetItem('20240201', '20240201', 2, 'once', 500, 'txn 2C', False, False)  # 2/1 1k
        option_budget_set.addBudgetItem('20240222', '20240222', 2, 'once', 500, 'txn 2D', False, False)  # 2/22 1;

        M = MemoRuleSet.MemoRuleSet([])
        M.addMemoRule('.*txn.*', 'Checking', None, 1)
        M.addMemoRule('.*txn.*', 'Checking', None, 2)
        M.addMemoRule('.*income.*', None, 'Checking', 1)

        MS = MilestoneSet.MilestoneSet([AccountMilestone.AccountMilestone('NetWorth > 0','Net Worth',-999999,0),
                                        AccountMilestone.AccountMilestone('NetWorth < 0','Net Worth',0,999999)
                                        ], [], [])

        S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)

        # todo
        scenario_A = ['.*A.*']
        scenario_B = ['.*B.*']
        scenario_C = ['.*C.*']
        scenario_D = ['.*D.*']
        S.addChoiceToAllScenarios(['A', 'B'], [scenario_A, scenario_B])
        S.addChoiceToAllScenarios(['C', 'D'], [scenario_C, scenario_D])

        E__dict = F.initialize_forecasts_with_scenario_set(A, S, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
        #E__dict = F.run_forecast_set(E__dict)
        E__dict = F.run_forecast_set_parallel(E__dict)
    else:
        list_of_file_names = ['Forecast_012619.json','Forecast_059579.json','Forecast_089140.json','Forecast_082983.json']
        E__dict = F.initialize_forecasts_from_file('./',list_of_file_names)

        MS = MilestoneSet.MilestoneSet([AccountMilestone.AccountMilestone('NetWorth < 0', 'Net Worth', -999999, 0),
                                        AccountMilestone.AccountMilestone('NetWorth > 0', 'Net Worth', 0, 999999),
                                        AccountMilestone.AccountMilestone('Net Worth Below 500', 'Net Worth', -999999, 500),
                                        AccountMilestone.AccountMilestone('Net Worth Below 200', 'Net Worth', -999999, 200)
                                        ],
                                       [MemoMilestone.MemoMilestone('txn 2C','txn 2C')],
                                       [CompositeMilestone.CompositeMilestone('2C and neg net worth',
                                                                              [AccountMilestone.AccountMilestone('NetWorth < 0', 'Net Worth', -999999, 0)],
                                                                              [MemoMilestone.MemoMilestone('txn 2C','txn 2C')]
                                                                              )])
        for key, value in E__dict.items():
            E__dict[key].milestone_set = MS
            E__dict[key].evaluateMilestones()

    F.generateScenarioSetHTMLReport(E__dict)

# worst case vs. er tech and $400 cc payments
# Forecast_068993 vs. Forecast_063709