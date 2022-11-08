import pandas as pd, datetime
class BudgetItem:

    def __init__(self,
                 start_date_YYYYMMDD,
                 priority,
                 cadence,
                 amount,
                 deferrable,
                 memo,
                 print_debug_messages=True,
                 throw_exceptions=True):
        """
        Creates a BudgetItem object. Input validation is performed.

        The BudgetItem constructor does not check types, but numerical parameters will raise a ValueError if they cannot be
        cast to float.

        :param str start_date_YYYYMMDD: A string that indicates the start date with format %Y%m%d.
        :param int priority: An integer >= 1 that indicates priority. See below for priority level meanings.
        :param str cadence: One of: 'once', 'daily', 'weekly', 'biweekly', 'monthly', 'quarterly', 'yearly'
        :param float amount: A dollar value for the amount of the transaction. See below for how to handle negative values.
        :param bool deferrable: True if the transaction can be delayed. False if it is a time-sensitive opportunity.
        :param str memo: A label for the transaction.

        Comment on Priority levels:
        This code executes transactions starting at priority 1 and moving up. Level 1 indicates non-negotiable, and the code will
        break if non-negotiable budget items cause account boundaries to be violated. Higher level priorities have no
        hard-coded meaning, but here is how I plan to use them at this time:

        1. Non-negotiable. (Income, Rent, Minimum cc payments, Minimum loan payments, cost of living line-items)
        2. Additional payments on credit card debt
        3. Non-deferrable budget items that I am willing to pay interest on
        4. Deferrable budget items that I am willing to pay interest on
        5. Non-deferrable budget items that I am not willing to pay interest on
        6. Deferrable budget items that I am not willing to pay interest on
        7. additional loan payments
        8. savings
        9. investments

        Comment on Amount:
        This implementation will subtract abs(Amount) from Account_From, and add abs(amount) to Account_To. Therefore,
        negative values for Amount are reflected in the memo values but don't change the directional change of account balances.

        #todo doctests
        >>> BudgetItem()
        Traceback (most recent call last):
        ...
        TypeError: BudgetItem.__init__() missing 6 required positional arguments: 'start_date_YYYYMMDD', 'priority', 'cadence', 'amount', 'deferrable', and 'memo'

        >>> print(BudgetItem(start_date_YYYYMMDD='20000101',
        ... priority=1,
        ... cadence='once',
        ... amount=10,
        ... deferrable=False,
        ... memo='test').toJSON())
        {
        "Start_Date":"2000-01-01 00:00:00",
        "Priority":"1",
        "Cadence":"once",
        "Amount":"10",
        "Deferrable":"False",
        "Memo":"test"
        }

        """

        self.start_date = start_date_YYYYMMDD
        self.priority = priority
        self.cadence = cadence
        self.amount = amount
        self.deferrable = deferrable
        self.memo = memo

        exception_type_error_ind = False
        exception_type_error_message_string = ""

        exception_value_error_ind = False
        exception_value_error_message_string = ""


        try:
            self.start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
        except:
            exception_type_error_message_string += 'failed cast BudgetItem.start_date to datetime\n'
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
        # try:
        #    self.cadence = str(self.cadence)
        # except:
        #    exception_type_error_message_string += 'failed cast BudgetItem.cadence to str\n'
        #    exception_type_error_ind = True

        try:
           assert self.cadence.lower() in ['once','daily','weekly','biweekly','monthly','quarterly','yearly']
        except:
           exception_value_error_message_string += 'BudgetItem.cadence is not one of: once, daily, weekly, biweekly, monthly, quarterly, yearly\n'
           exception_value_error_message_string += 'Value was:'+str(self.cadence)+'\n'
           exception_value_error_ind = True

        try:
           self.amount = float(self.amount)
        except:
           exception_type_error_message_string += 'failed cast BudgetItem.amount to float\n'
           exception_type_error_ind = True

        try:
           self.deferrable = bool(self.deferrable)
        except:
           exception_type_error_message_string += 'failed cast BudgetItem.deferrable to bool\n'
           exception_type_error_ind = True

        self.memo = str(self.memo)
        # try:
        #    self.memo = str(self.memo)
        # except:
        #    exception_type_error_message_string += 'failed cast BudgetItem.memo to str\n'
        #    exception_type_error_ind = True


        if print_debug_messages:
            if exception_type_error_ind:
                print(exception_type_error_message_string)

            if exception_value_error_ind:
                print(exception_value_error_message_string)

        if throw_exceptions:
            if exception_type_error_ind:
                raise TypeError

            if exception_value_error_ind:
                raise ValueError

    def __str__(self):
        single_budget_item_df = pd.DataFrame({
            'start_date': [self.start_date],
            'priority': [self.priority],
            'cadence': [self.cadence],
            'amount': [self.amount],
            'deferrable': [self.deferrable],
            'memo': [self.memo]
        })

        return single_budget_item_df.to_string()

    def __repr__(self):
        return str(self)

    def toJSON(self):
        """
        Get a string representing the BudgetItem object.
        """
        JSON_string = "{\n"
        JSON_string += "\"Start_Date\":" + "\"" + str(self.start_date) + "\",\n"
        JSON_string += "\"Priority\":" + "\"" + str(self.priority) + "\",\n"
        JSON_string += "\"Cadence\":" + "\"" + str(self.cadence) + "\",\n"
        JSON_string += "\"Amount\":" + "\"" + str(self.amount) + "\",\n"
        JSON_string += "\"Deferrable\":" + "\"" + str(self.deferrable) + "\",\n"
        JSON_string += "\"Memo\":" + "\"" + str(self.memo) + "\"\n"
        JSON_string += "}"
        return JSON_string

    # def fromJSON(self,JSON_string):
    #     #todo implement BudgetItem.fromJSON()
    #     pass

#this is written this way so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()