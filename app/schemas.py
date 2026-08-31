from pydantic import BaseModel, EmailStr
from datetime import datetime
from .models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    wallet_balance: float
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"