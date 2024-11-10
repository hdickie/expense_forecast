import pandas as pd

class InitialConditionsSet:

    # not classmethod bc no class level data is needed.
    @staticmethod
    def all_accounts_in_matched_memo_rules_are_present_in_account_set(account_set, budget_item_set, memo_rule_set):

        # distinct_base_account_names__from_acct = pd.DataFrame(
        #     pd.DataFrame(accounts_df.Name)
        #         .apply(lambda x: x[0].split(":")[0], axis=1)
        #         .drop_duplicates()
        # ).rename(columns={0: "Name"})
        # account_names__from_memo = pd.concat(
        #     [
        #         pd.DataFrame(memo_df[["Account_From"]]).rename(
        #             columns={"Account_From": "Name"}
        #         ),
        #         pd.DataFrame(memo_df[["Account_To"]]).rename(
        #             columns={"Account_To": "Name"}
        #         ),
        #     ]
        # )
        #
        # distinct_account_names__from_memo = pd.DataFrame(
        #     account_names__from_memo.loc[
        #         account_names__from_memo.Name != "None", "Name"
        #     ]
        #         .drop_duplicates()
        #         .reset_index(drop=True)
        # )
        #
        # A = None
        # B = None
        # try:
        #
        #     A = {""}
        #     for a in distinct_account_names__from_memo.Name.tolist():
        #         A = A.union({a})
        #     A = A - {
        #         "ALL_LOANS"
        #     }  # if we have a memo rule for ALL_LOANS, we don't want that to be checked against the list of account names
        #
        #     A2 = {""}
        #     for a in distinct_base_account_names__from_acct.Name.tolist():
        #         A2 = A2.union({a})
        #
        #     B = A.intersection(A2)
        #
        #     assert A == B
        # except Exception as e:
        #     error_text = str(e.args) + "\n"
        #     error_text += "An account name was mentioned in a memo rule that did not exist in the account set\n"
        #     error_text += "all accounts mentioned in memo rules:\n"
        #     error_text += distinct_account_names__from_memo.Name.to_string() + "\n"
        #     error_text += "all defined accounts:\n"
        #     error_text += distinct_base_account_names__from_acct.Name.to_string() + "\n"
        #     error_text += "intersection:\n"
        #     error_text += str(B) + "\n"
        #     error_text += "Accounts from Memo:\n"
        #     error_text += str(A) + "\n"
        #     error_ind = True

        raise NotImplementedError #todo

    @staticmethod
    def all_budget_items_have_one_and_only_one_matching_memo_rule(budget_item_set, memo_rule_set):

        # budget_df = budget_set.getBudgetItems()
        #         memo_df = memo_rule_set.getMemoRules()
        #
        #         error_text = ""
        #         error_ind = False
        #
        #         # for each distinct account name in all memo rules to and from fields, there is a matching account
        #         # that is, for each memo rule that mentions an account, the mentioned account should exist
        #         # not that it is NOT a requirement that the converse is true
        #         # that is, there can be an account that has no corresponding memo rules
        #
        #         # should be no duplicates and credit and loan acct splitting is already handled
        #
        #
        #
        #         for index, row in budget_df.iterrows():
        #             memo_rule_set.findMatchingMemoRule(
        #                 row.Memo, row.Priority
        #             )  # this will throw errors as needed

        raise NotImplementedError #todo

    def __eq__(self, other):
        raise NotImplementedError #todo

    def __ne__(self, other):
        raise NotImplementedError #todo

    def __add__(self, other):
        raise NotImplementedError #todo

    def __sub__(self, other):
        raise NotImplementedError #todo

    def __hash__(self):
        raise NotImplementedError #todo

    #todo confirm that I don't need __getstate__, __setstate__. I think pickle can compress data frames and I might not want that

    def __init__(self, start_date, end_date, account_set, budget_item_set, memo_rule_set, interval=1, **kwargs):

        interval = int(interval) #todo it could also be monthly or yearly, which is an irregular cadence
        assert interval >= 1

        try:
            start_date = pd.to_datetime(start_date).date()
        except Exception as e:
            raise e

        try:
            end_date = pd.to_datetime(end_date).date()
        except Exception as e:
            raise e

        assert start_date < end_date

        allowed_kwargs = ['forecast_set_name','forecast_name']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        if 'forecast_set_name' not in kwargs:
            forecast_set_name = ''

        if 'forecast_name' not in kwargs:
            forecast_name = ''

        #this recognizes subclasses of str as well without casting the input
        if not isinstance(forecast_name, str):
            raise TypeError("Expected a string for 'forecast_name'")

        if not isinstance(forecast_set_name, str):
            raise TypeError("Expected a string for 'forecast_set_name'")

        assert account_set.isSufficientToBeginForecast()
        assert InitialConditionsSet.all_budget_items_have_one_and_only_one_matching_memo_rule(budget_item_set, memo_rule_set)
        assert InitialConditionsSet.all_accounts_in_matched_memo_rules_are_present_in_account_set(account_set, budget_item_set,memo_rule_set)

        self.unique_id = None #todo


