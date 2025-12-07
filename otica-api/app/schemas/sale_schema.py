"""Schemas Pydantic para Sale."""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.sale_model import PaymentMethod


class SaleCheckout(BaseModel):
    """Schema para processar checkout/pagamento."""
    payment_method: PaymentMethod = Field(..., description="Método de pagamento")
    cash_session_id: Optional[int] = Field(None, description="ID da sessão de caixa (obrigatório se payment_method=CASH)")


class SaleResponse(BaseModel):
    """Schema de resposta para Sale."""
    id: int
    organization_id: str
    service_order_id: int
    customer_id: int
    store_id: int
    seller_id: int
    cash_session_id: Optional[int]
    total_amount: Decimal
    payment_method: PaymentMethod
    card_fee_rate: Optional[Decimal]
    card_gross_amount: Optional[Decimal]
    card_net_amount: Optional[Decimal]
    receivable_account_id: Optional[int]
    commissionable_amount: Optional[Decimal]
    sold_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

