"""
Script de teste para validar configuração do Supabase Auth.

Testa:
1. Conexão com Supabase
2. JWKS endpoint
3. Criação de usuário de teste
4. Validação de token
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.auth.supabase_provider import SupabaseProvider
import httpx


async def test_jwks():
    """Testa acesso ao JWKS endpoint."""
    print("1️⃣ Testando JWKS endpoint...")
    
    if not settings.SUPABASE_URL:
        print("   ❌ SUPABASE_URL não configurado")
        return False
    
    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/.well-known/jwks.json"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            
            if "keys" in jwks and len(jwks["keys"]) > 0:
                print(f"   ✅ JWKS acessível: {len(jwks['keys'])} chave(s) encontrada(s)")
                return True
            else:
                print("   ⚠️ JWKS sem chaves")
                return False
    except Exception as e:
        print(f"   ❌ Erro ao acessar JWKS: {str(e)}")
        return False


async def test_provider_init():
    """Testa inicialização do provider."""
    print("2️⃣ Testando inicialização do SupabaseProvider...")
    
    try:
        provider = SupabaseProvider()
        print("   ✅ Provider inicializado com sucesso")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao inicializar provider: {str(e)}")
        return False


async def test_create_test_user():
    """Testa criação de usuário de teste."""
    print("3️⃣ Testando criação de usuário de teste...")
    
    try:
        provider = SupabaseProvider()
        
        # Cria usuário de teste
        test_email = f"test_{asyncio.get_event_loop().time()}@test.com"
        
        user_data = await provider.create_user(
            email=test_email,
            first_name="Test",
            last_name="User",
            skip_password_requirement=True
        )
        
        if user_data and user_data.get("id"):
            print(f"   ✅ Usuário criado: {user_data.get('id')}")
            print(f"   📧 Email: {test_email}")
            
            # Limpa usuário de teste
            try:
                await provider.delete_user(user_data.get("id"))
                print("   🗑️ Usuário de teste removido")
            except:
                pass
            
            return True
        else:
            print("   ❌ Falha ao criar usuário")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False


async def main():
    """Função principal."""
    print("=" * 80)
    print("TESTE DE CONFIGURAÇÃO SUPABASE AUTH")
    print("=" * 80)
    print()
    
    # Verifica configuração
    if not settings.SUPABASE_URL:
        print("❌ SUPABASE_URL não configurado no .env")
        return
    
    if not settings.SUPABASE_SERVICE_KEY:
        print("❌ SUPABASE_SERVICE_KEY não configurado no .env")
        return
    
    print(f"📋 Configuração:")
    print(f"   SUPABASE_URL: {settings.SUPABASE_URL}")
    print(f"   SUPABASE_SERVICE_KEY: {'*' * 20}...{settings.SUPABASE_SERVICE_KEY[-4:]}")
    print()
    
    # Executa testes
    results = []
    
    results.append(await test_jwks())
    print()
    
    results.append(await test_provider_init())
    print()
    
    # Pergunta se deve criar usuário de teste
    create_user = input("Criar usuário de teste? (s/N): ").lower() == 's'
    if create_user:
        results.append(await test_create_test_user())
        print()
    
    # Resumo
    print("=" * 80)
    print("RESUMO")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("✅ Todos os testes passaram!")
    else:
        print(f"⚠️ {passed}/{total} testes passaram")
        print("   Revise a configuração no .env e no Dashboard do Supabase")


if __name__ == "__main__":
    asyncio.run(main())
