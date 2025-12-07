"""Serviço de autenticação que usa o provider configurado."""
from typing import Optional, Dict
from app.core.auth.auth_factory import get_auth_provider


def get_auth_service():
    """
    Dependency para obter o serviço de autenticação.
    
    Retorna o provider configurado (Clerk ou Supabase) através da factory.
    Mantém compatibilidade com código existente que usa ClerkService.
    """
    return get_auth_provider()
