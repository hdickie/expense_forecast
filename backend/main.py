from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
from core.ExpenseForecastServer import router
from fastapi.responses import JSONResponse
from fastapi import Request

logger = logging.getLogger("uvicorn.error")

# if __name__ == '__main__':
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

 #this allows cross origin resource sharing
# Headers from Origin: http://expense_forecast.localhost sent to api.localhost 
# will be blocked without this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://expense_forecast.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Server must respond with:
# Access-Control-Allow-Origin: http://expense_forecast.localhost
# Access-Control-Allow-Credentials: true  # Only if cookies/auth are involved
# and optionally
# Access-Control-Allow-Methods: POST, GET, OPTIONS
# Access-Control-Allow-Headers: X-CSRF-Token, Content-Type


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.include_router(router)