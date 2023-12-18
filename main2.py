import logging
import ExpenseForecast
import AccountSet
import BudgetSet
import MemoRuleSet
import MilestoneSet
import ForecastHandler


def compound_loan_A():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan A",balance=1100,min_balance=0,max_balance=1100,account_type="loan",
                    billing_start_date_YYYYMMDD="20240101",interest_type="compound",apr=0.1,interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1000,accrued_interest=100)
    return A.accounts

def compound_loan_A_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan A",balance=1000,min_balance=0,max_balance=1100,account_type="loan",
                    billing_start_date_YYYYMMDD="20240101",interest_type="compound",apr=0.1,interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1000,accrued_interest=0)
    return A.accounts

def compound_loan_B():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan B", balance=1600, min_balance=0, max_balance=1600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.01,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1500, accrued_interest=100)
    return A.accounts

def compound_loan_B_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan B", balance=1500, min_balance=0, max_balance=1600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.01,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=1500, accrued_interest=0)
    return A.accounts

def compound_loan_C():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan C", balance=2600, min_balance=0, max_balance=2600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.05,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=2500, accrued_interest=100)
    return A.accounts

def compound_loan_C_no_interest():
    A = AccountSet.AccountSet([])
    A.createAccount("test loan C", balance=2500, min_balance=0, max_balance=2600, account_type="loan",
                    billing_start_date_YYYYMMDD="20240101", interest_type="compound", apr=0.05,
                    interest_cadence="monthly",
                    minimum_payment=50,
                    principal_balance=2500, accrued_interest=0)
    return A.accounts

def checking():
    A = AccountSet.AccountSet([])
    A.createAccount("test checking", balance=10000, min_balance=0, max_balance=10000, account_type="checking")
    return A.accounts

def one_loan__p_1000__i_100__apr_01():
    return AccountSet.AccountSet(checking()+compound_loan_A())

def two_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001():
    return AccountSet.AccountSet(checking() + compound_loan_A() + compound_loan_B())

def three_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001___p_2500__i_100__apr_005():
    return AccountSet.AccountSet(checking() + compound_loan_A() + compound_loan_B() + compound_loan_C())

def one_loan__p_1000__i_000__apr_01():
    return AccountSet.AccountSet(checking()+compound_loan_A_no_interest())

def two_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001():
    return AccountSet.AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest())

def three_loans__p_1000__i_000__apr_01___p_1500__i_000__apr_001___p_2500__i_000__apr_005():
    return AccountSet.AccountSet(checking() + compound_loan_A_no_interest() + compound_loan_B_no_interest() + compound_loan_C_no_interest())




if __name__ == '__main__':

    account_set = three_loans__p_1000__i_100__apr_01___p_1500__i_100__apr_001___p_2500__i_100__apr_005()
    print(account_set)
    amount = 1500
    payment_amounts = account_set.allocate_additional_loan_payments(amount)
    print(payment_amounts)
    print(account_set.getAccounts().to_string())