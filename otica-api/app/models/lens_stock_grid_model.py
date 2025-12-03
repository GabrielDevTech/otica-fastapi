"""Model de LensStockGrid (Grade de Estoque de Lentes)."""
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class LensStockGrid(BaseModel):
    """Model para grade de estoque de lentes (Esférico x Cilíndrico)."""
    
    __tablename__ = "lens_stock_grid"
    
    organization_id = Column(String, nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_lens_id = Column(Integer, ForeignKey("products_lenses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Graus
    spherical = Column(Numeric(5, 2), nullable=False, doc="Esférico (ex: -2.00)")
    cylindrical = Column(Numeric(5, 2), nullable=False, doc="Cilíndrico (ex: -1.00)")
    axis = Column(Integer, nullable=True, doc="Eixo (0-180)")
    
    # Estoque
    quantity = Column(Integer, default=0, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="lens_stock_grid")
    product_lens = relationship("ProductLens", backref="lens_stock_grid")
    
    __table_args__ = (
        # Garante combinação única
        Index('idx_lens_grid_unique', 'store_id', 'product_lens_id', 'spherical', 'cylindrical', 'axis', unique=True),
    )

