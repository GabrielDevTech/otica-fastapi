"""Schemas Pydantic para AccessRequest."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from app.models.access_request_model import AccessRequestStatus
from app.models.staff_model import StaffRole


class AccessRequestBase(BaseModel):
    """Schema base de AccessRequest."""
    full_name: str = Field(..., min_length=2, max_length=255, description="Nome completo")
    email: EmailStr = Field(..., description="Email do solicitante")
    store_id: Optional[int] = Field(None, description="ID da loja")
    department_id: Optional[int] = Field(None, description="ID do setor")
    message: Optional[str] = Field(None, max_length=500, description="Mensagem opcional")


class AccessRequestCreate(AccessRequestBase):
    """Schema para criar um AccessRequest (público)."""
    access_code: str = Field(..., min_length=6, max_length=20, description="Código de acesso da organização")


class AccessRequestApprove(BaseModel):
    """Schema para aprovar um AccessRequest."""
    assigned_role: StaffRole = Field(..., description="Role a ser atribuído ao usuário")


class AccessRequestReject(BaseModel):
    """Schema para rejeitar um AccessRequest."""
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Motivo da rejeição")


class AccessRequestResponse(AccessRequestBase):
    """Schema de resposta de AccessRequest."""
    id: int
    organization_id: int
    status: AccessRequestStatus
    assigned_role: Optional[str] = None
    requested_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


class AccessRequestWithOrg(AccessRequestResponse):
    """Schema de resposta com dados da organização."""
    organization_name: Optional[str] = None
    store_name: Optional[str] = None
    department_name: Optional[str] = None

