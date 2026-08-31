from pydantic import BaseModel, EmailStr
from datetime import datetime
from .models import UserRole

from .models import CropStatus



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





class CropCreate(BaseModel):
    crop_name: str
    expected_yield_kg: float
    cost_needed: float


class CropOut(BaseModel):
    id: int
    farmer_id: int
    crop_name: str
    expected_yield_kg: float
    cost_needed: float
    price_per_kg: float
    qty_sold_kg: float
    status: CropStatus
    actual_yield_kg: float | None
    quality_grade: str | None
    fulfillment_ratio: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class HarvestRecord(BaseModel):
    actual_yield_kg: float
    quality_grade: str