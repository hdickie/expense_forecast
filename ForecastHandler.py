import copy
import ExpenseForecast, datetime
from log_methods import log_in_color
import BudgetSet
import json
import pandas as pd
from multiprocessing import Pool
import AccountSet
import BudgetSet
import MemoRuleSet

class ForecastHandler:

    def __init__(self):
        pass

    def initialize_from_excel_file(self,path_to_excel_file):
        AccountSet_df = pd.read_excel(path_to_excel_file, sheet_name='AccountSet')
        BudgetSet_df = pd.read_excel(path_to_excel_file, sheet_name='BudgetSet')
        MemoRuleSet_df = pd.read_excel(path_to_excel_file, sheet_name='MemoRuleSet')
        ChooseOneSet_df = pd.read_excel(path_to_excel_file, sheet_name='ChooseOneSet')
        AccountMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='AccountMilestones')
        MemoMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='MemoMilestones')
        CompositeMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='CompositeMilestones')
        config_df = pd.read_excel(path_to_excel_file, sheet_name='config')

        A = AccountSet.AccountSet([])
        M = MemoRuleSet.MemoRuleSet([])

        for account_index, account_row in AccountSet_df.iterrows():
            A.addAccount(account_row.Name,
                   account_row.Balance,
                   account_row.Min_Balance,
                   account_row.Max_Balance,
                   account_row.Account_Type,
                   billing_start_date_YYYYMMDD=account_row.Billing_Start_Dt,
                   interest_type=account_row.Interest_Type,
                   apr=account_row.APR,
                   interest_cadence=account_row.Interest_Cadence,
                   minimum_payment=account_row.Minimum_Payment,
                   previous_statement_balance=account_row.Previous_Statement_Balance,
                   principal_balance=account_row.Principal_Balance,
                   accrued_interest=account_row.Accrued_Interest)

        for memorule_index, memorule_row in MemoRuleSet_df.iterrows():
            M.addMemoRule(memorule_row.Memo_Regex,memorule_row.Account_From,memorule_row.Account_To,memorule_row.Transaction_Priority)

        og_budget_match_vec = [False] * BudgetSet_df.shape[0]
        og_memo_match_vec = [False] * MemoRuleSet_df.shape[0]

        set_ids = ChooseOneSet_df.Choose_One_Set_Id.unique()
        set_ids.sort()
        for set_id in set_ids:
            all_options_for_set = ChooseOneSet_df[ChooseOneSet_df.Choose_One_Set_Id == set_id,:]
            option_ids = all_options_for_set.Option_Id
            option_ids.sort()
            for option_id in option_ids:
                one_relevant_row_df = ChooseOneSet_df[ (ChooseOneSet_df.Choose_One_Set_Id == set_id) & (ChooseOneSet_df.Option_Id == option_id) ,:]

                for i in range(0,BudgetSet_df.shape[0]):
                    budget_row = BudgetSet_df.loc[i,:]

                    for memo_regex in one_relevant_row_df.Memo_Regex_List.split(';'):
                        pass
                        #todo left off here


        # choose_one_sets__list = []
        # for i in set_ids:
        #     choose_one_sets__list.append([])

        # #Scenario_Name	Choose_One_Set_Id	Option_Name	Option_Id	Memo_Regex_List (semicolon delimited)
        # for chooseoneset_index, chooseoneset_row in ChooseOneSet_df.iterrows():
        #     pass
        #     #choose_one_sets__dict[chooseoneset_row.Choose_One_Set_Id].append(chooseoneset_row.Memo_Regex_List)


    def outputHTMLreport(self,E):
        pass
        raise NotImplementedError


    def generateCompareTwoForecastsHTMLReport(self,E1, E2, output_dir='./'):

        assert E1.start_date == E2.start_date
        assert E1.end_date == E2.end_date

        start_date = E1.start_date
        end_date = E1.end_date

        report_id = E1.unique_id + '_vs_' + E2.unique_id

        networth_line_plot_path = output_dir + report_id + '_networth_line_plot.png'
        netgain_line_plot_path = output_dir + report_id + '_netgain_line_plot.png'
        accounttype_line_plot_path = output_dir + report_id + '_accounttype_line_plot_plot.png'
        interest_line_plot_path = output_dir + report_id + '_interest_line_plot_plot.png'
        milestone_line_plot_path = output_dir + report_id + '_milestone_line_plot.png'
        all_line_plot_path = output_dir + report_id + '_all_line_plot.png'

        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Expense Forecast Comparison """+ E1.unique_id + """ vs. """ + E2.unique_id +"""</title>
        <style>
        /* Style the tab */
        .tab {
          overflow: hidden;
          border: 1px solid #ccc;
          background-color: #f1f1f1;
        }

        /* Style the buttons that are used to open the tab content */
        .tab button {
          background-color: inherit;
          float: left;
          border: none;
          outline: none;
          cursor: pointer;
          padding: 14px 16px;
          transition: 0.3s;
        }

        /* Change background color of buttons on hover */
        .tab button:hover {
          background-color: #ddd;
        }

        /* Create an active/current tablink class */
        .tab button.active {
          background-color: #ccc;
        }

        /* Style the tab content */
        .tabcontent {
          display: none;
          padding: 6px 12px;
          border: 1px solid #ccc;
          border-top: none;
        }
        </style>


        </head>
        <body>
        <h1>Expense Forecast Comparison: "Scenario 1" vs. "Scenario 2"</h1>
        <p>"""+start_date+""" to """+end_date+"""</p>

        <!-- Tab links -->
        <div class="tab">
          <button class="tablinks" onclick="openTab(event, 'Summary')">Summary</button>
          <button class="tablinks" onclick="openTab(event, 'NetWorth')">Net Worth</button>
          <button class="tablinks" onclick="openTab(event, 'NetGainLoss')">Net Gain/Loss</button>
          <button class="tablinks" onclick="openTab(event, 'AccountType')">Account Type</button>
          <button class="tablinks" onclick="openTab(event, 'Interest')">Interest</button>
          <button class="tablinks" onclick="openTab(event, 'Interest')">Milestone</button>
          <button class="tablinks" onclick="openTab(event, 'All')">All</button>
        </div>

        <!-- Tab content -->
        <div id="Summary" class="tabcontent">
          <h3>Summary</h3>
          <p>Summary text.</p>
        </div>

        <div id="NetWorth" class="tabcontent">
          <h3>NetWorth</h3>
          <p>NetWorth text.</p>
          <img src=\""""+networth_line_plot_path+"""\">
        </div>

        <div id="NetGainLoss" class="tabcontent">
          <h3>NetGainLoss</h3>
          <p>NetGainLoss text.</p>
          <img src=\""""+netgain_line_plot_path+"""\">
        </div>

        <div id="AccountType" class="tabcontent">
          <h3>AccountType</h3>
          <p>AccountType text.</p>
          <img src=\""""+accounttype_line_plot_path+"""\">
        </div>

        <div id="Interest" class="tabcontent">
          <h3>Interest</h3>
          <p>Interest text.</p>
          <img src=\""""+interest_line_plot_path+"""\">
        </div>
        
        <div id="Milestone" class="tabcontent">
          <h3>Milestone</h3>
          <p>Milestone text.</p>
          <img src=\""""+milestone_line_plot_path+"""\">
        </div>

        <div id="All" class="tabcontent">
          <h3>All</h3>
          <p>All text.</p>
          <img src=\""""+all_line_plot_path+"""\">
        </div>

        <br>

        <script>
        function openTab(evt, tabName) {
          // Declare all variables
          var i, tabcontent, tablinks;

          // Get all elements with class="tabcontent" and hide them
          tabcontent = document.getElementsByClassName("tabcontent");
          for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
          }

          // Get all elements with class="tablinks" and remove the class "active"
          tablinks = document.getElementsByClassName("tablinks");
          for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
          }

          // Show the current tab, and add an "active" class to the button that opened the tab
          document.getElementById(tabName).style.display = "block";
          evt.currentTarget.className += " active";
        }
        </script>

        </body>
        </html>

        """

        with open('out.html','w') as f:
            f.write(html_body)


    def generateHTMLReport(self,E,output_dir='./'):

        start_date = E.start_date.strftime('%Y-%m-%d')
        end_date = E.end_date.strftime('%Y-%m-%d')

        report_id = E.unique_id

        start_ts__datetime = datetime.datetime.strptime(E.start_ts,'%Y_%m_%d__%H_%M_%S')
        end_ts__datetime = datetime.datetime.strptime(E.end_ts, '%Y_%m_%d__%H_%M_%S')
        simulation_time_elapsed = end_ts__datetime - start_ts__datetime

        #todo add a comment about whether the simulation was able to make it to the end or not.
        summary_text = """
        This forecast started at """+str(start_ts__datetime)+""", took """ + str(simulation_time_elapsed) + """ to complete, and finished at """ + str(end_ts__datetime) + """.
        """

        account_text = """
        The initial conditions and account boundaries are defined as:"""+E.initial_account_set.getAccounts().to_html()+"""
        """

        budget_set_text = """
        These transactions are considered for analysis:"""+E.initial_budget_set.getBudgetItems().to_html()+"""
        """

        memo_rule_text = """
        These decision rules are used:"""+E.initial_memo_rule_set.getMemoRules().to_html()+"""
        """

        initial_networth=E.forecast_df.head(1)['NetWorth'].iat[0]
        final_networth=E.forecast_df.tail(1)['NetWorth'].iat[0]
        networth_delta=final_networth-initial_networth
        num_days = E.forecast_df.shape[0]
        avg_networth_change=round(networth_delta/float(E.forecast_df.shape[0]),2)

        if networth_delta >= 0:
            rose_or_fell="rose"
        else:
            rose_or_fell="fell"

        networth_text = """
        Net Worth began at """+str(f"${float(initial_networth):,}")+""" and """+rose_or_fell+""" to """+str(f"${float(final_networth):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_networth_change):,}"+""" per day.
        """

        initial_loan_total = round(E.forecast_df.head(1).LoanTotal.iat[0],2)
        final_loan_total = round(E.forecast_df.tail(1).LoanTotal.iat[0],2)
        loan_delta = round(final_loan_total - initial_loan_total,2)
        initial_cc_debt_total = round(E.forecast_df.head(1).CCDebtTotal.iat[0],2)
        final_cc_debt_total = round(E.forecast_df.tail(1).CCDebtTotal.iat[0],2)
        cc_debt_delta = round(final_cc_debt_total - initial_cc_debt_total,2)
        initial_liquid_total = round(E.forecast_df.head(1).LiquidTotal.iat[0],2)
        final_liquid_total = round(E.forecast_df.tail(1).LiquidTotal.iat[0],2)
        liquid_delta = round(final_liquid_total - initial_liquid_total,2)

        avg_loan_delta = round(loan_delta / num_days,2)
        avg_cc_debt_delta = round(cc_debt_delta / num_days,2)
        avg_liquid_delta = round(liquid_delta / num_days,2)

        if avg_loan_delta >= 0:
            loan_rose_or_fell="rose"
        else:
            loan_rose_or_fell = "fell"

        if avg_cc_debt_delta >= 0:
            cc_debt_rose_or_fell="rose"
        else:
            cc_debt_rose_or_fell = "fell"

        if avg_liquid_delta >= 0:
            liquid_rose_or_fell="rose"
        else:
            liquid_rose_or_fell = "fell"

        account_type_text = """
        Loan debt began at """+str(f"${float(initial_loan_total):,}")+""" and """+loan_rose_or_fell+""" to """+str(f"${float(final_loan_total):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_loan_delta):,}"+""" per day.
        <br><br>
        Credit card debt began at """+str(f"${float(initial_cc_debt_total):,}")+""" and """+cc_debt_rose_or_fell+""" to """+str(f"${float(final_cc_debt_total):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_cc_debt_delta):,}"+""" per day.
        <br><br>
        Liquid cash began at """+str(f"${float(initial_liquid_total):,}")+""" and """+liquid_rose_or_fell+""" to """+str(f"${float(final_liquid_total):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_liquid_delta):,}"+""" per day.
        """

        networth_line_plot_path = output_dir + report_id + '_networth_line_plot.png'
        netgain_line_plot_path = output_dir + report_id + '_netgain_line_plot.png' #todo
        accounttype_line_plot_path = output_dir + report_id + '_accounttype_line_plot_plot.png'
        interest_line_plot_path = output_dir + report_id + '_interest_line_plot_plot.png' #todo
        milestone_line_plot_path = output_dir + report_id + '_milestone_line_plot.png' #todo
        all_line_plot_path = output_dir + report_id + '_all_line_plot.png'

        E.plotAll(all_line_plot_path)
        E.plotNetWorth(networth_line_plot_path)
        E.plotAccountTypeTotals(accounttype_line_plot_path)

        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Expense Forecast Report #""" + str(report_id) + """</title>
        <style>
        /* Style the tab */
        .tab {
          overflow: hidden;
          border: 1px solid #ccc;
          background-color: #f1f1f1;
        }

        /* Style the buttons that are used to open the tab content */
        .tab button {
          background-color: inherit;
          float: left;
          border: none;
          outline: none;
          cursor: pointer;
          padding: 14px 16px;
          transition: 0.3s;
        }

        /* Change background color of buttons on hover */
        .tab button:hover {
          background-color: #ddd;
        }

        /* Create an active/current tablink class */
        .tab button.active {
          background-color: #ccc;
        }

        /* Style the tab content */
        .tabcontent {
          display: none;
          padding: 6px 12px;
          border: 1px solid #ccc;
          border-top: none;
        }
        </style>


        </head>
        <body>
        <h1>Expense Forecast Report #""" + str(report_id) + """</h1>
        <p>"""+start_date+""" to """+end_date+"""</p>

        <!-- Tab links -->
        <div class="tab">
          <button class="tablinks active" onclick="openTab(event, 'Summary')">Summary</button>
          <button class="tablinks" onclick="openTab(event, 'NetWorth')">Net Worth</button>
          <button class="tablinks" onclick="openTab(event, 'NetGainLoss')">Net Gain/Loss</button>
          <button class="tablinks" onclick="openTab(event, 'AccountType')">Account Type</button>
          <button class="tablinks" onclick="openTab(event, 'Interest')">Interest</button>
          <button class="tablinks" onclick="openTab(event, 'Milestone')">Milestone</button>
          <button class="tablinks" onclick="openTab(event, 'All')">All</button>
        </div>

        <!-- Tab content -->
        <div id="Summary" class="tabcontent">
          <h3>Summary</h3>
          <p>"""+summary_text+"""</p>
          <h3>Accounts</h3>
          <p>"""+account_text+"""</p>
          <h3>Budget Items</h3>
          <p>"""+budget_set_text+"""</p>
          <h3>Memo Rules</h3>
          <p>"""+memo_rule_text+"""</p>
        </div>

        <div id="NetWorth" class="tabcontent">
          <h3>NetWorth</h3>
          <p>"""+networth_text+"""</p>
          <img src=\""""+networth_line_plot_path+"""\">
        </div>

        <div id="NetGainLoss" class="tabcontent">
          <h3>NetGainLoss</h3>
          <p>NetGainLoss text.</p>
          <img src=\""""+netgain_line_plot_path+"""\">
        </div>

        <div id="AccountType" class="tabcontent">
          <h3>AccountType</h3>
          <p>"""+account_type_text+"""</p>
          <img src=\""""+accounttype_line_plot_path+"""\">
        </div>

        <div id="Interest" class="tabcontent">
          <h3>Interest</h3>
          <p>Interest text.</p>
          <img src=\""""+interest_line_plot_path+"""\">
        </div>
        
        <div id="Milestone" class="tabcontent">
          <h3>Milestone</h3>
          <p>Milestone text.</p>
          <img src=\""""+milestone_line_plot_path+"""\">
        </div>

        <div id="All" class="tabcontent">
          <h3>All</h3>
          <p>All text.</p>
          <img src=\""""+all_line_plot_path+"""\">
        </div>

        <br>

        <script>
        function openTab(evt, tabName) {
          // Declare all variables
          var i, tabcontent, tablinks;

          // Get all elements with class="tabcontent" and hide them
          tabcontent = document.getElementsByClassName("tabcontent");
          for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
          }

          // Get all elements with class="tablinks" and remove the class "active"
          tablinks = document.getElementsByClassName("tablinks");
          for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
          }

          // Show the current tab, and add an "active" class to the button that opened the tab
          document.getElementById(tabName).style.display = "block";
          evt.currentTarget.className += " active";
        }
        
        //having this here leaves the Summary tab open when the page first loads
        document.getElementById("Summary").style.display = "block";
        </script>

        </body>
        </html>

        """

        with open('out.html','w') as f:
            f.write(html_body)

    def getRuntimeEstimate(self,AccountSet,BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD):
        log_in_color('green','debug','getRuntimeEstimate(start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')')
        log_in_color('green', 'debug', 'Length of forecast:')
        log_in_color('green', 'debug', 'Non-deferrable, partial-payment not allowed:')
        log_in_color('green', 'debug', 'Partial-payment allowed:')
        log_in_color('green', 'debug', 'Deferrable:')
        #number of days * 7.5 seconds
        # for each non-deferrable, partial-payment-not-allowed proposed item, add (end_date - date) * 7.5 seconds
        # for each partial payment allowed item, add [ (end_date - date) * 7.5 seconds, (end_date - date) * 7.5 seconds * 2 ] to get an range time estimate
        # for each deferrable payment, add [ (end_date - date) * 7.5 seconds, ( 1 + FLOOR( (end_date - date) / 14) )^2 / 2 * 7.5 seconds ]

        raise NotImplementedError


    def calculateMultipleChooseOne(self,AccountSet,Core_BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD, list_of_lists_of_budget_sets):

        #the number of returned forecasts will be equal to the product of the lengths of the lists in list_of_lists_of_budget_sets
        length_of_lists = [ len(x) for x in list_of_lists_of_budget_sets]
        number_of_returned_forecasts = 1
        for l in length_of_lists:
            number_of_returned_forecasts = number_of_returned_forecasts * l

        #at this point, our return variable is the correct size, and has an empty list for each budget set
        master_list = [Core_BudgetSet.budget_items] #this is a list of lists of budget items
        for list_of_budget_sets in list_of_lists_of_budget_sets:
            current_list = []

            for budget_set in list_of_budget_sets:
                for master_budget_item_list in master_list:
                    current_list.append(budget_set.budget_items + master_budget_item_list)

            master_list = current_list

        program_start = datetime.datetime.now()
        scenario_index = 0
        for budget_set in master_list:
            loop_start = datetime.datetime.now()
            B = BudgetSet.BudgetSet(budget_set)
            # print('B:')
            # print(B.getBudgetItems().to_string())
            print('Starting simulation scenario '+str(scenario_index))
            try:
                E = ExpenseForecast.ExpenseForecast(account_set=copy.deepcopy(AccountSet),
                                                        budget_set=B,
                                                        memo_rule_set=MemoRuleSet,
                                                        start_date_YYYYMMDD=start_date_YYYYMMDD,
                                                        end_date_YYYYMMDD=end_date_YYYYMMDD)
            except:
                print('Simulation scenario '+str(scenario_index)+' failed')

            loop_finish = datetime.datetime.now()

            loop_delta = loop_finish - loop_start
            time_since_started = loop_finish - program_start

            average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
            loops_remaining = number_of_returned_forecasts - (scenario_index + 1)
            ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop*loops_remaining)
            progress_string = 'Finished in '+str(loop_delta.seconds)+' seconds. ETC: '+str(ETC.strftime('%Y-%m-%d %H:%M:%S'))

            print(progress_string)

            scenario_index += 1

    #
    # def run_forecast_from_excel_inputs(self,path_to_excel):
    #
    #     if not self.input_excel_values_are_valid(str(path_to_excel)):
    #         raise ValueError("There was a problem with the excel sheet at this path: "+str(path_to_excel))
    #
    #     raise NotImplementedError
    #
    # def input_excel_values_are_valid(self,path_to_excel):
    #     raise NotImplementedError