"""Schemas Pydantic para CashMovement."""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.cash_movement_model import CashMovementType


class CashMovementBase(BaseModel):
    """Schema base para CashMovement."""
    movement_type: CashMovementType = Field(..., description="Tipo de movimentação")
    amount: Decimal = Field(..., gt=0, description="Valor da movimentação")
    description: Optional[str] = Field(None, max_length=255, description="Motivo da movimentação")


class CashMovementCreate(CashMovementBase):
    """Schema para criar CashMovement."""
    pass


class CashMovementResponse(CashMovementBase):
    """Schema de resposta para CashMovement."""
    id: int
    organization_id: str
    cash_session_id: int
    staff_id: int
    movement_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

