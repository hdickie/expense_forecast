import unittest
import Account

class TestAccountMethods(unittest.TestCase):

    def test_Account_Constructor(self):
        self.assertEqual('<class \'Account.Account\'>',str( type( Account.Account() ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want
        #Account.Account(name='Test Account')

        # check that the right exceptions are raised
        with self.assertRaises(ValueError):
            Account.Account(balance='X')

        with self.assertRaises(ValueError):
            Account.Account(interest_cadence='X')

        with self.assertRaises(ValueError):
            Account.Account(interest_type='X')


        # TODO implement more error checking here

    def test_str(self):
        self.assertIsNotNone(str(Account.Account()))

    def test_repr(self):
        self.assertIsNotNone(repr(Account.Account()))


