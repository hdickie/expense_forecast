import Account
import pytest
import pandas as pd
import datetime

class TestAccount:

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "name,balance,min_balance,max_balance,account_type,billing_start_date_YYYYMMDD,interest_type,apr,interest_cadence,minimum_payment,primary_checking_ind,print_debug_messages,raise_exceptions",
    #     [
    #         (
    #             "checking",
    #             0,
    #             0,
    #             0,
    #             "Checking",
    #             None,
    #             None,
    #             None,
    #             None,
    #             None,
    #             True,
    #             True,
    #             True,
    #         ),
    #         (
    #             "cc: prev stmt bal",
    #             0,
    #             0,
    #             0,
    #             "credit prev stmt bal",
    #             "20000101",
    #             None,
    #             0.25,
    #             "monthly",
    #             50,
    #             False,
    #             True,
    #             True,
    #         ),
    #         (
    #             "cc: curr stmt bal",
    #             0,
    #             0,
    #             0,
    #             "credit curr stmt bal",
    #             None,
    #             None,
    #             None,
    #             None,
    #             None,
    #             False,
    #             True,
    #             True,
    #         ),
    #         (
    #             "loan simple daily: principal balance",
    #             0,
    #             0,
    #             0,
    #             "principal balance",
    #             "20000101",
    #             "simple",
    #             0.25,
    #             "daily",
    #             50,
    #             False,
    #             True,
    #             True,
    #         ),
    #         (
    #             "loan compound monthly: principal balance",
    #             0,
    #             0,
    #             0,
    #             "principal balance",
    #             "20000101",
    #             "compound",
    #             0.25,
    #             "monthly",
    #             50,
    #             False,
    #             True,
    #             True,
    #         ),
    #         (
    #             "loan: interest",
    #             0,
    #             0,
    #             0,
    #             "interest",
    #             None,
    #             None,
    #             None,
    #             None,
    #             None,
    #             False,
    #             True,
    #             True,
    #         ),
    #     ],
    # )
    # def test_Account_constructor_valid_inputs(
    #     self,
    #     name,  # no default because it is a required field
    #     balance,
    #     min_balance,
    #     max_balance,
    #     account_type,  # checking, savings, credit, principal balance, interest
    #     billing_start_date_YYYYMMDD,
    #     interest_type,
    #     apr,
    #     interest_cadence,
    #     minimum_payment,
    #     primary_checking_ind,
    #     print_debug_messages,
    #     raise_exceptions,
    # ):
    #     A = Account.Account(
    #         name,
    #         balance,
    #         min_balance,
    #         max_balance,
    #         account_type,
    #         billing_start_date_YYYYMMDD,
    #         interest_type,
    #         apr,
    #         interest_cadence,
    #         minimum_payment,
    #         primary_checking_ind,
    #         print_debug_messages,
    #         raise_exceptions,
    #     )

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("min_balance,balance,max_balance",
                             [(0, 0, 0)]) #todo
    def test_validate_balances__expect_fail(self, min_balance, balance, max_balance):
        with pytest.raises(Exception):
            Account._validate_balances(min_balance, balance, max_balance)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type",
                             [('account_type')]) #todo
    def test_validate_account_type__expect_fail(self, account_type):
        with pytest.raises(Exception):
            Account._validate_account_type(account_type)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, account_name",
                             [("account_type", "account_name")]) #todo
    def test_validate_account_name__expect_fail(self, account_type, account_name):
        with pytest.raises(Exception):
            Account._validate_account_name(account_type, account_name)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, apr",
                             [("account_type", 0)]) #todo
    def test_validate_apr__expect_fail(self, account_type, apr):
        with pytest.raises(Exception):
            Account._validate_apr(account_type, apr)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, interest_cadence",
                             [("account_type", "interest_cadence")]) #todo
    def test_validate_interest_cadence__expect_fail(self, account_type, interest_cadence):
        with pytest.raises(Exception):
            Account._validate_interest_cadence(account_type, interest_cadence)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, interest_type",
                             [("account_type", "interest_type")]) #todo
    def test_validate_interest_type__expect_fail(self, account_type, interest_type):
        with pytest.raises(Exception):
            Account._validate_interest_type()
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, billing_start_date",
                             [("account_type", "billing_start_date")]) #todo
    def test_validate_billing_start_date__expect_fail(self, account_type, billing_start_date):
        with pytest.raises(Exception):
            Account._validate_billing_start_date(account_type, billing_start_date)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, minimum_payment",
                             [("account_type", 0)]) #todo
    def test_validate_minimum_payment__expect_fail(self, account_type, minimum_payment):
        with pytest.raises(Exception):
            Account._validate_minimum_payment(account_type, minimum_payment)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, primary_checking_ind",
                             [("account_type", "primary_checking_ind")]) #todo
    def test_validate_primary_checking_ind__expect_fail(self, account_type, primary_checking_ind):
        with pytest.raises(Exception):
            Account._validate_primary_checking_ind(account_type, primary_checking_ind)
        raise NotImplementedError



    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("min_balance,balance,max_balance",
                             [(0, 0, 0)])  # todo
    def test_validate_balances__expect_success(self, min_balance, balance, max_balance):
        Account._validate_balances(min_balance, balance, max_balance)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type",
                             [('account_type')])  # todo
    def test_validate_account_type__expect_success(self, account_type):
        Account._validate_account_type(account_type)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, account_name",
                             [("account_type", "account_name")])  # todo
    def test_validate_account_name__expect_success(self, account_type, account_name):
        Account._validate_account_name(account_type, account_name)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, apr",
                             [("account_type", 0)])  # todo
    def test_validate_apr__expect_success(self, account_type, apr):
        Account._validate_apr(account_type, apr)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, interest_cadence",
                             [("account_type", "interest_cadence")])  # todo
    def test_validate_interest_cadence__expect_success(self, account_type, interest_cadence):
        Account._validate_interest_cadence(account_type, interest_cadence)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, interest_type",
                             [("account_type", "interest_type")])  # todo
    def test_validate_interest_type__expect_success(self, account_type, interest_type):
        Account._validate_interest_type(account_type, interest_type)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, billing_start_date",
                             [("account_type", "billing_start_date")])  # todo
    def test_validate_billing_start_date__expect_success(self, account_type, billing_start_date):
        Account._validate_billing_start_date(account_type, billing_start_date)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, minimum_payment",
                             [("account_type", 0)])  # todo
    def test_validate_minimum_payment__expect_success(self, account_type, minimum_payment):
        Account._validate_minimum_payment(account_type, minimum_payment)
        raise NotImplementedError

    @pytest.mark.unit
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.parametrize("account_type, primary_checking_ind",
                             [("account_type", "primary_checking_ind")])  # todo
    def test_validate_primary_checking_ind__expect_success(self, account_type, primary_checking_ind):
        Account._validate_primary_checking_ind(account_type, primary_checking_ind)
        raise NotImplementedError

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "name,balance,min_balance,max_balance,account_type,**kwargs",
    #     [
    #         ("typo- invalid account type", 0, 0, 0, "shmecking",{}),
    #         ("NoneType- no account type", 0, 0, 0, None, {}),
    #         ("context warning for account type- used credit type", 0, 0, 0, "credit", {}),
    #         ("context warning for account type- used loan type", 0, 0, 0, "loan", {}),
    #         ("name missing colon- prev stmt bal", 0, 0, 0, "prev stmt bal", {"billing_start_date":datetime.datetime.strptime("20000101",'%Y%m%d'), "interest_type":"compound", "apr":0, "interest_cadence":"monthly", "minimum_payment":0, "primary_checking_ind":False}),
    #         ("name missing colon- prev stmt bal", 0, 0, 0, "principal balance", {"billing_start_date":datetime.datetime.strptime("20000101",'%Y%m%d'), "interest_type":"simple", "apr":0, "interest_cadence":"daily", "minimum_payment":0, "primary_checking_ind":False}),
    #         ("checking- bal not castable to numeric (None)", None, 0, 0, "Checking",{'primary_checking_ind':True}),
    #         ("checking- bal not castable to numeric (pd.NA)", pd.NA, 0, 0, "Checking", {'primary_checking_ind':True}),
    #         ("checking- bal not castable to numeric (string)", "X", 0, 0, "Checking", {'primary_checking_ind':True}),
    #         ("checking- min bal not castable to numeric (None)", 0, None, 0, "Checking", {'primary_checking_ind':True}),
    #         ("checking- min bal not castable to numeric (pd.NA)", 0, pd.NA, 0, "Checking", {'primary_checking_ind':True}),
    #         ("checking- min bal not castable to numeric (string)", 0, "X", 0, "Checking", {'primary_checking_ind':True}),
    #         ("checking- max bal not castable to numeric (None)", 0, 0, None, "Checking", {'primary_checking_ind':True}),
    #         ("checking- max bal not castable to numeric (pd.NA)", 0, 0, pd.NA, "Checking", {'primary_checking_ind':True}),
    #         ("checking- max bal not castable to numeric (string)", 0, 0, "X", "Checking", {'primary_checking_ind':True}),
    #         ("checking- min gt max", 0, 10, 0, "Checking", {'primary_checking_ind':True}),
    #         ("checking- max lt 0", 0, -100, -10, "Checking", {'primary_checking_ind':True}),
    #         ("checking- billing_start_dt is not None", 0, 0, 0, "Checking", {'billing_start_date':datetime.datetime.strptime("20000101",'%Y%m%d'),'primary_checking_ind':True}),
    #         ("checking- interest_type is not None", 0, 0, 0, "Checking",{'interest_type':'simple','primary_checking_ind':True}),
    #         ("checking- apr is not None", 0, 0, 0, "Checking",{'apr':0, 'primary_checking_ind':True}),
    #         ("checking- interest_cadence is not None", 0, 0, 0, "Checking", {'interest_cadence':'daily','primary_checking_ind':True}),
    #         ("checking- min_payment is not None", 0, 0, 0, "Checking", {'minimum_payment':0, 'primary_checking_ind':True}),
    #         ("cc- billing_start_dt not castable to date YYYYMMDD: prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':'not castable to date', 'interest_type':'compound','apr':0.25,'interest_cadence':'monthly','primary_checking_ind':True}),
    #         # ("cc- interest_type is not compound: prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "simple", 0.25, "monthly", 50, True, True, ValueError),
    #         ("cc- apr is not castable to numeric (None): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':None,'interest_cadence':'monthly','minimum_payment':0,'primary_checking_ind':True}),
    #         ("cc- apr is not castable to numeric (pd.NA): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':pd.NA,'interest_cadence':'monthly','minimum_payment':0,'primary_checking_ind':True}),
    #         ("cc- apr is not castable to numeric (string): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':'X','interest_cadence':'monthly','minimum_payment':0,'primary_checking_ind':True}),
    #         ("cc- apr is lt 0: prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':-1,'interest_cadence':'monthly','minimum_payment':0,'primary_checking_ind':True}),
    #         ("cc- interest_cadence is not monthly: prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':0,'interest_cadence':'shmonthly','minimum_payment':0,'primary_checking_ind':True}),
    #         ("cc- min_payment is not castable to numeric (None): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':0,'interest_cadence':'monthly','minimum_payment':None,'primary_checking_ind':True}),
    #         ("cc- min_payment is not castable to numeric (pd.NA): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':0,'interest_cadence':'monthly','minimum_payment':pd.NA,'primary_checking_ind':True}),
    #         ("cc- min_payment is not castable to numeric (string): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':0,'interest_cadence':'monthly','minimum_payment':'Not Castable','primary_checking_ind':True}),
    #         ("cc- min_payment lt 0: prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", {'billing_start_date':datetime.datetime.strptime("20000101","%Y%m%d"), 'interest_type':'compound','apr':0,'interest_cadence':'monthly','minimum_payment':-1,'primary_checking_ind':True}),
    #         ("cc- billing_start_dt is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", "not None", "compound", 0.25, "monthly", 50, False),
    #         ("cc- interest_type is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, "compound", 0.25, "monthly", 50, False),
    #         ("cc- apr is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, None, 0.25, "monthly", 50, False),
    #         ("cc- interest_cadence is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, None, None, "monthly", 50, False),
    #         ("cc- min_payment is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, None, None, None, 50, False),
    #         ("loan- billing_start_dt not castable to date YYYYMMDD: principal balance ", 0, 0, 0, "principal balance", "1234", "compound", 0.25, "monthly", 50, False),
    #         ("loan- interest_type is not simple or compound: principal balance ", 0, 0, 0, "principal balance", "20000101", "shmimple", 0.25, "monthly", 50, False),
    #         ("loan- apr is not castable to numeric (None): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", None, "monthly", 50, False),
    #         ("loan- apr is not castable to numeric (pd.NA): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", pd.NA, "monthly", 50, False),
    #         ("loan- apr is not castable to numeric (string): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", "X", "monthly", 50, False),
    #         ("loan- apr is lt 0: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", -0.25, "monthly", 50, False),
    #         # ("loan- interest_cadence is not daily, monthly or yearly: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", -0.25, "weekly", 50, True, True, ValueError),
    #         ("loan- min_payment is not castable to numeric (None): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", None, False),
    #         ("loan- min_payment is not castable to numeric (pd.NA): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", pd.NA, False),
    #         ("loan- min_payment is not castable to numeric (string): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", "X", False),
    #         ("loan- min_payment lt 0: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", -50, False),
    #         ("loan- billing_start_dt is not None: interest ", 0, 0, 0, "interest", "not None", "compound", 0.25, "monthly", 50, False),
    #         ("loan- interest_type is not None: interest ", 0, 0, 0, "interest", None, "compound", 0.25, "monthly", 50, False),
    #         ("loan- apr is not None: interest ", 0, 0, 0, "interest", None, None, 0.25, "monthly", 50, False),
    #         ("loan- interest_cadence is not None: interest ", 0, 0, 0, "interest", None, None, None, "monthly", 50, False),
    #         ("loan- min_payment is not None: interest ", 0, 0, 0, "interest", None, None, None, None, 50, False),
    #     ],
    # )
    # def test_Account_constructor_invalid_inputs( self, name, balance, min_balance, max_balance, account_type, **kwargs ):
    #
    #     # todo maybe check for substrings in exception bc i wanna make sure they throw for the right reason
    #     with pytest.raises(Exception):
    #         Account.Account(
    #             name,
    #             balance,
    #             min_balance,
    #             max_balance,
    #             account_type,
    #             **kwargs
    #         )

    # @pytest.mark.unit
    # @pytest.mark.skip(reason="this test sucks")
    # def test_str(self):
    #     test_account = Account.Account(
    #         name="test checking",
    #         balance=0,
    #         min_balance=0,
    #         max_balance=0,
    #         account_type="checking",
    #     )
    #     str(test_account)


# FAILED tests/Account/unit/test_Account__unit_test.py::TestAccount::test_Account_constructor_valid_inputs[checking-0-0-0-Checking-None-None-None-None-None-True-True-True] - TypeError: Account.__init__() takes 6 positional arguments but 14 were given
# FAILED tests/Account/unit/test_Account__unit_test.py::TestAccount::test_Account_constructor_valid_inputs[cc: prev stmt bal-0-0-0-credit prev stmt bal-20000101-None-0.25-monthly-50-False-True-True] - TypeError: Account.__init__() takes 6 positional arguments but 14 were given
# FAILED tests/Account/unit/test_Account__unit_test.py::TestAccount::test_Account_constructor_valid_inputs[cc: curr stmt bal-0-0-0-credit curr stmt bal-None-None-None-None-None-False-True-True] - TypeError: Account.__init__() takes 6 positional arguments but 14 were given
# FAILED tests/Account/unit/test_Account__unit_test.py::TestAccount::test_Account_constructor_valid_inputs[loan simple daily: principal balance-0-0-0-principal balance-20000101-simple-0.25-daily-50-False-True-True] - TypeError: Account.__init__() takes 6 positional arguments but 14 were given
# FAILED tests/Account/unit/test_Account__unit_test.py::TestAccount::test_Account_constructor_valid_inputs[loan compound monthly: principal balance-0-0-0-principal balance-20000101-compound-0.25-monthly-50-False-True-True] - TypeError: Account.__init__() takes 6 positional arguments but 14 were given
# FAILED tests/Account/unit/test_Account__unit_test.py::TestAccount::test_Account_constructor_valid_inputs[loan: interest-0-0-0-interest-None-None-None-None-None-False-True-True] - TypeError: Account.__init__() takes 6 positional arguments but 14 were given
# FAILED tests/ExpenseForecast/unit/test_ExpenseForecast__unit_test.py::TestExpenseForecastUnit::test_evaluate_account_milestone[test_account_milestone-account_set0-budget_set0-memo_rule_set0-20000101-20000103-milestone_set0-account_milestone_names0-expected_milestone_dates0] - TypeError: ExpenseForecast.__init__() takes 3 positional arguments but 7 were given
# 25 failed, 78 passed, 13 skipped, 158 deselected in 21.58s
