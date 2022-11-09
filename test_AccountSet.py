import unittest
import Account, AccountSet

class TestAccountSetMethods(unittest.TestCase):

    def test_AccountSet_Constructor(self):

        # check constructor with list of accounts
        test_acct = Account.Account(name="test checking",
        balance = 0,
        min_balance = 0,
        max_balance = 0,
        account_type = 'checking')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(AccountSet.AccountSet([test_acct]))))

    def test_addAccount(self):

        test_account_set = AccountSet.AccountSet([])

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