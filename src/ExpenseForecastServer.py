



class ExpenseForecastServer:

    def __init__(self):
        pass

    # 400 Bad Request - This means that client-side input fails validation.
    # 401 Unauthorized - This means the user isn't not authorized to access a resource. It usually returns when the user isn't authenticated.
    # 403 Forbidden - This means the user is authenticated, but it's not allowed to access a resource.
    # 404 Not Found - This indicates that a resource is not found.
    # 500 Internal server error - This is a generic server error. It probably shouldn't be thrown explicitly.
    # 502 Bad Gateway - This indicates an invalid response from an upstream server.
    # 503 Service Unavailable - This indicates that something unexpected happened on server side (It can be anything like server overload, some parts of the system failed, etc.).

    # fast-api cache

    # have version in the request path