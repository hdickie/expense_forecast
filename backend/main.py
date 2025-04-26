from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
from core.ExpenseForecastServer import router
from fastapi.responses import JSONResponse
from fastapi import Request
import sys
import traceback
import os
from sqlalchemy import inspect
from models.sqlalchemy.database import SessionLocal
from models.sqlalchemy.database import Base, engine
from models.sqlalchemy.models import User
from sqlalchemy import text

from contextlib import asynccontextmanager

# # "Hey! Treat the parent folder (expense_forecast/) as a module root. You can import backend now."
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("main")
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 👇 This happens when the app STARTS
    logger.info("Tables SQLAlchemy knows about:")
    for table_name, table_obj in Base.metadata.tables.items():
        logger.info(f"Table: {table_name}")


    # Confirm Base metadata
    logger.info("✅ SQLAlchemy Base Metadata Tables:")
    for table_name in Base.metadata.tables.keys():
        logger.info(f" - {table_name}")

    # Try real inspection too
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    logger.info(f"✅ Tables currently existing in database: {existing_tables}")

    import models.sqlalchemy.models
    Base.metadata.create_all(bind=engine)

    # Load Fief users
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id, email FROM fief_users"))
        fief_users = result.fetchall()

    logger.info(f"✅ Loaded {len(fief_users)} users from Fief.")

    # Insert into your app's `users` table
    db = SessionLocal()
    for fief_user in fief_users:
        user_id = str(fief_user.id)  # Fief user ids are UUIDs
        email = fief_user.email
        logger.info((email, user_id))

        # Check if user already exists
        existing_user = db.query(User).filter(User.id == user_id).first()
        if not existing_user:
            new_user = User(
                id=user_id,  # If your User model uses UUIDs
                email=email,
            )
            db.add(new_user)
    db.commit()
    db.close()
    
    yield  # ⬅️ This lets the app start running normally
    
    # 👇 (optional) This happens when the app is SHUTTING DOWN
    logger.info("App is shutting down")

# Then pass lifespan=lifespan to FastAPI instance
app = FastAPI(lifespan=lifespan)

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

async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.TracebackException.from_exception(exc)
    # Get the last call in the traceback (most recent frame where the error occurred)
    last_frame = tb.stack[-1] if tb.stack else None

    error_location = {
        "file": last_frame.filename if last_frame else "unknown",
        "line": last_frame.lineno if last_frame else "unknown",
        "function": last_frame.name if last_frame else "unknown"
    }

    logging.error(f"Unhandled exception in {error_location['file']} line {error_location['line']} → {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "file": error_location["file"],
            "line": error_location["line"],
            "function": error_location["function"],
            "traceback": "".join(tb.format())
        }
    )
app.include_router(router)

