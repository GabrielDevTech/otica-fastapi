"""Schemas Pydantic para Service Orders."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.service_order_model import ServiceOrderStatus, ItemType, LensSide


# ========== Service Order Schemas ==========

class ServiceOrderBase(BaseModel):
    """Schema base para Service Order."""
    customer_id: int = Field(..., description="ID do cliente")
    store_id: int = Field(..., description="ID da loja")
    notes: Optional[str] = Field(None, description="Observações")


class ServiceOrderCreate(ServiceOrderBase):
    """Schema para criação de Service Order."""
    # seller_id é injetado automaticamente do token
    # order_number é gerado automaticamente
    pass


class ServiceOrderUpdate(BaseModel):
    """Schema para atualização de Service Order."""
    customer_id: Optional[int] = None
    notes: Optional[str] = None


class ServiceOrderItemResponse(BaseModel):
    """Schema de resposta para item de Service Order."""
    id: int
    item_type: ItemType
    product_frame_id: Optional[int] = None
    product_lens_id: Optional[int] = None
    product_name: str
    product_reference_code: Optional[str] = None
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    total_price: Decimal
    reserved_quantity: int
    reserved_at: Optional[datetime] = None
    lens_spherical: Optional[Decimal] = None
    lens_cylindrical: Optional[Decimal] = None
    lens_axis: Optional[int] = None
    lens_addition: Optional[Decimal] = None
    lens_side: Optional[LensSide] = None
    needs_purchasing: bool
    
    class Config:
        from_attributes = True


class ServiceOrderResponse(BaseModel):
    """Schema de resposta para Service Order (lista)."""
    id: int
    order_number: str
    customer_id: int
    customer_name: Optional[str] = None
    customer_cpf: Optional[str] = None
    store_id: int
    store_name: Optional[str] = None
    seller_id: int
    seller_name: Optional[str] = None
    status: ServiceOrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    discount_percentage: Optional[Decimal] = None
    total: Decimal
    max_discount_allowed: Optional[Decimal] = None
    discount_approved_by: Optional[int] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    notes: Optional[str] = None
    items_count: int = 0
    
    class Config:
        from_attributes = True


class CustomerInfo(BaseModel):
    """Schema para informações do cliente."""
    id: int
    full_name: str
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    class Config:
        from_attributes = True


class StoreInfo(BaseModel):
    """Schema para informações da loja."""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class SellerInfo(BaseModel):
    """Schema para informações do vendedor."""
    id: int
    full_name: str
    email: Optional[str] = None
    
    class Config:
        from_attributes = True


class ServiceOrderDetailResponse(BaseModel):
    """Schema de resposta detalhada para Service Order."""
    id: int
    order_number: str
    customer_id: int
    customer: CustomerInfo
    store_id: int
    store: StoreInfo
    seller_id: int
    seller: SellerInfo
    status: ServiceOrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    discount_percentage: Optional[Decimal] = None
    total: Decimal
    max_discount_allowed: Optional[Decimal] = None
    discount_approved_by: Optional[int] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[ServiceOrderItemResponse] = []
    
    class Config:
        from_attributes = True


class ServiceOrderListResponse(BaseModel):
    """Schema de resposta para lista paginada de Service Orders."""
    items: List[ServiceOrderResponse]
    total: int
    page: int
    limit: int
    pages: int


# ========== Service Order Item Schemas ==========

class ServiceOrderItemCreateFrame(BaseModel):
    """Schema para adicionar armação à Service Order."""
    item_type: ItemType = Field(ItemType.FRAME, description="Tipo de item")
    product_frame_id: int = Field(..., description="ID da armação")
    quantity: int = Field(1, ge=1, description="Quantidade")
    unit_price: Decimal = Field(..., ge=0, description="Preço unitário")


class ServiceOrderItemCreateLens(BaseModel):
    """Schema para adicionar lente à Service Order."""
    item_type: ItemType = Field(ItemType.LENS, description="Tipo de item")
    product_lens_id: int = Field(..., description="ID da lente")
    quantity: int = Field(1, ge=1, description="Quantidade")
    unit_price: Decimal = Field(..., ge=0, description="Preço unitário")
    lens_spherical: Decimal = Field(..., description="Esférico")
    lens_cylindrical: Decimal = Field(..., description="Cilíndrico")
    lens_axis: int = Field(..., ge=0, le=180, description="Eixo (0-180)")
    lens_addition: Optional[Decimal] = Field(None, description="Adição (para multifocais)")
    lens_side: LensSide = Field(LensSide.BOTH, description="Lado da lente")


class ServiceOrderItemUpdate(BaseModel):
    """Schema para atualizar item de Service Order."""
    quantity: Optional[int] = Field(None, ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)


# ========== Discount Schemas ==========

class DiscountRequest(BaseModel):
    """Schema para aplicar desconto."""
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Valor do desconto")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentual do desconto")


# ========== Cancel Schemas ==========

class CancelRequest(BaseModel):
    """Schema para cancelar Service Order."""
    reason: Optional[str] = Field(None, description="Motivo do cancelamento")

