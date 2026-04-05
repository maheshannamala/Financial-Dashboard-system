from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models import RoleEnum, RecordTypeEnum

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    role: RoleEnum = RoleEnum.viewer

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: int

    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Record Schemas ---
class RecordBase(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be strictly positive")
    type: RecordTypeEnum
    category: str
    notes: Optional[str] = None

class RecordCreate(RecordBase):
    pass

class RecordResponse(RecordBase):
    id: int
    date: datetime
    created_by_id: int

    class Config:
        from_attributes = True

# --- Dashboard Schemas ---
class CategorySummary(BaseModel):
    category: str
    total: float

class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    category_expenses: List[CategorySummary]