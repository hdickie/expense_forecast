import Account, AccountSet

"""
Inconsistent account parameters: Min_Balance and Max_Balance
>>> print(AccountSet([Account.Account(name="Credit: Curr Stmt Bal",
... balance=75,
... min_balance=0,
... max_balance=100,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Curr Stmt Bal',
... minimum_payment=None
... ),
... Account.Account(name="Credit: Prev Stmt Bal",
... balance=75,
... min_balance=1,
... max_balance=101,
... apr=0.05,
... interest_cadence="Monthly",
... interest_type="Compound",
... billing_start_date_YYYYMMDD="20000101",
... account_type='Prev Stmt Bal',
... minimum_payment=40
... ),Account.Account(name="Loan: Interest",
... balance=75,
... min_balance=0,
... max_balance=100,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Interest',
... minimum_payment=None
... ),
... Account.Account(name="Loan: Principal Balance",
... balance=75,
... min_balance=1,
... max_balance=101,
... apr=0.05,
... interest_cadence="Monthly",
... interest_type="Compound",
... billing_start_date_YYYYMMDD="20000101",
... account_type='Principal Balance',
... minimum_payment=40
... )],raise_exceptions=False).toJSON())
ValueErrors:
Min_Balance did not match between Curr Stmt Bal and Prev Stmt Bal for account Credit
Max_Balance did not match between Curr Stmt Bal and Prev Stmt Bal for account Credit
Min_Balance did not match between Principal Balance and Interest for account Loan
Max_Balance did not match between Principal Balance and Interest for account Loan
<BLANKLINE>
{
{
"Name":"Credit: Curr Stmt Bal",
"Balance":"75.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Curr Stmt Bal",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Credit: Prev Stmt Bal",
"Balance":"75.0",
"Min_Balance":"1.0",
"Max_Balance":"101.0",
"Account_Type":"Prev Stmt Bal",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
},
{
"Name":"Loan: Interest",
"Balance":"75.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Interest",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Loan: Principal Balance",
"Balance":"75.0",
"Min_Balance":"1.0",
"Max_Balance":"101.0",
"Account_Type":"Principal Balance",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
}
}

Combined balance max account boundary violation
>>> print(AccountSet([Account.Account(name="Credit: Curr Stmt Bal",
... balance=75,
... min_balance=0,
... max_balance=100,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Curr Stmt Bal',
... minimum_payment=None
... ),
... Account.Account(name="Credit: Prev Stmt Bal",
... balance=75,
... min_balance=0,
... max_balance=100,
... apr=0.05,
... interest_cadence="Monthly",
... interest_type="Compound",
... billing_start_date_YYYYMMDD="20000101",
... account_type='Prev Stmt Bal',
... minimum_payment=40
... ),Account.Account(name="Loan: Interest",
... balance=75,
... min_balance=0,
... max_balance=100,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Interest',
... minimum_payment=None
... ),
... Account.Account(name="Loan: Principal Balance",
... balance=75,
... min_balance=0,
... max_balance=100,
... apr=0.05,
... interest_cadence="Monthly",
... interest_type="Compound",
... billing_start_date_YYYYMMDD="20000101",
... account_type='Principal Balance',
... minimum_payment=40
... )],raise_exceptions=False).toJSON())
ValueErrors:
Combined Prev and Curr Stmt bal was greater than max_balance for account Credit
Combined Principal Balance and Interest bal was greater than max_balance for account Loan
<BLANKLINE>
{
{
"Name":"Credit: Curr Stmt Bal",
"Balance":"75.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Curr Stmt Bal",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Credit: Prev Stmt Bal",
"Balance":"75.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Prev Stmt Bal",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
},
{
"Name":"Loan: Interest",
"Balance":"75.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Interest",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Loan: Principal Balance",
"Balance":"75.0",
"Min_Balance":"0.0",
"Max_Balance":"100.0",
"Account_Type":"Principal Balance",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
}
}

Combined balance min account boundary violation
>>> print(AccountSet([Account.Account(name="Credit: Curr Stmt Bal",
... balance=-10,
... min_balance=-15,
... max_balance=100,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Curr Stmt Bal',
... minimum_payment=None
... ),
... Account.Account(name="Credit: Prev Stmt Bal",
... balance=-10,
... min_balance=-15,
... max_balance=100,
... apr=0.05,
... interest_cadence="Monthly",
... interest_type="Compound",
... billing_start_date_YYYYMMDD="20000101",
... account_type='Prev Stmt Bal',
... minimum_payment=40
... ),Account.Account(name="Loan: Interest",
... balance=-10,
... min_balance=-15,
... max_balance=100,
... apr=None,
... interest_cadence=None,
... interest_type=None,
... billing_start_date_YYYYMMDD=None,
... account_type='Interest',
... minimum_payment=None
... ),
... Account.Account(name="Loan: Principal Balance",
... balance=-10,
... min_balance=-15,
... max_balance=100,
... apr=0.05,
... interest_cadence="Monthly",
... interest_type="Compound",
... billing_start_date_YYYYMMDD="20000101",
... account_type='Principal Balance',
... minimum_payment=40
... )],raise_exceptions=False).toJSON())
ValueErrors:
Combined Prev and Curr Stmt bal was less than min_balance for account Credit
Combined Principal Balance and Interest bal was less than min_balance for account Loan
<BLANKLINE>
{
{
"Name":"Credit: Curr Stmt Bal",
"Balance":"-10.0",
"Min_Balance":"-15.0",
"Max_Balance":"100.0",
"Account_Type":"Curr Stmt Bal",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Credit: Prev Stmt Bal",
"Balance":"-10.0",
"Min_Balance":"-15.0",
"Max_Balance":"100.0",
"Account_Type":"Prev Stmt Bal",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
},
{
"Name":"Loan: Interest",
"Balance":"-10.0",
"Min_Balance":"-15.0",
"Max_Balance":"100.0",
"Account_Type":"Interest",
"Billing_Start_Date":"None",
"Interest_Type":"None",
"APR":"None",
"Interest_Cadence":"None",
"Minimum_Payment":"None"
},
{
"Name":"Loan: Principal Balance",
"Balance":"-10.0",
"Min_Balance":"-15.0",
"Max_Balance":"100.0",
"Account_Type":"Principal Balance",
"Billing_Start_Date":"2000-01-01 00:00:00",
"Interest_Type":"Compound",
"APR":"0.05",
"Interest_Cadence":"Monthly",
"Minimum_Payment":"40.0"
}
}
"""

if __name__ == "__main__":
    import doctest
    from AccountSet import *
    doctest.testmod()