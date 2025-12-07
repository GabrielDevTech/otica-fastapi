"""Endpoints para busca unificada de produtos."""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above
from app.models.product_frame_model import ProductFrame
from app.models.product_lens_model import ProductLens
from app.models.inventory_level_model import InventoryLevel
from app.models.staff_model import StaffMember
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional as Opt


router = APIRouter(prefix="/products", tags=["products"])


class StockInfo(BaseModel):
    """Informações de estoque."""
    quantity: int
    reserved_quantity: int
    available: int


class FrameSearchResult(BaseModel):
    """Resultado de busca de armação."""
    id: int
    reference_code: str
    name: str
    brand: Optional[str]
    model: Optional[str]
    sell_price: Decimal
    stock: Optional[StockInfo] = None


class LensSearchResult(BaseModel):
    """Resultado de busca de lente."""
    id: int
    name: str
    sell_price: Decimal
    is_lab_order: bool


class ProductSearchResponse(BaseModel):
    """Resposta da busca unificada."""
    frames: List[FrameSearchResult]
    lenses: List[LensSearchResult]


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: Optional[str] = Query(None, description="Termo de busca (código, nome, marca)"),
    type: Optional[Literal["FRAME", "LENS", "ALL"]] = Query("ALL", description="Tipo de produto"),
    store_id: Optional[int] = Query(None, description="ID da loja (para verificar estoque)"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Busca unificada de Armações e Lentes.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    """
    frames = []
    lenses = []
    
    # Busca armações
    if type in ["FRAME", "ALL"]:
        frame_query = select(ProductFrame).where(
            ProductFrame.organization_id == current_org_id,
            ProductFrame.is_active == True
        )
        
        if q:
            search_term = f"%{q}%"
            frame_query = frame_query.where(
                or_(
                    ProductFrame.reference_code.ilike(search_term),
                    ProductFrame.name.ilike(search_term),
                    ProductFrame.brand.ilike(search_term),
                    ProductFrame.model.ilike(search_term)
                )
            )
        
        frame_result = await db.execute(frame_query)
        frame_list = frame_result.scalars().all()
        
        for frame in frame_list:
            stock_info = None
            
            # Se store_id fornecido, busca estoque
            if store_id:
                inv_result = await db.execute(
                    select(InventoryLevel).where(
                        InventoryLevel.store_id == store_id,
                        InventoryLevel.product_frame_id == frame.id,
                        InventoryLevel.organization_id == current_org_id
                    )
                )
                inv_level = inv_result.scalar_one_or_none()
                
                if inv_level:
                    stock_info = StockInfo(
                        quantity=inv_level.quantity,
                        reserved_quantity=inv_level.reserved_quantity,
                        available=inv_level.quantity - inv_level.reserved_quantity
                    )
            
            frames.append(FrameSearchResult(
                id=frame.id,
                reference_code=frame.reference_code,
                name=frame.name,
                brand=frame.brand,
                model=frame.model,
                sell_price=frame.sell_price,
                stock=stock_info
            ))
    
    # Busca lentes
    if type in ["LENS", "ALL"]:
        lens_query = select(ProductLens).where(
            ProductLens.organization_id == current_org_id,
            ProductLens.is_active == True
        )
        
        if q:
            search_term = f"%{q}%"
            lens_query = lens_query.where(
                or_(
                    ProductLens.name.ilike(search_term)
                )
            )
        
        lens_result = await db.execute(lens_query)
        lens_list = lens_result.scalars().all()
        
        for lens in lens_list:
            lenses.append(LensSearchResult(
                id=lens.id,
                name=lens.name,
                sell_price=lens.sell_price,
                is_lab_order=lens.is_lab_order
            ))
    
    return ProductSearchResponse(frames=frames, lenses=lenses)

