
# import ExpenseForecastCLient
import httpx
import ExpenseForecast
import asyncio
from redis import Redis
import psycopg2
import os

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


# Run manually for now
if __name__ == "__main__":
    pass
    # asyncio.run(test_get_select_forecast())
    action = 'check api for failing endpoints'

    if action == 'check api for failing endpoints':
        schema = httpx.get(os.getenv("API_URL")+"/openapi.json").json()

        for path, methods in schema["paths"].items():
            for method, config in methods.items():
                print(method, config)
                if "responses" not in config or "200" not in config["responses"]:
                    print(f"⚠️ Missing response_model in {method.upper()} {path}")
