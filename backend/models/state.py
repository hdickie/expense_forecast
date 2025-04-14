# backend/models/state.py
from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime

class UserState(BaseModel):
    id: UUID4
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # So we can pass in SQLAlchemy objects directly
