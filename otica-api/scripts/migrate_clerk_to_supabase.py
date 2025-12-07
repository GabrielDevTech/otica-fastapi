"""
Script de migração de usuários do Clerk para Supabase Authentication.

Este script:
1. Lista todos os StaffMember com clerk_id
2. Cria usuários correspondentes no Supabase
3. Atualiza app_metadata com organization_id
4. Atualiza clerk_id no banco com o novo user_id do Supabase

⚠️ IMPORTANTE: Execute em ambiente de staging primeiro!
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.staff_model import StaffMember
from app.models.organization_model import Organization
from app.core.config import settings
from app.core.auth.auth_factory import get_auth_provider
from app.core.auth.clerk_provider import ClerkProvider
from app.core.auth.supabase_provider import SupabaseProvider


async def migrate_users(db: AsyncSession, dry_run: bool = True):
    """
    Migra usuários do Clerk para Supabase.
    
    Args:
        db: Sessão do banco de dados
        dry_run: Se True, apenas mostra o que seria feito sem executar
    """
    print("=" * 80)
    print("MIGRAÇÃO DE USUÁRIOS: CLERK → SUPABASE")
    print("=" * 80)
    print(f"Modo: {'DRY RUN (simulação)' if dry_run else 'EXECUÇÃO REAL'}")
    print()
    
    # Verifica se está usando Supabase
    if settings.AUTH_PROVIDER.lower() != "supabase":
        print("❌ ERRO: AUTH_PROVIDER deve ser 'supabase' para migração")
        print(f"   Atual: {settings.AUTH_PROVIDER}")
        print("   Configure AUTH_PROVIDER=supabase no .env")
        return
    
    # Instancia providers
    clerk_provider = ClerkProvider()
    supabase_provider = SupabaseProvider()
    
    # Busca todos os staff com clerk_id
    result = await db.execute(
        select(StaffMember).where(StaffMember.clerk_id.isnot(None))
    )
    staff_members = result.scalars().all()
    
    print(f"📊 Total de usuários encontrados: {len(staff_members)}")
    print()
    
    if len(staff_members) == 0:
        print("✅ Nenhum usuário para migrar")
        return
    
    # Busca organizações para mapear clerk_org_id
    org_result = await db.execute(select(Organization))
    organizations = {org.clerk_org_id: org for org in org_result.scalars().all()}
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for staff in staff_members:
        try:
            print(f"🔄 Processando: {staff.full_name} ({staff.email})")
            print(f"   Clerk ID: {staff.clerk_id}")
            print(f"   Org ID: {staff.organization_id}")
            
            # Busca organização
            org = organizations.get(staff.organization_id)
            if not org:
                print(f"   ⚠️ Organização não encontrada: {staff.organization_id}")
                skipped_count += 1
                continue
            
            # Busca email do usuário no Clerk
            clerk_email = await clerk_provider.get_user_email(staff.clerk_id)
            if not clerk_email:
                print(f"   ⚠️ Email não encontrado no Clerk para {staff.clerk_id}")
                skipped_count += 1
                continue
            
            if clerk_email != staff.email:
                print(f"   ⚠️ Email diferente: Clerk={clerk_email}, DB={staff.email}")
            
            # Verifica se usuário já existe no Supabase
            existing_user = await supabase_provider.get_user_by_email(staff.email)
            
            if existing_user:
                print(f"   ✅ Usuário já existe no Supabase: {existing_user.get('id')}")
                supabase_user_id = existing_user.get('id')
                
                # Atualiza app_metadata se necessário
                if not dry_run:
                    await supabase_provider.add_user_to_organization(
                        supabase_user_id,
                        org.clerk_org_id,
                        "org:member"  # Role padrão
                    )
            else:
                # Cria usuário no Supabase
                print(f"   📝 Criando usuário no Supabase...")
                
                if dry_run:
                    print(f"   [DRY RUN] Criaria usuário: {staff.email}")
                    supabase_user_id = f"user_mock_{staff.id}"
                else:
                    # Busca nome completo
                    names = staff.full_name.split(' ', 1)
                    first_name = names[0] if names else staff.full_name
                    last_name = names[1] if len(names) > 1 else ""
                    
                    user_data = await supabase_provider.create_user(
                        email=staff.email,
                        first_name=first_name,
                        last_name=last_name,
                        skip_password_requirement=True
                    )
                    supabase_user_id = user_data.get('id')
                    
                    # Adiciona à organização
                    await supabase_provider.add_user_to_organization(
                        supabase_user_id,
                        org.clerk_org_id,
                        "org:member"
                    )
            
            # Atualiza clerk_id no banco (agora armazena Supabase user_id)
            if not dry_run:
                staff.clerk_id = supabase_user_id
                await db.commit()
                print(f"   ✅ Atualizado no banco: clerk_id = {supabase_user_id}")
            else:
                print(f"   [DRY RUN] Atualizaria clerk_id para: {supabase_user_id}")
            
            success_count += 1
            print()
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ ERRO: {str(e)}")
            print()
            if not dry_run:
                await db.rollback()
    
    print("=" * 80)
    print("RESUMO DA MIGRAÇÃO")
    print("=" * 80)
    print(f"✅ Sucesso: {success_count}")
    print(f"❌ Erros: {error_count}")
    print(f"⚠️ Ignorados: {skipped_count}")
    print(f"📊 Total: {len(staff_members)}")
    print()
    
    if dry_run:
        print("⚠️ Este foi um DRY RUN. Nenhuma alteração foi feita.")
        print("   Execute novamente com --execute para aplicar as mudanças.")
    else:
        print("✅ Migração concluída!")


async def migrate_organizations(db: AsyncSession, dry_run: bool = True):
    """
    Migra organizações (prepara app_metadata para usuários).
    
    Nota: No Supabase, organizações são representadas via app_metadata.
    Este script apenas valida que todas as organizações estão mapeadas.
    """
    print("=" * 80)
    print("VALIDAÇÃO DE ORGANIZAÇÕES")
    print("=" * 80)
    print()
    
    result = await db.execute(select(Organization))
    organizations = result.scalars().all()
    
    print(f"📊 Total de organizações: {len(organizations)}")
    print()
    
    for org in organizations:
        print(f"✅ {org.name}")
        print(f"   ID Interno: {org.id}")
        print(f"   Clerk Org ID: {org.clerk_org_id}")
        print(f"   Access Code: {org.access_code}")
        print()
    
    print("✅ Todas as organizações estão prontas para uso no Supabase")
    print("   (organization_id será armazenado em app_metadata dos usuários)")


async def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migra usuários do Clerk para Supabase")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Executa a migração (sem isso, apenas simula)"
    )
    parser.add_argument(
        "--organizations-only",
        action="store_true",
        help="Apenas valida organizações"
    )
    
    args = parser.parse_args()
    dry_run = not args.execute
    
    # Cria engine e sessão
    # Nota: Supabase usa pgbouncer que não suporta prepared statements
    # Por isso desabilitamos o cache de prepared statements
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={
            "server_settings": {
                "jit": "off"  # Desabilita JIT para compatibilidade com pgbouncer
            },
            "statement_cache_size": 0,  # Desabilita cache de prepared statements para pgbouncer
        },
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        if args.organizations_only:
            await migrate_organizations(db, dry_run)
        else:
            await migrate_users(db, dry_run)
            print()
            await migrate_organizations(db, dry_run)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
