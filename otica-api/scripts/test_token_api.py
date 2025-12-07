"""
Script para testar token JWT do Supabase fazendo requisições à API.

Este script:
1. Faz login no Supabase
2. Obtém o token JWT
3. Valida assinatura e expiração manualmente
4. Testa requisições à API do backend

Uso:
    python scripts/test_token_api.py
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos do app
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import time
import json
from datetime import datetime
from jose import jwt, JWTError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from supabase import create_client, Client
from app.core.config import settings


def jwk_to_pem(jwk: dict) -> str:
    """Converte uma chave JWK para formato PEM."""
    try:
        n_b64 = jwk['n']
        e_b64 = jwk['e']
        
        # Adiciona padding se necessário
        n_padded = n_b64 + '=' * (4 - len(n_b64) % 4)
        e_padded = e_b64 + '=' * (4 - len(e_b64) % 4)
        
        n_bytes = base64.urlsafe_b64decode(n_padded)
        e_bytes = base64.urlsafe_b64decode(e_padded)
        
        # Converte bytes para inteiros (big-endian)
        n_int = int.from_bytes(n_bytes, 'big')
        e_int = int.from_bytes(e_bytes, 'big')
        
        # Constrói a chave pública RSA
        public_numbers = rsa.RSAPublicNumbers(
            e_int,  # expoente (e)
            n_int   # módulo (n)
        )
        public_key = public_numbers.public_key(default_backend())
        
        # Serializa para PEM
        pem_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Erro ao converter JWK para PEM: {str(e)}")


def get_public_key_pem(token: str, jwks: dict) -> str | None:
    """Extrai a chave pública PEM correspondente ao token."""
    try:
        # Decodifica header manualmente
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64 = parts[0]
        header_padded = header_b64 + '=' * (4 - len(header_b64) % 4)
        header_bytes = base64.urlsafe_b64decode(header_padded)
        unverified_header = json.loads(header_bytes.decode('utf-8'))
        
        kid = unverified_header.get("kid")
        
        if not kid:
            return None
        
        # Encontra a chave correspondente no JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                try:
                    return jwk_to_pem(key)
                except Exception:
                    continue
        
        return None
    except Exception:
        return None


async def get_jwks(supabase_url: str) -> dict:
    """Busca as chaves públicas (JWKS) do Supabase."""
    jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        return response.json()


async def test_api_request(base_url: str, endpoint: str, token: str) -> dict:
    """Faz uma requisição à API do backend."""
    url = f"{base_url.rstrip('/')}{endpoint}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            return {
                "status_code": response.status_code,
                "success": response.is_success,
                "headers": dict(response.headers),
                "body": response.text[:500] if response.text else None,  # Limita a 500 chars
                "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            }
        except httpx.TimeoutException:
            return {
                "status_code": 0,
                "success": False,
                "error": "Timeout ao conectar com a API"
            }
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "error": str(e)
            }


async def main():
    """Função principal."""
    
    # Credenciais
    email = "bielleandro75@gmail.com"
    password = "SenhaTemporaria123"
    
    print("=" * 80)
    print("TESTE DE TOKEN JWT - SUPABASE → API BACKEND")
    print("=" * 80)
    print()
    
    # Verifica configurações
    if not settings.SUPABASE_URL:
        print("❌ ERRO: SUPABASE_URL não configurado no .env")
        return
    
    if not settings.SUPABASE_ANON_KEY:
        print("❌ ERRO: SUPABASE_ANON_KEY não configurado no .env")
        return
    
    supabase_url = settings.SUPABASE_URL.rstrip('/')
    anon_key = settings.SUPABASE_ANON_KEY
    
    # Verifica SERVICE_KEY (necessária para validar tokens HS256)
    service_key = settings.SUPABASE_SERVICE_KEY
    if not service_key:
        print("⚠️ AVISO: SUPABASE_SERVICE_KEY não configurado")
        print("   Tokens HS256 podem não ser validados corretamente")
        print("   Configure SUPABASE_SERVICE_KEY no .env para validação completa")
    else:
        print(f"✅ SUPABASE_SERVICE_KEY configurada (primeiros 20 chars): {service_key[:20]}...")
    
    # URL da API (assume localhost:8000 por padrão)
    api_base_url = "http://localhost:8000"
    
    print(f"📋 Configurações:")
    print(f"   SUPABASE_URL: {supabase_url}")
    print(f"   API Base URL: {api_base_url}")
    print(f"   Email: {email}")
    print()
    
    # 1. Faz login no Supabase
    print("🔐 [1/5] Fazendo login no Supabase...")
    try:
        supabase: Client = create_client(supabase_url, anon_key)
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not response or not response.session:
            print("❌ ERRO: Falha no login. Verifique as credenciais.")
            return
        
        session = response.session
        access_token = session.access_token
        
        print(f"✅ Login realizado com sucesso!")
        print(f"   User ID: {session.user.id}")
        print(f"   Email: {session.user.email}")
        print(f"   Token (primeiros 30 chars): {access_token[:30]}...")
        print()
    except Exception as e:
        print(f"❌ ERRO ao fazer login: {str(e)}")
        return
    
    # 2. Decodifica o token sem validar (decodificação manual)
    print("📄 [2/5] Decodificando token (sem validação)...")
    try:
        # Decodifica manualmente o JWT (header.payload.signature)
        parts = access_token.split('.')
        if len(parts) != 3:
            print("❌ ERRO: Token JWT inválido (não tem 3 partes)")
            return
        
        # Decodifica header
        header_b64 = parts[0]
        header_padded = header_b64 + '=' * (4 - len(header_b64) % 4)
        header_bytes = base64.urlsafe_b64decode(header_padded)
        unverified_header = json.loads(header_bytes.decode('utf-8'))
        
        # Decodifica payload
        payload_b64 = parts[1]
        payload_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_padded)
        unverified_payload = json.loads(payload_bytes.decode('utf-8'))
        
        print(f"✅ Token decodificado!")
        print(f"   Algoritmo: {unverified_header.get('alg')}")
        print(f"   Key ID (kid): {unverified_header.get('kid')}")
        print(f"   sub (user_id): {unverified_payload.get('sub')}")
        print(f"   email: {unverified_payload.get('email')}")
        print(f"   aud: {unverified_payload.get('aud')}")
        print(f"   exp: {unverified_payload.get('exp')} ({datetime.fromtimestamp(unverified_payload.get('exp', 0))})")
        
        # Verifica organization_id
        org_id = (
            unverified_payload.get("app_metadata", {}).get("organization_id") or
            unverified_payload.get("organization_id") or
            unverified_payload.get("user_metadata", {}).get("organization_id")
        )
        print(f"   organization_id: {org_id if org_id else '❌ NÃO ENCONTRADO'}")
        print()
    except Exception as e:
        print(f"❌ ERRO ao decodificar token: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Valida assinatura (detecta algoritmo: HS256 ou RS256)
    print("🔑 [3/5] Validando assinatura do token...")
    try:
        algorithm = unverified_header.get('alg')
        print(f"   Algoritmo detectado: {algorithm}")
        
        if algorithm == "HS256":
            # Para HS256, usa a chave secreta do Supabase
            print("   Usando chave secreta (HS256)...")
            
            # Para HS256, precisa usar SERVICE_KEY (não anon_key)
            secret_key = settings.SUPABASE_SERVICE_KEY
            
            if not secret_key:
                print("❌ ERRO: SUPABASE_SERVICE_KEY não configurado")
                print("   Para tokens HS256, é necessário SUPABASE_SERVICE_KEY")
                print("   A SUPABASE_ANON_KEY não pode validar assinaturas HS256")
                return
            
            print(f"   ✅ SERVICE_KEY encontrada (primeiros 20 chars): {secret_key[:20]}...")
            
            try:
                payload = jwt.decode(
                    access_token,
                    secret_key,
                    algorithms=["HS256"],
                    options={
                        "verify_signature": True,
                        "verify_aud": False,
                        "verify_iss": False,
                        "verify_exp": False,  # Validaremos manualmente
                        "verify_nbf": False,
                        "verify_iat": False,
                    }
                )
                print("✅ Assinatura válida (HS256)!")
            except JWTError as e:
                error_msg = str(e)
                if "audience" in error_msg.lower() or "invalid audience" in error_msg.lower():
                    print("⚠️ Erro de audience detectado, mas ignorando (workaround)...")
                    # Valida apenas a assinatura sem outros claims
                    try:
                        jwt.decode(
                            access_token,
                            secret_key,
                            algorithms=["HS256"],
                            options={
                                "verify_signature": True,
                                "verify_aud": False,
                                "verify_iss": False,
                                "verify_exp": False,
                                "verify_nbf": False,
                                "verify_iat": False,
                            }
                        )
                        print("✅ Assinatura válida (HS256) - audience ignorado!")
                        payload = unverified_payload
                    except JWTError as sig_err:
                        print(f"⚠️ AVISO: Falha na validação de assinatura: {str(sig_err)}")
                        print("   Continuando com payload não verificado (o backend validará)")
                        payload = unverified_payload
                elif "signature" in error_msg.lower():
                    print(f"⚠️ AVISO: Falha na validação de assinatura: {error_msg}")
                    print("   Isso pode indicar que a SUPABASE_SERVICE_KEY está incorreta")
                    print("   ou que o token foi assinado com uma chave diferente")
                    print("   Continuando com payload não verificado (o backend validará)")
                    payload = unverified_payload
                else:
                    print(f"⚠️ AVISO: Erro na validação: {error_msg}")
                    print("   Continuando com payload não verificado (o backend validará)")
                    payload = unverified_payload
                    
        elif algorithm == "RS256":
            # Para RS256, usa JWKS
            print("   Obtendo JWKS (RS256)...")
            jwks = await get_jwks(supabase_url)
            jwks_keys = jwks.get("keys", [])
            
            print(f"✅ JWKS obtido! ({len(jwks_keys)} chaves)")
            
            public_key_pem = get_public_key_pem(access_token, jwks)
            
            if not public_key_pem:
                print("❌ ERRO: Não foi possível encontrar a chave pública correspondente ao token")
                return
            
            print(f"✅ Chave pública encontrada!")
            
            try:
                payload = jwt.decode(
                    access_token,
                    public_key_pem,
                    algorithms=["RS256"],
                    options={
                        "verify_signature": True,
                        "verify_aud": False,
                        "verify_iss": False,
                        "verify_exp": False,  # Validaremos manualmente
                        "verify_nbf": False,
                        "verify_iat": False,
                    }
                )
                print("✅ Assinatura válida (RS256)!")
            except JWTError as e:
                error_msg = str(e)
                if "audience" in error_msg.lower() or "invalid audience" in error_msg.lower():
                    print("⚠️ Erro de audience detectado, mas ignorando (workaround)...")
                    # Valida apenas a assinatura
                    try:
                        jwt.decode(
                            access_token,
                            public_key_pem,
                            algorithms=["RS256"],
                            options={
                                "verify_signature": True,
                                "verify_aud": False,
                                "verify_iss": False,
                                "verify_exp": False,
                                "verify_nbf": False,
                                "verify_iat": False,
                            }
                        )
                        print("✅ Assinatura válida (RS256) - audience ignorado!")
                        payload = unverified_payload
                    except JWTError as sig_err:
                        print(f"❌ ERRO na validação da assinatura: {str(sig_err)}")
                        return
                else:
                    print(f"❌ ERRO na validação da assinatura: {error_msg}")
                    return
        else:
            print(f"❌ ERRO: Algoritmo não suportado: {algorithm}")
            return
            
    except Exception as e:
        print(f"❌ ERRO ao validar assinatura: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Valida expiração
    print("⏰ [4/5] Validando expiração...")
    try:
        exp = unverified_payload.get("exp")
        current_time = int(time.time())
        
        if exp:
            exp_datetime = datetime.fromtimestamp(exp)
            current_datetime = datetime.fromtimestamp(current_time)
            
            if exp < current_time:
                print(f"❌ Token EXPIRADO! (expirou há {current_time - exp} segundos)")
                return
            else:
                time_until_expiry = exp - current_time
                print(f"✅ Token VÁLIDO! (expira em {time_until_expiry} segundos)")
        else:
            print("⚠️ Token não contém claim 'exp'")
    except Exception as e:
        print(f"❌ ERRO ao validar expiração: {str(e)}")
        return
    
    print()
    
    # 5. Testa requisições à API
    print("🌐 [5/5] Testando requisições à API do backend...")
    print()
    
    # Endpoints para testar
    endpoints = [
        "/api/v1/staff",
        "/api/v1/stores",
        "/api/v1/departments",
        "/api/v1/staff/stats",
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"📤 Testando: {endpoint}")
        result = await test_api_request(api_base_url, endpoint, access_token)
        results.append({
            "endpoint": endpoint,
            "result": result
        })
        
        if result.get("success"):
            print(f"   ✅ Status: {result['status_code']} OK")
            if result.get("json"):
                data = result["json"]
                if isinstance(data, list):
                    print(f"   📊 Retornou {len(data)} itens")
                elif isinstance(data, dict):
                    print(f"   📊 Retornou objeto com {len(data)} campos")
        else:
            status_code = result.get("status_code", 0)
            error = result.get("error", "Unknown error")
            body = result.get("body", "")
            
            print(f"   ❌ Status: {status_code}")
            if error:
                print(f"   ❌ Erro: {error}")
            if body:
                # Tenta extrair mensagem de erro do JSON
                try:
                    error_json = json.loads(body)
                    if "detail" in error_json:
                        print(f"   ❌ Detalhe: {error_json['detail']}")
                except:
                    print(f"   ❌ Resposta: {body[:100]}...")
        print()
    
    # Resumo final
    print("=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    successful = sum(1 for r in results if r["result"].get("success"))
    total = len(results)
    
    print(f"✅ Requisições bem-sucedidas: {successful}/{total}")
    print()
    
    for result in results:
        endpoint = result["endpoint"]
        status = result["result"].get("status_code", 0)
        success = result["result"].get("success", False)
        symbol = "✅" if success else "❌"
        print(f"{symbol} {endpoint}: {status}")
    
    print()
    print("=" * 80)
    
    if successful == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
    elif successful > 0:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
    else:
        print("❌ TODOS OS TESTES FALHARAM!")
        print()
        print("Possíveis causas:")
        print("1. Backend não está rodando")
        print("2. AUTH_PROVIDER não está configurado como 'supabase'")
        print("3. Token não contém organization_id")
        print("4. Problema de CORS")
        print("5. URL da API incorreta")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
