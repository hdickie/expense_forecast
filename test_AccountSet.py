import pytest
import pandas as pd
import tempfile
import Account, AccountSet, doctest, copy

def compound_loan_A():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan A",balance=1100,min_balance=0,max_balance=1100,account_type="loan",
                    billing_start_date_YYYYMMDD="20240101",interest_type="compound",apr=0.1,interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1000,interest_balance=100)
    return A.accounts

def compound_loan_A_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan A",balance=1000,min_balance=0,max_balance=1100,account_type="loan",
                    billing_start_date_YYYYMMDD="20240101",interest_type="compound",apr=0.1,interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1000,interest_balance=0)
    return A.accounts

def compound_loan_B():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan B", balance=1600, min_balance=0, max_balance=1600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.01,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1500, interest_balance=100)
    return A.accounts

def compound_loan_B_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan B", balance=1500, min_balance=0, max_balance=1600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.01,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1500, interest_balance=0)
    return A.accounts

def compound_loan_C():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan C", balance=2600, min_balance=0, max_balance=2600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.05,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=2500, interest_balance=100)
    return A.accounts

def compound_loan_C_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan C", balance=2500, min_balance=0, max_balance=2600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.05,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=2500, interest_balance=0)
    return A.accounts

def checking():
    A = AccountSet.AccountSet([])
    A.createAccount("test checking", balance=10000, min_balance=0, max_balance=10000, account_type="checking")
    return A.accounts

def cc(curr_bal,prev_bal,apr,bsd):
    A = AccountSet.AccountSet([])
    A.createAccount('test cc',curr_bal,0,20000,'credit',bsd,'compound',apr,'monthly',40,prev_bal)
    return A.accounts


def one_loan__p_1000__i_100__apr_01():
    return AccountSet.AccountSet(checking()+compound_loan_A())

def two_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001():
    return AccountSet.AccountSet(checking() + compound_loan_A() + compound_loan_B())

def three_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001___p_2500__i_100__apr_005():
    return AccountSet.AccountSet(checking() + compound_loan_A() + compound_loan_B() + compound_loan_C())

# def one_loan__p_1000__i_000__apr_01():
#     return AccountSet.AccountSet(checking()+compound_loan_A_no_interest())
#
# def two_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001():
#     return AccountSet.AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest())

def three_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001___p_2500__i_000__apr_005():
    return AccountSet.AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest() + compound_loan_C_no_interest())

class TestAccountSet:

    def test_AccountSet_doctests(self):
        #doctest.testmod(doctest_AccountSet,name="doctest_AccountSet")
        #doctest.DocTestSuite(module='doctest_AccountSet')
        #doctest.testfile('doctest_AccountSet.py')
        #doctest.run_docstring_examples('doctest_AccountSet.py',globs={})
        doctest.testmod(AccountSet)
    #

    @pytest.mark.parametrize(
        "accounts__list,expected_exception",
        [
            ([Account.Account(
              name='test combined total violates maximum : Principal Balance',
              balance=60,
              min_balance=0,
              max_balance=100,
              account_type='principal balance',
              billing_start_date_YYYYMMDD='20000101',
              interest_type='compound',
              apr=0.01,
              interest_cadence='monthly',
              minimum_payment=50
              ),
             Account.Account(
                 name='test combined total violates maximum : Interest',
                 balance=60,
                 min_balance=0,
                 max_balance=100,
                 account_type='interest',
                 billing_start_date_YYYYMMDD=None,
                 interest_type=None,
                 apr=None,
                 interest_cadence=None,
                 minimum_payment=None
             )
             ]
            ,ValueError), #combined balance violates max (loan)

            ([Account.Account(
                name='test cc : Prev Stmt Bal',
                balance=60,
                min_balance=0,
                max_balance=100,
                account_type='prev stmt bal',
                billing_start_date_YYYYMMDD='20000101',
                interest_type=None,
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test cc : Curr Stmt Bal',
                     balance=60,
                     min_balance=0,
                     max_balance=100,
                     account_type='curr stmt bal',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # combined balance violates max (cc)

            ([Account.Account(
                name='test cc : Prev Stmt Bal',
                balance=-100,
                min_balance=-100,
                max_balance=100,
                account_type='prev stmt bal',
                billing_start_date_YYYYMMDD='20000101',
                interest_type=None,
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test cc : Curr Stmt Bal',
                     balance=-100,
                     min_balance=-100,
                     max_balance=100,
                     account_type='curr stmt bal',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # combined balance violates min (cc)

            ([Account.Account(
                name='test : Principal Balance',
                balance=-100,
                min_balance=-100,
                max_balance=100,
                account_type='principal balance',
                billing_start_date_YYYYMMDD='20000101',
                interest_type='compound',
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test : Interest',
                     balance=-100,
                     min_balance=-100,
                     max_balance=100,
                     account_type='interest',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # combined balance violates min (loan)

            ([Account.Account(
                name='test combined total violates maximum : Principal Balance',
                balance=0,
                min_balance=0,
                max_balance=100,
                account_type='principal balance',
                billing_start_date_YYYYMMDD='20000101',
                interest_type='compound',
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test combined total violates maximum : Interest',
                     balance=60,
                     min_balance=0,
                     max_balance=1000,
                     account_type='interest',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # non-matching max_balance (loan)

            ([Account.Account(
                name='test combined total violates maximum : Prev Stm Bal',
                balance=0,
                min_balance=0,
                max_balance=1000,
                account_type='prev stmt bal',
                billing_start_date_YYYYMMDD='20000101',
                interest_type=None,
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test combined total violates maximum : Curr Stmt Bal',
                     balance=60,
                     min_balance=60,
                     max_balance=1000,
                     account_type='curr stmt bal',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # non-matching min_balance (cc)

            ([Account.Account(
                name='test : Principal Balance',
                balance=10,
                min_balance=10,
                max_balance=100,
                account_type='principal balance',
                billing_start_date_YYYYMMDD='20000101',
                interest_type='compound',
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test : Interest',
                     balance=60,
                     min_balance=0,
                     max_balance=100,
                     account_type='interest',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # non-matching min_balance (loan)

            ([Account.Account(
                name='test : Prev Stmt Bal',
                balance=10,
                min_balance=10,
                max_balance=100,
                account_type='prev stmt bal',
                billing_start_date_YYYYMMDD='20000101',
                interest_type=None,
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test : Curr Stmt Bal',
                     balance=60,
                     min_balance=0,
                     max_balance=100,
                     account_type='curr stmt bal',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # non-matching min_balance (cc)

            ([Account.Account(
                name='test : Prev Stmt Bal',
                balance=0,
                min_balance=0,
                max_balance=110,
                account_type='prev stmt bal',
                billing_start_date_YYYYMMDD='20000101',
                interest_type=None,
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            ),
                 Account.Account(
                     name='test : Curr Stmt Bal',
                     balance=0,
                     min_balance=0,
                     max_balance=100,
                     account_type='curr stmt bal',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  # non-matching max_balance (cc)

            ([Account.Account(
                name='tloan : Principal Balance',
                balance=0,
                min_balance=0,
                max_balance=100,
                account_type='principal balance',
                billing_start_date_YYYYMMDD='20000101',
                interest_type='compound',
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            )
             ]
            , ValueError),  # pbal no interest

            ([Account.Account(
                     name='loan : Interest',
                     balance=60,
                     min_balance=0,
                     max_balance=1000,
                     account_type='interest',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ]
            , ValueError),  #interest no pbal

            ([Account.Account(
                     name='cc : Curr Stmt Bal',
                     balance=60,
                     min_balance=0,
                     max_balance=1000,
                     account_type='curr stmt bal',
                     billing_start_date_YYYYMMDD=None,
                     interest_type=None,
                     apr=None,
                     interest_cadence=None,
                     minimum_payment=None
                 )
             ], ValueError), #curr no prev

            ([Account.Account(
                name='cc : Prev Stmt Bal',
                balance=0,
                min_balance=0,
                max_balance=1000,
                account_type='prev stmt bal',
                billing_start_date_YYYYMMDD='20000101',
                interest_type=None,
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            )],ValueError), #prev no curr

            ([Account.Account(
                name='test loan : Principal Balance',
                balance=60,
                min_balance=0,
                max_balance=100,
                account_type='principal balance',
                billing_start_date_YYYYMMDD='20000101',
                interest_type='compound',
                apr=0.01,
                interest_cadence='monthly',
                minimum_payment=50
            )],ValueError), # pbal no int

            ([Account.Account(
                 name='test loan : Interest',
                 balance=60,
                 min_balance=0,
                 max_balance=100,
                 account_type='interest',
                 billing_start_date_YYYYMMDD=None,
                 interest_type=None,
                 apr=None,
                 interest_cadence=None,
                 minimum_payment=None
             )], ValueError), #int no pbal

         # [Account.Account(
         #     name,
         #     balance,
         #     min_balance,
         #     max_balance,
         #     account_type,
         #     billing_start_date_YYYYMMDD=None,
         #     interest_type=None,
         #     apr=None,
         #     interest_cadence=None,
         #     minimum_payment=None
         # )],

        ])
    def test_AccountSet_Constructor__invalid_inputs(self,accounts__list,expected_exception):

        with pytest.raises(expected_exception):
            AccountSet.AccountSet(accounts__list)

    @pytest.mark.parametrize(
        "accounts__list",
        [   ([]), #empty list as input
         ([Account.Account(
              name='test checking',
              balance=0,
              min_balance=0,
              max_balance=100,
              account_type='checking',
              billing_start_date_YYYYMMDD=None,
              interest_type=None,
              apr=None,
              interest_cadence=None,
              minimum_payment=None
          )]),

         # [Account.Account(
         #     name,
         #     balance,
         #     min_balance,
         #     max_balance,
         #     account_type,
         #     billing_start_date_YYYYMMDD=None,
         #     interest_type=None,
         #     apr=None,
         #     interest_cadence=None,
         #     minimum_payment=None
         # )],

        ])
    def test_AccountSet_Constructor__valid_inputs(self,accounts__list):

        AccountSet.AccountSet(accounts__list)

        # # check constructor with list of accounts
        # checking_acct = Account.Account(name="test checking",
        # balance = 0,
        # min_balance = 0,
        # max_balance = 0,
        # account_type = 'checking',print_debug_messages=False)
        # self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(AccountSet.AccountSet([checking_acct]))))
        #
        # prv_bal_acct = Account.Account(name='Credit: Prev Stmt Bal',
        # balance = 0,
        # min_balance = 0,
        # max_balance = 0,
        # account_type = 'prev stmt bal',
        # billing_start_date_YYYYMMDD = '20000101',
        # interest_type = 'compound',
        # apr = 0.05,
        # interest_cadence = 'monthly',
        # minimum_payment = 40,print_debug_messages=False)
        #
        # cur_bal_acct = Account.Account(name='Credit: Curr Stmt Bal',
        #                                balance=0,
        #                                min_balance=0,
        #                                max_balance=0,
        #                                account_type='curr stmt bal',
        #                                billing_start_date_YYYYMMDD=None,
        #                                interest_type=None,
        #                                apr=None,
        #                                interest_cadence=None,
        #                                minimum_payment=None,print_debug_messages=False)
        #
        # principal_balance_acct = Account.Account(name='Loan: Principal Balance',
        #                                balance=0,
        #                                min_balance=0,
        #                                max_balance=0,
        #                                account_type='principal balance',
        #                                billing_start_date_YYYYMMDD='20000101',
        #                                interest_type='simple',
        #                                apr=0.05,
        #                                interest_cadence='daily',
        #                                minimum_payment=40,print_debug_messages=False)
        #
        # interest_acct = Account.Account(name='Loan: Interest',
        #                                balance=0,
        #                                min_balance=0,
        #                                max_balance=0,
        #                                account_type='interest',
        #                                billing_start_date_YYYYMMDD=None,
        #                                interest_type=None,
        #                                apr=None,
        #                                interest_cadence=None,
        #                                minimum_payment=None,print_debug_messages=False)
        #
        #
        # #these should not throw exceptions
        # valid_accountset_loan = AccountSet.AccountSet([checking_acct,principal_balance_acct,interest_acct],print_debug_messages=False)
        # valid_accountset_cc = AccountSet.AccountSet([checking_acct, prv_bal_acct, cur_bal_acct],print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):
        #     AccountSet.AccountSet([checking_acct,interest_acct],print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):
        #     AccountSet.AccountSet(['',None],print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):
        #     AccountSet.AccountSet([checking_acct,principal_balance_acct],print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):
        #     AccountSet.AccountSet([checking_acct,cur_bal_acct],print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):
        #     AccountSet.AccountSet([checking_acct,prv_bal_acct],print_debug_messages=False)
        #
        # cur_bal_75_acct = Account.Account(name='Credit: Curr Stmt Bal',
        #                                balance=75,
        #                                min_balance=0,
        #                                max_balance=100,
        #                                account_type='curr stmt bal',
        #                                billing_start_date_YYYYMMDD=None,
        #                                interest_type=None,
        #                                apr=None,
        #                                interest_cadence=None,
        #                                minimum_payment=None, print_debug_messages=False)
        #
        # prv_bal_75_acct = Account.Account(name='Credit: Prev Stmt Bal',
        #                                balance=75,
        #                                min_balance=0,
        #                                max_balance=100,
        #                                account_type='prev stmt bal',
        #                                billing_start_date_YYYYMMDD='20000101',
        #                                interest_type='compound',
        #                                apr=0.05,
        #                                interest_cadence='monthly',
        #                                minimum_payment=40, print_debug_messages=False)

        #
        # with self.assertRaises(ValueError):  # mismatching max
        #     AccountSet.AccountSet([cur_bal_acct, prv_bal_75_acct], print_debug_messages=False)
        #
        # cur_bal_minus_75_acct = Account.Account(name='Credit: Curr Stmt Bal',
        #                                   balance=-75,
        #                                   min_balance=-100,
        #                                   max_balance=100,
        #                                   account_type='curr stmt bal',
        #                                   billing_start_date_YYYYMMDD=None,
        #                                   interest_type=None,
        #                                   apr=None,
        #                                   interest_cadence=None,
        #                                   minimum_payment=None, print_debug_messages=False)
        #
        # prv_bal_minus_75_acct = Account.Account(name='Credit: Prev Stmt Bal',
        #                                   balance=-75,
        #                                   min_balance=-100,
        #                                   max_balance=100,
        #                                   account_type='prev stmt bal',
        #                                   billing_start_date_YYYYMMDD='20000101',
        #                                   interest_type='compound',
        #                                   apr=0.05,
        #                                   interest_cadence='monthly',
        #                                   minimum_payment=40, print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):  # combinaed balance violates max
        #     AccountSet.AccountSet([cur_bal_minus_75_acct, prv_bal_minus_75_acct], print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):  # mismatching max
        #     AccountSet.AccountSet([cur_bal_acct, prv_bal_minus_75_acct], print_debug_messages=False)
        #
        # principal_balance_75_acct = Account.Account(name='Loan: Principal Balance',
        #                                          balance=75,
        #                                          min_balance=0,
        #                                          max_balance=100,
        #                                          account_type='principal balance',
        #                                          billing_start_date_YYYYMMDD='20000101',
        #                                          interest_type='simple',
        #                                          apr=0.05,
        #                                          interest_cadence='daily',
        #                                          minimum_payment=40, print_debug_messages=False)
        #
        # interest_75_acct = Account.Account(name='Loan: Interest',
        #                                 balance=75,
        #                                 min_balance=0,
        #                                 max_balance=100,
        #                                 account_type='interest',
        #                                 billing_start_date_YYYYMMDD=None,
        #                                 interest_type=None,
        #                                 apr=None,
        #                                 interest_cadence=None,
        #                                 minimum_payment=None, print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):  # combinaed balance violates max
        #     AccountSet.AccountSet([principal_balance_75_acct, interest_75_acct], print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):  # mismatching max
        #     AccountSet.AccountSet([principal_balance_acct, interest_75_acct], print_debug_messages=False)
        #
        # principal_balance_minus_75_acct = Account.Account(name='Loan: Principal Balance',
        #                                             balance=-75,
        #                                             min_balance=-100,
        #                                             max_balance=0,
        #                                             account_type='principal balance',
        #                                             billing_start_date_YYYYMMDD='20000101',
        #                                             interest_type='simple',
        #                                             apr=0.05,
        #                                             interest_cadence='daily',
        #                                             minimum_payment=40, print_debug_messages=False)
        #
        # interest_minus_75_acct = Account.Account(name='Loan: Interest',
        #                                    balance=-75,
        #                                    min_balance=-100,
        #                                    max_balance=0,
        #                                    account_type='interest',
        #                                    billing_start_date_YYYYMMDD=None,
        #                                    interest_type=None,
        #                                    apr=None,
        #                                    interest_cadence=None,
        #                                    minimum_payment=None, print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):  # combinaed balance violates max
        #     AccountSet.AccountSet([principal_balance_minus_75_acct, interest_minus_75_acct], print_debug_messages=False)
        #
        # with self.assertRaises(ValueError):  # mismatching max
        #     AccountSet.AccountSet([principal_balance_acct, interest_minus_75_acct], print_debug_messages=False)

    # def test_addAccounts(self):
    #
    #     #TODO have i checked that principal balance and interest add up?
    #     #i notice that the principal balance field could be eliminated
    #
    #     test_account_set = AccountSet.AccountSet([])
    #
    #     with self.assertRaises(ValueError):
    #         test_account_set.createAccount(name="test loan",
    #                                        balance=0,
    #                                        min_balance=0,
    #                                        max_balance=10000,
    #                                        account_type='loan',
    #                                        billing_start_date_YYYYMMDD='20220101',
    #                                        interest_type = 'simple',
    #                                        apr=0.03,
    #                                        interest_cadence='daily',
    #                                        minimum_payment=1,
    #                                        previous_statement_balance=None,
    #                                        principal_balance=900,
    #                                        interest_balance=100,
    #                                        print_debug_messages=False)
    #
    #     # create a non-loan and non-credit type account
    #     test_account_set.createAccount(name="test checking",
    #                                    balance=0,
    #                                    min_balance=0,
    #                                    max_balance=0,
    #                                    account_type='checking')
    #     self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))
    #
    #     # create a credit card type account
    #     test_account_set.createAccount(name="test credit",
    #                                    balance=0,
    #                                    min_balance=0,
    #                                    max_balance=0,
    #                                    account_type='credit',
    #                                    billing_start_date_YYYYMMDD='20220101',
    #                                    interest_type='compound',
    #                                    apr=0.05,
    #                                    interest_cadence='monthly',
    #                                    minimum_payment=0,
    #                                    previous_statement_balance=0,
    #                                    principal_balance=None,
    #                                    interest_balance=None, print_debug_messages=True
    #                                    )
    #     self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))
    #
    #     # create a loan type account
    #     test_account_set.createAccount(name="test loan",
    #                                    balance=1000,
    #                                    min_balance=0,
    #                                    max_balance=10000,
    #                                    account_type='loan',
    #                                    billing_start_date_YYYYMMDD='20220101',
    #                                    interest_type = 'simple',
    #                                    apr=0.03,
    #                                    interest_cadence='daily',
    #                                    minimum_payment=1,
    #                                    previous_statement_balance=None,
    #                                    principal_balance=900,
    #                                    interest_balance=100
    #                                    )
    #     self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))
    #
    #     with self.assertRaises(ValueError):
    #         test_account_set.createAccount(name="test loan",
    #                                        balance=1000,
    #                                        min_balance=0,
    #                                        max_balance=10000,
    #                                        account_type='loan',
    #                                        billing_start_date_YYYYMMDD='20220101',
    #                                        interest_type='simple',
    #                                        apr=0.03,
    #                                        interest_cadence='daily',
    #                                        minimum_payment=1,
    #                                        previous_statement_balance=None,
    #                                        principal_balance=None,
    #                                        interest_balance=100
    #                                        )
    #
    #     with self.assertRaises(ValueError):
    #         test_account_set.createAccount(name="test loan",
    #                                        balance=1000,
    #                                        min_balance=0,
    #                                        max_balance=10000,
    #                                        account_type='loan',
    #                                        billing_start_date_YYYYMMDD='20220101',
    #                                        interest_type='simple',
    #                                        apr=0.03,
    #                                        interest_cadence='daily',
    #                                        minimum_payment=1,
    #                                        previous_statement_balance=None,
    #                                        principal_balance=900,
    #                                        interest_balance=None
    #                                        )
    #
    #     with self.assertRaises(ValueError):
    #         test_account_set.createAccount(name="test credit",
    #                                        balance=0,
    #                                        min_balance=0,
    #                                        max_balance=0,
    #                                        account_type='credit',
    #                                        billing_start_date_YYYYMMDD='20220101',
    #                                        interest_type='compound',
    #                                        apr=0.05,
    #                                        interest_cadence='monthly',
    #                                        minimum_payment=0,
    #                                        previous_statement_balance=None,
    #                                        principal_balance=None,
    #                                        interest_balance=None
    #                                        )

    # def test_allocate_additional_loan_payments__invalid_inputs(self,account_set,amount,expected_exception):
    #     pass

    @pytest.mark.parametrize(
        "Account_From, Account_To, Amount,income_flag,expected_result_vector",
        [("test checking",None,0.0,False,[1000.0, 1000.0, 500.0, 900.0, 100.0]),  #txn for 0
         ("test checking",None,100.0,False,[900.0, 1000.0, 500.0, 900.0, 100.0]),  #withdraw from checking account
         (None,"test checking",100.0,True,[1100.0, 1000.0, 500.0, 900.0, 100.0]),  #deposit to checking account

         ("test credit", None, 100.0, False, [1000.0, 1100.0, 500.0, 900.0, 100.0]),  #pay using credit
         ("test checking", "test credit", 50.0, False, [950.0, 1000.0, 450.0, 900.0, 100.0]),  #credit payment, less than prev stmt bal and curr stmt bal > 0
         ("test checking", "test credit", 501.0, False, [499.0, 999.0, 0.0, 900.0, 100.0]),  #credit payment, less than total balance, more than prev stmt balance, curr stmt bal != 0

         ("test checking", "test loan", 50.0, False, [950.0, 1000.0, 500.0, 900.0, 50.0]),  #loan payment, less than interest
         ("test checking", "test loan", 150.0, False, [850.0, 1000.0, 500.0, 850.0, 0.0]),  #loan payment, more than interest

         ("test checking", "ALL_LOANS", 150.0, False, [850.0, 1000.0, 500.0, 850.0, 0.0]),  #loan payment, more than interest
         ])
    def test_execute_transaction_valid_inputs(self,Account_From, Account_To, Amount,income_flag,expected_result_vector):
        test_account_set = AccountSet.AccountSet([])
        test_account_set.createAccount(name="test checking",
                                       balance=1000.0,
                                       min_balance=0.0,
                                       max_balance=float('inf'),
                                       account_type='checking',
                                       billing_start_date_YYYYMMDD=None,
                                       interest_type=None,
                                       apr=None,
                                       interest_cadence=None,
                                       minimum_payment=None,
                                       previous_statement_balance=None,
                                       principal_balance=None,
                                       interest_balance=None,
                                       print_debug_messages=False)

        test_account_set.createAccount(name="test credit",
                                       balance=1500.0,
                                       min_balance=0.0,
                                       max_balance=20000.0,
                                       account_type='credit',
                                       billing_start_date_YYYYMMDD='20000107',
                                       interest_type=None,
                                       apr=0.2479,
                                       interest_cadence='monthly',
                                       minimum_payment=20.0,
                                       previous_statement_balance=500.0,
                                       current_statement_balance=1000.0,
                                       principal_balance=None,
                                       interest_balance=None,
                                       print_debug_messages=False)

        test_account_set.createAccount(name="test loan",
                                       balance=1000.0,
                                       min_balance=0,
                                       max_balance=26000.0,
                                       account_type='loan',
                                       billing_start_date_YYYYMMDD='20230303',
                                       interest_type='simple',
                                       apr=0.067,
                                       interest_cadence='daily',
                                       minimum_payment='223.19',
                                       previous_statement_balance=None,
                                       principal_balance=900.0,
                                       interest_balance=100.0,
                                       print_debug_messages=False)

        test_account_set.executeTransaction(Account_From=Account_From, Account_To=Account_To, Amount=Amount, income_flag=income_flag)
        result_vector = list(test_account_set.getAccounts().iloc[:,1])
        assert result_vector == expected_result_vector

    # @pytest.mark.parametrize(
    #     "Account_From, Account_To, Amount,income_flag,expected_exception",
    #     [(),
    #      ()
    #      ])
    # def test_execute_transaction_invalid_inputs(self,Account_From, Account_To, Amount,income_flag,expected_exception):
    #     test_account_set = AccountSet.AccountSet([])
    #     test_account_set.createAccount(name="test checking",
    #                                    balance=1000.0,
    #                                    min_balance=0.0,
    #                                    max_balance=float('inf'),
    #                                    account_type='checking',
    #                                    billing_start_date_YYYYMMDD=None,
    #                                    interest_type=None,
    #                                    apr=None,
    #                                    interest_cadence=None,
    #                                    minimum_payment=None,
    #                                    previous_statement_balance=None,
    #                                    principal_balance=None,
    #                                    interest_balance=None,
    #                                    print_debug_messages=False)
    #
    #     test_account_set.createAccount(name="test credit",
    #                                    balance=1000.0,
    #                                    min_balance=0.0,
    #                                    max_balance=20000.0,
    #                                    account_type='credit',
    #                                    billing_start_date_YYYYMMDD='20000107',
    #                                    interest_type='compound',
    #                                    apr=0.2479,
    #                                    interest_cadence='monthly',
    #                                    minimum_payment=20.0,
    #                                    previous_statement_balance=500.0,
    #                                    principal_balance=None,
    #                                    interest_balance=None,
    #                                    print_debug_messages=False)
    #
    #     test_account_set.createAccount(name="test loan",
    #                                    balance=1000.0,
    #                                    min_balance=0,
    #                                    max_balance=26000.0,
    #                                    account_type='loan',
    #                                    billing_start_date_YYYYMMDD='20230303',
    #                                    interest_type='simple',
    #                                    apr=0.067,
    #                                    interest_cadence='daily',
    #                                    minimum_payment='223.19',
    #                                    previous_statement_balance=None,
    #                                    principal_balance=900.0,
    #                                    interest_balance=100.0,
    #                                    print_debug_messages=False)
    #
    #     with pytest.raises(expected_exception):
    #         test_account_set.executeTransaction(Account_From=Account_From, Account_To=Account_To, Amount=Amount,income_flag=income_flag)



    @pytest.mark.parametrize(
        "name,balance,min_balance,max_balance,account_type,billing_start_date_YYYYMMDD,interest_type,apr,interest_cadence,minimum_payment,previous_statement_balance,principal_balance,interest_balance,expected_exception",
        [('test loan',
          100,
          0,
          100,
          'loan',
          '20000101',
          'compoung',
          0.1,
          'monthly',
          50,
          None,
          None,
          100
        ,ValueError),  #miss pbal for type loan

         ('test loan',
          100,
          0,
          100,
          'loan',
          '20000101',
          'compoung',
          0.1,
          'monthly',
          50,
          None,
          100,
          None
          , ValueError),  # missing interest for type loan

         ('test credit',
          100,
          0,
          100,
          'credit',
          '20000101',
          'compound',
          0.1,
          'monthly',
          50,
          None,
          None,
          None
          , ValueError),  # missing prev stmt bal for type credit

         ('test loan',
          100,
          0,
          100,
          'loan',
          '20000101',
          'compoung',
          0.1,
          'monthly',
          50,
          None,
          100,
          100
          , ValueError),  # pbal + interest != balance

         # (name,
         #  balance,
         #  min_balance,
         #  max_balance,
         #  account_type,
         #  billing_start_date_YYYYMMDD,
         #  interest_type,
         #  apr,
         #  interest_cadence,
         #  minimum_payment,
         #  previous_statement_balance,
         #  principal_balance,
         #  interest_balance
         #  , ValueError),  # missing interest for type loan

         ])
    def test_createAccount__invalid_inputs(self,name,
          balance,
          min_balance,
          max_balance,
          account_type,
          billing_start_date_YYYYMMDD,
          interest_type,
          apr,
          interest_cadence,
          minimum_payment,
          previous_statement_balance,
          principal_balance,
          interest_balance,expected_exception):

        with pytest.raises(expected_exception):
            A = AccountSet.AccountSet([])
            A.createAccount(name,
              balance,
              min_balance,
              max_balance,
              account_type,
              billing_start_date_YYYYMMDD,
              interest_type,
              apr,
              interest_cadence,
              minimum_payment,
              previous_statement_balance,
              principal_balance,
              interest_balance)



    def test_getAccounts(self):
        test_account_set = AccountSet.AccountSet([])

        test_account_set.createAccount(name="test checking",
                                       balance = 0,
                                       min_balance = 0,
                                       max_balance = 0,
                                       account_type = 'checking')
        test_df = test_account_set.getAccounts()
        assert test_df is not None

    def test_str(self):
        test_str_account_set = AccountSet.AccountSet([])

        # create a non-loan and non-credit type account
        test_str_account_set.createAccount(name="test checking",
                                       balance=0,
                                       min_balance=0,
                                       max_balance=0,
                                       account_type='checking')

        # create a credit card type account
        test_str_account_set.createAccount(name="test credit",
                                       balance=0,
                                       min_balance=0,
                                       max_balance=0,
                                       account_type='credit',
                                       billing_start_date_YYYYMMDD='20220101',
                                       interest_type=None,
                                       apr=0.05,
                                       interest_cadence='monthly',
                                       minimum_payment=0,
                                       previous_statement_balance=0,
                                       current_statement_balance=0,
                                       principal_balance=None,
                                       interest_balance=None
                                       )

        # create a loan type account
        test_str_account_set.createAccount(name="test loan",
                                       balance=1000,
                                       min_balance=0,
                                       max_balance=10000,
                                       account_type='loan',
                                       billing_start_date_YYYYMMDD='20220101',
                                       interest_type='simple',
                                       apr=0.03,
                                       interest_cadence='daily',
                                       minimum_payment=1,
                                       previous_statement_balance=None,
                                       principal_balance=900,
                                       interest_balance=100
                                       )

        str(test_str_account_set)
    #
    # def test_to_excel(self):
    #
    #     A1 = AccountSet.AccountSet([])
    #     A2 = AccountSet.AccountSet(checking())
    #     A3 = AccountSet.AccountSet(checking() + cc(499,501,0.05,'20000102'))
    #     A4 = AccountSet.AccountSet(checking() + cc(499,501,0.05,'20000102') + compound_loan_A_no_interest())
    #
    #
    #     with tempfile.NamedTemporaryFile() as tmp:
    #         A1.to_excel(tmp)
    #         T1 = pd.read_excel(tmp)
    #         T1_s = T1.to_string().replace('\n',' ')
    #
    #         #it is absurd that I even have to do this, but Mac makes it so unnecessarily difficult to disable line wrap in any program at all
    #         T1_s__0_100 = T1_s[0:100]
    #         T1_s__100_200 = T1_s[100: 200]
    #
    #         assert T1_s__0_100 == 'Empty DataFrame Columns: [Unnamed: 0, Name, Balance, Min_Balance, Max_Balance, Account_Type, Billing'
    #         assert T1_s__100_200 == '_Start_Dt, Interest_Type, APR, Interest_Cadence, Minimum_Payment] Index: []'
    #
    #     with tempfile.NamedTemporaryFile() as tmp:
    #         A2.to_excel(tmp)
    #         T2 = pd.read_excel(tmp)
    #         T2_s = T2.to_string().replace('\n', ' ').replace('\t',' ')
    #
    #         T2_s__0_100 = T2_s[0:100]
    #         T2_s__100_200 = T2_s[100: 200]
    #
    #         assert T2_s__0_100 ==   '   Unnamed: 0           Name  Balance  Min_Balance  Max_Balance Account_Type  Billing_Start_Dt  Inte'
    #         assert T2_s__100_200 == 'rest_Type  APR  Interest_Cadence  Minimum_Payment 0           0  test checking    10000            0'
    #
    #     with tempfile.NamedTemporaryFile() as tmp:
    #         A3.to_excel(tmp)
    #         T3 = pd.read_excel(tmp)
    #         T3_s = T3.to_string().replace('\n', ' ').replace('\t', ' ')
    #
    #         T3_s__0_100 = T3_s[0:100]
    #         T3_s__100_200 = T3_s[100: 200]
    #         T3_s__200_300 = T3_s[200: 300]
    #         T3_s__300_400 = T3_s[300: 400]
    #         T3_s__400_500 = T3_s[400: 500]
    #         T3_s__500_600 = T3_s[500: 600]
    #
    #         assert T3_s__0_100   == '   Unnamed: 0                    Name  Balance  Min_Balance  Max_Balance   Account_Type  Billing_Sta'
    #         assert T3_s__100_200 == 'rt_Dt Interest_Type   APR Interest_Cadence  Minimum_Payment 0           0           test checking   '
    #         assert T3_s__200_300 == ' 10000            0        10000       checking               NaN           NaN   NaN              N'
    #         assert T3_s__300_400 == 'aN              NaN 1           1  test cc: Curr Stmt Bal      499            0        20000  curr s'
    #         assert T3_s__400_500 == 'tmt bal               NaN           NaN   NaN              NaN              NaN 2           2  test '
    #         assert T3_s__500_600 == 'cc: Prev Stmt Bal      501            0        20000  prev stmt bal        20000102.0      compound ' #note that the float dtype of date is valid here bc we just read it fro mexcel w none of the AccountSet context
    #
    #     with tempfile.NamedTemporaryFile() as tmp:
    #         A4.to_excel(tmp)
    #         T4 = pd.read_excel(tmp)
    #         T4_s = T4.to_string().replace('\n', ' ').replace('\t', ' ')
    #
    #         T4_s__0_100 = T4_s[0:100]
    #         T4_s__100_200 = T4_s[100: 200]
    #         T4_s__200_300 = T4_s[200: 300]
    #         T4_s__300_400 = T4_s[300: 400]
    #         T4_s__400_500 = T4_s[400: 500]
    #         T4_s__500_600 = T4_s[500: 600]
    #
    #         assert T4_s__0_100 ==   '   Unnamed: 0                            Name  Balance  Min_Balance  Max_Balance       Account_Type '
    #         assert T4_s__100_200 == ' Billing_Start_Dt Interest_Type   APR Interest_Cadence  Minimum_Payment 0           0               '
    #         assert T4_s__200_300 == '    test checking    10000            0        10000           checking               NaN           '
    #         assert T4_s__300_400 == 'NaN   NaN              NaN              NaN 1           1          test cc: Curr Stmt Bal      499  '
    #         assert T4_s__400_500 == '          0        20000      curr stmt bal               NaN           NaN   NaN              NaN  '
    #         assert T4_s__500_600 == '            NaN 2           2          test cc: Prev Stmt Bal      501            0        20000    '
    #
    # def test_from_excel(self):
    #     A1 = AccountSet.AccountSet([])
    #     A2 = AccountSet.AccountSet(checking())
    #     A3 = AccountSet.AccountSet(checking() + cc(499,501,0.05,'20000102'))
    #     A4 = AccountSet.AccountSet(checking() + cc(499,501,0.05,'20000102') + compound_loan_A_no_interest())
    #
    #     TA = AccountSet.AccountSet([])
    #
    #     with tempfile.TemporaryDirectory() as tmpdirname:
    #
    #         A1.to_excel(tmpdirname+'/A1.xlsx')
    #         A2.to_excel(tmpdirname + '/A2.xlsx')
    #         A3.to_excel(tmpdirname + '/A3.xlsx')
    #         A4.to_excel(tmpdirname + '/A4.xlsx')
    #
    #         TA.from_excel(tmpdirname + '/A1.xlsx')
    #         # print('TA.getAccounts().to_string():')
    #         # print(TA.getAccounts().to_string())
    #         # print('----')
    #         # print('A1.getAccounts().to_string():')
    #         # print(A1.getAccounts().to_string())
    #         assert TA.getAccounts().to_string() == A1.getAccounts().to_string()
    #
    #         TA.from_excel(tmpdirname + '/A2.xlsx')
    #         # print('TA.getAccounts().to_string():')
    #         # print(TA.getAccounts().to_string())
    #         # print('----')
    #         # print('A2.getAccounts().to_string():')
    #         # print(A2.getAccounts().to_string())
    #         assert TA.getAccounts().to_string() == A2.getAccounts().to_string()
    #
    #         TA.from_excel(tmpdirname + '/A3.xlsx')
    #         # print('TA.getAccounts().to_string():')
    #         # print(TA.getAccounts().to_string())
    #         # print('----')
    #         # print('A3.getAccounts().to_string():')
    #         # print(A3.getAccounts().to_string())
    #         assert TA.getAccounts().to_string() == A3.getAccounts().to_string()
    #
    #         TA.from_excel(tmpdirname + '/A4.xlsx')
    #         # print('TA.getAccounts().to_string():')
    #         # print(TA.getAccounts().to_string())
    #         # print('----')
    #         # print('A4.getAccounts().to_string():')
    #         # print(A4.getAccounts().to_string())
    #         assert TA.getAccounts().to_string() == A4.getAccounts().to_string()

#tests to implement
#from excel, curr stmt bal is second row
#from excel, principal balance is second row
#pay loan, amount was greater than available balance (and less than loan cost)


#functionality?
#loan allocation being broken out in memo