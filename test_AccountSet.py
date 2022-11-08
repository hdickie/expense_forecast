import unittest
import Account, AccountSet

class TestAccountSetMethods(unittest.TestCase):

    def test_AccountSet_Constructor(self):

        test_account_set = AccountSet.AccountSet()
        self.assertEqual('<class \'AccountSet.AccountSet\'>',str( type( test_account_set ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want

        # check constructor with list of accounts
        test_acct = Account.Account()
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(AccountSet.AccountSet([test_acct]))))

        #create a loan type account
        test_account_set.addAccount(account_type = 'loan')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))

        #create a credit type account
        test_account_set.addAccount(account_type='credit')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))

        #create a non-loan and non-credit type account
        test_account_set.addAccount(account_type='checking')
        self.assertEqual('<class \'AccountSet.AccountSet\'>', str(type(test_account_set)))

        #todo should we throw an exception when a non-standard account type is created?

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