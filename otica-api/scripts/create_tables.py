"""Script para criar tabelas no banco de dados."""
import asyncio
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models import staff_model  # Importa para registrar o model


async def create_tables():
    """
    Cria todas as tabelas definidas nos models.
    
    As conexões são gerenciadas pelo SQLAlchemy engine que:
    1. Usa o DATABASE_URL do .env
    2. Cria conexões assíncronas via asyncpg
    3. Gerencia pool de conexões automaticamente
    """
    print("🔌 Conectando ao banco de dados...")
    print(f"📊 Criando tabelas a partir dos models...")
    
    try:
        async with engine.begin() as conn:
            # Cria todas as tabelas definidas nos models
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tabelas criadas com sucesso!")
        print()
        print("📋 Tabelas criadas:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {str(e)}")
        print()
        print("Verifique:")
        print("1. Se o DATABASE_URL está correto no .env")
        print("2. Se o banco de dados está acessível")
        print("3. Se as credenciais estão corretas")
        raise
    finally:
        # Fecha o engine de forma segura
        try:
            await engine.dispose()
        except Exception:
            # Ignora erros de cleanup - as tabelas já foram criadas
            pass


if __name__ == "__main__":
    asyncio.run(create_tables())

