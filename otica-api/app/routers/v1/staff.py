"""Endpoints para gestão de Staff."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, or_
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import (
    get_current_staff,
    require_admin,
    require_manager_or_admin,
    require_staff_or_above
)
from app.models.staff_model import StaffMember, StaffRole
from app.models.store_model import Store
from app.models.department_model import Department
from app.models.organization_model import Organization
from app.schemas.staff_schema import (
    StaffCreate,
    StaffResponse,
    StaffFilter,
    StaffStats
)


router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("", response_model=List[StaffResponse])
async def list_staff(
    q: Optional[str] = Query(None, description="Busca textual em nome/email"),
    role: Optional[StaffRole] = Query(None, description="Filtrar por role"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Lista membros da equipe da organização atual.
    
    **Permissões**: STAFF, MANAGER ou ADMIN
    
    Filtros:
    - q: Busca textual em nome ou email
    - role: Filtra por role específico
    """
    query = select(StaffMember).where(
        StaffMember.organization_id == current_org_id
    )
    
    # Aplica filtro de busca textual
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                StaffMember.full_name.ilike(search_term),
                StaffMember.email.ilike(search_term)
            )
        )
    
    # Aplica filtro de role
    if role:
        query = query.where(StaffMember.role == role)
    
    result = await db.execute(query)
    staff_members = result.scalars().all()
    
    return staff_members


@router.get("/stats", response_model=StaffStats)
async def get_staff_stats(
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    """
    Retorna estatísticas agregadas da equipe da organização atual.
    
    **Permissões**: MANAGER ou ADMIN
    """
    # Query única com agregações
    query = select(
        func.count(StaffMember.id).label("total_users"),
        func.count(StaffMember.id).filter(StaffMember.is_active == True).label("active_users"),
        func.count(StaffMember.id).filter(StaffMember.role == StaffRole.ADMIN).label("admins"),
        func.count(StaffMember.id).filter(StaffMember.role == StaffRole.MANAGER).label("managers"),
    ).where(
        StaffMember.organization_id == current_org_id
    )
    
    result = await db.execute(query)
    stats = result.first()
    
    return StaffStats(
        total_users=stats.total_users or 0,
        active_users=stats.active_users or 0,
        admins=stats.admins or 0,
        managers=stats.managers or 0,
    )


async def get_org_internal_id(db: AsyncSession, clerk_org_id: str) -> int:
    """Obtém o ID interno da organização."""
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


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria um novo membro da equipe.
    
    **Permissões**: ADMIN apenas
    
    O organization_id é automaticamente injetado do token JWT.
    Qualquer organization_id enviado no corpo da requisição é ignorado.
    """
    # Converter org_id para ID interno
    org_id = await get_org_internal_id(db, current_org_id)
    
    # Validar se store pertence à organização
    store_result = await db.execute(
        select(Store).where(
            Store.id == staff_data.store_id,
            Store.organization_id == org_id
        )
    )
    store = store_result.scalar_one_or_none()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loja não encontrada ou não pertence à organização"
        )
    
    # Validar se department pertence à organização
    dept_result = await db.execute(
        select(Department).where(
            Department.id == staff_data.department_id,
            Department.organization_id == org_id
        )
    )
    department = dept_result.scalar_one_or_none()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setor não encontrado ou não pertence à organização"
        )
    
    # Verifica se email já existe na organização
    existing = await db.execute(
        select(StaffMember).where(
            StaffMember.organization_id == current_org_id,
            StaffMember.email == staff_data.email
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado nesta organização"
        )
    
    # Cria novo membro com organization_id do token
    new_staff = StaffMember(
        **staff_data.model_dump(),
        organization_id=current_org_id  # CRÍTICO: sempre do token, nunca do body
    )
    
    db.add(new_staff)
    await db.commit()
    await db.refresh(new_staff)
    
    return new_staff

