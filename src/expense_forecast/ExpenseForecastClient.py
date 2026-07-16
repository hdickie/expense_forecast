"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""



#TODO DEFER manual review of ExpenseForecastClient docstring
class ExpenseForecastClient:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DEFER manual review of ExpenseForecastClient.__init__ docstring
    def __init__(self):
        """
        #TODO DEFER one-line description of ExpenseForecastClient.__init__.

        #TODO DEFER multi-line description of ExpenseForecastClient.__init__.
        #TODO DEFER explain how ExpenseForecastClient.__init__ participates in this module.
        #TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DEFER confirm that ExpenseForecastClient.__init__ takes no parameters beyond self/cls.

        Returns
        -------
        None
            #TODO DEFER one-line description of return value of ExpenseForecastClient.__init__.

        Contract
        --------
        - #TODO DEFER contract lines for ExpenseForecastClient.__init__.
        - #TODO DEFER document exceptions, mutations, and precision assumptions for ExpenseForecastClient.__init__.

        @interface-report: show
        """
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
