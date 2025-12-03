"""Schemas Pydantic para Department."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DepartmentBase(BaseModel):
    """Schema base de Department."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Descrição do setor")


class DepartmentCreate(DepartmentBase):
    """Schema para criar um Department."""
    pass  # organization_id é injetado do token


class DepartmentUpdate(BaseModel):
    """Schema para atualizar um Department."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema de resposta de Department."""
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

