"""
Script para enviar emails de reset de senha para usuários migrados do Supabase.

Este script envia emails de reset de senha para todos os usuários que foram
migrados do Clerk para o Supabase, permitindo que eles definam suas próprias senhas.
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
from app.core.auth.supabase_provider import SupabaseProvider


async def send_reset_emails(db: AsyncSession, email_filter: str = None, dry_run: bool = False):
    """Envia emails de reset de senha para usuários migrados."""
    print("=" * 80)
    print("ENVIO DE EMAILS DE RESET DE SENHA")
    print("=" * 80)
    print()
    
    if settings.AUTH_PROVIDER.lower() != "supabase":
        print("❌ ERRO: AUTH_PROVIDER deve ser 'supabase'")
        return
    
    supabase_provider = SupabaseProvider()
    
    # Busca usuários migrados
    query = select(StaffMember).where(StaffMember.clerk_id.isnot(None))
    if email_filter:
        query = query.where(StaffMember.email == email_filter)
    
    result = await db.execute(query)
    staff_members = result.scalars().all()
    
    if not staff_members:
        print("⚠️ Nenhum usuário encontrado para enviar email.")
        return
    
    print(f"📧 Encontrados {len(staff_members)} usuário(s) para enviar email de reset.")
    print()
    
    success_count = 0
    error_count = 0
    
    for staff in staff_members:
        try:
            print(f"📤 Enviando email para: {staff.email} ({staff.full_name})")
            
            if dry_run:
                print(f"   [DRY RUN] Enviaria email de reset para {staff.email}")
                success_count += 1
            else:
                # Envia email de reset via Supabase
                # Nota: O Supabase Admin API não tem método direto para enviar reset
                # Vamos usar o método de convite que também permite definir senha
                # OU podemos usar a API REST diretamente
                
                # Método alternativo: usar Admin API para atualizar usuário e depois
                # usar a API pública para solicitar reset
                # Por enquanto, vamos apenas informar o usuário
                
                # TODO: Implementar envio real via Supabase Admin API
                # Por enquanto, instruímos o usuário a fazer manualmente
                print(f"   ⚠️ Envio automático ainda não implementado.")
                print(f"   💡 Acesse o Dashboard do Supabase e envie manualmente:")
                print(f"      https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/auth/users")
                print(f"      → Busque por: {staff.email}")
                print(f"      → Clique em ⋯ → 'Send password reset email'")
                
                # Alternativa: usar httpx para chamar a API REST do Supabase
                import httpx
                
                reset_url = f"{settings.SUPABASE_URL}/auth/v1/recover"
                headers = {
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Content-Type": "application/json"
                }
                data = {
                    "email": staff.email,
                    "redirect_to": "http://localhost:3000/reset-password"  # Ajuste conforme seu frontend
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(reset_url, headers=headers, json=data)
                    
                    if response.status_code == 200:
                        print(f"   ✅ Email de reset enviado com sucesso!")
                        success_count += 1
                    else:
                        print(f"   ❌ Erro ao enviar email: {response.status_code} - {response.text}")
                        error_count += 1
            
            print()
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ ERRO: {str(e)}")
            print()
    
    print("=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"✅ Sucesso: {success_count}")
    print(f"❌ Erros: {error_count}")
    print(f"📊 Total: {len(staff_members)}")
    print()
    
    if dry_run:
        print("⚠️ Este foi um DRY RUN. Nenhum email foi enviado.")
        print("   Execute novamente sem --dry-run para enviar os emails.")
    else:
        print("✅ Processo concluído!")
        print()
        print("💡 Nota: Se o envio automático não funcionou, você pode:")
        print("   1. Enviar manualmente pelo Dashboard do Supabase")
        print("   2. Usar o script set_passwords_supabase.py para definir senhas temporárias")


async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Envia emails de reset de senha para usuários migrados")
    parser.add_argument("--email", help="Email específico para enviar (opcional)")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simula, não envia emails")
    
    args = parser.parse_args()
    
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
        await send_reset_emails(db, email_filter=args.email, dry_run=args.dry_run)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
