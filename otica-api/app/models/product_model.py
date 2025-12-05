"""Models para Products (Produtos - Armações e Lentes)."""
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Index
from app.models.base_class import BaseModel


class ProductFrame(BaseModel):
    """Model para armações."""
    
    __tablename__ = "products_frames"
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    reference_code = Column(String(100), nullable=True, index=True)
    brand = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_product_frame_org', 'organization_id', 'reference_code'),
    )


class ProductLens(BaseModel):
    """Model para lentes."""
    
    __tablename__ = "products_lenses"
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    reference_code = Column(String(100), nullable=True, index=True)
    brand = Column(String(100), nullable=True)
    is_lab_order = Column(Boolean, default=False, nullable=False, doc="Se true, é lente de surfaçagem (não tem estoque)")
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_product_lens_org', 'organization_id', 'reference_code'),
    )


class InventoryLevel(BaseModel):
    """Model para níveis de estoque (armações)."""
    
    __tablename__ = "inventory_levels"
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)
    
    product_frame_id = Column(Integer, nullable=False, index=True)
    store_id = Column(Integer, nullable=True, index=True, doc="NULL = estoque geral da organização")
    
    quantity = Column(Integer, default=0, nullable=False, doc="Quantidade total")
    reserved_quantity = Column(Integer, default=0, nullable=False, doc="Quantidade reservada")
    
    __table_args__ = (
        Index('idx_inventory_org_frame', 'organization_id', 'product_frame_id'),
        Index('idx_inventory_org_store_frame', 'organization_id', 'store_id', 'product_frame_id'),
    )


class LensStockGrid(BaseModel):
    """Model para grade de estoque de lentes."""
    
    __tablename__ = "lens_stock_grid"
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)
    
    product_lens_id = Column(Integer, nullable=False, index=True)
    store_id = Column(Integer, nullable=True, index=True, doc="NULL = estoque geral da organização")
    
    # Parâmetros da lente
    spherical = Column(Numeric(6, 2), nullable=False)
    cylindrical = Column(Numeric(6, 2), nullable=False)
    axis = Column(Integer, nullable=False, doc="Eixo (0-180)")
    addition = Column(Numeric(6, 2), nullable=True, doc="Adição (para multifocais)")
    
    # Estoque
    quantity = Column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        Index('idx_lens_stock_org_lens', 'organization_id', 'product_lens_id'),
        Index('idx_lens_stock_params', 'organization_id', 'product_lens_id', 'spherical', 'cylindrical', 'axis', 'addition'),
    )

