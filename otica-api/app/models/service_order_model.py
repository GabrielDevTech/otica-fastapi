"""Models para Service Orders (Ordens de Serviço)."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base_class import BaseModel


class ServiceOrderStatus(str, enum.Enum):
    """Status da Service Order."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PAID = "PAID"
    AWAITING_LENS = "AWAITING_LENS"
    IN_PRODUCTION = "IN_PRODUCTION"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ItemType(str, enum.Enum):
    """Tipo de item da Service Order."""
    FRAME = "FRAME"
    LENS = "LENS"


class LensSide(str, enum.Enum):
    """Lado da lente."""
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BOTH = "BOTH"


class ServiceOrder(BaseModel):
    """Model para Service Orders (Ordens de Serviço)."""
    
    __tablename__ = "service_orders"
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("staff_members.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Campos da OS
    order_number = Column(String(50), unique=True, nullable=False, index=True, doc="Número da OS (ex: OS-2024-001)")
    status = Column(Enum(ServiceOrderStatus), default=ServiceOrderStatus.DRAFT, nullable=False, index=True)
    
    # Valores financeiros
    subtotal = Column(Numeric(10, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    discount_percentage = Column(Numeric(5, 2), nullable=True)
    total = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Controle de desconto
    max_discount_allowed = Column(Numeric(10, 2), nullable=True, doc="Limite máximo de desconto permitido")
    discount_approved_by = Column(Integer, ForeignKey("staff_members.id", ondelete="SET NULL"), nullable=True)
    
    # Datas importantes
    paid_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Observações
    notes = Column(String, nullable=True)
    
    # Relationships
    customer = relationship("Customer", backref="service_orders")
    store = relationship("Store", backref="service_orders")
    seller = relationship("StaffMember", foreign_keys=[seller_id], backref="service_orders_sold")
    approver = relationship("StaffMember", foreign_keys=[discount_approved_by], backref="service_orders_approved")
    items = relationship("ServiceOrderItem", back_populates="service_order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_service_order_org_status', 'organization_id', 'status'),
        Index('idx_service_order_org_customer', 'organization_id', 'customer_id'),
        Index('idx_service_order_org_seller', 'organization_id', 'seller_id'),
        Index('idx_service_order_org_store', 'organization_id', 'store_id'),
    )


class ServiceOrderItem(BaseModel):
    """Model para itens de Service Order (Armação ou Lente)."""
    
    __tablename__ = "service_order_items"
    
    # Relacionamento com Service Order
    service_order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tipo de item
    item_type = Column(Enum(ItemType), nullable=False, index=True)
    
    # Relacionamentos com produtos (um ou outro será preenchido)
    product_frame_id = Column(Integer, ForeignKey("products_frames.id", ondelete="RESTRICT"), nullable=True, index=True)
    product_lens_id = Column(Integer, ForeignKey("products_lenses.id", ondelete="RESTRICT"), nullable=True, index=True)
    
    # Informações do produto (cache para performance)
    product_name = Column(String(255), nullable=False, doc="Nome do produto (cache)")
    product_reference_code = Column(String(100), nullable=True, doc="Código de referência do produto")
    
    # Quantidade e preços
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Reserva de estoque (para armações)
    reserved_quantity = Column(Integer, default=0, nullable=False, doc="Quantidade reservada no estoque")
    reserved_at = Column(DateTime(timezone=True), nullable=True, doc="Data/hora da reserva")
    
    # Parâmetros de lente (quando item_type = LENS)
    lens_spherical = Column(Numeric(6, 2), nullable=True, doc="Esférico da lente")
    lens_cylindrical = Column(Numeric(6, 2), nullable=True, doc="Cilíndrico da lente")
    lens_axis = Column(Integer, nullable=True, doc="Eixo da lente (0-180)")
    lens_addition = Column(Numeric(6, 2), nullable=True, doc="Adição (para multifocais)")
    lens_side = Column(Enum(LensSide), nullable=True, doc="Lado da lente: LEFT, RIGHT, BOTH")
    
    # Controle de lente
    needs_purchasing = Column(Boolean, default=False, nullable=False, doc="Se true, lente precisa ser comprada (surfaçagem)")
    
    # Relationships
    service_order = relationship("ServiceOrder", back_populates="items")
    product_frame = relationship("ProductFrame", backref="service_order_items")
    product_lens = relationship("ProductLens", backref="service_order_items")
    
    __table_args__ = (
        Index('idx_service_order_item_type', 'service_order_id', 'item_type'),
    )

