import pandas as pd, datetime
class BudgetItem:

    def __init__(self,
                 start_date_YYYYMMDD,
                 end_date_YYYYMMDD,
                 priority,
                 cadence,
                 amount,
                 memo,
                 deferrable=False,
                 partial_payment_allowed=False,
                 print_debug_messages=True,
                 raise_exceptions=True):
        """
        Creates a BudgetItem object. Input validation is performed.

        The BudgetItem constructor does not check types, but numerical parameters will raise a ValueError if they cannot be
        cast to float.

        | Test Cases
        | Expected Successes
        | [x] S1 Valid values for all parameters
        |
        | Expected Fails
        | Parameters that are provided are incorrect
        | [x] F1 provide no parameters
        |
        | Incorrect Types provided for necessary parameters
        | [x] F2 Provide incorrect types for all necessary parameters
        |
        | Illegal values provided
        | [x] F3 Priority less than 1 and cadence is some random string
        | [ ] F4 All income should be priority 1. Therefore, income with a different priority should raise an exception

        :param str start_date_YYYYMMDD: A string that indicates the start date with format %Y%m%d.
        :param str start_date_YYYYMMDD: A string that indicates the end date with format %Y%m%d.
        :param int priority: An integer >= 1 that indicates priority. See below for priority level meanings.
        :param str cadence: One of: 'once', 'daily', 'weekly', 'semiweekly', 'monthly', 'quarterly', 'yearly'
        :param float amount: A dollar value for the amount of the transaction. See below for how to handle negative values.
        :param bool deferrable: True if the transaction can be delayed. False if it is a time-sensitive opportunity.
        :param str memo: A label for the transaction.

        Comment on Priority levels:
        This code executes transactions starting at priority 1 and moving up. Level 1 indicates non-negotiable, and the code will
        break if non-negotiable budget items cause account boundaries to be violated. Higher level priorities have no
        hard-coded meaning, but here is how I plan to use them at this time:

        1. Non-negotiable. (Income, Rent, Minimum cc payments, Minimum loan payments, cost of living line-items)
        2. Non-deferrable budget items that I am willing to pay interest on
        3. Deferrable budget items that I am willing to pay interest on
        4. Additional payments on credit card debt
        5. Non-deferrable budget items that I am not willing to pay interest on
        6. Deferrable budget items that I am not willing to pay interest on
        7. additional loan payments
        8. savings
        9. investments

        Comment on Amount:
        This implementation will subtract abs(Amount) from Account_From, and add abs(amount) to Account_To. Therefore,
        negative values for Amount are reflected in the memo values but don't change the directional change of account balances.

        """

        self.start_date = start_date_YYYYMMDD
        self.end_date = end_date_YYYYMMDD
        self.priority = priority
        self.cadence = cadence
        self.amount = amount
        self.memo = memo
        self.deferrable = deferrable
        self.partial_payment_allowed = partial_payment_allowed

        exception_type_error_ind = False
        exception_type_error_message_string = ""

        exception_value_error_ind = False
        exception_value_error_message_string = ""


        try:
            self.start_date = datetime.datetime.strptime(str(start_date_YYYYMMDD).replace('-',''),'%Y%m%d')
            #todo accept YYYY-MM-DD and YYYYMMDD
        except Exception as e:
            exception_type_error_message_string += str(e)
            exception_type_error_message_string += 'failed cast BudgetItem.start_date to datetime\n'
            exception_type_error_message_string += 'value was:'+str(start_date_YYYYMMDD)+'\n'
            exception_type_error_ind = True

        try:
            self.end_date = datetime.datetime.strptime(str(end_date_YYYYMMDD).replace('-',''),'%Y%m%d')
            #todo accept YYYY-MM-DD and YYYYMMDD
        except Exception as e:
            exception_type_error_message_string += str(e)
            exception_type_error_message_string += 'failed cast BudgetItem.end_date to datetime\n'
            exception_type_error_message_string += 'value was:'+str(end_date_YYYYMMDD)+'\n'
            exception_type_error_ind = True

        try:
           self.priority = int(self.priority)
        except:
           exception_type_error_message_string += 'failed cast BudgetItem.priority to int\n'
           exception_type_error_ind = True

        try:
           assert self.priority >= 1
        except:
           exception_value_error_message_string += 'BudgetItem.priority must be greater than or equal to 1\n'
           exception_value_error_ind = True

        self.cadence = str(self.cadence)

        try:
           assert self.cadence.lower() in ['once','daily','weekly','semiweekly','monthly','quarterly','yearly']
        except:
           exception_value_error_message_string += 'BudgetItem.cadence is not one of: once, daily, weekly, semiweekly, monthly, quarterly, yearly\n'
           exception_value_error_message_string += 'Value was:'+str(self.cadence)+'\n'
           exception_value_error_ind = True

        try:
           self.amount = float(self.amount)
        except:
           exception_type_error_message_string += 'failed cast BudgetItem.amount to float\n'
           exception_type_error_message_string += 'value was:'+str(self.amount)+'\n'
           exception_type_error_ind = True

        #almost everything can cast to bool which im not sure how I feel about
        # try:
        #    self.deferrable = bool(self.deferrable)
        # except:
        #    exception_type_error_message_string += 'failed cast BudgetItem.deferrable to bool\n'
        #    exception_type_error_ind = True

        self.memo = str(self.memo)
        # try:
        #    self.memo = str(self.memo)
        # except:
        #    exception_type_error_message_string += 'failed cast BudgetItem.memo to str\n'
        #    exception_type_error_ind = True

        if self.memo.lower() == 'income' and self.priority != 1:
            exception_value_error_message_string += 'If Memo = Income, then priority must = 1\n'
            exception_value_error_message_string += 'Value was:'+str(self.priority)
            exception_value_error_ind = True

        if print_debug_messages:
            if exception_type_error_ind: print(exception_type_error_message_string)

            if exception_value_error_ind: print(exception_value_error_message_string)

        if raise_exceptions:
            if exception_type_error_ind:
                raise TypeError

            if exception_value_error_ind:
                raise ValueError

    def __str__(self):
        return pd.DataFrame({
            'Start_Date': [self.start_date.strftime('%Y%m%d')],
            'End_Date': [self.end_date.strftime('%Y%m%d')],
            'Priority': [self.priority],
            'Cadence': [self.cadence],
            'Amount': [self.amount],
            'Memo': [self.memo],
            'Deferrable': [self.deferrable],
            'Partial_Payment_Allowed': [self.partial_payment_allowed]
        }).to_string()

    def to_json(self):
        """
        Get a <string> representing the <BudgetItem> object.

        """
        return pd.DataFrame({
            'Start_Date': [self.start_date.strftime('%Y%m%d')],
            'End_Date': [self.end_date.strftime('%Y%m%d')],
            'Priority': [self.priority],
            'Cadence': [self.cadence],
            'Amount': [self.amount],
            'Memo': [self.memo],
            'Deferrable': [self.deferrable],
            'Partial_Payment_Allowed': [self.partial_payment_allowed]
        }).to_json(orient="records")

    # def fromJSON(self,JSON_string):
    #     pass

#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()