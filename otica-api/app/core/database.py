"""Configuração do banco de dados SQLAlchemy."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# Engine assíncrono
# Nota: Supabase usa pgbouncer que não suporta prepared statements
# Por isso desabilitamos o cache de prepared statements
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Log SQL queries (desativar em produção)
    future=True,
    connect_args={
        "server_settings": {
            "jit": "off"  # Desabilita JIT para compatibilidade com pgbouncer
        },
        "statement_cache_size": 0,  # Desabilita cache de prepared statements para pgbouncer
    },
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Classe base para todos os models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency para obter sessão do banco de dados."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

