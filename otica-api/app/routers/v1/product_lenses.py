"""Endpoints para gestão de ProductLenses (Lentes)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above, require_admin
from app.models.product_lens_model import ProductLens
from app.models.lens_stock_grid_model import LensStockGrid
from app.models.staff_model import StaffMember
from app.schemas.product_lens_schema import (
    ProductLensCreate,
    ProductLensUpdate,
    ProductLensResponse
)

router = APIRouter(prefix="/product-lenses", tags=["product-lenses"])


@router.get("", response_model=List[ProductLensResponse])
async def list_product_lenses(
    is_lab_order: Optional[bool] = Query(None, description="Filtrar por tipo"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Lista lentes da organização."""
    query = select(ProductLens).where(
        ProductLens.organization_id == current_org_id,
        ProductLens.is_active == True
    )
    
    if is_lab_order is not None:
        query = query.where(ProductLens.is_lab_order == is_lab_order)
    
    result = await db.execute(query)
    lenses = result.scalars().all()
    
    return lenses


@router.get("/{lens_id}", response_model=ProductLensResponse)
async def get_product_lens(
    lens_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Obtém uma lente específica."""
    result = await db.execute(
        select(ProductLens).where(
            ProductLens.id == lens_id,
            ProductLens.organization_id == current_org_id
        )
    )
    lens = result.scalar_one_or_none()
    
    if not lens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lente não encontrada"
        )
    
    return lens


@router.post("", response_model=ProductLensResponse, status_code=status.HTTP_201_CREATED)
async def create_product_lens(
    lens_data: ProductLensCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria uma nova lente.
    
    Se is_lab_order = False e initial_stock_grid fornecido,
    cria grade de estoque.
    """
    # Cria lente
    new_lens = ProductLens(
        **lens_data.model_dump(exclude={"initial_stock_grid"}),
        organization_id=current_org_id
    )
    db.add(new_lens)
    await db.flush()
    
    # Se não é lab_order e tem grade inicial, cria estoque
    if not lens_data.is_lab_order and lens_data.initial_stock_grid:
        for grid_item in lens_data.initial_stock_grid:
            grid = LensStockGrid(
                organization_id=current_org_id,
                store_id=current_staff.store_id,
                product_lens_id=new_lens.id,
                **grid_item.model_dump()
            )
            db.add(grid)
    
    await db.commit()
    await db.refresh(new_lens)
    
    return new_lens


@router.patch("/{lens_id}", response_model=ProductLensResponse)
async def update_product_lens(
    lens_id: int,
    lens_data: ProductLensUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """Atualiza uma lente."""
    result = await db.execute(
        select(ProductLens).where(
            ProductLens.id == lens_id,
            ProductLens.organization_id == current_org_id
        )
    )
    lens = result.scalar_one_or_none()
    
    if not lens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lente não encontrada"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = lens_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lens, field, value)
    
    await db.commit()
    await db.refresh(lens)
    
    return lens


@router.delete("/{lens_id}", status_code=status.HTTP_200_OK)
async def delete_product_lens(
    lens_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Desativa uma lente (soft delete).
    
    Retorna 200 em vez de 204 para compatibilidade com proxy Next.js.
    """
    result = await db.execute(
        select(ProductLens).where(
            ProductLens.id == lens_id,
            ProductLens.organization_id == current_org_id
        )
    )
    lens = result.scalar_one_or_none()
    
    if not lens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lente não encontrada"
        )
    
    lens.is_active = False
    await db.commit()
    
    return {"message": "Lente deletada com sucesso", "id": lens_id}

