"""Model de Sale (Venda)."""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_class import BaseModel


class PaymentMethod(str, enum.Enum):
    """Método de pagamento."""
    CASH = "CASH"              # Dinheiro
    CARD = "CARD"              # Cartão
    PIX = "PIX"                # Pix
    CREDIT = "CREDIT"          # Crediário


class Sale(BaseModel):
    """Model para vendas."""
    
    __tablename__ = "sales"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    service_order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False, index=True)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id", ondelete="SET NULL"), nullable=True, index=True, doc="Apenas se pagamento em dinheiro")
    
    # Valores
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Cartão específico
    card_fee_rate = Column(Numeric(5, 2), nullable=True, doc="Taxa aplicada (de store.tax_rate_machine)")
    card_gross_amount = Column(Numeric(10, 2), nullable=True, doc="Valor bruto")
    card_net_amount = Column(Numeric(10, 2), nullable=True, doc="Valor líquido (após taxa)")
    
    # Crediário
    receivable_account_id = Column(Integer, ForeignKey("receivable_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Comissão
    commissionable_amount = Column(Numeric(10, 2), nullable=True, doc="Valor comissionável")
    
    # Datas
    sold_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    service_order = relationship("ServiceOrder", backref="sale")
    customer = relationship("Customer", backref="sales")
    store = relationship("Store", backref="sales")
    seller = relationship("StaffMember", foreign_keys=[seller_id], backref="sales")
    cash_session = relationship("CashSession", backref="sales")
    receivable_account = relationship("ReceivableAccount", foreign_keys=[receivable_account_id], backref="sale", uselist=False)
    
    __table_args__ = (
        Index('idx_sale_org_date', 'organization_id', 'sold_at'),
        Index('idx_sale_store_date', 'store_id', 'sold_at'),
        Index('idx_sale_seller', 'seller_id', 'sold_at'),
    )

