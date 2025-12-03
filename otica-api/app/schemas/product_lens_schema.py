"""Schemas Pydantic para ProductLens."""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class ProductLensBase(BaseModel):
    """Schema base para ProductLens."""
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sell_price: Decimal = Field(..., ge=0)
    is_lab_order: bool = Field(False, description="True = Surfaçagem, False = Estoque")
    treatment: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class LensStockGridCreate(BaseModel):
    """Schema para criar grade de estoque de lente."""
    spherical: Decimal = Field(..., description="Esférico (ex: -2.00)")
    cylindrical: Decimal = Field(..., description="Cilíndrico (ex: -1.00)")
    axis: Optional[int] = Field(None, ge=0, le=180)
    quantity: int = Field(0, ge=0)


class ProductLensCreate(ProductLensBase):
    """Schema para criar ProductLens."""
    initial_stock_grid: Optional[List[LensStockGridCreate]] = Field(
        None, 
        description="Grade inicial de estoque (apenas se is_lab_order = False)"
    )


class ProductLensUpdate(BaseModel):
    """Schema para atualizar ProductLens."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sell_price: Optional[Decimal] = Field(None, ge=0)
    is_lab_order: Optional[bool] = None
    treatment: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProductLensResponse(ProductLensBase):
    """Schema de resposta para ProductLens."""
    id: int
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

