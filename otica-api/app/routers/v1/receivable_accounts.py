"""Endpoints para gestão de Receivable Accounts (Contas a Receber)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_manager_or_admin
from app.models.receivable_account_model import ReceivableAccount, ReceivableStatus
from app.models.staff_model import StaffMember
from app.schemas.receivable_account_schema import ReceivableAccountResponse


router = APIRouter(prefix="/receivable-accounts", tags=["receivable-accounts"])


@router.get("", response_model=List[ReceivableAccountResponse])
async def list_receivable_accounts(
    status: Optional[ReceivableStatus] = Query(None, description="Filtrar por status"),
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    due_date_from: Optional[str] = Query(None, description="Data de vencimento inicial (YYYY-MM-DD)"),
    due_date_to: Optional[str] = Query(None, description="Data de vencimento final (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Lista contas a receber.
    
    **Permissões**: MANAGER ou ADMIN
    """
    from datetime import date
    
    query = select(ReceivableAccount).where(
        ReceivableAccount.organization_id == current_org_id,
        ReceivableAccount.is_active == True
    )
    
    if status:
        query = query.where(ReceivableAccount.status == status)
    
    if customer_id:
        query = query.where(ReceivableAccount.customer_id == customer_id)
    
    if due_date_from:
        try:
            from_date = date.fromisoformat(due_date_from)
            query = query.where(ReceivableAccount.due_date >= from_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data inválido. Use YYYY-MM-DD"
            )
    
    if due_date_to:
        try:
            to_date = date.fromisoformat(due_date_to)
            query = query.where(ReceivableAccount.due_date <= to_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data inválido. Use YYYY-MM-DD"
            )
    
    query = query.order_by(ReceivableAccount.due_date.asc())
    
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    return accounts

