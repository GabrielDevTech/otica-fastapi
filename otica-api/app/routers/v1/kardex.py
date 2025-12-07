"""Endpoints para gestão de Kardex (Histórico de Movimentação)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above
from app.models.kardex_model import Kardex, KardexType
from app.models.staff_model import StaffMember
from app.schemas.kardex_schema import KardexResponse


router = APIRouter(prefix="/kardex", tags=["kardex"])


@router.get("", response_model=List[KardexResponse])
async def list_kardex(
    store_id: Optional[int] = Query(None, description="Filtrar por loja"),
    product_frame_id: Optional[int] = Query(None, description="Filtrar por armação"),
    product_lens_id: Optional[int] = Query(None, description="Filtrar por lente"),
    movement_type: Optional[str] = Query(None, description="Filtrar por tipo (ENTRY, EXIT, RESERVATION, RELEASE)"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DDTHH:MM:SS)"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Lista movimentações do Kardex.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    """
    query = select(Kardex).where(
        Kardex.organization_id == current_org_id
    )
    
    if store_id:
        query = query.where(Kardex.store_id == store_id)
    
    if product_frame_id:
        query = query.where(Kardex.product_frame_id == product_frame_id)
    
    if product_lens_id:
        query = query.where(Kardex.product_lens_id == product_lens_id)
    
    if movement_type:
        query = query.where(Kardex.movement_type == movement_type)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(Kardex.movement_date >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data inválido. Use YYYY-MM-DDTHH:MM:SS"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.where(Kardex.movement_date <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data inválido. Use YYYY-MM-DDTHH:MM:SS"
            )
    
    query = query.order_by(Kardex.movement_date.desc())
    
    result = await db.execute(query)
    kardex_entries = result.scalars().all()
    
    return kardex_entries

