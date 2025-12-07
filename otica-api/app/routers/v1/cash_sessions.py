"""Endpoints para gestão de Cash Sessions (Apoio de Caixa)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import (
    get_current_staff,
    require_staff_or_above,
    require_manager_or_admin
)
from app.models.cash_session_model import CashSession, CashSessionStatus
from app.models.store_model import Store
from app.models.staff_model import StaffMember
from app.models.organization_model import Organization
from app.schemas.cash_session_schema import (
    CashSessionCreate,
    CashSessionClose,
    CashSessionAudit,
    CashSessionResponse,
    CashSessionStats
)


router = APIRouter(prefix="/cash-sessions", tags=["cash-sessions"])


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


@router.get("/my-session", response_model=Optional[CashSessionResponse])
async def get_my_session(
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Retorna a sessão de caixa ativa do vendedor logado.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    
    Retorna `null` se não houver sessão aberta.
    """
    result = await db.execute(
        select(CashSession).where(
            CashSession.organization_id == current_org_id,
            CashSession.staff_id == current_staff.id,
            CashSession.status == CashSessionStatus.OPEN,
            CashSession.is_active == True
        )
    )
    session = result.scalar_one_or_none()
    return session


@router.post("", response_model=CashSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_cash_session(
    session_data: CashSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Abre nova sessão de caixa.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    """
    # Verifica se já existe sessão aberta para este vendedor
    existing = await db.execute(
        select(CashSession).where(
            CashSession.organization_id == current_org_id,
            CashSession.staff_id == current_staff.id,
            CashSession.status == CashSessionStatus.OPEN,
            CashSession.is_active == True
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma sessão de caixa aberta para este vendedor"
        )
    
    # Valida que a loja pertence à organização
    org_id = await get_org_internal_id(db, current_org_id)
    store_result = await db.execute(
        select(Store).where(
            Store.id == session_data.store_id,
            Store.organization_id == org_id,
            Store.is_active == True
        )
    )
    store = store_result.scalar_one_or_none()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loja não encontrada ou não pertence à organização"
        )
    
    # Cria nova sessão
    new_session = CashSession(
        organization_id=current_org_id,
        store_id=session_data.store_id,
        staff_id=current_staff.id,
        status=CashSessionStatus.OPEN,
        opening_balance=session_data.opening_balance
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return new_session


@router.post("/{session_id}/close", response_model=CashSessionResponse)
async def close_cash_session(
    session_id: int,
    close_data: CashSessionClose,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Fecha a sessão de caixa.
    
    **Permissões**: SELLER (apenas sua sessão), MANAGER ou ADMIN
    """
    # Busca a sessão
    result = await db.execute(
        select(CashSession).where(
            CashSession.id == session_id,
            CashSession.organization_id == current_org_id,
            CashSession.is_active == True
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    # Valida permissão: SELLER só pode fechar sua própria sessão
    if current_staff.role.value not in ["MANAGER", "ADMIN"] and session.staff_id != current_staff.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode fechar sua própria sessão de caixa"
        )
    
    # Valida que está aberta
    if session.status != CashSessionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sessão já está fechada"
        )
    
    # Calcula o saldo (opening_balance + entradas - saídas)
    from app.models.cash_movement_model import CashMovement, CashMovementType
    from datetime import datetime
    
    movements_result = await db.execute(
        select(CashMovement).where(
            CashMovement.cash_session_id == session_id,
            CashMovement.is_active == True
        )
    )
    movements = movements_result.scalars().all()
    
    total_deposits = sum(m.amount for m in movements if m.movement_type == CashMovementType.DEPOSIT)
    total_withdrawals = sum(m.amount for m in movements if m.movement_type == CashMovementType.WITHDRAWAL)
    
    calculated_balance = session.opening_balance + total_deposits - total_withdrawals
    
    # Atualiza sessão
    session.closing_balance = close_data.closing_balance
    session.calculated_balance = calculated_balance
    session.discrepancy = calculated_balance - close_data.closing_balance
    session.closed_at = datetime.utcnow()
    
    # Se houver divergência, status = PENDING_AUDIT, senão CLOSED
    if session.discrepancy != 0:
        session.status = CashSessionStatus.PENDING_AUDIT
    else:
        session.status = CashSessionStatus.CLOSED
    
    await db.commit()
    await db.refresh(session)
    
    return session


@router.get("/dashboard-stats", response_model=CashSessionStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Retorna KPIs para dashboard gerencial.
    
    **Permissões**: MANAGER ou ADMIN
    """
    # Conta sessões ativas
    active_result = await db.execute(
        select(func.count(CashSession.id)).where(
            CashSession.organization_id == current_org_id,
            CashSession.status == CashSessionStatus.OPEN,
            CashSession.is_active == True
        )
    )
    active_sessions_count = active_result.scalar() or 0
    
    # Conta sessões pendentes de auditoria
    pending_result = await db.execute(
        select(func.count(CashSession.id)).where(
            CashSession.organization_id == current_org_id,
            CashSession.status == CashSessionStatus.PENDING_AUDIT,
            CashSession.is_active == True
        )
    )
    pending_audit_count = pending_result.scalar() or 0
    
    # Soma total de divergências pendentes
    discrepancy_result = await db.execute(
        select(func.coalesce(func.sum(CashSession.discrepancy), 0)).where(
            CashSession.organization_id == current_org_id,
            CashSession.status == CashSessionStatus.PENDING_AUDIT,
            CashSession.is_active == True
        )
    )
    total_discrepancy = discrepancy_result.scalar() or 0
    
    # TODO: Calcular taxas de cartão estimadas (mês)
    # Por enquanto retorna 0, será implementado quando houver vendas
    card_fees_estimated = 0
    
    return CashSessionStats(
        active_sessions_count=active_sessions_count,
        pending_audit_count=pending_audit_count,
        total_discrepancy=total_discrepancy,
        card_fees_estimated=card_fees_estimated
    )


@router.get("", response_model=List[CashSessionResponse])
async def list_cash_sessions(
    status: Optional[CashSessionStatus] = Query(None, description="Filtrar por status"),
    store_id: Optional[int] = Query(None, description="Filtrar por loja"),
    staff_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Lista todas as sessões de caixa.
    
    **Permissões**: MANAGER ou ADMIN
    """
    query = select(CashSession).where(
        CashSession.organization_id == current_org_id,
        CashSession.is_active == True
    )
    
    if status:
        query = query.where(CashSession.status == status)
    
    if store_id:
        query = query.where(CashSession.store_id == store_id)
    
    if staff_id:
        query = query.where(CashSession.staff_id == staff_id)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return sessions


@router.post("/{session_id}/audit", response_model=CashSessionResponse)
async def audit_cash_session(
    session_id: int,
    audit_data: CashSessionAudit,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Resolve divergência de caixa.
    
    **Permissões**: MANAGER ou ADMIN
    """
    # Busca a sessão
    result = await db.execute(
        select(CashSession).where(
            CashSession.id == session_id,
            CashSession.organization_id == current_org_id,
            CashSession.is_active == True
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    # Valida que está em PENDING_AUDIT
    if session.status != CashSessionStatus.PENDING_AUDIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sessão não está pendente de auditoria"
        )
    
    # Valida corrected_value se necessário
    if audit_data.action == "CORRECT_VALUE" and audit_data.corrected_value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="corrected_value é obrigatório quando action=CORRECT_VALUE"
        )
    
    # Aplica a ação
    from datetime import datetime
    
    session.audit_resolved_by = current_staff.id
    session.audit_resolved_at = datetime.utcnow()
    session.audit_action = audit_data.action
    session.audit_notes = audit_data.notes
    
    if audit_data.action == "CORRECT_VALUE":
        session.calculated_balance = audit_data.corrected_value
        session.discrepancy = audit_data.corrected_value - session.closing_balance
    
    # TODO: Implementar ações ACCEPT_LOSS e CHARGE_STAFF
    # ACCEPT_LOSS: Criar despesa automática (futuro módulo financeiro)
    # CHARGE_STAFF: Criar ReceivableAccount contra o vendedor
    
    session.status = CashSessionStatus.CLOSED
    
    await db.commit()
    await db.refresh(session)
    
    return session

