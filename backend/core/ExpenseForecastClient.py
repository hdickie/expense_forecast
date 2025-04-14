# from fief_client import Fief


# "Your API almost always has to send a response body. But clients don't necessarily
# need to send request bodies all the time, sometimes they only request a path,
# maybe with some query parameters, but don't send a body."

# 1. Submitting/Updating Data or Creating Resources
# 2. Sending Complex Query Parameters
# 3. Authentication

# GET retrieves resources.
# POST submits new data to the server.
# PUT updates existing data.
# DELETE removes data.

# GET ExpenseForecast ?
# GET ExpenseForecast/AccountSet etc.
# GET ForecastResult

# For example, suppose you wanted to return the author of particular comments.
# You could use /articles/:articleId/comments/:commentId/author. But that's getting out of hand.
# Instead, return the URI for that particular user within the JSON response instead:
# "author": "/users/:userId"

# filter and use pagination

# SSL certificates??

# # fief = Fief(
# #     "https://fief.expenseforecast.com",  # (1)!
# #     "YOUR_CLIENT_ID",  # (2)!
# #     "YOUR_CLIENT_SECRET",  # (3)!
# # )

# # redirect_url = "http://localhost:8000/callback"

# # auth_url = fief.auth_url(redirect_url, scope=["openid"])
# # print(f"Open this URL in your browser: {auth_url}")

# # code = input("Paste the callback code: ")

# # tokens, userinfo = fief.auth_callback(code, redirect_url)
# # print(f"Tokens: {tokens}")
# # print(f"Userinfo: {userinfo}")

import httpx

class ExpenseForecastClient:

    def __init__(self,
                access_token,
                 API_HOST="localhost",
                API_PORT=8001):
        self.BASE_URL="http://"+str(API_HOST)+":"+str(8001)
        self.access_token = access_token
        # self.API_KEY=API_KEY
        # response = httpx.get(
        #     "http://localhost:8000/admin/api/users/",
        #     headers={"Authorization": "Bearer "+self.API_KEY}
        # )
        # assert response.status_code == 200 #if not then api key does not work

    def post_with_session(
        url: str,
        json_body: dict,
        session_id: str,
        timeout: float = 5.0
    ) -> httpx.Response:
        try:
            client = httpx.Client(timeout=timeout, cookies={"session_id": session_id})
            response = client.post(url, json=json_body)

            if response.status_code == 200:
                return response

            # Known client-side or validation error
            elif response.status_code == 400:
                raise ValueError(f"Bad request: {response.json()}")

            elif response.status_code == 401:
                raise PermissionError("Unauthorized: Session may be invalid or expired")

            elif response.status_code == 422:
                raise ValueError(f"Unprocessable input: {response.json()}")

            else:
                raise RuntimeError(
                    f"Unexpected status code {response.status_code}: {response.text}"
                )

        except httpx.RequestError as e:
            raise ConnectionError(f"HTTP request failed: {e}")

        except Exception as e:
            raise RuntimeError(f"Unexpected error during request: {e}")


    def createAccount(self, account_name, balance, min_balance, max_balance, account_type):
        url = "http://localhost:8000/api/userinfo"
        headers = {"Authorization": "Bearer "+self.access_token}
        response = httpx.post(url, headers=headers, follow_redirects=True)

        json_body = {
            "name": account_name,
            "balance": balance,
                "min_balance": min_balance,
                "max_balance": max_balance,
                "account_type": account_type
        }
        
        cookies = {}
        url =  self.BASE_URL+"/draft/accounts"
        response = httpx.post(url, headers=headers, cookies=cookies, json=json_body)
        # print(response)
        assert response.status_code == 200

    def listAccounts(self):
        url =  self.BASE_URL+"/draft/accounts"
        headers = {"Authorization": "Bearer "+self.access_token}
        response = httpx.get(url, headers=headers, follow_redirects=True)

        # json_body = {
        #     "name": account_name,
        #     "balance": balance,
        #         "min_balance": min_balance,
        #         "max_balance": max_balance,
        #         "account_type": account_type
        # }
        # json_body = {}
        
        # cookies = {}
        # response = httpx.post(url, headers=headers, cookies=cookies, json=json_body)
        # print(response)
        # print(response.text)
        # print(response.json())
        assert response.status_code == 200
        return response.json()