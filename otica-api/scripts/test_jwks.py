"""Script para testar configuração de JWKS e chave pública."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_jwks, jwk_to_pem
import httpx


async def test_jwks_config():
    """Testa a configuração de JWKS e conversão de chaves."""
    print("=" * 60)
    print("TESTE DE CONFIGURAÇÃO - JWKS E CHAVE PÚBLICA")
    print("=" * 60)
    print()
    
    # 1. Verificar CLERK_ISSUER
    print("1️⃣  CONFIGURAÇÃO:")
    print(f"   CLERK_ISSUER: {settings.CLERK_ISSUER}")
    jwks_url = f"{settings.CLERK_ISSUER}/.well-known/jwks.json"
    print(f"   JWKS URL: {jwks_url}")
    print()
    
    # 2. Testar acesso ao JWKS
    print("2️⃣  TESTANDO ACESSO AO JWKS:")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_url)
            print(f"   Status HTTP: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ JWKS acessível!")
                jwks = response.json()
                print(f"   📋 Chaves disponíveis: {len(jwks.get('keys', []))}")
                print()
                
                # 3. Listar chaves
                print("3️⃣  CHAVES DISPONÍVEIS:")
                for i, key in enumerate(jwks.get("keys", []), 1):
                    print(f"   Chave {i}:")
                    print(f"      - kid: {key.get('kid')}")
                    print(f"      - kty: {key.get('kty')} (tipo)")
                    print(f"      - use: {key.get('use')} (uso)")
                    print(f"      - alg: {key.get('alg')} (algoritmo)")
                    
                    # 4. Testar conversão para PEM
                    print(f"      - Testando conversão JWK → PEM...")
                    try:
                        if key.get('kty') == 'RSA':
                            pem = jwk_to_pem(key)
                            print(f"      ✅ Conversão bem-sucedida!")
                            print(f"      📏 Tamanho PEM: {len(pem)} caracteres")
                            print(f"      📄 Primeiros 50 chars: {pem[:50]}...")
                        else:
                            print(f"      ⚠️  Tipo de chave não suportado: {key.get('kty')}")
                    except Exception as e:
                        print(f"      ❌ Erro na conversão: {str(e)}")
                    print()
                
                # 5. Resumo
                print("4️⃣  RESUMO:")
                rsa_keys = [k for k in jwks.get("keys", []) if k.get("kty") == "RSA"]
                print(f"   ✅ Total de chaves: {len(jwks.get('keys', []))}")
                print(f"   ✅ Chaves RSA: {len(rsa_keys)}")
                print(f"   ✅ Configuração parece correta!")
                
            else:
                print(f"   ❌ Erro ao acessar JWKS!")
                print(f"   📄 Resposta: {response.text}")
                print()
                print("   💡 Verifique:")
                print(f"      1. CLERK_ISSUER está correto? {settings.CLERK_ISSUER}")
                print(f"      2. URL está acessível? {jwks_url}")
                print(f"      3. Você tem conexão com a internet?")
                
    except httpx.ConnectError:
        print(f"   ❌ Erro de conexão!")
        print(f"   💡 Não foi possível conectar a {jwks_url}")
        print(f"   Verifique sua conexão com a internet")
    except httpx.TimeoutException:
        print(f"   ❌ Timeout ao buscar JWKS!")
        print(f"   💡 O servidor do Clerk pode estar lento")
    except Exception as e:
        print(f"   ❌ Erro inesperado: {str(e)}")
        print(f"   Tipo: {type(e).__name__}")
    
    print()
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_jwks_config())

