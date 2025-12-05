"""Endpoints para gestão de ProductFrames (Armações)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above, require_admin
from app.models.product_frame_model import ProductFrame
from app.models.inventory_level_model import InventoryLevel
from app.models.store_model import Store
from app.models.organization_model import Organization
from app.models.staff_model import StaffMember
from app.schemas.product_frame_schema import (
    ProductFrameCreate,
    ProductFrameUpdate,
    ProductFrameResponse
)

router = APIRouter(prefix="/product-frames", tags=["product-frames"])


async def get_org_internal_id(db: AsyncSession, clerk_org_id: str) -> int:
    """Obtém o ID interno da organização."""
    result = await db.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organização não encontrada"
        )
    return org.id


@router.get("", response_model=List[ProductFrameResponse])
async def list_product_frames(
    q: Optional[str] = Query(None, description="Busca em nome/código/marca"),
    store_id: Optional[int] = Query(None, description="Filtrar por loja"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Lista armações da organização."""
    query = select(ProductFrame).where(
        ProductFrame.organization_id == current_org_id,
        ProductFrame.is_active == True
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                ProductFrame.name.ilike(search_term),
                ProductFrame.reference_code.ilike(search_term),
                ProductFrame.brand.ilike(search_term)
            )
        )
    
    result = await db.execute(query)
    frames = result.scalars().all()
    
    # Se store_id fornecido, adiciona níveis de estoque
    if store_id:
        for frame in frames:
            inv_result = await db.execute(
                select(InventoryLevel).where(
                    InventoryLevel.product_frame_id == frame.id,
                    InventoryLevel.store_id == store_id
                )
            )
            inv = inv_result.scalar_one_or_none()
            if inv:
                # Adiciona nome da loja
                store_result = await db.execute(
                    select(Store).where(Store.id == store_id)
                )
                store = store_result.scalar_one_or_none()
                if store:
                    inv.store_name = store.name
                frame.inventory_levels = [inv]
    
    return frames


@router.get("/{frame_id}", response_model=ProductFrameResponse)
async def get_product_frame(
    frame_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Obtém uma armação específica."""
    result = await db.execute(
        select(ProductFrame).where(
            ProductFrame.id == frame_id,
            ProductFrame.organization_id == current_org_id
        )
    )
    frame = result.scalar_one_or_none()
    
    if not frame:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Armação não encontrada"
        )
    
    return frame


@router.post("", response_model=ProductFrameResponse, status_code=status.HTTP_201_CREATED)
async def create_product_frame(
    frame_data: ProductFrameCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria uma nova armação.
    
    Se `initial_stock` for fornecido, cria registro em inventory_levels
    para a loja do usuário logado.
    """
    # Verifica se código já existe
    existing = await db.execute(
        select(ProductFrame).where(
            ProductFrame.organization_id == current_org_id,
            ProductFrame.reference_code == frame_data.reference_code
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de referência já existe nesta organização"
        )
    
    # Cria armação
    new_frame = ProductFrame(
        **frame_data.model_dump(exclude={"initial_stock"}),
        organization_id=current_org_id
    )
    db.add(new_frame)
    await db.flush()  # Para obter o ID
    
    # Se initial_stock fornecido, cria inventory_level
    if frame_data.initial_stock is not None:
        inv_level = InventoryLevel(
            organization_id=current_org_id,
            store_id=current_staff.store_id,
            product_frame_id=new_frame.id,
            quantity=frame_data.initial_stock
        )
        db.add(inv_level)
    
    await db.commit()
    await db.refresh(new_frame)
    
    return new_frame


@router.patch("/{frame_id}", response_model=ProductFrameResponse)
async def update_product_frame(
    frame_id: int,
    frame_data: ProductFrameUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """Atualiza uma armação."""
    result = await db.execute(
        select(ProductFrame).where(
            ProductFrame.id == frame_id,
            ProductFrame.organization_id == current_org_id
        )
    )
    frame = result.scalar_one_or_none()
    
    if not frame:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Armação não encontrada"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = frame_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(frame, field, value)
    
    await db.commit()
    await db.refresh(frame)
    
    return frame


@router.delete("/{frame_id}", status_code=status.HTTP_200_OK)
async def delete_product_frame(
    frame_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Desativa uma armação (soft delete).
    
    Retorna 200 em vez de 204 para compatibilidade com proxy Next.js.
    """
    result = await db.execute(
        select(ProductFrame).where(
            ProductFrame.id == frame_id,
            ProductFrame.organization_id == current_org_id
        )
    )
    frame = result.scalar_one_or_none()
    
    if not frame:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Armação não encontrada"
        )
    
    frame.is_active = False
    await db.commit()
    
    return {"message": "Armação deletada com sucesso", "id": frame_id}

