"""Model de ReceivableAccount (Conta a Receber)."""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Date, DateTime, Text, Enum, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class ReceivableStatus(str, enum.Enum):
    """Status da conta a receber."""
    PENDING = "PENDING"        # Pendente
    PARTIAL = "PARTIAL"        # Parcialmente pago
    PAID = "PAID"              # Pago
    OVERDUE = "OVERDUE"        # Vencido
    CANCELLED = "CANCELLED"    # Cancelado


class ReceivableAccount(BaseModel):
    """Model para contas a receber."""
    
    __tablename__ = "receivable_accounts"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Valores
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    remaining_amount = Column(Numeric(10, 2), nullable=False, doc="total_amount - paid_amount")
    
    # Status e controle
    status = Column(Enum(ReceivableStatus), default=ReceivableStatus.PENDING, nullable=False)
    due_date = Column(Date, nullable=False, doc="Data de vencimento")
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Observações
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    customer = relationship("Customer", backref="receivable_accounts")
    # sale relationship é criado via backref em Sale.receivable_account
    
    __table_args__ = (
        Index('idx_rec_org_status', 'organization_id', 'status'),
        Index('idx_rec_customer', 'customer_id', 'due_date'),
        Index('idx_rec_due_date', 'due_date', 'status'),
    )

