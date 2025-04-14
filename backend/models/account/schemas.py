
from pydantic import BaseModel, Field
from typing import Union, Optional, Literal



class AccountBase(BaseModel):
    name: str
    balance: float
    min_balance: float
    max_balance: float
    account_type: Literal["checking", "savings", "credit", "loan", "investment"]
    
    billing_start_date_YYYYMMDD: Optional[str] = None
    interest_type: Optional[str] = None
    apr: Optional[float] = None
    interest_cadence: Optional[str] = None #replace w literal or enum later
    minimum_payment: Optional[float] = None
    primary_checking_ind: bool = False

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[float] = None
    min_balance: Optional[float] = None
    max_balance: Optional[float] = None
    account_type: Optional[str] = None
    billing_start_date_YYYYMMDD: Optional[str] = None
    interest_type: Optional[str] = None
    apr: Optional[float] = None
    interest_cadence: Optional[str] = None
    minimum_payment: Optional[float] = None
    primary_checking_ind: Optional[bool] = None

class AccountRead(AccountBase):
    id: str  # or UUID if you’re using UUIDs

class CheckingAccountCreate(AccountBase):
    account_type: Literal["checking"]
    apr: Literal[None] = None
    interest_type: Literal[None] = None

class CreditAccountCreate(AccountBase):
    account_type: Literal["credit"]
    apr: float
    interest_type: str
    minimum_payment: float

