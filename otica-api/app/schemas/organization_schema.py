"""Schemas Pydantic para Organization."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrganizationBase(BaseModel):
    """Schema base de Organization."""
    name: str = Field(..., min_length=2, max_length=255, description="Nome fantasia")
    cnpj: Optional[str] = Field(None, max_length=14, description="CNPJ (apenas números)")
    plan: str = Field(default="basic", description="Plano: basic, pro, enterprise")
    is_active: bool = Field(default=True)


class OrganizationCreate(OrganizationBase):
    """Schema para criar uma Organization."""
    clerk_org_id: str = Field(..., description="ID da organização no Clerk")
    access_code: str = Field(..., min_length=6, max_length=20, description="Código de acesso único")


class OrganizationUpdate(BaseModel):
    """Schema para atualizar uma Organization."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    cnpj: Optional[str] = Field(None, max_length=14)
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    access_code: Optional[str] = Field(None, min_length=6, max_length=20)


class OrganizationResponse(OrganizationBase):
    """Schema de resposta de Organization."""
    id: int
    clerk_org_id: str
    access_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationPublicInfo(BaseModel):
    """Schema público (para validar código de acesso)."""
    id: int
    name: str
    
    class Config:
        from_attributes = True

