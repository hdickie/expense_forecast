import logging

import pytest
import pandas as pd
import tempfile
import Account, AccountSet, doctest, copy
import datetime
from log_methods import log_in_color


def compound_loan_A():
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test loan A",
        balance=1100,
        min_balance=0,
        max_balance=1100,
        account_type="loan",
        billing_start_date="20240101",
        interest_type="compound",
        apr=0.1,
        interest_cadence="monthly",
        minimum_payment=50,
        billing_cycle_payment_balance=0,
        principal_balance=1000,
        interest_balance=100,
    )
    return A.accounts


def compound_loan_A_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test loan A",
        balance=1000,
        min_balance=0,
        max_balance=1100,
        account_type="loan",
        billing_start_date="20240101",
        interest_type="compound",
        apr=0.1,
        interest_cadence="monthly",
        minimum_payment=50,
        billing_cycle_payment_balance=0,
        principal_balance=1000,
        interest_balance=0,
    )
    return A.accounts


def compound_loan_B():
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test loan B",
        balance=1600,
        min_balance=0,
        max_balance=1600,
        account_type="loan",
        billing_start_date="20240101",
        interest_type="compound",
        apr=0.01,
        interest_cadence="monthly",
        minimum_payment=50,
        billing_cycle_payment_balance=0,
        principal_balance=1500,
        interest_balance=100,
    )
    return A.accounts


def compound_loan_B_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test loan B",
        balance=1500,
        min_balance=0,
        max_balance=1600,
        account_type="loan",
        billing_start_date="20240101",
        interest_type="compound",
        apr=0.01,
        interest_cadence="monthly",
        minimum_payment=50,
        billing_cycle_payment_balance=0,
        principal_balance=1500,
        interest_balance=0,
    )
    return A.accounts


def compound_loan_C():
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test loan C",
        balance=2600,
        min_balance=0,
        max_balance=2600,
        account_type="loan",
        billing_start_date="20240101",
        interest_type="compound",
        apr=0.05,
        interest_cadence="monthly",
        minimum_payment=50,
        billing_cycle_payment_balance=0,
        principal_balance=2500,
        interest_balance=100,
    )
    return A.accounts


def compound_loan_C_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test loan C",
        balance=2500,
        min_balance=0,
        max_balance=2600,
        account_type="loan",
        billing_start_date="20240101",
        interest_type="compound",
        apr=0.05,
        interest_cadence="monthly",
        minimum_payment=50,
        billing_cycle_payment_balance=0,
        principal_balance=2500,
        interest_balance=0,
    )
    return A.accounts


def checking():
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test checking",
        balance=10000,
        min_balance=0,
        max_balance=10000,
        account_type="checking",
    )
    return A.accounts


def cc(curr_bal, prev_bal, apr, bsd):
    A = AccountSet.AccountSet([])
    A.createAccount(
        "test cc",
        curr_bal,
        0,
        20000,
        "credit",
        bsd,
        "compound",
        apr,
        "monthly",
        40,
        prev_bal,
    )
    return A.accounts


def one_loan__p_1000__i_100__apr_01():
    return AccountSet.AccountSet(checking() + compound_loan_A())


def two_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001():
    return AccountSet.AccountSet(checking() + compound_loan_A() + compound_loan_B())


def three_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001___p_2500__i_100__apr_005():
    return AccountSet.AccountSet(
        checking() + compound_loan_A() + compound_loan_B() + compound_loan_C()
    )


# def one_loan__p_1000__i_000__apr_01():
#     return AccountSet.AccountSet(checking()+compound_loan_A_no_interest())
#
# def two_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001():
#     return AccountSet.AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest())


# todo should these be fixtures?
def three_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001___p_2500__i_000__apr_005():
    return AccountSet.AccountSet(
        checking()
        + compound_loan_A_no_interest()
        + compound_loan_B_no_interest()
        + compound_loan_C_no_interest()
    )


class TestAccountSet:

    @pytest.mark.unit
    @pytest.mark.skip(reason="do I still need this?")
    def test_AccountSet_doctests(self):
        # doctest.testmod(doctest_AccountSet,name="doctest_AccountSet")
        # doctest.DocTestSuite(module='doctest_AccountSet')
        # doctest.testfile('doctest_AccountSet.py')
        # doctest.run_docstring_examples('doctest_AccountSet.py',globs={})
        doctest.testmod(AccountSet)

    #

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "accounts__list,expected_exception",
    #     [
    #         (
    #             [
    #                 Account.Account(
    #                     name="test combined total violates maximum : Principal Balance",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test combined total violates maximum : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test combined total violates maximum : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates max (loan)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test cc : Prev Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test cc : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test cc : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates max (cc)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test cc : Prev Stmt Bal",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test cc : Curr Stmt Bal",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test cc : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates min (cc)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test : Principal Balance",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test : Interest",
    #                     balance=-100,
    #                     min_balance=-100,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # combined balance violates min (loan)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test combined total violates maximum : Principal Balance",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test combined total violates maximum : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test combined total violates maximum : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching max_balance (loan)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test combined total violates maximum : Prev Stm Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test combined total violates maximum : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=60,
    #                     max_balance=1000,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test combined total violates maximum : Credit Billing Cycle Payment Bal",
    #                     balance=60,
    #                     min_balance=60,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching min_balance (cc)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test : Principal Balance",
    #                     balance=10,
    #                     min_balance=10,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching min_balance (loan)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test : Prev Stmt Bal",
    #                     balance=10,
    #                     min_balance=10,
    #                     max_balance=100,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching min_balance (cc)
    #         (
    #             [
    #                 Account.Account(
    #                     name="test : Prev Stmt Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=110,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 ),
    #                 Account.Account(
    #                     name="test : Curr Stmt Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="test : Credit Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="credit billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # non-matching max_balance (cc)
    #         (
    #             [
    #                 Account.Account(
    #                     name="loan : Principal Balance",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # pbal no interest
    #         (
    #             [
    #                 Account.Account(
    #                     name="loan : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #                 Account.Account(
    #                     name="loan : Loan Billing Cycle Payment Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="loan billing cycle payment bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 ),
    #             ],
    #             ValueError,
    #         ),  # interest no pbal
    #         (
    #             [
    #                 Account.Account(
    #                     name="cc : Curr Stmt Bal",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit curr stmt bal",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # curr no prev
    #         (
    #             [
    #                 Account.Account(
    #                     name="cc : Prev Stmt Bal",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=1000,
    #                     account_type="credit prev stmt bal",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type=None,
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # prev no curr
    #         (
    #             [
    #                 Account.Account(
    #                     name="test loan : Principal Balance",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="principal balance",
    #                     billing_start_date=datetime.datetime.strptime("20000101","%Y%m%d"),
    #                     interest_type="compound",
    #                     apr=0.01,
    #                     interest_cadence="monthly",
    #                     minimum_payment=50,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # pbal no int
    #         (
    #             [
    #                 Account.Account(
    #                     name="test loan : Interest",
    #                     balance=60,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="interest",
    #                     billing_start_date=None,
    #                     interest_type=None,
    #                     apr=None,
    #                     interest_cadence=None,
    #                     minimum_payment=None,
    #                 )
    #             ],
    #             ValueError,
    #         ),  # int no pbal
    #         # [Account.Account(
    #         #     name,
    #         #     balance,
    #         #     min_balance,
    #         #     max_balance,
    #         #     account_type,
    #         #     billing_start_date=None,
    #         #     interest_type=None,
    #         #     apr=None,
    #         #     interest_cadence=None,
    #         #     minimum_payment=None
    #         # )],
    #     ],
    # )
    # def test_AccountSet_Constructor__invalid_inputs(
    #     self, accounts__list, expected_exception
    # ):
    #
    #     with pytest.raises(expected_exception):
    #         AccountSet.AccountSet(accounts__list)

    # @pytest.mark.parametrize(
    #     "accounts__list",
    #     [
    #         ([]),  # empty list as input
    #         (
    #             [
    #                 Account.Account(
    #                     name="test checking",
    #                     balance=0,
    #                     min_balance=0,
    #                     max_balance=100,
    #                     account_type="checking",
    #                     primary_checking_ind=True
    #                 )
    #             ]
    #         ),
    #     ],
    # )
    # def test_AccountSet_Constructor__valid_inputs(self, accounts__list):
    #
    #     AccountSet.AccountSet(accounts__list)

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "Account_From, Account_To, Amount,income_flag,expected_result_vector",
    #     [
    #         (
    #             "test checking",
    #             None,
    #             0.0,
    #             False,
    #             [1000.0, 1000.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # txn for 0
    #         (
    #             "test checking",
    #             None,
    #             100.0,
    #             False,
    #             [900.0, 1000.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # withdraw from checking account
    #         (
    #             None,
    #             "test checking",
    #             100.0,
    #             True,
    #             [1100.0, 1000.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # deposit to checking account
    #         (
    #             "test credit",
    #             None,
    #             100.0,
    #             False,
    #             [1000.0, 1100.0, 500.0, 0, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # pay using credit
    #         (
    #             "test checking",
    #             "test credit",
    #             50.0,
    #             False,
    #             [950.0, 1000.0, 450.0, 50, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # credit payment, less than credit prev stmt bal and credit curr stmt bal > 0
    #         (
    #             "test checking",
    #             "test credit",
    #             501.0,
    #             False,
    #             [499.0, 999.0, 0.0, 501, 500, 900.0, 100.0, 0, 900.0],
    #         ),  # credit payment, less than total balance, more than credit prev stmt balance, credit curr stmt bal != 0
    #         (
    #             "test checking",
    #             "test loan",
    #             50.0,
    #             False,
    #             [950.0, 1000.0, 500.0, 0, 500, 900.0, 50.0, 50, 900.0],
    #         ),  # loan payment, less than interest
    #         (
    #             "test checking",
    #             "test loan",
    #             150.0,
    #             False,
    #             [850.0, 1000.0, 500.0, 0, 500, 850.0, 0.0, 150, 900.0],
    #         ),  # loan payment, more than interest
    #         (
    #             "test checking",
    #             "ALL_LOANS",
    #             150.0,
    #             False,
    #             [850.0, 1000.0, 500.0, 0, 500, 850.0, 0.0, 150, 900.0],
    #         ),  # loan payment, more than interest
    #     ],
    # )
    # def test_execute_transaction_valid_inputs(
    #     self, Account_From, Account_To, Amount, income_flag, expected_result_vector
    # ):
    #     test_account_set = AccountSet.AccountSet([])
    #     test_account_set.createAccount(
    #         name="test checking",
    #         balance=1000.0,
    #         min_balance=0.0,
    #         max_balance=float("inf"),
    #         account_type="checking",
    #         billing_start_date=None,
    #         interest_type=None,
    #         apr=None,
    #         interest_cadence=None,
    #         minimum_payment=None,
    #         previous_statement_balance=None,
    #         principal_balance=None,
    #         interest_balance=None,
    #         billing_cycle_payment_balance=0,
    #         primary_checking_ind=True,
    #         print_debug_messages=False,
    #     )
    #
    #     test_account_set.createAccount(
    #         name="test credit",
    #         balance=1500.0,
    #         min_balance=0.0,
    #         max_balance=20000.0,
    #         account_type="credit",
    #         billing_start_date="20000107",
    #         interest_type=None,
    #         apr=0.2479,
    #         interest_cadence="monthly",
    #         minimum_payment=20.0,
    #         previous_statement_balance=500.0,
    #         current_statement_balance=1000.0,
    #         principal_balance=None,
    #         interest_balance=None,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=500.0,
    #         print_debug_messages=False,
    #     )
    #
    #     test_account_set.createAccount(
    #         name="test loan",
    #         balance=1000.0,
    #         min_balance=0,
    #         max_balance=26000.0,
    #         account_type="loan",
    #         billing_start_date="20230303",
    #         interest_type="simple",
    #         apr=0.067,
    #         interest_cadence="daily",
    #         minimum_payment="223.19",
    #         previous_statement_balance=None,
    #         principal_balance=900.0,
    #         interest_balance=100.0,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=900,
    #         print_debug_messages=False,
    #     )
    #
    #     test_account_set.executeTransaction(
    #         Account_From=Account_From,
    #         Account_To=Account_To,
    #         Amount=Amount,
    #         income_flag=income_flag,
    #     )
    #     result_vector = list(test_account_set.getAccounts().iloc[:, 1])
    #     assert result_vector == expected_result_vector

    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "name,balance,min_balance,max_balance,account_type,billing_start_date,interest_type,apr,interest_cadence,minimum_payment,previous_statement_balance,principal_balance,interest_balance,expected_exception",
    #     [
    #         (
    #             "test loan",
    #             100,
    #             0,
    #             100,
    #             "loan",
    #             "20000101",
    #             "compoung",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             None,
    #             100,
    #             ValueError,
    #         ),  # miss pbal for type loan
    #         (
    #             "test loan",
    #             100,
    #             0,
    #             100,
    #             "loan",
    #             "20000101",
    #             "compoung",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             100,
    #             None,
    #             ValueError,
    #         ),  # missing interest for type loan
    #         (
    #             "test credit",
    #             100,
    #             0,
    #             100,
    #             "credit",
    #             "20000101",
    #             "compound",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             None,
    #             None,
    #             ValueError,
    #         ),  # missing credit prev stmt bal for type credit
    #         (
    #             "test loan",
    #             100,
    #             0,
    #             100,
    #             "loan",
    #             "20000101",
    #             "compoung",
    #             0.1,
    #             "monthly",
    #             50,
    #             None,
    #             100,
    #             100,
    #             ValueError,
    #         ),  # pbal + interest != balance
    #         # (name,
    #         #  balance,
    #         #  min_balance,
    #         #  max_balance,
    #         #  account_type,
    #         #  billing_start_date,
    #         #  interest_type,
    #         #  apr,
    #         #  interest_cadence,
    #         #  minimum_payment,
    #         #  previous_statement_balance,
    #         #  principal_balance,
    #         #  interest_balance
    #         #  , ValueError),  # missing interest for type loan
    #     ],
    # )
    # def test_createAccount__invalid_inputs(
    #     self,
    #     name,
    #     balance,
    #     min_balance,
    #     max_balance,
    #     account_type,
    #     billing_start_date,
    #     interest_type,
    #     apr,
    #     interest_cadence,
    #     minimum_payment,
    #     previous_statement_balance,
    #     principal_balance,
    #     interest_balance,
    #     expected_exception,
    # ):
    #
    #     with pytest.raises(expected_exception):
    #         A = AccountSet.AccountSet([])
    #         A.createAccount(
    #             name,
    #             balance,
    #             min_balance,
    #             max_balance,
    #             account_type,
    #             billing_start_date,
    #             interest_type,
    #             apr,
    #             interest_cadence,
    #             minimum_payment,
    #             previous_statement_balance,
    #             principal_balance,
    #             interest_balance,
    #         )

    ### I think this test isn't very strong and will be covered in E2E cases
    # @pytest.mark.unit
    # def test_getAccounts(self):
    #     test_account_set = AccountSet.AccountSet([])
    #
    #     test_account_set.createAccount(
    #         name="test checking",
    #         balance=0,
    #         min_balance=0,
    #         max_balance=0,
    #         account_type="checking",
    #     )
    #     test_df = test_account_set.getAccounts()
    #     assert test_df is not None

    ### belongs in integration tests
    # @pytest.mark.unit
    # @pytest.mark.skip(reason="this test needs to be improved")
    # def test_str(self):
    #     test_str_account_set = AccountSet.AccountSet([])
    #
    #     # create a non-loan and non-credit type account
    #     test_str_account_set.createAccount(
    #         name="test checking",
    #         balance=0,
    #         min_balance=0,
    #         max_balance=0,
    #         account_type="checking",
    #     )
    #
    #     # create a credit card type account
    #     test_str_account_set.createAccount(
    #         name="test credit",
    #         balance=0,
    #         min_balance=0,
    #         max_balance=0,
    #         account_type="credit",
    #         billing_start_date="20220101",
    #         interest_type=None,
    #         apr=0.05,
    #         interest_cadence="monthly",
    #         minimum_payment=0,
    #         previous_statement_balance=0,
    #         current_statement_balance=0,
    #         principal_balance=None,
    #         interest_balance=None,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=0,
    #     )
    #
    #     # create a loan type account
    #     test_str_account_set.createAccount(
    #         name="test loan",
    #         balance=1000,
    #         min_balance=0,
    #         max_balance=10000,
    #         account_type="loan",
    #         billing_start_date="20220101",
    #         interest_type="simple",
    #         apr=0.03,
    #         interest_cadence="daily",
    #         minimum_payment=1,
    #         previous_statement_balance=None,
    #         principal_balance=900,
    #         interest_balance=100,
    #         billing_cycle_payment_balance=0,
    #         end_of_previous_cycle_balance=0,
    #     )
    #
    #     str(test_str_account_set)

    # These test cases were selected using math to ensure coverage of all cases.
    # See the gist of explanation here:
    # https://gist.github.com/hdickie/98e35458aac8a5cfd4cd7e268cf3bd55
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "test_name, advance_payment_amount, interest_accrued_this_cycle, principal_due_this_cycle, total_balance_post_accrual, min_payment, expected_result",
        [
            ("NZ_20210_0111", 100, 400, 100, 300, 200, 400),  # gpt helped
            ("Z_02110_1001", 0, 200, 100, 100, 100, 300),  # gpt helped
            # ("Z_42010_1110", 200, 300, 100, 300, 0, -1,),  # todo get rid of these or make them real
            # ("NZ_23100_1001", 200, 200, 100, 300, 200, -1),
            # ("NZ_11010_0100", 200, 100, 100, 200, 200, -1),
            # ("Z_41100_1111", 300, 100, 200, 400, 0, -1),
            # ("NZ_20200_0001", 100, 100, 100, 200, 100, -1),
            # ("NZ_10010_0001", 100, 100, 100, 200, 100, -1),
            # ("Z_03100_1011", 0, 200, 100, 300, 100, -1),
            # ("NZ_01000_0010", 100, 100, 100, 200, 200, -1),
        ],
    )
    def test_determineMinPaymentAmount(
        self,
        test_name,
        advance_payment_amount,
        interest_accrued_this_cycle,
        principal_due_this_cycle,
        total_balance_post_accrual,
        min_payment,
        expected_result,
    ):
        if expected_result == -1:
            pass
        else:
            try:
                print(
                    "test_name, advance_payment_amount, interest_accrued_this_cycle, principal_due_this_cycle, total_balance_post_accrual, min_payment, expected_result"
                )
                print(
                    test_name,
                    advance_payment_amount,
                    interest_accrued_this_cycle,
                    principal_due_this_cycle,
                    total_balance_post_accrual,
                    min_payment,
                    expected_result,
                )
                assert float(expected_result) == AccountSet.determineMinPaymentAmount(
                    float(advance_payment_amount),
                    float(interest_accrued_this_cycle),
                    float(principal_due_this_cycle),
                    float(total_balance_post_accrual),
                    float(min_payment),
                )
            except Exception as e:
                raise e
