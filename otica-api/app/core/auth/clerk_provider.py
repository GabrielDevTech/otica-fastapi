"""Implementação do provider Clerk."""
import httpx
from typing import Optional, Dict
from fastapi import HTTPException, status
from jose import jwt, JWTError
from jose.utils import base64url_decode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from app.core.auth.base_auth_provider import BaseAuthProvider
from app.core.config import settings


class ClerkProvider(BaseAuthProvider):
    """Provider de autenticação usando Clerk."""
    
    BASE_URL = "https://api.clerk.com/v1"
    
    def __init__(self):
        if not settings.CLERK_ISSUER:
            raise ValueError("CLERK_ISSUER não configurado no .env")
        if not settings.CLERK_SECRET_KEY:
            raise ValueError("CLERK_SECRET_KEY não configurado no .env")
        
        self.issuer = settings.CLERK_ISSUER
        self.headers = {
            "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
    
    async def get_jwks(self) -> dict:
        """Busca as chaves públicas (JWKS) do Clerk."""
        jwks_url = f"{self.issuer}/.well-known/jwks.json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            return response.json()
    
    def jwk_to_pem(self, jwk: dict) -> str:
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
    
    def get_public_key_pem(self, token: str, jwks: dict) -> Optional[str]:
        """Extrai a chave pública PEM correspondente ao token."""
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                return None
            
            # Encontra a chave correspondente no JWKS
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    try:
                        return self.jwk_to_pem(key)
                    except Exception:
                        continue
            
            return None
        except Exception:
            return None
    
    async def verify_token(self, token: str) -> Dict:
        """
        Valida o token JWT do Clerk e retorna o payload.
        
        Valida a assinatura do token usando as chaves públicas (JWKS) do Clerk.
        """
        try:
            # Busca JWKS
            try:
                jwks = await self.get_jwks()
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
            public_key_pem = self.get_public_key_pem(token, jwks)
            
            if not public_key_pem:
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
                audience=None,
                issuer=self.issuer,
                options={"verify_aud": False}
            )
            
            # Extrai organization_id
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
    
    async def get_user_email(self, user_id: str) -> Optional[str]:
        """Busca o email do usuário na API do Clerk."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/users/{user_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    email_addresses = user_data.get("email_addresses", [])
                    if email_addresses:
                        primary = next(
                            (e for e in email_addresses if e.get("id") == user_data.get("primary_email_address_id")),
                            email_addresses[0]
                        )
                        return primary.get("email_address")
                return None
        except Exception:
            return None
    
    async def create_user_invitation(
        self,
        email: str,
        organization_id: str,
        role: str = "org:member",
        redirect_url: Optional[str] = None
    ) -> Dict:
        """Cria um convite para um novo usuário e adiciona à organização."""
        async with httpx.AsyncClient() as client:
            payload = {
                "email_address": email,
                "role": role,
                "redirect_url": redirect_url or f"{settings.CORS_ORIGINS.split(',')[0]}/sign-in"
            }
            
            response = await client.post(
                f"{self.BASE_URL}/organizations/{organization_id}/invitations",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code not in [200, 201]:
                error_detail = response.json() if response.text else "Unknown error"
                raise Exception(f"Erro ao criar convite no Clerk: {error_detail}")
            
            return response.json()
    
    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str = "",
        skip_password_requirement: bool = True
    ) -> Dict:
        """Cria um usuário diretamente no Clerk."""
        async with httpx.AsyncClient() as client:
            payload = {
                "email_address": [email],
                "first_name": first_name,
                "last_name": last_name,
                "skip_password_requirement": skip_password_requirement
            }
            
            response = await client.post(
                f"{self.BASE_URL}/users",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code not in [200, 201]:
                error_detail = response.json() if response.text else "Unknown error"
                raise Exception(f"Erro ao criar usuário no Clerk: {error_detail}")
            
            return response.json()
    
    async def add_user_to_organization(
        self,
        user_id: str,
        organization_id: str,
        role: str = "org:member"
    ) -> Dict:
        """Adiciona um usuário existente a uma organização."""
        async with httpx.AsyncClient() as client:
            payload = {
                "user_id": user_id,
                "role": role
            }
            
            response = await client.post(
                f"{self.BASE_URL}/organizations/{organization_id}/memberships",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code not in [200, 201]:
                error_detail = response.json() if response.text else "Unknown error"
                raise Exception(f"Erro ao adicionar usuário à organização: {error_detail}")
            
            return response.json()
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Busca um usuário pelo email."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/users",
                headers=self.headers,
                params={"email_address": email}
            )
            
            if response.status_code != 200:
                return None
            
            users = response.json()
            if users and len(users) > 0:
                return users[0]
            
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Deleta um usuário do Clerk."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/users/{user_id}",
                headers=self.headers
            )
            
            return response.status_code in [200, 204]
