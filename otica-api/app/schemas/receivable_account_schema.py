"""Schemas Pydantic para ReceivableAccount."""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime, date
from app.models.receivable_account_model import ReceivableStatus


class ReceivableAccountBase(BaseModel):
    """Schema base para ReceivableAccount."""
    customer_id: int = Field(..., description="ID do cliente")
    total_amount: Decimal = Field(..., gt=0, description="Valor total")
    due_date: date = Field(..., description="Data de vencimento")
    notes: Optional[str] = Field(None, description="Observações")


class ReceivableAccountCreate(ReceivableAccountBase):
    """Schema para criar ReceivableAccount."""
    sale_id: Optional[int] = Field(None, description="ID da venda (opcional)")


class ReceivableAccountResponse(ReceivableAccountBase):
    """Schema de resposta para ReceivableAccount."""
    id: int
    organization_id: str
    sale_id: Optional[int]
    paid_amount: Decimal
    remaining_amount: Decimal
    status: ReceivableStatus
    paid_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

