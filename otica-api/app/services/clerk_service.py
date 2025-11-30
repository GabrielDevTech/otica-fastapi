"""Serviço de integração com a API do Clerk."""
import httpx
from typing import Optional
from app.core.config import settings


class ClerkService:
    """Serviço para operações com a API do Clerk."""
    
    BASE_URL = "https://api.clerk.com/v1"
    
    def __init__(self):
        if not settings.CLERK_SECRET_KEY:
            raise ValueError("CLERK_SECRET_KEY não configurado no .env")
        self.headers = {
            "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
    
    async def create_user_invitation(
        self,
        email: str,
        organization_id: str,
        role: str = "org:member",
        redirect_url: Optional[str] = None
    ) -> dict:
        """
        Cria um convite para um novo usuário e adiciona à organização.
        
        O Clerk enviará um email automático para o usuário definir sua senha.
        
        Args:
            email: Email do usuário a ser convidado
            organization_id: ID da organização no Clerk (org_xxx)
            role: Role na organização (org:admin, org:member)
            redirect_url: URL para redirecionar após aceitar convite
            
        Returns:
            dict com dados do convite criado
        """
        async with httpx.AsyncClient() as client:
            # Cria o convite para a organização
            payload = {
                "email_address": email,
                "role": role,
                "redirect_url": redirect_url or f"{settings.CORS_ORIGINS.split(',')[0]}/sign-in"
            }
            
            response = await client.post(
                f"{self.BASE_URL}/organizations/{organization_id}/invitations",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code not in [200, 201]:
                error_detail = response.json() if response.text else "Unknown error"
                raise Exception(f"Erro ao criar convite no Clerk: {error_detail}")
            
            return response.json()
    
    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str = "",
        skip_password_requirement: bool = True
    ) -> dict:
        """
        Cria um usuário diretamente no Clerk.
        
        Args:
            email: Email do usuário
            first_name: Primeiro nome
            last_name: Sobrenome
            skip_password_requirement: Se True, usuário definirá senha depois
            
        Returns:
            dict com dados do usuário criado
        """
        async with httpx.AsyncClient() as client:
            payload = {
                "email_address": [email],
                "first_name": first_name,
                "last_name": last_name,
                "skip_password_requirement": skip_password_requirement
            }
            
            response = await client.post(
                f"{self.BASE_URL}/users",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code not in [200, 201]:
                error_detail = response.json() if response.text else "Unknown error"
                raise Exception(f"Erro ao criar usuário no Clerk: {error_detail}")
            
            return response.json()
    
    async def add_user_to_organization(
        self,
        user_id: str,
        organization_id: str,
        role: str = "org:member"
    ) -> dict:
        """
        Adiciona um usuário existente a uma organização.
        
        Args:
            user_id: ID do usuário no Clerk (user_xxx)
            organization_id: ID da organização no Clerk (org_xxx)
            role: Role na organização
            
        Returns:
            dict com dados da membership
        """
        async with httpx.AsyncClient() as client:
            payload = {
                "user_id": user_id,
                "role": role
            }
            
            response = await client.post(
                f"{self.BASE_URL}/organizations/{organization_id}/memberships",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code not in [200, 201]:
                error_detail = response.json() if response.text else "Unknown error"
                raise Exception(f"Erro ao adicionar usuário à organização: {error_detail}")
            
            return response.json()
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Busca um usuário pelo email.
        
        Args:
            email: Email do usuário
            
        Returns:
            dict com dados do usuário ou None se não encontrado
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/users",
                headers=self.headers,
                params={"email_address": email}
            )
            
            if response.status_code != 200:
                return None
            
            users = response.json()
            if users and len(users) > 0:
                return users[0]
            
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Deleta um usuário do Clerk.
        
        Args:
            user_id: ID do usuário no Clerk
            
        Returns:
            True se deletado com sucesso
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/users/{user_id}",
                headers=self.headers
            )
            
            return response.status_code in [200, 204]


# Singleton lazy para uso global
_clerk_service_instance: ClerkService | None = None


def get_clerk_service() -> ClerkService:
    """Dependency para obter o serviço do Clerk."""
    global _clerk_service_instance
    
    if not settings.CLERK_SECRET_KEY:
        raise Exception("CLERK_SECRET_KEY não configurado. Configure no .env para usar este recurso.")
    
    if _clerk_service_instance is None:
        _clerk_service_instance = ClerkService()
    
    return _clerk_service_instance

