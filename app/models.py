import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
)
from sqlalchemy.orm import relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    farmer = "farmer"
    customer = "customer"


class CropStatus(str, enum.Enum):
    open = "open"
    funded = "funded"
    harvested = "harvested"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    wallet_balance = Column(Float, default=100000.0)
    created_at = Column(DateTime, default=utcnow)

    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    purchases = relationship("Purchase", back_populates="customer")


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    village = Column(String, nullable=True)
    district = Column(String, default="Guntur")
    phone = Column(String, nullable=True)

    user = relationship("User", back_populates="farmer_profile")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop_name = Column(String, nullable=False)
    expected_yield_kg = Column(Float, nullable=False)
    cost_needed = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    qty_sold_kg = Column(Float, default=0.0)
    status = Column(Enum(CropStatus), default=CropStatus.open)

    actual_yield_kg = Column(Float, nullable=True)
    quality_grade = Column(String, nullable=True)
    fulfillment_ratio = Column(Float, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    purchases = relationship("Purchase", back_populates="crop")
    ledger_entries = relationship("LedgerEntry", back_populates="crop")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    qty_kg = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=False)
    redeemed_qty_kg = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    crop = relationship("Crop", back_populates="purchases")
    customer = relationship("User", back_populates="purchases")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    prev_hash = Column(String, nullable=False)
    entry_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    crop = relationship("Crop", back_populates="ledger_entries")