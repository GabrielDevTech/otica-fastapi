"""Configurações da aplicação."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do .env."""
    
    # Auth Provider
    AUTH_PROVIDER: str = "clerk"  # clerk ou supabase
    
    # Clerk
    CLERK_ISSUER: str | None = None
    CLERK_PUBLISHABLE_KEY: str | None = None  # Opcional, para uso futuro
    CLERK_SECRET_KEY: str | None = None  # Opcional, para uso futuro
    
    # Supabase Auth
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None  # Admin key para operações de gerenciamento
    SUPABASE_JWT_SECRET: str | None = None  # JWT Secret para validar tokens de acesso (HS256)
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080,http://192.168.0.100:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origens CORS."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

