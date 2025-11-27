"""Schemas Pydantic para Staff."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.staff_model import StaffRole


class StaffBase(BaseModel):
    """Schema base para Staff."""
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    role: StaffRole
    department: Optional[str] = None
    is_active: bool = True


class StaffCreate(StaffBase):
    """Schema para criação de Staff."""
    # NÃO aceita organization_id (injetado pelo backend)
    pass


class StaffFilter(BaseModel):
    """Schema para filtros de busca."""
    q: Optional[str] = None
    role: Optional[StaffRole] = None


class StaffResponse(StaffBase):
    """Schema de resposta para Staff."""
    id: int
    organization_id: str
    clerk_id: Optional[str] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class StaffStats(BaseModel):
    """Schema para estatísticas de Staff."""
    total_users: int
    active_users: int
    admins: int
    managers: int

