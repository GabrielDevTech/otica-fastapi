"""Endpoints para gestão de Service Orders (Ordens de Serviço)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import get_current_staff, require_staff_or_above, require_manager_or_admin
from app.models.service_order_model import (
    ServiceOrder,
    ServiceOrderItem,
    ServiceOrderStatus,
    ItemType,
    LensSide,
)
from app.models.staff_model import StaffMember, StaffRole
from app.models.customer_model import Customer
from app.models.store_model import Store
from app.models.product_model import ProductFrame, ProductLens, InventoryLevel, LensStockGrid
from app.schemas.service_order_schema import (
    ServiceOrderCreate,
    ServiceOrderUpdate,
    ServiceOrderResponse,
    ServiceOrderDetailResponse,
    ServiceOrderListResponse,
    ServiceOrderItemResponse,
    ServiceOrderItemCreateFrame,
    ServiceOrderItemCreateLens,
    ServiceOrderItemUpdate,
    DiscountRequest,
    CancelRequest,
)


router = APIRouter(prefix="/service-orders", tags=["service-orders"])


# ========== Funções Auxiliares ==========

async def generate_order_number(db: AsyncSession, organization_id: str) -> str:
    """Gera número único de OS no formato OS-YYYY-NNNN."""
    current_year = datetime.now().year
    
    # Busca a última OS do ano atual
    result = await db.execute(
        select(ServiceOrder).where(
            ServiceOrder.organization_id == organization_id,
            ServiceOrder.order_number.like(f"OS-{current_year}-%")
        ).order_by(ServiceOrder.order_number.desc())
    )
    last_order = result.scalar_one_or_none()
    
    if last_order:
        # Extrai o número sequencial
        try:
            last_number = int(last_order.order_number.split("-")[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    return f"OS-{current_year}-{next_number:04d}"


async def recalculate_order_totals(db: AsyncSession, service_order: ServiceOrder):
    """Recalcula subtotal e total da Service Order."""
    # Soma todos os itens
    result = await db.execute(
        select(func.sum(ServiceOrderItem.total_price)).where(
            ServiceOrderItem.service_order_id == service_order.id
        )
    )
    subtotal = result.scalar() or Decimal("0.00")
    
    # Atualiza subtotal
    service_order.subtotal = subtotal
    
    # Recalcula total (subtotal - desconto)
    service_order.total = subtotal - service_order.discount_amount
    
    # Recalcula percentual de desconto
    if subtotal > 0:
        service_order.discount_percentage = (service_order.discount_amount / subtotal) * 100
    else:
        service_order.discount_percentage = None
    
    await db.commit()
    await db.refresh(service_order)


async def reserve_frame_inventory(
    db: AsyncSession,
    organization_id: str,
    product_frame_id: int,
    store_id: int,
    quantity: int
) -> bool:
    """Reserva estoque de armação. Retorna True se reservou, False se não há estoque."""
    # Busca nível de estoque
    result = await db.execute(
        select(InventoryLevel).where(
            InventoryLevel.organization_id == organization_id,
            InventoryLevel.product_frame_id == product_frame_id,
            InventoryLevel.store_id == store_id
        )
    )
    inventory = result.scalar_one_or_none()
    
    if not inventory:
        # Cria nível de estoque se não existir
        inventory = InventoryLevel(
            organization_id=organization_id,
            product_frame_id=product_frame_id,
            store_id=store_id,
            quantity=0,
            reserved_quantity=0
        )
        db.add(inventory)
        await db.flush()
    
    # Verifica se há estoque disponível
    available = inventory.quantity - inventory.reserved_quantity
    if available < quantity:
        return False
    
    # Reserva estoque
    inventory.reserved_quantity += quantity
    await db.commit()
    await db.refresh(inventory)
    
    return True


async def release_frame_inventory(
    db: AsyncSession,
    organization_id: str,
    product_frame_id: int,
    store_id: int,
    quantity: int
):
    """Libera reserva de estoque de armação."""
    result = await db.execute(
        select(InventoryLevel).where(
            InventoryLevel.organization_id == organization_id,
            InventoryLevel.product_frame_id == product_frame_id,
            InventoryLevel.store_id == store_id
        )
    )
    inventory = result.scalar_one_or_none()
    
    if inventory and inventory.reserved_quantity >= quantity:
        inventory.reserved_quantity -= quantity
        await db.commit()


async def check_lens_stock(
    db: AsyncSession,
    organization_id: str,
    product_lens_id: int,
    store_id: int,
    spherical: Decimal,
    cylindrical: Decimal,
    axis: int,
    addition: Optional[Decimal] = None
) -> bool:
    """Verifica se há estoque de lente com os parâmetros especificados."""
    query = select(LensStockGrid).where(
        LensStockGrid.organization_id == organization_id,
        LensStockGrid.product_lens_id == product_lens_id,
        LensStockGrid.store_id == store_id,
        LensStockGrid.spherical == spherical,
        LensStockGrid.cylindrical == cylindrical,
        LensStockGrid.axis == axis
    )
    
    if addition is not None:
        query = query.where(LensStockGrid.addition == addition)
    else:
        query = query.where(LensStockGrid.addition.is_(None))
    
    result = await db.execute(query)
    stock = result.scalar_one_or_none()
    
    return stock is not None and stock.quantity > 0


async def get_max_discount_allowed(
    db: AsyncSession,
    organization_id: str,
    seller_id: int,
    store_id: int
) -> Decimal:
    """Obtém o limite máximo de desconto permitido para o seller."""
    # TODO: Implementar lógica de busca de max_discount_allowed
    # Por enquanto, retorna um valor padrão
    # Prioridade: Seller > Loja > Global
    return Decimal("100.00")


# ========== Endpoints ==========

@router.get("", response_model=ServiceOrderListResponse)
async def list_service_orders(
    status_filter: Optional[ServiceOrderStatus] = Query(None, alias="status", description="Filtrar por status"),
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    store_id: Optional[int] = Query(None, description="Filtrar por loja"),
    seller_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    q: Optional[str] = Query(None, description="Busca por número da OS ou nome do cliente"),
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Lista todas as Service Orders da organização.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    
    **Regras:**
    - Seller só vê suas próprias OS
    - Manager/Admin vê todas as OS da organização
    """
    # Base query
    query = select(ServiceOrder).where(
        ServiceOrder.organization_id == current_org_id
    )
    
    # Filtro por role: Seller só vê suas próprias OS
    if current_staff.role == StaffRole.STAFF:
        query = query.where(ServiceOrder.seller_id == current_staff.id)
    
    # Filtros opcionais
    if status_filter:
        query = query.where(ServiceOrder.status == status_filter)
    if customer_id:
        query = query.where(ServiceOrder.customer_id == customer_id)
    if store_id:
        query = query.where(ServiceOrder.store_id == store_id)
    if seller_id:
        # Manager/Admin pode filtrar por seller
        if current_staff.role in [StaffRole.MANAGER, StaffRole.ADMIN]:
            query = query.where(ServiceOrder.seller_id == seller_id)
    
    # Busca textual
    if q:
        search_term = f"%{q}%"
        # Busca por número da OS ou nome do cliente
        # Usa subquery para buscar customer_id que correspondem ao termo
        customer_subquery = select(Customer.id).where(
            Customer.organization_id == current_org_id,
            Customer.full_name.ilike(search_term)
        )
        
        query = query.where(
            or_(
                ServiceOrder.order_number.ilike(search_term),
                ServiceOrder.customer_id.in_(customer_subquery)
            )
        )
    
    # Contagem total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginação e ordenação
    query = query.order_by(ServiceOrder.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Executa query
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # Prepara resposta com dados relacionados
    items = []
    for order in orders:
        # Busca dados do cliente
        customer_result = await db.execute(
            select(Customer).where(Customer.id == order.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        
        # Busca dados da loja
        store_result = await db.execute(
            select(Store).where(Store.id == order.store_id)
        )
        store = store_result.scalar_one_or_none()
        
        # Busca dados do vendedor
        seller_result = await db.execute(
            select(StaffMember).where(StaffMember.id == order.seller_id)
        )
        seller = seller_result.scalar_one_or_none()
        
        # Conta itens
        items_count_result = await db.execute(
            select(func.count(ServiceOrderItem.id)).where(
                ServiceOrderItem.service_order_id == order.id
            )
        )
        items_count = items_count_result.scalar() or 0
        
        items.append(ServiceOrderResponse(
            id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            customer_name=customer.full_name if customer else None,
            customer_cpf=customer.cpf if customer else None,
            store_id=order.store_id,
            store_name=store.name if store else None,
            seller_id=order.seller_id,
            seller_name=seller.full_name if seller else None,
            status=order.status,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            discount_percentage=order.discount_percentage,
            total=order.total,
            max_discount_allowed=order.max_discount_allowed,
            discount_approved_by=order.discount_approved_by,
            created_at=order.created_at,
            paid_at=order.paid_at,
            delivered_at=order.delivered_at,
            notes=order.notes,
            items_count=items_count,
        ))
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return ServiceOrderListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/{id}", response_model=ServiceOrderDetailResponse)
async def get_service_order(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Retorna os detalhes completos de uma Service Order.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    
    **Regras:**
    - Seller só pode ver suas próprias OS
    - Manager/Admin podem ver todas
    """
    result = await db.execute(
        select(ServiceOrder)
        .options(
            selectinload(ServiceOrder.items),
            joinedload(ServiceOrder.customer),
            joinedload(ServiceOrder.store),
            joinedload(ServiceOrder.seller)
        )
        .where(
            ServiceOrder.id == id,
            ServiceOrder.organization_id == current_org_id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Order não encontrada"
        )
    
    # Verifica permissão: Seller só vê suas próprias OS
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para visualizar esta Service Order"
        )
    
    # Prepara itens
    items = []
    for item in order.items:
        items.append(ServiceOrderItemResponse(
            id=item.id,
            item_type=item.item_type,
            product_frame_id=item.product_frame_id,
            product_lens_id=item.product_lens_id,
            product_name=item.product_name,
            product_reference_code=item.product_reference_code,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_amount=item.discount_amount,
            total_price=item.total_price,
            reserved_quantity=item.reserved_quantity,
            reserved_at=item.reserved_at,
            lens_spherical=item.lens_spherical,
            lens_cylindrical=item.lens_cylindrical,
            lens_axis=item.lens_axis,
            lens_addition=item.lens_addition,
            lens_side=item.lens_side,
            needs_purchasing=item.needs_purchasing,
        ))
    
    return ServiceOrderDetailResponse(
        id=order.id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        customer=order.customer,
        store_id=order.store_id,
        store=order.store,
        seller_id=order.seller_id,
        seller=order.seller,
        status=order.status,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        discount_percentage=order.discount_percentage,
        total=order.total,
        max_discount_allowed=order.max_discount_allowed,
        discount_approved_by=order.discount_approved_by,
        created_at=order.created_at,
        paid_at=order.paid_at,
        delivered_at=order.delivered_at,
        notes=order.notes,
        items=items,
    )


@router.post("", response_model=ServiceOrderDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_service_order(
    order_data: ServiceOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Cria uma nova Service Order no status DRAFT.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
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
            detail="Cliente não encontrado ou inativo"
        )
    
    # Valida loja
    store_result = await db.execute(
        select(Store).where(
            Store.id == order_data.store_id,
            Store.organization_id == current_org_id,
            Store.is_active == True
        )
    )
    store = store_result.scalar_one_or_none()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loja não encontrada ou inativa"
        )
    
    # Gera número da OS
    order_number = await generate_order_number(db, current_org_id)
    
    # Obtém limite de desconto
    max_discount = await get_max_discount_allowed(db, current_org_id, current_staff.id, order_data.store_id)
    
    # Cria Service Order
    new_order = ServiceOrder(
        organization_id=current_org_id,
        customer_id=order_data.customer_id,
        store_id=order_data.store_id,
        seller_id=current_staff.id,
        order_number=order_number,
        status=ServiceOrderStatus.DRAFT,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total=Decimal("0.00"),
        max_discount_allowed=max_discount,
        notes=order_data.notes,
    )
    
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    # Busca dados relacionados para resposta
    await db.refresh(new_order, ["customer", "store", "seller"])
    
    return ServiceOrderDetailResponse(
        id=new_order.id,
        order_number=new_order.order_number,
        customer_id=new_order.customer_id,
        customer=new_order.customer,
        store_id=new_order.store_id,
        store=new_order.store,
        seller_id=new_order.seller_id,
        seller=new_order.seller,
        status=new_order.status,
        subtotal=new_order.subtotal,
        discount_amount=new_order.discount_amount,
        discount_percentage=new_order.discount_percentage,
        total=new_order.total,
        max_discount_allowed=new_order.max_discount_allowed,
        discount_approved_by=new_order.discount_approved_by,
        created_at=new_order.created_at,
        paid_at=new_order.paid_at,
        delivered_at=new_order.delivered_at,
        notes=new_order.notes,
        items=[],
    )


@router.patch("/{id}", response_model=ServiceOrderDetailResponse)
async def update_service_order(
    id: int,
    order_data: ServiceOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Atualiza dados básicos da Service Order.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    
    **Regras:**
    - Só pode editar se status = DRAFT
    - Seller só pode editar suas próprias OS
    - Não pode alterar store_id, seller_id ou order_number
    """
    result = await db.execute(
        select(ServiceOrder).where(
            ServiceOrder.id == id,
            ServiceOrder.organization_id == current_org_id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Order não encontrada"
        )
    
    # Verifica se está em DRAFT
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service Order só pode ser editada enquanto estiver em DRAFT"
        )
    
    # Verifica permissão: Seller só edita suas próprias OS
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para editar esta Service Order"
        )
    
    # Atualiza campos
    if order_data.customer_id is not None:
        # Valida novo cliente
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
                detail="Cliente não encontrado ou inativo"
            )
        order.customer_id = order_data.customer_id
    
    if order_data.notes is not None:
        order.notes = order_data.notes
    
    await db.commit()
    await db.refresh(order)
    await db.refresh(order, ["customer", "store", "seller", "items"])
    
    # Prepara itens
    items = []
    for item in order.items:
        items.append(ServiceOrderItemResponse(
            id=item.id,
            item_type=item.item_type,
            product_frame_id=item.product_frame_id,
            product_lens_id=item.product_lens_id,
            product_name=item.product_name,
            product_reference_code=item.product_reference_code,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_amount=item.discount_amount,
            total_price=item.total_price,
            reserved_quantity=item.reserved_quantity,
            reserved_at=item.reserved_at,
            lens_spherical=item.lens_spherical,
            lens_cylindrical=item.lens_cylindrical,
            lens_axis=item.lens_axis,
            lens_addition=item.lens_addition,
            lens_side=item.lens_side,
            needs_purchasing=item.needs_purchasing,
        ))
    
    return ServiceOrderDetailResponse(
        id=order.id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        customer=order.customer,
        store_id=order.store_id,
        store=order.store,
        seller_id=order.seller_id,
        seller=order.seller,
        status=order.status,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        discount_percentage=order.discount_percentage,
        total=order.total,
        max_discount_allowed=order.max_discount_allowed,
        discount_approved_by=order.discount_approved_by,
        created_at=order.created_at,
        paid_at=order.paid_at,
        delivered_at=order.delivered_at,
        notes=order.notes,
        items=items,
    )


@router.post("/{id}/items", response_model=ServiceOrderItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_service_order(
    id: int,
    item_data: ServiceOrderItemCreateFrame | ServiceOrderItemCreateLens,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Adiciona um item (Armação ou Lente) à Service Order."""
    result = await db.execute(
        select(ServiceOrder).where(
            ServiceOrder.id == id,
            ServiceOrder.organization_id == current_org_id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order não encontrada")
    
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível adicionar itens em Service Orders com status DRAFT")
    
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar esta Service Order")
    
    if item_data.item_type == ItemType.FRAME:
        frame_result = await db.execute(
            select(ProductFrame).where(
                ProductFrame.id == item_data.product_frame_id,
                ProductFrame.organization_id == current_org_id,
                ProductFrame.is_active == True
            )
        )
        frame = frame_result.scalar_one_or_none()
        if not frame:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Armação não encontrada ou inativa")
        
        reserved = await reserve_frame_inventory(db, current_org_id, item_data.product_frame_id, order.store_id, item_data.quantity)
        if not reserved:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estoque insuficiente para esta armação")
        
        new_item = ServiceOrderItem(
            service_order_id=order.id,
            item_type=ItemType.FRAME,
            product_frame_id=item_data.product_frame_id,
            product_lens_id=None,
            product_name=frame.name,
            product_reference_code=frame.reference_code,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_amount=Decimal("0.00"),
            total_price=item_data.unit_price * item_data.quantity,
            reserved_quantity=item_data.quantity,
            reserved_at=datetime.now(),
            needs_purchasing=False,
        )
    else:
        lens_result = await db.execute(
            select(ProductLens).where(
                ProductLens.id == item_data.product_lens_id,
                ProductLens.organization_id == current_org_id,
                ProductLens.is_active == True
            )
        )
        lens = lens_result.scalar_one_or_none()
        if not lens:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lente não encontrada ou inativa")
        
        needs_purchasing = lens.is_lab_order
        if not needs_purchasing:
            has_stock = await check_lens_stock(db, current_org_id, item_data.product_lens_id, order.store_id, item_data.lens_spherical, item_data.lens_cylindrical, item_data.lens_axis, item_data.lens_addition)
            if not has_stock:
                needs_purchasing = True
        
        new_item = ServiceOrderItem(
            service_order_id=order.id,
            item_type=ItemType.LENS,
            product_frame_id=None,
            product_lens_id=item_data.product_lens_id,
            product_name=lens.name,
            product_reference_code=lens.reference_code,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_amount=Decimal("0.00"),
            total_price=item_data.unit_price * item_data.quantity,
            reserved_quantity=0,
            reserved_at=None,
            lens_spherical=item_data.lens_spherical,
            lens_cylindrical=item_data.lens_cylindrical,
            lens_axis=item_data.lens_axis,
            lens_addition=item_data.lens_addition,
            lens_side=item_data.lens_side,
            needs_purchasing=needs_purchasing,
        )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    await recalculate_order_totals(db, order)
    
    return ServiceOrderItemResponse(
        id=new_item.id,
        item_type=new_item.item_type,
        product_frame_id=new_item.product_frame_id,
        product_lens_id=new_item.product_lens_id,
        product_name=new_item.product_name,
        product_reference_code=new_item.product_reference_code,
        quantity=new_item.quantity,
        unit_price=new_item.unit_price,
        discount_amount=new_item.discount_amount,
        total_price=new_item.total_price,
        reserved_quantity=new_item.reserved_quantity,
        reserved_at=new_item.reserved_at,
        lens_spherical=new_item.lens_spherical,
        lens_cylindrical=new_item.lens_cylindrical,
        lens_axis=new_item.lens_axis,
        lens_addition=new_item.lens_addition,
        lens_side=new_item.lens_side,
        needs_purchasing=new_item.needs_purchasing,
    )


@router.delete("/{id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_service_order(
    id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Remove um item da Service Order e libera a reserva de estoque."""
    result = await db.execute(
        select(ServiceOrder).where(ServiceOrder.id == id, ServiceOrder.organization_id == current_org_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order não encontrada")
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível remover itens em Service Orders com status DRAFT")
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar esta Service Order")
    
    item_result = await db.execute(select(ServiceOrderItem).where(ServiceOrderItem.id == item_id, ServiceOrderItem.service_order_id == id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado")
    
    if item.item_type == ItemType.FRAME and item.product_frame_id and item.reserved_quantity > 0:
        await release_frame_inventory(db, current_org_id, item.product_frame_id, order.store_id, item.reserved_quantity)
    
    # Remove item
    await db.execute(delete(ServiceOrderItem).where(ServiceOrderItem.id == item_id))
    await db.commit()
    await recalculate_order_totals(db, order)


@router.patch("/{id}/items/{item_id}", response_model=ServiceOrderItemResponse)
async def update_service_order_item(
    id: int,
    item_id: int,
    item_data: ServiceOrderItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Atualiza um item existente."""
    result = await db.execute(select(ServiceOrder).where(ServiceOrder.id == id, ServiceOrder.organization_id == current_org_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order não encontrada")
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível atualizar itens em Service Orders com status DRAFT")
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar esta Service Order")
    
    item_result = await db.execute(select(ServiceOrderItem).where(ServiceOrderItem.id == item_id, ServiceOrderItem.service_order_id == id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado")
    
    old_quantity = item.quantity
    if item_data.quantity is not None:
        item.quantity = item_data.quantity
    if item_data.unit_price is not None:
        item.unit_price = item_data.unit_price
    if item_data.discount_amount is not None:
        item.discount_amount = item_data.discount_amount
    
    item.total_price = (item.unit_price * item.quantity) - item.discount_amount
    
    if item.item_type == ItemType.FRAME and item.product_frame_id:
        if item_data.quantity is not None and item_data.quantity != old_quantity:
            diff = item_data.quantity - old_quantity
            if diff > 0:
                reserved = await reserve_frame_inventory(db, current_org_id, item.product_frame_id, order.store_id, diff)
                if not reserved:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estoque insuficiente para esta quantidade")
                item.reserved_quantity += diff
            elif diff < 0:
                await release_frame_inventory(db, current_org_id, item.product_frame_id, order.store_id, abs(diff))
                item.reserved_quantity += diff
    
    await db.commit()
    await db.refresh(item)
    await recalculate_order_totals(db, order)
    
    return ServiceOrderItemResponse(
        id=item.id, item_type=item.item_type, product_frame_id=item.product_frame_id, product_lens_id=item.product_lens_id,
        product_name=item.product_name, product_reference_code=item.product_reference_code, quantity=item.quantity,
        unit_price=item.unit_price, discount_amount=item.discount_amount, total_price=item.total_price,
        reserved_quantity=item.reserved_quantity, reserved_at=item.reserved_at, lens_spherical=item.lens_spherical,
        lens_cylindrical=item.lens_cylindrical, lens_axis=item.lens_axis, lens_addition=item.lens_addition,
        lens_side=item.lens_side, needs_purchasing=item.needs_purchasing,
    )


@router.post("/{id}/discount", response_model=ServiceOrderDetailResponse)
async def apply_discount_to_service_order(
    id: int,
    discount_data: DiscountRequest,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Aplica desconto na Service Order."""
    result = await db.execute(select(ServiceOrder).where(ServiceOrder.id == id, ServiceOrder.organization_id == current_org_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order não encontrada")
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível aplicar desconto em Service Orders com status DRAFT")
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar esta Service Order")
    
    if discount_data.discount_amount is not None:
        discount_amount = discount_data.discount_amount
        if discount_amount > order.subtotal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Desconto não pode ser maior que o subtotal")
        discount_percentage = (discount_amount / order.subtotal) * 100 if order.subtotal > 0 else 0
    elif discount_data.discount_percentage is not None:
        discount_percentage = discount_data.discount_percentage
        discount_amount = (order.subtotal * discount_percentage) / 100
        if discount_amount > order.subtotal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Desconto calculado excede o subtotal")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deve informar discount_amount ou discount_percentage")
    
    max_discount = order.max_discount_allowed or Decimal("0.00")
    if discount_amount > max_discount:
        if current_staff.role == StaffRole.STAFF:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Desconto excede limite permitido. Requer aprovação de gerente.")
        else:
            order.discount_approved_by = current_staff.id
    
    order.discount_amount = discount_amount
    order.discount_percentage = discount_percentage
    order.total = order.subtotal - discount_amount
    
    await db.commit()
    await db.refresh(order)
    await db.refresh(order, ["customer", "store", "seller", "items"])
    
    items = [ServiceOrderItemResponse(id=i.id, item_type=i.item_type, product_frame_id=i.product_frame_id, product_lens_id=i.product_lens_id, product_name=i.product_name, product_reference_code=i.product_reference_code, quantity=i.quantity, unit_price=i.unit_price, discount_amount=i.discount_amount, total_price=i.total_price, reserved_quantity=i.reserved_quantity, reserved_at=i.reserved_at, lens_spherical=i.lens_spherical, lens_cylindrical=i.lens_cylindrical, lens_axis=i.lens_axis, lens_addition=i.lens_addition, lens_side=i.lens_side, needs_purchasing=i.needs_purchasing) for i in order.items]
    
    return ServiceOrderDetailResponse(id=order.id, order_number=order.order_number, customer_id=order.customer_id, customer=order.customer, store_id=order.store_id, store=order.store, seller_id=order.seller_id, seller=order.seller, status=order.status, subtotal=order.subtotal, discount_amount=order.discount_amount, discount_percentage=order.discount_percentage, total=order.total, max_discount_allowed=order.max_discount_allowed, discount_approved_by=order.discount_approved_by, created_at=order.created_at, paid_at=order.paid_at, delivered_at=order.delivered_at, notes=order.notes, items=items)


@router.post("/{id}/send-to-payment", response_model=ServiceOrderDetailResponse)
async def send_service_order_to_payment(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Altera o status de DRAFT para PENDING."""
    result = await db.execute(select(ServiceOrder).where(ServiceOrder.id == id, ServiceOrder.organization_id == current_org_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order não encontrada")
    if order.status != ServiceOrderStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service Order deve estar em DRAFT para ser enviada para pagamento")
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar esta Service Order")
    
    items_count_result = await db.execute(select(func.count(ServiceOrderItem.id)).where(ServiceOrderItem.service_order_id == order.id))
    items_count = items_count_result.scalar() or 0
    if items_count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service Order deve ter pelo menos 1 item")
    if order.total <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total da Service Order deve ser maior que zero")
    
    order.status = ServiceOrderStatus.PENDING
    await db.commit()
    await db.refresh(order)
    await db.refresh(order, ["customer", "store", "seller", "items"])
    
    items = [ServiceOrderItemResponse(id=i.id, item_type=i.item_type, product_frame_id=i.product_frame_id, product_lens_id=i.product_lens_id, product_name=i.product_name, product_reference_code=i.product_reference_code, quantity=i.quantity, unit_price=i.unit_price, discount_amount=i.discount_amount, total_price=i.total_price, reserved_quantity=i.reserved_quantity, reserved_at=i.reserved_at, lens_spherical=i.lens_spherical, lens_cylindrical=i.lens_cylindrical, lens_axis=i.lens_axis, lens_addition=i.lens_addition, lens_side=i.lens_side, needs_purchasing=i.needs_purchasing) for i in order.items]
    
    return ServiceOrderDetailResponse(id=order.id, order_number=order.order_number, customer_id=order.customer_id, customer=order.customer, store_id=order.store_id, store=order.store, seller_id=order.seller_id, seller=order.seller, status=order.status, subtotal=order.subtotal, discount_amount=order.discount_amount, discount_percentage=order.discount_percentage, total=order.total, max_discount_allowed=order.max_discount_allowed, discount_approved_by=order.discount_approved_by, created_at=order.created_at, paid_at=order.paid_at, delivered_at=order.delivered_at, notes=order.notes, items=items)


@router.post("/{id}/cancel", response_model=ServiceOrderDetailResponse)
async def cancel_service_order(
    id: int,
    cancel_data: Optional[CancelRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Cancela uma Service Order. Libera todas as reservas de estoque."""
    result = await db.execute(select(ServiceOrder).options(selectinload(ServiceOrder.items)).where(ServiceOrder.id == id, ServiceOrder.organization_id == current_org_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order não encontrada")
    if order.status not in [ServiceOrderStatus.DRAFT, ServiceOrderStatus.PENDING]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service Order só pode ser cancelada se estiver em DRAFT ou PENDING")
    if current_staff.role == StaffRole.STAFF and order.seller_id != current_staff.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para cancelar esta Service Order")
    
    for item in order.items:
        if item.item_type == ItemType.FRAME and item.product_frame_id and item.reserved_quantity > 0:
            await release_frame_inventory(db, current_org_id, item.product_frame_id, order.store_id, item.reserved_quantity)
            item.reserved_quantity = 0
            item.reserved_at = None
    
    order.status = ServiceOrderStatus.CANCELLED
    if cancel_data and cancel_data.reason:
        if order.notes:
            order.notes = f"{order.notes}\n[CANCELADO: {cancel_data.reason}]"
        else:
            order.notes = f"[CANCELADO: {cancel_data.reason}]"
    
    await db.commit()
    await db.refresh(order)
    await db.refresh(order, ["customer", "store", "seller", "items"])
    
    items = [ServiceOrderItemResponse(id=i.id, item_type=i.item_type, product_frame_id=i.product_frame_id, product_lens_id=i.product_lens_id, product_name=i.product_name, product_reference_code=i.product_reference_code, quantity=i.quantity, unit_price=i.unit_price, discount_amount=i.discount_amount, total_price=i.total_price, reserved_quantity=i.reserved_quantity, reserved_at=i.reserved_at, lens_spherical=i.lens_spherical, lens_cylindrical=i.lens_cylindrical, lens_axis=i.lens_axis, lens_addition=i.lens_addition, lens_side=i.lens_side, needs_purchasing=i.needs_purchasing) for i in order.items]
    
    return ServiceOrderDetailResponse(id=order.id, order_number=order.order_number, customer_id=order.customer_id, customer=order.customer, store_id=order.store_id, store=order.store, seller_id=order.seller_id, seller=order.seller, status=order.status, subtotal=order.subtotal, discount_amount=order.discount_amount, discount_percentage=order.discount_percentage, total=order.total, max_discount_allowed=order.max_discount_allowed, discount_approved_by=order.discount_approved_by, created_at=order.created_at, paid_at=order.paid_at, delivered_at=order.delivered_at, notes=order.notes, items=items)

