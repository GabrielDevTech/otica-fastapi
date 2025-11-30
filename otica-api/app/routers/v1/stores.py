"""Endpoints para gestão de Stores (Lojas)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_admin, require_staff_or_above
from app.models.store_model import Store
from app.models.organization_model import Organization
from app.models.staff_model import StaffMember
from app.schemas.store_schema import StoreCreate, StoreUpdate, StoreResponse


router = APIRouter(prefix="/stores", tags=["stores"])


async def get_org_internal_id(
    db: AsyncSession,
    clerk_org_id: str
) -> int:
    """Obtém o ID interno da organização pelo clerk_org_id."""
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


@router.get("", response_model=List[StoreResponse])
async def list_stores(
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Lista todas as lojas da organização atual.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Store).where(
            Store.organization_id == org_id,
            Store.is_active == True
        )
    )
    stores = result.scalars().all()
    
    return stores


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Obtém uma loja específica.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Store).where(
            Store.id == store_id,
            Store.organization_id == org_id
        )
    )
    store = result.scalar_one_or_none()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loja não encontrada"
        )
    
    return store


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    store_data: StoreCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria uma nova loja.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    # Verifica se já existe loja com mesmo nome na org
    existing = await db.execute(
        select(Store).where(
            Store.organization_id == org_id,
            Store.name == store_data.name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma loja com este nome"
        )
    
    new_store = Store(
        **store_data.model_dump(),
        organization_id=org_id
    )
    
    db.add(new_store)
    await db.commit()
    await db.refresh(new_store)
    
    return new_store


@router.patch("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: int,
    store_data: StoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Atualiza uma loja.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Store).where(
            Store.id == store_id,
            Store.organization_id == org_id
        )
    )
    store = result.scalar_one_or_none()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loja não encontrada"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = store_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(store, field, value)
    
    await db.commit()
    await db.refresh(store)
    
    return store


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Desativa uma loja (soft delete).
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Store).where(
            Store.id == store_id,
            Store.organization_id == org_id
        )
    )
    store = result.scalar_one_or_none()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loja não encontrada"
        )
    
    store.is_active = False
    await db.commit()

