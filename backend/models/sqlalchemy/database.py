from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# DATABASE_URL = "postgresql://hdickie:hoypiloy@postgres:5432/postgres"
DATABASE_URL = "postgresql://fief:fief@postgres:5432/fief"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from models.sqlalchemy.models import Base
