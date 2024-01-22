import pytest
import ForecastSet
import BudgetSet
import BudgetItem

class TestForecastSet:

    @pytest.mark.parametrize('core_budget_set,option_budget_set',

                             [(BudgetSet.BudgetSet([]),BudgetSet.BudgetSet([]))]

                             )
    def test_ForecastSetConstructor(self,core_budget_set,option_budget_set):
        S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)

    @pytest.mark.parametrize('core_budget_set,option_budget_set',

                             [(BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')

                                                    ]),
                               BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')

                                                    ])),

                              (BudgetSet.BudgetSet(
                                  [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')

                                   ]),
                               BudgetSet.BudgetSet(
                                   [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1')

                                    ])), #todo make this different from pervious test case

                              ]

                             )
    def test_ForecastSetConstructor__expect_fail(self, core_budget_set, option_budget_set):

        with pytest.raises(ValueError):
            S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)

    @pytest.mark.parametrize('core_budget_set,option_budget_set',

                             [(BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1'),
                                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 2'),
                                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 3')

                                                    ]),
                               BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1A'),
                                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1B'),
                                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1C'),
                                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2A'),
                                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2B'),
                                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2C')
                                                    ])),


                              ])
    def test_addScenario(self,core_budget_set,option_budget_set):
        S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)

        S.addScenario(['.*A.*'])
        S.addScenario(['.*B.*'])
        S.addScenario(['.*C.*'])

        print(S)

    @pytest.mark.parametrize('core_budget_set,option_budget_set',

                             [(BudgetSet.BudgetSet(
                                 [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1'),
                                  BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 2'),
                                  BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 3')

                                  ]),
                               BudgetSet.BudgetSet(
                                   [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1A'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1B'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1C'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1D'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2A'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2B'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2C'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2D')
                                    ])),

                              ])
    def test_addChoiceToAllScenarios(self,core_budget_set,option_budget_set):
        S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)

        scenario_A = ['.*A.*']
        scenario_B = ['.*B.*']
        scenario_C = ['.*C.*']
        scenario_D = ['.*D.*']
        S.addChoiceToAllScenarios(['A','B'],[scenario_A,scenario_B])
        S.addChoiceToAllScenarios(['C','D'],[scenario_C, scenario_D])

        print(S)

    def test_listScenarios(self):
        raise NotImplementedError

    def test_str(self):
        raise NotImplementedError

    @pytest.mark.parametrize('core_budget_set,option_budget_set',

                             [(BudgetSet.BudgetSet(
                                 [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 1'),
                                  BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 2'),
                                  BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'core 3')

                                  ]),
                               BudgetSet.BudgetSet(
                                   [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1A'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1B'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1C'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 1D'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2A'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2B'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2C'),
                                    BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 10, 'option 2D')
                                    ])),

                             ])


    def test_listChoices(self):
        raise NotImplementedError

    def test_addCustomLabelToScenario(self):
        raise NotImplementedError