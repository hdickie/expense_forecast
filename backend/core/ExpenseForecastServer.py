
# HumanMiles “Your future called. It’s fine with this.”

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from fief_client import FiefAsync
from fief_client.integrations.fastapi import FiefAuth
from fastapi.security import OAuth2AuthorizationCodeBearer
from fief_client import FiefUserInfo
from fastapi import Request, Response, HTTPException
from redis import Redis
import json
from fastapi.responses import RedirectResponse
import datetime
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from pydantic import BaseModel, Field
import httpx
import subprocess
from dotenv import load_dotenv
import os
from fastapi import Depends, HTTPException, Header
from fief_client import FiefAccessTokenInfo, FiefAsync
from core import AccountSet
from models.account.schemas import AccountCreate
from fastapi import Request
from urllib.parse import urlencode
load_dotenv(".env") 

import logging
logger = logging.getLogger("core.ExpenseForecastServer")

from fastapi import APIRouter
router = APIRouter()

# 400 Bad Request - This means that client-side input fails validation.
# 401 Unauthorized - This means the user isn't not authorized to access a resource. It usually returns when the user isn't authenticated.
# 403 Forbidden - This means the user is authenticated, but it's not allowed to access a resource.
# 404 Not Found - This indicates that a resource is not found.
# 500 Internal server error - This is a generic server error. It probably shouldn't be thrown explicitly.
# 502 Bad Gateway - This indicates an invalid response from an upstream server.
# 503 Service Unavailable - This indicates that something unexpected happened on server side (It can be anything like server overload, some parts of the system failed, etc.).

# fast-api cache

# have version in the request path


redis = Redis(host="redis", port=6379, db=0, decode_responses=True)
from os import getenv

fief = FiefAsync(
    getenv("FIEF_INTERNAL_DOMAIN"),
    getenv("FIEF_CLIENT_ID"),
    getenv("FIEF_CLIENT_SECRET")
)

scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{getenv('FIEF_DOMAIN')}/authorize",
    tokenUrl=f"{getenv('FIEF_DOMAIN')}/api/token",
    scopes={"openid": "openid", "offline_access": "offline_access"},
    auto_error=False,
)

class SessionData(BaseModel):
    user_id: str
    forecast_id: Optional[str] = None

auth = FiefAuth(fief, scheme)



class User(BaseModel):
    username: str
    # role: str
    # isAdmin: str
    # add whatever fields you want to collect from the client

# class SessionData(BaseModel):
#     user_id: str
#     forecast_id: str | None = None  # Optional now, can expand later

SESSION_COOKIE_NAME = "session_id"
SESSION_TTL = 3600  # 1 hour

class ForecastSelect(BaseModel):
    forecast_name: str

def get_current_user(request: Request):
    access_token = request.headers.get('authorization').split(' ')[1]
    #url = "http://localhost:8000/api/userinfo" #todo could be cached
    url = f"{getenv('FIEF_DOMAIN')}/api/userinfo"
    headers = {"Authorization": "Bearer "+access_token}
    response = httpx.get(url, headers=headers, follow_redirects=True)
    return response.json()["email"]



def get_session_data(request: Request) -> SessionData:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="Missing session")

    session_raw = redis.get(session_id)
    if not session_raw:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    return json.loads(session_raw)
    #return SessionData.parse_raw(session_raw)

# login_url = fief.get_authorization_url(
#     redirect_uri="https://your-app.com/callback",
#     scope=["openid", "email", "profile"],
#     extras={"tenant": "your-tenant-id"}  # 👈 Add your tenant here
# )


@router.get("/login", name="login")
async def login(request: Request):
    try:
        print('ENTER login')
        
        redirect_uri = str(request.url_for("auth_callback"))
        
        print("redirect_uri:"+str(redirect_uri))
        # auth_url = await fief.auth_url(
        #     redirect_uri=redirect_uri,
        #     scope=["openid", "offline_access", "profile", "email"],
        #     extras_params={"tenant": "expense-forecast"}
        # )
        print("FIEF config:")
        print("FIEF_INTERNAL_DOMAIN:", getenv("FIEF_INTERNAL_DOMAIN"))
        print("FIEF_CLIENT_ID:", getenv("FIEF_CLIENT_ID"))
        print("FIEF_CLIENT_SECRET:", getenv("FIEF_CLIENT_SECRET"))

        
        discovery_url = f"{getenv('FIEF_INTERNAL_DOMAIN')}/.well-known/openid-configuration"
        print("🔎 Discovery URL:", discovery_url)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(discovery_url)
                response.raise_for_status()
                print("✅ Discovery response:", response.json())
            except Exception as e:
                print("💥 Exception while hitting discovery URL:", str(e))
                raise

        redirect_uri = "http://api.localhost/auth/callback"
        params = {
            "response_type": "code",
            "client_id": getenv("FIEF_CLIENT_ID"),
            "redirect_uri": redirect_uri,
            "scope": "openid offline_access profile email",
            "tenant": "expense-forecast"
        }

        query_string = urlencode(params)
        auth_url = f"{getenv('FIEF_DOMAIN')}/authorize?{query_string}"

        # auth_url = await fief.auth_url(
        #         redirect_uri=redirect_uri,
        #         scope=["openid", "offline_access", "profile", "email"],
        #         extras_params={"tenant": "expense-forecast"}
        #     )

        print("auth_url:", auth_url)
        print('EXIT login')
        return RedirectResponse(auth_url)
    except Exception as e:
        print(e)
        import traceback
        print("🔥 Exception in login():", str(e))
        traceback.print_exc()
        raise e

@router.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request, response: Response):
    print('ENTER auth_callback')
    
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # redirect_uri = str(request.url_for("auth_callback"))
    # redirect_uri = f"{getenv('FIEF_DOMAIN')}/callback"
    redirect_uri = "http://api.localhost/auth/callback"


    print("CODE:", code, flush=True)
    print("REDIRECT URI:", redirect_uri, flush=True)
    print("FIEF_CLIENT_ID:", getenv("FIEF_CLIENT_ID"), flush=True)
    print("FIEF_CLIENT_SECRET:", getenv("FIEF_CLIENT_SECRET"), flush=True)
    print("Token endpoint should be:", f"{getenv('FIEF_INTERNAL_DOMAIN')}/api/token", flush=True)


    try:

        # token, userinfo = await fief.auth_callback(code, redirect_uri)
        async with httpx.AsyncClient() as client:
            try:
                token_resp = await client.post(
                    f"{getenv('FIEF_INTERNAL_DOMAIN')}/api/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": getenv("FIEF_CLIENT_ID"),
                        "client_secret": getenv("FIEF_CLIENT_SECRET")
                    }
                )
                print("Token response:", token_resp.status_code, token_resp.text)
                token_resp.raise_for_status()
            except Exception as e:
                print("🔥 Raw token error:", str(e))
                raise

        token_data = token_resp.json()
        userinfo = await fief.userinfo(token_data.get("access_token"))

        # Store the token or create a session here
        #lookup api_key, and then map it in redis to session_id

        session_id = redis.get(f"email_to_sessionid:{userinfo['email']}")
        if session_id is None:
            session_id = str(uuid4())
        session_data = {    
            "userinfo": userinfo,
            "session_id": session_id,
            "access_token": token_data.get("access_token"),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "expires_at": token_data.get("expires_at")  # optional
        }

        response.set_cookie("session_id", session_id, httponly=True)
        print('Set session_id cookie to '+str(session_id))

        redis.setex(f"sessionid_to_sessiondata:{session_id}", 3600, json.dumps(session_data))
        print('Set session_id -> session data for '+str(session_id))

        redis.setex(f"email_to_sessionid:{userinfo['email']}", 3600, session_id)
        print('Set Email -> session_id for '+str(userinfo['email'] + ' = '+str(session_id)))
        
        print('EXIT auth_callback (SUCCESS)')
        return session_data

    except Exception as e:
        print(e)
        import traceback
        print("🔥 Exception in login():", str(e))
        traceback.print_exc()
        print('EXIT auth_callback (FAIL)')
        raise HTTPException(status_code=401, detail=f"Auth failed: {str(e)}")
    
@router.get("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    redis.delete(f"session:{session_id}")

    for cookie_name in request.cookies.keys():
        response.delete_cookie(cookie_name)
    
    # Optionally: redirect to Fief logout URL
    return {"message": "Logged out"}



## Example usage
# // Every 5 minutes
# setInterval(() => {
#   fetch("/ping", { method: "POST", credentials: "include" });
# }, 5 * 60 * 1000);
#use to prevent session data expiry
@router.get("/ping")
@router.post("/ping")
async def ping(request: Request):
    
    #there are smart-people reasons for this that I don't fully understand
    if request.method == 'POST':
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401)

        raw = redis.get(f"session:{session_id}")
        if not raw:
            raise HTTPException(status_code=401)
        
        # Optional: re-store to refresh TTL
        redis.setex(f"session:{session_id}", 3600, raw)

    return {"ok": True}




@router.post("/forecast/current")
async def set_current_forecast(
    forecast_name: ForecastSelect,
    request: Request,
    user: dict = Depends(get_current_user)
):
    # print("Cookies:", request.cookies)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session_id = request.cookies.get("session_id")
    session_raw = redis.get(f"session:{session_id}")
    session_data = json.loads(session_raw)

    session_data["current_forecast_name"] = forecast_name.forecast_name
    redis.setex(f"session:{session_id}", 3600, json.dumps(session_data))

    return {"message": "SET current_forecast = "+str(forecast_name), "name": forecast_name.forecast_name}

@router.get("/forecast/current")
async def set_current_forecast(
    request: Request,
    user: dict = Depends(get_current_user)
):
    # print("Cookies:", request.cookies)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session_id = request.cookies.get("session_id")
    session_raw = redis.get(f"session:{session_id}")
    session_data = json.loads(session_raw)

    if 'current_forecast_name' in session_data:
        forecast_name = session_data["current_forecast_name"]
    else:
        forecast_name = None

    #just to reset expiry ts
    redis.setex(f"session:{session_id}", 3600, json.dumps(session_data))

    return {"message": "GET current_forecast = "+str(forecast_name), "name": forecast_name}


@router.post("/users/{user_id}/forecasts/{forecast_name}/accounts")
async def create_account_for_user_forecast(
    user_id: str,
    forecast_name: str,
    account: AccountCreate  # <- your Pydantic model
):
    
    #todo if draft forecast does not exist, create it

    return {
        "user_id": user_id,
        "forecast_name": forecast_name,
        "account": account.dict()
    }

# @app.post("/draft/accounts")
# async def create_account_for_user_forecast(
#     user_id: str,
#     forecast_id: str
# ):
#     return {
#         "user_id": user_id,
#         "forecast_id": forecast_id,
#         "account": account.dict()
#     }


@router.post("/draft/accounts")
async def create_account(
    account: AccountCreate,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    #current_user is email, 
    session_id = redis.get(f"email_to_sessionid:{current_user}")
    session_raw = redis.get(f"sessionid_to_sessiondata:{session_id}")
    if session_raw is None: #then there is no session data for this user
        session_data = {}
    else:
        session_data = json.loads(session_raw)

    current_forecast_name = session_data.get("current_forecast_name","default")
    draft_account_set_serialized = session_data.get("draft_account_set",None)

    if draft_account_set_serialized is None:
        draft_account_set = AccountSet.AccountSet()
        #todo access request data, and create account accordingly
    else:
        pass
        draft_account_set = AccountSet.AccountSet()
        #todo deserialize from string in session_data dict, DONT VALIDATE, and update it (do validate)

    session_data["draft_account_set"] = json.dumps(draft_account_set.to_dict())
    redis.setex(f"sessionid_to_sessiondata:{session_id}", 3600, json.dumps(session_data))
        
    return JSONResponse(
            status_code=200,
            content={"status": "Account created"})

@router.get("/draft/accounts")
async def list_accounts(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    #current_user is email, 
    session_id = redis.get(f"email_to_sessionid:{current_user}")
    session_raw = redis.get(f"sessionid_to_sessiondata:{session_id}")
    if session_raw is None: #then there is no session data for this user
        return JSONResponse(
            status_code=200,
            content={"status": "No accounts"})
    else:
        session_data = json.loads(session_raw)
        draft_account_set_serialized = session_data.get("draft_account_set")
        print('draft_account_set_serialized:')
        print(draft_account_set_serialized)
        draft_account_set = AccountSet.AccountSet.from_json(draft_account_set_serialized)
        return JSONResponse(
                status_code=200,
                content={"status": draft_account_set.to_json()})

# GET     /users/{user_id}/forecasts/{forecast_id}/accounts        ← list accounts
# POST    /users/{user_id}/forecasts/{forecast_id}/accounts        ← create new account
# GET     /accounts/{account_id}                                   ← retrieve one account
# PATCH   /accounts/{account_id}                                   ← update account
# DELETE  /accounts/{account_id}                                   ← delete account

@router.get("/health")
async def health():
    return {"status": "ok"}

def check_redis_connection(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT")):
    try:
        result = subprocess.run(
            ["redis-cli", "-h", host, "-p", str(port), "ping"],
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "PONG"
    except subprocess.CalledProcessError as e:
        print(f"Redis ping failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("redis-cli not found. Make sure Redis is installed and in PATH.")
        return False

def check_postgres_connection(host=os.getenv("POSTGRES_HOST"), 
                              port=os.getenv("POSTGRES_PORT"), 
                              user=os.getenv("POSTGRES_USER"), 
                              dbname=os.getenv("POSTGRES_DBNAME")):
    try:
        result = subprocess.run(
            [
                "psql",
                f"--host={host}",
                f"--port={port}",
                f"--username={user}",
                f"--dbname={dbname}",
                "--command=SELECT 1;"
            ],
            check=True,
            capture_output=True,
            text=True,
            env={"PGPASSWORD": os.getenv("POSTGRES_PASSWORD")}  # Optional: avoid interactive password
        )
        return "1" in result.stdout
    except subprocess.CalledProcessError as e:
        print(f"PostgreSQL ping failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("psql not found. Make sure PostgreSQL client is installed and in PATH.")
        return False

def check_fief_connection(base_url=os.getenv("FIEF_URL")):
    try:
        response = httpx.get(f"{base_url}/.well-known/openid-configuration", timeout=5)
        return response.status_code == 200
    except httpx.RequestError as e:
        print(f"Fief ping failed: {e}")
        return False


@router.get("/ready")
async def ready():
    db_ok = check_postgres_connection()
    redis_ok = check_redis_connection()
    fief_ok = check_fief_connection()

    if db_ok and redis_ok and fief_ok:
        return {"status": "ready"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", 
                     "db": db_ok, 
                     "redis": redis_ok, 
                     "fief": fief_ok}
        )
    


# def verify_fief_api_key(authorization: str = Header(...)) -> dict:
#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Invalid Authorization header")

#     token = authorization.split(" ", 1)[1]

#     response = httpx.post(
#         "http://localhost:8001/api/token/introspect",
#         data={"token": token},
#         auth=("your-client-id", "your-client-secret")  # Only if introspection is protected
#     )

#     if response.status_code != 200 or not response.json().get("active"):
#         raise HTTPException(status_code=401, detail="Invalid token")

#     return response.json()  # contains user_id, scope, etc.


# fief = FiefAsync( 
#     "http://localhost:8000",  # (1)!
#     "_EKEqlT8iLXsr4lE9UbokooFxXORsj2AelqPv0q9Bu0",  # (2)!
#     "DR63yfZCDvVrKa4qp4_JjOEhIrNcZEITXxlxdM5Xvqs",  # (3)!
# )

# scheme = OAuth2AuthorizationCodeBearer(  
#     "http://localhost:8000/authorize",  
#     "http://localhost:8000/api/token",  
#     scopes={"openid": "openid", "offline_access": "offline_access"},
#     auto_error=False,  
# )
# auth = FiefAuth(fief, scheme)  

# @router.get("/user")
# async def get_user(
#     access_token_info: FiefAccessTokenInfo = Depends(
#         auth.authenticated()
#         # auth.authenticated(scope=["openid", "required_scope"])
#     ),
# ):
#     return access_token_info

@router.get("/user")
async def get_user(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token")

    token_info = await fief.introspect_token(access_token)
    return token_info

@router.get("/debug_headers")
async def debug_headers(request: Request):
    return dict(request.headers)

@router.get("/debug_cookie")
async def debug_cookies(request: Request):
    return request.cookies

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class ParameterRow(BaseModel):
    start_date: str
    end_date: str
    forecast_name: str
    approximate: Optional[bool] = False

class AccountRow(BaseModel):
    name: str
    balance: float
    min_balance: Optional[float]
    max_balance: Optional[float]
    type: Literal["checking", "credit", "loan", "investment"]
    billing_start_date: Optional[str]
    interest_type: Optional[str]
    apr: Optional[float]
    interest_cadence: Optional[Literal["daily", "monthly"]]
    minimum_payment: Optional[float]
    primary_checking: Optional[bool] = False

class LineItemRow(BaseModel):
    name: str
    amount: float
    priority: int
    cadence: Literal["once", "daily", "weekly", "semiweekly", "monthly", "quarterly", "yearly"]
    start_date: Optional[str]
    end_date: Optional[str]
    deferrable: bool
    partial_payment_allowed: bool

class DecisionRuleRow(BaseModel):
    memo_regex: str
    priority: int
    account_from: str
    account_to: str

class MilestoneRow(BaseModel):
    milestone_name: str
    account_name: str
    min_balance: Optional[float]
    max_balance: Optional[float]
    memo_regex: Optional[str]
    account_milestone_names: Optional[str]
    memo_milestone_name: Optional[str]

class DraftSubmission(BaseModel):
    parameters: List[ParameterRow]
    accounts: List[AccountRow]
    line_items: List[LineItemRow]
    decision_rules: List[DecisionRuleRow]
    milestones: List[MilestoneRow]

# --- API endpoint with business rule validation ---

@router.post("/draft/submit")
async def submit_draft(draft: DraftSubmission):
    errors = []

    # Business rule: Only one account can be marked as primary checking
    primary_count = sum(1 for a in draft.accounts if a.primary_checking)
    if primary_count > 1:
        errors.append({
            "section": "accounts",
            "field": "primary_checking",
            "message": "Only one account can be set as primary checking"
        })

    # Example: No account can have negative balance
    for i, account in enumerate(draft.accounts):
        if account.balance < 0:
            errors.append({
                "section": "accounts",
                "row": i,
                "field": "balance",
                "message": "Balance cannot be negative"
            })

    # Example: Line item amounts must be positive
    for i, item in enumerate(draft.line_items):
        if item.amount < 0:
            errors.append({
                "section": "line_items",
                "row": i,
                "field": "amount",
                "message": "Amount must be non-negative"
            })

    if errors:
        return {
            "status": "rejected",
            "errors": errors
        }

    # ✅ Passed validation
    return { "status": "accepted" }

# Date,Hume Checking,Hume Credit: Curr Stmt Bal,Hume Credit: Prev Stmt Bal,Hume Credit: Credit Billing Cycle Payment Bal,Hume Credit: Credit End of Prev Cycle Bal,Marginal Interest,Net Gain,Net Loss,Net Worth,Loan Total,CC Debt Total,Liquid Total,Next Income Date,Memo Directives,Memo
@router.get("/view/forecast/sample")
async def get_sample_view_table_data(request: Request):
    return JSONResponse(
            status_code=200,
            content=
            [
    {
        "Date": "2025-04-01",
        "Hume Checking": "214.60",
        "Hume Credit: Curr Stmt Bal": "175.62",
        "Hume Credit: Prev Stmt Bal": "212.66",
        "Hume Credit: Credit Billing Cycle Payment Bal": "308.17",
        "Hume Credit: Credit End of Prev Cycle Bal": "322.86",
        "Marginal Interest": "430.18",
        "Net Gain": "173.85",
        "Net Loss": "457.40",
        "Net Worth": "85.87",
        "Loan Total": "20.01",
        "CC Debt Total": "106.24",
        "Liquid Total": "116.30",
        "Next Income Date": "2025-04-15",
        "Memo Directives": "",
        "Memo": ""
    },
    {
        "Date": "2025-04-02",
        "Hume Checking": "215.54",
        "Hume Credit: Curr Stmt Bal": "248.97",
        "Hume Credit: Prev Stmt Bal": "352.01",
        "Hume Credit: Credit Billing Cycle Payment Bal": "8.34",
        "Hume Credit: Credit End of Prev Cycle Bal": "250.43",
        "Marginal Interest": "421.58",
        "Net Gain": "120.98",
        "Net Loss": "354.76",
        "Net Worth": "258.85",
        "Loan Total": "251.08",
        "CC Debt Total": "336.68",
        "Liquid Total": "225.16",
        "Next Income Date": "2025-04-16",
        "Memo Directives": "",
        "Memo": ""
    },
    {
        "Date": "2025-04-03",
        "Hume Checking": "331.99",
        "Hume Credit: Curr Stmt Bal": "4.83",
        "Hume Credit: Prev Stmt Bal": "104.81",
        "Hume Credit: Credit Billing Cycle Payment Bal": "423.73",
        "Hume Credit: Credit End of Prev Cycle Bal": "431.36",
        "Marginal Interest": "261.66",
        "Net Gain": "430.14",
        "Net Loss": "197.40",
        "Net Worth": "418.20",
        "Loan Total": "79.17",
        "CC Debt Total": "406.52",
        "Liquid Total": "94.07",
        "Next Income Date": "2025-04-17",
        "Memo Directives": "",
        "Memo": ""
    },
    {
        "Date": "2025-04-04",
        "Hume Checking": "245.16",
        "Hume Credit: Curr Stmt Bal": "81.47",
        "Hume Credit: Prev Stmt Bal": "139.83",
        "Hume Credit: Credit Billing Cycle Payment Bal": "217.77",
        "Hume Credit: Credit End of Prev Cycle Bal": "352.94",
        "Marginal Interest": "308.03",
        "Net Gain": "171.60",
        "Net Loss": "492.80",
        "Net Worth": "87.68",
        "Loan Total": "117.61",
        "CC Debt Total": "217.51",
        "Liquid Total": "129.50",
        "Next Income Date": "2025-04-18",
        "Memo Directives": "",
        "Memo": ""
    },
    {
        "Date": "2025-04-05",
        "Hume Checking": "129.16",
        "Hume Credit: Curr Stmt Bal": "346.18",
        "Hume Credit: Prev Stmt Bal": "429.95",
        "Hume Credit: Credit Billing Cycle Payment Bal": "266.06",
        "Hume Credit: Credit End of Prev Cycle Bal": "16.50",
        "Marginal Interest": "428.39",
        "Net Gain": "420.47",
        "Net Loss": "54.86",
        "Net Worth": "299.99",
        "Loan Total": "389.41",
        "CC Debt Total": "203.93",
        "Liquid Total": "103.47",
        "Next Income Date": "2025-04-19",
        "Memo Directives": "",
        "Memo": ""
    }
]
)

@router.get('/view/sankey/sample')
async def get_sample_sankey_table_data(request: Request):
    return JSONResponse(
            status_code=200,
            content=[
                {  
                    "source": "Website",
                    "target": "Sign Up Page",
                    "value": 300
                },
                {  
                    "source": "Sign Up Page",
                    "target": "Completed Signup",
                    "value": 200
                },
                {  
                    "source": "Sign Up Page",
                    "target": "Abandoned",
                    "value": 100
                },
                {  
                    "source": "Website",
                    "target": "Product Page",
                    "value": 500
                },
                {  
                    "source": "Product Page",
                    "target": "Added to Cart",
                    "value": 250
                },
                {  
                    "source": "Product Page",
                    "target": "Bounced",
                    "value": 250
                },
                {  
                    "source": "Added to Cart",
                    "target": "Completed Purchase",
                    "value": 150
                },
                {  
                    "source": "Added to Cart",
                    "target": "Abandoned Cart",
                    "value": 100
                },
            ]
        )

@router.get('/view/lineitem/sample')
async def get_sample_sankey_table_data(request: Request):
    return JSONResponse(
            status_code=200,
            content=
            [{
                "Date": "2025-04-01",
                "Amount": "100.00",
                "Memo": "Income"
            },
            {
                "Date": "2025-04-02",
                "Amount": "50.00",
                "Memo": "Txn 1"
            },
            {
                "Date": "2025-04-03",
                "Amount": "120.00",
                "Memo": "Txn 2"
            }])

@router.get('/view/milestone/sample')
async def get_sample_sankey_table_data(request: Request):
    return JSONResponse(
            status_code=200,
            content=
            [{
                "Name": "Account Milestone 1",
                "Type": "Account",
                "Condition": "account condition"
            },
            {
                "Name": "Memo Milestone 1",
                "Type": "Memo",
                "Condition": "memp condition"
            },
            {
                "Name": "Composite Milestone 1",
                "Type": "Composite",
                "Condition": "composite condition"
            }])


@router.get("/browse/sample")
async def get_sample_browse_table_data(request: Request):
    #   { title: "Forecast Name", field: "name", headerFilter: "input" },
    #   { title: "Start Date", field: "start_date", sorter: "date", headerFilter: "input" },
    #   { title: "End Date", field: "end_date", sorter: "date", headerFilter: "input" },
    #   { title: "Status", field: "status", headerFilter: "list", headerFilterParams: { values: true } },
    #   { title: "Progress", field: "progress", sorter: "string" },
    #   { title: "Start Timestamp", field: "start_timestamp", sorter: "datetime" },
    #   { title: "ETC", field: "etc", sorter: "datetime" }
    return JSONResponse(
            status_code=200,
            content=
            [{  
                "set_name": "",
                "name": "April Forecast",
                "start_date": "2025-04-01",
                "end_date": "2025-04-30",
                "status": "Completed",
                "progress": "100%",
                "start_timestamp": "2025-04-01T08:00:00Z",
                "etc": "2025-04-01T10:30:00Z"
            },
            {
                "set_name": "",
                "name": "May Forecast",
                "start_date": "2025-05-01",
                "end_date": "2025-05-31",
                "status": "Running",
                "progress": "42%",
                "start_timestamp": "2025-05-01T07:45:00Z",
                "etc": "2025-05-01T11:15:00Z"
            },
            {
                "set_name": "",
                "name": "June Forecast",
                "start_date": "2025-06-01",
                "end_date": "2025-06-30",
                "status": "Pending",
                "progress": "0%",
                "start_timestamp": "2025-06-01T09:00:00Z",
                "etc": "2025-06-01T10:00:00Z"
            }
            
            ,
            {
                "set_name": "Test Set",
                "name": "AB",
                "start_date": "2025-06-01",
                "end_date": "2025-06-30",
                "status": "Pending",
                "progress": "0%",
                "start_timestamp": "2025-06-01T09:00:00Z",
                "etc": "2025-06-01T10:00:00Z"
            },
            {
                "set_name": "Test Set",
                "name": "AC",
                "start_date": "2025-06-01",
                "end_date": "2025-06-30",
                "status": "Pending",
                "progress": "0%",
                "start_timestamp": "2025-06-01T09:00:00Z",
                "etc": "2025-06-01T10:00:00Z"
            },
            {
                "set_name": "Test Set",
                "name": "AD",
                "start_date": "2025-06-01",
                "end_date": "2025-06-30",
                "status": "Pending",
                "progress": "0%",
                "start_timestamp": "2025-06-01T09:00:00Z",
                "etc": "2025-06-01T10:00:00Z"
            }
            
            ])
    

@router.get("/draft/parameter/sample")
async def get_sample_draft_account_data(request: Request):
    pass
    #return JSONResponse(
    # status_code=200,
    # content=
    # [{
    #     "name": "April Forecast",
    #     "start_date": "2025-04-01",
    #     "end_date": "2025-04-30",
    #     "status": "Completed",
    #     "progress": "100%",
    #     "start_timestamp": "2025-04-01T08:00:00Z",
    #     "etc": "2025-04-01T10:30:00Z"
    # },
    # {
    #     "name": "May Forecast",
    #     "start_date": "2025-05-01",
    #     "end_date": "2025-05-31",
    #     "status": "Running",
    #     "progress": "42%",
    #     "start_timestamp": "2025-05-01T07:45:00Z",
    #     "etc": "2025-05-01T11:15:00Z"
    # },
    # {
    #     "name": "June Forecast",
    #     "start_date": "2025-06-01",
    #     "end_date": "2025-06-30",
    #     "status": "Pending",
    #     "progress": "0%",
    #     "start_timestamp": "2025-06-01T09:00:00Z",
    #     "etc": "2025-06-01T10:00:00Z"
    # }])

@router.get("/draft/account/sample")
async def get_sample_draft_account_data(request: Request):
    pass
    #return JSONResponse(
    # status_code=200,
    # content=
    # [{
    #     "name": "April Forecast",
    #     "start_date": "2025-04-01",
    #     "end_date": "2025-04-30",
    #     "status": "Completed",
    #     "progress": "100%",
    #     "start_timestamp": "2025-04-01T08:00:00Z",
    #     "etc": "2025-04-01T10:30:00Z"
    # },
    # {
    #     "name": "May Forecast",
    #     "start_date": "2025-05-01",
    #     "end_date": "2025-05-31",
    #     "status": "Running",
    #     "progress": "42%",
    #     "start_timestamp": "2025-05-01T07:45:00Z",
    #     "etc": "2025-05-01T11:15:00Z"
    # },
    # {
    #     "name": "June Forecast",
    #     "start_date": "2025-06-01",
    #     "end_date": "2025-06-30",
    #     "status": "Pending",
    #     "progress": "0%",
    #     "start_timestamp": "2025-06-01T09:00:00Z",
    #     "etc": "2025-06-01T10:00:00Z"
    # }])

@router.get("/draft/lineitem/sample")
async def get_sample_draft_account_data(request: Request):
    pass
    #return JSONResponse(
    # status_code=200,
    # content=
    # [{
    #     "name": "April Forecast",
    #     "start_date": "2025-04-01",
    #     "end_date": "2025-04-30",
    #     "status": "Completed",
    #     "progress": "100%",
    #     "start_timestamp": "2025-04-01T08:00:00Z",
    #     "etc": "2025-04-01T10:30:00Z"
    # },
    # {
    #     "name": "May Forecast",
    #     "start_date": "2025-05-01",
    #     "end_date": "2025-05-31",
    #     "status": "Running",
    #     "progress": "42%",
    #     "start_timestamp": "2025-05-01T07:45:00Z",
    #     "etc": "2025-05-01T11:15:00Z"
    # },
    # {
    #     "name": "June Forecast",
    #     "start_date": "2025-06-01",
    #     "end_date": "2025-06-30",
    #     "status": "Pending",
    #     "progress": "0%",
    #     "start_timestamp": "2025-06-01T09:00:00Z",
    #     "etc": "2025-06-01T10:00:00Z"
    # }])

@router.get("/draft/decisionrule/sample")
async def get_sample_draft_account_data(request: Request):
    pass
    #return JSONResponse(
    # status_code=200,
    # content=
    # [{
    #     "name": "April Forecast",
    #     "start_date": "2025-04-01",
    #     "end_date": "2025-04-30",
    #     "status": "Completed",
    #     "progress": "100%",
    #     "start_timestamp": "2025-04-01T08:00:00Z",
    #     "etc": "2025-04-01T10:30:00Z"
    # },
    # {
    #     "name": "May Forecast",
    #     "start_date": "2025-05-01",
    #     "end_date": "2025-05-31",
    #     "status": "Running",
    #     "progress": "42%",
    #     "start_timestamp": "2025-05-01T07:45:00Z",
    #     "etc": "2025-05-01T11:15:00Z"
    # },
    # {
    #     "name": "June Forecast",
    #     "start_date": "2025-06-01",
    #     "end_date": "2025-06-30",
    #     "status": "Pending",
    #     "progress": "0%",
    #     "start_timestamp": "2025-06-01T09:00:00Z",
    #     "etc": "2025-06-01T10:00:00Z"
    # }])

@router.get("/draft/milestone/sample")
async def get_sample_draft_account_data(request: Request):
    pass
    #return JSONResponse(
    # status_code=200,
    # content=
    # [{
    #     "name": "April Forecast",
    #     "start_date": "2025-04-01",
    #     "end_date": "2025-04-30",
    #     "status": "Completed",
    #     "progress": "100%",
    #     "start_timestamp": "2025-04-01T08:00:00Z",
    #     "etc": "2025-04-01T10:30:00Z"
    # },
    # {
    #     "name": "May Forecast",
    #     "start_date": "2025-05-01",
    #     "end_date": "2025-05-31",
    #     "status": "Running",
    #     "progress": "42%",
    #     "start_timestamp": "2025-05-01T07:45:00Z",
    #     "etc": "2025-05-01T11:15:00Z"
    # },
    # {
    #     "name": "June Forecast",
    #     "start_date": "2025-06-01",
    #     "end_date": "2025-06-30",
    #     "status": "Pending",
    #     "progress": "0%",
    #     "start_timestamp": "2025-06-01T09:00:00Z",
    #     "etc": "2025-06-01T10:00:00Z"
    # }])

# app.include_router(router) #this needs to be at bottom of file