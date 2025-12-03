"""Schemas Pydantic para Store."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime


class StoreBase(BaseModel):
    """Schema base de Store."""
    name: str = Field(..., min_length=1, max_length=255)
    address_data: Optional[Dict[str, Any]] = Field(None, description="Endereço completo em JSON")
    phone: Optional[str] = Field(None, max_length=20)
    tax_rate_machine: Optional[Decimal] = Field(None, ge=0, le=100, description="Taxa da máquina (ex: 2.5)")


class StoreCreate(StoreBase):
    """Schema para criar uma Store."""
    pass  # organization_id é injetado do token


class StoreUpdate(BaseModel):
    """Schema para atualizar uma Store."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address_data: Optional[Dict[str, Any]] = None
    phone: Optional[str] = Field(None, max_length=20)
    tax_rate_machine: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    """Schema de resposta de Store."""
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

