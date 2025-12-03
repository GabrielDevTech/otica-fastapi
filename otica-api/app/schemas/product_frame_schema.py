"""Schemas Pydantic para ProductFrame."""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ProductFrameBase(BaseModel):
    """Schema base para ProductFrame."""
    reference_code: str = Field(..., min_length=1, max_length=100, description="Código de barras")
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sell_price: Decimal = Field(..., ge=0)
    min_stock_alert: int = Field(0, ge=0)
    description: Optional[str] = None


class ProductFrameCreate(ProductFrameBase):
    """Schema para criar ProductFrame."""
    initial_stock: Optional[int] = Field(None, ge=0, description="Estoque inicial na loja do usuário")


class ProductFrameUpdate(BaseModel):
    """Schema para atualizar ProductFrame."""
    reference_code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sell_price: Optional[Decimal] = Field(None, ge=0)
    min_stock_alert: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class InventoryLevelResponse(BaseModel):
    """Schema de resposta para InventoryLevel."""
    id: int
    store_id: int
    product_frame_id: int
    quantity: int
    reserved_quantity: int
    store_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductFrameResponse(ProductFrameBase):
    """Schema de resposta para ProductFrame."""
    id: int
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    inventory_levels: Optional[list[InventoryLevelResponse]] = None
    
    class Config:
        from_attributes = True

