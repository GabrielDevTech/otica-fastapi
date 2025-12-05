"""Model de InventoryLevel (Nível de Estoque)."""
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class InventoryLevel(BaseModel):
    """Model para níveis de estoque por loja."""
    
    __tablename__ = "inventory_levels"
    
    organization_id = Column(String, nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_frame_id = Column(Integer, ForeignKey("products_frames.id", ondelete="CASCADE"), nullable=False, index=True)
    
    quantity = Column(Integer, default=0, nullable=False, doc="Quantidade em estoque")
    reserved_quantity = Column(Integer, default=0, nullable=False, doc="Quantidade reservada")
    
    # Relationships
    store = relationship("Store", backref="inventory_levels")
    product_frame = relationship("ProductFrame", backref="inventory_levels")
    
    __table_args__ = (
        # Garante um registro único por loja + produto
        Index('idx_inv_store_frame', 'store_id', 'product_frame_id', unique=True),
        Index('idx_inv_org_store', 'organization_id', 'store_id'),
    )

