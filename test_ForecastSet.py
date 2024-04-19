import pytest
import ForecastSet
import BudgetSet
import BudgetItem
import ExpenseForecast
import MilestoneSet
import AccountSet
import MemoRuleSet
import datetime

class TestForecastSet:

    # @pytest.mark.parametrize('core_budget_set,option_budget_set',
    #
    #                          [(BudgetSet.BudgetSet([]),BudgetSet.BudgetSet([]))]
    #
    #                          )
    # def test_ForecastSetConstructor(self,core_budget_set,option_budget_set):
    #     S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)
    #
    # @pytest.mark.parametrize('core_budget_set,option_budget_set',
    #
    #                          [(BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')
    #
    #                                                 ]),
    #                            BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')
    #
    #                                                 ])),
    #
    #                           (BudgetSet.BudgetSet(
    #                               [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')
    #
    #                                ]),
    #                            BudgetSet.BudgetSet(
    #                                [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')
    #
    #                                 ])), #todo make this different from pervious test case
    #
    #                           ]
    #
    #                          )
    # def test_ForecastSetConstructor__expect_fail(self, core_budget_set, option_budget_set):
    #
    #     with pytest.raises(ValueError):
    #         S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)
    #
    # @pytest.mark.parametrize('core_budget_set,option_budget_set',
    #
    #                          [(BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1'),
    #                                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 2'),
    #                                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 3')
    #
    #                                                 ]),
    #                            BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1A'),
    #                                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1B'),
    #                                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1C'),
    #                                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2A'),
    #                                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2B'),
    #                                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2C')
    #                                                 ])),
    #
    #
    #                           ])
    # # def test_addScenario(self,core_budget_set,option_budget_set):
    # #     S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)
    # #
    # #     S.addScenario(['.*A.*'])
    # #     S.addScenario(['.*B.*'])
    # #     S.addScenario(['.*C.*'])
    # #
    # #     print(S)
    #
    # @pytest.mark.parametrize('core_budget_set,option_budget_set',
    #
    #                          [(BudgetSet.BudgetSet(
    #                              [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1'),
    #                               BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 2'),
    #                               BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 3')
    #
    #                               ]),
    #                            BudgetSet.BudgetSet(
    #                                [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1A'),
    #                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1B'),
    #                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1C'),
    #                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1D'),
    #                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2A'),
    #                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2B'),
    #                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2C'),
    #                                 BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2D')
    #                                 ])),
    #
    #                           ])
    # def test_addChoiceToAllForecasts(self,core_budget_set,option_budget_set):
    #     S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)
    #
    #     scenario_A = ['.*A.*']
    #     scenario_B = ['.*B.*']
    #     scenario_C = ['.*C.*']
    #     scenario_D = ['.*D.*']
    #     S.addChoiceToAllForecasts(['A','B'],[scenario_A,scenario_B])
    #     S.addChoiceToAllForecasts(['C','D'],[scenario_C, scenario_D])
    #
    #     print(S)
    #
    # def test_str(self):
    #     raise NotImplementedError
    #
    # def test_renameForecast(self):
    #     raise NotImplementedError

    def test_update_date_range(self):
        start_date = datetime.datetime.now().strftime('%Y%m%d')
        end_date = '20240430'

        A = AccountSet.AccountSet([])
        B1 = BudgetSet.BudgetSet([])
        M = MemoRuleSet.MemoRuleSet([])

        B_optional = BudgetSet.BudgetSet([])
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option A', False, False)
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option B', False, False)
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option C', False, False)
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option D', False, False)

        A.createCheckingAccount('Checking', 5000, 0, 99999)
        B1.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 1', False, False)
        M.addMemoRule('.*', 'Checking', 'None', 1)

        MS = MilestoneSet.MilestoneSet([], [], [])
        E1 = ExpenseForecast.ExpenseForecast(A, B1, M, start_date, end_date, MS)

        option_budget_set = BudgetSet.BudgetSet(
            [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1A'),
             BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1B'),
             BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1C'),
             BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1D'),
             BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2A'),
             BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2B'),
             BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2C'),
             BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2D')
             ])

        S = ForecastSet.ForecastSet(E1, option_budget_set)
        S.addChoiceToAllForecasts(['A', 'B'], [['.*A.*'], ['.*B.*']])
        S.addChoiceToAllForecasts(['C', 'D'], [['.*C.*'], ['.*D.*']])
        S.initialize_forecasts()

        for k, v in S.initialized_forecasts.items():
            print(k,v.unique_id)
        S.update_date_range('20240101','20250101')
        print('---------')
        for k, v in S.initialized_forecasts.items():
            print(k,v.unique_id)

        assert False

    def test_ForecastSet_to_json(self):
        start_date = datetime.datetime.now().strftime('%Y%m%d')
        end_date = '20240430'

        A = AccountSet.AccountSet([])
        B1 = BudgetSet.BudgetSet([])
        M = MemoRuleSet.MemoRuleSet([])

        B_optional = BudgetSet.BudgetSet([])
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option A', False, False)
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option B', False, False)
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option C', False, False)
        B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option D', False, False)

        A.createCheckingAccount('Checking', 5000, 0, 99999)
        B1.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 1', False, False)
        M.addMemoRule('.*', 'Checking', 'None', 1)

        MS = MilestoneSet.MilestoneSet([], [], [])
        E1 = ExpenseForecast.ExpenseForecast(A, B1, M, start_date, end_date, MS)

        option_budget_set = BudgetSet.BudgetSet(
                                   [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1A'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1B'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1C'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1D'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2A'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2B'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2C'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2D')
                                    ])

        S = ForecastSet.ForecastSet(E1, option_budget_set)

        S.addChoiceToAllForecasts(['A', 'B'], [['.*A.*'], ['.*B.*']])
        S.addChoiceToAllForecasts(['C', 'D'], [['.*C.*'], ['.*D.*']])

        S_json = S.to_json()

        S2 = ForecastSet.from_json_string(S_json)

        # print('--------------')
        # print('--------------')
        # print('--------------')
        # print(S.to_json())
        # print('--------------')
        # print('--------------')
        # print('--------------')
        # print(S2.to_json())
        # print('--------------')
        # print('--------------')
        # print('--------------')

        with open('S.json','w') as f:
            f.writelines(S.to_json())

        with open('S2.json','w') as f:
            f.writelines(S2.to_json())


        assert S.base_forecast.to_json() == S2.base_forecast.to_json()
        assert S.option_budget_set.to_json() == S2.option_budget_set.to_json()
        assert S.forecast_set_name == S2.forecast_set_name

        # this doesn't work bc memory addresses
        # assert str(S.forecast_name_to_budget_item_set__dict) == str(S2.forecast_name_to_budget_item_set__dict)
        # assert str(S.initialized_forecasts) == str(S2.initialized_forecasts)
        # assert str(S.id_to_name) == str(S2.id_to_name)

        assert S.forecast_name_to_budget_item_set__dict.keys() == S2.forecast_name_to_budget_item_set__dict.keys()
        assert S.initialized_forecasts.keys() == S2.initialized_forecasts.keys()
        assert S.id_to_name.keys() == S2.id_to_name.keys()

        for k in S.forecast_name_to_budget_item_set__dict.keys():
            assert S.forecast_name_to_budget_item_set__dict[k].to_json() == S2.forecast_name_to_budget_item_set__dict[k].to_json()

        for k in S.initialized_forecasts.keys():
            assert S.initialized_forecasts[k].to_json() == S2.initialized_forecasts[k].to_json()

        for k in S.id_to_name.keys():
            assert S.id_to_name[k] == S2.id_to_name[k]

        assert S.to_json() == S2.to_json()