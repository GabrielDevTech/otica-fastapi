"""Script para debugar token JWT e verificar validação."""
import asyncio
import sys
import os
import jwt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_jwks, get_public_key_pem
import httpx


async def debug_token(token: str):
    """Debuga um token JWT e mostra informações detalhadas."""
    print("=" * 60)
    print("DEBUG DE TOKEN JWT")
    print("=" * 60)
    print()
    
    # 1. Decodificar token sem validar
    try:
        unverified_header = jwt.get_unverified_header(token)
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        
        print("1️⃣  HEADER DO TOKEN:")
        print(f"   {unverified_header}")
        print()
        
        print("2️⃣  PAYLOAD DO TOKEN (sem validação):")
        for key, value in unverified_payload.items():
            print(f"   {key}: {value}")
        print()
        
        # Verificar campos importantes
        print("3️⃣  VERIFICAÇÕES:")
        if "kid" in unverified_header:
            print(f"   ✅ Token tem 'kid': {unverified_header['kid']}")
        else:
            print(f"   ❌ Token NÃO tem 'kid' no header")
        
        if "org_id" in unverified_payload:
            print(f"   ✅ Token tem 'org_id': {unverified_payload['org_id']}")
        else:
            print(f"   ❌ Token NÃO tem 'org_id' no payload")
        
        if "sub" in unverified_payload:
            print(f"   ✅ Token tem 'sub' (user_id): {unverified_payload['sub']}")
        else:
            print(f"   ❌ Token NÃO tem 'sub' no payload")
        
        issuer = unverified_payload.get("iss", "")
        if issuer == settings.CLERK_ISSUER:
            print(f"   ✅ Issuer correto: {issuer}")
        else:
            print(f"   ⚠️  Issuer diferente! Token: {issuer}, Config: {settings.CLERK_ISSUER}")
        print()
        
    except Exception as e:
        print(f"❌ Erro ao decodificar token: {str(e)}")
        return
    
    # 2. Buscar JWKS
    print("4️⃣  BUSCANDO JWKS DO CLERK:")
    try:
        jwks = await get_jwks()
        print(f"   ✅ JWKS obtido com sucesso")
        print(f"   📋 Chaves disponíveis: {len(jwks.get('keys', []))}")
        
        for i, key in enumerate(jwks.get("keys", []), 1):
            print(f"   Chave {i}:")
            print(f"      - kid: {key.get('kid')}")
            print(f"      - kty: {key.get('kty')}")
            print(f"      - use: {key.get('use')}")
        print()
        
        # 3. Tentar encontrar chave correspondente
        token_kid = unverified_header.get("kid")
        if token_kid:
            print("5️⃣  BUSCANDO CHAVE CORRESPONDENTE:")
            matching_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == token_kid:
                    matching_key = key
                    print(f"   ✅ Chave encontrada! kid: {token_kid}")
                    break
            
            if not matching_key:
                print(f"   ❌ Chave NÃO encontrada para kid: {token_kid}")
                print(f"   💡 Verifique se o token é do mesmo Clerk (issuer correto)")
            else:
                # Tentar converter para PEM
                print("6️⃣  CONVERTENDO CHAVE PARA PEM:")
                try:
                    from app.core.security import jwk_to_pem
                    pem = jwk_to_pem(matching_key)
                    print(f"   ✅ Conversão bem-sucedida!")
                    print(f"   📏 Tamanho da chave PEM: {len(pem)} caracteres")
                except Exception as e:
                    print(f"   ❌ Erro na conversão: {str(e)}")
                    print(f"   💡 Problema na conversão JWK → PEM")
        print()
        
    except httpx.HTTPStatusError as e:
        print(f"   ❌ Erro HTTP ao buscar JWKS: {e.response.status_code}")
        print(f"   📄 Resposta: {e.response.text}")
        print()
        print(f"   💡 Verifique:")
        print(f"      1. CLERK_ISSUER no .env: {settings.CLERK_ISSUER}")
        print(f"      2. URL do JWKS: {settings.CLERK_ISSUER}/.well-known/jwks.json")
    except Exception as e:
        print(f"   ❌ Erro ao buscar JWKS: {str(e)}")
    
    print("=" * 60)
    print("DEBUG CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/debug_token.py <token_jwt>")
        print()
        print("Exemplo:")
        print("  python scripts/debug_token.py eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")
        sys.exit(1)
    
    token = sys.argv[1]
    asyncio.run(debug_token(token))

