"""
Script para definir senhas para usuários no Supabase.

Permite definir senhas temporárias para usuários migrados, seja individualmente
ou em lote.
"""
import asyncio
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.staff_model import StaffMember
from app.core.config import settings
from supabase import create_client, Client


async def set_password(
    db: AsyncSession,
    supabase_admin: Client,
    email: str,
    password: str,
    dry_run: bool = False
):
    """Define senha para um usuário específico."""
    # Busca o staff member
    result = await db.execute(
        select(StaffMember).where(StaffMember.email == email)
    )
    staff = result.scalar_one_or_none()
    
    if not staff:
        print(f"❌ Usuário não encontrado: {email}")
        return False
    
    if not staff.clerk_id:
        print(f"❌ Usuário não foi migrado (sem clerk_id): {email}")
        return False
    
    try:
        if dry_run:
            print(f"[DRY RUN] Definiria senha para {email} ({staff.full_name})")
            return True
        
        # Atualiza senha via Admin API
        response = supabase_admin.auth.admin.update_user_by_id(
            staff.clerk_id,
            {"password": password}
        )
        
        # Verifica resposta
        user_data = None
        if isinstance(response, dict):
            user_data = response.get("user", response)
        elif hasattr(response, 'user'):
            user_data = response.user
        elif hasattr(response, 'id'):
            user_data = response
        
        if user_data:
            print(f"✅ Senha definida com sucesso para {email} ({staff.full_name})")
            return True
        else:
            print(f"❌ Resposta inválida do Supabase para {email}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao definir senha para {email}: {str(e)}")
        return False


async def set_passwords(
    db: AsyncSession,
    email_filter: str = None,
    password: str = None,
    all_users: bool = False,
    dry_run: bool = False
):
    """Define senhas para usuários."""
    print("=" * 80)
    print("DEFINIR SENHAS NO SUPABASE")
    print("=" * 80)
    print()
    
    if settings.AUTH_PROVIDER.lower() != "supabase":
        print("❌ ERRO: AUTH_PROVIDER deve ser 'supabase'")
        return
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("❌ ERRO: SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar configurados")
        return
    
    if not password and not all_users:
        print("❌ ERRO: Você deve fornecer --password ou usar --all com --password")
        return
    
    # Cria cliente Supabase Admin
    supabase_admin = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )
    
    # Busca usuários
    query = select(StaffMember).where(StaffMember.clerk_id.isnot(None))
    
    if email_filter:
        query = query.where(StaffMember.email == email_filter)
    
    result = await db.execute(query)
    staff_members = result.scalars().all()
    
    if not staff_members:
        print("⚠️ Nenhum usuário encontrado.")
        return
    
    print(f"📊 Encontrados {len(staff_members)} usuário(s).")
    print()
    
    if all_users and not password:
        print("❌ ERRO: --all requer --password")
        return
    
    success_count = 0
    error_count = 0
    
    for staff in staff_members:
        # Se --all, usa a senha fornecida
        # Se email específico, usa a senha fornecida
        result = await set_password(
            db,
            supabase_admin,
            staff.email,
            password,
            dry_run
        )
        
        if result:
            success_count += 1
        else:
            error_count += 1
        print()
    
    print("=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"✅ Sucesso: {success_count}")
    print(f"❌ Erros: {error_count}")
    print(f"📊 Total: {len(staff_members)}")
    print()
    
    if dry_run:
        print("⚠️ Este foi um DRY RUN. Nenhuma senha foi definida.")
        print("   Execute novamente sem --dry-run para aplicar as mudanças.")
    else:
        print("✅ Processo concluído!")
        print()
        print("⚠️ IMPORTANTE:")
        print("   - Compartilhe as senhas temporárias com os usuários por canal seguro")
        print("   - Recomende que os usuários alterem a senha no primeiro login")
        print("   - Não reutilize senhas antigas do Clerk")


async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Define senhas para usuários no Supabase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Define senha para um usuário específico
  py scripts/set_passwords_supabase.py --email usuario@example.com --password "Senha123"

  # Define senha padrão para todos os usuários (CUIDADO!)
  py scripts/set_passwords_supabase.py --all --password "SenhaTemporaria123"

  # Dry run (simula sem aplicar)
  py scripts/set_passwords_supabase.py --all --password "Senha123" --dry-run
        """
    )
    parser.add_argument("--email", help="Email do usuário (opcional se usar --all)")
    parser.add_argument("--password", help="Senha a ser definida")
    parser.add_argument("--all", action="store_true", help="Aplica para todos os usuários migrados")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simula, não define senhas")
    
    args = parser.parse_args()
    
    if not args.email and not args.all:
        parser.error("Você deve fornecer --email ou --all")
    
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
        await set_passwords(
            db,
            email_filter=args.email,
            password=args.password,
            all_users=args.all,
            dry_run=args.dry_run
        )
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
