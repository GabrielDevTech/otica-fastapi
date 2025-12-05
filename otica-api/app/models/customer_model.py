"""Model de Customer (Cliente)."""
from sqlalchemy import Column, Integer, String, Boolean, Index
from app.models.base_class import BaseModel


class Customer(BaseModel):
    """Model para clientes."""
    
    __tablename__ = "customers"
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)
    
    full_name = Column(String(255), nullable=False)
    cpf = Column(String(14), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_customer_org_cpf', 'organization_id', 'cpf'),
    )

