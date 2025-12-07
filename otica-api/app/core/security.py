"""Segurança e autenticação com providers de autenticação."""
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.auth.auth_factory import get_auth_provider

security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Valida o token JWT usando o provider configurado e retorna o payload.
    
    Usa a abstração de autenticação para suportar múltiplos providers
    (Clerk, Supabase, etc.) de forma transparente.
    
    Raises:
        HTTPException: 401 se token inválido, 403 se não tiver org_id
    """
    token = credentials.credentials
    provider = get_auth_provider()
    return await provider.verify_token(token)


async def get_current_org_id(
    token_data: dict = Depends(verify_token)
) -> str:
    """
    Dependency que retorna o organization_id do token validado.
    
    Esta é a dependência principal usada em todas as rotas que precisam
    de isolamento multi-tenant.
    """
    return token_data["org_id"]


async def get_current_user_id(
    token_data: dict = Depends(verify_token)
) -> str:
    """
    Dependency que retorna o user_id (clerk_id) do token validado.
    """
    return token_data["user_id"]

