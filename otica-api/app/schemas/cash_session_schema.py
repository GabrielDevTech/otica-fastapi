"""Schemas Pydantic para CashSession."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime
from app.models.cash_session_model import CashSessionStatus


class CashSessionBase(BaseModel):
    """Schema base para CashSession."""
    opening_balance: Decimal = Field(..., ge=0, description="Fundo de troco inicial")


class CashSessionCreate(CashSessionBase):
    """Schema para criar CashSession."""
    store_id: int = Field(..., description="ID da loja")


class CashSessionClose(BaseModel):
    """Schema para fechar CashSession."""
    closing_balance: Decimal = Field(..., ge=0, description="Valor informado ao fechar")


class CashSessionAudit(BaseModel):
    """Schema para auditar CashSession."""
    action: Literal["ACCEPT_LOSS", "CHARGE_STAFF", "CORRECT_VALUE"] = Field(..., description="Ação de auditoria")
    corrected_value: Optional[Decimal] = Field(None, description="Novo valor (se action=CORRECT_VALUE)")
    notes: Optional[str] = Field(None, description="Observações da auditoria")


class CashSessionResponse(CashSessionBase):
    """Schema de resposta para CashSession."""
    id: int
    organization_id: str
    store_id: int
    staff_id: int
    status: CashSessionStatus
    opened_at: datetime
    closed_at: Optional[datetime]
    closing_balance: Optional[Decimal]
    calculated_balance: Optional[Decimal]
    discrepancy: Optional[Decimal]
    audit_resolved_by: Optional[int]
    audit_resolved_at: Optional[datetime]
    audit_action: Optional[str]
    audit_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CashSessionStats(BaseModel):
    """KPIs para dashboard gerencial."""
    active_sessions_count: int = Field(..., description="Número de caixas abertos")
    pending_audit_count: int = Field(..., description="Número de caixas com divergência pendente")
    total_discrepancy: Decimal = Field(..., description="Soma de todas as divergências pendentes")
    card_fees_estimated: Decimal = Field(..., description="Taxas de cartão estimadas (mês)")

