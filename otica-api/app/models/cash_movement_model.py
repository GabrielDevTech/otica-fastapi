"""Model de CashMovement (Movimentação de Caixa)."""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_class import BaseModel


class CashMovementType(str, enum.Enum):
    """Tipo de movimentação de caixa."""
    WITHDRAWAL = "WITHDRAWAL"  # Sangria / Retirada
    DEPOSIT = "DEPOSIT"         # Suprimento / Entrada


class CashMovement(BaseModel):
    """Model para movimentações de caixa (sangria/suprimento)."""
    
    __tablename__ = "cash_movements"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Dados
    movement_type = Column(Enum(CashMovementType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False, doc="Valor da movimentação")
    description = Column(String(255), nullable=True, doc="Motivo (ex: 'Pagar lanche', 'Buscar troco')")
    movement_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    cash_session = relationship("CashSession", backref="cash_movements")
    staff = relationship("StaffMember", backref="cash_movements")
    
    __table_args__ = (
        Index('idx_cash_mov_session', 'cash_session_id', 'movement_date'),
        Index('idx_cash_mov_org', 'organization_id', 'movement_date'),
    )

