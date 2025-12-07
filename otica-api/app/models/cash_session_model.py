"""Model de CashSession (Sessão de Caixa)."""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Text, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_class import BaseModel


class CashSessionStatus(str, enum.Enum):
    """Status da sessão de caixa."""
    OPEN = "OPEN"                    # Caixa aberto
    CLOSED = "CLOSED"                # Caixa fechado normalmente
    PENDING_AUDIT = "PENDING_AUDIT"  # Fechado com divergência (aguardando auditoria)


class CashSession(BaseModel):
    """Model para sessões de caixa."""
    
    __tablename__ = "cash_sessions"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status e controle
    status = Column(Enum(CashSessionStatus), default=CashSessionStatus.OPEN, nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Valores financeiros
    opening_balance = Column(Numeric(10, 2), nullable=False, doc="Fundo de troco inicial")
    closing_balance = Column(Numeric(10, 2), nullable=True, doc="Valor informado pelo vendedor ao fechar")
    calculated_balance = Column(Numeric(10, 2), nullable=True, doc="Valor calculado pelo sistema")
    discrepancy = Column(Numeric(10, 2), nullable=True, doc="Diferença (calculated - closing)")
    
    # Auditoria
    audit_resolved_by = Column(Integer, ForeignKey("staff_members.id", ondelete="SET NULL"), nullable=True)
    audit_resolved_at = Column(DateTime(timezone=True), nullable=True)
    audit_action = Column(String(50), nullable=True, doc="ACCEPT_LOSS, CHARGE_STAFF, CORRECT_VALUE")
    audit_notes = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="cash_sessions")
    staff = relationship("StaffMember", foreign_keys=[staff_id], backref="cash_sessions")
    auditor = relationship("StaffMember", foreign_keys=[audit_resolved_by])
    
    __table_args__ = (
        Index('idx_cash_org_store', 'organization_id', 'store_id'),
        Index('idx_cash_staff_status', 'staff_id', 'status'),
        Index('idx_cash_status_org', 'status', 'organization_id'),
    )

