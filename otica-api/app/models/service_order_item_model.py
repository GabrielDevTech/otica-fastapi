"""Model de ServiceOrderItem (Item da Ordem de Serviço)."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class ServiceOrderItem(BaseModel):
    """Model para itens de uma Ordem de Serviço."""
    
    __tablename__ = "service_order_items"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    service_order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tipo de item
    item_type = Column(String(20), nullable=False, doc="FRAME, LENS, SERVICE")
    
    # Produto (pode ser frame ou lens)
    product_frame_id = Column(Integer, ForeignKey("products_frames.id", ondelete="SET NULL"), nullable=True)
    product_lens_id = Column(Integer, ForeignKey("products_lenses.id", ondelete="SET NULL"), nullable=True)
    
    # Quantidade e preços
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Reserva de estoque
    reserved_quantity = Column(Integer, default=0, nullable=False, doc="Quantidade reservada em inventory_levels")
    reserved_at = Column(DateTime(timezone=True), nullable=True, doc="Quando foi reservado")
    
    # Lente específica
    lens_spherical = Column(Numeric(5, 2), nullable=True, doc="Esférico")
    lens_cylindrical = Column(Numeric(5, 2), nullable=True, doc="Cilíndrico")
    lens_axis = Column(Integer, nullable=True, doc="Eixo")
    lens_addition = Column(Numeric(5, 2), nullable=True, doc="Adição")
    lens_side = Column(String(10), nullable=True, doc="OD, OE, AMBOS")
    
    # Flags
    needs_purchasing = Column(Boolean, default=False, nullable=False, doc="Lente surfaçagem precisa comprar")
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    service_order = relationship("ServiceOrder", back_populates="items")
    product_frame = relationship("ProductFrame", backref="order_items")
    product_lens = relationship("ProductLens", backref="order_items")
    
    __table_args__ = (
        Index('idx_soi_order', 'service_order_id', 'item_type'),
        Index('idx_soi_reserved', 'reserved_quantity', 'reserved_at'),
    )

