import pytest
from core.ExpenseForecastClient import ExpenseForecastClient
import os
import redis
import httpx


import logging
logger = logging.getLogger("test.integration.Draft")

@pytest.fixture(scope="session", autouse=True)
def delete_redis_test_data():
    r = redis.Redis(host='localhost', port=6379, db=0) #todo use os.getenv
    # r.delete("some_key")

    # session_id = redis.get(f"email_to_sessionid:{current_user}")
    # session_raw = redis.get(f"sessionid_to_sessiondata:{session_id}")


@pytest.fixture(scope="session", autouse=True)
def wait_until_ready():
    """
    Run once per test session to confirm that the app is ready.
    Fails early if dependencies are down.
    """

    assert os.getenv("API_URL") is not None

    try:
        response = httpx.get(os.getenv("API_URL") + "/ready")
    except Exception as e:
        print("Server is probably not running. Start it with: uvicorn core.ExpenseForecastServer:app --reload --port 8001")
        raise e
    
    if response.status_code != 200:
        print("Readiness check failed.")
        print("Status code:", response.status_code)
        print("Response body:", response.text)  # safer than .json() for debugging
        assert False, "Readiness check failed"


@pytest.fixture(scope="session")
def get_expense_forecast_client():
    #copy paste from /login response
    access_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImVIVHBVZkk5QU9QS2RLa2JBOThHZkNnY0ZzUmI0REVrYlp2LUdzeHVjOUUifQ.eyJhY3IiOiIwIiwiYXVkIjpbIl9FS0VxbFQ4aUxYc3I0bEU5VWJva29vRnhYT1JzajJBZWxxUHYwcTlCdTAiXSwiYXV0aF90aW1lIjoxNzQ0Mjc0NTc4LCJhenAiOiJfRUtFcWxUOGlMWHNyNGxFOVVib2tvb0Z4WE9Sc2oyQWVscVB2MHE5QnUwIiwiZXhwIjoxNzQ0MzYxNDAwLCJpYXQiOjE3NDQyNzUwMDAsImlzcyI6Imh0dHBzOi8vbG9jYWxob3N0OjgwMDAiLCJwZXJtaXNzaW9ucyI6WyJmaWVmOmFkbWluIl0sInNjb3BlIjoib3BlbmlkIG9mZmxpbmVfYWNjZXNzIHByb2ZpbGUgZW1haWwiLCJzdWIiOiI3MmIxNjIxNy05MjQyLTQwNGQtOTdkMi02ZWY0ZGRiOWQ2NWYifQ.hr830uTBMzgzwEcLuRThnXMYtNiTi_XxxtnXTL8brlNwD--vceUW4HEScF-pAtRzqft_OTWfKgzl0FRn7aSsFzJGeXIEU-gqPH-w4RSblcOQc64LmFJl0BHeILb6vwJZcV5nfW9ZyDCdB9QMb0A8DI0_MwQcuRNTHOX5R7pO2hXY_oAzNowyUkrvXvagOpIOrrKAhRIoTKj7CkOnoTTaEXxvKc4rNSB5t3KS9Gl6WJt949eM0MtH0lzqXgvLN0B9aekBUBY8-TvIDacWXSLzsz7mPtT1oaTUkypFTtLxTM4lFR24XtXdYSj-wHOIN37M3kC2Mo0OQAuysHte0S00KUOgo9PRte5A7DD6QEmYwhfbG3DQwg1tWI9tQf8Yv0HqTrBv8MYbG0Zi5hUJaxG3RWipIafsCHrJcOIb6Ebbnd2j1HG34WzmAjjif6VjEOTnqrY7myvfp8-bm27K5Li2CwhF0asxb9Gj4gjYRT_Ua6FPO9oU_VfBczGcV0sO42AXCwmMHNpkuIryUSecASDhryYB5-VgqRwmlFQAHxxD_iE5gike0fyWsCB9JQ1grWPphIfzkyme_hbWN5kfcX7ysue5W_7A1hecDHgj-gCCrKp0W1Z4-XIUEF2_flsGXqJWtLQ3jsViACgXAdJSim2y4n7VtCdI_RCARUt3ySJ3tI8"
    client = ExpenseForecastClient(access_token)
    return client

class TestDraftIntegration:

    @pytest.mark.integration
    def test_create_draft_account_no_forecast_name_no_other_accounts(self, get_expense_forecast_client):
        client = get_expense_forecast_client
        client.createAccount(account_name='Checking', 
                             balance=50, 
                             min_balance=0, 
                             max_balance='inf', 
                             account_type='checking')

        current_draft_accounts = client.listAccounts() #no name parameter assumes the draft account set
        print(current_draft_accounts)

        raise NotImplementedError