"""Model de Organization (Organização/Tenant)."""
from sqlalchemy import Column, Integer, String, Boolean
from app.models.base_class import BaseModel


class Organization(BaseModel):
    """Model para organizações (tenants)."""
    
    __tablename__ = "organizations"
    
    clerk_org_id = Column(String(255), unique=True, nullable=False, doc="ID da organização no Clerk")
    name = Column(String(255), nullable=False, doc="Nome fantasia")
    cnpj = Column(String(14), nullable=True, doc="CNPJ da empresa")
    access_code = Column(String(20), unique=True, nullable=False, doc="Código para solicitar acesso")
    plan = Column(String(50), default="basic", nullable=False, doc="Plano: basic, pro, enterprise")
    is_active = Column(Boolean, default=True, nullable=False)

