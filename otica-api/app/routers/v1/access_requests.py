"""Endpoints para gestão de AccessRequests (Solicitações de Acesso)."""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_admin
from app.models.access_request_model import AccessRequest, AccessRequestStatus
from app.models.organization_model import Organization
from app.models.store_model import Store
from app.models.department_model import Department
from app.models.staff_model import StaffMember, StaffRole
from app.schemas.access_request_schema import (
    AccessRequestCreate,
    AccessRequestApprove,
    AccessRequestReject,
    AccessRequestResponse,
    AccessRequestWithOrg
)
from app.services.auth_service import get_auth_service
from app.core.auth.base_auth_provider import BaseAuthProvider


router = APIRouter(prefix="/access-requests", tags=["access-requests"])


# ============================================
# ENDPOINTS PÚBLICOS (sem autenticação)
# ============================================

@router.post("/public", response_model=AccessRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_access_request(
    request_data: AccessRequestCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Cria uma solicitação de acesso (endpoint PÚBLICO).
    
    O usuário precisa fornecer o código de acesso da organização.
    
    **Autenticação**: Não requer (público)
    """
    # Busca organização pelo código de acesso
    result = await db.execute(
        select(Organization).where(
            Organization.access_code == request_data.access_code,
            Organization.is_active == True
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de acesso inválido"
        )
    
    # Verifica se já existe solicitação pendente para este email na org
    existing = await db.execute(
        select(AccessRequest).where(
            AccessRequest.organization_id == org.id,
            AccessRequest.email == request_data.email,
            AccessRequest.status == AccessRequestStatus.PENDING
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma solicitação pendente para este email"
        )
    
    # Verifica se usuário já é membro da org
    existing_staff = await db.execute(
        select(StaffMember).where(
            StaffMember.organization_id == org.clerk_org_id,
            StaffMember.email == request_data.email
        )
    )
    if existing_staff.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email já está cadastrado nesta organização"
        )
    
    # Valida store_id se fornecido
    if request_data.store_id:
        store_result = await db.execute(
            select(Store).where(
                Store.id == request_data.store_id,
                Store.organization_id == org.id
            )
        )
        if not store_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loja não encontrada"
            )
    
    # Valida department_id se fornecido
    if request_data.department_id:
        dept_result = await db.execute(
            select(Department).where(
                Department.id == request_data.department_id,
                Department.organization_id == org.id
            )
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Setor não encontrado"
            )
    
    # Cria a solicitação
    new_request = AccessRequest(
        organization_id=org.id,
        store_id=request_data.store_id,
        department_id=request_data.department_id,
        full_name=request_data.full_name,
        email=request_data.email,
        message=request_data.message,
        status=AccessRequestStatus.PENDING
    )
    
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    
    return new_request


@router.get("/public/validate-code")
async def validate_access_code(
    code: str = Query(..., description="Código de acesso da organização"),
    db: AsyncSession = Depends(get_db),
):
    """
    Valida um código de acesso e retorna info básica da organização (PÚBLICO).
    
    Usado no frontend para mostrar o nome da organização antes de preencher o form.
    
    **Autenticação**: Não requer (público)
    """
    result = await db.execute(
        select(Organization).where(
            Organization.access_code == code,
            Organization.is_active == True
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de acesso inválido"
        )
    
    # Busca lojas e setores da organização para o form
    stores_result = await db.execute(
        select(Store).where(
            Store.organization_id == org.id,
            Store.is_active == True
        )
    )
    stores = stores_result.scalars().all()
    
    depts_result = await db.execute(
        select(Department).where(
            Department.organization_id == org.id,
            Department.is_active == True
        )
    )
    departments = depts_result.scalars().all()
    
    return {
        "organization_name": org.name,
        "stores": [{"id": s.id, "name": s.name} for s in stores],
        "departments": [{"id": d.id, "name": d.name} for d in departments]
    }


# ============================================
# ENDPOINTS AUTENTICADOS (admin)
# ============================================

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


@router.get("", response_model=List[AccessRequestWithOrg])
async def list_access_requests(
    status_filter: AccessRequestStatus = Query(None, description="Filtrar por status"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Lista solicitações de acesso da organização atual.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    query = select(AccessRequest).where(AccessRequest.organization_id == org_id)
    
    if status_filter:
        query = query.where(AccessRequest.status == status_filter)
    
    query = query.order_by(AccessRequest.requested_at.desc())
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    # Enriquece com nomes
    enriched = []
    for req in requests:
        req_dict = {
            "id": req.id,
            "organization_id": req.organization_id,
            "store_id": req.store_id,
            "department_id": req.department_id,
            "full_name": req.full_name,
            "email": req.email,
            "message": req.message,
            "status": req.status,
            "assigned_role": req.assigned_role,
            "requested_at": req.created_at,
            "reviewed_at": req.reviewed_at,
            "reviewed_by": req.reviewed_by,
            "rejection_reason": req.rejection_reason,
            "store_name": None,
            "department_name": None,
            "organization_name": None
        }
        
        if req.store_id:
            store_result = await db.execute(select(Store).where(Store.id == req.store_id))
            store = store_result.scalar_one_or_none()
            if store:
                req_dict["store_name"] = store.name
        
        if req.department_id:
            dept_result = await db.execute(select(Department).where(Department.id == req.department_id))
            dept = dept_result.scalar_one_or_none()
            if dept:
                req_dict["department_name"] = dept.name
        
        enriched.append(AccessRequestWithOrg(**req_dict))
    
    return enriched


@router.get("/{request_id}", response_model=AccessRequestWithOrg)
async def get_access_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Obtém uma solicitação específica.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(AccessRequest).where(
            AccessRequest.id == request_id,
            AccessRequest.organization_id == org_id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    return request


@router.post("/{request_id}/approve", response_model=dict)
async def approve_access_request(
    request_id: int,
    approve_data: AccessRequestApprove,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
    auth_service: BaseAuthProvider = Depends(get_auth_service),
):
    """
    Aprova uma solicitação de acesso.
    
    1. Cria convite no Clerk (envia email automático)
    2. Cria StaffMember no banco
    3. Atualiza status da solicitação
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    # Busca a organização completa para pegar o clerk_org_id
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()
    
    # Busca a solicitação
    result = await db.execute(
        select(AccessRequest).where(
            AccessRequest.id == request_id,
            AccessRequest.organization_id == org_id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    if request.status != AccessRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solicitação já foi {request.status.value}"
        )
    
    # Mapeia role para Clerk role
    clerk_role = "org:member"
    if approve_data.assigned_role == StaffRole.ADMIN:
        clerk_role = "org:admin"
    
    try:
        # 1. Cria convite no Clerk
        invitation = await auth_service.create_user_invitation(
            email=request.email,
            organization_id=org.clerk_org_id,
            role=clerk_role
        )
        
        # 2. Cria StaffMember no banco (clerk_id será preenchido quando o usuário aceitar)
        new_staff = StaffMember(
            organization_id=org.clerk_org_id,
            store_id=request.store_id,
            department_id=request.department_id,
            full_name=request.full_name,
            email=request.email,
            role=approve_data.assigned_role,
            is_active=True,
            clerk_id=None  # Será atualizado via webhook ou no primeiro login
        )
        db.add(new_staff)
        
        # 3. Atualiza a solicitação
        request.status = AccessRequestStatus.APPROVED
        request.assigned_role = approve_data.assigned_role.value
        request.reviewed_at = datetime.utcnow().isoformat()
        request.reviewed_by = current_staff.id
        
        await db.commit()
        
        return {
            "message": "Solicitação aprovada com sucesso. Um email foi enviado para o usuário.",
            "staff_id": new_staff.id,
            "invitation_id": invitation.get("id")
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao aprovar solicitação: {str(e)}"
        )


@router.post("/{request_id}/reject", response_model=dict)
async def reject_access_request(
    request_id: int,
    reject_data: AccessRequestReject,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Rejeita uma solicitação de acesso.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(AccessRequest).where(
            AccessRequest.id == request_id,
            AccessRequest.organization_id == org_id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    if request.status != AccessRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solicitação já foi {request.status.value}"
        )
    
    request.status = AccessRequestStatus.REJECTED
    request.rejection_reason = reject_data.rejection_reason
    request.reviewed_at = datetime.utcnow().isoformat()
    request.reviewed_by = current_staff.id
    
    await db.commit()
    
    return {"message": "Solicitação rejeitada"}


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_access_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Deleta uma solicitação de acesso.
    
    **Permissões**: ADMIN apenas
    """
    org_id = await get_org_internal_id(db, current_org_id)
    
    result = await db.execute(
        select(AccessRequest).where(
            AccessRequest.id == request_id,
            AccessRequest.organization_id == org_id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    await db.delete(request)
    await db.commit()

