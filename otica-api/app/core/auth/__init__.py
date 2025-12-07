"""Módulo de abstração de autenticação."""
from app.core.auth.base_auth_provider import BaseAuthProvider
from app.core.auth.auth_factory import get_auth_provider, AuthProviderType
from app.core.auth.clerk_provider import ClerkProvider
from app.core.auth.supabase_provider import SupabaseProvider

__all__ = [
    "BaseAuthProvider",
    "get_auth_provider",
    "AuthProviderType",
    "ClerkProvider",
    "SupabaseProvider",
]
