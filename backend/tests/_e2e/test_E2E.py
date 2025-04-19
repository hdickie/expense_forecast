import pytest
from core.AccountSet import AccountSet
from backend.core.LineItemSet import LineItemSet
from backend.core.DecisionRuleSet import DecisionRuleSet
from core.MilestoneSet import MilestoneSet
from core.ExpenseForecast import ExpenseForecast

from models.account.params import CheckingAccountParams
from models.account.params import CreditCardAccountParams
from models.account.params import LoanAccountParams
from models.lineitem.params import LineItemParams
from models.decisionrule.params import DecisionRuleParams
from models.milestone.params import AccountMilestoneParams

import logging
import datetime
logger = logging.getLogger("test.E2E")

class TestE2E:
    pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_pay_off_credit_card(self):
        pass
        # raise NotImplementedError

    # ;count_skipped_tests = len();print(count_skipped_tests)

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_optimize_loan_payment(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_home_ownership(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_retirement(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_risk_management(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_impulse_spending(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_accruals_and_milestone_tracking(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_define_rich(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_communicate(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_privacy(self):
        pass

    "from junitparser import JUnitXml;xml = JUnitXml.fromfile('test_results.xml');skipped_tests = len([case for suite in xml for case in suite if case.result and case.result[0].type == 'pytest.skip']);print(str(len(xml.tests)));print(str(len(skipped_tests)))"

    @pytest.mark.E2E
    def test_basic_forecast(self):
        A = AccountSet()
        B = LineItemSet()
        M = DecisionRuleSet()
        MS = MilestoneSet()

        start_date_YYYYMMDD = '20250701'
        end_date_YYYYMMDD = '20250801'

        A.createCheckingAccount("Checking",1500,0,float('inf'),True)
        

        E = ExpenseForecast(A,B,M,
                            start_date_YYYYMMDD,
                            end_date_YYYYMMDD,MS)
        E.runForecast()
        # print(E.forecast_df.to_string())
        logger.info('Forecast_ID: '+str(E.unique_id))
        logger.info(E.forecast_df.to_string())

        E.forecast_df.to_csv('/home/hdickie/Github/expense_forecast/csv_out/Forecast_'+str(E.unique_id)+'.csv')

    @pytest.mark.E2E
    def test_motivating_use_case(self):
        A = AccountSet(validate=False) #bc will add checking acocunt later
        B = LineItemSet()
        M = DecisionRuleSet()
        MS = MilestoneSet()

        start_date = datetime.datetime.strptime('2025-04-15','%Y-%m-%d')
        end_date = datetime.datetime.strptime('2026-01-01','%Y-%m-%d')
        credit_bsd = datetime.datetime.strptime('2000-01-07','%Y-%m-%d')

        checking_params = CheckingAccountParams(name="Hume Checking",
                                                balance=1500,
                                                min_balance=0,
                                                max_balance=float('inf'),
                                                primary_checking_ind=True)
        
        credit_params = CreditCardAccountParams(name="Hume Credit", 
                                                balance=10_000, 
                                                current_statement_balance=10_000,
                                                previous_statement_balance=10_000,
                                                end_of_previous_cycle_balance=10_000,
                                               min_balance=0, 
                                                max_balance=24_000,
                                                billing_start_date=credit_bsd, 
                                                apr=0.28, 
                                                minimum_payment=50)
        
        loan_params = LoanAccountParams(name="Sum Loan",
                                        balance=17_000,
                                        min_balance=0,
                                        max_balance=float('inf'),
                                        principal_balance=17_000,
                                        interest_balance=0,
                                        billing_start_date=datetime.datetime.strptime('20000103','%Y%m%d'),
                                        interest_type="simple",
                                        apr=0.05,
                                        interest_cadence="daily",
                                        minimum_payment=223.19,
                                        end_of_previous_cycle_balance=17_000
                                        )
        
        A.createCheckingAccount(checking_params)
        A.createCreditCardAccount(credit_params)
        A.createLoanAccount(loan_params)
        
        food_params = LineItemParams(memo='food', amount=30, 
                                       priority=1, cadence="daily", start_date=start_date, end_date=end_date,
                                       partial_payment_allowed=False,
                                       deferrable=False)
        B.addLineItem(food_params)

        memo_rule_params = DecisionRuleParams(memo_regex='.*', transaction_priority = 1,account_from='Hume Credit')
        M.addDecisionRule(memo_rule_params)

        ### not in the mood
        # account_milstone_params = AccountMilestoneParams(milestone_name = 'checking stays above 5k', 
        #                                                  account_name='Hume Checking',
        #                                                  min_balance=5000)
        # MS.addAccountMilestone(account_milstone_params)

        E = ExpenseForecast(account_set=A,
                            lineitem_set=B,
                            decisionrule_set=M,
                            start_date=start_date,
                            end_date=end_date,
                            milestone_set=MS)
        E.runForecast()
        # print(E.forecast_df.to_string())
        logger.info('Forecast_ID: '+str(E.unique_id))
        logger.info(E.forecast_df.to_string())

        E.forecast_df.to_csv('/home/hdickie/Github/expense_forecast/backend/csv_out/Forecast_'+str(E.unique_id)+'.csv')