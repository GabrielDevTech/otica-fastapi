"""Controle de acesso baseado em roles."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id, get_current_user_id
from app.models.staff_model import StaffMember, StaffRole


async def get_current_staff(
    current_org_id: str = Depends(get_current_org_id),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> StaffMember:
    """
    Dependency que retorna o StaffMember do usuário atual.
    
    Busca o staff pelo clerk_id (user_id do token) e organization_id.
    
    Raises:
        HTTPException: 404 se o usuário não for encontrado no staff
    """
    staff = await db.execute(
        select(StaffMember).where(
            StaffMember.clerk_id == current_user_id,
            StaffMember.organization_id == current_org_id,
            StaffMember.is_active == True
        )
    )
    staff_member = staff.scalar_one_or_none()
    
    if not staff_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado na equipe ou inativo"
        )
    
    return staff_member


def require_role(*allowed_roles: StaffRole):
    """
    Factory que cria uma dependency para verificar roles.
    
    Uso:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_staff: StaffMember = Depends(require_role(StaffRole.ADMIN))
        ):
            ...
    """
    async def check_role(
        current_staff: StaffMember = Depends(get_current_staff)
    ) -> StaffMember:
        if current_staff.role not in allowed_roles:
            roles_str = ", ".join([role.value for role in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Roles permitidos: {roles_str}. Seu role: {current_staff.role.value}"
            )
        return current_staff
    
    return check_role


# Dependencies pré-configuradas para roles comuns
require_admin = require_role(StaffRole.ADMIN)
require_manager_or_admin = require_role(StaffRole.ADMIN, StaffRole.MANAGER)
require_staff_or_above = require_role(StaffRole.ADMIN, StaffRole.MANAGER, StaffRole.STAFF)

