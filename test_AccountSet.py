import unittest
import Account, AccountSet, doctest

class TestAccountSetMethods(unittest.TestCase):

    def test_AccountSet_doctests(self):
        #doctest.testmod(doctest_AccountSet,name="doctest_AccountSet")
        #doctest.DocTestSuite(module='doctest_AccountSet')
        #doctest.testfile('doctest_AccountSet.py')
        #doctest.run_docstring_examples('doctest_AccountSet.py',globs={})
        doctest.testmod(AccountSet)

    def test_AccountSet_Constructor(self):

        # check constructor with list of accounts
        checking_acct = Account.Account(name="test checking",
        balance = 0,
        min_balance = 0,
        max_balance = 0,
        account_type = 'checking')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(AccountSet.AccountSet([checking_acct]))))

        prv_bal_acct = Account.Account(name='Credit: Prev Stmt Bal',
        balance = 0,
        min_balance = 0,
        max_balance = 0,
        account_type = 'Prev Stmt Bal',
        billing_start_date_YYYYMMDD = '20000101',
        interest_type = 'compound',
        apr = 0.05,
        interest_cadence = 'monthly',
        minimum_payment = 40)

        cur_bal_acct = Account.Account(name='Credit: Curr Stmt Bal',
                                       balance=0,
                                       min_balance=0,
                                       max_balance=0,
                                       account_type='Curr Stmt Bal',
                                       billing_start_date_YYYYMMDD=None,
                                       interest_type=None,
                                       apr=None,
                                       interest_cadence=None,
                                       minimum_payment=None)

        principal_balance_acct = Account.Account(name='Loan: Principal Balance',
                                       balance=0,
                                       min_balance=0,
                                       max_balance=0,
                                       account_type='Principal Balance',
                                       billing_start_date_YYYYMMDD='20000101',
                                       interest_type='simple',
                                       apr=0.05,
                                       interest_cadence='daily',
                                       minimum_payment=40)

        interest_acct = Account.Account(name='Loan: Interest',
                                       balance=0,
                                       min_balance=0,
                                       max_balance=0,
                                       account_type='Interest',
                                       billing_start_date_YYYYMMDD=None,
                                       interest_type=None,
                                       apr=None,
                                       interest_cadence=None,
                                       minimum_payment=None)


        #these hould not throw exceptions
        valid_accountset_loan = AccountSet.AccountSet([checking_acct,principal_balance_acct,interest_acct])
        valid_accountset_cc = AccountSet.AccountSet([checking_acct, prv_bal_acct, cur_bal_acct])

        with self.assertRaises(ValueError):
            AccountSet.AccountSet([checking_acct,interest_acct])

        with self.assertRaises(ValueError):
            AccountSet.AccountSet([checking_acct,principal_balance_acct])

        with self.assertRaises(ValueError):
            AccountSet.AccountSet([checking_acct,cur_bal_acct])

        with self.assertRaises(ValueError):
            AccountSet.AccountSet([checking_acct,prv_bal_acct])


    def test_addAccount(self):

        test_account_set = AccountSet.AccountSet([])

        with self.assertRaises(ValueError):
            test_account_set.addAccount(name="test loan",
                                    balance=0,
                                    min_balance=0,
                                    max_balance=10000,
                                    account_type='loan',
                                    billing_start_date_YYYYMMDD='20220101',
                                    interest_type = 'simple',
                                    apr=0.03,
                                    interest_cadence='daily',
                                    minimum_payment=1,
                                    previous_statement_balance=None,
                                    principal_balance=900,
                                    accrued_interest=100,
                            print_debug_messages=False)

        # create a non-loan and non-credit type account
        test_account_set.addAccount(name="test checking",
                                    balance=0,
                                    min_balance=0,
                                    max_balance=0,
                                    account_type='checking')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))

        # create a credit card type account
        test_account_set.addAccount(name="test credit",
                                    balance=0,
                                    min_balance=0,
                                    max_balance=0,
                                    account_type='credit',
                                    billing_start_date_YYYYMMDD='20220101',
                                    interest_type='compound',
                                    apr=0.05,
                                    interest_cadence='monthly',
                                    minimum_payment=0,
                                    previous_statement_balance=0,
                                    principal_balance=None,
                                    accrued_interest=None
                                    )
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))

        # create a loan type account
        test_account_set.addAccount(name="test loan",
                                    balance=1000,
                                    min_balance=0,
                                    max_balance=10000,
                                    account_type='loan',
                                    billing_start_date_YYYYMMDD='20220101',
                                    interest_type = 'simple',
                                    apr=0.03,
                                    interest_cadence='daily',
                                    minimum_payment=1,
                                    previous_statement_balance=None,
                                    principal_balance=900,
                                    accrued_interest=100
                                    )
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))




    def test_getAccounts(self):
        test_account_set = AccountSet.AccountSet([])
        test_df = test_account_set.getAccounts()
        self.assertIsNotNone(test_df)

        test_account_set.addAccount(name="test checking",
         balance = 0,
         min_balance = 0,
         max_balance = 0,
         account_type = 'checking')
        test_df = test_account_set.getAccounts()
        self.assertIsNotNone(test_df)

    def test_str(self):
        test_account_set = AccountSet.AccountSet([])
        account_str = str(test_account_set)
        self.assertIsNotNone(account_str)

        test_account_set.addAccount(name="test checking",
         balance = 0,
         min_balance = 0,
         max_balance = 0,
         account_type = 'checking')
        account_str = str(test_account_set)
        self.assertIsNotNone(account_str)

    def test_repr(self):
        self.assertIsNotNone(repr(AccountSet.AccountSet()))

    def test_toJSON(self):

        # test_account_set = AccountSet.AccountSet()
        #
        # # create a non-loan and non-credit type account
        # test_account_set.addAccount(name="test checking",
        #                             balance=0,
        #                             min_balance=0,
        #                             max_balance=0,
        #                             account_type='checking')
        #
        # # create a credit card type account
        # test_account_set.addAccount(name="test credit",
        #                             balance=0,
        #                             min_balance=0,
        #                             max_balance=0,
        #                             account_type='credit',
        #                             billing_start_date_YYYYMMDD='20220101',
        #                             interest_type='compound',
        #                             apr=0.05,
        #                             interest_cadence='monthly',
        #                             minimum_payment=0,
        #                             previous_statement_balance=0,
        #                             principal_balance=None,
        #                             accrued_interest=None
        #                             )
        #
        # # create a loan type account
        # test_account_set.addAccount(name="test loan",
        #                             balance=1000,
        #                             min_balance=0,
        #                             max_balance=10000,
        #                             account_type='loan',
        #                             billing_start_date_YYYYMMDD='20220101',
        #                             interest_type='simple',
        #                             apr=0.03,
        #                             interest_cadence='daily',
        #                             minimum_payment=1,
        #                             previous_statement_balance=None,
        #                             principal_balance=900,
        #                             accrued_interest=100
        #                             )

        test_account_set = AccountSet.AccountSet([Account.Account(name="Credit: Curr Stmt Bal",
        balance=50,
        min_balance=0,
        max_balance=100,
        apr=None,
        interest_cadence=None,
        interest_type=None,
        billing_start_date_YYYYMMDD=None,
        account_type='Curr Stmt Bal',
        minimum_payment=None
        ),
        Account.Account(name="Credit: Prev Stmt Bal",
        balance=50,
        min_balance=0,
        max_balance=100,
        apr=0.05,
        interest_cadence="Monthly",
        interest_type="Compound",
        billing_start_date_YYYYMMDD="20000101",
        account_type='Prev Stmt Bal',
        minimum_payment=40
        ),Account.Account(name="Loan: Interest",
        balance=50,
        min_balance=0,
        max_balance=100,
        apr=None,
        interest_cadence=None,
        interest_type=None,
        billing_start_date_YYYYMMDD=None,
        account_type='Interest',
        minimum_payment=None
        ),
        Account.Account(name="Loan: Principal Balance",
        balance=50,
        min_balance=0,
        max_balance=100,
        apr=0.05,
        interest_cadence="Monthly",
        interest_type="Compound",
        billing_start_date_YYYYMMDD="20000101",
        account_type='Principal Balance',
        minimum_payment=40
        )])
        test_account_set_JSON = test_account_set.toJSON()

        test_expectation = """{
{
"Name":"Credit: Curr Stmt Bal",
"Balance":"50.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Curr Stmt Bal",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Credit: Prev Stmt Bal",
"Balance":"50.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Prev Stmt Bal",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
},
{
"Name":"Loan: Interest",
"Balance":"50.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Interest",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Loan: Principal Balance",
"Balance":"50.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Principal Balance",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
}
}"""
        assert test_account_set_JSON == test_expectation
