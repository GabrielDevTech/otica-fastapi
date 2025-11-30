"""Model de AccessRequest (Solicitação de Acesso)."""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel
import enum


class AccessRequestStatus(str, enum.Enum):
    """Status possíveis de uma solicitação de acesso."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccessRequest(BaseModel):
    """Model para solicitações de acesso."""
    
    __tablename__ = "access_requests"
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=True, doc="Mensagem opcional do solicitante")
    
    status = Column(
        Enum(AccessRequestStatus, name="access_request_status", create_type=False),
        default=AccessRequestStatus.PENDING,
        nullable=False
    )
    assigned_role = Column(String(50), nullable=True, doc="Role atribuído na aprovação")
    
    reviewed_at = Column(String, nullable=True)  # Será atualizado manualmente
    reviewed_by = Column(Integer, nullable=True, doc="ID do staff que aprovou/rejeitou")
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="access_requests")
    store = relationship("Store", backref="access_requests")
    department = relationship("Department", backref="access_requests")

