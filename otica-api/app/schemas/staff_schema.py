"""Schemas Pydantic para Staff."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.staff_model import StaffRole


class StaffBase(BaseModel):
    """Schema base para Staff."""
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    role: StaffRole
    store_id: int = Field(..., description="ID da loja (obrigatório)")
    department_id: int = Field(..., description="ID do setor (obrigatório)")
    job_title: Optional[str] = Field(None, description="Cargo específico")
    is_active: bool = True


class StaffCreate(StaffBase):
    """Schema para criação de Staff."""
    # NÃO aceita organization_id (injetado pelo backend)
    pass


class StaffUpdate(BaseModel):
    """Schema para atualizar Staff."""
    full_name: Optional[str] = Field(None, min_length=2)
    email: Optional[EmailStr] = None
    role: Optional[StaffRole] = None
    store_id: Optional[int] = Field(None, description="ID da loja")
    department_id: Optional[int] = Field(None, description="ID do setor")
    job_title: Optional[str] = None
    is_active: Optional[bool] = None


class StaffInvite(BaseModel):
    """Schema para convidar um novo Staff (admin cria direto)."""
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    role: StaffRole
    store_id: int = Field(..., description="ID da loja (obrigatório)")
    department_id: int = Field(..., description="ID do setor (obrigatório)")
    job_title: Optional[str] = Field(None, description="Cargo específico")


class StaffFilter(BaseModel):
    """Schema para filtros de busca."""
    q: Optional[str] = None
    role: Optional[StaffRole] = None
    store_id: Optional[int] = None
    department_id: Optional[int] = None


class StaffResponse(StaffBase):
    """Schema de resposta para Staff."""
    id: int
    clerk_id: Optional[str] = None
    organization_id: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StaffWithDetails(StaffResponse):
    """Schema de resposta com detalhes de loja e setor."""
    store_name: Optional[str] = None
    department_name: Optional[str] = None


class StaffStats(BaseModel):
    """Schema para estatísticas de Staff."""
    total_users: int
    active_users: int
    admins: int
    managers: int

