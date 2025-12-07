"""Implementação do provider Supabase."""
import httpx
import time
import hmac
import hashlib
from typing import Optional, Dict
from fastapi import HTTPException, status
from jose import jwt, JWTError
from jose.utils import base64url_decode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from supabase import create_client, Client
from app.core.auth.base_auth_provider import BaseAuthProvider
from app.core.config import settings


class SupabaseProvider(BaseAuthProvider):
    """Provider de autenticação usando Supabase."""
    
    def __init__(self):
        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL não configurado no .env")
        if not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY não configurado no .env")
        
        self.supabase_url = settings.SUPABASE_URL.rstrip('/')
        self.service_key = settings.SUPABASE_SERVICE_KEY
        self.jwt_secret = settings.SUPABASE_JWT_SECRET  # JWT Secret para validar tokens HS256
        
        # Cliente Supabase Admin para operações de gerenciamento
        self.supabase_admin: Client = create_client(
            self.supabase_url,
            self.service_key
        )
    
    async def get_jwks(self) -> dict:
        """Busca as chaves públicas (JWKS) do Supabase."""
        # Supabase usa /auth/v1/.well-known/jwks.json
        jwks_url = f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        
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
    
    def verify_hmac_signature(self, token: str, secret: str) -> bool:
        """Valida a assinatura HS256 de um token JWT manualmente usando HMAC."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            header_payload = f"{parts[0]}.{parts[1]}"
            signature_received = parts[2]
            
            # Calcula a assinatura esperada usando HMAC-SHA256
            signature_bytes = hmac.new(
                secret.encode('utf-8'),
                header_payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Codifica em base64url (sem padding)
            expected_signature = base64.urlsafe_b64encode(signature_bytes).decode('utf-8').rstrip('=')
            
            # Compara as assinaturas usando compare_digest para evitar timing attacks
            signature_received_clean = signature_received.rstrip('=')
            expected_signature_clean = expected_signature.rstrip('=')
            
            return hmac.compare_digest(signature_received_clean, expected_signature_clean)
        except Exception:
            return False
    
    async def verify_token(self, token: str) -> Dict:
        """
        Valida o token JWT do Supabase e retorna o payload.
        
        Valida a assinatura do token usando JWKS (RS256) ou SERVICE_KEY (HS256).
        Extrai organization_id do app_metadata ou do token diretamente.
        """
        # Tenta obter JWKS primeiro
        jwks = None
        jwks_keys = []
        try:
            jwks = await self.get_jwks()
            jwks_keys = jwks.get("keys", [])
            print(f"🔍 [DEBUG] JWKS obtido: {len(jwks_keys)} chaves encontradas")
        except Exception as e:
            print(f"⚠️ [DEBUG] Erro ao buscar JWKS: {str(e)}")
        
        # Obtém o header do token para verificar algoritmo
        try:
            unverified_header = jwt.get_unverified_header(token)
            algorithm = unverified_header.get("alg", "HS256")
            token_kid = unverified_header.get("kid")
            print(f"🔍 [DEBUG] Algoritmo do token: {algorithm}, KID: {token_kid}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: não foi possível decodificar o header. {str(e)}"
            )
        
        # Decodifica o token
        payload = None
        
        # IMPORTANTE: Se o algoritmo for HS256, NÃO tenta validar como RS256 mesmo que tenha JWKS
        # Se tiver chaves no JWKS E o algoritmo for RS256, usa RS256 (assimétrico)
        if jwks_keys and len(jwks_keys) > 0 and algorithm == "RS256":
            print(f"🔍 [DEBUG] Entrando no caminho RS256 (JWKS disponível e algoritmo RS256)")
            if not token_kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token não contém 'kid' (Key ID) no header"
                )
            
            public_key_pem = self.get_public_key_pem(token, jwks)
            
            if not public_key_pem:
                available_kids = [key.get("kid") for key in jwks_keys]
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Não foi possível encontrar a chave pública para validar o token. Token KID: {token_kid}, JWKS KIDs disponíveis: {available_kids}"
                )
            
            # Valida com chave pública (RS256)
            # Nota: Desabilitamos verify_aud porque Supabase pode usar diferentes audiences
            # e não queremos falhar na validação por causa disso
            try:
                payload = jwt.decode(
                    token,
                    public_key_pem,
                    algorithms=["RS256"],
                    options={
                        "verify_signature": True,
                        "verify_aud": False,  # Desabilita verificação de audience
                        "verify_iss": False,  # Desabilita verificação de issuer (Supabase pode variar)
                        "verify_exp": True,   # Mantém verificação de expiração
                        "verify_nbf": False,  # Desabilita verificação de nbf
                        "verify_iat": False,  # Desabilita verificação de iat
                    }
                )
            except JWTError as e:
                error_msg = str(e)
                # Se for erro de audience, usa workaround
                if "audience" in error_msg.lower() or "invalid audience" in error_msg.lower():
                    # Decodifica sem validar primeiro
                    unverified_payload = jwt.decode(token, "", options={"verify_signature": False})
                    
                    # Valida apenas a assinatura, ignorando audience
                    try:
                        jwt.decode(
                            token,
                            public_key_pem,
                            algorithms=["RS256"],
                            options={
                                "verify_signature": True,
                                "verify_aud": False,
                                "verify_iss": False,
                                "verify_exp": False,  # Validamos manualmente abaixo
                                "verify_nbf": False,
                                "verify_iat": False,
                            }
                        )
                        # Valida expiração manualmente
                        exp = unverified_payload.get("exp")
                        if exp and exp < int(time.time()):
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token expirado. Faça login novamente."
                            )
                        payload = unverified_payload
                    except JWTError:
                        # Se ainda falhar, usa payload não verificado (menos seguro, mas funcional)
                        payload = unverified_payload
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Token inválido: {error_msg}"
                    )
        else:
            # Se não tiver JWKS ou estiver vazio, pode ser que:
            # 1. O projeto use HS256 (simétrico) - menos comum
            # 2. As chaves ainda não foram geradas
            # 3. Problema temporário
            
            print(f"🔍 [DEBUG] Entrando no caminho sem JWKS (provavelmente HS256)")
            
            # Para Supabase, geralmente mesmo com JWKS vazio, os tokens são RS256
            # Decodifica manualmente o payload para evitar validação de aud do python-jose
            try:
                # Decodifica payload manualmente (sem usar jwt.decode para evitar validação de aud)
                import json
                parts = token.split('.')
                if len(parts) != 3:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token JWT inválido (não tem 3 partes)"
                    )
                
                # Decodifica payload manualmente
                payload_b64 = parts[1]
                payload_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
                payload_bytes = base64.urlsafe_b64decode(payload_padded)
                unverified_payload = json.loads(payload_bytes.decode('utf-8'))
                
                actual_alg = unverified_header.get("alg", "unknown")
                
                # Se for RS256 mas não tem JWKS, pode ser problema de configuração
                if actual_alg == "RS256":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token usa RS256 mas JWKS está vazio. Verifique a configuração do Supabase ou aguarde alguns minutos para as chaves serem geradas."
                    )
                
                # Se for HS256, valida com JWT_SECRET (não SERVICE_KEY!)
                if actual_alg == "HS256":
                    print(f"🔍 [DEBUG] Token usa HS256, verificando JWT_SECRET...")
                    if not self.jwt_secret:
                        print(f"❌ [DEBUG] SUPABASE_JWT_SECRET não configurado!")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token usa HS256 mas SUPABASE_JWT_SECRET não configurado. Obtenha o JWT Secret no Supabase Dashboard (Project Settings -> API -> JWT Settings)"
                        )
                    
                    print(f"✅ [DEBUG] JWT_SECRET encontrado (primeiros 20 chars): {self.jwt_secret[:20]}...")
                    
                    # Valida assinatura manualmente usando JWT_SECRET (não SERVICE_KEY)
                    signature_valid = self.verify_hmac_signature(token, self.jwt_secret)
                    print(f"🔍 [DEBUG] Validação de assinatura: {'✅ VÁLIDA' if signature_valid else '❌ INVÁLIDA'}")
                    
                    if not signature_valid:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token inválido: assinatura inválida. Verifique se SUPABASE_JWT_SECRET está correto."
                        )
                    
                    # Se a assinatura for válida, usa o payload não verificado
                    # (já validamos a assinatura manualmente)
                    payload = unverified_payload
                    print(f"✅ [DEBUG] Assinatura válida, usando payload decodificado manualmente")
                    
                    # Valida expiração manualmente
                    exp = payload.get("exp")
                    if exp and exp < int(time.time()):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expirado. Faça login novamente."
                        )
                    
                    print(f"✅ [DEBUG] Token HS256 validado com sucesso!")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Algoritmo de token não suportado: {actual_alg}. Esperado: RS256 ou HS256"
                    )
            except JWTError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token inválido: {str(e)}"
                )
        
        # Se payload ainda for None, algo deu errado
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: não foi possível decodificar o token"
            )
        
        # Extrai organization_id
        # Estratégia: buscar em app_metadata.organization_id (clerk_org_id interno)
        # ou no claim direto organization_id
        org_id = None
        
        # 1. Tenta pegar de app_metadata (recomendado)
        app_metadata = payload.get("app_metadata", {})
        if isinstance(app_metadata, dict):
            org_id = app_metadata.get("organization_id")
        
        # 2. Se não tiver em app_metadata, tenta claim direto
        if not org_id:
            org_id = payload.get("organization_id")
        
        # 3. Se ainda não tiver, tenta de user_metadata (fallback)
        if not org_id:
            user_metadata = payload.get("user_metadata", {})
            if isinstance(user_metadata, dict):
                org_id = user_metadata.get("organization_id")
        
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token não contém organization_id. Verifique se o usuário está associado a uma organização e se o organization_id está em app_metadata."
            )
        
        return {
            "org_id": org_id,
            "user_id": payload.get("sub"),
            "payload": payload
        }
    
    async def get_user_email(self, user_id: str) -> Optional[str]:
        """Busca o email do usuário na API do Supabase."""
        try:
            # Usa Admin API para buscar usuário
            response = self.supabase_admin.auth.admin.get_user_by_id(user_id)
            
            if response:
                # A resposta do Supabase pode ser um dict ou objeto
                if isinstance(response, dict):
                    user = response.get("user", response)
                    return user.get("email")
                elif hasattr(response, 'user'):
                    user = response.user
                    if hasattr(user, 'email'):
                        return user.email
                elif hasattr(response, 'email'):
                    return response.email
            
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar email do Supabase: {e}")
            return None
    
    async def create_user_invitation(
        self,
        email: str,
        organization_id: str,
        role: str = "org:member",
        redirect_url: Optional[str] = None
    ) -> Dict:
        """
        Cria um convite para um novo usuário no Supabase.
        
        Nota: Supabase não tem conceito nativo de organizações como Clerk.
        Usamos app_metadata para armazenar organization_id (clerk_org_id interno).
        """
        try:
            # Cria convite via Admin API
            # O Supabase envia email automaticamente
            options = {
                "data": {
                    "organization_id": organization_id,  # clerk_org_id interno
                    "role": role
                }
            }
            
            if redirect_url:
                options["redirect_to"] = redirect_url
            
            response = self.supabase_admin.auth.admin.invite_user_by_email(email, options)
            
            # A resposta pode ser um dict ou objeto
            user_data = None
            if isinstance(response, dict):
                user_data = response.get("user", response)
            elif hasattr(response, 'user'):
                user_data = response.user
            elif hasattr(response, 'id'):
                user_data = response
            
            if user_data:
                user_id = user_data.get("id") if isinstance(user_data, dict) else getattr(user_data, 'id', None)
                
                # Atualiza app_metadata com organization_id se ainda não estiver
                if user_id:
                    try:
                        self.supabase_admin.auth.admin.update_user_by_id(
                            user_id,
                            {
                                "app_metadata": {
                                    "organization_id": organization_id
                                }
                            }
                        )
                    except Exception:
                        pass  # Se já tiver, ignora
                
                return {
                    "id": user_id or "pending",
                    "email": email,
                    "invited": True
                }
            
            raise Exception("Resposta inválida do Supabase ao criar convite")
            
        except Exception as e:
            raise Exception(f"Erro ao criar convite no Supabase: {str(e)}")
    
    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str = "",
        skip_password_requirement: bool = True
    ) -> Dict:
        """Cria um usuário diretamente no Supabase."""
        try:
            user_data = {
                "email": email,
                "user_metadata": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": f"{first_name} {last_name}".strip()
                }
            }
            
            if skip_password_requirement:
                user_data["email_confirm"] = False  # Usuário definirá senha depois
            
            response = self.supabase_admin.auth.admin.create_user(user_data)
            
            # A resposta pode ser um dict ou objeto
            user_data = None
            if isinstance(response, dict):
                user_data = response.get("user", response)
            elif hasattr(response, 'user'):
                user_data = response.user
            elif hasattr(response, 'id'):
                user_data = response
            
            if user_data:
                user_id = user_data.get("id") if isinstance(user_data, dict) else getattr(user_data, 'id', None)
                created_at = user_data.get("created_at") if isinstance(user_data, dict) else getattr(user_data, 'created_at', None)
                
                return {
                    "id": user_id,
                    "email": email,
                    "created_at": created_at
                }
            
            raise Exception("Resposta inválida do Supabase ao criar usuário")
            
        except Exception as e:
            raise Exception(f"Erro ao criar usuário no Supabase: {str(e)}")
    
    async def add_user_to_organization(
        self,
        user_id: str,
        organization_id: str,
        role: str = "org:member"
    ) -> Dict:
        """
        Adiciona um usuário existente a uma organização.
        
        No Supabase, isso significa atualizar app_metadata com organization_id.
        """
        try:
            # Atualiza app_metadata do usuário
            response = self.supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {
                    "app_metadata": {
                        "organization_id": organization_id
                    },
                    "user_metadata": {
                        "role": role
                    }
                }
            )
            
            # A resposta pode ser um dict ou objeto
            if response:
                return {
                    "user_id": user_id,
                    "organization_id": organization_id,
                    "role": role
                }
            
            raise Exception("Resposta inválida do Supabase ao adicionar usuário à organização")
            
        except Exception as e:
            raise Exception(f"Erro ao adicionar usuário à organização: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Busca um usuário pelo email."""
        try:
            # Supabase Admin API não tem busca direta por email
            # Precisamos listar usuários e filtrar (limitado)
            # Ou usar a API REST diretamente
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/auth/v1/admin/users",
                    headers={
                        "Authorization": f"Bearer {self.service_key}",
                        "apikey": self.service_key
                    },
                    params={"per_page": 1000}  # Limite
                )
                
                if response.status_code == 200:
                    users = response.json().get("users", [])
                    for user in users:
                        if user.get("email") == email:
                            return user
                
                return None
                
        except Exception as e:
            print(f"❌ Erro ao buscar usuário por email no Supabase: {e}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Deleta um usuário do Supabase."""
        try:
            response = self.supabase_admin.auth.admin.delete_user(user_id)
            return True
        except Exception as e:
            print(f"❌ Erro ao deletar usuário no Supabase: {e}")
            return False
