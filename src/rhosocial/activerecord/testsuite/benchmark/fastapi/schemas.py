"""HTTP schemas for FastAPI benchmark scenarios."""

from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool
    backend: str
    scenario: str


class UserCreate(BaseModel):
    username: str
    email: str
    age: Optional[int] = None
    balance: float = 0.0
    notes: Optional[str] = None
    is_active: bool = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    age: Optional[int] = None
    balance: float
    notes: Optional[str] = None
    is_active: bool
