"""Endpoints para gestão de Sales (Vendas/Checkout)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above, get_current_staff
from app.models.sale_model import Sale, PaymentMethod
from app.models.service_order_model import ServiceOrder, ServiceOrderStatus
from app.models.cash_session_model import CashSession, CashSessionStatus
from app.models.store_model import Store
from app.models.organization_model import Organization
from app.models.inventory_level_model import InventoryLevel
from app.models.receivable_account_model import ReceivableAccount, ReceivableStatus
from app.models.staff_model import StaffMember
from app.schemas.sale_schema import SaleCheckout, SaleResponse


router = APIRouter(prefix="/sales", tags=["sales"])


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


@router.post("/{order_id}/checkout", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def checkout_sale(
    order_id: int,
    checkout_data: SaleCheckout,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Processa pagamento e finaliza venda.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    """
    # Busca OS
    result = await db.execute(
        select(ServiceOrder).where(
            ServiceOrder.id == order_id,
            ServiceOrder.organization_id == current_org_id,
            ServiceOrder.is_active == True
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordem de Serviço não encontrada"
        )
    
    # Valida que está em PENDING
    if order.status != ServiceOrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OS deve estar em PENDING para processar pagamento"
        )
    
    cash_session_id = None
    card_fee_rate = None
    card_gross_amount = None
    card_net_amount = None
    receivable_account_id = None
    
    # Processa conforme método de pagamento
    if checkout_data.payment_method == PaymentMethod.CASH:
        # Valida sessão de caixa
        if not checkout_data.cash_session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cash_session_id é obrigatório para pagamento em dinheiro"
            )
        
        session_result = await db.execute(
            select(CashSession).where(
                CashSession.id == checkout_data.cash_session_id,
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
                detail="Sessão de caixa não encontrada ou não está aberta"
            )
        
        cash_session_id = session.id
        # TODO: Criar lançamento de entrada no caixa (futuro módulo financeiro)
    
    elif checkout_data.payment_method == PaymentMethod.CARD:
        # Busca taxa da loja
        org_id = await get_org_internal_id(db, current_org_id)
        store_result = await db.execute(
            select(Store).where(
                Store.id == order.store_id,
                Store.organization_id == org_id
            )
        )
        store = store_result.scalar_one_or_none()
        
        if store and store.tax_rate_machine:
            card_fee_rate = store.tax_rate_machine
            card_gross_amount = order.total
            card_net_amount = order.total * (1 - card_fee_rate / 100)
        else:
            card_gross_amount = order.total
            card_net_amount = order.total
    
    elif checkout_data.payment_method in [PaymentMethod.PIX, PaymentMethod.CREDIT]:
        # Cria conta a receber
        from datetime import date, timedelta
        
        # Data de vencimento padrão: 30 dias (pode ser configurável)
        due_date = date.today() + timedelta(days=30)
        
        new_receivable = ReceivableAccount(
            organization_id=current_org_id,
            customer_id=order.customer_id,
            sale_id=None,  # Será atualizado após criar a venda
            total_amount=order.total,
            paid_amount=0,
            remaining_amount=order.total,
            status=ReceivableStatus.PENDING,
            due_date=due_date
        )
        
        db.add(new_receivable)
        await db.flush()  # Para obter o ID
        
        receivable_account_id = new_receivable.id
    
    # Baixa estoque definitivo
    from app.models.service_order_item_model import ServiceOrderItem
    
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order_id)
    )
    items = items_result.scalars().all()
    
    for item in items:
        if item.item_type == "FRAME" and item.product_frame_id and item.reserved_quantity > 0:
            inv_result = await db.execute(
                select(InventoryLevel).where(
                    InventoryLevel.store_id == order.store_id,
                    InventoryLevel.product_frame_id == item.product_frame_id,
                    InventoryLevel.organization_id == current_org_id
                )
            )
            inv_level = inv_result.scalar_one_or_none()
            
            if inv_level:
                # Baixa estoque
                inv_level.quantity -= item.reserved_quantity
                inv_level.reserved_quantity -= item.reserved_quantity
                
                # TODO: Criar registro no Kardex
    
    # Cria venda
    new_sale = Sale(
        organization_id=current_org_id,
        service_order_id=order.id,
        customer_id=order.customer_id,
        store_id=order.store_id,
        seller_id=order.seller_id,
        cash_session_id=cash_session_id,
        total_amount=order.total,
        payment_method=checkout_data.payment_method,
        card_fee_rate=card_fee_rate,
        card_gross_amount=card_gross_amount,
        card_net_amount=card_net_amount,
        receivable_account_id=receivable_account_id,
        commissionable_amount=order.total  # TODO: Calcular comissão (futuro)
    )
    
    db.add(new_sale)
    
    # Atualiza conta a receber com sale_id
    if receivable_account_id:
        receivable_result = await db.execute(
            select(ReceivableAccount).where(ReceivableAccount.id == receivable_account_id)
        )
        receivable = receivable_result.scalar_one_or_none()
        if receivable:
            receivable.sale_id = new_sale.id
    
    # Atualiza OS
    order.status = ServiceOrderStatus.PAID
    order.paid_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(new_sale)
    
    return new_sale

