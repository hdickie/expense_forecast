import pandas as pd
import re
import jsonpickle


class MemoRule:

    def __init__(
        self,
        memo_regex,
        account_from,
        account_to,
        transaction_priority,
        print_debug_messages=True,
        raise_exceptions=True,
    ):
        """
        Creates a <MemoRule> object. Input validation is performed.

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

        # todo MemoRule.MemoRule():: ValueError if from = to? and also if both are empty string ##https://github.com/hdickie/expense_forecast/issues/45

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
        if self.account_from == "ALL_LOANS":
            exception_value_error_message_string += "ALL_LOANS cannot be Account_From\n"
            exception_value_error_ind = True

        self.account_to = str(self.account_to)
        # try:
        #    self.account_to = str(self.account_to)
        # except:
        #    exception_type_error_message_string += 'failed cast MemoRule.account_to to str\n'
        #    exception_type_error_ind = True

        try:
            self.transaction_priority = int(self.transaction_priority)
        except Exception:
            exception_type_error_message_string += (
                "failed cast MemoRule.transaction_priority to int\n"
            )
            exception_type_error_message_string += (
                "Value was:" + str(self.transaction_priority) + "\n"
            )
            exception_type_error_ind = True

        try:
            x = re.search(self.memo_regex, "")
        except Exception:
            exception_value_error_message_string += "An exception was thrown when MemoRule.memo_regex was interpreted as a regex.\n"
            exception_value_error_message_string += (
                "Value was:" + str(self.memo_regex) + "\n"
            )
            exception_value_error_ind = True

        try:
            assert self.transaction_priority >= 1
        except Exception:
            exception_value_error_message_string += (
                "MemoRule.transaction_priority must be greater than or equal to 1.\n"
            )
            exception_value_error_message_string += (
                "Value was:" + str(self.transaction_priority) + "\n"
            )
            exception_value_error_ind = True

        if print_debug_messages:
            if exception_type_error_ind:
                print(exception_type_error_message_string)

            if exception_value_error_ind:
                print(exception_value_error_message_string)

        if raise_exceptions:
            if exception_type_error_ind:
                raise TypeError

            if exception_value_error_ind:
                raise ValueError

    def __str__(self):
        single_memo_rule_df = pd.DataFrame(
            {
                "Memo_Regex": [self.memo_regex],
                "Account_From": [self.account_from],
                "Account_To": [self.account_to],
                "Transaction_Priority": [self.transaction_priority],
            }
        )

        return single_memo_rule_df.to_string()

    def to_json(self):
        """
        Get a JSON <string> representing the <MemoRule> object.
        """
        return jsonpickle.encode(self, indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()
