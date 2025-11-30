"""Schemas Pydantic para Store."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StoreBase(BaseModel):
    """Schema base de Store."""
    name: str = Field(..., min_length=2, max_length=255, description="Nome da loja")
    address: Optional[str] = Field(None, description="Endereço")
    phone: Optional[str] = Field(None, max_length=20, description="Telefone")
    is_active: bool = Field(default=True)


class StoreCreate(StoreBase):
    """Schema para criar uma Store."""
    pass  # organization_id é injetado do token


class StoreUpdate(BaseModel):
    """Schema para atualizar uma Store."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    """Schema de resposta de Store."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

