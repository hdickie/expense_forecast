
class ExpenseForecastClient:

    def __init__(self):
        pass

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