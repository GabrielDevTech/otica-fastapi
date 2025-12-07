"""Endpoints para Fila de Laboratório."""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above
from app.models.service_order_model import ServiceOrder, ServiceOrderStatus
from app.models.service_order_item_model import ServiceOrderItem
from app.models.staff_model import StaffMember
from app.schemas.service_order_schema import ServiceOrderResponse
from app.routers.v1.service_orders import build_service_order_response
from pydantic import BaseModel


router = APIRouter(prefix="/lab", tags=["lab"])


class LabQueueResponse(BaseModel):
    """Resposta da fila Kanban."""
    awaiting_mount: List[ServiceOrderResponse]
    awaiting_lens: List[ServiceOrderResponse]
    in_production: List[ServiceOrderResponse]
    ready: List[ServiceOrderResponse]


@router.get("/queue", response_model=LabQueueResponse)
async def get_lab_queue(
    store_id: Optional[int] = Query(None, description="Filtrar por loja"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Retorna OS organizadas por status (Kanban).
    
    **Permissões**: SELLER (read), STAFF, MANAGER ou ADMIN
    """
    # Query base
    query = select(ServiceOrder).where(
        ServiceOrder.organization_id == current_org_id,
        ServiceOrder.is_active == True,
        ServiceOrder.status.in_([
            ServiceOrderStatus.PAID,
            ServiceOrderStatus.AWAITING_LENS,
            ServiceOrderStatus.IN_PRODUCTION,
            ServiceOrderStatus.READY
        ])
    )
    
    if store_id:
        query = query.where(ServiceOrder.store_id == store_id)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # Carrega itens para todas as OS de uma vez
    order_ids = [order.id for order in orders]
    items_by_order = {}
    
    if order_ids:
        items_result = await db.execute(
            select(ServiceOrderItem).where(ServiceOrderItem.service_order_id.in_(order_ids))
        )
        all_items = items_result.scalars().all()
        
        # Agrupa itens por order_id
        for item in all_items:
            if item.service_order_id not in items_by_order:
                items_by_order[item.service_order_id] = []
            items_by_order[item.service_order_id].append(item)
    
    # Constrói resposta e agrupa por status
    awaiting_mount = []
    awaiting_lens = []
    in_production = []
    ready = []
    
    for order in orders:
        items = items_by_order.get(order.id, [])
        order_response = build_service_order_response(order, items)
        
        if order.status == ServiceOrderStatus.PAID:
            awaiting_mount.append(order_response)
        elif order.status == ServiceOrderStatus.AWAITING_LENS:
            awaiting_lens.append(order_response)
        elif order.status == ServiceOrderStatus.IN_PRODUCTION:
            in_production.append(order_response)
        elif order.status == ServiceOrderStatus.READY:
            ready.append(order_response)
    
    return LabQueueResponse(
        awaiting_mount=awaiting_mount,
        awaiting_lens=awaiting_lens,
        in_production=in_production,
        ready=ready
    )

