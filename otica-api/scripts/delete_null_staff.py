"""
Script para deletar registro de staff_members com store_id e department_id NULL.

ATENÇÃO: Este script irá DELETAR permanentemente o registro.
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path do Python
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from app.core.database import engine


async def delete_null_staff():
    """Deleta registro de staff_members com store_id e department_id NULL."""
    async with engine.connect() as conn:
        await conn.begin()
        
        print("🔍 Verificando registros com store_id e department_id NULL...")
        
        # Verificar registros
        result = await conn.execute(text("""
            SELECT id, organization_id, full_name, store_id, department_id
            FROM staff_members
            WHERE store_id IS NULL OR department_id IS NULL;
        """))
        
        records = result.fetchall()
        
        if not records:
            print("✅ Nenhum registro encontrado com store_id ou department_id NULL")
            await conn.rollback()
            return
        
        print(f"\n📋 Encontrados {len(records)} registro(s):")
        for record in records:
            print(f"   - ID: {record.id}, Nome: {record.full_name}, Org: {record.organization_id}")
        
        # Deletar o registro específico
        print("\n🗑️ Deletando registro ID 1...")
        result = await conn.execute(text("""
            DELETE FROM staff_members 
            WHERE id = 1 
              AND organization_id = 'org_362OYRBaXMAnCkLlLmpYqPWOe8z'
              AND store_id IS NULL 
              AND department_id IS NULL;
        """))
        
        deleted_count = result.rowcount
        
        if deleted_count > 0:
            print(f"✅ {deleted_count} registro(s) deletado(s) com sucesso!")
            await conn.commit()
            
            # Verificar se foi deletado
            result = await conn.execute(text("""
                SELECT * FROM staff_members WHERE id = 1;
            """))
            remaining = result.fetchone()
            
            if remaining:
                print("⚠️ Ainda existe um registro com ID 1 (mas pode ter store_id/department_id preenchidos)")
            else:
                print("✅ Registro ID 1 não existe mais")
        else:
            print("⚠️ Nenhum registro foi deletado. Verifique se o ID e organization_id estão corretos.")
            await conn.rollback()


if __name__ == "__main__":
    print("⚠️ ATENÇÃO: Este script irá DELETAR permanentemente o registro!")
    response = input("Deseja continuar? (sim/não): ")
    
    if response.lower() in ['sim', 's', 'yes', 'y']:
        asyncio.run(delete_null_staff())
    else:
        print("❌ Operação cancelada.")

