import unittest
import Account

class TestAccountMethods(unittest.TestCase):

    def test_Account_Constructor(self):
        self.assertEqual('<class \'Account.Account\'>',str( type(
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking'
            )
        ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want
        #Account.Account(name='Test Account')

        # check that the right exceptions are raised
        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance='X',
                            min_balance=0,
                            max_balance=0,
                            account_type='checking',print_debug_messages=False)


        # TODO implement more error checking here

    def test_str(self):
        self.assertIsNotNone(str(Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking')))

    def test_repr(self):
        self.assertIsNotNone(repr(Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking')))


