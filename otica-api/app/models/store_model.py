"""Model de Store (Loja)."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class Store(BaseModel):
    """Model para lojas de uma organização."""
    
    __tablename__ = "stores"
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # NOVOS CAMPOS
    address_data = Column(JSON, nullable=True, doc="Endereço completo em JSON")
    phone = Column(String(20), nullable=True)
    tax_rate_machine = Column(Numeric(5, 2), nullable=True, doc="Taxa da máquina de cartão (ex: 2.5)")
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organization", backref="stores")

