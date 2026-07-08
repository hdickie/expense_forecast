import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult

from expense_forecast.AccountMilestone import AccountMilestone
from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.CompositeMilestone import CompositeMilestone

from datetime import date

def get_test_E_IO():

    start_date = date(2000,1,1)
    end_date = date(2000,1,5)

    A = AccountSet()
    A.createCheckingAccount('Checking',1200,0,10_000,True)

    B = BudgetSet()
    B.addBudgetItem(start_date, end_date, 1, 'daily', 300, 'Test Txn', False)

    M = MemoRuleSet()
    M.addMemoRule('.*','Checking',None,1)

    return ExpenseForecastInitialConditions(start_date, end_date, A, B, M)

class TestMilestoneSetIntegration:

    @pytest.mark.integration
    def test_MilestoneSet_AccountMilestone_evaluation(self):
        
        IO = get_test_E_IO()
        MS = MilestoneSet(account_milestones=[AccountMilestone('Account Milestone','Checking',0,0) ])

        R = ForecastHandler().runForecast(IO, MS)

        assert R.milestone_results[0]['Account Milestone'] == date(2000,1,5)

        R.writeToJSONFile('test_MilestoneSet_AccountMilestone_evaluation')
        ForecastHandler().generateHTMLReport(R)


    @pytest.mark.integration
    def test_MilestoneSet_MemoMilestone_evaluation(self):

        IO = get_test_E_IO()
        MS = MilestoneSet(memo_milestones=[MemoMilestone('Memo Milestone','Test Txn') ])

        R = ForecastHandler().runForecast(IO, MS)

        assert R.milestone_results[1]['Memo Milestone'] == date(2000,1,2)

        R.writeToJSONFile('test_MilestoneSet_MemoMilestone_evaluation')
        ForecastHandler().generateHTMLReport(R)

    @pytest.mark.integration
    def test_MilestoneSet_CompositeMilestone_evaluation(self):
        
        IO = get_test_E_IO()
        MS = MilestoneSet(
            composite_milestones=[ CompositeMilestone(
                                    milestone_name='Composite Milestone',
                                    account_milestones=[AccountMilestone('Account Milestone','Checking',0,0)],
                                     memo_milestones=[MemoMilestone('Memo Milestone','Test Txn' ) ] ) ] )
        
        R = ForecastHandler().runForecast(IO, MS)

        assert R.milestone_results[2]['Composite Milestone'] == date(2000,1,5)
        composite_results_df = ForecastHandler()._report_milestone_results_df(
            R, "Composite"
        )
        assert composite_results_df["Milestone"].iat[0] == "Composite Milestone"
        assert composite_results_df["Date"].iat[0].date() == date(2000,1,5)

        R.writeToJSONFile('test_MilestoneSet_CompositeMilestone_evaluation')
        ForecastHandler().generateHTMLReport(R)
        
        



    ## out of scope for now
    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_to_json(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_from_json(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_to_excel(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_from_excel(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_to_database(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_from_database(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_to_csv(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_from_csv(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_log_output(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_MilestoneSet_interactions_w_API_Client_object(self):
    #     pass
