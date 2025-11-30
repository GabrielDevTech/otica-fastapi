"""Endpoints para gestão de Departments (Setores)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_admin, require_staff_or_above
from app.models.department_model import Department
from app.models.organization_model import Organization
from app.models.staff_model import StaffMember
from app.schemas.department_schema import DepartmentCreate, DepartmentUpdate, DepartmentResponse


router = APIRouter(prefix="/departments", tags=["departments"])


async def get_org_internal_id(
    db: AsyncSession,
    clerk_org_id: str
) -> int:
    """Obtém o ID interno da organização pelo clerk_org_id."""
    result = await db.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organização não encontrada"
        )
    return org.id


@router.get("", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Lista todos os setores da organização atual.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Department).where(
            Department.organization_id == org_id,
            Department.is_active == True
        )
    )
    departments = result.scalars().all()
    
    return departments


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Obtém um setor específico.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.organization_id == org_id
        )
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor não encontrado"
        )
    
    return department


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria um novo setor.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    # Verifica se já existe setor com mesmo nome na org
    existing = await db.execute(
        select(Department).where(
            Department.organization_id == org_id,
            Department.name == department_data.name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um setor com este nome"
        )
    
    new_department = Department(
        **department_data.model_dump(),
        organization_id=org_id
    )
    
    db.add(new_department)
    await db.commit()
    await db.refresh(new_department)
    
    return new_department


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Atualiza um setor.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.organization_id == org_id
        )
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor não encontrado"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = department_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)
    
    await db.commit()
    await db.refresh(department)
    
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Desativa um setor (soft delete).
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(Department).where(
            Department.id == department_id,
            Department.organization_id == org_id
        )
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor não encontrado"
        )
    
    department.is_active = False
    await db.commit()

