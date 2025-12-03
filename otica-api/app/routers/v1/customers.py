"""Endpoints para gestão de Customers (Clientes)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above
from app.models.customer_model import Customer
from app.models.staff_model import StaffMember
from app.schemas.customer_schema import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerQuickCreate
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    q: Optional[str] = Query(None, description="Busca em nome/CPF/email"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Lista clientes da organização."""
    query = select(Customer).where(
        Customer.organization_id == current_org_id,
        Customer.is_active == True
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Customer.full_name.ilike(search_term),
                Customer.cpf.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        )
    
    result = await db.execute(query)
    customers = result.scalars().all()
    
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Obtém um cliente específico."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id
        )
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    return customer


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Cria um novo cliente."""
    # Verifica se CPF já existe
    existing = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado nesta organização"
        )
    
    new_customer = Customer(
        **customer_data.model_dump(),
        organization_id=current_org_id
    )
    
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    
    return new_customer


@router.post("/quick", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_quick(
    customer_data: CustomerQuickCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Cria cliente rapidamente (otimizado para Modal na tela de vendas).
    
    Campos mínimos: nome, CPF, data de nascimento, telefone (opcional).
    """
    # Verifica se CPF já existe
    existing = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado nesta organização"
        )
    
    new_customer = Customer(
        full_name=customer_data.full_name,
        cpf=customer_data.cpf,
        birth_date=customer_data.birth_date,
        phone=customer_data.phone,
        organization_id=current_org_id
    )
    
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    
    return new_customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Atualiza um cliente."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id
        )
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    await db.commit()
    await db.refresh(customer)
    
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Desativa um cliente (soft delete)."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id
        )
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    customer.is_active = False
    await db.commit()

