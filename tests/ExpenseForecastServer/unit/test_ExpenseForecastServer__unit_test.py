# import pytest
# import subprocess
# import ForecastRunner
# import AccountSet
# import BudgetSet
# import MemoRuleSet
# import MilestoneSet
# import ExpenseForecast
# import ForecastHandler
# import os
# import concurrent.futures
# import datetime
# from time import sleep
#
# class TestForecastRunnerMethods:
#
#
#     @pytest.mark.parametrize('param1,param2',
#                              [('param1','param2'),
#                               ])
#     def test_start_forecast(self, param1,param2):
#         start_date = datetime.datetime.now().strftime('%Y%m%d')
#         end_date = '20240430'
#         start_date2 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date2 = '20240501'
#         start_date3 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date3 = '20240502'
#         start_date4 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date4 = '20240503'
#         start_date5 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date5 = '20240504'
#
#         A = AccountSet.AccountSet([])
#         B = BudgetSet.BudgetSet([])
#         M = MemoRuleSet.MemoRuleSet([])
#
#         A.createCheckingAccount('Checking', 5000, 0, 99999)
#         B.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food', False, False)
#         M.addMemoRule('.*', 'Checking', 'None', 1)
#
#         MS = MilestoneSet.MilestoneSet([], [], [])
#         E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date, end_date, MS)
#         E2 = ExpenseForecast.ExpenseForecast(A, B, M, start_date2, end_date2, MS)
#         E3 = ExpenseForecast.ExpenseForecast(A, B, M, start_date3, end_date3, MS)
#         E4 = ExpenseForecast.ExpenseForecast(A, B, M, start_date4, end_date4, MS)
#         E5 = ExpenseForecast.ExpenseForecast(A, B, M, start_date5, end_date5, MS)
#
#         R = ForecastRunner.ForecastRunner('/Users/hume/Github/expense_forecast/lock/')
#         R.start_forecast(E1)
#         R.start_forecast(E2)
#         R.start_forecast(E3)
#         R.start_forecast(E4)
#         R.start_forecast(E5)
#
#         R.ps()
#         sleep(5)
#         R.cancel('049833')
#         R.ps()




# class TestForecastRunnerMethods:
#     @pytest.mark.parametrize('param1,param2',
#                              [('param1','param2'),
#                               ])
#     def test_start_forecast(self, param1,param2):
#         start_date = datetime.datetime.now().strftime('%Y%m%d')




import pytest
from logging_config import setup_logging
from dotenv import load_dotenv
import os
import httpx
from redis import Redis
import psycopg2
import datetime

from pathlib import Path
# load_dotenv(Path(__file__).resolve().parents[2] / ".env")

load_dotenv('.env') #assumes tests are called from project root...
redis = Redis(host=os.getenv("REDIS_HOST"), 
              port=os.getenv("REDIS_PORT"), 
              db=0, 
              decode_responses=True)

@pytest.fixture(scope="session", autouse=True)
def init_logging():
    """Set up colorized, structured logging once for all tests."""
    log_dir = Path("logs/test_runs")
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"test_run_{timestamp}.log"

    setup_logging(log_file=log_file)

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


@pytest.fixture(scope="session", autouse=True)
def clean_test_db():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DBNAME"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # # ⚠️ Drop only test-related tables or rows!
    # cursor.execute("""
    #     DELETE FROM accounts;
    #     DELETE FROM forecasts;
    #     -- or TRUNCATE TABLE accounts CASCADE;
    # """)

    # print("✅ Test DB cleaned")

    # yield  # Run the test suite

    # # Optionally, clean again after tests
    # cursor.execute("""
    #     DELETE FROM accounts;
    #     DELETE FROM forecasts;
    # """)

    cursor.close()
    conn.close()


    
class TestExpenseForecastServerMethods:
    def test_ready(self):
        response = httpx.get(os.getenv("API_URL")+"/ready")
        assert response.status_code == 200

    def test_healthy(self):
        response = httpx.get(os.getenv("API_URL")+"/health")
        assert response.status_code == 200

    def test_authenticated(self):
        session_id = redis.get(f"email:{os.getenv('TEST_USER_EMAIL')}")
        response = httpx.get(os.getenv("API_URL")+"/me", cookies={"session_id": session_id})
        if response.status_code == 401:
            print("Probably not authenticated. Visit localhost:8001/login to login.")
            print(response.text)
        assert response.status_code == 200

    