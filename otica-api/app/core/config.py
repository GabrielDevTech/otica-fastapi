"""Configurações da aplicação."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do .env."""
    
    # Clerk
    CLERK_ISSUER: str
    CLERK_PUBLISHABLE_KEY: str | None = None  # Opcional, para uso futuro
    CLERK_SECRET_KEY: str | None = None  # Opcional, para uso futuro
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origens CORS."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

