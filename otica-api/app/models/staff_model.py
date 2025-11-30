"""Model de Staff (Equipe)."""
from sqlalchemy import Column, Integer, String, Boolean, Enum, Index, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.models.base_class import BaseModel


class StaffRole(str, enum.Enum):
    """Roles dos membros da equipe."""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    ASSISTANT = "ASSISTANT"


class StaffMember(BaseModel):
    """Model para membros da equipe."""
    
    __tablename__ = "staff_members"
    
    clerk_id = Column(String, unique=True, nullable=True, doc="Vínculo com usuário Clerk")
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos com Store e Department
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)  # Unique por Tenant via index composto
    role = Column(Enum(StaffRole), default=StaffRole.STAFF, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar_url = Column(String, nullable=True)
    
    # Relationships
    store = relationship("Store", backref="staff_members")
    department = relationship("Department", backref="staff_members")
    
    __table_args__ = (
        # Garante email único DENTRO da mesma organização
        Index('idx_staff_org_email', 'organization_id', 'email', unique=True),
        Index('idx_staff_org_role', 'organization_id', 'role'),
    )

