"""Schemas Pydantic para ServiceOrder."""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from decimal import Decimal
from datetime import datetime, date
from app.models.service_order_model import ServiceOrderStatus


class ServiceOrderItemBase(BaseModel):
    """Schema base para ServiceOrderItem."""
    item_type: Literal["FRAME", "LENS", "SERVICE"] = Field(..., description="Tipo de item")
    product_frame_id: Optional[int] = Field(None, description="ID da armação (se item_type=FRAME)")
    product_lens_id: Optional[int] = Field(None, description="ID da lente (se item_type=LENS)")
    quantity: int = Field(1, gt=0, description="Quantidade")
    unit_price: Decimal = Field(..., gt=0, description="Preço unitário")
    discount_amount: Decimal = Field(0, ge=0, description="Desconto em valor")
    # Lente específica
    lens_spherical: Optional[Decimal] = Field(None, description="Esférico")
    lens_cylindrical: Optional[Decimal] = Field(None, description="Cilíndrico")
    lens_axis: Optional[int] = Field(None, ge=0, le=180, description="Eixo")
    lens_addition: Optional[Decimal] = Field(None, description="Adição")
    lens_side: Optional[Literal["OD", "OE", "AMBOS"]] = Field(None, description="Lado da lente")


class ServiceOrderItemCreate(ServiceOrderItemBase):
    """Schema para criar ServiceOrderItem."""
    pass


class ServiceOrderItemResponse(ServiceOrderItemBase):
    """Schema de resposta para ServiceOrderItem."""
    id: int
    service_order_id: int
    total_price: Decimal
    reserved_quantity: int
    needs_purchasing: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class ServiceOrderBase(BaseModel):
    """Schema base para ServiceOrder."""
    customer_id: int = Field(..., description="ID do cliente")
    store_id: int = Field(..., description="ID da loja")
    notes: Optional[str] = Field(None, description="Observações")


class ServiceOrderCreate(ServiceOrderBase):
    """Schema para criar ServiceOrder."""
    items: List[ServiceOrderItemCreate] = Field(..., min_items=1, description="Lista de itens")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Desconto percentual geral")


class ServiceOrderUpdate(BaseModel):
    """Schema para atualizar ServiceOrder (apenas enquanto DRAFT)."""
    items: Optional[List[ServiceOrderItemCreate]] = Field(None, description="Lista de itens atualizada")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Desconto percentual")
    notes: Optional[str] = Field(None, description="Observações")


class ServiceOrderResponse(ServiceOrderBase):
    """Schema de resposta para ServiceOrder."""
    id: int
    organization_id: str
    seller_id: int
    status: ServiceOrderStatus
    order_number: str
    subtotal: Decimal
    discount_amount: Decimal
    discount_percentage: Optional[Decimal]
    total: Decimal
    max_discount_allowed: Optional[Decimal]
    discount_approved_by: Optional[int]
    paid_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    items: List[ServiceOrderItemResponse]
    
    class Config:
        from_attributes = True


class ServiceOrderStatusUpdate(BaseModel):
    """Schema para atualizar status da OS."""
    status: ServiceOrderStatus = Field(..., description="Novo status")

