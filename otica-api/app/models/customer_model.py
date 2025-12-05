"""Model de Customer (Cliente)."""
from sqlalchemy import Column, Integer, String, Boolean, Date, Index
from app.models.base_class import BaseModel


class Customer(BaseModel):
    """Model para clientes."""
    
    __tablename__ = "customers"
    
    organization_id = Column(String, nullable=False, index=True)
    
    # Dados pessoais
    full_name = Column(String(255), nullable=False)
    cpf = Column(String(11), nullable=False, index=True, doc="CPF (11 dígitos, sem formatação)")
    birth_date = Column(Date, nullable=False, doc="Data de nascimento (obrigatório para cálculo de adição)")
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Dados profissionais
    profession = Column(String(100), nullable=True, doc="Profissão (ajuda na venda consultiva)")
    
    # Endereço
    address_street = Column(String(255), nullable=True)
    address_number = Column(String(20), nullable=True)
    address_complement = Column(String(100), nullable=True)
    address_neighborhood = Column(String(100), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(2), nullable=True)
    address_zipcode = Column(String(10), nullable=True)
    
    # Outros
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        # Garante CPF único por organização
        # NOTA: O sistema reativa clientes deletados ao invés de criar novos
        Index('idx_customer_org_cpf', 'organization_id', 'cpf', unique=True),
        Index('idx_customer_org_name', 'organization_id', 'full_name'),
    )

