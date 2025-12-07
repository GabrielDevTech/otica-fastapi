"""Factory para criar instâncias de providers de autenticação."""
from enum import Enum
from app.core.auth.base_auth_provider import BaseAuthProvider
from app.core.auth.clerk_provider import ClerkProvider
from app.core.auth.supabase_provider import SupabaseProvider
from app.core.config import settings


class AuthProviderType(str, Enum):
    """Tipos de providers de autenticação disponíveis."""
    CLERK = "clerk"
    SUPABASE = "supabase"


def get_auth_provider() -> BaseAuthProvider:
    """
    Factory que retorna o provider de autenticação baseado na variável de ambiente.
    
    Returns:
        Instância do provider configurado (ClerkProvider ou SupabaseProvider)
        
    Raises:
        ValueError: Se o provider não for suportado ou não estiver configurado
    """
    provider_type = getattr(settings, "AUTH_PROVIDER", "clerk").lower()
    
    if provider_type == AuthProviderType.CLERK.value:
        return ClerkProvider()
    elif provider_type == AuthProviderType.SUPABASE.value:
        return SupabaseProvider()
    else:
        raise ValueError(
            f"Provider de autenticação '{provider_type}' não suportado. "
            f"Use: {', '.join([p.value for p in AuthProviderType])}"
        )
