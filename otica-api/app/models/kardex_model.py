"""Model de Kardex (Histórico de Movimentação de Estoque)."""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_class import BaseModel


class KardexType(str, enum.Enum):
    """Tipo de movimentação no Kardex."""
    ENTRY = "ENTRY"            # Entrada (compra, ajuste positivo)
    EXIT = "EXIT"              # Saída (venda, ajuste negativo)
    RESERVATION = "RESERVATION"  # Reserva
    RELEASE = "RELEASE"        # Liberação de reserva


class Kardex(BaseModel):
    """Model para histórico de movimentações de estoque."""
    
    __tablename__ = "kardex"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_frame_id = Column(Integer, ForeignKey("products_frames.id", ondelete="CASCADE"), nullable=True, index=True)
    product_lens_id = Column(Integer, ForeignKey("products_lenses.id", ondelete="CASCADE"), nullable=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Dados
    movement_type = Column(String(20), nullable=False, doc="ENTRY, EXIT, RESERVATION, RELEASE")
    quantity = Column(Integer, nullable=False, doc="Quantidade movimentada (positivo ou negativo)")
    balance_before = Column(Integer, nullable=False, doc="Saldo antes da movimentação")
    balance_after = Column(Integer, nullable=False, doc="Saldo após a movimentação")
    
    # Rastreabilidade
    moved_by = Column(Integer, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes = Column(String(255), nullable=True)
    
    # Relationships
    store = relationship("Store", backref="kardex")
    product_frame = relationship("ProductFrame", backref="kardex")
    product_lens = relationship("ProductLens", backref="kardex")
    sale = relationship("Sale", backref="kardex")
    service_order = relationship("ServiceOrder", backref="kardex")
    staff = relationship("StaffMember", backref="kardex")
    
    __table_args__ = (
        Index('idx_kardex_store_date', 'store_id', 'movement_date'),
        Index('idx_kardex_product', 'product_frame_id', 'movement_date'),
        Index('idx_kardex_org_date', 'organization_id', 'movement_date'),
    )

