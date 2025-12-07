"""Interface abstrata para providers de autenticação."""
from abc import ABC, abstractmethod
from typing import Optional, Dict


class BaseAuthProvider(ABC):
    """Interface para providers de autenticação (Clerk, Supabase, etc.)."""
    
    @abstractmethod
    async def verify_token(self, token: str) -> Dict:
        """
        Valida token JWT e retorna payload com org_id e user_id.
        
        Args:
            token: Token JWT a ser validado
            
        Returns:
            Dict com:
                - org_id: ID da organização
                - user_id: ID do usuário
                - payload: Payload completo do token
                
        Raises:
            HTTPException: Se token inválido ou sem org_id
        """
        pass
    
    @abstractmethod
    async def get_user_email(self, user_id: str) -> Optional[str]:
        """
        Busca email do usuário pelo ID.
        
        Args:
            user_id: ID do usuário no provider de autenticação
            
        Returns:
            Email do usuário ou None se não encontrado
        """
        pass
    
    @abstractmethod
    async def create_user_invitation(
        self,
        email: str,
        organization_id: str,
        role: str = "org:member",
        redirect_url: Optional[str] = None
    ) -> Dict:
        """
        Cria um convite para um novo usuário e adiciona à organização.
        
        Args:
            email: Email do usuário a ser convidado
            organization_id: ID da organização no provider
            role: Role na organização
            redirect_url: URL para redirecionar após aceitar convite
            
        Returns:
            Dict com dados do convite criado
        """
        pass
    
    @abstractmethod
    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str = "",
        skip_password_requirement: bool = True
    ) -> Dict:
        """
        Cria um usuário diretamente no provider.
        
        Args:
            email: Email do usuário
            first_name: Primeiro nome
            last_name: Sobrenome
            skip_password_requirement: Se True, usuário definirá senha depois
            
        Returns:
            Dict com dados do usuário criado
        """
        pass
    
    @abstractmethod
    async def add_user_to_organization(
        self,
        user_id: str,
        organization_id: str,
        role: str = "org:member"
    ) -> Dict:
        """
        Adiciona um usuário existente a uma organização.
        
        Args:
            user_id: ID do usuário no provider
            organization_id: ID da organização no provider
            role: Role na organização
            
        Returns:
            Dict com dados da membership
        """
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Busca um usuário pelo email.
        
        Args:
            email: Email do usuário
            
        Returns:
            Dict com dados do usuário ou None se não encontrado
        """
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """
        Deleta um usuário do provider.
        
        Args:
            user_id: ID do usuário no provider
            
        Returns:
            True se deletado com sucesso
        """
        pass
