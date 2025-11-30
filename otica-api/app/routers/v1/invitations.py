"""Endpoints para convites diretos de usuários (Admin)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_admin
from app.models.organization_model import Organization
from app.models.store_model import Store
from app.models.department_model import Department
from app.models.staff_model import StaffMember, StaffRole
from app.schemas.staff_schema import StaffInvite, StaffResponse
from app.services.clerk_service import get_clerk_service, ClerkService


router = APIRouter(prefix="/invitations", tags=["invitations"])


async def get_org_data(
    db: AsyncSession,
    clerk_org_id: str
) -> Organization:
    """Obtém a organização pelo clerk_org_id."""
    result = await db.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organização não encontrada"
        )
    return org


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def invite_user(
    invite_data: StaffInvite,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
    clerk_service: ClerkService = Depends(get_clerk_service),
):
    """
    Convida um novo usuário diretamente (sem solicitação).
    
    O admin preenche o formulário e o usuário recebe um email
    para definir sua senha.
    
    **Permissões**: ADMIN apenas
    """
    org = await get_org_data(db, current_org_id)
    
    # Verifica se email já existe na organização
    existing = await db.execute(
        select(StaffMember).where(
            StaffMember.organization_id == current_org_id,
            StaffMember.email == invite_data.email
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado nesta organização"
        )
    
    # Valida store_id se fornecido
    if invite_data.store_id:
        store_result = await db.execute(
            select(Store).where(
                Store.id == invite_data.store_id,
                Store.organization_id == org.id
            )
        )
        if not store_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loja não encontrada"
            )
    
    # Valida department_id se fornecido
    if invite_data.department_id:
        dept_result = await db.execute(
            select(Department).where(
                Department.id == invite_data.department_id,
                Department.organization_id == org.id
            )
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Setor não encontrado"
            )
    
    # Mapeia role para Clerk role
    clerk_role = "org:member"
    if invite_data.role == StaffRole.ADMIN:
        clerk_role = "org:admin"
    
    try:
        # 1. Cria convite no Clerk
        invitation = await clerk_service.create_user_invitation(
            email=invite_data.email,
            organization_id=org.clerk_org_id,
            role=clerk_role
        )
        
        # 2. Cria StaffMember no banco
        new_staff = StaffMember(
            organization_id=current_org_id,
            store_id=invite_data.store_id,
            department_id=invite_data.department_id,
            full_name=invite_data.full_name,
            email=invite_data.email,
            role=invite_data.role,
            is_active=True,
            clerk_id=None  # Será atualizado quando aceitar o convite
        )
        db.add(new_staff)
        await db.commit()
        await db.refresh(new_staff)
        
        return {
            "message": "Convite enviado com sucesso!",
            "staff_id": new_staff.id,
            "invitation_id": invitation.get("id"),
            "email": invite_data.email
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar convite: {str(e)}"
        )


@router.post("/resend/{staff_id}", response_model=dict)
async def resend_invitation(
    staff_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
    clerk_service: ClerkService = Depends(get_clerk_service),
):
    """
    Reenvia convite para um usuário que ainda não aceitou.
    
    **Permissões**: ADMIN apenas
    """
    org = await get_org_data(db, current_org_id)
    
    # Busca o staff
    result = await db.execute(
        select(StaffMember).where(
            StaffMember.id == staff_id,
            StaffMember.organization_id == current_org_id
        )
    )
    staff = result.scalar_one_or_none()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    if staff.clerk_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já aceitou o convite"
        )
    
    # Mapeia role para Clerk role
    clerk_role = "org:member"
    if staff.role == StaffRole.ADMIN:
        clerk_role = "org:admin"
    
    try:
        # Reenvia convite
        invitation = await clerk_service.create_user_invitation(
            email=staff.email,
            organization_id=org.clerk_org_id,
            role=clerk_role
        )
        
        return {
            "message": "Convite reenviado com sucesso!",
            "invitation_id": invitation.get("id"),
            "email": staff.email
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao reenviar convite: {str(e)}"
        )

