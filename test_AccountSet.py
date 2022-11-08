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

        test_account_set = AccountSet.AccountSet()

        # create a loan type account
        test_account_set.addAccount(account_type='loan')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))

        # create a credit type account
        test_account_set.addAccount(account_type='credit')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))

        # create a non-loan and non-credit type account
        test_account_set.addAccount(account_type='checking')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))


    def test_getAccounts(self):
        test_account_set = AccountSet.AccountSet()
        test_df = test_account_set.getAccounts()
        self.assertIsNotNone(test_df)

        test_account_set.addAccount(account_type='credit')
        test_df = test_account_set.getAccounts()
        self.assertIsNotNone(test_df)

    def test_str(self):
        test_account_set = AccountSet.AccountSet()
        account_str = str(test_account_set)
        self.assertIsNotNone(account_str)

        test_account_set.addAccount()
        account_str = str(test_account_set)
        self.assertIsNotNone(account_str)

    def test_repr(self):
        self.assertIsNotNone(repr(AccountSet.AccountSet()))