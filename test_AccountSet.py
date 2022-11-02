import unittest
import Account, AccountSet

class TestAccountSetMethods(unittest.TestCase):

    def test_AccountSet_Constructor(self):

        #TODO change this to use isinstance
        self.assertEqual('<class \'Account.AccountSet\'>',str( type( Account.Account() ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want


        pass
