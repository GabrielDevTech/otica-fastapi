"""Model de ServiceOrder (Ordem de Serviço)."""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Text, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_class import BaseModel


class ServiceOrderStatus(str, enum.Enum):
    """Status da Ordem de Serviço."""
    DRAFT = "DRAFT"                    # Rascunho (pode editar)
    PENDING = "PENDING"                # Aguardando pagamento
    PAID = "PAID"                      # Paga, aguardando montagem
    AWAITING_LENS = "AWAITING_LENS"    # Aguardando lente (surfaçagem)
    IN_PRODUCTION = "IN_PRODUCTION"    # Em produção
    READY = "READY"                    # Pronto / Controle qualidade
    DELIVERED = "DELIVERED"            # Entregue
    CANCELLED = "CANCELLED"            # Cancelada


class ServiceOrder(BaseModel):
    """Model para Ordens de Serviço."""
    
    __tablename__ = "service_orders"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status e controle
    status = Column(Enum(ServiceOrderStatus), default=ServiceOrderStatus.DRAFT, nullable=False)
    order_number = Column(String(50), nullable=False, unique=True, index=True, doc="Número da OS (ex: OS-2024-001)")
    
    # Valores
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    discount_percentage = Column(Numeric(5, 2), nullable=True, doc="Percentual de desconto aplicado")
    total = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Controle de desconto
    discount_approved_by = Column(Integer, ForeignKey("staff_members.id", ondelete="SET NULL"), nullable=True, doc="Quem aprovou desconto acima do limite")
    max_discount_allowed = Column(Numeric(5, 2), nullable=True, default=10.0, doc="Limite de desconto (%)")
    
    # Datas
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Observações
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    customer = relationship("Customer", backref="service_orders")
    store = relationship("Store", backref="service_orders")
    seller = relationship("StaffMember", foreign_keys=[seller_id], backref="service_orders")
    approver = relationship("StaffMember", foreign_keys=[discount_approved_by])
    items = relationship("ServiceOrderItem", back_populates="service_order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_so_org_status', 'organization_id', 'status'),
        Index('idx_so_store_date', 'store_id', 'created_at'),
        Index('idx_so_seller', 'seller_id', 'created_at'),
    )

