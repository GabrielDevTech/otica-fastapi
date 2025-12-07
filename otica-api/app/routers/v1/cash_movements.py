"""Endpoints para gestão de Cash Movements (Sangria/Suprimento)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above, get_current_staff
from app.models.cash_movement_model import CashMovement
from app.models.cash_session_model import CashSession, CashSessionStatus
from app.models.staff_model import StaffMember
from app.schemas.cash_movement_schema import (
    CashMovementCreate,
    CashMovementResponse
)


router = APIRouter(prefix="/cash-movements", tags=["cash-movements"])


@router.post("", response_model=CashMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_cash_movement(
    movement_data: CashMovementCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Registra sangria ou suprimento de dinheiro.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    """
    # Busca sessão ativa do vendedor
    session_result = await db.execute(
        select(CashSession).where(
            CashSession.organization_id == current_org_id,
            CashSession.staff_id == current_staff.id,
            CashSession.status == CashSessionStatus.OPEN,
            CashSession.is_active == True
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não há sessão de caixa aberta. Abra uma sessão antes de registrar movimentações."
        )
    
    # Cria movimento
    new_movement = CashMovement(
        organization_id=current_org_id,
        cash_session_id=session.id,
        staff_id=current_staff.id,
        movement_type=movement_data.movement_type,
        amount=movement_data.amount,
        description=movement_data.description
    )
    
    db.add(new_movement)
    await db.commit()
    await db.refresh(new_movement)
    
    return new_movement


@router.get("", response_model=List[CashMovementResponse])
async def list_cash_movements(
    cash_session_id: Optional[int] = Query(None, description="ID da sessão (opcional, usa sessão atual se não informado)"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Lista movimentações de caixa.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    
    Se `cash_session_id` não for informado, usa a sessão ativa do vendedor.
    """
    # Se não informou session_id, busca sessão ativa
    if cash_session_id is None:
        session_result = await db.execute(
            select(CashSession).where(
                CashSession.organization_id == current_org_id,
                CashSession.staff_id == current_staff.id,
                CashSession.status == CashSessionStatus.OPEN,
                CashSession.is_active == True
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não há sessão de caixa aberta"
            )
        
        cash_session_id = session.id
    
    # Valida que a sessão pertence à organização
    session_result = await db.execute(
        select(CashSession).where(
            CashSession.id == cash_session_id,
            CashSession.organization_id == current_org_id,
            CashSession.is_active == True
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    # Lista movimentos
    result = await db.execute(
        select(CashMovement).where(
            CashMovement.cash_session_id == cash_session_id,
            CashMovement.organization_id == current_org_id,
            CashMovement.is_active == True
        ).order_by(CashMovement.movement_date.desc())
    )
    movements = result.scalars().all()
    
    return movements

