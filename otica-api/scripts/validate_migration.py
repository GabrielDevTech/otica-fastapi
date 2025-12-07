"""
Script de validação pós-migração.

Valida que a migração do Clerk para Supabase foi bem-sucedida.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.staff_model import StaffMember
from app.models.organization_model import Organization
from app.core.config import settings
from app.core.auth.supabase_provider import SupabaseProvider


async def validate_migration(db: AsyncSession):
    """Valida a migração."""
    print("=" * 80)
    print("VALIDAÇÃO PÓS-MIGRAÇÃO")
    print("=" * 80)
    print()
    
    if settings.AUTH_PROVIDER.lower() != "supabase":
        print("❌ ERRO: AUTH_PROVIDER deve ser 'supabase'")
        return
    
    supabase_provider = SupabaseProvider()
    
    # 1. Valida usuários
    print("1️⃣ Validando usuários...")
    result = await db.execute(
        select(StaffMember).where(StaffMember.clerk_id.isnot(None))
    )
    staff_members = result.scalars().all()
    
    valid_count = 0
    invalid_count = 0
    
    for staff in staff_members:
        # Verifica se o user_id existe no Supabase
        try:
            user_email = await supabase_provider.get_user_email(staff.clerk_id)
            if user_email:
                if user_email.lower() == staff.email.lower():
                    valid_count += 1
                    print(f"   ✅ {staff.full_name}: OK")
                else:
                    invalid_count += 1
                    print(f"   ⚠️ {staff.full_name}: Email diferente (Supabase={user_email}, DB={staff.email})")
            else:
                invalid_count += 1
                print(f"   ❌ {staff.full_name}: Usuário não encontrado no Supabase (ID: {staff.clerk_id})")
        except Exception as e:
            invalid_count += 1
            print(f"   ❌ {staff.full_name}: Erro ao validar ({str(e)})")
    
    print()
    print(f"   ✅ Válidos: {valid_count}")
    print(f"   ❌ Inválidos: {invalid_count}")
    print()
    
    # 2. Valida organizações
    print("2️⃣ Validando organizações...")
    org_result = await db.execute(select(Organization))
    organizations = org_result.scalars().all()
    
    print(f"   📊 Total de organizações: {len(organizations)}")
    for org in organizations:
        print(f"   ✅ {org.name} (ID: {org.clerk_org_id})")
    print()
    
    # 3. Valida tokens
    print("3️⃣ Validação de tokens...")
    print("   ℹ️ Para validar tokens, teste os endpoints da API com tokens do Supabase")
    print()
    
    # Resumo
    print("=" * 80)
    print("RESUMO")
    print("=" * 80)
    total = valid_count + invalid_count
    if total > 0:
        success_rate = (valid_count / total) * 100
        print(f"Taxa de sucesso: {success_rate:.1f}% ({valid_count}/{total})")
    
    if invalid_count == 0:
        print("✅ Migração validada com sucesso!")
    else:
        print(f"⚠️ Encontrados {invalid_count} problemas. Revise os erros acima.")


async def main():
    """Função principal."""
    # Nota: Supabase usa pgbouncer que não suporta prepared statements
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={
            "server_settings": {
                "jit": "off"
            },
            "statement_cache_size": 0,  # Desabilita cache para pgbouncer
        },
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        await validate_migration(db)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
