"""Schemas Pydantic para Kardex."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.kardex_model import KardexType


class KardexResponse(BaseModel):
    """Schema de resposta para Kardex."""
    id: int
    organization_id: str
    store_id: int
    product_frame_id: Optional[int]
    product_lens_id: Optional[int]
    sale_id: Optional[int]
    service_order_id: Optional[int]
    movement_type: str = Field(..., description="ENTRY, EXIT, RESERVATION, RELEASE")
    quantity: int = Field(..., description="Quantidade movimentada (positivo ou negativo)")
    balance_before: int = Field(..., description="Saldo antes da movimentação")
    balance_after: int = Field(..., description="Saldo após a movimentação")
    moved_by: int = Field(..., description="ID do funcionário que fez a movimentação")
    movement_date: datetime
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

