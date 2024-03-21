import ExpenseForecast
import ForecastHandler
import BudgetSet
import AccountSet
import MemoRuleSet
import MilestoneSet
import ForecastSet
import AccountMilestone
import pandas as pd

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

if __name__ == '__main__':
    F = ForecastHandler.ForecastHandler()

    # E = ExpenseForecast.initialize_from_excel_file('./out/approx_test.ods')
    # print('Running '+str(E.unique_id))
    # E.runForecast()
    # F.generateHTMLReport(E,'./out/')
    #
    # #relevant_columns_df = E.forecast_df[['Date','Checking','Memo']]
    #
    # E.forecast_df.to_csv('./out/Forecast_'+str(E.unique_id)+'.csv',index=False)

    #
    # this forecast tells me I need to make about $650 (6 shifts) more than what I am expected to make to pay my tax debt in time
    # I could theoretically move out by may 1... i would have $2400 which should be enough to move
    # an overbudget for tuition for fall is $2k (17 shifts)
    # an additional 2 shifts per week is max, so i could earn that about in 3 months assuming no overtime
    # then I would owe my mom 4 x 1200 = 4800