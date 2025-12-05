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
    """Obtém um cliente específico (apenas clientes ativos)."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id,
            Customer.is_active == True
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
    """
    Cria um novo cliente ou reativa cliente existente com mesmo CPF.
    
    Se já existir um cliente ativo com o CPF, retorna erro.
    Se existir um cliente inativo (deletado) com o CPF, reativa e atualiza os dados.
    """
    # Verifica se CPF já existe (apenas clientes ativos)
    existing_active = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf,
            Customer.is_active == True
        )
    )
    if existing_active.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado nesta organização"
        )
    
    # Verifica se existe cliente inativo (deletado) com mesmo CPF
    existing_inactive = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf,
            Customer.is_active == False
        )
    )
    inactive_customer = existing_inactive.scalar_one_or_none()
    
    if inactive_customer:
        # Reativa o cliente e atualiza os dados
        update_data = customer_data.model_dump()
        for field, value in update_data.items():
            setattr(inactive_customer, field, value)
        inactive_customer.is_active = True
        
        await db.commit()
        await db.refresh(inactive_customer)
        
        return inactive_customer
    
    # Se não existe nenhum cliente com esse CPF, cria novo
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
    
    Se já existir um cliente inativo (deletado) com o CPF, reativa e atualiza.
    """
    # Verifica se CPF já existe (apenas clientes ativos)
    existing_active = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf,
            Customer.is_active == True
        )
    )
    if existing_active.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado nesta organização"
        )
    
    # Verifica se existe cliente inativo (deletado) com mesmo CPF
    existing_inactive = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf,
            Customer.is_active == False
        )
    )
    inactive_customer = existing_inactive.scalar_one_or_none()
    
    if inactive_customer:
        # Reativa o cliente e atualiza os dados (apenas campos do quick create)
        inactive_customer.full_name = customer_data.full_name
        inactive_customer.cpf = customer_data.cpf
        inactive_customer.birth_date = customer_data.birth_date
        inactive_customer.phone = customer_data.phone
        inactive_customer.is_active = True
        
        await db.commit()
        await db.refresh(inactive_customer)
        
        return inactive_customer
    
    # Se não existe nenhum cliente com esse CPF, cria novo
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
    """Atualiza um cliente (apenas clientes ativos)."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id,
            Customer.is_active == True
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
    
    # Se CPF está sendo atualizado, verificar se já existe (apenas clientes ativos)
    if "cpf" in update_data and update_data["cpf"] != customer.cpf:
        existing_cpf = await db.execute(
            select(Customer).where(
                Customer.organization_id == current_org_id,
                Customer.cpf == update_data["cpf"],
                Customer.is_active == True,
                Customer.id != customer_id
            )
        )
        if existing_cpf.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já cadastrado para outro cliente ativo nesta organização"
            )
    
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    await db.commit()
    await db.refresh(customer)
    
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Desativa um cliente (soft delete).
    
    Retorna 200 em vez de 204 para compatibilidade com proxy Next.js.
    """
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
    
    return {"message": "Cliente deletado com sucesso", "id": customer_id}

