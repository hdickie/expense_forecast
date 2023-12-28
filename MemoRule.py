
import pandas as pd, re

class MemoRule:

    def __init__(self,memo_regex,account_from,account_to,transaction_priority,
                 print_debug_messages=True,
                 raise_exceptions=True):
        """
        Creates a <MemoRule> object. Input validation is performed.

        | Test Cases
        | Expected Successes
        | S1 Valid values for all parameters #todo refactor MemoRule.MemoRule() doctest S1 to use _S1 label
        |
        | Expected Fails
        | Parameters that are provided are incorrect
        | F1 provide no parameters #todo refactor MemoRule.MemoRule() doctest F1 to use _F1 label
        |
        | Incorrect Types provided for necessary parameters
        | F2 Provide incorrect types for all necessary parameters #todo refactor MemoRule.MemoRule() doctest F2 to use _F2 label
        |
        | Illegal values provided
        | F3 memo_regex explodes when interpreted as regex #todo refactor Account.Account() doctest F3 to use _F3 label
        | F4 transaction priority is less than 1 #todo refactor Account.Account() doctest F4 to use _F4 label
        | F5 transaction priority is not an integer #todo refactor Account.Account() doctest F5 to use _F5 label

        :param memo_regex: A regex to determine if this memo rule should be used for a budget item.
        :param account_from: Name of the account which funds will be drawn from
        :param account_to: Name of the account which funds will be depoisted
        :param transaction_priority: This priority index must match the priority of the transaction

        >>> MemoRule()
        Traceback (most recent call last):
        ...
        TypeError: MemoRule.__init__() missing 4 required positional arguments: 'memo_regex', 'account_from', 'account_to', and 'transaction_priority'

        >>> print(MemoRule(memo_regex='(',account_from='',account_to='',transaction_priority=1,raise_exceptions=False).toJSON())
        An exception was thrown when MemoRule.memo_regex was interpreted as a regex.
        <BLANKLINE>
        <BLANKLINE>
        {
        "Memo_Regex":"(",
        "Account_From":"",
        "Account_To":"",
        "Transaction_Priority":"1"
        }

        >>> print(MemoRule(memo_regex='',account_from='',account_to='',transaction_priority=1).toJSON())
        {
        "Memo_Regex":"",
        "Account_From":"",
        "Account_To":"",
        "Transaction_Priority":"1"
        }


        """
        self.memo_regex = memo_regex
        self.account_from = account_from
        self.account_to = account_to
        self.transaction_priority = transaction_priority

        exception_type_error_ind = False
        exception_type_error_message_string = ""

        exception_value_error_ind = False
        exception_value_error_message_string = ""

        #todo MemoRule.MemoRule():: ValueError if from = to? and also if both are empty string

        self.memo_regex = str(self.memo_regex)
        # try:
        #    self.memo_regex = str(self.memo_regex)
        # except:
        #    exception_type_error_message_string += 'failed cast MemoRule.memo_regex to str\n'
        #    exception_type_error_ind = True

        self.account_from = str(self.account_from)
        # try:
        #    self.account_from = str(self.account_from)
        # except:
        #    exception_type_error_message_string += 'failed cast MemoRule.account_from to str\n'
        #    exception_type_error_ind = True

        self.account_to = str(self.account_to)
        # try:
        #    self.account_to = str(self.account_to)
        # except:
        #    exception_type_error_message_string += 'failed cast MemoRule.account_to to str\n'
        #    exception_type_error_ind = True

        try:
           self.transaction_priority = int(self.transaction_priority)
        except:
           exception_type_error_message_string += 'failed cast MemoRule.transaction_priority to int\n'
           exception_type_error_message_string += "Value was:" + str(self.transaction_priority) + '\n'
           exception_type_error_ind = True

        try:
            x = re.search(self.memo_regex,'')
        except:
            exception_value_error_message_string += "An exception was thrown when MemoRule.memo_regex was interpreted as a regex.\n"
            exception_value_error_message_string += "Value was:"+str(self.memo_regex)+'\n'
            exception_value_error_ind = True

        try:
            assert self.transaction_priority >= 1
        except:
            exception_value_error_message_string += "MemoRule.transaction_priority must be greater than or equal to 1.\n"
            exception_value_error_message_string += "Value was:" + str(self.transaction_priority) + '\n'
            exception_value_error_ind = True

        if print_debug_messages:
            if exception_type_error_ind: print(exception_type_error_message_string)

            if exception_value_error_ind:print(exception_value_error_message_string)

        if raise_exceptions:
            if exception_type_error_ind:
                raise TypeError

            if exception_value_error_ind:
                raise ValueError


    def __str__(self):
        single_memo_rule_df = pd.DataFrame({
            'Memo_Regex': [self.memo_regex],
            'Account_From': [self.account_from],
            'Account_To': [self.account_to],
            'Transaction_Priority': [self.transaction_priority]
        })

        return single_memo_rule_df.to_string()


    def to_json(self):
        """
        Get a JSON <string> representing the <MemoRule> object.
        """

        #todo in other places I used pd.DataFrame().to_json(orient="records")

        JSON_string = "{\n"
        JSON_string += "\"Memo_Regex\":" + "\"" + str(self.memo_regex) + "\",\n"
        JSON_string += "\"Account_From\":" + "\"" + str(self.account_from) + "\",\n"
        JSON_string += "\"Account_To\":" + "\"" + str(self.account_to) + "\",\n"
        JSON_string += "\"Transaction_Priority\":" + "\"" + str(self.transaction_priority) + "\"\n"
        JSON_string += "}"
        return JSON_string

    # def fromJSON(self,JSON_string):
    #     pass

#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()