
# import ExpenseForecastCLient
import httpx
# from core import ExpenseForecast
import asyncio
from redis import Redis
import psycopg2
import os
import json
test_user_email = 'hume.dickie@live.com'

FIEF_ACCESS_TOKEN = "FkqVQ0U1g96cgNF8HUTKxhQRqIu9HINFHT90j0_sU74"  # Replace with actual token
FIEF_BASE_URL = "http://localhost:8000"

redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)

def test_login_and_fetch_me():
    # Step 1: Authenticate with Fief token
    headers = {
        "Authorization": f"Bearer {FIEF_ACCESS_TOKEN}"
    }

    login_response = httpx.post(f"{FIEF_BASE_URL}/login", headers=headers)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    # Extract the session cookie
    cookies = login_response.cookies
    session_cookie = cookies.get("session_id")
    assert session_cookie is not None, "No session cookie set"

    # Step 2: Use the session cookie to call /me
    me_response = httpx.get(f"{FIEF_BASE_URL}/me", cookies={"session_id": session_cookie})
    assert me_response.status_code == 200, f"Session invalid: {me_response.text}"

    print("User session:", me_response.json())

#assumes a valid session is active and accesible via redis
async def test_post_select_forecast():
    # print('ENTER test')
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:

        session_id = redis.get(f"email:{test_user_email}")
        session_data = redis.get(f"session:{session_id}")


        # print(f'test_user_email:{test_user_email}')
        # print(f'session:{session_id}')

        assert session_data is not None, "No session data set"

        response = await client.post(
            "/forecast/current",
            json={"forecast_name": 'test forecast name'},  # 👈 value is string
            cookies={"session_id": session_id}   # 👈 for auth, if needed
        )
        # print(f'response.status_code:{response.status_code}')
        assert response.status_code == 200
        print(response.text)

async def test_get_select_forecast():
    # print('ENTER test')
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:

        session_id = redis.get(f"email:{test_user_email}")
        session_data = redis.get(f"session:{session_id}")

        # print(f"session_id:{session_id}")
        # print(f"session_data:{session_data}")
        # print(f'test_user_email:{test_user_email}')
        # print(f'session:{session_id}')

        assert session_data is not None, "No session data set"

        response = await client.get(
            "/forecast/current",
            cookies={"session_id": session_id}   # 👈 for auth, if needed
        )
        # print(f'response.status_code:{response.status_code}')
        assert response.status_code == 200
        print(response.text)

async def test_create_account():
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        
        session_id = redis.get(f"email:{test_user_email}")
        session_data = redis.get(f"session:{session_id}")

        # @app.get("/users/{user_id}/forecasts/{forecast_id}/accounts")
        response = await client.post(
            "/forecast/current",
            json={"forecast_name": 'test forecast name'},  # 👈 value is string
            cookies={"session_id": session_id}   # 👈 for auth, if needed
        )
        # print(f'response.status_code:{response.status_code}')
        assert response.status_code == 200
        print(response.text)


import ExpenseForecastClient

# Run manually for now
if __name__ == "__main__":
    pass
    # asyncio.run(test_get_select_forecast())
    # action = 'check api for failing endpoints'

    # if action == 'check api for failing endpoints':
    #     schema = httpx.get(os.getenv("API_URL")+"/openapi.json").json()

    #     for path, methods in schema["paths"].items():
    #         for method, config in methods.items():
    #             print(method, config)
    #             if "responses" not in config or "200" not in config["responses"]:
    #                 print(f"⚠️ Missing response_model in {method.upper()} {path}")

    # API_KEY='w47laO07YYmGAddvYkoQt0VydnNfrEFu0ey02oRS5jI'
    # client = ExpenseForecastClient.ExpenseForecastClient()

    # url =  "HTTP://localhost:8000/authorize"
    # cookies = {
    #     "session_id": "abc123",
    #     "user_pref": "dark_mode"
    # }
    # cookies = {}

    # headers = {"Authorization": "Bearer "+self.API_KEY}
    # headers = {}

    # json_body = {
    #     "name": "Test User",
    #     "email": "test@example.com"
    # }
    # json_body = {}

    # response = httpx.post(url, headers=headers, cookies=cookies, json=json_body)
    # response = httpx.get(url)
    # print(response)
    # print(dir(response))

    # # You can list or check existing clients first
    # # existing = httpx.get(f"{FIEF_DOMAIN}/admin/clients/", headers=headers)
    # url = "http://localhost:8000/admin/api/clients/?limit=10&skip=0"
    # response = httpx.get(url, headers=headers)
    # print(response)
    # print(json.dumps(response.json(),indent=4))

    access_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImVIVHBVZkk5QU9QS2RLa2JBOThHZkNnY0ZzUmI0REVrYlp2LUdzeHVjOUUifQ.eyJhY3IiOiIwIiwiYXVkIjpbIl9FS0VxbFQ4aUxYc3I0bEU5VWJva29vRnhYT1JzajJBZWxxUHYwcTlCdTAiXSwiYXV0aF90aW1lIjoxNzQ0Mjc0NTc4LCJhenAiOiJfRUtFcWxUOGlMWHNyNGxFOVVib2tvb0Z4WE9Sc2oyQWVscVB2MHE5QnUwIiwiZXhwIjoxNzQ0MzYxNDAwLCJpYXQiOjE3NDQyNzUwMDAsImlzcyI6Imh0dHBzOi8vbG9jYWxob3N0OjgwMDAiLCJwZXJtaXNzaW9ucyI6WyJmaWVmOmFkbWluIl0sInNjb3BlIjoib3BlbmlkIG9mZmxpbmVfYWNjZXNzIHByb2ZpbGUgZW1haWwiLCJzdWIiOiI3MmIxNjIxNy05MjQyLTQwNGQtOTdkMi02ZWY0ZGRiOWQ2NWYifQ.hr830uTBMzgzwEcLuRThnXMYtNiTi_XxxtnXTL8brlNwD--vceUW4HEScF-pAtRzqft_OTWfKgzl0FRn7aSsFzJGeXIEU-gqPH-w4RSblcOQc64LmFJl0BHeILb6vwJZcV5nfW9ZyDCdB9QMb0A8DI0_MwQcuRNTHOX5R7pO2hXY_oAzNowyUkrvXvagOpIOrrKAhRIoTKj7CkOnoTTaEXxvKc4rNSB5t3KS9Gl6WJt949eM0MtH0lzqXgvLN0B9aekBUBY8-TvIDacWXSLzsz7mPtT1oaTUkypFTtLxTM4lFR24XtXdYSj-wHOIN37M3kC2Mo0OQAuysHte0S00KUOgo9PRte5A7DD6QEmYwhfbG3DQwg1tWI9tQf8Yv0HqTrBv8MYbG0Zi5hUJaxG3RWipIafsCHrJcOIb6Ebbnd2j1HG34WzmAjjif6VjEOTnqrY7myvfp8-bm27K5Li2CwhF0asxb9Gj4gjYRT_Ua6FPO9oU_VfBczGcV0sO42AXCwmMHNpkuIryUSecASDhryYB5-VgqRwmlFQAHxxD_iE5gike0fyWsCB9JQ1grWPphIfzkyme_hbWN5kfcX7ysue5W_7A1hecDHgj-gCCrKp0W1Z4-XIUEF2_flsGXqJWtLQ3jsViACgXAdJSim2y4n7VtCdI_RCARUt3ySJ3tI8"
    client = ExpenseForecastClient.ExpenseForecastClient(access_token)
    client.createAccount(account_name='Checking', 
                             balance=50, 
                             min_balance=0, 
                             max_balance='inf', 
                             account_type='checking')

    current_draft_accounts = client.listAccounts() #no name parameter assumes the draft account set
    print(current_draft_accounts)

