import Account
import pytest
import pandas as pd

class TestAccount:

    @pytest.mark.unit
    @pytest.mark.parametrize("name,balance,min_balance,max_balance,account_type,billing_start_date_YYYYMMDD,interest_type,apr,interest_cadence,minimum_payment,primary_checking_ind,print_debug_messages,raise_exceptions",
                             [("checking", 0, 0, 0, "Checking", None, None, None, None, None, True, True, True),
                              ("cc: prev stmt bal", 0, 0, 0, "credit prev stmt bal", "20000101", None, 0.25, "monthly", 50, False, True, True),
                              ("cc: curr stmt bal", 0, 0, 0, "credit curr stmt bal", None, None, None, None, None, False, True, True),
                              ("loan simple daily: principal balance", 0, 0, 0, "principal balance", "20000101", "simple", 0.25, "daily", 50, False, True, True),
                              ("loan compound monthly: principal balance", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", 50, False, True, True),
                              ("loan: interest", 0, 0, 0, "interest", None, None, None, None, None, False, True, True),

                              ])
    def test_Account_constructor_valid_inputs(self, name,  # no default because it is a required field
                                                balance,
                                                min_balance,
                                                max_balance,
                                                account_type,  # checking, savings, credit, principal balance, interest
                                                billing_start_date_YYYYMMDD,
                                                interest_type,
                                                apr,
                                                interest_cadence,
                                                minimum_payment,
                                                primary_checking_ind,
                                                print_debug_messages,
                                                raise_exceptions):
        A = Account.Account(name,
                            balance,
                            min_balance,
                            max_balance,
                            account_type,
                            billing_start_date_YYYYMMDD,
                            interest_type,
                            apr,
                            interest_cadence,
                            minimum_payment,
                            primary_checking_ind,
                            print_debug_messages,
                            raise_exceptions)

    @pytest.mark.unit
    @pytest.mark.parametrize("name,balance,min_balance,max_balance,account_type,billing_start_date_YYYYMMDD,interest_type,apr,interest_cadence,minimum_payment,primary_checking_ind,print_debug_messages,raise_exceptions",
                             [("typo- invalid account type", 0,0,0,"shmecking",None,None,None,None,None,False,True,True),
                              ("NoneType- no account type", 0, 0, 0, None, None, None, None, None, None,False, True,True),
                              ("context warning for account type- used credit type", 0, 0, 0, 'credit', None, None, None, None, None,False, True, True),
                              ("context warning for account type- used loan type", 0, 0, 0, 'loan', None, None, None,None, None,False, True, True),

                              ("name missing colon- prev stmt bal", 0, 0, 0, 'prev stmt bal', "20000101", 'compound',0, 'monthly',0,False, True, True),
                              ("name missing colon- prev stmt bal", 0, 0, 0, 'principal balance', "20000101", 'simple',0, 'daily',0,False, True, True),

                              ("checking- bal not castable to numeric (None)", None,0,0,"Checking",None,None,None,None,None,True,True,True),
                              ("checking- bal not castable to numeric (pd.NA)", pd.NA, 0, 0, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- bal not castable to numeric (string)", "X", 0, 0, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- min bal not castable to numeric (None)", 0, None, 0, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- min bal not castable to numeric (pd.NA)", 0, pd.NA, 0, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- min bal not castable to numeric (string)", 0, "X", 0, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- max bal not castable to numeric (None)", 0, 0, None, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- max bal not castable to numeric (pd.NA)", 0, 0, pd.NA, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- max bal not castable to numeric (string)", 0, 0, "X", "Checking", None, None, None, None, None,True, True, True),
                              ("checking- min gt max", 0, 10, 0, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- max lt 0", 0, -100, -10, "Checking", None, None, None, None, None,True, True, True),
                              ("checking- billing_start_dt is not None", 0, 0, 0, "Checking", 'not None', None, None, None, None,True, True, True),
                              ("checking- interest_type is not None", 0, 0, 0, "Checking", None, 'not None', None, None, None,True, True, True),
                              ("checking- apr is not None", 0, 0, 0, "Checking", None, None, 'not None', None, None,True, True, True),
                              ("checking- interest_cadence is not None", 0, 0, 0, "Checking", None, None, None, 'not None', None,True, True, True),
                              ("checking- min_payment is not None", 0, 0, 0, "Checking", None, None, None, None, 'not None',True, True, True),

                              ("cc- billing_start_dt not castable to date YYYYMMDD: prev stmt bal ", 0,0,0,"credit prev stmt bal","1234","compound",0.25,"monthly",50,False,True,True),
                              #("cc- interest_type is not compound: prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "simple", 0.25, "monthly", 50, True, True, ValueError),
                              ("cc- apr is not castable to numeric (None): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", None, "monthly", 50, False,True, True),
                              ("cc- apr is not castable to numeric (pd.NA): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", pd.NA, "monthly", 50,False, True, True),
                              ("cc- apr is not castable to numeric (string): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", "X", "monthly", 50,False, True, True),
                              ("cc- apr is lt 0: prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", -0.25, "monthly", 50,False, True, True),
                              ("cc- interest_cadence is not monthly: prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", -0.25, "daily", 50,False, True, True),
                              ("cc- min_payment is not castable to numeric (None): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", 0.25, "monthly", None,False, True, True),
                              ("cc- min_payment is not castable to numeric (pd.NA): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", 0.25, "monthly", pd.NA,False, True, True),
                              ("cc- min_payment is not castable to numeric (string): prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", 0.25, "monthly", "X",False, True, True),
                              ("cc- min_payment lt 0: prev stmt bal ", 0, 0, 0, "credit prev stmt bal", "20000101", "compound", 0.25, "monthly", -50,False, True, True),

                              ("cc- billing_start_dt is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", "not None", "compound", 0.25, "monthly", 50,False, True, True),
                              ("cc- interest_type is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, "compound", 0.25, "monthly", 50,False, True, True),
                              ("cc- apr is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, None, 0.25, "monthly", 50,False, True, True),
                              ("cc- interest_cadence is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, None, None, "monthly", 50,False, True, True),
                              ("cc- min_payment is not None: curr stmt bal ", 0, 0, 0, "credit prev stmt bal", None, None, None, None, 50,False, True, True),

                              ("loan- billing_start_dt not castable to date YYYYMMDD: principal balance ", 0, 0, 0, "principal balance", "1234", "compound", 0.25, "monthly", 50,False, True, True),
                              ("loan- interest_type is not simple or compound: principal balance ", 0, 0, 0, "principal balance", "20000101", "shmimple", 0.25, "monthly", 50,False, True, True),
                              ("loan- apr is not castable to numeric (None): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", None, "monthly", 50,False, True, True),
                              ("loan- apr is not castable to numeric (pd.NA): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", pd.NA, "monthly", 50,False, True, True),
                              ("loan- apr is not castable to numeric (string): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", "X", "monthly", 50,False, True, True),
                              ("loan- apr is lt 0: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", -0.25, "monthly", 50,False, True, True),
                              #("loan- interest_cadence is not daily, monthly or yearly: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", -0.25, "weekly", 50, True, True, ValueError),
                              ("loan- min_payment is not castable to numeric (None): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", None,False, True, True),
                              ("loan- min_payment is not castable to numeric (pd.NA): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", pd.NA,False, True, True),
                              ("loan- min_payment is not castable to numeric (string): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", "X",False, True, True),
                              ("loan- min_payment lt 0: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", -50, False,True, True),

                              ("loan- billing_start_dt is not None: interest ", 0, 0, 0, "interest", "not None", "compound", 0.25, "monthly", 50,False, True, True),
                              ("loan- interest_type is not None: interest ", 0, 0, 0, "interest", None, "compound", 0.25, "monthly", 50,False, True, True),
                              ("loan- apr is not None: interest ", 0, 0, 0, "interest", None, None, 0.25, "monthly", 50,False, True, True),
                              ("loan- interest_cadence is not None: interest ", 0, 0, 0, "interest", None, None, None, "monthly", 50,False, True, True),
                              ("loan- min_payment is not None: interest ", 0, 0, 0, "interest", None, None, None, None, 50,False, True, True),

                              ])
    def test_Account_constructor_invalid_inputs(self,name,
                 balance,
                 min_balance,
                 max_balance,
                 account_type,
                 billing_start_date_YYYYMMDD,
                 interest_type,
                 apr,
                 interest_cadence,
                 minimum_payment,
                primary_checking_ind,
                 print_debug_messages,
                 raise_exceptions):

        #todo maybe check for substrings in exception bc i wanna make sure they throw for the right reason
        with pytest.raises(Exception):
            Account.Account(name,
                                balance,
                                min_balance,
                                max_balance,
                                account_type,
                                billing_start_date_YYYYMMDD,
                                interest_type,
                                apr,
                                interest_cadence,
                                minimum_payment,
                                print_debug_messages,
                                raise_exceptions)

    @pytest.mark.unit
    @pytest.mark.skip(reason="this test sucks")
    def test_str(self):
        test_account = Account.Account(name="test checking",
                                       balance=0,
                                       min_balance=0,
                                       max_balance=0,
                                       account_type='checking')
        str(test_account)

