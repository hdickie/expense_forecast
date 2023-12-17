import unittest
import Account
import doctest
from nose2.tools import params
import pandas as pd

class TestAccountMethods(unittest.TestCase):

    def test_Account_doctests(self):
        doctest.testmod(Account)

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
        with self.assertRaises(TypeError):
            Account.Account(name='test account',
                            balance='X',
                            min_balance=0,
                            max_balance=0,
                            account_type='checking',print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='credit prev stmt bal: test account min payment value error',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            apr=0,
                            billing_start_date_YYYYMMDD='20000101',
                            account_type='prev stmt bal',
                            interest_cadence='monthly',
                            minimum_payment='X',
                            print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='account name missing colon character',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            apr=0,
                            billing_start_date_YYYYMMDD='20000101',
                            account_type='prev stmt bal',
                            interest_cadence='monthly',
                            minimum_payment=0,
                            print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='shmecking', print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account type None',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type=None, print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account type credit',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='credit', print_debug_messages=False)

        with self.assertRaises(TypeError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance='not a float',
                            max_balance=0,
                            account_type='checking', print_debug_messages=False)

        with self.assertRaises(TypeError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance='not a float',
                            account_type='checking', print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=1,
                            max_balance=-1,
                            account_type='checking', print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking',
                            apr=0.05,
                            print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking',
                            billing_start_date_YYYYMMDD='20000101',
                            print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking',
                            interest_type='non null value',
                            print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking',
                            interest_cadence='non null value',
                            print_debug_messages=False)

        with self.assertRaises(TypeError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='savings',
                            billing_start_date_YYYYMMDD='not a date string',
                            print_debug_messages=False)

        with self.assertRaises(ValueError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='curr stmt bal',
                            minimum_payment=5,
                            print_debug_messages=False)

        with self.assertRaises(TypeError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='prev stmt bal',
                            minimum_payment='not a float',
                            raise_exceptionse=False) #just for debugging this test

        with self.assertRaises(TypeError):
            Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='savings',
                            billing_start_date_YYYYMMDD='not a date string',
                            print_debug_messages=False)


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

    def test_toJSON(self):
        test_account = Account.Account(name='test account',
                            balance=0,
                            min_balance=0,
                            max_balance=0,
                            account_type='checking')
        test_account_JSON = test_account.toJSON()
        test_expectation = """{\n"Name":"test account",\n"Balance":"0.0",\n"Min_Balance":"0.0",\n"Max_Balance":"0.0",\n"Account_Type":"checking",\n"Billing_Start_Date":"None",\n"Interest_Type":"None",\n"APR":"None",\n"Interest_Cadence":"None",\n"Minimum_Payment":"None"\n}"""
        assert test_account_JSON == test_expectation

