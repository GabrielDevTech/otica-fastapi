"""Segurança e autenticação com Clerk."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.utils import base64url_decode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import httpx
from app.core.config import settings


security = HTTPBearer()


async def get_jwks() -> dict:
    """Busca as chaves públicas (JWKS) do Clerk."""
    jwks_url = f"{settings.CLERK_ISSUER}/.well-known/jwks.json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        return response.json()


def jwk_to_pem(jwk: dict) -> str:
    """Converte uma chave JWK para formato PEM."""
    try:
        # Decodifica base64url para bytes
        # base64url_decode do jose retorna bytes
        n_b64 = jwk['n']
        e_b64 = jwk['e']
        
        # Decodifica base64url manualmente (mais confiável)
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


def get_public_key_pem(token: str, jwks: dict) -> Optional[str]:
    """Extrai a chave pública PEM correspondente ao token."""
    try:
        # Decodifica o header do token sem validar
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            return None
        
        # Encontra a chave correspondente no JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                try:
                    return jwk_to_pem(key)
                except Exception as e:
                    # Se falhar na conversão, tenta próxima chave
                    continue
        
        return None
    except Exception as e:
        return None


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Valida o token JWT do Clerk e retorna o payload.
    
    Valida a assinatura do token usando as chaves públicas (JWKS) do Clerk.
    
    Raises:
        HTTPException: 401 se token inválido, 403 se não tiver org_id
    """
    token = credentials.credentials
    
    try:
        # Busca JWKS
        try:
            jwks = await get_jwks()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Erro ao buscar JWKS do Clerk: {str(e)}. Verifique CLERK_ISSUER no .env"
            )
        
        # Obtém o kid do token
        try:
            unverified_header = jwt.get_unverified_header(token)
            token_kid = unverified_header.get("kid")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: não foi possível decodificar o header. {str(e)}"
            )
        
        if not token_kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token não contém 'kid' (Key ID) no header"
            )
        
        # Obtém a chave pública PEM correspondente ao token
        public_key_pem = get_public_key_pem(token, jwks)
        
        if not public_key_pem:
            # Lista os kids disponíveis no JWKS para debug
            available_kids = [key.get("kid") for key in jwks.get("keys", [])]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Não foi possível encontrar a chave pública para validar o token. Token KID: {token_kid}, JWKS KIDs disponíveis: {available_kids}"
            )
        
        # Valida e decodifica o token com a chave pública
        payload = jwt.decode(
            token,
            public_key_pem,
            algorithms=["RS256"],
            audience=None,  # Clerk pode não incluir audience
            issuer=settings.CLERK_ISSUER,
            options={"verify_aud": False}  # Desabilita verificação de audience se não estiver presente
        )
        
        # Extrai organization_id
        # Clerk pode usar "org_id" ou "o.id" (organization object)
        org_id = payload.get("org_id")
        
        # Se não tiver org_id direto, tenta pegar de "o.id" (organization object do Clerk)
        if not org_id and "o" in payload:
            org_obj = payload.get("o", {})
            if isinstance(org_obj, dict):
                org_id = org_obj.get("id")
        
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token não contém organization_id. Verifique se o usuário está em uma organização no Clerk."
            )
        
        return {
            "org_id": org_id,
            "user_id": payload.get("sub"),
            "payload": payload
        }
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erro ao validar token: {str(e)}"
        )


async def get_current_org_id(
    token_data: dict = Depends(verify_token)
) -> str:
    """
    Dependency que retorna o organization_id do token validado.
    
    Esta é a dependência principal usada em todas as rotas que precisam
    de isolamento multi-tenant.
    """
    return token_data["org_id"]


async def get_current_user_id(
    token_data: dict = Depends(verify_token)
) -> str:
    """
    Dependency que retorna o user_id (clerk_id) do token validado.
    """
    return token_data["user_id"]

