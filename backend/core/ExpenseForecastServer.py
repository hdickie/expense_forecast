
# HumanMiles “Your future called. It’s fine with this.”

from fastapi import Depends, FastAPI
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
from pydantic import BaseModel, Field
import httpx
import subprocess
from dotenv import load_dotenv
import os
from fastapi import Depends, HTTPException, Header
from fief_client import FiefAccessTokenInfo, FiefAsync
from core.AccountSet import AccountSet
from models.account.schemas import AccountCreate
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException
from typing import List, Literal
import logging
from fastapi import APIRouter
from os import getenv
import sys
from core.ExpenseForecast import ExpenseForecast
from core.LineItem import LineItem
from core.LineItemSet import LineItemSet
from core.DecisionRule import DecisionRule
from core.DecisionRuleSet import DecisionRuleSet
from core.MilestoneSet import MilestoneSet

from models.expenseforecast.params import ExpenseForecastParams

from models.account.params import CheckingAccountParams
from models.account.params import CreditCardAccountParams
from models.account.params import LoanAccountParams
from models.account.params import InvestmentAccountParams
from models.lineitem.params import LineItemParams
from models.decisionrule.params import DecisionRuleParams
from models.milestone.params import AccountMilestoneParams
from models.milestone.params import MemoMilestoneParams
from models.milestone.params import CompositeMilestoneParams
from models.expenseforecast.schemas import DraftSubmission

from models.expenseforecast.schemas import User
from models.expenseforecast.schemas import SessionData
from models.expenseforecast.schemas import ForecastSelect
from tasks.submit_forecast import validate_and_submit_draft_task, run_forecast

from datetime import datetime
from models.sqlalchemy.models import ForecastStatusHistoryModel, ForecastStatusModel
from models.sqlalchemy.database import SessionLocal

from fastapi import WebSocket
from celery.result import AsyncResult
import asyncio

load_dotenv(".env") 
logger = logging.getLogger("core.ExpenseForecastServer")

logger.setLevel(logging.INFO)  # Or DEBUG if you want more noise

# Create console handler
handler = logging.StreamHandler(sys.stdout)  # Important! stdout not stderr
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

# Avoid duplicate handlers if code reloads
if not logger.handlers:
    logger.addHandler(handler)

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


auth = FiefAuth(fief, scheme)





# class SessionData(BaseModel):
#     user_id: str
#     forecast_id: str | None = None  # Optional now, can expand later

SESSION_COOKIE_NAME = "session_id"
SESSION_TTL = 3600  # 1 hour


from models.sqlalchemy.database import engine
from sqlalchemy import text

def get_current_user(request: Request):
    # Try cookie first
    logger.info('ENTER get_current_user')
    # logger.info(f'query_params={request.query_params}')
    # user = request.query_params.get("user")
    # logger.info(f'user={user}')
    # 
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id FROM fief_users where email = 'hume.dickie@live.com'"))
        row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        dev_user_uuid = row[0]
    logger.info(f'dev_user_uuid={dev_user_uuid}')
    logger.info('EXIT get_current_user (success)')
    return dev_user_uuid
    # access_token = request.cookies.get('access_token')
    # logger.info(f'access_token:{access_token}')
    
    # # # Try Authorization header second
    # # if not access_token:
    # #     auth_header = request.headers.get('authorization')
    # #     if auth_header and auth_header.startswith('Bearer '):
    # #         access_token = auth_header.split(' ')[1]
    
    # if not access_token:
    #     raise HTTPException(status_code=401, detail="Missing access token")

    # url = f"{os.getenv('FIEF_DOMAIN')}/api/userinfo"
    # headers = {"Authorization": f"Bearer {access_token}"}


    # response = httpx.get(url, headers=headers)
    # logger.info(f'response:{str(response)}')


    # response.raise_for_status()
    # userinfo = response.json()

    # return userinfo["email"] 




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

@router.get("/test-cookie")
async def test_cookie():
    response = RedirectResponse(url="http://expense_forecast.localhost")
    response.set_cookie(
        key="test_cookie",
        value="abc123",
        domain=".localhost",
        httponly=True,
        samesite="lax",  # this will work locally
        secure=False     # this is key for http://localhost
    )
    logger.info(response)
    return response

@router.get("/login", name="login")
async def login(request: Request):
    try:
        # redirect_uri = str(request.url_for("auth_callback"))
        
        discovery_url = f"{getenv('FIEF_INTERNAL_DOMAIN')}/.well-known/openid-configuration"
        

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(discovery_url)
                response.raise_for_status()
            except Exception as e:
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

        return RedirectResponse(auth_url)
    except Exception as e:
        print(e)
        import traceback
        print("🔥 Exception in login():", str(e))
        traceback.print_exc()
        raise e

@router.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request, response: Response): #not sure if i am allowed to take response out of the signature here
    print('ENTER auth_callback')

    response = RedirectResponse(url="http://expense_forecast.localhost/")
    
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    redirect_uri = "http://api.localhost/auth/callback"

    try:
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

            # Set cookie with the access token
        response.set_cookie(
            key="access_token",
            value=token_data.get("access_token"),
            domain=".localhost",   # important: share across subdomains
            httponly=True,
            samesite="none",
            secure=False           # True if you're on HTTPS, False for local dev
        )

        response.set_cookie(key="session_id", 
                            value=session_id, 
                            domain=".localhost",   # important: share across subdomains
                            httponly=True,
                            # samesite="none",
                            secure=False   )
        # print('Set session_id cookie to '+str(session_id))

        redis.setex(f"sessionid_to_sessiondata:{session_id}", 3600, json.dumps(session_data))
        # print('Set session_id -> session data for '+str(session_id))

        redis.setex(f"email_to_sessionid:{userinfo['email']}", 3600, session_id)
        # print('Set Email -> session_id for '+str(userinfo['email'] + ' = '+str(session_id)))
        
        print('EXIT auth_callback (SUCCESS)')
        return response

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
    
    return RedirectResponse(
        url="http://fief.localhost/authorize?client_id=_EKEqlT8iLXsr4lE9UbokooFxXORsj2AelqPv0q9Bu0&redirect_uri=http%3A%2F%2Fapi.localhost%2Fauth%2Fcallback&response_type=code&scope=openid%20email%20profile&prompt=login"
    )



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

# --- API endpoint with business rule validation ---



# @router.post("/draft/submit")
# async def submit_draft(draft: DraftSubmission,
#     current_user: User = Depends(get_current_user)):
#     logger.info('ENTER submit_draft')

#     validation_response = validate_draft_submission(draft)
#     # submitVettedForecast(draft)

#     logger.info(current_user)
#     logger.info(str(draft.parameters))
    
#     # ✅ Passed validation
#     rv = { "status": "accepted" }
#     logger.info(rv)
#     logger.info('EXIT submit_draft')
#     return rv



@router.get("/task/status/{task_id}")
async def check_task_status(task_id: str):
    result = AsyncResult(task_id)

    if result.state == 'PENDING':
        return {"status": "pending"}
    elif result.state == 'SUCCESS':
        return {"status": "success", "result": result.result}
    elif result.state == 'FAILURE':
        return {"status": "failure", "error": str(result.result)}
    else:
        return {"status": result.state.lower()}

@router.websocket("/ws/task_status/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    result = AsyncResult(task_id)

    while True:
        if result.ready():
            if result.successful():
                await websocket.send_json({"status": "success", "result": result.result})
            else:
                await websocket.send_json({"status": "failure", "error": str(result.result)})
            break
        await asyncio.sleep(2)  # wait 2 seconds before checking again

    await websocket.close()

@router.post("/draft/submit")
async def submit_draft(draft: DraftSubmission,
    current_user: User = Depends(get_current_user)):
    
    task = validate_and_submit_draft_task.delay(draft.model_dump(mode="json"))

    return {"task_id": task.id}

   
@router.get("/draft/load")
async def get_draft(current_user: User = Depends(get_current_user)):
    # redis.setex(f"user_to_saved_draft:{current_user}", 3600, json.dumps(draft.dict()))

    draft_data = redis.get(f"user_to_saved_draft:{current_user}")
    return draft_data

@router.post("/draft/save")
async def save_draft(draft: DraftSubmission,
    current_user: User = Depends(get_current_user)):
    logger.info('ENTER save_draft')
    logger.info(f'user:{current_user}')
    logger.info('Current Draft (may be incomplete):')
    logger.info(draft)
    # logger.info(draft.parameters)
    
    redis.setex(f"user_to_saved_draft:{current_user}", 3600, json.dumps(draft.dict()))

    

@router.post("/request-feature")
async def post_request_feature(request: Request):
    raise NotImplementedError

@router.post("/report-problem")
async def post_report_problem(request: Request):
    raise NotImplementedError

@router.post("/report-error")
async def post_report_error(request: Request):
    raise NotImplementedError

# Date,Hume Checking,Hume Credit: Curr Stmt Bal,Hume Credit: Prev Stmt Bal,Hume Credit: Credit Billing Cycle Payment Bal,Hume Credit: Credit End of Prev Cycle Bal,Marginal Interest,Net Gain,Net Loss,Net Worth,Loan Total,CC Debt Total,Liquid Total,Next Income Date,Memo Directives,Memo
@router.get("/view/forecast/sample")
async def get_sample_view_forecast_table_data(request: Request):
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
async def get_sample_view_sankey_data(request: Request):
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
async def get_sample_view_lineitem_table_data(request: Request):
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
async def get_sample_view_milestone_table_data(request: Request):
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


@router.get("/browse/data")
async def get_browse_table_data(request: Request):
    logger.info('ENTER get_browse_table_data')
    logger.info(request)
    return_content = []

    db = SessionLocal()
    rows = db.query(ForecastStatusModel).all()

    return_content = []
    for row in rows:
        return_content.append({
            "stable_id": row.stable_id,
            "name": row.forecast_name,
            "start_date": row.start_date.strftime('%Y-%m-%d'),
            "end_date": row.end_date.strftime('%Y-%m-%d'),
            "status": row.status,
            "start_timestamp": row.start_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "elapsed": str(datetime.now() - row.start_ts), 
        })

    logger.info('return_content:')
    logger.info(return_content)
    ### start_date and end_date are null?
    # [{'stable_id': '250430_4_0_0f99F', 'name': None, 'start_date': None, 'end_date': None, 'status': 'Submitted', 
    # 'start_timestamp': datetime.datetime(2025, 4, 30, 11, 24, 20, 826567), 'elapsed': '-1 day, 23:59:55.018944'}]
    db.close()

    logger.info('EXIT get_browse_table_data')
    return JSONResponse(
        status_code=200,
        content=return_content
    )

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
async def get_sample_draft_parameter_data(request: Request):
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
async def get_sample_draft_lineitem_data(request: Request):
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
async def get_sample_draft_decisionrule_data(request: Request):
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
async def get_sample_draft_milestone_data(request: Request):
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

@router.post("/draft/run/{forecast_id}")
async def run_forecast_endpoint(
    forecast_id: str,
    current_user: User = Depends(get_current_user),
):
    task = run_forecast.delay(current_user, forecast_id)
    return {"task_id": task.id}


@router.get("/draft/parameter/{user_id}")
async def get_user_draft_parameter_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError

@router.get("/draft/account/{user_id}")
async def get_user_draft_account_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError

@router.get("/draft/lineitem/{user_id}")
async def get_user_draft_account_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError

@router.get("/draft/decisionrule/{user_id}")
async def get_user_draft_account_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError

@router.get("/draft/milestone/{user_id}")
async def get_user_draft_account_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError


@router.get("/browse/{user_id}")
async def get_user_browse_forecast_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError


@router.get("/view/forecast/{user_id}/{forecast_id}")
async def get_user_view_forecast_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError

@router.get("/view/sankey/{user_id}/{forecast_id}")
async def get_user_view_sankey_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError

@router.get("/view/milestone/{user_id}/{forecast_id}")
async def get_user_view_milestone_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError
  
@router.get("/view/lineitem/{user_id}/{forecast_id}")
async def get_user_view_lineitem_data(request: Request,
    current_user: User = Depends(get_current_user)):
    raise NotImplementedError
  

# app.include_router(router) #this needs to be at bottom of file

