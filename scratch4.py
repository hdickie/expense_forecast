import pandas as pd
import datetime
import re
import copy
from log_methods import log_in_color
from generate_date_sequence import generate_date_sequence
logger = setup_logger('ExpenseForecast', './log/ExpenseForecast.log', level=logging.INFO)

def propagateOptimizationTransactionsIntoTheFuture(self, account_set_before_p2_plus_txn, forecast_df, date_string_YYYYMMDD):
    bal_string = ' '
    for index, row in account_set_before_p2_plus_txn.getAccounts().iterrows():
        bal_string += '$' + str(row.Balance) + ' '
    # log_in_color(logger, 'magenta', 'info',
    #              'ENTER propagateOptimizationTransactionsIntoTheFuture(' + str(date_string_YYYYMMDD) + ') (before txn bals) '+str(bal_string),
    #              self.log_stack_depth)
    # log_in_color(logger, 'magenta', 'info', 'BEFORE')
    # log_in_color(logger, 'magenta', 'info', forecast_df.to_string())

    account_set_after_p2_plus_txn = self.sync_account_set_w_forecast_day(
        copy.deepcopy(account_set_before_p2_plus_txn), forecast_df, date_string_YYYYMMDD)

    A_df = account_set_after_p2_plus_txn.getAccounts()
    B_df = account_set_before_p2_plus_txn.getAccounts()

    account_deltas = A_df.Balance - B_df.Balance
    for i in range(0, len(account_deltas)):
        # account_deltas[i] = round(account_deltas[i], 2)

        try:
            if A_df.iloc[i, 4] in ('checking', 'principal balance', 'interest'):
                assert account_deltas[i] <= 0  # sanity check. only true for loan and checking
            # we actually cant enforce anything for curr and prev
        except AssertionError as e:
            log_in_color(logger, 'red', 'error', str(account_deltas))
            log_in_color(logger, 'red', 'error', str(e.args))
            raise e
    account_deltas = pd.DataFrame(account_deltas).T
    # log_in_color(logger, 'magenta', 'info', account_deltas.to_string())
    del i

    # log_in_color(logger, 'magenta', 'info', 'account_deltas:')
    # log_in_color(logger, 'magenta', 'info', account_deltas)

    future_rows_only_row_sel_vec = [
        datetime.datetime.strptime(d, '%Y%m%d') > datetime.datetime.strptime(date_string_YYYYMMDD, '%Y%m%d') for d
        in forecast_df.Date]
    future_rows_only_df = forecast_df.iloc[future_rows_only_row_sel_vec, :]
    future_rows_only_df.reset_index(drop=True, inplace=True)

    # log_in_color(logger, 'magenta', 'info', 'future_rows_only_df (top of propagateOptimizationTransactionsIntoTheFuture):')
    # log_in_color(logger, 'magenta', 'info', future_rows_only_df.to_string())

    interest_accrual_dates__list_of_lists = []
    for a_index, a_row in A_df.iterrows():
        if a_row.Interest_Cadence is None:
            interest_accrual_dates__list_of_lists.append([])
            continue
        if a_row.Interest_Cadence == 'None':
            interest_accrual_dates__list_of_lists.append([])
            continue

        num_days = (datetime.datetime.strptime(self.end_date_YYYYMMDD, '%Y%m%d') - datetime.datetime.strptime(
            a_row.Billing_Start_Dt, '%Y%m%d')).days
        account_specific_iad = generate_date_sequence(a_row.Billing_Start_Dt, num_days, a_row.Interest_Cadence)
        interest_accrual_dates__list_of_lists.append(account_specific_iad)

    billing_dates__list_of_lists = []
    for a_index, a_row in A_df.iterrows():
        if a_row.Billing_Start_Dt is None:
            billing_dates__list_of_lists.append([])
            continue
        if a_row.Billing_Start_Dt == 'None':
            billing_dates__list_of_lists.append([])
            continue

        num_days = (datetime.datetime.strptime(self.end_date_YYYYMMDD, '%Y%m%d') - datetime.datetime.strptime(
            a_row.Billing_Start_Dt, '%Y%m%d')).days
        account_specific_bd = generate_date_sequence(a_row.Billing_Start_Dt, num_days, 'monthly')
        billing_dates__list_of_lists.append(account_specific_bd)

    # Propagate constant deltas
    # this does need to happen before adjustment of satisfice payments bc interest value day-of will be used
    # and it is more consistent/makes more sense/is easier to read when accessing pbal from the same context
    for account_index, account_row in account_set_after_p2_plus_txn.getAccounts().iterrows():

        # if this method has been called on the last day of the forecast, there is no work to do
        if forecast_df[forecast_df.Date > date_string_YYYYMMDD].empty:
            break

        if account_deltas.iloc[0, account_index] == 0:
            continue

        col_sel_vec = (forecast_df.columns == account_row.Name)

        # if not an interest bearing account, we can do this
        # log_in_color(logger, 'white', 'info', 'account_row.Name: ' + str(account_row.Name))
        if account_row.Account_Type != 'interest':  # if pbal was paid as well, this subtraction of a constant would not suffice
            # log_in_color(logger, 'white', 'info', 'account_deltas:')
            # log_in_color(logger, 'white', 'info', account_deltas)
            # log_in_color(logger, 'white', 'info', '+= ' + str(account_deltas.iloc[0, account_index]))
            future_rows_only_df.iloc[:, col_sel_vec] += account_deltas.iloc[0, account_index]

    # recalculate interest and reapply min payments and update min payment memo
    # min payments must be reapplied before interest calc can be corrected, and may as well update memo at same time
    # log_in_color(logger, 'white', 'info', 'future_rows_only_df:')
    # log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())
    for f_i, f_row in future_rows_only_df.iterrows():
        f_row = pd.DataFrame(f_row).T
        f_row.reset_index(drop=True, inplace=True)

        for a_i in range(1, forecast_df.shape[1] - 1):  # left bound is 1 bc skip Date

            if account_deltas.iloc[0, a_i - 1] == 0:
                continue  # if no optimization was made, then satisfice does not need to be edited

            if f_i == future_rows_only_df.shape[0]:
                continue  # last day of forecast so we can stop

            account_row = A_df.iloc[a_i - 1, :]

            # log_in_color(logger, 'magenta', 'info', 'f_row.Date.iat[0]:'+str(f_row.Date.iat[0]))
            # log_in_color(logger, 'magenta', 'info', 'account_row.Account_Type:' + str(account_row.Account_Type))
            # log_in_color(logger, 'magenta', 'info', 'pbal_billing_dates:')
            # log_in_color(logger, 'magenta', 'info', pbal_billing_dates)
            # criterion_1 = (f_row.Date.iat[0] in pbal_billing_dates)
            # criterion_2 = (account_row.Account_Type == 'principal balance')
            # log_in_color(logger, 'magenta', 'info', 'criterion_1:' + str(criterion_1))
            # log_in_color(logger, 'magenta', 'info', 'criterion_2:' + str(criterion_2))

            if account_row.Account_Type == 'interest':
                pbal_billing_dates = billing_dates__list_of_lists[a_i - 2]
                if f_row.Date.iat[0] in pbal_billing_dates:
                    # log_in_color(logger, 'magenta', 'info', 'Billing date for loan account reached')
                    # log_in_color(logger, 'magenta', 'info', 'pbal_billing_dates:')
                    # log_in_color(logger, 'magenta', 'info', pbal_billing_dates)
                    # log_in_color(logger, 'magenta', 'info', 'f_row.Memo.iat[0]:'+str(f_row.Memo.iat[0]))
                    if 'loan min payment' in f_row.Memo.iat[0]:
                        #    log_in_color(logger, 'magenta', 'info',str(f_row.Date.iat[0]) + ' About to re-process min loan payments')
                        #    log_in_color(logger, 'magenta', 'info', 'account_deltas:')
                        #    log_in_color(logger, 'magenta', 'info',account_deltas)

                        # even if og additional went all to interest, later min payments may become split
                        # across interest and pbal if there was an additional payment in the past
                        account_base_name = f_row.columns[a_i].split(':')[0]

                        pbal_account_row = A_df.iloc[a_i - 2, :]

                        interest_denominator = -1
                        if pbal_account_row.Interest_Cadence == 'daily':
                            interest_denominator = 365.25
                        elif pbal_account_row.Interest_Cadence == 'weekly':
                            interest_denominator = 52.18
                        elif pbal_account_row.Interest_Cadence == 'semiweekly':
                            interest_denominator = 26.09
                        elif pbal_account_row.Interest_Cadence == 'monthly':
                            interest_denominator = 12
                        elif pbal_account_row.Interest_Cadence == 'yearly':
                            interest_denominator = 1

                        # # todo this is negative and has not been corrected yet
                        # pbal_before_min_payment_applied = future_rows_only_df.iloc[f_i, a_i - 1]
                        #
                        # new_marginal_interest = pbal_before_min_payment_applied * pbal_account_row.APR / interest_denominator
                        # interest_before_min_payment_applied = future_rows_only_df.iloc[
                        #                                           f_i - 1, a_i] + new_marginal_interest
                        #
                        # future_rows_only_df.iloc[f_i, a_i] = interest_before_min_payment_applied

                        # log_in_color(logger, 'white', 'info',
                        #              'future_rows_only_df (after case 4):')
                        # log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())

                        # log_in_color(logger, 'magenta', 'info', 'pbal_before_min_payment_applied:'+str(pbal_before_min_payment_applied))
                        # log_in_color(logger, 'magenta', 'info', 'interest_before_min_payment_applied:' + str(interest_before_min_payment_applied))

                        memo_line_items = f_row.Memo.iat[0].split(';')
                        memo_line_items_to_keep = []
                        memo_line_items_relevant_to_minimum_payment = []
                        for memo_line_item in memo_line_items:
                            # log_in_color(logger, 'magenta', 'info', 'memo_line_item:')
                            # log_in_color(logger, 'magenta', 'info', memo_line_item)
                            # log_in_color(logger, 'magenta', 'info', 'account_base_name:')
                            # log_in_color(logger, 'magenta', 'info', account_base_name)
                            if account_base_name in memo_line_item:
                                if 'loan min payment' in memo_line_item:
                                    memo_line_items_relevant_to_minimum_payment.append(memo_line_item)
                            else:
                                # we dont need this if we use string.replace
                                memo_line_items_to_keep.append(memo_line_item)

                        future_rows_only_df__date = [datetime.datetime.strptime(d, '%Y%m%d') for d in
                                                     future_rows_only_df.Date]
                        row_sel_vec = [d >= datetime.datetime.strptime(f_row.Date.iat[0], '%Y%m%d') for d in
                                       future_rows_only_df__date]
                        if len(memo_line_items_relevant_to_minimum_payment) == 0:
                            continue  # I think that this never happens
                        elif len(memo_line_items_relevant_to_minimum_payment) == 1:

                            # todo this is negative and has not been corrected yet
                            pbal_before_min_payment_applied = future_rows_only_df.iloc[f_i, a_i - 1]

                            new_marginal_interest = pbal_before_min_payment_applied * pbal_account_row.APR / interest_denominator
                            interest_before_min_payment_applied = future_rows_only_df.iloc[
                                                                      f_i - 1, a_i] + new_marginal_interest

                            future_rows_only_df.iloc[f_i, a_i] = interest_before_min_payment_applied

                            # e.g. loan min payment (Loan C: Interest -$0.28); loan min payment (Loan C: Principal Balance -$49.72);

                            account_name_match = re.search('\((.*)-\$(.*)\)',
                                                           memo_line_items_relevant_to_minimum_payment[0])
                            account_name = account_name_match.group(1)

                            og_payment_amount_match = re.search('\(.*-\$(.*)\)',
                                                                memo_line_items_relevant_to_minimum_payment[0])
                            og_amount = float(og_payment_amount_match.group(1))

                            # log_in_color(logger, 'magenta', 'info', 'account_name:' + str(account_name))
                            # log_in_color(logger, 'magenta', 'info', 'og_amount:' + str(og_amount))

                            # log_in_color(logger, 'magenta', 'info', 'before re-apply min payments:')
                            # log_in_color(logger, 'magenta', 'info', 'future_rows_only_df:')
                            # log_in_color(logger, 'magenta', 'info', future_rows_only_df.to_string())

                            # log_in_color(logger, 'white', 'info', 'BEFORE (og pymnt was single account):')
                            # log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())

                            if ': Interest' in account_name:
                                if og_amount > interest_before_min_payment_applied:
                                    # future_rows_only_df.iloc[:, col_sel_vec]
                                    amt_to_pay_toward_interest = interest_before_min_payment_applied

                                    # If min payments affected pbal before this adjustment, then that needs to be accounted for
                                    # This seems to work, but even when I wrote it I was not able to put into words why it was necessary...
                                    # I think it likely is not the only way, and this logic seems like 2 consecutive days
                                    # of additional loan payments could fuck this up. #todo revisit this
                                    already_paid_toward_pbal = future_rows_only_df.iloc[f_i - 1, a_i - 1] - \
                                                               future_rows_only_df.iloc[f_i, a_i - 1]
                                    # log_in_color(logger, 'magenta', 'info','already_paid_toward_pbal:' + str(already_paid_toward_pbal))
                                    amt_to_pay_toward_pbal = (
                                                                         og_amount - already_paid_toward_pbal) - amt_to_pay_toward_interest

                                    # I added this for the case where already paid off
                                    # I used min instead of just 0 bc in my head its more robust but tbh I havent thought about the other
                                    # cases
                                    amt_to_pay_toward_pbal = min(future_rows_only_df.iloc[f_i, a_i - 1],
                                                                 amt_to_pay_toward_pbal)

                                    # log_in_color(logger, 'magenta', 'info', 'amt_to_pay_toward_pbal:' + str(amt_to_pay_toward_pbal))
                                    # log_in_color(logger, 'magenta', 'info', 'amt_to_pay_toward_interest:'+str(amt_to_pay_toward_interest))

                                    # log_in_color(logger, 'magenta', 'info','Principal before modification:')
                                    # log_in_color(logger, 'magenta', 'info', future_rows_only_df.iloc[row_sel_vec , a_i - 1 ].head(1).iat[0])

                                    future_rows_only_df.iloc[row_sel_vec, a_i - 1] -= amt_to_pay_toward_pbal

                                    # log_in_color(logger, 'magenta', 'info', 'Principal after modification:')
                                    # log_in_color(logger, 'magenta', 'info',future_rows_only_df.iloc[row_sel_vec, a_i - 1].head(1).iat[0])

                                    # log_in_color(logger, 'magenta', 'info', 'Interest before modification:')
                                    # log_in_color(logger, 'magenta', 'info', future_rows_only_df.iloc[row_sel_vec, a_i].head(1).iat[0])

                                    future_rows_only_df.iloc[row_sel_vec, a_i] -= amt_to_pay_toward_interest

                                    # log_in_color(logger, 'magenta', 'info', 'Interest after modification:')
                                    # log_in_color(logger, 'magenta', 'info', future_rows_only_df.iloc[row_sel_vec, a_i].head(1).iat[0])

                                    # loan min payment (Loan C: Interest -$0.28); loan min payment (Loan C: Principal Balance -$49.72);
                                    memo_pbal_amount = og_amount - amt_to_pay_toward_interest

                                    # if pbal balance was 0 yesterday, then memo pbal should be 0
                                    if future_rows_only_df.iloc[f_i, a_i - 1] == 0:
                                        memo_pbal_amount = 0

                                    replacement_memo = ''
                                    if memo_pbal_amount > 0 and amt_to_pay_toward_interest > 0:
                                        replacement_memo = ' loan min payment (' + account_name + ': Principal Balance -$' + str(
                                            round(memo_pbal_amount,
                                                  2)) + '); loan min payment (' + account_name + ': Interest -$' + str(
                                            round(amt_to_pay_toward_interest, 2)) + ')'
                                    elif memo_pbal_amount > 0 and amt_to_pay_toward_interest == 0:
                                        replacement_memo = ' loan min payment (' + account_name + ': Principal Balance -$' + str(
                                            round(memo_pbal_amount, 2)) + ')'
                                    elif memo_pbal_amount == 0 and amt_to_pay_toward_interest > 0:
                                        replacement_memo = ' loan min payment (' + account_name + ': Interest -$' + str(
                                            round(amt_to_pay_toward_interest, 2)) + ')'
                                    elif memo_pbal_amount == 0 and amt_to_pay_toward_interest == 0:
                                        replacement_memo = ''

                                    future_rows_only_df.loc[f_i, 'Memo'] = future_rows_only_df.loc[f_i, 'Memo'].replace(
                                        memo_line_items_relevant_to_minimum_payment[0], replacement_memo)
                                    future_rows_only_df.loc[f_i, 'Memo'] = future_rows_only_df.loc[f_i, 'Memo'].replace(
                                        ';;', ';')  # not sure this is right
                                else:
                                    # we can reapply the min payment to the same account, memo does not change
                                    future_rows_only_df.iloc[row_sel_vec, a_i] -= og_amount
                            elif ': Principal Balance' in account_name:
                                if og_amount > pbal_before_min_payment_applied:  # I think that this case will never happen in practice
                                    amt_to_pay_toward_pbal = pbal_before_min_payment_applied
                                    amt_to_pay_toward_interest = og_amount - amt_to_pay_toward_pbal

                                    # log_in_color(logger, 'magenta', 'info',
                                    #              'amt_to_pay_toward_interest:' + str(amt_to_pay_toward_interest))
                                    # log_in_color(logger, 'magenta', 'info',
                                    #              'amt_to_pay_toward_pbal:' + str(amt_to_pay_toward_pbal))

                                    future_rows_only_df.iloc[row_sel_vec, a_i - 1] -= amt_to_pay_toward_pbal
                                    future_rows_only_df.iloc[row_sel_vec, a_i] -= amt_to_pay_toward_interest
                                else:
                                    # we can reapply the min payment to the same account
                                    future_rows_only_df.iloc[row_sel_vec, a_i - 1] -= og_amount

                            # log_in_color(logger, 'white', 'info', 'AFTER (og pymnt was single account):')
                            # log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())

                            # log_in_color(logger, 'magenta', 'info', 'future_rows_only_df:')
                            # log_in_color(logger, 'magenta', 'info', future_rows_only_df.to_string())

                        else:
                            assert len(memo_line_items_relevant_to_minimum_payment) == 2

                            log_in_color(logger, 'white', 'info', 'future_rows_only_df BEFORE:')
                            log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())

                            og_interest_payment_memo_line_item = memo_line_items_relevant_to_minimum_payment[0]
                            og_pbal_payment_memo_line_item = memo_line_items_relevant_to_minimum_payment[1]
                            og_interest_payment_amount_match = re.search('\(.*-\$(.*)\)',og_interest_payment_memo_line_item)
                            og_pbal_payment_amount_match = re.search('\(.*-\$(.*)\)', og_pbal_payment_memo_line_item)
                            og_interest_amount = float(og_interest_payment_amount_match.group(1))
                            og_pbal_amount = float(og_pbal_payment_amount_match.group(1))

                            amt_to_pay_toward_interest = future_rows_only_df.iloc[f_i - 1, a_i]
                            amt_to_pay_toward_pbal = og_interest_amount - amt_to_pay_toward_interest

                            memo_pbal_amount = og_pbal_amount + amt_to_pay_toward_pbal

                            if future_rows_only_df.iloc[f_i, a_i - 1] <= 0:
                                # log_in_color(logger, 'magenta', 'info','overpayment by min payment detected')
                                future_rows_only_df.iloc[row_sel_vec, a_i - 1] = 0
                                memo_pbal_amount = 0
                            else:
                                future_rows_only_df.iloc[row_sel_vec, a_i - 1] -= amt_to_pay_toward_pbal


                            pbal_before_min_payment_applied = future_rows_only_df.iloc[f_i, a_i - 1]

                            new_marginal_interest = pbal_before_min_payment_applied * pbal_account_row.APR / interest_denominator
                            interest_before_min_payment_applied = future_rows_only_df.iloc[
                                                                      f_i - 1, a_i] + new_marginal_interest

                            future_rows_only_df.iloc[f_i, a_i] = interest_before_min_payment_applied

                            acount_name_match = re.search('\((.*)-\$(.*)\)',
                                                          memo_line_items_relevant_to_minimum_payment[0])
                            account_name = acount_name_match.group(1)
                            account_base_name = account_name.split(':')[0]



                            # already_paid_toward_pbal = future_rows_only_df.iloc[f_i - 1, a_i - 1] - future_rows_only_df.iloc[f_i, a_i - 1]
                            # log_in_color(logger, 'magenta', 'info','already_paid_toward_pbal:' + str(already_paid_toward_pbal))
                            # log_in_color(logger, 'magenta', 'info','og_pbal_amount:' + str(og_pbal_amount))
                            # log_in_color(logger, 'magenta', 'info','already_paid_toward_pbal:' + str(already_paid_toward_pbal))
                            # log_in_color(logger, 'magenta', 'info','amt_to_pay_toward_interest:' + str(amt_to_pay_toward_interest))





                            # if a past additional payment made this min payment not necessary


                            # log_in_color(logger, 'magenta', 'info','amt_to_pay_toward_pbal:' + str(amt_to_pay_toward_pbal))
                            # log_in_color(logger, 'magenta', 'info','(amt_to_pay_toward_interest - og_interest_amount):' + str(amt_to_pay_toward_interest - og_interest_amount))

                            # log_in_color(logger, 'magenta', 'info', 'future_rows_only_df before edit:')
                            # log_in_color(logger, 'magenta', 'info', future_rows_only_df.to_string() )

                            # log_in_color(logger, 'white', 'info', 'OG PBAL AMT:')
                            # log_in_color(logger, 'white', 'info', str(og_pbal_amount))
                            # log_in_color(logger, 'white', 'info', 'OG INTEREST AMT:')
                            # log_in_color(logger, 'white', 'info', str(og_interest_amount))
                            # log_in_color(logger, 'white', 'info', 'REPLACEMENT PBAL AMT:')
                            # log_in_color(logger, 'white', 'info', str(memo_pbal_amount))
                            # log_in_color(logger, 'white', 'info', 'REPLACEMENT INTEREST AMT:')
                            # log_in_color(logger, 'white', 'info', str(amt_to_pay_toward_interest))
                            # log_in_color(logger, 'white', 'info', 'BEFORE (og pmt was 2 accts):')
                            # log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())



                            # rounding errors
                            if abs(future_rows_only_df.iloc[f_i, a_i - 1]) < 0.01:
                                future_rows_only_df.iloc[row_sel_vec, a_i - 1] = 0

                            future_rows_only_df.iloc[row_sel_vec, a_i] -= amt_to_pay_toward_interest
                            # log_in_color(logger, 'magenta', 'info', 'future_rows_only_df after edit:')
                            # log_in_color(logger, 'magenta', 'info', future_rows_only_df.to_string())

                            replacement_pbal_memo = ''
                            replacement_interest_memo = ''

                            if memo_pbal_amount > 0:
                                replacement_pbal_memo = ' loan min payment (' + account_base_name + ': Principal Balance -$' + str(
                                    round(memo_pbal_amount, 2)) + ')'

                            if amt_to_pay_toward_interest > 0:
                                replacement_interest_memo = ' loan min payment (' + account_base_name + ': Interest -$' + str(
                                    round(amt_to_pay_toward_interest, 2)) + ')'

                            future_rows_only_df.loc[f_i, 'Memo'] = future_rows_only_df.loc[f_i, 'Memo'].replace(
                                memo_line_items_relevant_to_minimum_payment[0], replacement_pbal_memo)
                            future_rows_only_df.loc[f_i, 'Memo'] = future_rows_only_df.loc[f_i, 'Memo'].replace(
                                memo_line_items_relevant_to_minimum_payment[1], replacement_interest_memo)
                            future_rows_only_df.loc[f_i, 'Memo'] = future_rows_only_df.loc[f_i, 'Memo'].replace(';;;',
                                                                                                                ';')  # not sure this is right

                            log_in_color(logger, 'white', 'info', 'future_rows_only_df AFTER:')
                            log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())

                    else:
                        pass  # loan was already paid off

            elif account_row.Account_Type == 'prev stmt bal':
                if 'cc min payment' in f_row.Memo.iat[0]:

                    account_base_name = account_row.Name.split(':')[0]
                    memo_line_items = f_row.Memo.iat[0].split(';')
                    memo_line_items_to_keep = []
                    memo_line_items_relevant_to_minimum_payment = []
                    for memo_line_item in memo_line_items:
                        if account_base_name in memo_line_item:
                            if 'cc min payment' in memo_line_item:
                                memo_line_items_relevant_to_minimum_payment.append(memo_line_item)
                        else:
                            # we dont need this if we use string.replace
                            memo_line_items_to_keep.append(memo_line_item)

                    if len(memo_line_items_relevant_to_minimum_payment) == 1:
                        # e.g. cc min payment (Credit: Prev Stmt Bal -$149.24);

                        # log_in_color(logger, 'magenta', 'info', 'f_row before recalculated cc min payment:')
                        # log_in_color(logger, 'magenta', 'info', f_row.to_string())

                        account_name_match = re.search('\((.*)-\$(.*)\)',
                                                       memo_line_items_relevant_to_minimum_payment[0])
                        account_name = account_name_match.group(1).strip()

                        og_payment_amount_match = re.search('\(.*-\$(.*)\)',
                                                            memo_line_items_relevant_to_minimum_payment[0])
                        og_amount = float(og_payment_amount_match.group(1))

                        col_sel_vec = (f_row.columns == account_name)

                        future_rows_only_df__date = [datetime.datetime.strptime(d, '%Y%m%d') for d in
                                                     future_rows_only_df.Date]
                        row_sel_vec = [d >= datetime.datetime.strptime(f_row.Date.iat[0], '%Y%m%d') for d in
                                       future_rows_only_df__date]

                        # reverse the min payment
                        future_rows_only_df.iloc[row_sel_vec, col_sel_vec] += og_amount

                        memo_to_replace = memo_line_items_relevant_to_minimum_payment[0] + ';'
                        # log_in_color(logger, 'magenta', 'info', 'memo_to_replace:')
                        # log_in_color(logger, 'magenta', 'info', memo_to_replace)
                        new_memo = future_rows_only_df.iloc[row_sel_vec, :].Memo.iat[0].replace(memo_to_replace, '')
                        f_row.Memo = new_memo

                        account_set = self.sync_account_set_w_forecast_day(
                            copy.deepcopy(account_set_before_p2_plus_txn), future_rows_only_df, f_row.Date.iat[0])
                        updated_forecast_df_row = self.executeCreditCardMinimumPayments(account_set, f_row)

                        # p2+ curr balance funds may have moved from curr to prev.
                        # this was accounted for in the above payment that just happened, but needs to be propogated
                        # while also respecting other potential p2+ payments
                        # For that reason, we propogate the delta instead of just set equal to the current result
                        if f_i == future_rows_only_df.shape[0]:
                            pass
                        else:

                            # log_in_color(logger, 'white', 'info', 'BEFORE (case 3):')
                            # log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())

                            # todo this logic does not seem rock solid to me
                            current_tmrw_value = future_rows_only_df.iloc[f_i + 1, a_i]
                            current_today_value = updated_forecast_df_row.iloc[0, a_i]
                            # row_sel_vec includes the day current being processed, which has already been applied the delta
                            future_rows_only_df.iloc[f_i, col_sel_vec] += (current_tmrw_value - current_today_value)
                            future_rows_only_df.iloc[row_sel_vec, col_sel_vec] -= (
                                        current_tmrw_value - current_today_value)

                            # log_in_color(logger, 'white', 'info', 'AFTER (case 3):')
                            # log_in_color(logger, 'white', 'info', future_rows_only_df.to_string())

                        # log_in_color(logger, 'magenta', 'info', 'updated_forecast_df_row after recalculated cc min payment:')
                        # log_in_color(logger, 'magenta', 'info', updated_forecast_df_row.to_string())

                        row_sel_vec = [d == datetime.datetime.strptime(f_row.Date.iat[0], '%Y%m%d') for d in
                                       future_rows_only_df__date]

                        # log_in_color(logger, 'magenta', 'info', 'new_memo:')
                        # log_in_color(logger, 'magenta', 'info', new_memo)

                        # log_in_color(logger, 'magenta', 'info', 'f_row after recalculated cc min payment:')
                        # log_in_color(logger, 'magenta', 'info', updated_forecast_df_row.to_string())
                        future_rows_only_df.iloc[row_sel_vec, :] = updated_forecast_df_row



            # all billing dates are interest accrual dates, but not all interest accrual dates are billing dates
            pbal_interest_accrual_dates = interest_accrual_dates__list_of_lists[a_i - 2]
            if f_row.Date.iat[0] in pbal_interest_accrual_dates and account_row.Account_Type == 'interest':

                pbal_account_row = A_df.iloc[a_i - 2, :]

                interest_denominator = -1
                if pbal_account_row.Interest_Cadence == 'daily':
                    interest_denominator = 365.25
                elif pbal_account_row.Interest_Cadence == 'weekly':
                    interest_denominator = 52.18
                elif pbal_account_row.Interest_Cadence == 'semiweekly':
                    interest_denominator = 26.09
                elif pbal_account_row.Interest_Cadence == 'monthly':
                    interest_denominator = 12
                elif pbal_account_row.Interest_Cadence == 'yearly':
                    interest_denominator = 1

                new_marginal_interest = pbal_account_row.Balance * pbal_account_row.APR / interest_denominator

                pbal_billing_dates = billing_dates__list_of_lists[a_i - 2]

                if f_i == 0:
                    future_rows_only_df.iloc[f_i, a_i] = account_row.Balance
                else:
                    if f_row.Date.iat[0] in pbal_billing_dates:
                        pass  # the value is already correct
                    else:
                        future_rows_only_df.iloc[f_i, a_i] = future_rows_only_df.iloc[f_i - 1, a_i]

                if f_row.Date.iat[0] not in pbal_billing_dates:
                    future_rows_only_df.iloc[f_i, a_i] += new_marginal_interest
                    future_rows_only_df.iloc[f_i, a_i] = future_rows_only_df.iloc[f_i, a_i]

            if account_row.Account_Type == 'curr stmt bal':
                cc_billing_dates = billing_dates__list_of_lists[a_i]  # this will access prev bal account row
                if f_row.Date.iat[0] in cc_billing_dates:
                    future_rows_only_df__date = [datetime.datetime.strptime(d, '%Y%m%d') for d in
                                                 future_rows_only_df.Date]
                    row_sel_vec = [d >= datetime.datetime.strptime(f_row.Date.iat[0], '%Y%m%d') for d in
                                   future_rows_only_df__date]

                    curr_stmt_bal_value = future_rows_only_df.iloc[f_i, a_i]

                    future_rows_only_df.iloc[row_sel_vec, a_i] -= curr_stmt_bal_value
                    future_rows_only_df.iloc[row_sel_vec, a_i + 1] += curr_stmt_bal_value

    # df.round(2) did not work so I have resorted to the below instead
    # todo this could be done better
    # for f_i, f_row in future_rows_only_df.iterrows():
    #     for a_i, a_row in A_df.iterrows():
    #         future_rows_only_df.iloc[f_i,a_i + 1] = round(future_rows_only_df.iloc[f_i,a_i + 1],2)

    # check if account boundaries are violated
    for account_index, account_row in account_set_after_p2_plus_txn.getAccounts().iterrows():

        # if this method has been called on the last day of the forecast, there is no work to do
        if future_rows_only_df.empty:
            break

        if account_deltas.iloc[0, account_index] == 0:
            continue

        col_sel_vec = (future_rows_only_df.columns == account_row.Name)

        min_future_acct_bal = min(future_rows_only_df.loc[:, col_sel_vec].values)
        max_future_acct_bal = max(future_rows_only_df.loc[:, col_sel_vec].values)

        try:
            assert account_row.Min_Balance <= min_future_acct_bal
        except AssertionError:
            error_msg = "Failure in propagateOptimizationTransactionsIntoTheFuture\n"
            error_msg += "Account boundaries were violated\n"
            error_msg += "account_row.Min_Balance <= min_future_acct_bal was not True\n"
            error_msg += str(account_row.Min_Balance) + " <= " + str(min_future_acct_bal) + '\n'
            error_msg += future_rows_only_df.to_string()
            raise ValueError(error_msg)

        try:
            assert account_row.Max_Balance >= max_future_acct_bal
        except AssertionError:
            error_msg = "Failure in propagateOptimizationTransactionsIntoTheFuture\n"
            error_msg += "Account boundaries were violated\n"
            error_msg += "account_row.Max_Balance >= max_future_acct_bal was not True\n"
            error_msg += str(account_row.Max_Balance) + " <= " + str(max_future_acct_bal) + '\n'
            error_msg += future_rows_only_df.to_string()
            raise ValueError(error_msg)

    forecast_df.iloc[future_rows_only_row_sel_vec, :] = future_rows_only_df
    # log_in_color(logger, 'magenta', 'info', 'AFTER')
    # log_in_color(logger, 'magenta', 'info', forecast_df.to_string())
    # log_in_color(logger, 'magenta', 'info',
    #              'EXIT propagateOptimizationTransactionsIntoTheFuture(' + str(date_string_YYYYMMDD) + ')',
    #              self.log_stack_depth)
    return forecast_df
