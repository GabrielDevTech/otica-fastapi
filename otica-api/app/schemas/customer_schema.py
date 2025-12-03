"""Schemas Pydantic para Customer."""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
import re


class CustomerBase(BaseModel):
    """Schema base para Customer."""
    full_name: str = Field(..., min_length=2, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF (11 dígitos, sem formatação)")
    birth_date: date = Field(..., description="Data de nascimento")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    profession: Optional[str] = Field(None, max_length=100)
    address_street: Optional[str] = Field(None, max_length=255)
    address_number: Optional[str] = Field(None, max_length=20)
    address_complement: Optional[str] = Field(None, max_length=100)
    address_neighborhood: Optional[str] = Field(None, max_length=100)
    address_city: Optional[str] = Field(None, max_length=100)
    address_state: Optional[str] = Field(None, max_length=2)
    address_zipcode: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v):
        # Remove formatação
        cpf = re.sub(r'[^0-9]', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf


class CustomerCreate(CustomerBase):
    """Schema para criar Customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema para atualizar Customer."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    profession: Optional[str] = Field(None, max_length=100)
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zipcode: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Schema de resposta para Customer."""
    id: int
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerQuickCreate(BaseModel):
    """Schema otimizado para criação rápida via Modal."""
    full_name: str = Field(..., min_length=2, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=11)
    birth_date: date
    phone: Optional[str] = Field(None, max_length=20)
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v):
        cpf = re.sub(r'[^0-9]', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf

