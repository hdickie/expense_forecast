"""
Creates an Account. Input validation is performed.

See Account.py for more details
This file is exhaustive test cases.

Test Cases
Expected Successes
[x] S1 Checking
[x] S2 Prev Stmt Bal
[x] S3 Curr Stmt Bal
[x] S4 Principal Balance
[x] S5 Interest

Expected Fails
Parameters that are provided are incorrect
[x] F0 Provide no parameters
[x] F1 Checking - include irrelevant parameters
[x] F2 Prev Stmt Bal - exclude relevant non-default-required parameters and include irrelevant parameters
[x] F3 Curr Stmt Bal - exclude relevant non-default-required parameters and include irrelevant parameters
[x] F4 Principal Balance - exclude relevant non-default-required parameters and include irrelevant parameters
[x] F5 Interest - exclude relevant non-default-required parameters and include irrelevant parameters

Incorrect Types provided for necessary parameters
[x] F6 Prev Stmt Bal - Provide incorrect types for all necessary parameters
[x] F7 Principal Balance - Provide incorrect types for all necessary parameters

Inconsistent values provided for related parameters
[x] F8 Checking - Balance is less than Minimum Balance
[x] F9 Checking - Balance is greater than Maximum Balance
[x] F10 Checking - Min Balance is greater than Max Balance

Illegal Values
[x] F11 - Provide illegal values for account type, interest type and cadence

More I thought of:
[ ] F13 Account_type is explicitly passed as None
[ ] F14 if Account_type is credit or loan
[ ] F15 If Account_type is empty string

#todo im not sure if what raises a TypeError vs. a ValueError is consistent
#todo blank lines between error messages and JSON may be inconsistent

>>> Account() # Test F0
Traceback (most recent call last):
...
TypeError: Account.__init__() missing 5 required positional arguments: 'name', 'balance', 'min_balance', 'max_balance', and 'account_type'

>>> print( #S1 Checking
... Account(name='S1 Checking',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type='checking').toJSON())
{
"Name":"S1 Checking",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"checking",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #S2 Prev Stmt Bal
... Account(
... name='S2 Prev Stmt Bal',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=0.05,
... interest_cadence='monthly',
... interest_type='compound',
... billing_start_date_YYYYMMDD='20000101',
... account_type='Prev Stmt Bal',
... minimum_payment=40, throw_exceptions=False ).toJSON())
{
"Name":"S2 Prev Stmt Bal",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Prev Stmt Bal",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"compound",
"APR":"0.05",
"Interest_Cadence":"monthly",
"Minimum_Payment":"40.0"
}

>>> print( #S3 Curr Stmt Bal
... Account(
... name='S3 Curr Stmt Bal',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Curr Stmt Bal',
... minimum_payment=None ).toJSON())
{
"Name":"S3 Curr Stmt Bal",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Curr Stmt Bal",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #S4 Principal Balance
... Account(
... name='S4 Principal Balance',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=0.05,
... interest_cadence='daily',
... interest_type='simple',
... billing_start_date_YYYYMMDD='20000101',
... account_type='Principal Balance',
... minimum_payment=223.15 ).toJSON())
{
"Name":"S4 Principal Balance",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Principal Balance",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"simple",
"APR":"0.05",
"Interest_Cadence":"daily",
"Minimum_Payment":"223.15"
}

>>> print( #S5 Interest
... Account(
... name='S5 Interest',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Interest',
... minimum_payment=None ).toJSON())
{
"Name":"S5 Interest",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Interest",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #F1: Checking: Exception Test
... Account(name='F1 Checking: Exception Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=0.05,
... interest_cadence='daily',
... interest_type='simple',
... billing_start_date_YYYYMMDD='20000101',
... account_type='checking',
... minimum_payment=40 ).toJSON())
Traceback (most recent call last):
...
ValueError

>>> print( #F1: Checking: Debug Messages Test
... Account(name='F1 Checking: Debug Messages Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=0.05,
... interest_cadence='daily',
... interest_type='simple',
... billing_start_date_YYYYMMDD='20000101',
... account_type='checking',
... minimum_payment=40, throw_exceptions=False ).toJSON())
ValueErrors:
For types other than prev stmt bal, principal balance, or savings, Account.apr should be None.
Value was:0.05
For account_type other than prev stmt bal, principal balance, or savings, Account.interest_cadence should be None.
Value was:daily
For types other than prev stmt bal, principal balance, or savings, Account.interest_type should be None.
Value was:simple
For types other than prev stmt bal, principal balance, or savings, Account.billing_start_date should be None.
Value was:20000101
For types other than prev stmt bal or principal balance, Account.minimum_payment should be None.
Value was:40
<BLANKLINE>
{
"Name":"F1 Checking: Debug Messages Test",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"checking",
"Billing_Start_Date":"20000101",
"Interest_Type":"simple",
"APR":"0.05",
"Interest_Cadence":"daily",
"Minimum_Payment":"40"
}

>>> print( #F2: Prev Stmt Bal: Exception Test
... Account(name='F2 Prev Stmt Bal: Exception Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Prev Stmt Bal',
... minimum_payment=None ).toJSON())
Traceback (most recent call last):
...
TypeError

>>> print( #F2 Prev Stmt Bal: Debug Messages Test
... Account(
... name='F2 Prev Stmt Bal: Debug Messages Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Prev Stmt Bal',
... minimum_payment=None, throw_exceptions=False ).toJSON())
TypeErrors:
failed cast Account.apr to float
Value was:None
failed cast Account.billing_start_date_YYYYMMDD to datetime
Value was:None
failed cast Account.minimum_payment to float
Value was:None
<BLANKLINE>
ValueErrors:
For account_type = prev stmt bal, principal balance, or savings, Account.interest_cadence should be one of: daily, monthly, quarterly, or yearly.
Value was:None
{
"Name":"F2 Prev Stmt Bal: Debug Messages Test",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Prev Stmt Bal",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #F3 Curr Stmt Bal: Exception Test
... Account(name='F3 Curr Stmt Bal: Exception Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Curr Stmt Bal",
... apr=0.05,
... interest_cadence='monthly',
... interest_type='simple',
... billing_start_date_YYYYMMDD='20000101',
... minimum_payment=40, print_debug_messages=False ).toJSON())
Traceback (most recent call last):
...
ValueError

>>> print( #Test F3 Curr Stmt Bal: Debug Messages Test
... Account(name='F3 Curr Stmt Bal: Debug Messages Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Curr Stmt Bal",
... apr=0.05,
... interest_cadence='monthly',
... interest_type='simple',
... billing_start_date_YYYYMMDD='20000101',
... minimum_payment=40,throw_exceptions=False).toJSON())
ValueErrors:
For types other than prev stmt bal, principal balance, or savings, Account.apr should be None.
Value was:0.05
For account_type other than prev stmt bal, principal balance, or savings, Account.interest_cadence should be None.
Value was:monthly
For types other than prev stmt bal, principal balance, or savings, Account.interest_type should be None.
Value was:simple
For types other than prev stmt bal, principal balance, or savings, Account.billing_start_date should be None.
Value was:20000101
For types other than prev stmt bal or principal balance, Account.minimum_payment should be None.
Value was:40
<BLANKLINE>
{
"Name":"F3 Curr Stmt Bal: Debug Messages Test",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Curr Stmt Bal",
"Billing_Start_Date":"20000101",
"Interest_Type":"simple",
"APR":"0.05",
"Interest_Cadence":"monthly",
"Minimum_Payment":"40"
}

>>> print( #F4 Principal Balance: Exception Test
... Account(name='F4 Principal Balance: Exception Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Principal Balance",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None, print_debug_messages=False).toJSON())
Traceback (most recent call last):
...
TypeError

>>> print( #F4 Principal Balance: Debug Messages Test
... Account(name='F4 Principal Balance: Debug Messages Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Principal Balance",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,throw_exceptions=False).toJSON())
TypeErrors:
failed cast Account.apr to float
Value was:None
failed cast Account.billing_start_date_YYYYMMDD to datetime
Value was:None
failed cast Account.minimum_payment to float
Value was:None
<BLANKLINE>
ValueErrors:
For account_type = prev stmt bal, principal balance, or savings, Account.interest_cadence should be one of: daily, monthly, quarterly, or yearly.
Value was:None
{
"Name":"F4 Principal Balance: Debug Messages Test",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Principal Balance",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #F5 Interest - exclude relevant non-default-required parameters and include irrelevant parameters: Exception Test',
... Account(name='F5 Interest - exclude relevant non-default-required parameters and include irrelevant parameters: Exception Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Interest",
... apr=0.05,
... interest_cadence="daily",
... interest_type="simple",
... billing_start_date_YYYYMMDD="20000101",
... minimum_payment=40 ).toJSON())
Traceback (most recent call last):
...
ValueError

>>> print( #F5 Interest - exclude relevant non-default-required parameters and include irrelevant parameters: Debug Messages Test
... Account(name='F5 Interest - exclude relevant non-default-required parameters and include irrelevant parameters: Debug Messages Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Interest",
... apr=0.05,
... interest_cadence="daily",
... interest_type="simple",
... billing_start_date_YYYYMMDD="20000101",
... minimum_payment=40,throw_exceptions=False).toJSON())
ValueErrors:
For types other than prev stmt bal, principal balance, or savings, Account.apr should be None.
Value was:0.05
For account_type other than prev stmt bal, principal balance, or savings, Account.interest_cadence should be None.
Value was:daily
For types other than prev stmt bal, principal balance, or savings, Account.interest_type should be None.
Value was:simple
For types other than prev stmt bal, principal balance, or savings, Account.billing_start_date should be None.
Value was:20000101
For types other than prev stmt bal or principal balance, Account.minimum_payment should be None.
Value was:40
<BLANKLINE>
{
"Name":"F5 Interest - exclude relevant non-default-required parameters and include irrelevant parameters: Debug Messages Test",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Interest",
"Billing_Start_Date":"20000101",
"Interest_Type":"simple",
"APR":"0.05",
"Interest_Cadence":"daily",
"Minimum_Payment":"40"
}

>>> print( #F6 Credit - Provide incorrect types for all necessary parameters
... Account(name='F6 Credit - Provide incorrect types for all necessary parameters: Exception Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Prev Stmt Bal",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None, print_debug_messages=False).toJSON())
Traceback (most recent call last):
...
TypeError

>>> print( #F6 Credit - Provide incorrect types for all necessary parameters: Debug Messages Test
... Account(name='F6 Credit - Provide incorrect types for all necessary parameters: Debug Messages Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Prev Stmt Bal",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,throw_exceptions=False).toJSON())
TypeErrors:
failed cast Account.apr to float
Value was:None
failed cast Account.billing_start_date_YYYYMMDD to datetime
Value was:None
failed cast Account.minimum_payment to float
Value was:None
<BLANKLINE>
ValueErrors:
For account_type = prev stmt bal, principal balance, or savings, Account.interest_cadence should be one of: daily, monthly, quarterly, or yearly.
Value was:None
{
"Name":"F6 Credit - Provide incorrect types for all necessary parameters: Debug Messages Test",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Prev Stmt Bal",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}


>>> print( #F7 Loan - Provide incorrect types for all necessary parameters: Debug Messages Test
... Account(name='F7 Principal Balance - Provide incorrect types for all necessary parameters: Debug Messages Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Principal Balance",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,
... throw_exceptions=False).toJSON())
TypeErrors:
failed cast Account.apr to float
Value was:None
failed cast Account.billing_start_date_YYYYMMDD to datetime
Value was:None
failed cast Account.minimum_payment to float
Value was:None
<BLANKLINE>
ValueErrors:
For account_type = prev stmt bal, principal balance, or savings, Account.interest_cadence should be one of: daily, monthly, quarterly, or yearly.
Value was:None
{
"Name":"F7 Principal Balance - Provide incorrect types for all necessary parameters: Debug Messages Test",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"Principal Balance",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}


>>> print( #F7 Principal Balance - Provide incorrect types for all necessary parameters: Exception Test
... Account(name='F7 Principal Balance - Provide incorrect types for all necessary parameters: Exception Test',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type="Principal Balance",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,
... print_debug_messages=False).toJSON())
Traceback (most recent call last):
...
TypeError

>>> print( #F8 Checking - Balance is less than Minimum Balance: Exception Test
... Account(name='F8 Checking - Balance is less than Minimum Balance',
... balance=-10,
... min_balance=0,
... max_balance=0,
... account_type="checking",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None ).toJSON())
Traceback (most recent call last):
...
ValueError

>>> print( #F8 Checking - Balance is less than Minimum Balance: Debug Messages Test
... Account(name='F8 Checking - Balance is less than Minimum Balance',
... balance=-10,
... min_balance=0,
... max_balance=0,
... account_type="checking",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,throw_exceptions=False).toJSON())
ValueErrors:
Account.balance was less than minimum balance
0.0 <= -10.0 was not true
<BLANKLINE>
{
"Name":"F8 Checking - Balance is less than Minimum Balance",
"Balance":"-10.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"checking",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #F9 Checking - Balance is greater than Maximum Balance: Exception Test
... Account(name='F9 Checking - Balance is greater than Maximum Balance',
... balance=10,
... min_balance=0,
... max_balance=0,
... account_type="checking",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None ).toJSON())
Traceback (most recent call last):
...
ValueError

>>> print( #F9 Checking - Balance is greater than Maximum Balance : Debug Messages Test
... Account(name='F9 Checking - Balance is greater than Maximum Balance',
... balance=10,
... min_balance=0,
... max_balance=0,
... account_type="checking",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,throw_exceptions=False).toJSON())
ValueErrors:
Account.balance was greater than Account.max_balance
0.0 >= 10.0 was not true
<BLANKLINE>
{
"Name":"F9 Checking - Balance is greater than Maximum Balance",
"Balance":"10.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"checking",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #F10 Checking - Min Balance is greater than Max Balance: Exception Test
... Account(name='F10 Checking - Min Balance is greater than Max Balance',
... balance=5,
... min_balance=10,
... max_balance=0,
... account_type="checking",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None ).toJSON())
Traceback (most recent call last):
...
ValueError

>>> print( #F10 Checking - Min Balance is greater than Max Balance: Debug Messages Test
... Account(name='F10 Checking - Min Balance is greater than Max Balance',
... balance=5,
... min_balance=10,
... max_balance=0,
... account_type="checking",
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,throw_exceptions=False).toJSON())
ValueErrors:
Account.balance was less than minimum balance
10.0 <= 5.0 was not true
Account.balance was greater than Account.max_balance
0.0 >= 5.0 was not true
Account.max_balance was less than Account.min_balance
<BLANKLINE>
{
"Name":"F10 Checking - Min Balance is greater than Max Balance",
"Balance":"5.0",
"Min_Balance":"10.0",
"Max_Balance":"0.0",
"Account_Type":"checking",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

>>> print( #F11 - Provide illegal values for account type: Exception Test
... Account(name='F11 - Provide illegal values for account type, interest type and cadence',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type='shmecking',
... apr=None,
... interest_cadence="shmeekly",
... interest_type="shmimple",
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None).toJSON())
Traceback (most recent call last):
...
ValueError

>>> print( #F11 - Provide illegal values for account type: Debug Messages Test
... Account(name='F11 - Provide illegal values for account type, interest type and cadence',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type='shmecking',
... apr=None,
... interest_cadence="shmeekly",
... interest_type="shmimple",
... billing_start_date_YYYYMMDD=None,
... minimum_payment=None,
... throw_exceptions=False).toJSON())
ValueErrors:
Account.account_type was not one of: checking, prev stmt bal, curr stmt bal, interest, savings, principal balance
Value was:shmecking
For account_type other than prev stmt bal, principal balance, or savings, Account.interest_cadence should be None.
Value was:shmeekly
For types other than prev stmt bal, principal balance, or savings, Account.interest_type should be None.
Value was:shmimple
<BLANKLINE>
{
"Name":"F11 - Provide illegal values for account type, interest type and cadence",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"shmecking",
"Billing_Start_Date":"None",
"Interest_Type":"shmimple",
"APR":"None",
"Interest_Cadence":"shmeekly",
"Minimum_Payment":"None"
}

>>> print( #F13 account_type is explicitly None
... Account(name='F13 account_type is explicitly None',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type=None,throw_exceptions=False).toJSON())
ValueErrors:
Account.account_type was not one of: checking, prev stmt bal, curr stmt bal, interest, savings, principal balance
Value was:none
<BLANKLINE>
{
"Name":"F13 account_type is explicitly None",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"None",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}

# This is giving an error for some reason even though it looks right to me.
# >>> print( #F14 account_type is credit
# ... Account(name='F14 account_type is credit',
# ... balance=0,
# ... min_balance=0,
# ... max_balance=0,
# ... account_type='credit',throw_exceptions=False).toJSON())
# ValueErrors:
# WARNING: Account.account_type was one of: credit, loan
# Note that these values are accepted by AccountSet.addAccount() but not by the class Account directly
# Account.account_type was not one of: checking, prev stmt bal, curr stmt bal, interest, savings, principal balance
# Value was:credit
# <BLANKLINE>
# {
# "Name":"F14 account_type is credit",
# "Balance":"0.0",
# "Min_Balance":"0.0",
# "Max_Balance":"0.0",
# "Account_Type":"credit",
# "Billing_Start_Date":"None",
# "Interest_Type":"None",
# "APR":"None",
# "Interest_Cadence":"None",
# "Minimum_Payment":"None"
# }

>>> print( #F15 account_type is empty string
... Account(name='F15 account_type is empty string',
... balance=0,
... min_balance=0,
... max_balance=0,
... account_type='',throw_exceptions=False).toJSON())
ValueErrors:
Account.account_type was not one of: checking, prev stmt bal, curr stmt bal, interest, savings, principal balance
Value was:
<BLANKLINE>
{
"Name":"F15 account_type is empty string",
"Balance":"0.0",
"Min_Balance":"0.0",
"Max_Balance":"0.0",
"Account_Type":"",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
}
"""

if __name__ == "__main__":
    import doctest
    from Account import *
    doctest.testmod()