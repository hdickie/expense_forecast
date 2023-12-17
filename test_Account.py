import Account
import pytest
import pandas as pd

class TestAccount:

    @pytest.fixture
    def checkingAccount(self):
        return NotImplementedError

    @pytest.fixture
    def creditCurrStmtBalAccount(self):
        return NotImplementedError

    @pytest.fixture
    def creditPrevStmtBalAccount(self):
        return NotImplementedError

    @pytest.fixture
    def loanPrincipalBalanceSimpleDailyAccount(self):
        return NotImplementedError

    @pytest.fixture
    def loanPrincipalBalanceMonthlyCompoundAccount(self):
        return NotImplementedError

    @pytest.fixture
    def loanInterestAccount(self):
        return NotImplementedError


    def test_Account_doctests(self):
        raise NotImplementedError

    @pytest.mark.parametrize("name,balance,min_balance,max_balance,account_type,billing_start_date_YYYYMMDD,interest_type,apr,interest_cadence,minimum_payment,print_debug_messages,raise_exceptions",
                             [("checking", 0, 0, 0, "Checking", None, None, None, None, None, True, True),
                              ("cc: prev stmt bal", 0, 0, 0, "prev stmt bal", "20000101", "compound", 0.25, "monthly", 50, True, True),
                              ("cc: curr stmt bal", 0, 0, 0, "curr stmt bal", None, None, None, None, None, True, True),
                              ("loan simple daily: principal balance", 0, 0, 0, "principal balance", "20000101", "simple", 0.25, "daily", 50, True, True),
                              ("loan compound monthly: principal balance", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", 50, True, True),
                              ("loan: interest", 0, 0, 0, "interest", None, None, None, None, 50, True, True),

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
                            print_debug_messages,
                            raise_exceptions)

    def test_Account_str(self):
        raise NotImplementedError



    @pytest.mark.parametrize("name,balance,min_balance,max_balance,account_type,billing_start_date_YYYYMMDD,interest_type,apr,interest_cadence,minimum_payment,print_debug_messages,raise_exceptions,expected_exception",
                             [("N/A- invalid account type", 0,0,0,"shmecking",None,None,None,None,None,True,True,ValueError),
                              ("checking- bal not castable to numeric (None)", None,0,0,"Checking",None,None,None,None,None,True,True,TypeError),
                              ("checking- bal not castable to numeric (pd.NA)", pd.NA, 0, 0, "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- bal not castable to numeric (string)", "X", 0, 0, "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- min bal not castable to numeric (None)", 0, None, 0, "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- min bal not castable to numeric (pd.NA)", 0, pd.NA, 0, "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- min bal not castable to numeric (string)", 0, "X", 0, "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- max bal not castable to numeric (None)", 0, 0, None, "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- max bal not castable to numeric (pd.NA)", 0, 0, pd.NA, "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- max bal not castable to numeric (string)", 0, 0, "X", "Checking", None, None, None, None, None, True, True, TypeError),
                              ("checking- min gt max", 0, 10, 0, "Checking", None, None, None, None, None, True, True, ValueError),
                              ("checking- max lt 0", 0, -100, -10, "Checking", None, None, None, None, None, True, True, ValueError),
                              ("checking- billing_start_dt is not None", 0, 0, 0, "Checking", 'not None', None, None, None, None, True, True, ValueError),
                              ("checking- interest_type is not None", 0, 0, 0, "Checking", None, 'not None', None, None, None, True, True, ValueError),
                              ("checking- apr is not None", 0, 0, 0, "Checking", None, None, 'not None', None, None, True, True, ValueError),
                              ("checking- interest_cadence is not None", 0, 0, 0, "Checking", None, None, None, 'not None', None, True, True, ValueError),
                              ("checking- min_payment is not None", 0, 0, 0, "Checking", None, None, None, None, 'not None', True, True, ValueError),

                              ("cc- billing_start_dt not castable to date YYYYMMDD: prev stmt bal ", 0,0,0,"prev stmt bal","1234","compound",0.25,"monthly",50,True,True,TypeError),
                              #("cc- interest_type is not compound: prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "simple", 0.25, "monthly", 50, True, True, ValueError),
                              ("cc- apr is not castable to numeric (None): prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", None, "monthly", 50, True, True, TypeError),
                              ("cc- apr is not castable to numeric (pd.NA): prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", pd.NA, "monthly", 50, True, True, TypeError),
                              ("cc- apr is not castable to numeric (string): prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", "X", "monthly", 50, True, True, TypeError),
                              ("cc- apr is lt 0: prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", -0.25, "monthly", 50, True, True, ValueError),
                              ("cc- interest_cadence is not monthly: prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", -0.25, "daily", 50, True, True, ValueError),
                              ("cc- min_payment is not castable to numeric (None): prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", 0.25, "monthly", None, True, True, TypeError),
                              ("cc- min_payment is not castable to numeric (pd.NA): prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", 0.25, "monthly", pd.NA, True, True, TypeError),
                              ("cc- min_payment is not castable to numeric (string): prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", 0.25, "monthly", "X", True, True, TypeError),
                              ("cc- min_payment lt 0: prev stmt bal ", 0, 0, 0, "prev stmt bal", "20000101", "compound", 0.25, "monthly", -50, True, True, ValueError),

                              ("cc- billing_start_dt is not None: curr stmt bal ", 0, 0, 0, "prev stmt bal", "not None", "compound", 0.25, "monthly", 50, True, True, TypeError),
                              ("cc- interest_type is not None: curr stmt bal ", 0, 0, 0, "prev stmt bal", None, "compound", 0.25, "monthly", 50, True, True, TypeError),
                              ("cc- apr is not None: curr stmt bal ", 0, 0, 0, "prev stmt bal", None, None, 0.25, "monthly", 50, True, True, TypeError),
                              ("cc- interest_cadence is not None: curr stmt bal ", 0, 0, 0, "prev stmt bal", None, None, None, "monthly", 50, True, True, TypeError),
                              ("cc- min_payment is not None: curr stmt bal ", 0, 0, 0, "prev stmt bal", None, None, None, None, 50, True, True, TypeError),

                              ("loan- billing_start_dt not castable to date YYYYMMDD: principal balance ", 0, 0, 0, "principal balance", "1234", "compound", 0.25, "monthly", 50, True, True, TypeError),
                              ("loan- interest_type is not simple or compound: principal balance ", 0, 0, 0, "principal balance", "20000101", "shmimple", 0.25, "monthly", 50, True, True, ValueError),
                              ("loan- apr is not castable to numeric (None): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", None, "monthly", 50, True, True, TypeError),
                              ("loan- apr is not castable to numeric (pd.NA): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", pd.NA, "monthly", 50, True, True, TypeError),
                              ("loan- apr is not castable to numeric (string): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", "X", "monthly", 50, True, True, TypeError),
                              ("loan- apr is lt 0: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", -0.25, "monthly", 50, True, True, ValueError),
                              #("loan- interest_cadence is not daily, monthly or yearly: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", -0.25, "weekly", 50, True, True, ValueError),
                              ("loan- min_payment is not castable to numeric (None): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", None, True, True, TypeError),
                              ("loan- min_payment is not castable to numeric (pd.NA): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", pd.NA, True, True, TypeError),
                              ("loan- min_payment is not castable to numeric (string): principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", "X", True, True, TypeError),
                              ("loan- min_payment lt 0: principal balance ", 0, 0, 0, "principal balance", "20000101", "compound", 0.25, "monthly", -50, True, True, ValueError),

                              ("loan- billing_start_dt is not None: interest ", 0, 0, 0, "interest", "not None", "compound", 0.25, "monthly", 50, True, True, ValueError),
                              ("loan- interest_type is not None: interest ", 0, 0, 0, "interest", None, "compound", 0.25, "monthly", 50, True, True, ValueError),
                              ("loan- apr is not None: interest ", 0, 0, 0, "interest", None, None, 0.25, "monthly", 50, True, True, ValueError),
                              ("loan- interest_cadence is not None: interest ", 0, 0, 0, "interest", None, None, None, "monthly", 50, True, True, ValueError),
                              ("loan- min_payment is not None: interest ", 0, 0, 0, "interest", None, None, None, None, 50, True, True, ValueError),

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
                 print_debug_messages,
                 raise_exceptions,
                 expected_exception):

        with pytest.raises(expected_exception):
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
                                print_debug_messages,
                                raise_exceptions)

    def test_Account_repr(self):
        raise NotImplementedError

    def test_Account_toJSON(self):
        raise NotImplementedError

