"""
Script para tornar store_id e department_id obrigatórios em staff_members.

Execute este script APÓS deletar todos os registros com store_id ou department_id NULL.
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path do Python
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from app.core.database import engine


async def make_fields_required():
    """Torna store_id e department_id obrigatórios."""
    async with engine.connect() as conn:
        await conn.begin()
        
        print("🔍 Verificando se há registros NULL...")
        
        # Verificar store_id NULL
        result = await conn.execute(text("""
            SELECT COUNT(*) as null_count 
            FROM staff_members 
            WHERE store_id IS NULL;
        """))
        store_null_count = result.scalar()
        
        # Verificar department_id NULL
        result = await conn.execute(text("""
            SELECT COUNT(*) as null_count 
            FROM staff_members 
            WHERE department_id IS NULL;
        """))
        dept_null_count = result.scalar()
        
        if store_null_count > 0 or dept_null_count > 0:
            print(f"⚠️ Ainda há registros com NULL:")
            print(f"   - store_id NULL: {store_null_count}")
            print(f"   - department_id NULL: {dept_null_count}")
            print("   💡 Atualize ou delete esses registros antes de continuar.")
            await conn.rollback()
            return
        
        print("✅ Nenhum registro NULL encontrado. Prosseguindo...")
        
        # Tornar store_id obrigatório
        print("\n1️⃣ Tornando store_id obrigatório...")
        try:
            await conn.execute(text("""
                ALTER TABLE staff_members 
                ALTER COLUMN store_id SET NOT NULL;
            """))
            print("   ✅ store_id agora é obrigatório")
        except Exception as e:
            print(f"   ⚠️ Erro: {e}")
            await conn.rollback()
            return
        
        # Tornar department_id obrigatório
        print("\n2️⃣ Tornando department_id obrigatório...")
        try:
            await conn.execute(text("""
                ALTER TABLE staff_members 
                ALTER COLUMN department_id SET NOT NULL;
            """))
            print("   ✅ department_id agora é obrigatório")
        except Exception as e:
            print(f"   ⚠️ Erro: {e}")
            await conn.rollback()
            return
        
        await conn.commit()
        print("\n✅ Campos tornados obrigatórios com sucesso!")


if __name__ == "__main__":
    asyncio.run(make_fields_required())

