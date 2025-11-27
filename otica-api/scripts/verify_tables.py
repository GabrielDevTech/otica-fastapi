"""Script para verificar se as tabelas foram criadas."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text


async def verify_tables():
    """Verifica se as tabelas existem no banco."""
    try:
        async with engine.connect() as conn:
            # Verifica se a tabela staff_members existe
            result = await conn.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'staff_members'
                """)
            )
            
            if result.scalar():
                print("✅ Tabela 'staff_members' existe no banco de dados!")
                
                # Verifica se o enum foi criado
                enum_result = await conn.execute(
                    text("""
                        SELECT typname 
                        FROM pg_type 
                        WHERE typname = 'staffrole'
                    """)
                )
                
                if enum_result.scalar():
                    print("✅ Enum 'staffrole' criado com sucesso!")
                else:
                    print("⚠️  Enum 'staffrole' não encontrado")
                
                # Lista os índices
                indexes_result = await conn.execute(
                    text("""
                        SELECT indexname 
                        FROM pg_indexes 
                        WHERE tablename = 'staff_members'
                    """)
                )
                
                indexes = [row[0] for row in indexes_result.fetchall()]
                print(f"\n📋 Índices criados ({len(indexes)}):")
                for idx in indexes:
                    print(f"   - {idx}")
                
                print("\n✅ Tudo certo! Banco de dados configurado com sucesso!")
            else:
                print("❌ Tabela 'staff_members' não encontrada!")
                print("Execute: python scripts/create_tables.py")
                
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {str(e)}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_tables())

