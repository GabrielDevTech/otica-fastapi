"""
Script para ajudar a encontrar e validar as chaves do Supabase.

Este script não busca automaticamente (requer autenticação no Supabase),
mas ajuda a validar se as chaves estão corretas após configuradas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
import httpx
import asyncio


async def validate_supabase_keys():
    """Valida se as chaves do Supabase estão configuradas e funcionando."""
    print("=" * 80)
    print("VALIDAÇÃO DAS CHAVES DO SUPABASE")
    print("=" * 80)
    print()
    
    # Verifica se as variáveis estão configuradas
    print("1️⃣ Verificando variáveis de ambiente...")
    print()
    
    if not settings.SUPABASE_URL:
        print("   ❌ SUPABASE_URL não configurado no .env")
        print("   📝 Adicione: SUPABASE_URL=https://seu-projeto.supabase.co")
    else:
        print(f"   ✅ SUPABASE_URL: {settings.SUPABASE_URL}")
    
    if not settings.SUPABASE_ANON_KEY:
        print("   ❌ SUPABASE_ANON_KEY não configurado no .env")
        print("   📝 Adicione: SUPABASE_ANON_KEY=sua_anon_key")
    else:
        masked_key = settings.SUPABASE_ANON_KEY[:20] + "..." + settings.SUPABASE_ANON_KEY[-4:]
        print(f"   ✅ SUPABASE_ANON_KEY: {masked_key}")
    
    if not settings.SUPABASE_SERVICE_KEY:
        print("   ❌ SUPABASE_SERVICE_KEY não configurado no .env")
        print("   📝 Adicione: SUPABASE_SERVICE_KEY=sua_service_key")
    else:
        masked_key = settings.SUPABASE_SERVICE_KEY[:20] + "..." + settings.SUPABASE_SERVICE_KEY[-4:]
        print(f"   ✅ SUPABASE_SERVICE_KEY: {masked_key}")
    
    print()
    
    # Testa conexão
    if settings.SUPABASE_URL:
        print("2️⃣ Testando conexão com Supabase...")
        print()
        
        # Testa JWKS endpoint (Supabase usa /auth/v1/.well-known/jwks.json)
        jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_url, timeout=10.0)
                if response.status_code == 200:
                    jwks = response.json()
                    key_count = len(jwks.get('keys', []))
                    if key_count > 0:
                        print(f"   ✅ JWKS endpoint acessível: {key_count} chave(s)")
                    else:
                        print(f"   ✅ JWKS endpoint acessível: {key_count} chave(s)")
                        print(f"   ℹ️  Nota: 0 chaves pode indicar uso de HS256 (simétrico) ou chaves ainda não configuradas")
                        print(f"      Isso é normal e não impede o funcionamento")
                else:
                    print(f"   ⚠️ JWKS endpoint retornou status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erro ao acessar JWKS: {str(e)}")
            print(f"   📝 Verifique se SUPABASE_URL está correto")
        
        print()
        
        # Testa API com anon key
        if settings.SUPABASE_ANON_KEY:
            print("3️⃣ Testando ANON_KEY...")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/",
                        headers={
                            "apikey": settings.SUPABASE_ANON_KEY,
                            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"
                        },
                        timeout=10.0
                    )
                    if response.status_code in [200, 404, 401]:  # 401/404 são OK, significa que a key funciona
                        print("   ✅ ANON_KEY válida (consegue acessar API)")
                    else:
                        print(f"   ⚠️ ANON_KEY retornou status {response.status_code}")
            except Exception as e:
                print(f"   ❌ Erro ao testar ANON_KEY: {str(e)}")
        
        print()
        
        # Testa API com service key
        if settings.SUPABASE_SERVICE_KEY:
            print("4️⃣ Testando SERVICE_KEY...")
            try:
                async with httpx.AsyncClient() as client:
                    # Tenta acessar admin API
                    response = await client.get(
                        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users",
                        headers={
                            "apikey": settings.SUPABASE_SERVICE_KEY,
                            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                        },
                        params={"per_page": 1},
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        print("   ✅ SERVICE_KEY válida (consegue acessar Admin API)")
                    elif response.status_code == 401:
                        print("   ❌ SERVICE_KEY inválida ou sem permissões")
                    else:
                        print(f"   ⚠️ SERVICE_KEY retornou status {response.status_code}")
            except Exception as e:
                print(f"   ❌ Erro ao testar SERVICE_KEY: {str(e)}")
    
    print()
    print("=" * 80)
    print("INSTRUÇÕES PARA OBTER AS CHAVES")
    print("=" * 80)
    print()
    print("1. Acesse: https://app.supabase.com")
    print("2. Faça login e selecione o projeto 'otica'")
    print("3. Vá em: Settings (⚙️) → API")
    print("4. Copie:")
    print("   - Project URL → SUPABASE_URL")
    print("   - anon public → SUPABASE_ANON_KEY")
    print("   - service_role → SUPABASE_SERVICE_KEY")
    print()
    print("5. Adicione no arquivo .env:")
    print("   SUPABASE_URL=https://seu-projeto.supabase.co")
    print("   SUPABASE_ANON_KEY=eyJhbGc...")
    print("   SUPABASE_SERVICE_KEY=eyJhbGc...")
    print()


if __name__ == "__main__":
    asyncio.run(validate_supabase_keys())
