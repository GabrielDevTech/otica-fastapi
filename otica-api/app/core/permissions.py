"""Controle de acesso baseado em roles."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id, get_current_user_id
from app.models.staff_model import StaffMember, StaffRole
import httpx
from app.core.config import settings


async def get_user_email_from_clerk(user_id: str) -> str | None:
    """
    Busca o email do usuário na API do Clerk.
    
    Usado quando precisamos vincular um staff_member (criado por convite)
    ao clerk_id do usuário que acabou de criar sua conta.
    """
    if not settings.CLERK_SECRET_KEY:
        print("⚠️ CLERK_SECRET_KEY não configurado")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.clerk.com/v1/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                user_data = response.json()
                email_addresses = user_data.get("email_addresses", [])
                if email_addresses:
                    primary = next(
                        (e for e in email_addresses if e.get("id") == user_data.get("primary_email_address_id")),
                        email_addresses[0]
                    )
                    email = primary.get("email_address")
                    print(f"📧 Email encontrado no Clerk para {user_id}: {email}")
                    return email
            else:
                print(f"⚠️ Clerk API retornou {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro ao buscar email do Clerk: {e}")
        return None


async def get_current_staff(
    current_org_id: str = Depends(get_current_org_id),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> StaffMember:
    """
    Dependency que retorna o StaffMember do usuário atual.
    
    Busca o staff pelo clerk_id (user_id do token) e organization_id.
    Se não encontrar pelo clerk_id, tenta encontrar pelo email (para usuários
    que acabaram de aceitar o convite) e atualiza o clerk_id.
    """
    print(f"🔍 Buscando staff: clerk_id={current_user_id}, org_id={current_org_id}")
    
    # 1. Primeiro, tenta buscar pelo clerk_id
    result = await db.execute(
        select(StaffMember).where(
            StaffMember.clerk_id == current_user_id,
            StaffMember.organization_id == current_org_id,
            StaffMember.is_active == True
        )
    )
    staff_member = result.scalar_one_or_none()
    
    if staff_member:
        print(f"✅ Staff encontrado pelo clerk_id: {staff_member.full_name}")
        return staff_member
    
    print(f"⚠️ Staff não encontrado pelo clerk_id, tentando pelo email...")
    
    # 2. Se não encontrou pelo clerk_id, busca pelo email
    user_email = await get_user_email_from_clerk(current_user_id)
    
    if user_email:
        result = await db.execute(
            select(StaffMember).where(
                StaffMember.email == user_email,
                StaffMember.organization_id == current_org_id,
                StaffMember.clerk_id == None,  # Ainda não vinculado
                StaffMember.is_active == True
            )
        )
        staff_member = result.scalar_one_or_none()
        
        if staff_member:
            # 3. Encontrou! Atualiza o clerk_id
            print(f"✅ Staff encontrado pelo email! Vinculando clerk_id...")
            staff_member.clerk_id = current_user_id
            await db.commit()
            await db.refresh(staff_member)
            print(f"✅ Vinculado clerk_id {current_user_id} ao staff {staff_member.id} ({user_email})")
            return staff_member
        else:
            print(f"❌ Nenhum staff encontrado com email={user_email} e clerk_id=NULL")
    
    # 4. Não encontrou de nenhuma forma
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuário não encontrado na equipe ou inativo"
    )


def require_role(*allowed_roles: StaffRole):
    """
    Factory que cria uma dependency para verificar roles.
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
