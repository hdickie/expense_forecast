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
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Literal
import subprocess
from dotenv import load_dotenv
import os


from . import AccountSet

load_dotenv(".env") 

import logging
logger = logging.getLogger("core.ExpenseForecastServer")


# 400 Bad Request - This means that client-side input fails validation.
# 401 Unauthorized - This means the user isn't not authorized to access a resource. It usually returns when the user isn't authenticated.
# 403 Forbidden - This means the user is authenticated, but it's not allowed to access a resource.
# 404 Not Found - This indicates that a resource is not found.
# 500 Internal server error - This is a generic server error. It probably shouldn't be thrown explicitly.
# 502 Bad Gateway - This indicates an invalid response from an upstream server.
# 503 Service Unavailable - This indicates that something unexpected happened on server side (It can be anything like server overload, some parts of the system failed, etc.).

# fast-api cache

# have version in the request path


app = FastAPI()
router = APIRouter()
redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
SESSION_COOKIE_NAME = "session_id"

class SessionData(BaseModel):
    user_id: str
    forecast_id: Optional[str] = None

fief = FiefAsync(
    "http://localhost:8000",         # Fief server
    "_EKEqlT8iLXsr4lE9UbokooFxXORsj2AelqPv0q9Bu0",  # Replace this!
    "DR63yfZCDvVrKa4qp4_JjOEhIrNcZEITXxlxdM5Xvqs"
)

scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="http://localhost:8000/authorize",
    tokenUrl="http://localhost:8000/api/token",
    scopes={"openid": "openid", "offline_access": "offline_access"},
    auto_error=False,
)

auth = FiefAuth(fief, scheme)



app = FastAPI()
app.state = {} #non-persistent memory for dev use. Comment out for prod

app.state["accounts"] = []

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
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    session_raw = redis.get(f"session:{session_id}")
    if not session_raw:
        raise HTTPException(status_code=401, detail="Session expired")

    session_data = json.loads(session_raw)
    uname = session_data["userinfo"]["email"]
    return User(username=uname)

def get_session_data(request: Request) -> SessionData:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="Missing session")

    session_raw = redis.get(session_id)
    if not session_raw:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    return json.loads(session_raw)
    #return SessionData.parse_raw(session_raw)


    
@router.get("/me")
def get_me(request: Request):
    # print('Cookies:')
    # print(request.cookies)
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Missing session ID")

    raw = redis.get(f"session:{session_id}")
    if not raw:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # session = SessionData.parse_raw(raw)
    # return {"user_id": session.user_id, "email": session.email}
    return json.loads(raw)


@router.get("/login")
async def login():
    redirect_uri = "http://localhost:8001/auth/callback"
    auth_url = await fief.auth_url(
        redirect_uri=redirect_uri,
        scope=["openid", "offline_access"]
    )
    return RedirectResponse(auth_url)

@router.get("/auth/callback")
async def auth_callback(request: Request, response: Response):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    redirect_uri = "http://localhost:8001/auth/callback"

    try:

        token, userinfo = await fief.auth_callback(code, redirect_uri)

        userinfo = await fief.userinfo(token["access_token"])

        # Store the token or create a session here

        session_id = str(uuid4())
        session_data = {    
            "userinfo": userinfo,
            "session_id": session_id,
            "access_token": token["access_token"],
            "created_at": datetime.datetime.utcnow().isoformat(),
            "expires_at": token.get("expires_at")  # optional
        }

        response.set_cookie("session_id", session_id, httponly=True)
        print('Set session_id cookie to '+str(session_id))

        redis.setex(f"session:{session_id}", 3600, json.dumps(session_data))
        print('Set session_id -> session data for '+str(session_id))

        redis.setex(f"email:{userinfo["email"]}", 3600, session_id)
        print('Set Email -> session_id for '+str(userinfo['email'] + ' = '+str(session_id)))
        

        

        return session_data

    except Exception as e:
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
@router.post("/ping")
async def ping(request: Request):
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

from typing import Union

AccountCreate = Union[
    CheckingAccountCreate,
    CreditAccountCreate,
    # Add others
]


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
    session_id = request.cookies.get("session_id")
    session_raw = redis.get(f"session:{session_id}")
    session_data = json.loads(session_raw)

    current_forecast_name = session_data.get("current_forecast_name","default")
    draft_account_set = session_data.get("draft_account_set",None)
    if draft_account_set is None:
        account_set = AccountSet.AccountSet()
    else:
        pass
    
    return {"message": "Account created", "data": account.dict()}

# GET     /users/{user_id}/forecasts/{forecast_id}/accounts        ← list accounts
# POST    /users/{user_id}/forecasts/{forecast_id}/accounts        ← create new account
# GET     /accounts/{account_id}                                   ← retrieve one account
# PATCH   /accounts/{account_id}                                   ← update account
# DELETE  /accounts/{account_id}                                   ← delete account

@app.get("/health")
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

import httpx


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
    
app.include_router(router) #this needs to be at bottom of file