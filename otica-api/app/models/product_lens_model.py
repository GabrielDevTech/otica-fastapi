"""Model de ProductLens (Lente)."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class ProductLens(BaseModel):
    """Model para lentes de óculos."""
    
    __tablename__ = "products_lenses"
    
    organization_id = Column(String, nullable=False, index=True)
    
    # Campos comuns
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    
    # Preços
    cost_price = Column(Numeric(10, 2), nullable=True)
    sell_price = Column(Numeric(10, 2), nullable=False)
    
    # Tipo de lente
    is_lab_order = Column(Boolean, default=False, nullable=False, doc="True = Surfaçagem (laboratório), False = Estoque")
    
    # Tratamentos (para lentes de estoque)
    treatment = Column(String(100), nullable=True, doc="Ex: Anti-reflexo, Blue Light, etc.")
    
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_lens_org_active', 'organization_id', 'is_active'),
    )

