"""Model de ProductFrame (Armação)."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class ProductFrame(BaseModel):
    """Model para armações de óculos."""
    
    __tablename__ = "products_frames"
    
    organization_id = Column(String, nullable=False, index=True)
    
    # Campos essenciais
    reference_code = Column(String(100), nullable=False, index=True, doc="Código de barras")
    name = Column(String(255), nullable=False, doc="Nome da armação")
    brand = Column(String(100), nullable=True, doc="Marca")
    model = Column(String(100), nullable=True, doc="Modelo")
    
    # Preços
    cost_price = Column(Numeric(10, 2), nullable=True, doc="Preço de custo")
    sell_price = Column(Numeric(10, 2), nullable=False, doc="Preço de venda")
    
    # Estoque
    min_stock_alert = Column(Integer, default=0, nullable=False, doc="Quantidade mínima para alerta")
    
    # Outros
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        # Garante código único por organização
        Index('idx_frame_org_code', 'organization_id', 'reference_code', unique=True),
        Index('idx_frame_org_active', 'organization_id', 'is_active'),
    )

