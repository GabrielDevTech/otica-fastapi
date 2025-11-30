"""Model de Department (Setor)."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class Department(BaseModel):
    """Model para setores de uma organização (globais)."""
    
    __tablename__ = "departments"
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organization", backref="departments")

