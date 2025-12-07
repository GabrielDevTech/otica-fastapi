"""Endpoints para gestão de Service Orders (Ordens de Serviço)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from datetime import datetime
from decimal import Decimal
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import (
    get_current_staff,
    require_staff_or_above,
    require_manager_or_admin
)
from app.models.service_order_model import ServiceOrder, ServiceOrderStatus
from app.models.service_order_item_model import ServiceOrderItem
from app.models.customer_model import Customer
from app.models.store_model import Store
from app.models.organization_model import Organization
from app.models.staff_model import StaffMember
from app.models.inventory_level_model import InventoryLevel
from app.models.product_frame_model import ProductFrame
from app.models.product_lens_model import ProductLens
from app.models.lens_stock_grid_model import LensStockGrid
from app.schemas.service_order_schema import (
    ServiceOrderCreate,
    ServiceOrderUpdate,
    ServiceOrderResponse,
    ServiceOrderStatusUpdate,
    ServiceOrderItemResponse
)


router = APIRouter(prefix="/service-orders", tags=["service-orders"])


def build_service_order_response(order: ServiceOrder, items: List[ServiceOrderItem]) -> ServiceOrderResponse:
    """Constrói ServiceOrderResponse manualmente para evitar lazy loading."""
    order_dict = {
        "id": order.id,
        "organization_id": order.organization_id,
        "customer_id": order.customer_id,
        "store_id": order.store_id,
        "seller_id": order.seller_id,
        "status": order.status,
        "order_number": order.order_number,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount,
        "discount_percentage": order.discount_percentage,
        "total": order.total,
        "max_discount_allowed": order.max_discount_allowed,
        "discount_approved_by": order.discount_approved_by,
        "paid_at": order.paid_at,
        "delivered_at": order.delivered_at,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "is_active": order.is_active,
        "notes": order.notes,
        "items": [
            ServiceOrderItemResponse(
                id=item.id,
                service_order_id=item.service_order_id,
                item_type=item.item_type,
                product_frame_id=item.product_frame_id,
                product_lens_id=item.product_lens_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                total_price=item.total_price,
                reserved_quantity=item.reserved_quantity,
                lens_spherical=item.lens_spherical,
                lens_cylindrical=item.lens_cylindrical,
                lens_axis=item.lens_axis,
                lens_addition=item.lens_addition,
                lens_side=item.lens_side,
                needs_purchasing=item.needs_purchasing,
                is_active=item.is_active,
            )
            for item in items
        ]
    }
    return ServiceOrderResponse(**order_dict)


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


async def generate_order_number(db: AsyncSession, organization_id: str) -> str:
    """Gera número único de OS (ex: OS-2024-001)."""
    current_year = datetime.now().year
    
    # Busca última OS do ano
    result = await db.execute(
        select(ServiceOrder).where(
            ServiceOrder.organization_id == organization_id,
            ServiceOrder.order_number.like(f"OS-{current_year}-%")
        ).order_by(ServiceOrder.order_number.desc())
    )
    last_order = result.scalar_one_or_none()
    
    if last_order:
        # Extrai o número da última OS
        last_number = int(last_order.order_number.split("-")[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"OS-{current_year}-{new_number:03d}"


def calculate_order_totals(items: List[ServiceOrderItem], discount_percentage: Optional[Decimal] = None) -> tuple[Decimal, Decimal, Decimal]:
    """Calcula subtotal, discount_amount e total da OS."""
    subtotal = sum(item.total_price for item in items)
    
    if discount_percentage:
        discount_amount = subtotal * (discount_percentage / 100)
    else:
        discount_amount = Decimal(0)
    
    total = subtotal - discount_amount
    
    return subtotal, discount_amount, total


@router.post("", response_model=ServiceOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_service_order(
    order_data: ServiceOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Cria nova Ordem de Serviço.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    """
    # Valida cliente
    customer_result = await db.execute(
        select(Customer).where(
            Customer.id == order_data.customer_id,
            Customer.organization_id == current_org_id,
            Customer.is_active == True
        )
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Valida loja
    org_id = await get_org_internal_id(db, current_org_id)
    store_result = await db.execute(
        select(Store).where(
            Store.id == order_data.store_id,
            Store.organization_id == org_id,
            Store.is_active == True
        )
    )
    store = store_result.scalar_one_or_none()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loja não encontrada"
        )
    
    # Gera número da OS
    order_number = await generate_order_number(db, current_org_id)
    
    # Cria OS
    new_order = ServiceOrder(
        organization_id=current_org_id,
        customer_id=order_data.customer_id,
        store_id=order_data.store_id,
        seller_id=current_staff.id,
        order_number=order_number,
        status=ServiceOrderStatus.DRAFT,
        discount_percentage=order_data.discount_percentage,
        max_discount_allowed=Decimal("10.0"),  # Limite padrão 10%
        notes=order_data.notes
    )
    
    db.add(new_order)
    await db.flush()  # Para obter o ID
    
    # Processa itens
    items_list = []
    for item_data in order_data.items:
        # Calcula total_price do item
        item_subtotal = item_data.unit_price * item_data.quantity
        item_total = item_subtotal - item_data.discount_amount
        
        # Cria item
        new_item = ServiceOrderItem(
            organization_id=current_org_id,
            service_order_id=new_order.id,
            item_type=item_data.item_type,
            product_frame_id=item_data.product_frame_id,
            product_lens_id=item_data.product_lens_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_amount=item_data.discount_amount,
            total_price=item_total,
            lens_spherical=item_data.lens_spherical,
            lens_cylindrical=item_data.lens_cylindrical,
            lens_axis=item_data.lens_axis,
            lens_addition=item_data.lens_addition,
            lens_side=item_data.lens_side
        )
        
        # Se for FRAME, valida estoque e reserva
        if item_data.item_type == "FRAME" and item_data.product_frame_id:
            inv_result = await db.execute(
                select(InventoryLevel).where(
                    InventoryLevel.store_id == order_data.store_id,
                    InventoryLevel.product_frame_id == item_data.product_frame_id,
                    InventoryLevel.organization_id == current_org_id
                )
            )
            inv_level = inv_result.scalar_one_or_none()
            
            if not inv_level:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estoque não encontrado para armação ID {item_data.product_frame_id}"
                )
            
            available = inv_level.quantity - inv_level.reserved_quantity
            if available < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estoque insuficiente. Disponível: {available}, Solicitado: {item_data.quantity}"
                )
            
            # Reserva estoque
            new_item.reserved_quantity = item_data.quantity
            new_item.reserved_at = datetime.utcnow()
            inv_level.reserved_quantity += item_data.quantity
        
        # Se for LENS, valida estoque na grid ou marca needs_purchasing
        elif item_data.item_type == "LENS" and item_data.product_lens_id:
            lens_result = await db.execute(
                select(ProductLens).where(
                    ProductLens.id == item_data.product_lens_id,
                    ProductLens.organization_id == current_org_id,
                    ProductLens.is_active == True
                )
            )
            lens = lens_result.scalar_one_or_none()
            
            if not lens:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Lente não encontrada"
                )
            
            # Se não for lab_order, valida estoque na grid
            if not lens.is_lab_order:
                if item_data.lens_spherical and item_data.lens_cylindrical:
                    grid_result = await db.execute(
                        select(LensStockGrid).where(
                            LensStockGrid.product_lens_id == item_data.product_lens_id,
                            LensStockGrid.spherical == item_data.lens_spherical,
                            LensStockGrid.cylindrical == item_data.lens_cylindrical,
                            LensStockGrid.organization_id == current_org_id
                        )
                    )
                    grid = grid_result.scalar_one_or_none()
                    
                    if not grid or grid.quantity < item_data.quantity:
                        new_item.needs_purchasing = True
            else:
                # Lente surfaçagem sempre precisa comprar
                new_item.needs_purchasing = True
        
        items_list.append(new_item)
        db.add(new_item)
    
    # Calcula totais
    new_order.subtotal, new_order.discount_amount, new_order.total = calculate_order_totals(items_list, order_data.discount_percentage)
    
    # Valida desconto
    if order_data.discount_percentage and order_data.discount_percentage > new_order.max_discount_allowed:
        # Requer aprovação (não bloqueia criação, mas marca que precisa aprovação)
        pass  # Será aprovado via endpoint específico
    
    await db.commit()
    await db.refresh(new_order)
    
    # Carrega itens para resposta
    await db.refresh(new_order)
    result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == new_order.id)
    )
    items = result.scalars().all()
    
    return build_service_order_response(new_order, items)


@router.get("", response_model=List[ServiceOrderResponse])
async def list_service_orders(
    status: Optional[ServiceOrderStatus] = Query(None, description="Filtrar por status"),
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    store_id: Optional[int] = Query(None, description="Filtrar por loja"),
    seller_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Lista Ordens de Serviço.
    
    **Permissões**: SELLER (apenas suas), STAFF, MANAGER ou ADMIN
    """
    query = select(ServiceOrder).where(
        ServiceOrder.organization_id == current_org_id,
        ServiceOrder.is_active == True
    )
    
    # SELLER vê apenas suas OS
    if current_staff.role.value == "SELLER":
        query = query.where(ServiceOrder.seller_id == current_staff.id)
    elif seller_id:
        query = query.where(ServiceOrder.seller_id == seller_id)
    
    if status:
        query = query.where(ServiceOrder.status == status)
    
    if customer_id:
        query = query.where(ServiceOrder.customer_id == customer_id)
    
    if store_id:
        query = query.where(ServiceOrder.store_id == store_id)
    
    query = query.order_by(ServiceOrder.created_at.desc())
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # Carrega itens para cada OS e constrói resposta manualmente
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
    
    # Constrói resposta manualmente para evitar lazy loading
    response_orders = []
    for order in orders:
        items = items_by_order.get(order.id, [])
        response_orders.append(build_service_order_response(order, items))
    
    return response_orders


@router.get("/{order_id}", response_model=ServiceOrderResponse)
async def get_service_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Obtém OS específica.
    
    **Permissões**: SELLER (apenas suas), STAFF, MANAGER ou ADMIN
    """
    query = select(ServiceOrder).where(
        ServiceOrder.id == order_id,
        ServiceOrder.organization_id == current_org_id,
        ServiceOrder.is_active == True
    )
    
    # SELLER só vê suas OS
    if current_staff.role.value == "SELLER":
        query = query.where(ServiceOrder.seller_id == current_staff.id)
    
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordem de Serviço não encontrada"
        )
    
    # Carrega itens
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order.id)
    )
    items = items_result.scalars().all()
    
    return build_service_order_response(order, items)


@router.patch("/{order_id}", response_model=ServiceOrderResponse)
async def update_service_order(
    order_id: int,
    order_data: ServiceOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Edita OS (apenas se status = DRAFT).
    
    **Permissões**: SELLER (apenas suas), STAFF, MANAGER ou ADMIN
    """
    # Busca OS
    query = select(ServiceOrder).where(
        ServiceOrder.id == order_id,
        ServiceOrder.organization_id == current_org_id,
        ServiceOrder.is_active == True
    )
    
    if current_staff.role.value == "SELLER":
        query = query.where(ServiceOrder.seller_id == current_staff.id)
    
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordem de Serviço não encontrada"
        )
    
    # Valida que está em DRAFT
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas OS em DRAFT podem ser editadas"
        )
    
    # Libera reservas antigas
    old_items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order_id)
    )
    old_items = old_items_result.scalars().all()
    
    for old_item in old_items:
        if old_item.item_type == "FRAME" and old_item.product_frame_id and old_item.reserved_quantity > 0:
            inv_result = await db.execute(
                select(InventoryLevel).where(
                    InventoryLevel.store_id == order.store_id,
                    InventoryLevel.product_frame_id == old_item.product_frame_id,
                    InventoryLevel.organization_id == current_org_id
                )
            )
            inv_level = inv_result.scalar_one_or_none()
            if inv_level:
                inv_level.reserved_quantity -= old_item.reserved_quantity
    
    # Remove itens antigos
    await db.execute(
        delete(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order_id)
    )
    
    # Atualiza campos básicos
    if order_data.notes is not None:
        order.notes = order_data.notes
    
    if order_data.discount_percentage is not None:
        order.discount_percentage = order_data.discount_percentage
    
    # Processa novos itens (se fornecidos)
    if order_data.items:
        items_list = []
        for item_data in order_data.items:
            item_subtotal = item_data.unit_price * item_data.quantity
            item_total = item_subtotal - item_data.discount_amount
            
            new_item = ServiceOrderItem(
                organization_id=current_org_id,
                service_order_id=order.id,
                item_type=item_data.item_type,
                product_frame_id=item_data.product_frame_id,
                product_lens_id=item_data.product_lens_id,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                discount_amount=item_data.discount_amount,
                total_price=item_total,
                lens_spherical=item_data.lens_spherical,
                lens_cylindrical=item_data.lens_cylindrical,
                lens_axis=item_data.lens_axis,
                lens_addition=item_data.lens_addition,
                lens_side=item_data.lens_side
            )
            
            # Reserva estoque se for FRAME
            if item_data.item_type == "FRAME" and item_data.product_frame_id:
                inv_result = await db.execute(
                    select(InventoryLevel).where(
                        InventoryLevel.store_id == order.store_id,
                        InventoryLevel.product_frame_id == item_data.product_frame_id,
                        InventoryLevel.organization_id == current_org_id
                    )
                )
                inv_level = inv_result.scalar_one_or_none()
                
                if inv_level:
                    available = inv_level.quantity - inv_level.reserved_quantity
                    if available < item_data.quantity:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Estoque insuficiente. Disponível: {available}, Solicitado: {item_data.quantity}"
                        )
                    
                    new_item.reserved_quantity = item_data.quantity
                    new_item.reserved_at = datetime.utcnow()
                    inv_level.reserved_quantity += item_data.quantity
            
            items_list.append(new_item)
            db.add(new_item)
        
        # Recalcula totais
        order.subtotal, order.discount_amount, order.total = calculate_order_totals(items_list, order_data.discount_percentage)
    else:
        # Recalcula apenas com desconto atualizado
        items_result = await db.execute(
            select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order_id)
        )
        existing_items = items_result.scalars().all()
        order.subtotal, order.discount_amount, order.total = calculate_order_totals(existing_items, order.discount_percentage)
    
    await db.commit()
    await db.refresh(order)
    
    # Carrega itens
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order.id)
    )
    items = items_result.scalars().all()
    
    return build_service_order_response(order, items)


@router.post("/{order_id}/approve-discount", response_model=ServiceOrderResponse)
async def approve_discount(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Aprova desconto acima do limite.
    
    **Permissões**: MANAGER ou ADMIN
    """
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
    
    # Aprova desconto
    order.discount_approved_by = current_staff.id
    
    # Recalcula totais
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order_id)
    )
    items = items_result.scalars().all()
    order.subtotal, order.discount_amount, order.total = calculate_order_totals(items, order.discount_percentage)
    
    await db.commit()
    await db.refresh(order)
    
    # Carrega itens
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order.id)
    )
    items = items_result.scalars().all()
    
    return build_service_order_response(order, items)


@router.post("/{order_id}/send-to-payment", response_model=ServiceOrderResponse)
async def send_to_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Envia OS para pagamento.
    
    **Permissões**: SELLER, STAFF, MANAGER ou ADMIN
    """
    query = select(ServiceOrder).where(
        ServiceOrder.id == order_id,
        ServiceOrder.organization_id == current_org_id,
        ServiceOrder.is_active == True
    )
    
    if current_staff.role.value == "SELLER":
        query = query.where(ServiceOrder.seller_id == current_staff.id)
    
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordem de Serviço não encontrada"
        )
    
    # Valida que está em DRAFT
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas OS em DRAFT podem ser enviadas para pagamento"
        )
    
    # Valida estoque final
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order_id)
    )
    items = items_result.scalars().all()
    
    for item in items:
        if item.item_type == "FRAME" and item.product_frame_id:
            inv_result = await db.execute(
                select(InventoryLevel).where(
                    InventoryLevel.store_id == order.store_id,
                    InventoryLevel.product_frame_id == item.product_frame_id,
                    InventoryLevel.organization_id == current_org_id
                )
            )
            inv_level = inv_result.scalar_one_or_none()
            
            if inv_level:
                available = inv_level.quantity - inv_level.reserved_quantity
                if available < item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Estoque insuficiente para armação. Disponível: {available}, Solicitado: {item.quantity}"
                    )
    
    # Atualiza status
    order.status = ServiceOrderStatus.PENDING
    
    await db.commit()
    await db.refresh(order)
    
    # Carrega itens
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order.id)
    )
    items = items_result.scalars().all()
    
    return build_service_order_response(order, items)


@router.patch("/{order_id}/status", response_model=ServiceOrderResponse)
async def update_service_order_status(
    order_id: int,
    status_data: ServiceOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Atualiza status da OS (para laboratório).
    
    **Permissões**: MANAGER ou ADMIN (futuro: LAB_TECH)
    """
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
    
    # Valida transições permitidas (simplificado - pode ser expandido)
    valid_transitions = {
        ServiceOrderStatus.PENDING: [ServiceOrderStatus.PAID],
        ServiceOrderStatus.PAID: [ServiceOrderStatus.AWAITING_LENS, ServiceOrderStatus.IN_PRODUCTION],
        ServiceOrderStatus.AWAITING_LENS: [ServiceOrderStatus.IN_PRODUCTION],
        ServiceOrderStatus.IN_PRODUCTION: [ServiceOrderStatus.READY],
        ServiceOrderStatus.READY: [ServiceOrderStatus.DELIVERED]
    }
    
    if order.status in valid_transitions:
        if status_data.status not in valid_transitions[order.status]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transição de {order.status} para {status_data.status} não é permitida"
            )
    
    # Atualiza status
    order.status = status_data.status
    
    if status_data.status == ServiceOrderStatus.READY:
        # TODO: Baixar estoque de lentes se houver quebra
        pass
    
    await db.commit()
    await db.refresh(order)
    
    # Carrega itens
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order.id)
    )
    items = items_result.scalars().all()
    
    return build_service_order_response(order, items)


@router.post("/{order_id}/cancel", response_model=ServiceOrderResponse)
async def cancel_service_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Cancela OS (estorno).
    
    **Permissões**: MANAGER ou ADMIN
    """
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
    
    # Libera todas as reservas de estoque
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
                inv_level.reserved_quantity -= item.reserved_quantity
    
    # Atualiza status
    order.status = ServiceOrderStatus.CANCELLED
    
    # TODO: Reverter lançamentos financeiros se já pago
    
    await db.commit()
    await db.refresh(order)
    
    # Carrega itens
    items_result = await db.execute(
        select(ServiceOrderItem).where(ServiceOrderItem.service_order_id == order.id)
    )
    items = items_result.scalars().all()
    
    return build_service_order_response(order, items)

