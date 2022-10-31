import unittest
import Account

class TestAccountMethods(unittest.TestCase):

    def test_Account_Constructor(self):
        self.assertEqual('<class \'Account.Account\'>',str( type( Account.Account() ) ) )
